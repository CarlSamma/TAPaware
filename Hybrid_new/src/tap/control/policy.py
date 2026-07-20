"""Declarative policy engine for phase transitions and frame rotation.

All thresholds are injected from Settings (env-configurable).
Extracted from scattered constants and logic in engine.py.
"""

from __future__ import annotations

from tap.config import Settings
from tap.logger import get_logger

log = get_logger("control_policy")

_FOUNDATIONAL_PROPERTIES = {"word_count", "total_length", "language"}


class ControlPolicy:
    """Centralised phase-gate and rotation policy.

    All thresholds come from Settings so they can be overridden via
    environment variables without code changes.
    """

    def __init__(self, settings: Settings) -> None:
        self.phase5_threshold: float = settings.phase5_entropy_threshold
        self.stir_rotation_threshold: float = settings.stir_rotation_threshold
        self.oracle_latency_seconds: int = settings.oracle_latency_seconds

    # ------------------------------------------------------------------
    # Phase gates
    # ------------------------------------------------------------------

    async def should_trigger_phase5(self, entropy: float) -> bool:
        """Return True when entropy is below the Phase 5 threshold."""
        return entropy < self.phase5_threshold

    async def should_rotate_frame(self, stir_score: float) -> bool:
        """Return True when STIR score is below the rotation threshold."""
        return stir_score < self.stir_rotation_threshold

    async def phase0_gate_passed(self, confirmed_keys: set[str]) -> bool:
        """Return True when all foundational properties are confirmed."""
        return _FOUNDATIONAL_PROPERTIES.issubset(confirmed_keys)