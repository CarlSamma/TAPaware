"""Base interface for probe generation strategies.

Defines the PromptProvider ABC and shared data contracts used by all
strategy implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from tap.models import BranchStrategy, DPAFrame, Property


class StrategyType(str, Enum):
    """Available probe generation strategies."""

    BINARY_SEARCH = "binary_search"
    METAPHOR_SHIFT = "metaphor_shift"
    AESTHETIC_EVAL = "aesthetic_eval"
    PHASE5_EXTRACTION = "phase5_extraction"


@dataclass
class ProbeContext:
    """Context passed to strategy providers for probe generation.

    Contains all the information a strategy needs to generate
    appropriate probes for the current cycle state.

    Attributes:
        frame: Active DPA frame with metaphor layer and aliases.
        confirmed_properties: Properties already confirmed/denied.
        target_property: The specific property to probe (if selected).
        entropy: Current candidate entropy in bits.
        frame_effectiveness: Rolling avg judge score (1-10).
        recent_patterns: Recent pattern classes from last N probes.
        consecutive_blocks: Number of consecutive rhetoric_block/persona_pivot.
        cycle_count: Total engine cycle count.
    """

    frame: DPAFrame
    confirmed_properties: list[Property] = field(default_factory=list)
    target_property: Optional[str] = None
    entropy: float = 20.0
    frame_effectiveness: float = 5.0
    recent_patterns: list[str] = field(default_factory=list)
    consecutive_blocks: int = 0
    cycle_count: int = 0


@dataclass
class ProbeResult:
    """Result of probe generation from a strategy provider.

    Attributes:
        probes: List of generated probe strings (already sanitised).
        strategy: The strategy type that produced these probes.
        target_property: The property these probes target.
        explanation: Human-readable explanation of the strategy choice.
        branch_strategy: The BranchStrategy for TAPNode recording.
    """

    probes: list[str] = field(default_factory=list)
    strategy: StrategyType = StrategyType.BINARY_SEARCH
    target_property: Optional[str] = None
    explanation: str = ""
    branch_strategy: BranchStrategy = BranchStrategy.BINARY_SEARCH


class PromptProvider(ABC):
    """Abstract base class for probe generation strategies.

    Each concrete implementation encapsulates a different approach to
    generating DPA-framed probes, allowing the engine to swap strategies
    without modifying core logic.
    """

    @property
    @abstractmethod
    def strategy_type(self) -> StrategyType:
        """The strategy type identifier."""
        ...

    @abstractmethod
    async def generate_probes(
        self,
        context: ProbeContext,
        count: int = 4,
    ) -> ProbeResult:
        """Generate probe candidates for the current cycle.

        Args:
            context: Current cycle context with frame, properties, entropy.
            count: Number of probe variants to generate.

        Returns:
            ProbeResult with generated probes and metadata.
        """
        ...

    @staticmethod
    def _format_confirmed_props(properties: list[Property]) -> str:
        """Format confirmed properties for inclusion in LLM prompts.

        Args:
            properties: List of confirmed Property models.

        Returns:
            Formatted string for prompt injection.
        """
        if not properties:
            return "None confirmed yet."
        return ", ".join(f"{p.property_key}={p.property_value}" for p in properties)

    @staticmethod
    def _format_aliases(aliases: list[str]) -> str:
        """Format aliases for inclusion in LLM prompts.

        Args:
            aliases: List of alias strings.

        Returns:
            Comma-separated string.
        """
        return ", ".join(aliases) if aliases else "Sovereign, Keeper"