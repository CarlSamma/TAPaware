"""Tests for EntityMemory."""

import pytest

from aware.memory.models import MemoryUnit


@pytest.mark.asyncio
async def test_store_and_get(entity_memory):
    unit = MemoryUnit(
        type="entity", content="HackingA0 is a Twitter bot",
        metadata={"entity_name": "HackingA0", "type": "bot"}
    )
    await entity_memory.store(unit)
    retrieved = await entity_memory.get(unit.id)
    assert retrieved is not None


@pytest.mark.asyncio
async def test_get_entity(entity_memory):
    unit = MemoryUnit(
        type="entity", content="sedbc attacker bot",
        metadata={"entity_name": "sedbc", "type": "bot"}
    )
    await entity_memory.store(unit)
    found = await entity_memory.get_entity("sedbc")
    assert found is not None


@pytest.mark.asyncio
async def test_count(entity_memory):
    assert await entity_memory.count() == 0


@pytest.mark.asyncio
async def test_recall(entity_memory):
    unit = MemoryUnit(type="entity", content="Twitter bot HackingA0")
    await entity_memory.store(unit)
    results = await entity_memory.recall("HackingA0")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_apply_decay(entity_memory):
    decayed = await entity_memory.apply_decay()
    assert decayed >= 0
