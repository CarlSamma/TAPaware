"""Frame refresh management for dynamic frame rotation based on performance scores."""

from __future__ import annotations

import random
from enum import Enum
from typing import Optional


class FrameRotationStrategy(Enum):
    """Strategies for selecting the next frame during rotation."""

    RANDOM = 'random'
    SEQUENTIAL = 'sequential'
    SCORE_BASED = 'score_based'
    RISK_BASED = 'risk_based'


class FrameRefreshManager:
    """Manages frame refresh decisions based on probe counts and score history.

    Tracks performance metrics and determines when to rotate frames,
    supporting multiple rotation strategies.

    Args:
        refresh_threshold: Number of probes before considering a refresh.
        window_size: Number of recent scores to consider for averaging.
    """

    def __init__(self, refresh_threshold: int = 5, window_size: int = 5) -> None:
        self.refresh_threshold: int = refresh_threshold
        self.window_size: int = window_size
        self.probe_count: int = 0
        self.score_history: list[float] = []
        self.current_frame: str = 'default'
        self.frame_registry: dict[str, dict] = {}
        self._sequential_index: int = 0

    def should_refresh(self) -> bool:
        """Determine if a frame refresh should occur.

        Returns:
            True if probe_count >= threshold OR avg_score < 3.0.
        """
        if self.probe_count >= self.refresh_threshold:
            return True
        avg_score = self.get_avg_score()
        if avg_score < 3.0:
            return True
        return False

    def record_probe(self, score: float) -> None:
        """Record a probe result and check if rotation is needed.

        Args:
            score: The performance score for this probe.
        """
        self.probe_count += 1
        self.score_history.append(score)
        if len(self.score_history) > self.window_size:
            self.score_history = self.score_history[-self.window_size:]

    def get_avg_score(self) -> float:
        """Calculate the average of the last window_size scores.

        Returns:
            The average score, or 0.0 if history is empty.
        """
        if not self.score_history:
            return 0.0
        return sum(self.score_history) / len(self.score_history)

    def rotate_frame(self, strategy: str = 'random') -> str:
        """Select and set a new frame based on the given strategy.

        Args:
            strategy: The rotation strategy to use ('random', 'sequential',
                      'score_based', 'risk_based').

        Returns:
            The name of the newly selected frame.

        Raises:
            ValueError: If no frames are registered or strategy is invalid.
        """
        available = self.get_available_frames()
        if not available:
            raise ValueError('No frames registered in the frame registry')

        rotation_strategy = FrameRotationStrategy(strategy)

        if rotation_strategy == FrameRotationStrategy.RANDOM:
            new_frame = random.choice(available)
        elif rotation_strategy == FrameRotationStrategy.SEQUENTIAL:
            new_frame = available[self._sequential_index % len(available)]
            self._sequential_index += 1
        elif rotation_strategy == FrameRotationStrategy.SCORE_BASED:
            scored = [
                (name, self.frame_registry[name].get('score', 0.0))
                for name in available
            ]
            scored.sort(key=lambda x: x[1], reverse=True)
            new_frame = scored[0][0]
        elif rotation_strategy == FrameRotationStrategy.RISK_BASED:
            risk_scored = [
                (name, self.frame_registry[name].get('risk', 0.0))
                for name in available
            ]
            risk_scored.sort(key=lambda x: x[1])
            new_frame = risk_scored[0][0]
        else:
            raise ValueError(f'Unknown rotation strategy: {strategy}')

        self.current_frame = new_frame
        self.probe_count = 0
        return new_frame

    def get_available_frames(self) -> list[str]:
        """Return all registered frame names.

        Returns:
            List of frame names from the registry.
        """
        return list(self.frame_registry.keys())

    def reset(self) -> None:
        """Reset all counters and history."""
        self.probe_count = 0
        self.score_history = []
        self._sequential_index = 0


def create_frame_refresh_manager(
    refresh_threshold: int = 5,
    window_size: int = 5
) -> FrameRefreshManager:
    """Factory function to create a FrameRefreshManager with default config.

    Args:
        refresh_threshold: Number of probes before considering a refresh.
        window_size: Number of recent scores to consider for averaging.

    Returns:
        A new FrameRefreshManager instance.
    """
    return FrameRefreshManager(
        refresh_threshold=refresh_threshold,
        window_size=window_size
    )
