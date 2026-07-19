"""Centralized configuration for the Aware framework."""

from __future__ import annotations

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class AwareConfig(BaseSettings):
    """All tunables in one place.  Override via env vars with prefix ``AWARE_``
    or via a ``.env`` file in the project root."""

    # ── Database ──────────────────────────────────────────────
    db_path: str = Field(default="data/aware.db", description="SQLite database path")

    # ── Embeddings ────────────────────────────────────────────
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="sentence-transformers model name",
    )
    embedding_dim: int = Field(default=384, description="Embedding vector dimension")

    # ── Vector Search ─────────────────────────────────────────
    vector_top_k: int = Field(default=20, description="Max ANN results")
    similarity_threshold: float = Field(default=0.5, description="Min cosine similarity")

    # ── Memory Lifecycle ──────────────────────────────────────
    decay_rate: float = Field(default=0.1, description="Exponential decay rate")
    decay_interval_hours: float = Field(default=24.0, description="Hours between decay passes")
    consolidation_threshold: int = Field(
        default=3,
        description="Min occurrences before episodic → semantic promotion",
    )

    # ── Context Engineering ───────────────────────────────────
    context_max_tokens: int = Field(default=8000, description="Max context window tokens")
    context_compression_threshold: float = Field(
        default=0.8,
        description="Trigger compression at this usage ratio",
    )

    # ── LLM ───────────────────────────────────────────────────
    llm_model: str = Field(default="gpt-4o-mini", description="LLM model for summarization")
    llm_api_key: Optional[str] = Field(default=None, description="OpenAI API key")

    model_config = {"env_prefix": "AWARE_", "env_file": ".env", "extra": "ignore"}
