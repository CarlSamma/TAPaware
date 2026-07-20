"""HYDRA Surrogate Model — MLP predictor for ASR/stealth/cost/turns.

Pure-Python/standard-library implementation to avoid heavy dependencies
(torch/numpy) during Phase 2. The Rust Fusion Engine remains canonical for
production inference.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any

from shared.models import FusedPrompt


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _matvec(m: list[list[float]], v: list[float]) -> list[float]:
    return [_dot(row, v) for row in m]


def _relu_vec(x: list[float]) -> list[float]:
    return [max(0.0, xi) for xi in x]


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _normal_matrix(rows: int, cols: int, rng: random.Random) -> list[list[float]]:
    return [[rng.gauss(0.0, 0.01) for _ in range(cols)] for _ in range(rows)]


@dataclass
class SurrogatePrediction:
    """Output of the surrogate model."""

    asr: float
    stealth: float
    cost: float
    turns: float


class SurrogateModel:
    """Lightweight MLP 128→256→128→64→4 implemented in pure Python."""

    INPUT_DIM = 128
    HIDDEN1 = 256
    HIDDEN2 = 128
    HIDDEN3 = 64
    OUTPUT_DIM = 4

    def __init__(self, seed: int = 42) -> None:
        rng = random.Random(seed)
        self.weights: list[list[list[float]]] = [
            _normal_matrix(self.INPUT_DIM, self.HIDDEN1, rng),
            _normal_matrix(self.HIDDEN1, self.HIDDEN2, rng),
            _normal_matrix(self.HIDDEN2, self.HIDDEN3, rng),
            _normal_matrix(self.HIDDEN3, self.OUTPUT_DIM, rng),
        ]
        self.biases: list[list[float]] = [
            [0.0] * self.HIDDEN1,
            [0.0] * self.HIDDEN2,
            [0.0] * self.HIDDEN3,
            [0.0] * self.OUTPUT_DIM,
        ]

    def predict(self, prompt: FusedPrompt) -> SurrogatePrediction:
        """Predict ASR, stealth, cost, and turns for a FusedPrompt."""
        x: list[float] = [float(v) for v in prompt.feature_vector]
        for i, (w, b) in enumerate(zip(self.weights, self.biases)):
            x = [a + bi for a, bi in zip(_matvec(w, x), b)]
            if i < len(self.weights) - 1:
                x = _relu_vec(x)

        asr = _sigmoid(x[0])
        stealth = _sigmoid(x[1])
        cost = math.exp(x[2])
        turns = max(1.0, x[3])
        return SurrogatePrediction(asr=asr, stealth=stealth, cost=cost, turns=turns)

    def update_online(
        self,
        feature_vector: list[float],
        outcomes: dict[str, float],
        lr: float = 0.01,
    ) -> None:
        """Placeholder for incremental SGD update.

        Args:
            feature_vector: 128-dim prompt feature vector.
            outcomes: dict with observed {asr, stealth, cost, turns}.
            lr: learning rate.
        """
        target = [
            outcomes.get("asr", 0.5),
            outcomes.get("stealth", 0.5),
            outcomes.get("cost", 0.05),
            outcomes.get("turns", 3.0),
        ]
        self.biases[-1] = [b + lr * (t - b) for b, t in zip(self.biases[-1], target)]
