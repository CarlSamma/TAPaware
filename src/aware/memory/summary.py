"""Summary Memory — compressed context for long conversations."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from .database import Database
from .models import MemoryUnit


class SummaryMemory:
    """Compressed summaries of long conversations and sessions.

    Maps to TAP's SSOT (Single Source of Truth) living markdown.
    """

    def __init__(self, db: Database, llm_client=None) -> None:
        self.db = db
        self.llm_client = llm_client

    async def store(self, unit: MemoryUnit) -> MemoryUnit:
        # Optionally compress via LLM
        if self.llm_client and len(unit.content) > 500:
            unit.content = await self._compress(unit.content)

        await self.db.execute(
            """INSERT OR REPLACE INTO memory_units
               (id, type, content, metadata, timestamp, confidence, decay_rate,
                last_accessed, access_count, session_id)
               VALUES (?, 'summary', ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                unit.id,
                unit.content,
                json.dumps(unit.metadata),
                unit.timestamp.isoformat(),
                unit.confidence,
                unit.decay_rate,
                (unit.last_accessed or unit.timestamp).isoformat(),
                unit.access_count,
                unit.session_id,
            ),
        )
        await self.db.commit()
        return unit

    async def recall(
        self, query: str, limit: int = 10, threshold: float = 0.5
    ) -> List[Tuple[MemoryUnit, float]]:
        """Return most recent summaries matching keyword."""
        rows = await self.db.fetchall(
            """SELECT * FROM memory_units
               WHERE type = 'summary' AND (content LIKE ? OR metadata LIKE ?)
               ORDER BY timestamp DESC LIMIT ?""",
            (f"%{query}%", f"%{query}%", limit),
        )
        return [(MemoryUnit.from_row(r), 0.7) for r in rows]

    async def get(self, memory_id: str) -> Optional[MemoryUnit]:
        row = await self.db.fetchone(
            "SELECT * FROM memory_units WHERE id = ? AND type = 'summary'",
            (memory_id,),
        )
        return MemoryUnit.from_row(row) if row else None

    async def delete(self, memory_id: str) -> bool:
        cursor = await self.db.execute(
            "DELETE FROM memory_units WHERE id = ? AND type = 'summary'",
            (memory_id,),
        )
        await self.db.commit()
        return cursor.rowcount > 0

    async def count(self) -> int:
        row = await self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM memory_units WHERE type = 'summary'"
        )
        return row["cnt"] if row else 0

    async def apply_decay(self) -> int:
        now = datetime.now(timezone.utc).isoformat()
        cursor = await self.db.execute(
            """UPDATE memory_units
               SET confidence = confidence * exp(-decay_rate * (
                   (julianday(?) - julianday(COALESCE(last_accessed, timestamp))) * 24
               ))
               WHERE type = 'summary' AND confidence > 0""",
            (now,),
        )
        await self.db.commit()
        return cursor.rowcount

    # ── Internal ──────────────────────────────────────────────

    async def _compress(self, text: str) -> str:
        """LLM-based text summarization (placeholder — requires openai client)."""
        # Fallback: truncation
        if len(text) > 1000:
            return text[:997] + "..."
        return text


