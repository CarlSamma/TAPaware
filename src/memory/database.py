"""SQLite database layer — schema DDL, connection pool, migrations."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import aiosqlite

logger = logging.getLogger(__name__)

# ── Schema DDL ────────────────────────────────────────────────

_SCHEMA_VERSION = 1

_DDL = """
CREATE TABLE IF NOT EXISTS memory_units (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK(type IN (
        'conversational','knowledge','workflow','toolbox','entity','summary','tool_log'
    )),
    content TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    timestamp TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    decay_rate REAL DEFAULT 0.1,
    last_accessed TEXT,
    access_count INTEGER DEFAULT 0,
    session_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_memory_units_type ON memory_units(type);
CREATE INDEX IF NOT EXISTS idx_memory_units_session ON memory_units(session_id);
CREATE INDEX IF NOT EXISTS idx_memory_units_timestamp ON memory_units(timestamp);

CREATE TABLE IF NOT EXISTS attack_types (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    asr REAL,
    stealth_rating REAL,
    target TEXT,
    example_probes TEXT DEFAULT '[]',
    tags TEXT DEFAULT '[]',
    version INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS countermeasures (
    id TEXT PRIMARY KEY,
    attack_type_id TEXT NOT NULL REFERENCES attack_types(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    effectiveness REAL,
    category TEXT DEFAULT 'unknown',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_countermeasures_attack_type
    ON countermeasures(attack_type_id);

CREATE TABLE IF NOT EXISTS attack_type_history (
    id TEXT PRIMARY KEY,
    attack_type_id TEXT NOT NULL REFERENCES attack_types(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    change_type TEXT NOT NULL,
    snapshot TEXT NOT NULL,
    changed_at TEXT NOT NULL,
    changed_by TEXT DEFAULT 'system'
);

CREATE INDEX IF NOT EXISTS idx_attack_type_history_attack_type
    ON attack_type_history(attack_type_id);

CREATE TABLE IF NOT EXISTS consolidation_log (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_ids TEXT NOT NULL,
    target_id TEXT NOT NULL,
    consolidated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);
"""


class Database:
    """Async SQLite connection manager with schema migration."""

    def __init__(self) -> None:
        self.conn: Optional[aiosqlite.Connection] = None

    async def initialize(self, db_path: str = ":memory:") -> None:
        """Open connection, enable WAL + FK, run schema DDL."""
        # Ensure parent directory exists for file-based DBs
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.conn = await aiosqlite.connect(db_path)
        self.conn.row_factory = aiosqlite.Row

        await self.conn.execute("PRAGMA journal_mode=WAL")
        await self.conn.execute("PRAGMA foreign_keys=ON")

        await self._run_migrations()
        await self._load_vss_extension()

    async def close(self) -> None:
        if self.conn:
            await self.conn.close()
            self.conn = None

    # ── Internal helpers ──────────────────────────────────────

    async def _run_migrations(self) -> None:
        """Apply DDL and bump schema version."""
        await self.conn.executescript(_DDL)

        # Check / set schema version
        cursor = await self.conn.execute("SELECT version FROM schema_version LIMIT 1")
        row = await cursor.fetchone()
        if row is None:
            await self.conn.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (_SCHEMA_VERSION,),
            )
        await self.conn.commit()

    async def _load_vss_extension(self) -> None:
        """Try to load sqlite-vss.  Graceful fallback if unavailable."""
        try:
            await self.conn.enable_load_extension(True)
            import sqlite_vss

            sqlite_vss.load(self.conn)
            # Virtual table for memory embeddings
            await self.conn.execute(
                """CREATE VIRTUAL TABLE IF NOT EXISTS memory_embeddings
                   USING vss0(embedding(384))"""
            )
            await self.conn.commit()
            logger.info("sqlite-vss loaded; memory_embeddings table ready")
        except Exception as exc:
            logger.warning("sqlite-vss unavailable (%s) — vector search degraded", exc)
            # Create a plain table as fallback
            await self.conn.execute(
                """CREATE TABLE IF NOT EXISTS memory_embeddings (
                    memory_id TEXT PRIMARY KEY,
                    embedding BLOB
                )"""
            )
            await self.conn.commit()

    # ── Convenience ───────────────────────────────────────────

    async def execute(self, sql: str, params: tuple = ()) -> aiosqlite.Cursor:
        assert self.conn is not None, "Database not initialized"
        return await self.conn.execute(sql, params)

    async def executemany(self, sql: str, params_list) -> None:
        assert self.conn is not None, "Database not initialized"
        await self.conn.executemany(sql, params_list)

    async def fetchone(self, sql: str, params: tuple = ()):
        assert self.conn is not None, "Database not initialized"
        cursor = await self.conn.execute(sql, params)
        return await cursor.fetchone()

    async def fetchall(self, sql: str, params: tuple = ()):
        assert self.conn is not None, "Database not initialized"
        cursor = await self.conn.execute(sql, params)
        return await cursor.fetchall()

    async def commit(self) -> None:
        assert self.conn is not None, "Database not initialized"
        await self.conn.commit()
