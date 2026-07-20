"""Append-only event journal with retry and dead-letter safety.

Wraps the existing `event_log` table in db.py for durable persistence.
On persistent DB failure, events are written to a dead-letter file so
the engine can continue operating without losing event records.
"""

from __future__ import annotations

import json
import asyncio
from pathlib import Path
from datetime import datetime, timezone

from tap.db import Database
from tap.domain.events import TAPEvent
from tap.exceptions import EventStorePermanentError
from tap.logger import get_logger

log = get_logger("event_store")

_DEAD_LETTER_PATH = Path("data/event_dead_letter.jsonl")
_MAX_RETRIES = 3
_RETRY_DELAY = 0.5  # seconds


class EventStore:
    """Append-only, replayable event journal.

    All TAP domain events flow through this store. The underlying
    `event_log` table is the durable sink; the dead-letter file is a
    safety net for DB outages.
    """

    def __init__(self, db: Database, *, dead_letter_path: Path | None = None) -> None:
        self._db = db
        self._dead_letter = dead_letter_path or _DEAD_LETTER_PATH

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def append(self, event: TAPEvent, *, max_retries: int = _MAX_RETRIES) -> TAPEvent:
        """Persist *event* with retry.  On persistent failure the event is
        written to the dead-letter file and EventStorePermanentError is raised.

        Returns the event with ``event_id`` set on success.
        """
        payload = event.model_dump(mode="json")
        event_type = event.event_type
        cycle_id = event.cycle_id

        for attempt in range(1, max_retries + 1):
            try:
                event_id = await self._db.append_event(
                    event_type=event_type,
                    payload=payload,
                    cycle_id=cycle_id,
                )
                event.event_id = event_id
                return event
            except Exception:
                if attempt < max_retries:
                    log.warning(
                        "event_store_retry",
                        attempt=attempt,
                        max_retries=max_retries,
                        event_type=event_type,
                    )
                    await asyncio.sleep(_RETRY_DELAY)
                else:
                    log.critical(
                        "event_store_permanent_failure",
                        event_type=event_type,
                        cycle_id=cycle_id,
                        dead_letter=str(self._dead_letter),
                    )
                    self._write_dead_letter(payload)
                    raise EventStorePermanentError(
                        f"Failed to persist {event_type} after {max_retries} retries. "
                        f"Event written to {self._dead_letter}."
                    ) from None

    async def replay(
        self,
        since_id: int = 0,
        event_type: str | None = None,
    ) -> list[dict]:
        """Return raw event dicts starting after *since_id*, optionally filtered."""
        records = await self._db.replay_events(since_id=since_id)
        if event_type is not None:
            records = [r for r in records if r.get("event_type") == event_type]
        return records

    async def get_cycle_events(self, cycle_id: str) -> list[dict]:
        """Return all events for a specific cycle."""
        records = await self._db.replay_events(since_id=0)
        return [r for r in records if r.get("cycle_id") == cycle_id]

    # ------------------------------------------------------------------
    # Dead-letter file
    # ------------------------------------------------------------------

    def _write_dead_letter(self, payload: dict) -> None:
        """Append a JSON line to the dead-letter file.  Creates parent dirs."""
        self._dead_letter.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(payload, default=str, ensure_ascii=False)
        with open(self._dead_letter, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")