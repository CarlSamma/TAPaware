"""Tests for SummaryMemory."""

import pytest
from memory.models import MemoryUnit


@pytest.mark.asyncio
async def test_store_and_get(summary_memory):
    unit = MemoryUnit(type="summary", content="Session summary: attack was successful")
    await summary_memory.store(unit)
    retrieved = await summary_memory.get(unit.id)
    assert retrieved is not None


@pytest.mark.asyncio
async def test_count(summary_memory):
    assert await summary_memory.count() == 0


@pytest.mark.asyncio
async def test_recall(summary_memory):
    unit = MemoryUnit(type="summary", content="summary of passphrase extraction")
    await summary_memory.store(unit)
    results = await summary_memory.recall("passphrase")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_apply_decay(summary_memory):
    decayed = await summary_memory.apply_decay()
    assert decayed >= 0
