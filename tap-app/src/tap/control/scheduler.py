"""ProbeScheduler — enforces Oracle Protocol inter-probe latency.

Extracted from engine._enforce_probe_latency().
Latency duration is injected from ControlPolicy (which reads from Settings).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from tap.control.policy import ControlPolicy
from tap.db import Database
from tap.logger import get_logger

log = get_logger("probe_scheduler")


class ProbeScheduler:
    """Enforces minimum latency between consecutive probes."""

    def __init__(self, db: Database, policy: ControlPolicy) -> None:
        self._db = db
        self._policy = policy

    async def enforce_latency(self) -> None:
        """Sleep until minimum latency has elapsed since the last probe."""
        last = await self._db.get_latest_our_bot_tweet()
        if not last:
            return

        now = datetime.now(timezone.utc)
        elapsed = (now - last.created_at).total_seconds()
        min_latency = self._policy.oracle_latency_seconds

        if elapsed < min_latency:
            remaining = min_latency - elapsed
            log.info(
                "probe_latency_enforced",
                elapsed_seconds=int(elapsed),
                remaining_seconds=int(remaining),
                min_latency=min_latency,
            )
            await asyncio.sleep(remaining)

    async def time_until_next_probe(self) -> float:
        """Return seconds remaining before the next probe is legal (0 = ready)."""
        last = await self._db.get_latest_our_bot_tweet()
        if not last:
            return 0.0
        now = datetime.now(timezone.utc)
        elapsed = (now - last.created_at).total_seconds()
        remaining = self._policy.oracle_latency_seconds - elapsed
        return max(0.0, remaining)