"""Tests for MemoryPersistence."""

import json
import pytest
import tempfile
from pathlib import Path
from memory.persistence import MemoryPersistence
from memory.models import MemoryUnit


@pytest.mark.asyncio
async def test_save_session(db):
    persistence = MemoryPersistence(db)
    record = await persistence.save_session("sess_1", {"key": "val"})
    assert record.id == "sess_1"


@pytest.mark.asyncio
async def test_load_session_context(db, conversational_memory):
    persistence = MemoryPersistence(db)
    # Save session first so load_session_context can find it
    await persistence.save_session("sess_1", {"key": "val"})

    unit = MemoryUnit(
        type="conversational", content="test",
        session_id="sess_1"
    )
    await conversational_memory.store(unit)

    ctx = await persistence.load_session_context("sess_1")
    assert ctx is not None
    assert ctx["memory_count"] >= 1


@pytest.mark.asyncio
async def test_list_sessions(db):
    persistence = MemoryPersistence(db)
    await persistence.save_session("s1")
    await persistence.save_session("s2")
    sessions = await persistence.list_sessions()
    assert len(sessions) >= 2


@pytest.mark.asyncio
async def test_export_import_memories(db, conversational_memory):
    unit = MemoryUnit(
        type="conversational", content="export test",
        session_id="export_sess"
    )
    await conversational_memory.store(unit)

    persistence = MemoryPersistence(db)

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp_path = f.name

    await persistence.export_session_memories("export_sess", tmp_path)
    assert Path(tmp_path).exists()

    # Import into new session
    new_session_id = await persistence.import_session_memories(tmp_path)
    assert new_session_id is not None

    Path(tmp_path).unlink()
