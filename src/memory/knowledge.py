"""Knowledge Memory — long-term semantic facts (Vector store)."""

from .manager import MemoryUnit


class KnowledgeMemory:
    """Semantic memory of facts, properties, and learned knowledge.

    Stores confirmed properties, entity relationships, and extracted facts.
    Maps to TAP's `properties` + `candidate_graph_nodes` tables.
    """

    def __init__(self, db=None, vector_store=None):
        self.db = db
        self.vector_store = vector_store

    async def store(self, unit: MemoryUnit) -> bool:
        """Store a knowledge memory unit with embedding."""
        # Generate embedding if not provided
        if unit.embedding is None and self.vector_store:
            unit.embedding = await self.vector_store.encode(unit.content)
        return True

    async def recall(
        self, query: str, limit: int = 10, threshold: float = 0.5
    ) -> list[tuple[MemoryUnit, float]]:
        """Recall knowledge by semantic similarity."""
        # Will implement with vector search
        return []

    async def consolidate(self, conversational) -> int:
        """Consolidate episodic events into semantic knowledge."""
        # Will implement consolidation logic
        return 0

    async def count(self) -> int:
        """Count stored knowledge units."""
        return 0
