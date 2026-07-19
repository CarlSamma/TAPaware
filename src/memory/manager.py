"""Unified Memory Manager — CRUD interface for all 7 memory types."""

from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime


@dataclass
class MemoryUnit:
    """Atomic memory representation."""
    type: str  # conversational, knowledge, workflow, toolbox, entity, summary, tool_log
    content: str
    metadata: dict = field(default_factory=dict)
    embedding: Optional[list[float]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    confidence: float = 1.0
    decay_rate: float = 0.1


@dataclass
class RecallResult:
    """Result from memory recall."""
    unit: MemoryUnit
    score: float
    memory_type: str


class MemoryManager:
    """Unified interface for all 7 memory types.

    Provides CRUD operations across different memory stores,
    hiding the complexity of raw SQL or vector queries.
    """

    def __init__(self, db=None, vector_store=None, llm_client=None):
        self.db = db
        self.vector_store = vector_store
        self.llm_client = llm_client

        # Initialize memory stores
        from .conversational import ConversationalMemory
        from .knowledge import KnowledgeMemory
        from .workflow import WorkflowMemory
        from .toolbox import ToolboxMemory
        from .entity import EntityMemory
        from .summary import SummaryMemory
        from .tool_log import ToolLogMemory

        self.conversational = ConversationalMemory(db)
        self.knowledge = KnowledgeMemory(db, vector_store)
        self.workflow = WorkflowMemory(db, vector_store)
        self.toolbox = ToolboxMemory(db, vector_store)
        self.entity = EntityMemory(db, vector_store)
        self.summary = SummaryMemory(db, llm_client)
        self.tool_log = ToolLogMemory(db)

        self._stores = {
            "conversational": self.conversational,
            "knowledge": self.knowledge,
            "workflow": self.workflow,
            "toolbox": self.toolbox,
            "entity": self.entity,
            "summary": self.summary,
            "tool_log": self.tool_log,
        }

    async def recall(
        self,
        query: str,
        memory_types: Optional[list[str]] = None,
        limit: int = 10,
        threshold: float = 0.5,
    ) -> list[RecallResult]:
        """Semantic recall across memory types.

        Args:
            query: Search query
            memory_types: Filter by specific types (None = all)
            limit: Max results per type
            threshold: Minimum similarity score

        Returns:
            List of RecallResult sorted by score descending
        """
        results = []
        types_to_search = memory_types or list(self._stores.keys())

        for mem_type in types_to_search:
            if mem_type not in self._stores:
                continue

            store = self._stores[mem_type]
            if hasattr(store, "recall"):
                recalls = await store.recall(query, limit=limit, threshold=threshold)
                for unit, score in recalls:
                    results.append(RecallResult(
                        unit=unit,
                        score=score,
                        memory_type=mem_type,
                    ))

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    async def store(self, unit: MemoryUnit, memory_type: str) -> bool:
        """Store a memory unit with automatic type routing.

        Args:
            unit: MemoryUnit to store
            memory_type: Target memory type

        Returns:
            True if stored successfully
        """
        if memory_type not in self._stores:
            raise ValueError(f"Unknown memory type: {memory_type}")

        store = self._stores[memory_type]
        return await store.store(unit)

    async def consolidate(self) -> dict:
        """Consolidate episodic → semantic, apply decay.

        Returns:
            Statistics about consolidation
        """
        stats = {
            "consolidated": 0,
            "decayed": 0,
            "removed": 0,
        }

        # Consolidate conversational → knowledge
        if hasattr(self.knowledge, "consolidate"):
            consolidated = await self.knowledge.consolidate(self.conversational)
            stats["consolidated"] = consolidated

        # Apply decay to all types
        for mem_type, store in self._stores.items():
            if hasattr(store, "apply_decay"):
                decayed = await store.apply_decay()
                stats["decayed"] += decayed

        return stats

    async def get_stats(self) -> dict:
        """Get memory statistics."""
        stats = {}
        for mem_type, store in self._stores.items():
            if hasattr(store, "count"):
                stats[mem_type] = await store.count()
        return stats
