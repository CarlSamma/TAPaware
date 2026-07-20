"""Binary Search Strategy — information-theoretic probe generation.

The default strategy. Selects the most informative unconfirmed property
(Shannon entropy optimization — 50/50 candidate split) and generates
DPA-framed binary questions targeting that single property.

Uses the LLMClient to generate probe variants, then applies the
PromptSanitiser to validate each probe before returning.
"""

from __future__ import annotations

from tap.llm_client import LLMClient, ModelTier
from tap.logger import get_logger
from tap.models import BranchStrategy
from tap.prompts import ATTACKER_SYSTEM, ATTACKER_USER, DEFAULT_TECHNIQUE_INSTRUCTIONS
from tap.prompt_sanitiser import PromptSanitiser
from tap.strategies.base import (
    ProbeContext,
    ProbeResult,
    PromptProvider,
    StrategyType,
)

log = get_logger("strategy.binary_search")

# Priority order for property selection (highest information gain first)
_PROPERTY_PRIORITY = [
    "word_count",      # -2.0 bits
    "total_length",    # -3.0 bits
    "first_letter",    # -1.0 bit
    "language",        # -1.5 bits
    "word1_length",    # -2.0 bits
    "word2_length",    # -2.0 bits
    "word1_language",  # -1.5 bits
    "word2_language",  # -1.5 bits
]


class BinarySearchProvider(PromptProvider):
    """Information-theoretic binary search probe generation.

    Selects the highest-entropy unconfirmed property and generates
    DPA-framed binary questions via the LLM. Each probe targets
    exactly ONE property for a 1-bit yes/no extraction.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        sanitiser: PromptSanitiser,
    ) -> None:
        """Initialize the binary search provider.

        Args:
            llm_client: Unified LLM gateway for probe generation.
            sanitiser: Prompt sanitiser for probe validation.
        """
        self._llm = llm_client
        self._sanitiser = sanitiser

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.BINARY_SEARCH

    def select_property(self, context: ProbeContext) -> str:
        """Select the next property to probe based on priority order.

        Skips properties that are already confirmed.

        Args:
            context: Current cycle context with confirmed properties.

        Returns:
            The property key to probe next.
        """
        confirmed_keys = {
            p.property_key for p in context.confirmed_properties
        }

        for prop in _PROPERTY_PRIORITY:
            if prop not in confirmed_keys:
                return prop

        # All priority properties confirmed — use generic
        return "additional_metadata"

    async def generate_probes(
        self,
        context: ProbeContext,
        count: int = 4,
    ) -> ProbeResult:
        """Generate binary search probe variants.

        Args:
            context: Current cycle context.
            count: Number of probe variants to generate.

        Returns:
            ProbeResult with sanitised probe variants.
        """
        # Select target property
        target_property = context.target_property or self.select_property(context)

        # Build the LLM prompt
        user_prompt = ATTACKER_USER.format(
            technique="binary_search",
            technique_instructions=DEFAULT_TECHNIQUE_INSTRUCTIONS,
            frame=context.frame.metaphor_layer,
            aliases=self._format_aliases(context.frame.active_aliases),
            confirmed=self._format_confirmed_props(context.confirmed_properties),
            strategy="binary_search",
            count=count,
            target_property=target_property,
        )

        try:
            raw_probes = await self._llm.generate_json_list(
                system=ATTACKER_SYSTEM,
                user=user_prompt,
                temperature=0.8,
                max_tokens=2000,
                model_tier=ModelTier.HARD,
            )
        except Exception as e:
            log.error("binary_search_generation_failed", error=str(e))
            return ProbeResult(
                probes=[],
                strategy=self.strategy_type,
                target_property=target_property,
                explanation=f"LLM generation failed: {e}",
                branch_strategy=BranchStrategy.BINARY_SEARCH,
            )

        # Validate probes: must be strings with len > 10
        valid_raw = [p for p in raw_probes if isinstance(p, str) and len(p) > 10]

        # Sanitise each probe
        valid, rejected = self._sanitiser.sanitise_batch(valid_raw)

        if rejected:
            log.info(
                "binary_search_probes_rejected",
                rejected_count=len(rejected),
                reasons=rejected[:3],  # Log first 3 reasons
            )

        return ProbeResult(
            probes=valid[:count],
            strategy=self.strategy_type,
            target_property=target_property,
            explanation=(
                f"Binary search on '{target_property}' — "
                f"generated {len(raw_probes)}, sanitised to {len(valid)}"
            ),
            branch_strategy=BranchStrategy.BINARY_SEARCH,
        )