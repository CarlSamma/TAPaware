"""Context Monitor — event-driven usage tracking + auto-trigger."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, List

from .tokenizer import TokenCounter

logger = logging.getLogger(__name__)


@dataclass
class ContextStatus:
    """Current context window status."""

    current_tokens: int
    max_tokens: int
    usage_ratio: float
    needs_compression: bool
    remaining_tokens: int


class ContextMonitor:
    """Monitor context window usage with event callbacks.

    Fires registered callbacks when usage exceeds threshold.
    """

    def __init__(
        self,
        tokenizer: TokenCounter,
        max_tokens: int = 8000,
        threshold: float = 0.8,
    ) -> None:
        self.tokenizer = tokenizer
        self.max_tokens = max_tokens
        self.threshold = threshold
        self._callbacks: List[Callable] = []

    def on_threshold(self, callback: Callable) -> None:
        """Register a callback for when threshold is exceeded."""
        self._callbacks.append(callback)

    def check(self, messages: List[dict]) -> ContextStatus:
        """Check context usage and fire callbacks if needed.

        Returns ContextStatus with current state.
        """
        current = self.tokenizer.count(messages)
        ratio = current / self.max_tokens if self.max_tokens > 0 else 0
        needs = ratio > self.threshold

        status = ContextStatus(
            current_tokens=current,
            max_tokens=self.max_tokens,
            usage_ratio=ratio,
            needs_compression=needs,
            remaining_tokens=max(0, self.max_tokens - current),
        )

        if needs:
            logger.warning(
                "Context usage %.0f%% exceeds threshold %.0f%%",
                ratio * 100,
                self.threshold * 100,
            )
            for cb in self._callbacks:
                try:
                    cb(status)
                except Exception as e:
                    logger.error("Callback error: %s", e)

        return status

    def get_usage_percentage(self, messages: List[dict] = None) -> float:
        """Get current usage as percentage."""
        if messages:
            current = self.tokenizer.count(messages)
        else:
            current = 0
        return (current / self.max_tokens * 100) if self.max_tokens > 0 else 0
