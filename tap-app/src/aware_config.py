"""Aware configuration — maps to TAP's Settings, no separate env vars."""

from __future__ import annotations

from typing import Optional


class AwareConfig:
    """Configuration for Aware memory within TAP.

    Uses sensible defaults. No separate .env variables needed —
    Aware piggybacks on TAP's database directory.
    """

    db_path: str = "data/aware.db"
    embedding_model: str = "none"
    embedding_dim: int = 384
    vector_top_k: int = 20
    similarity_threshold: float = 0.5
    decay_rate: float = 0.1
    decay_interval_hours: float = 24.0
    consolidation_threshold: int = 3
    context_max_tokens: int = 8000
    context_compression_threshold: float = 0.8
    llm_model: str = "gpt-4o-mini"
    llm_api_key: Optional[str] = None
