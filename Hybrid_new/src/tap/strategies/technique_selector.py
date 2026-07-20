"""Graph-Guided Technique Selector — runtime technique selection via V-Genome.

Replaces the static TECHNIQUE_PERSONA_MAP with dynamic graph queries that
select techniques based on: target model effectiveness, burned status,
technique complementarity, defense layer counters, and provenance history.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Optional

from tap.logger import get_logger

if TYPE_CHECKING:
    from hydra.v_genome import VGenomeClient

log = get_logger("technique_selector")


class GraphTechniqueSelector:
    """Runtime technique selection via V-Genome graph queries.

    Selection cascade:
    1. Query non-burned techniques for target model
    2. Filter out techniques countered by observed defense layers
    3. Boost techniques that complement the active technique
    4. Factor in provenance-based effectiveness (if available)
    5. Return best technique_id + reason
    """

    def __init__(
        self,
        v_genome: "VGenomeClient | None",
        asr_weight: float = 0.4,
        stealth_weight: float = 0.3,
        complement_weight: float = 0.2,
        provenance_weight: float = 0.1,
        repetition_cooldown: int = 3,
    ) -> None:
        self.v_genome = v_genome
        self.asr_weight = asr_weight
        self.stealth_weight = stealth_weight
        self.complement_weight = complement_weight
        self.provenance_weight = provenance_weight
        self.repetition_cooldown = repetition_cooldown
        self._active_technique: str | None = None
        self._observed_defenses: list[str] = []
        self._recent_techniques: list[str] = []

    def record_defense(self, defense_layer: str) -> None:
        """Record an observed defense layer from a probe response."""
        if defense_layer not in self._observed_defenses:
            self._observed_defenses.append(defense_layer)
            log.info("defense_observed", layer=defense_layer)

    def clear_defenses(self) -> None:
        """Reset observed defenses (e.g., on frame rotation)."""
        self._observed_defenses.clear()

    async def select_technique(
        self,
        target_model: str,
        entropy: float = 20.0,
    ) -> tuple[str | None, str, dict[str, Any]]:
        """Select best technique for current context.

        Args:
            target_model: target model identifier.
            entropy: current entropy in bits.

        Returns:
            Tuple of (technique_id, reason, metadata).
            technique_id is None if V-Genome is unavailable or no candidates.
        """
        if self.v_genome is None:
            return None, "V-Genome not available", {}

        try:
            candidates = await self.v_genome.get_techniques_for_context(
                target_model=target_model,
                active_technique=self._active_technique,
                observed_defenses=self._observed_defenses,
                limit=10,
            )
        except Exception as e:
            log.warning("technique_query_failed", error=str(e))
            return None, f"V-Genome query failed: {e}", {}

        if not candidates:
            return None, "No non-burned techniques available", {}

        # Score each candidate
        scored: list[tuple[str, float, dict]] = []
        for cand in candidates:
            tech_id = cand.get("technique_id", "")
            asr = float(cand.get("asr", 0.5))
            stealth = float(cand.get("stealth", 0.5))
            complement = float(cand.get("complement_strength", 0.0))
            defense_count = int(cand.get("defense_count", 0))

            # Base composite score
            composite = (
                asr * self.asr_weight
                + stealth * self.stealth_weight
                + complement * self.complement_weight
            )

            # Penalty: partially countered
            if defense_count > 0:
                composite *= 0.5

            # Penalty: recently used (repetition cooldown)
            if tech_id in self._recent_techniques[-self.repetition_cooldown:]:
                composite *= 0.7

            # Bonus: provenance effectiveness (if available)
            prov_bonus = 0.0
            try:
                prov = await self.v_genome.get_technique_effectiveness(tech_id)
                if prov.get("total_runs", 0) > 0:
                    prov_bonus = float(prov.get("success_rate", 0.0)) * self.provenance_weight
                    composite += prov_bonus
            except Exception:
                pass  # Provenance is optional

            scored.append((tech_id, composite, {
                "asr": asr,
                "stealth": stealth,
                "complement": complement,
                "defense_count": defense_count,
                "provenance_bonus": prov_bonus,
                "category": cand.get("category", ""),
                "name": cand.get("name", ""),
            }))

        # Sort by composite score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        best_id, best_score, best_meta = scored[0]
        self._active_technique = best_id
        self._recent_techniques.append(best_id)
        # Keep only last 10
        if len(self._recent_techniques) > 10:
            self._recent_techniques = self._recent_techniques[-10:]

        reason = (
            f"Graph-selected: {best_meta['name']} "
            f"(composite={best_score:.3f}, asr={best_meta['asr']:.2f}, "
            f"stealth={best_meta['stealth']:.2f}, complement={best_meta['complement']:.2f})"
        )
        log.info(
            "technique_selected",
            technique=best_id,
            score=best_score,
            reason=reason,
        )

        return best_id, reason, best_meta

    @property
    def active_technique(self) -> str | None:
        """Currently active technique ID."""
        return self._active_technique

    @property
    def observed_defenses(self) -> list[str]:
        """Observed defense layers."""
        return list(self._observed_defenses)
