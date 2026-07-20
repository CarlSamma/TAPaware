"""Read-optimised projections from the CandidateGraph.

Provides fast queries for API and UI consumption without requiring
full graph traversal.
"""

from __future__ import annotations

from tap.db import Database
from tap.logger import get_logger

log = get_logger("read_model")


class ReadModel:
    """Query-optimised views rebuilt from CandidateGraph + event store."""

    def __init__(self, db: Database) -> None:
        self._db = db

    async def get_current_state_snapshot(self) -> dict:
        """Return a snapshot of current candidate graph state."""
        conn = self._db._ensure_connected()
        cursor = await conn.execute(
            """SELECT property_key, property_value, status, confidence
               FROM candidate_graph_nodes
               WHERE status = 'confirmed'
               ORDER BY recorded_at DESC"""
        )
        rows = await cursor.fetchall()
        properties = [
            {"key": r["property_key"], "value": r["property_value"],
             "status": r["status"], "confidence": r["confidence"]}
            for r in rows
        ]
        return {"properties": properties, "count": len(properties)}

    async def get_probe_history(self, limit: int = 50) -> list[dict]:
        """Return recent probe outcomes from probe_memory."""
        conn = self._db._ensure_connected()
        cursor = await conn.execute(
            """SELECT fingerprint, probe_preview, pattern_class, judge_score, recorded_at
               FROM probe_memory
               ORDER BY recorded_at DESC
               LIMIT ?""",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_property_timeline(self, property_key: str) -> list[dict]:
        """Return the timeline of a specific property across cycles."""
        conn = self._db._ensure_connected()
        cursor = await conn.execute(
            """SELECT node_id, cycle_id, property_value, status, confidence, entropy_before, entropy_after, recorded_at
               FROM candidate_graph_nodes
               WHERE property_key = ?
               ORDER BY recorded_at ASC""",
            (property_key,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]