"""Conversational Memory — episodic chat history (SQLite SQL)."""

from .manager import MemoryUnit


class ConversationalMemory:
    """Episodic memory of conversations and interactions.

    Stores raw events from the attack cycle: probes, replies, classifications.
    Maps to TAP's `event_log` + `tweets` tables.
    """

    def __init__(self, db=None):
        self.db = db

    async def store(self, unit: MemoryUnit) -> bool:
        """Store a conversational memory unit."""
        if self.db:
            # Store in event_log table
            pass
        return True

    async def recall(
        self, query: str, limit: int = 10, threshold: float = 0.5
    ) -> list[tuple[MemoryUnit, float]]:
        """Recall conversational memories by keyword search."""
        # For now, return empty — will implement with vector search
        return []

    async def count(self) -> int:
        """Count stored conversational memories."""
        return 0
