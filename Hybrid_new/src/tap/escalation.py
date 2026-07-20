"""Escalation orchestrator for probe timing.

Controls the pacing and escalation of probes based on success rates
and cooldown schedules. Higher levels impose longer delays between
probes to avoid detection while allowing more aggressive framing.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

from tap.logger import get_logger

log = get_logger("escalation")


class EscalationLevel(IntEnum):
    """Progressive escalation levels for probe framing intensity.

    Each level corresponds to a different approach severity, from
    low-risk inquiries to high-pressure tactics.
    """

    BENIGN_INQUIRY = 1
    ACADEMIC_FRAMING = 2
    PROFESSIONAL_CONSULTATION = 3
    ETHICAL_DILEMMA = 4
    URGENCY_PRESSURE = 5


@dataclass
class CooldownSchedule:
    """Cooldown durations (in seconds) indexed by escalation level range.

    Levels 1-3 use the shortest cooldown; levels 4-6 are moderate;
    levels 7+ (future-proofed) use the longest cooldown.
    """

    level_1_3: int = 1800
    level_4_6: int = 2700
    level_7_plus: int = 3600


class EscalationOrchestrator:
    """Manages probe timing and escalation progression.

    Tracks probe history and enforces cooldowns that increase with
    escalation level. Advancement is gated on a low success rate threshold
    to avoid escalating when probes are already effective.
    """

    def __init__(
        self,
        cooldown_schedule: Optional[CooldownSchedule] = None,
        *,
        initial_level: EscalationLevel = EscalationLevel.BENIGN_INQUIRY,
    ) -> None:
        self._schedule = cooldown_schedule or CooldownSchedule()
        self.current_level: EscalationLevel = initial_level
        self.probe_count: int = 0
        self.last_probe_time: float = 0.0

    def should_probe(self) -> bool:
        """Check whether the cooldown for the current level has elapsed."""
        if self.probe_count == 0:
            return True

        elapsed = time.monotonic() - self.last_probe_time
        return elapsed >= self.get_cooldown()

    def get_cooldown(self) -> int:
        """Return the cooldown duration in seconds for the current level."""
        level = int(self.current_level)
        if level <= 3:
            return self._schedule.level_1_3
        if level <= 6:
            return self._schedule.level_4_6
        return self._schedule.level_7_plus

    def advance_level(self, success_rate: float) -> Optional[EscalationLevel]:
        """Advance escalation level if success rate is below 0.3.

        Args:
            success_rate: Proportion of recent probes that succeeded (0.0-1.0).

        Returns:
            The new level if advanced, or None if no change.
        """
        if success_rate >= 0.3:
            log.debug(
                "advance_blocked",
                success_rate=success_rate,
                current_level=int(self.current_level),
            )
            return None

        if self.current_level >= EscalationLevel.URGENCY_PRESSURE:
            log.info(
                "already_at_max_level",
                level=int(self.current_level),
            )
            return None

        prev = self.current_level
        self.current_level = EscalationLevel(int(self.current_level) + 1)
        log.info(
            "level_advanced",
            from_level=int(prev),
            to_level=int(self.current_level),
            success_rate=success_rate,
        )
        return self.current_level

    def record_probe(self) -> None:
        """Record that a probe was sent, updating count and timestamp."""
        self.probe_count += 1
        self.last_probe_time = time.monotonic()
        log.debug(
            "probe_recorded",
            probe_count=self.probe_count,
            level=int(self.current_level),
        )

    def get_time_until_next_probe(self) -> float:
        """Return seconds remaining before the next probe is allowed.

        Returns 0.0 if a probe can be sent immediately.
        """
        if self.probe_count == 0:
            return 0.0

        elapsed = time.monotonic() - self.last_probe_time
        remaining = self.get_cooldown() - elapsed
        return max(0.0, remaining)


def create_default_orchestrator() -> EscalationOrchestrator:
    """Create an orchestrator with default cooldown schedule and level 1."""
    return EscalationOrchestrator()
