"""No-op embedding service for keyword-only mode."""

from __future__ import annotations

from typing import List


class EmbeddingService:
    """Stub embedding service — vector search is disabled in keyword-only mode."""

    def __init__(self, model_name: str = "none") -> None:
        self._model_name = model_name

    async def encode(self, text: str) -> List[float]:
        raise NotImplementedError(
            "Embeddings unavailable — install sentence-transformers for vector search"
        )

    async def encode_batch(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError(
            "Embeddings unavailable — install sentence-transformers for vector search"
        )

    @property
    def dimension(self) -> int:
        return 384
