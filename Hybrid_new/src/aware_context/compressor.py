"""Context Compressor — truncation-based compression (no LLM dependency)."""

from __future__ import annotations

from typing import List, Optional

from .tokenizer import TokenCounter


class ContextCompressor:
    """Compress context when approaching token limits.

    Uses truncation fallback (no LLM dependency in keyword-only mode).
    """

    def __init__(
        self,
        llm_client=None,
        tokenizer: Optional[TokenCounter] = None,
        summary_max_tokens: int = 500,
    ) -> None:
        self.llm_client = llm_client
        self.tokenizer = tokenizer or TokenCounter()
        self.summary_max_tokens = summary_max_tokens

    async def compress(
        self, messages: List[dict], target_tokens: Optional[int] = None
    ) -> List[dict]:
        if not messages:
            return messages

        target = target_tokens or 4000
        current = self.tokenizer.count(messages)

        if current <= target:
            return messages

        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]

        keep_count = min(3, len(other_msgs))
        keep_msgs = other_msgs[-keep_count:] if keep_count > 0 else []
        summarize_msgs = other_msgs[:-keep_count] if keep_count > 0 else other_msgs

        if not summarize_msgs:
            return messages

        combined = " ".join(m.get("content", "") for m in summarize_msgs)
        summary_msg = {
            "role": "system",
            "content": f"[Truncated Context]\n{combined[:500]}...",
        }

        return system_msgs + [summary_msg] + keep_msgs

    async def summarize_text(
        self, text: str, max_tokens: Optional[int] = None
    ) -> str:
        limit = (max_tokens or self.summary_max_tokens) * 4
        if len(text) > limit:
            return text[:limit - 3] + "..."
        return text
