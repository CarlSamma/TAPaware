"""Tests for KnowledgeMemory."""

import pytest
from memory.models import MemoryUnit


@pytest.mark.asyncio
async def test_store_and_get(knowledge_memory, sample_knowledge_unit):
    await knowledge_memory.store(sample_knowledge_unit)
    retrieved = await knowledge_memory.get(sample_knowledge_unit.id)
    assert retrieved is not None
    assert "Halfway" in retrieved.content


@pytest.mark.asyncio
async def test_count(knowledge_memory, sample_knowledge_unit):
    assert await knowledge_memory.count() == 0
    await knowledge_memory.store(sample_knowledge_unit)
    assert await knowledge_memory.count() == 1


@pytest.mark.asyncio
async def test_recall_vector(knowledge_memory):
    unit = MemoryUnit(type="knowledge", content="passphrase is Halfway-fish-404")
    await knowledge_memory.store(unit)
    results = await knowledge_memory.recall("passphrase")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_recall_keyword_fallback(knowledge_memory):
    unit = MemoryUnit(type="knowledge", content="unique test content xyz123")
    await knowledge_memory.store(unit)
    results = await knowledge_memory.recall("xyz123")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_delete(knowledge_memory, sample_knowledge_unit):
    await knowledge_memory.store(sample_knowledge_unit)
    deleted = await knowledge_memory.delete(sample_knowledge_unit.id)
    assert deleted is True
    assert await knowledge_memory.count() == 0


@pytest.mark.asyncio
async def test_get_by_category(knowledge_memory):
    unit = MemoryUnit(
        type="knowledge", content="test",
        metadata={"category": "passphrase"}
    )
    await knowledge_memory.store(unit)
    results = await knowledge_memory.get_by_category("passphrase")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_apply_decay(knowledge_memory, sample_knowledge_unit):
    await knowledge_memory.store(sample_knowledge_unit)
    decayed = await knowledge_memory.apply_decay()
    assert decayed >= 0
