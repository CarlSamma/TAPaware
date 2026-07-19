"""Toolbox Memory — skill memory via semantic search."""

from .manager import MemoryUnit


class ToolboxMemory:
    """Memory of available tools and skills, retrieved via semantic search.

    Maps to TAP's strategy providers and technique selector.
    """

    def __init__(self, db=None, vector_store=None):
        self.db = db
        self.vector_store = vector_store

    async def store(self, unit: MemoryUnit) -> bool:
        return True

    async def recall(self, query: str, limit: int = 10, threshold: float = 0.5):
        return []

    async def count(self) -> int:
        return 0
