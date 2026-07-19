"""Context Monitor — usage tracking + auto-trigger at 80%."""


class ContextMonitor:
    """Monitor context window usage and trigger compression.

    Automatically triggers summarization when context exceeds threshold.
    """

    def __init__(self, max_tokens: int = 8000, threshold: float = 0.8):
        self.max_tokens = max_tokens
        self.threshold = threshold
        self.current_usage = 0

    def check(self, token_count: int) -> bool:
        """Check if compression is needed.

        Args:
            token_count: Current token count

        Returns:
            True if compression needed
        """
        self.current_usage = token_count
        return token_count > self.max_tokens * self.threshold

    def get_usage_percentage(self) -> float:
        """Get current usage as percentage."""
        return (self.current_usage / self.max_tokens) * 100 if self.max_tokens > 0 else 0
