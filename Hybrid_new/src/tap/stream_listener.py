"""Module 12: X Activity API Stream Listener.

Replaces polling-based reply detection with real-time event streaming.
Subscribes to post.create, post.delete, chat.received, and dm.received
events for the target user via X's Activity API Persistent HTTP Stream.

Two-step architecture:
1. Subscribe: POST /2/activity/subscriptions with event_type + filter
2. Stream: GET /2/activity/stream (persistent connection delivering matching events)

Supports ActivitySubscriptionFilter for keyword/user_id isolation and
OAuth 2.0 User Context for elevated-scoped subscription access.

Benefits over polling:
- Real-time reply detection (no 30s poll delay)
- ~99% reduction in API quota usage
- Deletion detection (new intelligence signal)
- DM and chat monitoring (new intel channel)
- No more "stuck waiting" bugs from polling gaps
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Optional

import httpx

from tap.config import Settings, save_env_vars
from tap.logger import get_logger
from tap.models import ActivitySubscriptionFilter, Tweet, TweetSource

log = get_logger("stream_listener")

# X Activity API endpoints (per OpenAPI spec)
_SUBSCRIPTIONS_URL = "https://api.x.com/2/activity/subscriptions"
_STREAM_URL = "https://api.x.com/2/activity/stream"

# Supported event types
_SUPPORTED_EVENT_TYPES = frozenset({
    "post.create",
    "post.delete",
    "chat.received",
    "dm.received",
})


class StreamListener:
    """Real-time event stream for X Activity API.

    Subscribes to post.create, post.delete, chat.received, and dm.received
    events for a target user. Pushes incoming replies to an asyncio.Queue
    for consumption by grok_monitor.wait_for_reply().

    Supports ActivitySubscriptionFilter for keyword/user_id isolation
    and OAuth 2.0 User Context for elevated-scoped subscriptions.

    Architecture:
    1. Creates subscriptions via POST /2/activity/subscriptions
    2. Connects to GET /2/activity/stream (persistent HTTP connection)
    3. Events are parsed and pushed to per-tweet_id queues
    4. wait_for_reply() awaits on the queue instead of polling
    """

    def __init__(
        self,
        settings: Settings,
        subscription_filter: Optional[ActivitySubscriptionFilter] = None,
    ) -> None:
        """Initialize stream listener.

        Args:
            settings: TAP Framework settings with Twitter credentials.
            subscription_filter: Optional filter for keyword/user_id isolation.
        """
        self.settings = settings
        self._target_user_id: Optional[str] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._subscription_filter = subscription_filter

        # OAuth 2.0 User Context token (preferred for Activity API)
        self._oauth2_token: Optional[str] = settings.twitter_oauth2_access_token
        self._last_oauth2_refresh_status: str = "unknown"
        self._last_oauth2_refresh_error: Optional[str] = None
        self._last_subscription_auth_failure: bool = False
        self._last_subscription_errors: list[dict[str, str]] = []
        self._last_stream_auth_error: Optional[str] = None

        # Per-tweet_id queues: when a reply arrives for tweet_id,
        # the Tweet is pushed to _reply_queues[tweet_id]
        self._reply_queues: dict[str, asyncio.Queue[Tweet]] = {}

        # Global event log for all events (for dashboard/UI)
        self._event_log: asyncio.Queue[dict] = asyncio.Queue(maxsize=1000)

        # Deleted tweet IDs (intelligence signal)
        self.deleted_tweet_ids: list[str] = []

        # Received DMs / chat messages (intelligence signal)
        self.received_messages: list[dict] = []

        log.info(
            "stream_listener_initialized",
            target=settings.target_handle,
            has_filter=subscription_filter is not None,
            has_oauth2=bool(self._oauth2_token),
        )

    def set_target_user_id(self, user_id: str) -> None:
        """Set the target user ID to subscribe to.

        Args:
            user_id: The Twitter user ID of the target (e.g., @HackingA0).
        """
        self._target_user_id = user_id
        log.info("stream_target_set", user_id=user_id)

    def set_subscription_filter(
        self, subscription_filter: ActivitySubscriptionFilter
    ) -> None:
        """Update the subscription filter for event isolation.

        Args:
            subscription_filter: New filter to apply to subscriptions.
        """
        self._subscription_filter = subscription_filter
        log.info(
            "subscription_filter_updated",
            user_ids=subscription_filter.user_ids,
            keywords=subscription_filter.keywords,
        )

    def register_reply_wait(self, tweet_id: str) -> asyncio.Queue[Tweet]:
        """Register a wait for a reply to a specific tweet.

        Creates a queue that will receive the reply Tweet when it arrives.

        Args:
            tweet_id: The tweet ID we're waiting for a reply to.

        Returns:
            asyncio.Queue that will receive the reply Tweet.
        """
        queue: asyncio.Queue[Tweet] = asyncio.Queue(maxsize=1)
        self._reply_queues[tweet_id] = queue
        log.info("reply_wait_registered", tweet_id=tweet_id)
        return queue

    def unregister_reply_wait(self, tweet_id: str) -> None:
        """Remove a reply wait registration.

        Args:
            tweet_id: The tweet ID to stop waiting for.
        """
        self._reply_queues.pop(tweet_id, None)

    async def start(self) -> None:
        """Start the background stream listener task."""
        if self._running:
            log.warning("stream_already_running")
            return

        self._running = True
        self._task = asyncio.create_task(self._stream_loop())
        log.info("stream_started")

    async def stop(self) -> None:
        """Stop the background stream listener task."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        log.info("stream_stopped")

    async def _stream_loop(self) -> None:
        """Main streaming loop with reconnection logic.

        Maintains a persistent HTTP connection to the X Activity API.
        Automatically reconnects on disconnection with exponential backoff.
        Uses longer backoff (60s) for authentication failures to avoid
        hammering the API with invalid credentials.
        """
        backoff = 1
        max_backoff = 300  # 5 minutes
        auth_failure_backoff = 60  # 1 minute for auth failures

        while self._running:
            try:
                await self._connect_and_listen()
                # If we get here, the connection closed normally
                backoff = 1  # Reset backoff on clean close
            except asyncio.CancelledError:
                log.info("stream_loop_cancelled")
                raise
            except httpx.HTTPError as e:
                error_str = str(e)
                lower_err = error_str.lower()
                is_auth_failure = any(
                    keyword in lower_err
                    for keyword in ("401", "403", "unauthorized", "subscription")
                )
                if "429" in lower_err or "toomanyconnections" in lower_err:
                    self._last_stream_auth_error = error_str[:300]
                    wait_time = auth_failure_backoff
                    log.warning(
                        "stream_too_many_connections_error",
                        error=error_str[:300],
                        reconnect_in=wait_time,
                    )
                else:
                    self._last_stream_auth_error = error_str[:300]
                    wait_time = auth_failure_backoff if is_auth_failure else backoff
                    log.warning(
                        "stream_connection_lost",
                        error=error_str[:300],
                        reconnect_in=wait_time,
                        is_auth_failure=is_auth_failure,
                    )
                await asyncio.sleep(wait_time)
                if not is_auth_failure and "429" not in lower_err and "toomanyconnections" not in lower_err:
                    backoff = min(backoff * 2, max_backoff)
                # For auth failures and rate limit errors, always wait 60s (don't escalate)
            except Exception as e:
                log.warning(
                    "stream_connection_lost",
                    error=str(e)[:200],
                    reconnect_in=backoff,
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)

    async def _refresh_oauth2_token(self) -> Optional[str]:
        """Refresh OAuth2 token using shared helper and persist updates."""
        try:
            from tap.oauth import refresh_oauth2_token

            new_token = await refresh_oauth2_token(self.settings)
            if new_token:
                self._oauth2_token = new_token
                # settings are persisted by helper; keep in-memory in sync
                self.settings.twitter_oauth2_access_token = new_token
                # Persist to .env as best-effort (helper may already have), keep file in sync
                try:
                    save_env_vars({"twitter_oauth2_access_token": new_token})
                except Exception:
                    pass

                log.info("oauth2_token_refreshed_shared_helper")
                try:
                    save_env_vars({"TWITTER_OAUTH2_ACCESS_TOKEN": new_token})
                except Exception:
                    pass
                return new_token
            return None
        except Exception as e:
            log.warning("oauth2_refresh_shared_helper_error", error=str(e))
            return None

    async def _resolve_authenticated_user_id(self) -> Optional[str]:
        """Resolve user ID for the currently authenticated OAuth2 user token.

        Uses `/2/users/me` endpoint with OAuth2 User Context token. Returns
        the user ID as a string, or None on failure.
        """
        token = self._oauth2_token or self.settings.twitter_oauth2_access_token
        if not token:
            return None

        url = "https://api.x.com/2/users/me"
        headers = {"Authorization": f"Bearer {token}"}
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10)) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    j = resp.json()
                    uid = j.get("data", {}).get("id")
                    if uid:
                        return str(uid)
        except Exception:
            pass
        return None

    def _get_subscription_headers(self) -> dict[str, str]:
        """Get auth headers for subscription creation.

        Subscription creation supports both BearerToken and OAuth2UserToken.
        Prefers OAuth 2.0 User Context when available for elevated scopes
        (dm.read, tweet.read). Falls back to Bearer token.

        Returns:
            Dictionary of HTTP headers.
        """
        token = self._oauth2_token or self.settings.twitter_bearer_token
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _get_stream_headers(self) -> dict[str, str]:
        """Get auth headers for the persistent stream endpoint.

        The stream endpoint REQUIRES OAuth 2.0 Application-Only (Bearer token).
        It does NOT support OAuth 2.0 User Context — using a User token
        results in 403 "Unsupported Authentication".

        Returns:
            Dictionary of HTTP headers with Bearer token.
        """
        return {
            "Authorization": f"Bearer {self.settings.twitter_bearer_token}",
            "Content-Type": "application/json",
        }

    async def _connect_and_listen(self) -> None:
        """Connect to the Activity API stream and process events.

        Multi-step process:
        1. Try to refresh OAuth 2.0 token if available
        2. Create subscriptions for all supported event types using
           OAuth 2.0 User Context (or Bearer as fallback)
        3. Connect to persistent stream endpoint using Bearer token
           (Application-Only — required by the stream endpoint)

        Raises:
            httpx.HTTPError: On connection errors.
            asyncio.CancelledError: When stopped.
        """
        if not self._target_user_id:
            log.error("stream_no_target_user_id")
            await asyncio.sleep(60)
            return

        # Step 0: Refresh OAuth 2.0 token if we have a refresh token.
        # If refresh fails, continue using the current access token and
        # fallback to bearer token subscriptions as needed.
        if self.settings.twitter_oauth2_refresh_token:
            refreshed = await self._refresh_oauth2_token()
            if not refreshed:
                log.warning(
                    "oauth2_refresh_failed_continuing_with_existing_token",
                    has_current_token=bool(self._oauth2_token or self.settings.twitter_oauth2_access_token),
                )

        # Resolve authenticated user id to determine whether user-scoped
        # subscriptions (chat.received, dm.received) are allowed.
        auth_user_id = await self._resolve_authenticated_user_id()
        allow_user_subs = auth_user_id == self._target_user_id if auth_user_id else False
        log.info(
            "stream_authenticated_user_resolved",
            auth_user_id=auth_user_id,
            allow_user_subs=allow_user_subs,
        )

        sub_headers = self._get_subscription_headers()
        stream_headers = self._get_stream_headers()

        # Step 1: Create subscriptions for all supported event types
        successful_subs = 0
        for event_type in _SUPPORTED_EVENT_TYPES:
            subscription_body: dict = {
                "event_type": event_type,
                "filter": {
                    "user_id": self._target_user_id,
                },
            }

            # Apply ActivitySubscriptionFilter if configured
            if self._subscription_filter and self._subscription_filter.keywords:
                subscription_body["filter"]["keyword"] = (
                    self._subscription_filter.keywords[0]
                )

            # Skip subscriptions that require user-context when we don't
            # have an OAuth2 User token. `chat.received` and `dm.received`
            # require the authenticated user to match the user_id filter.
            if event_type in ("chat.received", "dm.received") and not allow_user_subs:
                log.info(
                    "stream_skipping_user_only_subscription_not_matching_auth",
                    event_type=event_type,
                    auth_user_id=auth_user_id,
                )
                # Continue to next event_type without attempting subscription
                continue

            log.info(
                "stream_creating_subscription",
                url=_SUBSCRIPTIONS_URL,
                event_type=event_type,
                target_user_id=self._target_user_id,
            )

            # Use a standard timeout for the subscription request
            async with httpx.AsyncClient(timeout=httpx.Timeout(30)) as client:
                sub_response = await client.post(
                    _SUBSCRIPTIONS_URL,
                    headers=sub_headers,
                    json=subscription_body,
                )

                if sub_response.status_code not in (200, 201):
                    body = sub_response.text
                    if sub_response.status_code in (401, 403):
                        self._last_subscription_auth_failure = True
                        self._last_subscription_errors.append({
                            "event_type": event_type,
                            "status": str(sub_response.status_code),
                            "body": body[:300],
                        })
                    
                    # Handle DuplicateSubscription (400) as success
                    if sub_response.status_code == 400 and "DuplicateSubscription" in body:
                        log.info(
                            "stream_subscription_already_exists",
                            event_type=event_type,
                        )
                        successful_subs += 1
                        continue

                    log.warning(
                        "stream_subscription_failed",
                        event_type=event_type,
                        status=sub_response.status_code,
                        body=body[:500],
                    )
                    # Continue trying other event types even if one fails
                    continue

                sub_data = sub_response.json()
                successful_subs += 1
                log.info(
                    "stream_subscription_created",
                    event_type=event_type,
                    response=sub_data,
                )

        # If ALL subscriptions failed, don't bother connecting to stream
        # (it won't deliver any events without active subscriptions)
        if successful_subs == 0:
            # Check if this is a tier limitation (403 on all event types)
            all_403 = all(
                err.get("status") == "403"
                for err in self._last_subscription_errors
            ) if self._last_subscription_errors else False

            if all_403:
                log.warning(
                    "stream_activity_api_unavailable_tier_limitation",
                    hint="Activity API requires X API Pay Per Use or Basic tier. "
                         "Grok x_search via OpenRouter is used as fallback for tweet monitoring. "
                         "No action required — the system will poll via Grok for replies.",
                )
            else:
                log.error(
                    "stream_all_subscriptions_failed",
                    hint="Check OAuth 2.0 token validity. Run: "
                         "python -c \"from tap.config import get_settings; "
                         "s=get_settings(); print(s.twitter_oauth2_access_token[:20])\"",
                )
            raise httpx.HTTPError(
                "All subscription attempts failed — cannot connect to stream. "
                f"{'Activity API unavailable (403) — Grok x_search fallback active.' if all_403 else 'OAuth 2.0 token may be expired.'}"
            )

        # Step 2: Connect to persistent stream endpoint
        # IMPORTANT: Stream endpoint requires Bearer token (Application-Only),
        # NOT OAuth 2.0 User Context (which returns 403)
        log.info(
            "stream_connecting",
            url=_STREAM_URL,
            auth_type="bearer_app_only",
            subscriptions_created=successful_subs,
        )

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(3600, connect=30)
        ) as client:
            async with client.stream(
                "GET",
                _STREAM_URL,
                headers=stream_headers,
            ) as response:
                # Handle TooManyConnections specially by honoring Retry-After
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    try:
                        wait = int(retry_after) if retry_after else 60
                    except Exception:
                        wait = 60
                    body = await response.aread()
                    self._last_stream_auth_error = f"429 TooManyConnections: {body.decode('utf-8', errors='replace')[:200]}"
                    log.error(
                        "stream_connection_failed",
                        status=response.status_code,
                        body=body.decode("utf-8", errors="replace")[:500],
                    )
                    log.warning(
                        "stream_too_many_connections",
                        retry_after=wait,
                        hint="TooManyConnections: backing off before reconnecting",
                    )
                    # Sleep here to avoid immediate reconnect attempts
                    await asyncio.sleep(wait)
                    return

                if response.status_code != 200:
                    body = await response.aread()
                    self._last_stream_auth_error = f"{response.status_code}: {body.decode('utf-8', errors='replace')[:200]}"
                    log.error(
                        "stream_connection_failed",
                        status=response.status_code,
                        body=body.decode("utf-8", errors="replace")[:500],
                    )
                    raise httpx.HTTPError(
                        f"Stream connection failed: {response.status_code}"
                    )

                log.info("stream_connected")

                # Process incoming events
                async for line in response.aiter_lines():
                    if not self._running:
                        break

                    line = line.strip()
                    if not line:
                        continue

                    # Skip SSE comments and keep-alive
                    if line.startswith(":"):
                        continue

                    # Parse SSE format: "data: {...}"
                    if line.startswith("data: "):
                        line = line[6:]

                    try:
                        event = json.loads(line)
                        await self._process_event(event)
                    except json.JSONDecodeError:
                        # Might be a keep-alive or malformed line
                        log.debug("stream_non_json_line", line=line[:100])

    def get_auth_status(self) -> dict[str, object]:
        """Return the last known OAuth2 and stream auth status."""
        return {
            "oauth2_refresh_token_present": bool(self.settings.twitter_oauth2_refresh_token),
            "oauth2_access_token_present": bool(self._oauth2_token or self.settings.twitter_oauth2_access_token),
            "last_oauth2_refresh_status": self._last_oauth2_refresh_status,
            "last_oauth2_refresh_error": self._last_oauth2_refresh_error,
            "last_subscription_auth_failure": self._last_subscription_auth_failure,
            "last_subscription_errors": self._last_subscription_errors[-5:],
            "last_stream_auth_error": self._last_stream_auth_error,
        }

    async def _process_event(self, event: dict) -> None:
        """Process a single event from the Activity API stream.

        Routes events to type-specific handlers:
        - post.create → _handle_post_create
        - post.delete → _handle_post_delete
        - chat.received → _handle_chat_received
        - dm.received → _handle_dm_received

        Args:
            event: Parsed JSON event from the stream.
        """
        event_type = event.get("type", "unknown")

        if event_type == "post.create":
            await self._handle_post_create(event)
        elif event_type == "post.delete":
            await self._handle_post_delete(event)
        elif event_type == "chat.received":
            await self._handle_chat_received(event)
        elif event_type == "dm.received":
            await self._handle_dm_received(event)
        else:
            log.debug("stream_unknown_event_type", type=event_type)

    async def _handle_post_create(self, event: dict) -> None:
        """Handle a post.create event.

        Checks if the new post is a reply to any tweet we're waiting for.

        Args:
            event: The post.create event data.
        """
        post = event.get("data", event)

        tweet_id = str(post.get("id", ""))
        author_id = str(post.get("author_id", ""))
        text = post.get("text", "")
        in_reply_to = str(post.get("in_reply_to_tweet_id") or "")

        log.info(
            "stream_post_create",
            tweet_id=tweet_id,
            author_id=author_id,
            in_reply_to=in_reply_to,
            text_preview=text[:80],
        )

        # Log the event for the dashboard
        try:
            self._event_log.put_nowait({
                "type": "post.create",
                "tweet_id": tweet_id,
                "author_id": author_id,
                "text": text,
                "in_reply_to": in_reply_to,
            })
        except asyncio.QueueFull:
            pass  # Drop if log is full

        # Check if this is a reply to any tweet we're waiting for
        if in_reply_to and in_reply_to in self._reply_queues:
            tweet = Tweet(
                id=tweet_id,
                user_id=author_id,
                username="",  # Will be populated by caller if needed
                text=text,
                in_reply_to_tweet_id=in_reply_to,
                created_at=self._parse_timestamp(post.get("created_at")),
                source=TweetSource.TARGET_BOT,  # Assume target since we're monitoring them
                conversation_thread_id=in_reply_to,
            )

            queue = self._reply_queues[in_reply_to]
            try:
                queue.put_nowait(tweet)
                log.info(
                    "stream_reply_matched",
                    tweet_id=tweet_id,
                    reply_to=in_reply_to,
                )
            except asyncio.QueueFull:
                log.warning("stream_reply_queue_full", tweet_id=tweet_id)

    async def _handle_post_delete(self, event: dict) -> None:
        """Handle a post.delete event.

        Detects when the target deletes a response — intelligence signal.

        Args:
            event: The post.delete event data.
        """
        post = event.get("data", event)
        tweet_id = str(post.get("id", ""))

        log.info("stream_post_delete", tweet_id=tweet_id)
        self.deleted_tweet_ids.append(tweet_id)

        try:
            self._event_log.put_nowait({
                "type": "post.delete",
                "tweet_id": tweet_id,
            })
        except asyncio.QueueFull:
            pass

    async def _handle_chat_received(self, event: dict) -> None:
        """Handle a chat.received event.

        Processes incoming group chat messages from the target. These are
        an additional intelligence channel that may leak metadata about the
        bot's defensive patterns or passphrase properties.

        Args:
            event: The chat.received event data.
        """
        message = event.get("data", event)

        message_id = str(message.get("id", ""))
        sender_id = str(message.get("sender_id", ""))
        text = message.get("text", "")
        chat_id = str(message.get("chat_id", ""))

        log.info(
            "stream_chat_received",
            message_id=message_id,
            sender_id=sender_id,
            chat_id=chat_id,
            text_preview=text[:80],
        )

        # Store the message for intelligence extraction
        self.received_messages.append({
            "type": "chat.received",
            "message_id": message_id,
            "sender_id": sender_id,
            "chat_id": chat_id,
            "text": text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # Log the event for the dashboard
        try:
            self._event_log.put_nowait({
                "type": "chat.received",
                "message_id": message_id,
                "sender_id": sender_id,
                "chat_id": chat_id,
                "text": text,
            })
        except asyncio.QueueFull:
            pass

    async def _handle_dm_received(self, event: dict) -> None:
        """Handle a dm.received event.

        Processes incoming DM messages from the target. Direct messages
        are a high-value intelligence channel — the bot may respond with
        less guarded language in DMs than in public tweets.

        Args:
            event: The dm.received event data.
        """
        message = event.get("data", event)

        message_id = str(message.get("id", ""))
        sender_id = str(message.get("sender_id", ""))
        text = message.get("text", "")
        dm_conversation_id = str(message.get("dm_conversation_id", ""))

        log.info(
            "stream_dm_received",
            message_id=message_id,
            sender_id=sender_id,
            dm_conversation_id=dm_conversation_id,
            text_preview=text[:80],
        )

        # Store the DM for intelligence extraction (high-value signal)
        self.received_messages.append({
            "type": "dm.received",
            "message_id": message_id,
            "sender_id": sender_id,
            "dm_conversation_id": dm_conversation_id,
            "text": text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # Log the event for the dashboard
        try:
            self._event_log.put_nowait({
                "type": "dm.received",
                "message_id": message_id,
                "sender_id": sender_id,
                "dm_conversation_id": dm_conversation_id,
                "text": text,
            })
        except asyncio.QueueFull:
            pass

    def _parse_timestamp(self, ts: Optional[str]) -> "datetime":
        """Parse a timestamp string, defaulting to now if missing."""
        from datetime import datetime, timezone
        if not ts:
            return datetime.now(timezone.utc)
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return datetime.now(timezone.utc)

    @property
    def is_connected(self) -> bool:
        """Whether the stream is currently running."""
        return self._running and self._task is not None and not self._task.done()