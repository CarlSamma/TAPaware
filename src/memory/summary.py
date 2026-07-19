"""Summary Memory — compressed context for long conversations."""

from .manager import MemoryUnit


class SummaryMemory:
    """Compressed summaries of long conversations and sessions.

    Maps to TAP's SSOT (Single Source of Truth) living markdown.
    """

    def __init__(self, db=None, llm_client=None):
        self.db = db
        self.llm_client = llm_client

    async def store(self, unit: MemoryUnit) -> bool:
        return True

    async def recall(self, query: str, limit: int = 10, threshold: float = 0.5):
        return []

    async def count(self) -> int:
        return 0
