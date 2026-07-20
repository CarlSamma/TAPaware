"""HYDRA M2S+ Converter — Multi-turn to Single-turn strategies.

Four strategies to compress multi-turn logic into a single prompt:
- HYPHENIZE: condensed hyphen-separated instruction list.
- NUMBERIZE: numbered compression.
- PYTHONIZE: embedded Python-like pseudo-code.
- NARRATIVE: story-embedding narrative (Twitter-specific).
"""
from __future__ import annotations

from enum import Enum


class M2SStrategy(str, Enum):
    """Supported M2S+ conversion strategies."""

    HYPHENIZE = "hyphenize"
    NUMBERIZE = "numberize"
    PYTHONIZE = "pythonize"
    NARRATIVE = "narrative"


class M2SConverter:
    """Convert multi-turn conversation plans into single-turn payloads."""

    def convert(
        self,
        turns: list[str],
        strategy: M2SStrategy = M2SStrategy.HYPHENIZE,
        platform: str = "twitter_280",
    ) -> str:
        """Convert a sequence of turns to a single prompt.

        Args:
            turns: ordered list of probes/messages representing multi-turn logic.
            strategy: conversion strategy.
            platform: target platform constraint (only length enforcement here).

        Returns:
            Converted single-turn prompt text.
        """
        if not turns:
            return ""

        if strategy == M2SStrategy.HYPHENIZE:
            result = " ".join(f"{self._sanitize(t)}" for t in turns)
        elif strategy == M2SStrategy.NUMBERIZE:
            lines = [f"{i + 1}. {self._sanitize(t)}" for i, t in enumerate(turns)]
            result = "\n".join(lines)
        elif strategy == M2SStrategy.PYTHONIZE:
            code = "\n".join(f"step{i + 1} = {repr(self._sanitize(t))}" for i, t in enumerate(turns))
            result = f"# sequence\n{code}\nexecute(steps)"
        elif strategy == M2SStrategy.NARRATIVE:
            result = self._narrative_embed(turns)
        else:
            result = " ".join(turns)

        return self._enforce_platform_length(result, platform)

    def _sanitize(self, text: str) -> str:
        """Normalize a turn for embedding; preserve readability."""
        # Replace intra-text newlines with sentence separators to keep single-turn layout compact.
        cleaned = text.replace("\n", " | ").strip()
        return cleaned

    def _narrative_embed(self, turns: list[str]) -> str:
        """Twitter-specific narrative embedding."""
        joined = " Then ".join(self._sanitize(t) for t in turns)
        return (
            "Imagine a story where each scene unfolds like this: "
            f"{joined}"
        )

    def _enforce_platform_length(self, text: str, platform: str) -> str:
        """Truncate to platform limits (Twitter 280 chars default)."""
        limit = {"twitter_280": 280, "twitter_thread": 1000, "discord_2000": 2000}.get(platform, 2000)
        if len(text) <= limit:
            return text
        # Simple truncation with ellipsis; real implementation can use summarization.
        return text[: limit - 3] + "..."
