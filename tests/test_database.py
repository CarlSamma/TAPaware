"""Tests for Database layer."""

import pytest


@pytest.mark.asyncio
async def test_initialize_creates_schema(db):
    """Schema should be created on init."""
    row = await db.fetchone("SELECT version FROM schema_version LIMIT 1")
    assert row is not None


@pytest.mark.asyncio
async def test_wal_mode(db):
    row = await db.fetchone("PRAGMA journal_mode")
    assert row[0] in ("wal", "memory")  # in-memory DB uses "memory"


@pytest.mark.asyncio
async def test_foreign_keys(db):
    row = await db.fetchone("PRAGMA foreign_keys")
    assert row[0] == 1


@pytest.mark.asyncio
async def test_memory_units_table(db):
    await db.execute(
        "INSERT INTO memory_units (id, type, content, timestamp) VALUES ('t1', 'knowledge', 'test', '2025-01-01T00:00:00')"
    )
    row = await db.fetchone("SELECT * FROM memory_units WHERE id = 't1'")
    assert row is not None
    assert row["content"] == "test"


@pytest.mark.asyncio
async def test_attack_types_table(db):
    await db.execute(
        """INSERT INTO attack_types (id, name, category, description, created_at, updated_at)
           VALUES ('a1', 'test_type', 'injection', 'desc', '2025-01-01T00:00:00', '2025-01-01T00:00:00')"""
    )
    row = await db.fetchone("SELECT * FROM attack_types WHERE id = 'a1'")
    assert row is not None
    assert row["name"] == "test_type"


@pytest.mark.asyncio
async def test_countermeasures_table(db):
    await db.execute(
        """INSERT INTO attack_types (id, name, category, description, created_at, updated_at)
           VALUES ('a1', 'test', 'x', 'd', '2025-01-01T00:00:00', '2025-01-01T00:00:00')"""
    )
    await db.execute(
        """INSERT INTO countermeasures (id, attack_type_id, name, description, created_at)
           VALUES ('c1', 'a1', 'cm1', 'd1', '2025-01-01T00:00:00')"""
    )
    row = await db.fetchone("SELECT * FROM countermeasures WHERE id = 'c1'")
    assert row is not None


@pytest.mark.asyncio
async def test_in_memory_db():
    from memory.database import Database
    db = Database()
    await db.initialize(":memory:")
    row = await db.fetchone("SELECT 1 as val")
    assert row["val"] == 1
    await db.close()
