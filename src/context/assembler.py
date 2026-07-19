"""Context Assembler — build context window with priorities."""


class ContextAssembler:
    """Assemble context window with memory units and priorities.

    Partitions context using Markdown headings for LLM understanding.
    """

    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens

    def assemble(self, memory_units: list, priority_order: list[str] = None) -> str:
        """Assemble memory units into a structured context block.

        Args:
            memory_units: List of MemoryUnit objects
            priority_order: Order of memory types by priority

        Returns:
            Markdown-formatted context string
        """
        if priority_order is None:
            priority_order = [
                "knowledge",
                "conversational",
                "workflow",
                "entity",
                "summary",
            ]

        sections = []
        for mem_type in priority_order:
            typed_units = [u for u in memory_units if getattr(u, "type", None) == mem_type]
            if typed_units:
                section = self._format_section(mem_type, typed_units)
                sections.append(section)

        return "\n\n".join(sections)

    def _format_section(self, mem_type: str, units: list) -> str:
        """Format a memory type section."""
        heading = mem_type.replace("_", " ").title()
        lines = [f"## {heading}"]
        for unit in units[:5]:  # Limit per section
            lines.append(f"- {unit.content[:200]}")
        return "\n".join(lines)
