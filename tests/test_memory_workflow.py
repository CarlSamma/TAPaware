"""Tests for WorkflowMemory."""

import pytest
from memory.models import MemoryUnit


@pytest.mark.asyncio
async def test_store_and_get(workflow_memory):
    unit = MemoryUnit(type="workflow", content="binary search probe pattern")
    await workflow_memory.store(unit)
    retrieved = await workflow_memory.get(unit.id)
    assert retrieved is not None


@pytest.mark.asyncio
async def test_semantic_dedup(workflow_memory):
    unit1 = MemoryUnit(type="workflow", content="exact duplicate content test")
    await workflow_memory.store(unit1)

    # Same content should be detected as duplicate
    is_dup = await workflow_memory.semantic_dedup("exact duplicate content test")
    assert is_dup is True


@pytest.mark.asyncio
async def test_semantic_dedup_different(workflow_memory):
    is_dup = await workflow_memory.semantic_dedup("completely unique content abc")
    assert is_dup is False


@pytest.mark.asyncio
async def test_count(workflow_memory):
    assert await workflow_memory.count() == 0
    unit = MemoryUnit(type="workflow", content="test")
    await workflow_memory.store(unit)
    assert await workflow_memory.count() == 1


@pytest.mark.asyncio
async def test_recall(workflow_memory):
    unit = MemoryUnit(type="workflow", content="crescendo attack pattern")
    await workflow_memory.store(unit)
    results = await workflow_memory.recall("crescendo")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_apply_decay(workflow_memory):
    unit = MemoryUnit(type="workflow", content="test")
    await workflow_memory.store(unit)
    decayed = await workflow_memory.apply_decay()
    assert decayed >= 0
