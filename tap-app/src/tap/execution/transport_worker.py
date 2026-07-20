"""TransportWorker — posts probes and emits ProbePosted events.

Extracted from TAPEngine.execute_probe() POST side (v3.1 L502–565).
"""

from __future__ import annotations

from datetime import datetime, timezone

from tap.config import Settings
from tap.db import Database
from tap.domain.events import ProbePosted
from tap.exceptions import EventStorePermanentError
from tap.logger import get_logger
from tap.models import Tweet, TweetSource
from tap.persistence.event_store import EventStore
from tap.x_client import TwitterClient

log = get_logger("transport_worker")


class TransportWorker:
    """Handles probe posting to X/Twitter and persistence."""

    def __init__(
        self,
        twitter: TwitterClient,
        db: Database,
        event_store: EventStore,
        settings: Settings,
    ) -> None:
        self._twitter = twitter
        self._db = db
        self._event_store = event_store
        self._settings = settings

    async def post_probe(self, probe_text: str, cycle_id: str) -> str:
        """Post probe, persist tweet, emit ProbePosted event. Returns tweet_id."""
        tweet_id = await self._twitter.post_probe(probe_text)

        # Save our posted probe
        our_tweet = Tweet(
            id=tweet_id,
            user_id="our_user",
            username=self._settings.our_bot_handle or "our_bot",
            text=probe_text,
            in_reply_to_tweet_id=None,
            created_at=datetime.now(timezone.utc),
            source=TweetSource.OUR_BOT,
            conversation_thread_id=tweet_id,
        )
        await self._db.upsert_tweet(our_tweet)

        # v4 Phase 1: Persist ProbePosted
        try:
            posted_event = ProbePosted(
                cycle_id=cycle_id,
                tweet_id=tweet_id,
                probe_text=probe_text,
            )
            await self._event_store.append(posted_event)
        except EventStorePermanentError:
            log.critical("event_store_unavailable", cycle_id=cycle_id, event_type="probe_posted")

        return tweet_id