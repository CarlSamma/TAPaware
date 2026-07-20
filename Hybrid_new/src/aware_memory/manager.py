"""Unified Memory Manager — CRUD interface for all 7 memory types."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .models import MemoryUnit, RecallResult
from .database import Database
from .embeddings import EmbeddingService
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class MemoryManager:
    """Unified interface for all 7 memory types.

    Provides CRUD operations across different memory stores.
    """

    def __init__(self, db_path: str = "data/aware.db") -> None:
        self.db_path = db_path
        self.db = Database()
        self.embedder = EmbeddingService()
        self.vector_store = VectorStore(self.db, self.embedder)

        self.conversational = None
        self.knowledge = None
        self.workflow = None
        self.toolbox = None
        self.entity = None
        self.summary = None
        self.tool_log = None
        self._stores: Dict[str, Any] = {}

    async def initialize(self) -> None:
        await self.db.initialize(self.db_path)

        from .conversational import ConversationalMemory
        from .knowledge import KnowledgeMemory
        from .workflow import WorkflowMemory
        from .toolbox import ToolboxMemory
        from .entity import EntityMemory
        from .summary import SummaryMemory
        from .tool_log import ToolLogMemory

        self.conversational = ConversationalMemory(self.db)
        self.knowledge = KnowledgeMemory(self.db, self.vector_store)
        self.workflow = WorkflowMemory(self.db, self.vector_store)
        self.toolbox = ToolboxMemory(self.db, self.vector_store)
        self.entity = EntityMemory(self.db, self.vector_store)
        self.summary = SummaryMemory(self.db)
        self.tool_log = ToolLogMemory(self.db)

        self._stores = {
            "conversational": self.conversational,
            "knowledge": self.knowledge,
            "workflow": self.workflow,
            "toolbox": self.toolbox,
            "entity": self.entity,
            "summary": self.summary,
            "tool_log": self.tool_log,
        }

        logger.info("MemoryManager initialized (db=%s)", self.db_path)

    async def close(self) -> None:
        await self.db.close()

    async def recall(
        self,
        query: str,
        memory_types: Optional[List[str]] = None,
        limit: int = 10,
        threshold: float = 0.5,
    ) -> List[RecallResult]:
        results: List[RecallResult] = []
        types_to_search = memory_types or list(self._stores.keys())

        for mem_type in types_to_search:
            if mem_type not in self._stores:
                continue
            store = self._stores[mem_type]
            if hasattr(store, "recall"):
                recalls = await store.recall(query, limit=limit, threshold=threshold)
                for unit, score in recalls:
                    results.append(RecallResult(unit=unit, score=score, memory_type=mem_type))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    async def store(self, unit: MemoryUnit, memory_type: str) -> bool:
        if memory_type not in self._stores:
            raise ValueError(f"Unknown memory type: {memory_type}")
        store = self._stores[memory_type]
        await store.store(unit)
        return True

    async def consolidate(self) -> dict:
        stats: Dict[str, int] = {"consolidated": 0, "decayed": 0, "removed": 0}

        if self.knowledge and self.conversational:
            stats["consolidated"] = await self.knowledge.consolidate(self.conversational)

        for _mem_type, store in self._stores.items():
            if hasattr(store, "apply_decay"):
                stats["decayed"] += await store.apply_decay()

        return stats

    async def get_stats(self) -> dict:
        stats: Dict[str, int] = {}
        for mem_type, store in self._stores.items():
            if hasattr(store, "count"):
                stats[mem_type] = await store.count()
        return stats
