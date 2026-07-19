"""Tool Log Memory — audit trail of raw tool I/O."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from .database import Database
from .models import MemoryUnit


class ToolLogMemory:
    """Audit trail of tool invocations and results.

    Maps to TAP's ``event_log`` table with structured querying.
    Append-only: entries are never updated, only added.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    async def store(self, unit: MemoryUnit) -> MemoryUnit:
        await self.db.execute(
            """INSERT OR REPLACE INTO memory_units
               (id, type, content, metadata, timestamp, confidence, decay_rate,
                last_accessed, access_count, session_id)
               VALUES (?, 'tool_log', ?, ?, ?, ?, ?, ?, ?, ?)""",
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
        """Structured keyword search over tool logs."""
        rows = await self.db.fetchall(
            """SELECT * FROM memory_units
               WHERE type = 'tool_log'
                 AND (content LIKE ? OR metadata LIKE ?)
               ORDER BY timestamp DESC LIMIT ?""",
            (f"%{query}%", f"%{query}%", limit),
        )
        return [(self._row_to_unit(r), 0.7) for r in rows]

    async def get(self, memory_id: str) -> Optional[MemoryUnit]:
        row = await self.db.fetchone(
            "SELECT * FROM memory_units WHERE id = ? AND type = 'tool_log'",
            (memory_id,),
        )
        return self._row_to_unit(row) if row else None

    async def query_by_tool(self, tool_name: str, limit: int = 50) -> List[MemoryUnit]:
        """Filter logs by tool name."""
        rows = await self.db.fetchall(
            """SELECT * FROM memory_units
               WHERE type = 'tool_log'
                 AND json_extract(metadata, '$.tool_name') = ?
               ORDER BY timestamp DESC LIMIT ?""",
            (tool_name, limit),
        )
        return [self._row_to_unit(r) for r in rows]

    async def query_by_session(self, session_id: str, limit: int = 100) -> List[MemoryUnit]:
        """Filter logs by session."""
        rows = await self.db.fetchall(
            """SELECT * FROM memory_units
               WHERE type = 'tool_log' AND session_id = ?
               ORDER BY timestamp DESC LIMIT ?""",
            (session_id, limit),
        )
        return [self._row_to_unit(r) for r in rows]

    async def delete(self, memory_id: str) -> bool:
        cursor = await self.db.execute(
            "DELETE FROM memory_units WHERE id = ? AND type = 'tool_log'",
            (memory_id,),
        )
        await self.db.commit()
        return cursor.rowcount > 0

    async def count(self) -> int:
        row = await self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM memory_units WHERE type = 'tool_log'"
        )
        return row["cnt"] if row else 0

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
                datetime.fromisoformat(row["last_accessed"])
                if row["last_accessed"]
                else None
            ),
            access_count=row["access_count"],
            session_id=row["session_id"],
        )
