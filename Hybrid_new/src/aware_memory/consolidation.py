"""Memory Consolidation — episodic -> semantic promotion engine."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List

from .database import Database
from .models import MemoryUnit

logger = logging.getLogger(__name__)


class MemoryConsolidator:
    """Promotes episodic (conversational) memories to semantic (knowledge) memories."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def consolidate_session(self, session_id: str) -> Dict[str, int]:
        rows = await self.db.fetchall(
            """SELECT * FROM memory_units
               WHERE type = 'conversational' AND session_id = ?
               ORDER BY timestamp""",
            (session_id,),
        )
        if not rows:
            return {"promoted": 0, "skipped": 0}

        units = [self._row_to_unit(r) for r in rows]

        promoted = 0
        skipped = 0

        # Group by content similarity (simple dedup for keyword-only mode)
        seen_contents: dict[str, list[MemoryUnit]] = {}
        for u in units:
            key = u.content[:100].lower().strip()
            seen_contents.setdefault(key, []).append(u)

        for key, cluster in seen_contents.items():
            if len(cluster) >= 3:
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

    async def get_consolidation_stats(self) -> dict:
        total_row = await self.db.fetchone("SELECT COUNT(*) as cnt FROM consolidation_log")
        pending_row = await self.db.fetchone(
            """SELECT COUNT(*) as cnt FROM memory_units
               WHERE type = 'conversational' AND confidence > 0.7"""
        )
        return {
            "total_consolidated": total_row["cnt"] if total_row else 0,
            "pending_consolidation": pending_row["cnt"] if pending_row else 0,
        }

    @staticmethod
    def _summarize_cluster(cluster: List[MemoryUnit]) -> str:
        if len(cluster) == 1:
            return cluster[0].content
        contents = [u.content for u in cluster[:5]]
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
