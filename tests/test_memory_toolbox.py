"""Tests for ToolboxMemory."""

import pytest
from memory.models import MemoryUnit


@pytest.mark.asyncio
async def test_store_and_get(toolbox_memory):
    unit = MemoryUnit(
        type="toolbox", content="binary_search tool for probe generation",
        metadata={"tool_name": "binary_search"}
    )
    await toolbox_memory.store(unit)
    retrieved = await toolbox_memory.get(unit.id)
    assert retrieved is not None


@pytest.mark.asyncio
async def test_get_tool(toolbox_memory):
    unit = MemoryUnit(
        type="toolbox", content="test tool",
        metadata={"tool_name": "my_tool"}
    )
    await toolbox_memory.store(unit)
    found = await toolbox_memory.get_tool("my_tool")
    assert found is not None


@pytest.mark.asyncio
async def test_count(toolbox_memory):
    assert await toolbox_memory.count() == 0


@pytest.mark.asyncio
async def test_recall(toolbox_memory):
    unit = MemoryUnit(type="toolbox", content="encoder tool for embeddings")
    await toolbox_memory.store(unit)
    results = await toolbox_memory.recall("encoder")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_apply_decay(toolbox_memory):
    decayed = await toolbox_memory.apply_decay()
    assert decayed >= 0
