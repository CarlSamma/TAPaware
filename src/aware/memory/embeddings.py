"""Embedding generation via sentence-transformers (local) or OpenAI-compatible API (remote)."""

from __future__ import annotations

import logging
from typing import List

import httpx

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Thin wrapper around sentence-transformers with lazy model loading."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model_name = model_name
        self._model = None  # lazy

    def _ensure_model(self) -> None:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info("Loading embedding model '%s' …", self._model_name)
                self._model = SentenceTransformer(self._model_name)
                logger.info("Model loaded (%d dims)", self._model.get_sentence_embedding_dimension())
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for embeddings. "
                    "Install with: pip install sentence-transformers"
                )

    async def encode(self, text: str) -> List[float]:
        """Encode a single text into a normalized embedding vector."""
        self._ensure_model()
        vec = self._model.encode(text, normalize_embeddings=True)
        return vec.tolist()

    async def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode multiple texts in one batch call."""
        if not texts:
            return []
        self._ensure_model()
        vecs = self._model.encode(texts, normalize_embeddings=True)
        return vecs.tolist()

    @property
    def dimension(self) -> int:
        self._ensure_model()
        return self._model.get_sentence_embedding_dimension()


class RemoteEmbeddingService:
    """OpenAI-compatible API embedding service (OpenRouter, OpenAI, etc.)."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        base_url: str = "https://api.openai.com/v1",
        dimension: int = 1536,
    ) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._dimension = dimension
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def encode(self, text: str) -> List[float]:
        return (await self.encode_batch([text]))[0]

    async def encode_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            response = await self._client.post(
                "/embeddings",
                json={"input": texts, "model": self._model},
            )
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]
        except Exception:
            logger.exception("Remote embedding API call failed")
            raise

    async def close(self) -> None:
        await self._client.aclose()

    @property
    def dimension(self) -> int:
        return self._dimension
