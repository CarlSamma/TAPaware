"""Context Compressor — summarization + compaction."""


class ContextCompressor:
    """Compress context when approaching token limits.

    Uses summarization to reduce context size while preserving key information.
    """

    def __init__(self, llm_client=None, summary_max_tokens: int = 500):
        self.llm_client = llm_client
        self.summary_max_tokens = summary_max_tokens

    async def compress(self, messages: list[dict]) -> list[dict]:
        """Compress messages to fit within token limits.

        Args:
            messages: List of message dicts

        Returns:
            Compressed message list
        """
        # Simple truncation for now — will implement LLM summarization
        if len(messages) > 10:
            # Keep system message + last 5 messages
            system_msgs = [m for m in messages if m.get("role") == "system"]
            other_msgs = [m for m in messages if m.get("role") != "system"]
            return system_msgs + other_msgs[-5:]
        return messages
