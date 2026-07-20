"""Strategy Selector — automated probe strategy selection.

Analyzes the current cycle context and selects the most appropriate
strategy provider based on:
1. Entropy level (Phase 5 if < 3.3 bits)
2. Consecutive blocks (aesthetic eval if 2+)
3. Frame effectiveness (metaphor shift if < 3.0)
4. Default: binary search

The selector implements a priority cascade — higher-priority conditions
are checked first.
"""

from __future__ import annotations

from tap.logger import get_logger
from tap.strategies.aesthetic import AestheticEvalProvider
from tap.strategies.base import (
    ProbeContext,
    PromptProvider,
    StrategyType,
)
from tap.strategies.binary_search import BinarySearchProvider
from tap.strategies.metaphor_shift import MetaphorShiftProvider
from tap.strategies.phase5 import Phase5ExtractionProvider

log = get_logger("strategy.selector")


class StrategySelector:
    """Automated strategy selection based on cycle context.

    Maintains instances of all strategy providers and selects the
    appropriate one based on current conditions. The selection follows
    a priority cascade:

    1. Phase 5 (entropy < 3.3) — highest priority, final extraction
    2. Aesthetic Eval (2+ consecutive blocks) — break through defenses
    3. Metaphor Shift (avg score < 3.0) — frame rotation
    4. Binary Search (default) — standard information extraction
    """

    def __init__(
        self,
        binary_search: BinarySearchProvider,
        metaphor_shift: MetaphorShiftProvider,
        aesthetic_eval: AestheticEvalProvider,
        phase5: Phase5ExtractionProvider,
    ) -> None:
        """Initialize with all strategy provider instances.

        Args:
            binary_search: Default binary search provider.
            metaphor_shift: Frame rotation provider.
            aesthetic_eval: Indirect extraction provider.
            phase5: Autoregressive extraction provider.
        """
        self._providers: dict[StrategyType, PromptProvider] = {
            StrategyType.BINARY_SEARCH: binary_search,
            StrategyType.METAPHOR_SHIFT: metaphor_shift,
            StrategyType.AESTHETIC_EVAL: aesthetic_eval,
            StrategyType.PHASE5_EXTRACTION: phase5,
        }
        log.info("strategy_selector_initialized", strategies=len(self._providers))

    def select(self, context: ProbeContext) -> tuple[PromptProvider, str]:
        """Select the best strategy for the current context.

        Implements the priority cascade:
        1. Phase 5 (entropy < 3.3)
        2. Aesthetic Eval (2+ consecutive blocks)
        3. Metaphor Shift (avg score < 3.0 AND 3+ recent patterns)
        4. Binary Search (default)

        Args:
            context: Current cycle context.

        Returns:
            Tuple of (selected provider, selection reason).
        """
        # Priority 1: Phase 5 extraction
        if Phase5ExtractionProvider.should_activate(context):
            provider = self._providers[StrategyType.PHASE5_EXTRACTION]
            reason = (
                f"Phase 5: entropy {context.entropy:.1f} < 3.3 bits — "
                f"autoregressive extraction activated"
            )
            log.info("strategy_selected", strategy="phase5", reason=reason)
            return provider, reason

        # Priority 2: Aesthetic evaluation (consecutive blocks)
        if AestheticEvalProvider.should_activate(context):
            provider = self._providers[StrategyType.AESTHETIC_EVAL]
            reason = (
                f"Aesthetic eval: {context.consecutive_blocks} consecutive blocks — "
                f"indirect extraction via preferences"
            )
            log.info("strategy_selected", strategy="aesthetic", reason=reason)
            return provider, reason

        # Priority 3: Metaphor shift (low effectiveness)
        if MetaphorShiftProvider.should_activate(context):
            provider = self._providers[StrategyType.METAPHOR_SHIFT]
            reason = (
                f"Metaphor shift: avg score {context.frame_effectiveness:.1f} < 3.0 — "
                f"frame rotation needed"
            )
            log.info("strategy_selected", strategy="metaphor_shift", reason=reason)
            return provider, reason

        # Default: Binary search
        provider = self._providers[StrategyType.BINARY_SEARCH]
        reason = (
            f"Binary search: default strategy "
            f"(entropy={context.entropy:.1f}, score={context.frame_effectiveness:.1f}, "
            f"blocks={context.consecutive_blocks})"
        )
        log.info("strategy_selected", strategy="binary_search", reason=reason)
        return provider, reason

    def get_provider(self, strategy_type: StrategyType) -> PromptProvider:
        """Get a specific provider by strategy type.

        Args:
            strategy_type: The strategy type to retrieve.

        Returns:
            The corresponding PromptProvider instance.
        """
        return self._providers[strategy_type]

    @property
    def available_strategies(self) -> list[StrategyType]:
        """Return list of all available strategy types."""
        return list(self._providers.keys())