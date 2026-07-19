"""Tool Log Memory — audit trail of raw tool I/O."""

from .manager import MemoryUnit


class ToolLogMemory:
    """Audit trail of tool invocations and results.

    Maps to TAP's `event_log` table with structured querying.
    """

    def __init__(self, db=None):
        self.db = db

    async def store(self, unit: MemoryUnit) -> bool:
        return True

    async def recall(self, query: str, limit: int = 10, threshold: float = 0.5):
        return []

    async def count(self) -> int:
        return 0
