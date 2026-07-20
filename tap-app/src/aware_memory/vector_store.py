"""Vector store — keyword-only fallback (no sqlite-vss)."""

from __future__ import annotations

import json
import logging
from typing import List, Optional, Tuple

from .database import Database
from .embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class VectorStore:
    """Vector CRUD + search.

    In keyword-only mode, insert/delete are no-ops and search always
    returns empty results. Memory types fall back to keyword LIKE queries.
    """

    def __init__(self, db: Database, embedder: EmbeddingService) -> None:
        self.db = db
        self.embedder = embedder

    async def insert(self, memory_id: str, embedding: List[float]) -> None:
        pass

    async def search(
        self,
        query: str,
        top_k: int = 20,
        threshold: float = 0.5,
    ) -> List[Tuple[str, float]]:
        return []

    async def delete(self, memory_id: str) -> None:
        pass

    async def update(self, memory_id: str, embedding: List[float]) -> None:
        pass

    async def count(self) -> int:
        return 0
