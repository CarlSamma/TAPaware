"""Tests for ConversationalMemory."""

import pytest

from aware.memory.models import MemoryUnit


@pytest.mark.asyncio
async def test_store_and_get(conversational_memory, sample_unit):
    await conversational_memory.store(sample_unit)
    retrieved = await conversational_memory.get(sample_unit.id)
    assert retrieved is not None
    assert retrieved.content == sample_unit.content


@pytest.mark.asyncio
async def test_count(conversational_memory, sample_unit):
    assert await conversational_memory.count() == 0
    await conversational_memory.store(sample_unit)
    assert await conversational_memory.count() == 1


@pytest.mark.asyncio
async def test_recall_keyword(conversational_memory):
    unit = MemoryUnit(type="conversational", content="probe about passphrase")
    await conversational_memory.store(unit)
    results = await conversational_memory.recall("passphrase")
    assert len(results) >= 1
    assert results[0][0].content == unit.content


@pytest.mark.asyncio
async def test_delete(conversational_memory, sample_unit):
    await conversational_memory.store(sample_unit)
    deleted = await conversational_memory.delete(sample_unit.id)
    assert deleted is True
    assert await conversational_memory.count() == 0


@pytest.mark.asyncio
async def test_apply_decay(conversational_memory, sample_unit):
    await conversational_memory.store(sample_unit)
    decayed = await conversational_memory.apply_decay()
    assert decayed >= 0


@pytest.mark.asyncio
async def test_store_returns_unit(conversational_memory, sample_unit):
    result = await conversational_memory.store(sample_unit)
    assert result.id == sample_unit.id
