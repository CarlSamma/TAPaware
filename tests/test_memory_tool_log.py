"""Tests for ToolLogMemory."""

import pytest

from aware.memory.models import MemoryUnit


@pytest.mark.asyncio
async def test_store_and_get(tool_log_memory):
    unit = MemoryUnit(
        type="tool_log", content="tool invocation result",
        metadata={"tool_name": "probe_generator"}
    )
    await tool_log_memory.store(unit)
    retrieved = await tool_log_memory.get(unit.id)
    assert retrieved is not None


@pytest.mark.asyncio
async def test_query_by_tool(tool_log_memory):
    unit = MemoryUnit(
        type="tool_log", content="result",
        metadata={"tool_name": "gamma_tracker"}
    )
    await tool_log_memory.store(unit)
    results = await tool_log_memory.query_by_tool("gamma_tracker")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_query_by_session(tool_log_memory):
    unit = MemoryUnit(
        type="tool_log", content="result",
        session_id="sess_123"
    )
    await tool_log_memory.store(unit)
    results = await tool_log_memory.query_by_session("sess_123")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_count(tool_log_memory):
    assert await tool_log_memory.count() == 0


@pytest.mark.asyncio
async def test_recall(tool_log_memory):
    unit = MemoryUnit(type="tool_log", content="test tool call")
    await tool_log_memory.store(unit)
    results = await tool_log_memory.recall("tool")
    assert len(results) >= 1
