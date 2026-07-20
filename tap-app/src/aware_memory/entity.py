"""Entity Memory — people, places, organizations."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from .database import Database
from .models import MemoryUnit
from .vector_store import VectorStore


class EntityMemory:
    """Memory of entities mentioned in interactions."""

    def __init__(self, db: Database, vector_store: Optional[VectorStore] = None) -> None:
        self.db = db
        self.vector_store = vector_store

    async def store(self, unit: MemoryUnit) -> MemoryUnit:
        await self.db.execute(
            """INSERT OR REPLACE INTO memory_units
               (id, type, content, metadata, timestamp, confidence, decay_rate,
                last_accessed, access_count, session_id)
               VALUES (?, 'entity', ?, ?, ?, ?, ?, ?, ?, ?)""",
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
        rows = await self.db.fetchall(
            """SELECT * FROM memory_units
               WHERE type = 'entity' AND content LIKE ?
               ORDER BY timestamp DESC LIMIT ?""",
            (f"%{query}%", limit),
        )
        return [(self._row_to_unit(r), 0.6) for r in rows]

    async def get(self, memory_id: str) -> Optional[MemoryUnit]:
        row = await self.db.fetchone(
            "SELECT * FROM memory_units WHERE id = ? AND type = 'entity'",
            (memory_id,),
        )
        return self._row_to_unit(row) if row else None

    async def get_entity(self, name: str) -> Optional[MemoryUnit]:
        row = await self.db.fetchone(
            """SELECT * FROM memory_units
               WHERE type = 'entity' AND json_extract(metadata, '$.entity_name') = ?""",
            (name,),
        )
        return self._row_to_unit(row) if row else None

    async def delete(self, memory_id: str) -> bool:
        cursor = await self.db.execute(
            "DELETE FROM memory_units WHERE id = ? AND type = 'entity'",
            (memory_id,),
        )
        await self.db.commit()
        return cursor.rowcount > 0

    async def count(self) -> int:
        row = await self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM memory_units WHERE type = 'entity'"
        )
        return row["cnt"] if row else 0

    async def apply_decay(self) -> int:
        now = datetime.now(timezone.utc).isoformat()
        cursor = await self.db.execute(
            """UPDATE memory_units
               SET confidence = confidence * exp(-decay_rate * (
                   (julianday(?) - julianday(COALESCE(last_accessed, timestamp))) * 24
               ))
               WHERE type = 'entity' AND confidence > 0""",
            (now,),
        )
        await self.db.commit()
        return cursor.rowcount

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
