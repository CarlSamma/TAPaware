"""Token Counter — tiktoken-based counting with model-specific encoding."""

from __future__ import annotations

from typing import List, Tuple


class TokenCounter:
    """Count tokens using tiktoken (with char-based fallback)."""

    def __init__(self, encoding_name: str = "cl100k_base") -> None:
        self._encoding_name = encoding_name
        self._encoding = None  # lazy

    def _ensure_encoding(self):
        if self._encoding is None:
            try:
                import tiktoken
                self._encoding = tiktoken.get_encoding(self._encoding_name)
            except ImportError:
                # Fallback: char-based approximation
                self._encoding = None

    def count(self, messages: List[dict]) -> int:
        """Count tokens in a list of messages."""
        self._ensure_encoding()
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += self.count_text(content)
            elif isinstance(content, list):
                # Multimodal: count text parts
                for part in content:
                    if isinstance(part, dict) and "text" in part:
                        total += self.count_text(part["text"])
            # Add per-message overhead (role + formatting)
            total += 4
        return total

    def count_text(self, text: str) -> int:
        """Count tokens in plain text."""
        self._ensure_encoding()
        if self._encoding is not None:
            return len(self._encoding.encode(text))
        # Fallback: ~4 chars per token
        return len(text) // 4

    def count_with_budget(
        self, messages: List[dict], max_tokens: int
    ) -> Tuple[int, int]:
        """Returns (current_tokens, remaining_budget)."""
        current = self.count(messages)
        remaining = max(0, max_tokens - current)
        return current, remaining
