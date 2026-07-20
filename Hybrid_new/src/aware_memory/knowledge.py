"""Knowledge Memory — long-term semantic facts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from .database import Database
from .models import MemoryUnit
from .vector_store import VectorStore


class KnowledgeMemory:
    """Semantic memory of facts, properties, and learned knowledge."""

    def __init__(self, db: Database, vector_store: Optional[VectorStore] = None) -> None:
        self.db = db
        self.vector_store = vector_store

    async def store(self, unit: MemoryUnit) -> MemoryUnit:
        await self.db.execute(
            """INSERT OR REPLACE INTO memory_units
               (id, type, content, metadata, timestamp, confidence, decay_rate,
                last_accessed, access_count, session_id)
               VALUES (?, 'knowledge', ?, ?, ?, ?, ?, ?, ?, ?)""",
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
        results: List[Tuple[MemoryUnit, float]] = []

        rows = await self.db.fetchall(
            """SELECT * FROM memory_units
               WHERE type = 'knowledge' AND content LIKE ?
               ORDER BY timestamp DESC LIMIT ?""",
            (f"%{query}%", limit),
        )
        for row in rows:
            results.append((self._row_to_unit(row), 0.6))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    async def get(self, memory_id: str) -> Optional[MemoryUnit]:
        row = await self.db.fetchone(
            "SELECT * FROM memory_units WHERE id = ? AND type = 'knowledge'",
            (memory_id,),
        )
        return self._row_to_unit(row) if row else None

    async def delete(self, memory_id: str) -> bool:
        cursor = await self.db.execute(
            "DELETE FROM memory_units WHERE id = ? AND type = 'knowledge'",
            (memory_id,),
        )
        await self.db.commit()
        return cursor.rowcount > 0

    async def count(self) -> int:
        row = await self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM memory_units WHERE type = 'knowledge'"
        )
        return row["cnt"] if row else 0

    async def consolidate(self, conversational) -> int:
        rows = await self.db.fetchall(
            """SELECT * FROM memory_units
               WHERE type = 'conversational' AND confidence > 0.7
               ORDER BY access_count DESC LIMIT 50"""
        )
        if not rows:
            return 0

        consolidated = 0
        for row in rows:
            unit = conversational._row_to_unit(row)
            existing = await self.db.fetchone(
                """SELECT id FROM memory_units
                   WHERE type = 'knowledge' AND content = ?""",
                (unit.content,),
            )
            if not existing:
                knowledge_unit = MemoryUnit(
                    type="knowledge",
                    content=unit.content,
                    metadata={**unit.metadata, "source": "consolidation"},
                    confidence=unit.confidence * 0.9,
                    session_id=unit.session_id,
                )
                await self.store(knowledge_unit)
                consolidated += 1

        return consolidated

    async def apply_decay(self) -> int:
        now = datetime.now(timezone.utc).isoformat()
        cursor = await self.db.execute(
            """UPDATE memory_units
               SET confidence = confidence * exp(-decay_rate * (
                   (julianday(?) - julianday(COALESCE(last_accessed, timestamp))) * 24
               ))
               WHERE type = 'knowledge' AND confidence > 0""",
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
