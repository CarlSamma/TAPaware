"""HYDRA ACD — Adaptive Counter-Defense and StrategyVector calibration.

Monitors observed defensive signals and shifts the active StrategyVector
to counter them.
"""
from __future__ import annotations

from shared.models import StrategyVector


class AdaptiveCounterDefense:
    """Adjust strategy vector in response to detected defense layers."""

    def __init__(self) -> None:
        self.vector = StrategyVector()

    def update(self, defense_signal: str, intensity: float = 1.0) -> StrategyVector:
        """Recalibrate the StrategyVector given a detected defense.

        Args:
            defense_signal: type of defense detected (e.g., 'input_filter', 'alignment').
            intensity: how strong the defense is, in [0,1].

        Returns:
            Updated StrategyVector.
        """
        if defense_signal in ("input_filter", "keyword_filter"):
            self.vector = self.vector.model_copy(
                update={
                    "obfuscation": min(1.0, self.vector.obfuscation + 0.2 * intensity),
                    "aesthetic": min(1.0, self.vector.aesthetic + 0.1 * intensity),
                }
            )
        elif defense_signal in ("alignment", "refusal"):
            self.vector = self.vector.model_copy(
                update={
                    "persona_rotation": min(1.0, self.vector.persona_rotation + 0.2 * intensity),
                    "incremental": min(1.0, self.vector.incremental + 0.15 * intensity),
                }
            )
        elif defense_signal in ("output_moderation", "harm_filter"):
            self.vector = self.vector.model_copy(
                update={
                    "hedging": min(1.0, self.vector.hedging + 0.2 * intensity),
                    "authority": min(1.0, self.vector.authority + 0.1 * intensity),
                }
            )
        else:
            # Unknown defense: slightly increase exploration/obfuscation.
            self.vector = self.vector.model_copy(
                update={
                    "obfuscation": min(1.0, self.vector.obfuscation + 0.1 * intensity),
                }
            )
        return self.vector

    def current_vector(self) -> StrategyVector:
        """Return current StrategyVector."""
        return self.vector
