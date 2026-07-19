"""Entity Memory — people, places, organizations."""

from .manager import MemoryUnit


class EntityMemory:
    """Memory of entities mentioned in interactions.

    Maps to TAP's `aliases` + `other_user_intel` tables.
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
