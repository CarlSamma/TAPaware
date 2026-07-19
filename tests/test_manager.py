"""Tests for MemoryManager."""

import pytest
from memory.models import MemoryUnit


@pytest.mark.asyncio
async def test_initialize(memory_manager):
    assert memory_manager.db.conn is not None


@pytest.mark.asyncio
async def test_store_and_recall(memory_manager):
    unit = MemoryUnit(type="conversational", content="test probe")
    await memory_manager.store(unit, "conversational")
    results = await memory_manager.recall("test probe")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_store_invalid_type_raises(memory_manager):
    unit = MemoryUnit(type="test", content="test")
    with pytest.raises(ValueError, match="Unknown memory type"):
        await memory_manager.store(unit, "nonexistent")


@pytest.mark.asyncio
async def test_get_stats(memory_manager):
    stats = await memory_manager.get_stats()
    assert "conversational" in stats
    assert "knowledge" in stats
    assert all(v >= 0 for v in stats.values())


@pytest.mark.asyncio
async def test_consolidate(memory_manager):
    result = await memory_manager.consolidate()
    assert "consolidated" in result
    assert "decayed" in result


@pytest.mark.asyncio
async def test_cross_type_recall(memory_manager):
    await memory_manager.store(
        MemoryUnit(type="conversational", content="probe about password"),
        "conversational",
    )
    await memory_manager.store(
        MemoryUnit(type="knowledge", content="password is secret"),
        "knowledge",
    )
    results = await memory_manager.recall("password")
    types_found = {r.memory_type for r in results}
    assert len(types_found) >= 1


@pytest.mark.asyncio
async def test_recall_filter_types(memory_manager):
    await memory_manager.store(
        MemoryUnit(type="conversational", content="test conv"),
        "conversational",
    )
    results = await memory_manager.recall("test", memory_types=["conversational"])
    assert all(r.memory_type == "conversational" for r in results)
