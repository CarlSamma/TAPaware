"""SQLite database layer for Aware memory."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import aiosqlite

logger = logging.getLogger(__name__)

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
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.conn = await aiosqlite.connect(db_path)
        self.conn.row_factory = aiosqlite.Row

        await self.conn.execute("PRAGMA journal_mode=WAL")
        await self.conn.execute("PRAGMA foreign_keys=ON")

        await self._run_migrations()

    async def close(self) -> None:
        if self.conn:
            await self.conn.close()
            self.conn = None

    async def _run_migrations(self) -> None:
        await self.conn.executescript(_DDL)
        cursor = await self.conn.execute("SELECT version FROM schema_version LIMIT 1")
        row = await cursor.fetchone()
        if row is None:
            await self.conn.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (_SCHEMA_VERSION,),
            )
        await self.conn.commit()

    async def execute(self, sql: str, params: tuple = ()):
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
