"""Memory Persistence — cross-session save/load + backup."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .database import Database
from .models import MemoryUnit, SessionRecord

logger = logging.getLogger(__name__)


class MemoryPersistence:
    """Cross-session persistence with backup and restore."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def save_session(
        self, session_id: str, metadata: Optional[dict] = None
    ) -> SessionRecord:
        now = datetime.now(timezone.utc)
        record = SessionRecord(
            id=session_id,
            started_at=now,
            ended_at=now,
            metadata=metadata or {},
        )

        await self.db.execute(
            """INSERT OR REPLACE INTO sessions (id, started_at, ended_at, metadata)
               VALUES (?, ?, ?, ?)""",
            (
                record.id,
                record.started_at.isoformat(),
                record.ended_at.isoformat(),
                json.dumps(record.metadata),
            ),
        )
        await self.db.commit()
        return record

    async def load_session_context(self, session_id: str) -> Optional[dict]:
        row = await self.db.fetchone(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        )
        if not row:
            return None

        memories = await self.db.fetchall(
            "SELECT * FROM memory_units WHERE session_id = ? ORDER BY timestamp",
            (session_id,),
        )

        return {
            "session": {
                "id": row["id"],
                "started_at": row["started_at"],
                "ended_at": row["ended_at"],
                "metadata": json.loads(row["metadata"] or "{}"),
            },
            "memory_count": len(memories),
            "memories": [
                {
                    "id": r["id"],
                    "type": r["type"],
                    "content": r["content"],
                    "confidence": r["confidence"],
                }
                for r in memories
            ],
        }

    async def list_sessions(self, limit: int = 50) -> List[dict]:
        rows = await self.db.fetchall(
            "SELECT * FROM sessions ORDER BY started_at DESC LIMIT ?", (limit,)
        )
        return [
            {
                "id": r["id"],
                "started_at": r["started_at"],
                "ended_at": r["ended_at"],
                "metadata": json.loads(r["metadata"] or "{}"),
            }
            for r in rows
        ]

    async def backup(self, backup_path: str) -> str:
        db_path = self.db.conn.filename if self.db.conn else ":memory:"
        if db_path == ":memory:":
            raise ValueError("Cannot backup an in-memory database")

        Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
        await self.db.conn.execute("VACUUM INTO ?", (backup_path,))
        logger.info("Database backed up to %s", backup_path)
        return backup_path

    async def export_session_memories(
        self, session_id: str, path: str
    ) -> None:
        rows = await self.db.fetchall(
            "SELECT * FROM memory_units WHERE session_id = ? ORDER BY timestamp",
            (session_id,),
        )

        export = {
            "session_id": session_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "count": len(rows),
            "memories": [
                {
                    "id": r["id"],
                    "type": r["type"],
                    "content": r["content"],
                    "metadata": json.loads(r["metadata"] or "{}"),
                    "timestamp": r["timestamp"],
                    "confidence": r["confidence"],
                }
                for r in rows
            ],
        }

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(export, f, indent=2, default=str)

    async def import_session_memories(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        session_id = data.get("session_id", str(datetime.now(timezone.utc).timestamp()))

        for mem in data.get("memories", []):
            await self.db.execute(
                """INSERT OR REPLACE INTO memory_units
                   (id, type, content, metadata, timestamp, confidence, decay_rate,
                    last_accessed, access_count, session_id)
                   VALUES (?, ?, ?, ?, ?, ?, 0.1, ?, 0, ?)""",
                (
                    mem["id"],
                    mem["type"],
                    mem["content"],
                    json.dumps(mem.get("metadata", {})),
                    mem.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    mem.get("confidence", 1.0),
                    mem.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    session_id,
                ),
            )

        await self.db.commit()
        logger.info("Imported %d memories into session %s", len(data.get("memories", [])), session_id)
        return session_id
