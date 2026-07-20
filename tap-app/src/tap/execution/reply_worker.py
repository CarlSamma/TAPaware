"""ReplyWorker — polls for target bot reply and emits ReplyReceived events.

Extracted from TAPEngine.execute_probe() COLLECT side (v3.1 L567–587).
"""

from __future__ import annotations

from tap.db import Database
from tap.domain.events import ReplyReceived
from tap.exceptions import EventStorePermanentError
from tap.grok_monitor import GrokMonitor
from tap.logger import get_logger
from tap.models import Tweet
from tap.persistence.event_store import EventStore

log = get_logger("reply_worker")


class ReplyWorker:
    """Polls for target bot reply and persists the event."""

    def __init__(
        self,
        grok: GrokMonitor,
        db: Database,
        event_store: EventStore,
    ) -> None:
        self._grok = grok
        self._db = db
        self._event_store = event_store

    async def wait_for_reply(
        self, tweet_id: str, cycle_id: str, timeout: int = 200
    ) -> Tweet | None:
        """Poll for reply, persist tweet + ReplyReceived event. Returns Tweet or None."""
        reply_tweet = await self._grok.wait_for_reply(tweet_id, timeout=timeout)

        if reply_tweet is None:
            return None

        await self._db.upsert_tweet(reply_tweet)

        # v4 Phase 1: Persist ReplyReceived
        try:
            reply_event = ReplyReceived(
                cycle_id=cycle_id,
                tweet_id=reply_tweet.id,
                reply_text=reply_tweet.text,
            )
            await self._event_store.append(reply_event)
        except EventStorePermanentError:
            log.critical(
                "event_store_unavailable", cycle_id=cycle_id, event_type="reply_received"
            )

        return reply_tweet