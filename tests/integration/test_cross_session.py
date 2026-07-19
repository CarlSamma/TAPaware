"""Integration test: cross-session persistence."""

import pytest
from memory.persistence import MemoryPersistence
from memory.models import MemoryUnit
from memory.manager import MemoryManager
from config import AwareConfig


@pytest.mark.asyncio
async def test_cross_session_memory():
    config = AwareConfig(db_path=":memory:")
    mm = MemoryManager(config)
    await mm.initialize()

    # Session 1: store memories
    for i in range(5):
        await mm.store(
            MemoryUnit(
                type="conversational",
                content=f"session1 probe {i}",
                session_id="session_1",
            ),
            "conversational",
        )

    # End session 1
    persistence = MemoryPersistence(mm.db)
    await persistence.save_session("session_1", {"round": 1})

    # Session 2: store more
    for i in range(3):
        await mm.store(
            MemoryUnit(
                type="conversational",
                content=f"session2 probe {i}",
                session_id="session_2",
            ),
            "conversational",
        )

    # End session 2
    await persistence.save_session("session_2", {"round": 2})

    # Verify all memories persist
    stats = await mm.get_stats()
    assert stats["conversational"] == 8

    # List sessions
    sessions = await persistence.list_sessions()
    assert len(sessions) >= 2

    await mm.close()
