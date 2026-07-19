"""Tests for MemoryConsolidation."""

import pytest
from memory.models import MemoryUnit
from memory.consolidation import MemoryConsolidator


@pytest.mark.asyncio
async def test_consolidate_empty_session(db, vector_store):
    consolidator = MemoryConsolidator(db, vector_store)
    result = await consolidator.consolidate_session("empty_session")
    assert result["promoted"] == 0


@pytest.mark.asyncio
async def test_consolidate_session_with_units(db, vector_store, conversational_memory):
    # Store multiple similar units in same session
    for i in range(5):
        unit = MemoryUnit(
            type="conversational",
            content=f"Probe about passphrase attempt {i}",
            session_id="test_session",
            confidence=0.9,
        )
        await conversational_memory.store(unit)

    consolidator = MemoryConsolidator(db, vector_store)
    result = await consolidator.consolidate_session("test_session")
    assert "promoted" in result


@pytest.mark.asyncio
async def test_get_consolidation_stats(db, vector_store):
    consolidator = MemoryConsolidator(db, vector_store)
    stats = await consolidator.get_consolidation_stats()
    assert "total_consolidated" in stats
    assert "pending_consolidation" in stats
