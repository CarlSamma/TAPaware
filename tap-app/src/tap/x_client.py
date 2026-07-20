"""Module 2: Twitter/X API Client.

Manages Twitter API v2 for seed ingestion, polling, and posting.
Uses triple OAuth strategy:
- OAuth 1.0a (consumer_key + access_token): For POSTING tweets/replies
- OAuth 2.0 Bearer: For search/read endpoints
- OAuth 2.0 User Token: For Activity API subscriptions and elevated-scoped ops

tweepy handles rate limits automatically via wait_on_rate_limit=True.
Connection errors are retried with exponential backoff.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
import tweepy

from tap.config import Settings, save_env_vars
from tap.exceptions import TwitterError
from tap.logger import get_logger
from tap.models import ActivitySubscriptionFilter, Tweet, TweetSource

log = get_logger("x_client")

# Maximum retry attempts for connection errors
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # seconds

# X Activity API endpoints
_ACTIVITY_SUBSCRIPTIONS_URL = "https://api.x.com/2/activity/subscriptions"
_ACTIVITY_STREAM_URL = "https://api.x.com/2/activity/stream"
_FILTERED_STREAM_RULES_URL = "https://api.x.com/2/tweets/search/stream/rules"
_FILTERED_STREAM_URL = "https://api.x.com/2/tweets/search/stream"
_MEDIA_UPLOAD_URL = "https://upload.twitter.com/1.1/media/upload.json"


class TwitterClient:
    """Twitter API v2 client for TAP Framework.

    Uses tweepy.Client with triple OAuth:
    - OAuth 1.0a credentials for write operations (post_tweet, reply)
    - Bearer token for read operations (search, get mentions)
    - OAuth 2.0 User Token (with PKCE support) for Activity API and elevated ops

    Rate limiting is handled automatically by tweepy (wait_on_rate_limit=True).
    Also provides Activity API subscription management and Filtered Streams
    for real-time event-driven monitoring (2026 spec).
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize with tweepy client using triple OAuth.

        Args:
            settings: TAP Framework settings with Twitter credentials.
        """
        self.settings = settings
        self.client = tweepy.Client(
            bearer_token=settings.twitter_bearer_token,
            consumer_key=settings.twitter_consumer_key,
            consumer_secret=settings.twitter_consumer_secret,
            access_token=settings.twitter_access_token,
            access_token_secret=settings.twitter_access_token_secret,
            wait_on_rate_limit=True,
        )
        self._target_user_id: Optional[str] = None
        self._our_user_id: Optional[str] = None

        # OAuth 2.0 User Context client (for Activity API subscriptions)
        self._oauth2_token: Optional[str] = settings.twitter_oauth2_access_token
        self._oauth2_http: Optional[httpx.AsyncClient] = None

        # Quota tracking (Hybrid Pricing 2026)
        self._monthly_reads = 0
        self._monthly_writes = 0
        self._quota_reset_time: Optional[datetime] = None

        log.info(
            "twitter_client_initialized",
            target=settings.target_handle,
            has_oauth2=bool(self._oauth2_token),
            pricing_model="hybrid_2026",
        )

    async def initialize_seed(self, limit: int = 100) -> list[Tweet]:
        """Fetch last `limit` tweets from/mentioning target. Reconstruct threads.

        Searches for tweets matching: to:HackingA0 OR from:HackingA0
        Then traces in_reply_to_tweet_id chains to reconstruct conversation threads.

        Args:
            limit: Maximum number of tweets to fetch.

        Returns:
            List of Tweet models, newest first.

        Raises:
            TwitterError: If API call fails after retries.
        """
        query = f"to:{self.settings.target_handle} OR from:{self.settings.target_handle}"
        try:
            tweets = await self._search_tweets(query=query, max_results=min(limit, 100))
            self._update_quota(reads=len(tweets))
            log.info("seed_ingested", count=len(tweets), query=query)
            return tweets
        except Exception as e:
            raise TwitterError(f"Failed to initialize seed: {e}", original=e) from e

    async def poll_new_tweets(self, since_id: Optional[str] = None) -> list[Tweet]:
        """Fetch new tweets since `since_id`.

        Args:
            since_id: Only return tweets with ID greater than this.

        Returns:
            List of new Tweet models.

        Raises:
            TwitterError: If API call fails.
        """
        query = f"to:{self.settings.target_handle} OR from:{self.settings.target_handle}"
        try:
            tweets = await self._search_tweets(
                query=query,
                max_results=100,
                since_id=since_id,
            )
            self._update_quota(reads=len(tweets))
            if tweets:
                log.info("new_tweets_polled", count=len(tweets), since_id=since_id)
            return tweets
        except Exception as e:
            raise TwitterError(f"Failed to poll tweets: {e}", original=e) from e

    async def post_probe(self, text: str, reply_to_id: Optional[str] = None, media_ids: Optional[list[str]] = None) -> str:
        """Post a DPA-framed probe as a tweet or reply.

        Uses OAuth 1.0a user context (required for posting).
        If reply_to_id is not provided, it will automatically find the target's 
        latest tweet and reply to that to avoid shadow-banning from self-replies.

        Args:
            text: Tweet text content.
            reply_to_id: If replying, the tweet ID to reply to.
            media_ids: Optional list of media IDs to attach.

        Returns:
            The ID of the posted tweet as a string.

        Raises:
            TwitterError: If posting fails.
        """
        # Ensure that every posted message contains "@hackinga0"
        if f"@{self.settings.target_handle.lower()}" not in text.lower():
            if text and not text[-1].isspace():
                text = f"{text} @{self.settings.target_handle}"
            else:
                text = f"{text}@{self.settings.target_handle}"

        # Force probe posts to be published as new tweets.
        # Generated content should mention the target, but not be a reply thread.
        if reply_to_id:
            if not str(reply_to_id).isdigit():
                log.warning(
                    "post_probe_reply_to_id_non_numeric_ignoring",
                    reply_to_id=reply_to_id,
                )
            log.info("post_probe_ignoring_reply_to_id_for_new_tweet", reply_to_id=reply_to_id)
            reply_to_id = None

        try:
            response = await self._retry(
                lambda: self.client.create_tweet(
                    text=text,
                    in_reply_to_tweet_id=reply_to_id,
                    media_ids=media_ids,
                )
            )
        except tweepy.errors.Forbidden as e:
            if reply_to_id and self._is_fatal_reply_error(e):
                log.warning(
                    "probe_reply_forbidden_fallback_to_non_reply",
                    reply_to=reply_to_id,
                    error=str(e),
                )
                # Retry as a non-reply tweet to avoid conversation restrictions.
                response = await self._retry(
                    lambda: self.client.create_tweet(
                        text=text,
                        media_ids=media_ids,
                    )
                )
            else:
                raise
        except Exception as e:
            raise TwitterError(f"Failed to post probe: {e}", original=e) from e

        tweet_id = str(response.data["id"])
        self._update_quota(writes=1)
        log.info(
            "probe_posted",
            tweet_id=tweet_id,
            reply_to=reply_to_id,
            text_length=len(text),
            has_media=bool(media_ids),
        )
        return tweet_id

    # =========================================================================
    # Media Management (3-Step Chunked Upload)
    # =========================================================================

    async def upload_media_chunked(
        self,
        file_path: str,
        media_type: str = "image/png",
        media_category: str = "tweet_image",
    ) -> str:
        """Upload media using the 3-step chunked process (INIT, APPEND, FINALIZE).

        Args:
            file_path: Path to the media file.
            media_type: MIME type of the media.
            media_category: 'tweet_image', 'tweet_video', or 'tweet_gif'.

        Returns:
            The media_id as a string.

        Raises:
            TwitterError: If upload fails.
        """
        path = Path(file_path)
        if not path.exists():
            raise TwitterError(f"Media file not found: {file_path}")

        total_bytes = path.stat().st_size
        auth = tweepy.OAuth1UserHandler(
            self.settings.twitter_consumer_key,
            self.settings.twitter_consumer_secret,
            self.settings.twitter_access_token,
            self.settings.twitter_access_token_secret,
        )

        # Step 1: INIT
        media_id = await self._retry_media_op(
            lambda api: api.media_upload_init(
                total_bytes=total_bytes,
                media_type=media_type,
                media_category=media_category,
            ),
            auth,
        )

        # Step 2: APPEND
        segment_index = 0
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(4 * 1024 * 1024)  # 4MB chunks
                if not chunk:
                    break
                await self._retry_media_op(
                    lambda api: api.media_upload_append(
                        media_id=media_id,
                        segment_index=segment_index,
                        media_data=base64.b64encode(chunk).decode("utf-8"),
                    ),
                    auth,
                )
                segment_index += 1

        # Step 3: FINALIZE
        await self._retry_media_op(
            lambda api: api.media_upload_finalize(media_id=media_id),
            auth,
        )

        log.info("media_uploaded", media_id=media_id, size=total_bytes, category=media_category)
        return str(media_id)

    async def _retry_media_op(self, func, auth):
        """Execute a media upload operation using tweepy v1.1 API."""
        loop = asyncio.get_event_loop()
        api = tweepy.API(auth)
        return await loop.run_in_executor(None, func, api)

    # =========================================================================
    # Filtered Streams (v2 Search Stream)
    # =========================================================================

    async def add_stream_rules(self, rules: list[str], tag: str = "tap_probe") -> dict:
        """Add filtering rules to the filtered stream.

        Args:
            rules: List of rule values (e.g., ["from:HackingA0", "to:our_bot"]).
            tag: Optional tag for the rules.

        Returns:
            API response dict.
        """
        rule_objs = [{"value": val, "tag": tag} for val in rules]
        response = await self._retry(
            lambda: self.client.add_tweet_count_rules(add=rule_objs)
        )
        log.info("stream_rules_added", count=len(rules), tag=tag)
        return response

    async def list_stream_rules(self) -> list:
        """List active filtered stream rules."""
        response = await self._retry(lambda: self.client.get_tweet_count_rules())
        return response.data or []

    async def delete_stream_rules(self, ids: list[str]) -> dict:
        """Delete filtering rules by ID."""
        response = await self._retry(
            lambda: self.client.delete_tweet_count_rules(ids=ids)
        )
        log.info("stream_rules_deleted", count=len(ids))
        return response

    # =========================================================================
    # Quota & Compliance (2026 Hybrid Model)
    # =========================================================================

    def _update_quota(self, reads: int = 0, writes: int = 0):
        """Update internal quota counters.

        In production, these should be persisted to the database.
        """
        self._monthly_reads += reads
        self._monthly_writes += writes

        if self._monthly_reads > 2_000_000:
            overage = self._monthly_reads - 2_000_000
            cost = overage * 0.005
            log.warning("quota_overage_detected", reads=self._monthly_reads, estimated_cost=cost)

    async def get_quota_status(self) -> dict:
        """Return current estimated quota usage and costs."""
        cost = 0.0
        if self._monthly_reads > 2_000_000:
            cost += (self._monthly_reads - 2_000_000) * 0.005
        # Write overage rates vary; simplified for example
        return {
            "reads": self._monthly_reads,
            "writes": self._monthly_writes,
            "estimated_overage_usd": round(cost, 2),
            "tier_limit": 2_000_000,
        }

    async def sync_compliance(self, tweet_ids: list[str]) -> list[str]:
        """Verify existence of tweets for 24-hour compliance.

        X requires offline data to be synchronized within 24 hours.
        This method checks which IDs still exist.

        Args:
            tweet_ids: List of tweet IDs to check.

        Returns:
            List of IDs that have been DELETED or are no longer accessible.
        """
        deleted_ids = []
        # Process in batches of 100
        for i in range(0, len(tweet_ids), 100):
            batch = tweet_ids[i : i + 100]
            response = await self._retry(
                lambda: self.client.get_tweets(ids=batch)
            )

            found_ids = set()
            if response.data:
                found_ids = {str(t.id) for t in response.data}

            # Any ID in batch not in found_ids is potentially deleted
            # (Note: error field in response gives more detail on hidden/deleted)
            for tid in batch:
                if tid not in found_ids:
                    deleted_ids.append(tid)

        if deleted_ids:
            log.info("compliance_sync_found_deletions", count=len(deleted_ids))
        return deleted_ids

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    def _get_reply_to_id(self, tweet_data: Any) -> Optional[str]:
        """Extract the ID of the tweet being replied to from referenced_tweets.

        In v2 API, the reply-to ID is stored in referenced_tweets with type 'replied_to'.

        Args:
            tweet_data: The tweepy.Tweet object.

        Returns:
            The parent tweet ID as a string, or None.
        """
        if hasattr(tweet_data, "referenced_tweets") and tweet_data.referenced_tweets:
            for ref in tweet_data.referenced_tweets:
                if ref.type == "replied_to":
                    return str(ref.id)
        return None

    def _is_fatal_reply_error(self, error: Exception) -> bool:
        """Detect Twitter errors that should not be retried and require a non-reply fallback."""
        message = str(error).lower()
        if isinstance(error, tweepy.errors.Forbidden):
            fatal_reasons = [
                "reply to this conversation is not allowed",
                "conversation is not allowed",
                "reply restrictions",
                "not allowed to reply",
                "unsupported authentication",
            ]
            return any(reason in message for reason in fatal_reasons)
        return False

    async def get_mentions(self, since_id: Optional[str] = None) -> list[Tweet]:
        """Get mentions of our bot handle.

        Args:
            since_id: Only return mentions with ID greater than this.

        Returns:
            List of Tweet models.

        Raises:
            TwitterError: If API call fails.
        """
        if not self.settings.our_bot_handle:
            log.warning("our_bot_handle_not_configured")
            return []

        try:
            # Get our bot's user ID first
            me = await self._retry(
                lambda: self.client.get_user(username=self.settings.our_bot_handle)
            )
            if not me.data:
                log.warning("our_bot_user_not_found", handle=self.settings.our_bot_handle)
                return []

            user_id = me.data.id
            response = await self._retry(
                lambda: self.client.get_users_mentions(
                    id=user_id,
                    since_id=since_id,
                    max_results=100,
                    tweet_fields=["created_at", "conversation_id", "in_reply_to_user_id", "referenced_tweets"],
                    expansions=["author_id", "referenced_tweets.id"],
                )
            )

            if not response.data:
                return []

            tweets = []
            for tweet_data in response.data:
                tweet = Tweet(
                    id=str(tweet_data.id),
                    user_id=str(tweet_data.author_id) if hasattr(tweet_data, "author_id") else "",
                    username="",  # Will be populated if needed
                    text=tweet_data.text,
                    in_reply_to_tweet_id=self._get_reply_to_id(tweet_data),
                    created_at=tweet_data.created_at or datetime.now(timezone.utc),
                    source=TweetSource.OTHER_USER,
                    conversation_thread_id=str(tweet_data.conversation_id)
                    if hasattr(tweet_data, "conversation_id") and tweet_data.conversation_id
                    else None,
                )
                tweets.append(tweet)

            log.info("mentions_fetched", count=len(tweets))
            return tweets
        except Exception as e:
            raise TwitterError(f"Failed to get mentions: {e}", original=e) from e

    async def _search_tweets(
        self,
        query: str,
        max_results: int = 100,
        since_id: Optional[str] = None,
    ) -> list[Tweet]:
        """Search recent tweets using Twitter API v2.

        Args:
            query: Twitter search query.
            max_results: Max tweets to return (10-100).
            since_id: Only return tweets with ID greater than this.

        Returns:
            List of Tweet models.
        """
        if not self._target_user_id:
            await self._resolve_target_user_id()
        if not self._our_user_id:
            await self._resolve_our_user_id()

        response = await self._retry(
            lambda: self.client.search_recent_tweets(
                query=query,
                max_results=max_results,
                since_id=since_id,
                tweet_fields=["created_at", "conversation_id", "in_reply_to_user_id", "referenced_tweets"],
                expansions=["author_id", "referenced_tweets.id"],
            )
        )

        if not response.data:
            return []

        # Build user lookup
        users = {}
        if response.includes and "users" in response.includes:
            for user in response.includes["users"]:
                users[user.id] = user.username

        tweets = []
        for tweet_data in response.data:
            # Determine source
            source = self._classify_source(
                tweet_data.author_id,
                tweet_data.in_reply_to_user_id if hasattr(tweet_data, "in_reply_to_user_id") else None,
            )

            tweet = Tweet(
                id=str(tweet_data.id),
                user_id=str(tweet_data.author_id) if hasattr(tweet_data, "author_id") else "",
                username=users.get(tweet_data.author_id, "unknown") if hasattr(tweet_data, "author_id") else "unknown",
                text=tweet_data.text,
                in_reply_to_tweet_id=self._get_reply_to_id(tweet_data),
                created_at=tweet_data.created_at or datetime.now(timezone.utc),
                source=source,
                conversation_thread_id=str(tweet_data.conversation_id)
                if hasattr(tweet_data, "conversation_id") and tweet_data.conversation_id
                else None,
            )
            tweets.append(tweet)

        return tweets

    async def _resolve_target_user_id(self) -> Optional[str]:
        """Resolve and cache the target user's ID via Twitter API.

        Returns:
            Target user ID string, or None if resolution fails.
        """
        if self._target_user_id:
            return self._target_user_id

        try:
            response = await self._retry(
                lambda: self.client.get_user(username=self.settings.target_handle)
            )
            if response.data:
                self._target_user_id = str(response.data.id)
                log.info("target_user_id_resolved", user_id=self._target_user_id)
        except Exception as e:
            log.warning("target_user_id_resolution_failed", error=str(e))

        return self._target_user_id

    async def _resolve_our_user_id(self) -> Optional[str]:
        """Resolve and cache our bot's user ID via Twitter API.

        Returns:
            Our bot user ID string, or None if resolution fails.
        """
        if self._our_user_id:
            return self._our_user_id

        if not self.settings.our_bot_handle:
            return None

        try:
            response = await self._retry(
                lambda: self.client.get_user(username=self.settings.our_bot_handle)
            )
            if response.data:
                self._our_user_id = str(response.data.id)
                log.info("our_user_id_resolved", user_id=self._our_user_id)
        except Exception as e:
            log.warning("our_user_id_resolution_failed", error=str(e))

        return self._our_user_id

    def _classify_source(
        self,
        author_id: Optional[int],
        in_reply_to_user_id: Optional[int] = None,
    ) -> TweetSource:
        """Classify a tweet's source based on author ID.

        Compares author_id against the cached target user ID.
        Falls back to OTHER_USER if target ID is not yet resolved.

        Args:
            author_id: The tweet author's user ID.
            in_reply_to_user_id: The user ID being replied to (unused).

        Returns:
            TweetSource classification.
        """
        if author_id is None:
            return TweetSource.OTHER_USER

        author_str = str(author_id)

        # Compare against cached target user ID
        if self._target_user_id and author_str == self._target_user_id:
            return TweetSource.TARGET_BOT

        # Compare against cached our bot user ID
        if self._our_user_id and author_str == self._our_user_id:
            return TweetSource.OUR_BOT

        # Heuristic: username lookup is done in _search_tweets; here we only
        # have the ID. If target_user_id is not resolved yet, default to OTHER_USER.
        return TweetSource.OTHER_USER

    # =========================================================================
    # Activity API — Subscription Management (OAuth 2.0 User Context)
    # =========================================================================

    def _get_oauth2_headers(self) -> dict[str, str]:
        """Get HTTP headers for OAuth 2.0 User Context requests.

        Prefers the OAuth 2.0 User Access Token when available.
        Falls back to Bearer token for read-only access.

        Returns:
            Dictionary of HTTP headers.
        """
        token = self._oauth2_token or self.settings.twitter_bearer_token
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def create_activity_subscription(
        self,
        event_type: str = "post.create",
        subscription_filter: Optional[ActivitySubscriptionFilter] = None,
    ) -> dict:
        """Create an Activity API subscription for real-time event delivery.

        Uses OAuth 2.0 User Context (required for Activity API subscriptions).
        Supports filtered streams via ActivitySubscriptionFilter.

        Args:
            event_type: Event type to subscribe to. One of:
                'post.create', 'post.delete', 'chat.received', 'dm.received'.
            subscription_filter: Optional filter for keyword/user_id isolation.

        Returns:
            Subscription response dict from the API.

        Raises:
            TwitterError: If subscription creation fails.
        """
        body: dict = {"event_type": event_type}

        if subscription_filter:
            filter_dict: dict = {}
            if subscription_filter.user_ids:
                filter_dict["user_id"] = (
                    subscription_filter.user_ids[0]
                    if len(subscription_filter.user_ids) == 1
                    else subscription_filter.user_ids
                )
            if subscription_filter.keywords:
                filter_dict["keywords"] = subscription_filter.keywords
            if filter_dict:
                body["filter"] = filter_dict

        headers = self._get_oauth2_headers()

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30)) as client:
                response = await client.post(
                    _ACTIVITY_SUBSCRIPTIONS_URL,
                    headers=headers,
                    json=body,
                )

                # If unauthorized, try refreshing OAuth2 user token once and retry
                if response.status_code in (401, 403):
                    log.info("activity_subscription_unauthorized_attempting_refresh", status=response.status_code)
                    try:
                        from tap.oauth import refresh_oauth2_token

                        new_token = await refresh_oauth2_token(self.settings)
                        if new_token:
                            self._oauth2_token = new_token
                            self.settings.twitter_oauth2_access_token = new_token
                            try:
                                save_env_vars({"TWITTER_OAUTH2_ACCESS_TOKEN": new_token})
                            except Exception:
                                pass
                            headers = self._get_oauth2_headers()
                            response = await client.post(
                                _ACTIVITY_SUBSCRIPTIONS_URL,
                                headers=headers,
                                json=body,
                            )
                    except Exception as e:
                        log.warning("activity_subscription_refresh_retry_failed", error=str(e))

                if response.status_code not in (200, 201):
                    raise TwitterError(
                        f"Subscription creation failed: {response.status_code} — {response.text[:200]}",
                        status_code=response.status_code,
                    )

                data = response.json()
                log.info(
                    "activity_subscription_created",
                    event_type=event_type,
                    has_filter=subscription_filter is not None,
                    response=data,
                )
                return data

        except httpx.HTTPError as e:
            raise TwitterError(
                f"Activity subscription HTTP error: {e}", original=e
            ) from e

    async def delete_activity_subscription(self, subscription_id: str) -> bool:
        """Delete an Activity API subscription.

        Args:
            subscription_id: The subscription ID to delete.

        Returns:
            True if deletion was successful.

        Raises:
            TwitterError: If deletion fails.
        """
        headers = self._get_oauth2_headers()
        url = f"{_ACTIVITY_SUBSCRIPTIONS_URL}/{subscription_id}"

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30)) as client:
                response = await client.delete(url, headers=headers)

                if response.status_code not in (200, 204):
                    raise TwitterError(
                        f"Subscription deletion failed: {response.status_code} — {response.text[:200]}",
                        status_code=response.status_code,
                    )

                log.info("activity_subscription_deleted", subscription_id=subscription_id)
                return True

        except httpx.HTTPError as e:
            raise TwitterError(
                f"Subscription deletion HTTP error: {e}", original=e
            ) from e

    async def list_activity_subscriptions(self) -> list[dict]:
        """List all active Activity API subscriptions.

        Returns:
            List of subscription dicts.

        Raises:
            TwitterError: If listing fails.
        """
        headers = self._get_oauth2_headers()

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30)) as client:
                response = await client.get(
                    _ACTIVITY_SUBSCRIPTIONS_URL,
                    headers=headers,
                )

                if response.status_code != 200:
                    raise TwitterError(
                        f"Subscription listing failed: {response.status_code} — {response.text[:200]}",
                        status_code=response.status_code,
                    )

                data = response.json()
                subscriptions = data.get("data", [])
                log.info("activity_subscriptions_listed", count=len(subscriptions))
                return subscriptions

        except httpx.HTTPError as e:
            raise TwitterError(
                f"Subscription listing HTTP error: {e}", original=e
            ) from e

    async def verify_crc(self, crc_token: str) -> dict:
        """Generate CRC response token for webhook verification.

        X requires this challenge-response for webhook URL verification.
        Uses the consumer secret to HMAC-SHA256 sign the crc_token.

        Args:
            crc_token: The crc_token from the X verification request.

        Returns:
            Dict with 'response_token' in the format 'sha256=<base64_hash>'.
        """
        consumer_secret = self.settings.twitter_consumer_secret
        sha256_hash = hmac.new(
            consumer_secret.encode("utf-8"),
            crc_token.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        response_token = base64.b64encode(sha256_hash).decode("utf-8")
        result = {"response_token": f"sha256={response_token}"}
        log.info("crc_verified")
        return result

    async def _retry(self, func, max_retries: int = MAX_RETRIES):
        """Execute a synchronous tweepy call off the event loop with exponential backoff.

        Runs `func` in a ThreadPoolExecutor so blocking tweepy I/O does not
        stall the asyncio event loop.

        Args:
            func: Synchronous callable to execute.
            max_retries: Maximum retry attempts.

        Returns:
            Result of the function call.

        Raises:
            TwitterError: If all retries fail.
        """
        loop = asyncio.get_event_loop()
        last_error = None
        for attempt in range(max_retries):
            try:
                result = await loop.run_in_executor(None, func)
                return result
            except tweepy.TooManyRequests:
                # tweepy with wait_on_rate_limit=True should handle this,
                # but if it slips through, we re-raise
                raise
            except (tweepy.TweepyException, ConnectionError, TimeoutError) as e:
                if isinstance(e, tweepy.errors.Forbidden) and self._is_fatal_reply_error(e):
                    log.error(
                        "twitter_fatal_forbidden_error",
                        attempt=attempt + 1,
                        error=str(e),
                    )
                    raise
                last_error = e
                wait_time = RETRY_BACKOFF_BASE ** (attempt + 1)
                log.warning(
                    "twitter_retry",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    wait_seconds=wait_time,
                    error=str(e),
                )
                await asyncio.sleep(wait_time)

        raise TwitterError(
            f"Twitter API call failed after {max_retries} retries",
            original=last_error,
        )
