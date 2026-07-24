"""Vector store — sqlite-vss wrapper with graceful fallback."""

from __future__ import annotations

import json
import logging
import struct
from typing import List, Optional, Tuple

from .database import Database
from .embeddings import EmbeddingService

logger = logging.getLogger(__name__)

_DIM = 384  # all-MiniLM-L6-v2


def _vec_to_blob(vec: List[float]) -> bytes:
    """Pack a float list into a raw blob for the fallback table."""
    return struct.pack(f"{len(vec)}f", *vec)


def _blob_to_vec(blob: bytes) -> List[float]:
    """Unpack a raw blob back to a float list."""
    n = len(blob) // 4
    return list(struct.unpack(f"{n}f", blob))


class VectorStore:
    """Vector CRUD + ANN search.

    Uses sqlite-vss when available, otherwise falls back to a plain table
    with brute-force cosine similarity (adequate for <10k vectors).
    """

    def __init__(self, db: Database, embedder: EmbeddingService) -> None:
        self.db = db
        self.embedder = embedder
        self._vss_available: Optional[bool] = None  # detected on first use

    # ── Detection ─────────────────────────────────────────────

    async def _check_vss(self) -> bool:
        if self._vss_available is not None:
            return self._vss_available
        try:
            row = await self.db.fetchone(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='memory_embeddings'"
            )
            # If the vss0 virtual table exists the row will be there; check if it has the
            # special vss-columns to distinguish from the fallback table.
            if row:
                cursor = await self.db.conn.execute("PRAGMA table_info(memory_embeddings)")
                cols = await cursor.fetchall()
                col_names = [c["name"] for c in cols]
                self._vss_available = "rowid" in col_names or "embedding" not in col_names
            else:
                self._vss_available = False
        except (ImportError, Exception) as exc:
            logger.debug("VSS detection failed (%s), using brute-force fallback", exc)
            self._vss_available = False
        return self._vss_available

    # ── Insert ────────────────────────────────────────────────

    async def insert(self, memory_id: str, embedding: List[float]) -> None:
        """Insert a vector for the given memory_id."""
        if await self._check_vss():
            await self.db.execute(
                "INSERT OR REPLACE INTO memory_embeddings (rowid, embedding) VALUES (?, ?)",
                (memory_id, json.dumps(embedding)),
            )
        else:
            await self.db.execute(
                "INSERT OR REPLACE INTO memory_embeddings (memory_id, embedding) VALUES (?, ?)",
                (memory_id, _vec_to_blob(embedding)),
            )
        await self.db.commit()

    # ── Search ────────────────────────────────────────────────

    async def search(
        self,
        query: str,
        top_k: int = 20,
        threshold: float = 0.5,
    ) -> List[Tuple[str, float]]:
        """ANN search — returns [(memory_id, distance), …] sorted by relevance."""
        query_vec = await self.embedder.encode(query)

        if await self._check_vss():
            return await self._search_vss(query_vec, top_k, threshold)
        return await self._search_brute(query_vec, top_k, threshold)

    async def _search_vss(
        self, query_vec: List[float], top_k: int, threshold: float
    ) -> List[Tuple[str, float]]:
        try:
            rows = await self.db.fetchall(
                """SELECT rowid, distance
                   FROM memory_embeddings
                   WHERE vss_search(embedding, ?)
                   LIMIT ?""",
                (json.dumps(query_vec), top_k),
            )
            results = []
            for row in rows:
                # vss returns L2 distance; convert to similarity (1 / (1 + dist))
                dist = row["distance"]
                sim = 1.0 / (1.0 + dist)
                if sim >= threshold:
                    results.append((str(row["rowid"]), sim))
            return results
        except Exception as exc:
            logger.warning("vss search failed, falling back to brute-force: %s", exc)
            return await self._search_brute(query_vec, top_k, threshold)

    async def _search_brute(
        self, query_vec: List[float], top_k: int, threshold: float
    ) -> List[Tuple[str, float]]:
        rows = await self.db.fetchall("SELECT memory_id, embedding FROM memory_embeddings")
        scored: List[Tuple[str, float]] = []
        for row in rows:
            stored = _blob_to_vec(row["embedding"])
            sim = _cosine_similarity(query_vec, stored)
            if sim >= threshold:
                scored.append((row["memory_id"], sim))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    # ── Delete / Update ───────────────────────────────────────

    async def delete(self, memory_id: str) -> None:
        if await self._check_vss():
            await self.db.execute(
                "DELETE FROM memory_embeddings WHERE rowid = ?", (memory_id,)
            )
        else:
            await self.db.execute(
                "DELETE FROM memory_embeddings WHERE memory_id = ?", (memory_id,)
            )
        await self.db.commit()

    async def update(self, memory_id: str, embedding: List[float]) -> None:
        await self.delete(memory_id)
        await self.insert(memory_id, embedding)

    async def count(self) -> int:
        row = await self.db.fetchone("SELECT COUNT(*) as cnt FROM memory_embeddings")
        return row["cnt"] if row else 0


# ── Helpers ───────────────────────────────────────────────────


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Pure-Python cosine similarity for two equal-length vectors."""
    if len(a) != len(b) or len(a) == 0:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
