"""Context Assembler — token-budget-aware priority assembly."""

from __future__ import annotations

from typing import List, Optional

from .tokenizer import TokenCounter


class ContextAssembler:
    """Assemble context window with memory units and priorities."""

    def __init__(
        self, tokenizer: TokenCounter, max_tokens: int = 8000
    ) -> None:
        self.tokenizer = tokenizer
        self.max_tokens = max_tokens

    def assemble(
        self,
        memory_units: list,
        priority_order: Optional[List[str]] = None,
        token_budget: Optional[int] = None,
    ) -> str:
        budget = token_budget or self.max_tokens

        if priority_order is None:
            priority_order = [
                "knowledge",
                "conversational",
                "workflow",
                "entity",
                "summary",
                "toolbox",
                "tool_log",
            ]

        by_type: dict = {}
        for unit in memory_units:
            t = getattr(unit, "type", None)
            if t:
                by_type.setdefault(t, []).append(unit)

        sections: List[str] = []
        used_tokens = 0

        for mem_type in priority_order:
            units = by_type.get(mem_type, [])
            if not units:
                continue

            heading = mem_type.replace("_", " ").title()
            lines = [f"## {heading}"]
            for unit in units[:5]:
                content = unit.content[:300]
                lines.append(f"- {content}")
            section_text = "\n".join(lines)
            section_tokens = self.tokenizer.count_text(section_text)

            if used_tokens + section_tokens <= budget:
                sections.append(section_text)
                used_tokens += section_tokens
            else:
                remaining = budget - used_tokens
                if remaining > 50:
                    truncated = self._truncate_section(mem_type, units, remaining)
                    sections.append(truncated)
                break

        return "\n\n".join(sections)

    def _truncate_section(
        self, mem_type: str, units: list, token_budget: int
    ) -> str:
        heading = mem_type.replace("_", " ").title()
        lines = [f"## {heading}"]
        used = self.tokenizer.count_text(heading)

        for unit in units[:5]:
            content = unit.content[:300]
            line = f"- {content}"
            line_tokens = self.tokenizer.count_text(line)
            if used + line_tokens <= token_budget:
                lines.append(line)
                used += line_tokens
            else:
                break

        return "\n".join(lines)
