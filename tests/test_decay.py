"""Tests for MemoryDecay."""

import pytest

from aware.memory.decay import MemoryDecay
from aware.memory.models import MemoryUnit


@pytest.mark.asyncio
async def test_apply_decay(db, conversational_memory):
    unit = MemoryUnit(type="conversational", content="test", confidence=1.0)
    await conversational_memory.store(unit)

    decay = MemoryDecay(db)
    archived = await decay.apply_decay()
    assert archived >= 0


@pytest.mark.asyncio
async def test_touch_updates_access(db, conversational_memory):
    unit = MemoryUnit(type="conversational", content="test")
    await conversational_memory.store(unit)

    decay = MemoryDecay(db)
    await decay.touch(unit.id)

    # Verify access_count incremented
    row = await db.fetchone(
        "SELECT access_count FROM memory_units WHERE id = ?", (unit.id,)
    )
    assert row["access_count"] == 1


@pytest.mark.asyncio
async def test_get_stale_units(db, conversational_memory):
    unit = MemoryUnit(type="conversational", content="test", confidence=0.05)
    await conversational_memory.store(unit)

    decay = MemoryDecay(db)
    stale = await decay.get_stale_units(threshold=0.1)
    assert len(stale) >= 1


@pytest.mark.asyncio
async def test_purge(db, conversational_memory):
    unit = MemoryUnit(type="conversational", content="test", confidence=0.01)
    await conversational_memory.store(unit)

    decay = MemoryDecay(db)
    deleted = await decay.purge(below_threshold=0.05)
    assert deleted >= 1


@pytest.mark.asyncio
async def test_get_decay_stats(db, conversational_memory):
    decay = MemoryDecay(db)
    stats = await decay.get_decay_stats()
    assert "total" in stats
    assert "high_confidence" in stats
