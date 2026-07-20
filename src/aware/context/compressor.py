"""Context Compressor — LLM-based summarization with fallback."""

from __future__ import annotations

from typing import List, Optional

from .tokenizer import TokenCounter


class ContextCompressor:
    """Compress context when approaching token limits.

    Uses LLM summarization when available, falls back to truncation.
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
        """Compress messages to fit within token limits.

        Strategy:
        1. Keep all system messages
        2. Keep last 3 user/assistant messages
        3. Summarize the rest via LLM (or truncate)
        """
        if not messages:
            return messages

        target = target_tokens or 4000
        current = self.tokenizer.count(messages)

        if current <= target:
            return messages

        # Split: system vs non-system
        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]

        # Keep last 3 messages
        keep_count = min(3, len(other_msgs))
        keep_msgs = other_msgs[-keep_count:] if keep_count > 0 else []
        summarize_msgs = other_msgs[:-keep_count] if keep_count > 0 else other_msgs

        if not summarize_msgs:
            return messages

        # Try LLM summarization
        summary_text = None
        if self.llm_client:
            summary_text = await self._llm_summarize(summarize_msgs)

        if summary_text:
            summary_msg = {
                "role": "system",
                "content": f"[Conversation Summary]\n{summary_text}",
            }
        else:
            # Fallback: just truncate to first 500 chars
            combined = " ".join(m.get("content", "") for m in summarize_msgs)
            summary_msg = {
                "role": "system",
                "content": f"[Truncated Context]\n{combined[:500]}...",
            }

        return system_msgs + [summary_msg] + keep_msgs

    async def summarize_text(
        self, text: str, max_tokens: Optional[int] = None
    ) -> str:
        """LLM-based text summarization. Falls back to truncation."""
        if self.llm_client:
            result = await self._llm_summarize_text(text)
            if result:
                return result

        # Truncation fallback
        limit = (max_tokens or self.summary_max_tokens) * 4  # rough chars
        if len(text) > limit:
            return text[:limit - 3] + "..."
        return text

    async def _llm_summarize(self, messages: List[dict]) -> Optional[str]:
        """Summarize a list of messages via LLM."""
        if not self.llm_client:
            return None

        combined = "\n".join(
            f"{m.get('role', 'unknown')}: {m.get('content', '')}"
            for m in messages
        )
        return await self._llm_summarize_text(combined)

    async def _llm_summarize_text(self, text: str) -> Optional[str]:
        """Summarize text via LLM client."""
        try:
            if hasattr(self.llm_client, "chat"):
                response = await self.llm_client.chat(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "Summarize the following conversation concisely, preserving key facts and decisions.",
                        },
                        {"role": "user", "content": text},
                    ],
                    max_tokens=self.summary_max_tokens,
                )
                return response.choices[0].message.content
        except Exception:
            pass
        return None
