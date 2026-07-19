"""Workflow Memory — procedural memory of action patterns."""

from .manager import MemoryUnit


class WorkflowMemory:
    """Procedural memory of successful attack patterns and tool sequences.

    Maps to TAP's `probe_memory` + V-Genome provenance.
    """

    def __init__(self, db=None, vector_store=None):
        self.db = db
        self.vector_store = vector_store

    async def store(self, unit: MemoryUnit) -> bool:
        return True

    async def recall(self, query: str, limit: int = 10, threshold: float = 0.5):
        return []

    async def semantic_dedup(self, content: str, threshold: float = 0.85) -> bool:
        """Check if content is semantically similar to recent items."""
        return False

    async def count(self) -> int:
        return 0
