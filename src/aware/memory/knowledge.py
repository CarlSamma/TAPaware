"""Knowledge Memory — long-term semantic facts (vector store)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from .database import Database
from .models import MemoryUnit
from .vector_store import VectorStore


class KnowledgeMemory:
    """Semantic memory of facts, properties, and learned knowledge.

    Stores confirmed properties, entity relationships, and extracted facts.
    Maps to TAP's ``properties`` + ``candidate_graph_nodes`` tables.
    """

    def __init__(self, db: Database, vector_store: Optional[VectorStore] = None) -> None:
        self.db = db
        self.vector_store = vector_store

    async def store(self, unit: MemoryUnit) -> MemoryUnit:
        """Store a knowledge memory unit with embedding + dedup check."""
        # Generate embedding if not provided
        if unit.embedding is None and self.vector_store:
            unit.embedding = await self.vector_store.embedder.encode(unit.content)

        # Semantic dedup: skip if >0.95 similarity to existing
        if unit.embedding and self.vector_store:
            similar = await self.vector_store.search(unit.content, top_k=1, threshold=0.95)
            if similar and similar[0][0] != unit.id:
                # Nearly identical unit exists — update rather than duplicate
                existing_id = similar[0][0]
                unit.id = existing_id

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

        # Store embedding in vector table
        if unit.embedding and self.vector_store:
            await self.vector_store.insert(unit.id, unit.embedding)

        return unit

    async def recall(
        self, query: str, limit: int = 10, threshold: float = 0.5
    ) -> List[Tuple[MemoryUnit, float]]:
        """Semantic search via vector store, fallback to keyword."""
        results: List[Tuple[MemoryUnit, float]] = []

        # Vector search first
        if self.vector_store:
            vector_results = await self.vector_store.search(query, top_k=limit, threshold=threshold)
            for mem_id, score in vector_results:
                unit = await self.get(mem_id)
                if unit:
                    results.append((unit, score))

        # Fill remaining with keyword search
        if len(results) < limit:
            kw_limit = limit - len(results)
            existing_ids = {r[0].id for r in results}
            rows = await self.db.fetchall(
                """SELECT * FROM memory_units
                   WHERE type = 'knowledge' AND content LIKE ?
                   ORDER BY timestamp DESC LIMIT ?""",
                (f"%{query}%", kw_limit),
            )
            for row in rows:
                if row["id"] not in existing_ids:
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
        if self.vector_store:
            await self.vector_store.delete(memory_id)
        await self.db.commit()
        return cursor.rowcount > 0

    async def count(self) -> int:
        row = await self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM memory_units WHERE type = 'knowledge'"
        )
        return row["cnt"] if row else 0

    async def get_by_category(self, category: str, limit: int = 50) -> List[MemoryUnit]:
        """Filter knowledge by metadata category."""
        rows = await self.db.fetchall(
            """SELECT * FROM memory_units
               WHERE type = 'knowledge' AND json_extract(metadata, '$.category') = ?
               ORDER BY timestamp DESC LIMIT ?""",
            (category, limit),
        )
        return [self._row_to_unit(r) for r in rows]

    async def consolidate(self, conversational) -> int:
        """Consolidate repeated episodic patterns into semantic knowledge."""
        # Fetch high-confidence conversational memories
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
            # Check if already in knowledge
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
                    confidence=unit.confidence * 0.9,  # slight decay during promotion
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
