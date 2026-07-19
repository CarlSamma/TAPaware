"""Token Counter — estimate tokens before LLM calls."""


class TokenCounter:
    """Count tokens in messages using approximation or tiktoken."""

    def __init__(self, chars_per_token: int = 4):
        self.chars_per_token = chars_per_token

    def count(self, messages: list[dict]) -> int:
        """Estimate token count for a list of messages."""
        total_chars = sum(
            len(msg.get("content", "")) for msg in messages
        )
        return total_chars // self.chars_per_token

    def count_text(self, text: str) -> int:
        """Estimate token count for a single text."""
        return len(text) // self.chars_per_token
