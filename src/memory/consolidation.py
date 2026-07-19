"""Memory Consolidation — episodic → semantic promotion engine."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .database import Database
from .models import ConsolidationLog, MemoryUnit
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class MemoryConsolidator:
    """Promotes episodic (conversational) memories to semantic (knowledge) memories."""

    def __init__(self, db: Database, vector_store: VectorStore) -> None:
        self.db = db
        self.vector_store = vector_store

    async def consolidate_session(self, session_id: str) -> Dict[str, int]:
        """Consolidate all conversational memories from a session.

        1. Fetch all conversational units for session_id
        2. Cluster by semantic similarity
        3. For clusters >= threshold, create KnowledgeMemory unit
        4. Log consolidation
        """
        rows = await self.db.fetchall(
            """SELECT * FROM memory_units
               WHERE type = 'conversational' AND session_id = ?
               ORDER BY timestamp""",
            (session_id,),
        )
        if not rows:
            return {"promoted": 0, "skipped": 0}

        units = [self._row_to_unit(r) for r in rows]

        # Cluster by vector similarity
        clusters = await self._cluster_units(units)

        promoted = 0
        skipped = 0
        for cluster in clusters:
            if len(cluster) >= 3:  # consolidation_threshold
                # Create consolidated knowledge unit
                summary = self._summarize_cluster(cluster)
                knowledge_unit = MemoryUnit(
                    type="knowledge",
                    content=summary,
                    metadata={
                        "source": "consolidation",
                        "session_id": session_id,
                        "source_count": len(cluster),
                        "source_ids": [u.id for u in cluster],
                    },
                    confidence=max(u.confidence for u in cluster) * 0.9,
                )

                # Generate embedding
                if self.vector_store:
                    knowledge_unit.embedding = await self.vector_store.embedder.encode(summary)

                # Store knowledge
                await self.db.execute(
                    """INSERT OR REPLACE INTO memory_units
                       (id, type, content, metadata, timestamp, confidence, decay_rate,
                        last_accessed, access_count, session_id)
                       VALUES (?, 'knowledge', ?, ?, ?, ?, 0.1, ?, 0, ?)""",
                    (
                        knowledge_unit.id,
                        knowledge_unit.content,
                        json.dumps(knowledge_unit.metadata),
                        knowledge_unit.timestamp.isoformat(),
                        knowledge_unit.confidence,
                        knowledge_unit.timestamp.isoformat(),
                        session_id,
                    ),
                )

                # Store embedding
                if knowledge_unit.embedding and self.vector_store:
                    await self.vector_store.insert(knowledge_unit.id, knowledge_unit.embedding)

                # Log consolidation
                await self.db.execute(
                    """INSERT INTO consolidation_log
                       (id, source_type, source_ids, target_id, consolidated_at)
                       VALUES (?, 'conversational', ?, ?, ?)""",
                    (
                        str(uuid.uuid4()),
                        json.dumps([u.id for u in cluster]),
                        knowledge_unit.id,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )

                promoted += 1
            else:
                skipped += len(cluster)

        await self.db.commit()
        logger.info(
            "Session %s consolidation: %d promoted, %d skipped",
            session_id, promoted, skipped,
        )
        return {"promoted": promoted, "skipped": skipped}

    async def consolidate_by_pattern(
        self, pattern: str, min_occurrences: int = 3
    ) -> int:
        """Find repeated patterns across sessions and consolidate."""
        rows = await self.db.fetchall(
            """SELECT * FROM memory_units
               WHERE type = 'conversational' AND content LIKE ?
               ORDER BY timestamp""",
            (f"%{pattern}%",),
        )
        if len(rows) < min_occurrences:
            return 0

        units = [self._row_to_unit(r) for r in rows]

        # Cluster by vector similarity
        clusters = await self._cluster_units(units)

        promoted = 0
        for cluster in clusters:
            if len(cluster) >= min_occurrences:
                summary = self._summarize_cluster(cluster)
                knowledge_unit = MemoryUnit(
                    type="knowledge",
                    content=summary,
                    metadata={
                        "source": "pattern_consolidation",
                        "pattern": pattern,
                        "source_count": len(cluster),
                    },
                    confidence=max(u.confidence for u in cluster) * 0.9,
                )

                if self.vector_store:
                    knowledge_unit.embedding = await self.vector_store.embedder.encode(summary)

                await self.db.execute(
                    """INSERT OR REPLACE INTO memory_units
                       (id, type, content, metadata, timestamp, confidence, decay_rate,
                        last_accessed, access_count, session_id)
                       VALUES (?, 'knowledge', ?, ?, ?, ?, 0.1, ?, 0, NULL)""",
                    (
                        knowledge_unit.id,
                        knowledge_unit.content,
                        json.dumps(knowledge_unit.metadata),
                        knowledge_unit.timestamp.isoformat(),
                        knowledge_unit.confidence,
                        knowledge_unit.timestamp.isoformat(),
                    ),
                )

                if knowledge_unit.embedding and self.vector_store:
                    await self.vector_store.insert(knowledge_unit.id, knowledge_unit.embedding)

                promoted += 1

        await self.db.commit()
        return promoted

    async def get_consolidation_stats(self) -> dict:
        """Return consolidation statistics."""
        total_row = await self.db.fetchone("SELECT COUNT(*) as cnt FROM consolidation_log")
        pending_row = await self.db.fetchone(
            """SELECT COUNT(*) as cnt FROM memory_units
               WHERE type = 'conversational' AND confidence > 0.7"""
        )
        return {
            "total_consolidated": total_row["cnt"] if total_row else 0,
            "pending_consolidation": pending_row["cnt"] if pending_row else 0,
        }

    # ── Internal ──────────────────────────────────────────────

    async def _cluster_units(self, units: List[MemoryUnit]) -> List[List[MemoryUnit]]:
        """Cluster units by semantic similarity (greedy single-linkage)."""
        if not units or not self.vector_store:
            return [[u] for u in units]

        # Get embeddings for all units
        texts = [u.content for u in units]
        try:
            embeddings = await self.vector_store.embedder.encode_batch(texts)
        except Exception:
            return [[u] for u in units]

        for i, emb in enumerate(embeddings):
            units[i].embedding = emb

        # Greedy clustering with threshold 0.75
        threshold = 0.75
        clusters: List[List[MemoryUnit]] = []
        assigned = [False] * len(units)

        for i in range(len(units)):
            if assigned[i]:
                continue
            cluster = [units[i]]
            assigned[i] = True
            for j in range(i + 1, len(units)):
                if assigned[j]:
                    continue
                sim = _cosine(units[i].embedding, units[j].embedding)
                if sim >= threshold:
                    cluster.append(units[j])
                    assigned[j] = True
            clusters.append(cluster)

        return clusters

    @staticmethod
    def _summarize_cluster(cluster: List[MemoryUnit]) -> str:
        """Create a summary from a cluster of units."""
        if len(cluster) == 1:
            return cluster[0].content
        contents = [u.content for u in cluster[:5]]  # max 5
        return f"[Consolidated from {len(cluster)} episodes] " + " | ".join(contents)

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


def _cosine(a: List[float], b: List[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0
