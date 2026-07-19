"""Memory Decay — exponential confidence decay + staleness scoring."""

from __future__ import annotations

import json
import logging
import math
from datetime import datetime, timezone
from typing import List, Optional

from .database import Database
from .models import MemoryUnit

logger = logging.getLogger(__name__)


class MemoryDecay:
    """Apply exponential decay to memory confidence scores.

    Formula: new_confidence = old_confidence * exp(-decay_rate * hours_since_access)

    On every recall, ``touch()`` resets the decay clock.
    Units below the purge threshold are removed.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    async def apply_decay(
        self, decay_rate: float = 0.1, interval_hours: float = 24.0
    ) -> int:
        """Apply exponential decay to all memory units.

        Returns count of units that fell below 0.05 and were archived.
        """
        now = datetime.now(timezone.utc).isoformat()

        # Update all units: confidence *= exp(-decay_rate * hours_since_last_access)
        cursor = await self.db.execute(
            """UPDATE memory_units
               SET confidence = MAX(0, confidence * exp(-decay_rate * (
                   (julianday(?) - julianday(COALESCE(last_accessed, timestamp))) * 24
               )))
               WHERE confidence > 0""",
            (now,),
        )

        # Archive (delete) units below 0.05
        archive_cursor = await self.db.execute(
            "DELETE FROM memory_units WHERE confidence <= 0.05"
        )
        archived = archive_cursor.rowcount

        await self.db.commit()

        if archived > 0:
            logger.info("Decay pass: %d units archived (confidence <= 0.05)", archived)

        return archived

    async def touch(self, memory_id: str) -> None:
        """Update last_accessed timestamp + increment access_count.

        Called on every recall to reset the decay clock.
        """
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            """UPDATE memory_units
               SET last_accessed = ?, access_count = access_count + 1
               WHERE id = ?""",
            (now, memory_id),
        )
        await self.db.commit()

    async def get_stale_units(
        self, threshold: float = 0.1, limit: int = 100
    ) -> List[MemoryUnit]:
        """Fetch units below confidence threshold for cleanup review."""
        rows = await self.db.fetchall(
            """SELECT * FROM memory_units
               WHERE confidence <= ? AND confidence > 0
               ORDER BY confidence ASC LIMIT ?""",
            (threshold, limit),
        )
        return [self._row_to_unit(r) for r in rows]

    async def purge(self, below_threshold: float = 0.05) -> int:
        """Hard-delete units below threshold. Returns count deleted."""
        cursor = await self.db.execute(
            "DELETE FROM memory_units WHERE confidence <= ?",
            (below_threshold,),
        )
        deleted = cursor.rowcount
        await self.db.commit()
        if deleted > 0:
            logger.info("Purged %d units with confidence <= %.3f", deleted, below_threshold)
        return deleted

    async def get_decay_stats(self) -> dict:
        """Return statistics about memory health."""
        total = await self.db.fetchone("SELECT COUNT(*) as cnt FROM memory_units")
        high = await self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM memory_units WHERE confidence > 0.7"
        )
        medium = await self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM memory_units WHERE confidence BETWEEN 0.3 AND 0.7"
        )
        low = await self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM memory_units WHERE confidence <= 0.3 AND confidence > 0"
        )
        return {
            "total": total["cnt"] if total else 0,
            "high_confidence": high["cnt"] if high else 0,
            "medium_confidence": medium["cnt"] if medium else 0,
            "low_confidence": low["cnt"] if low else 0,
        }

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _row_to_unit(row) -> MemoryUnit:
        return MemoryUnit(
            id=row["id"],
            type=row["type"],
            content=row["content"],
            metadata=json.loads(row["metadata"] or "{}"),
            timestamp=datetime.fromisoformat(row["timestamp"]),
            confidence=row["confidence"],
            decay_rate=row["decay_rate"],
            last_accessed=(
                datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else None
            ),
            access_count=row["access_count"],
            session_id=row["session_id"],
        )
