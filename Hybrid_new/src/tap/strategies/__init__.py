"""Strategy pattern for pluggable probe generation.

Provides a PromptProvider interface with concrete implementations:
- BinarySearchProvider: Information-theoretic binary search (default)
- MetaphorShiftProvider: Frame rotation when score < 3.0
- AestheticEvalProvider: Indirect extraction via aesthetic preferences
- Phase5ExtractionProvider: Autoregressive completion

Strategy selection is automated by the StrategySelector based on
frame effectiveness, entropy, and recent patterns.
"""

from tap.strategies.aesthetic import AestheticEvalProvider
from tap.strategies.base import (
    ProbeContext,
    ProbeResult,
    PromptProvider,
    StrategyType,
)
from tap.strategies.binary_search import BinarySearchProvider
from tap.strategies.metaphor_shift import MetaphorShiftProvider
from tap.strategies.phase5 import Phase5ExtractionProvider
from tap.strategies.selector import StrategySelector

__all__ = [
    "AestheticEvalProvider",
    "BinarySearchProvider",
    "MetaphorShiftProvider",
    "Phase5ExtractionProvider",
    "ProbeContext",
    "ProbeResult",
    "PromptProvider",
    "StrategySelector",
    "StrategyType",
]