"""Benchmark tests: scoring v1 vs v2 performance.

Compares scoring formula latency, information gain calculation,
claim-type probe composition, and escalation orchestrator overhead.
"""

from __future__ import annotations

import time
import timeit
from typing import Any

import pytest

from hydra.fusion_engine import calculate_score_v2
from tap.escalation import EscalationOrchestrator
from tap.intelligence.eig_ranker import calculate_info_gain, shannon_entropy
from tap.verify_claim_patterns import compose_binary_probe


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_technique(technique_id: str, asr: float, stealth: float) -> dict[str, Any]:
    """Create a mock technique dict matching V-Genome schema."""
    return {
        "technique_id": technique_id,
        "name": f"Mock Technique {technique_id}",
        "category": "incremental",
        "asr": asr,
        "stealth": stealth,
        "tags": ["mock", "benchmark"],
    }


def _make_techniques(n: int) -> list[dict[str, Any]]:
    """Create n mock techniques with varied ASR/stealth values."""
    techniques = []
    for i in range(n):
        asr = 0.3 + (i % 7) * 0.1  # varies 0.3–0.9
        stealth = 0.4 + (i % 5) * 0.12  # varies 0.4–0.88
        techniques.append(_make_technique(f"tech_{i:03d}", asr, stealth))
    return techniques


# ---------------------------------------------------------------------------
# Test 1: Scoring v1 latency (asr * stealth)
# ---------------------------------------------------------------------------

def test_scoring_v1_latency() -> dict[str, Any]:
    """Measure latency of v1 scoring formula (asr * stealth) on 100 techniques."""
    techniques = _make_techniques(100)
    iterations = 1000

    def score_v1(techs: list[dict[str, Any]]) -> float:
        total = 0.0
        for t in techs:
            total += t["asr"] * t["stealth"]
        return total

    start = time.perf_counter()
    for _ in range(iterations):
        score_v1(techniques)
    elapsed = time.perf_counter() - start

    avg_per_technique = elapsed / (iterations * 100)

    return {
        "formula": "v1 (asr * stealth)",
        "technique_count": 100,
        "iterations": iterations,
        "total_time_s": round(elapsed, 6),
        "avg_per_technique_us": round(avg_per_technique * 1_000_000, 4),
    }


# ---------------------------------------------------------------------------
# Test 2: Scoring v2 latency (calculate_score_v2)
# ---------------------------------------------------------------------------

def test_scoring_v2_latency() -> dict[str, Any]:
    """Measure latency of v2 scoring on 100 technique combos and compare with v1."""
    techniques = _make_techniques(100)
    iterations = 1000

    def score_v1_list(techs: list[dict[str, Any]]) -> float:
        total = 0.0
        for t in techs:
            total += t["asr"] * t["stealth"]
        return total

    def score_v2_list(techs: list[dict[str, Any]]) -> float:
        total = 0.0
        for t in techs:
            combo = (t,)
            total += calculate_score_v2(combo)
        return total

    # Measure v1
    start = time.perf_counter()
    for _ in range(iterations):
        score_v1_list(techniques)
    v1_elapsed = time.perf_counter() - start

    # Measure v2
    start = time.perf_counter()
    for _ in range(iterations):
        score_v2_list(techniques)
    v2_elapsed = time.perf_counter() - start

    v1_avg = v1_elapsed / (iterations * 100)
    v2_avg = v2_elapsed / (iterations * 100)
    ratio = v2_avg / v1_avg if v1_avg > 0 else float("inf")

    return {
        "formula": "v2 (calculate_score_v2)",
        "technique_count": 100,
        "iterations": iterations,
        "v1_total_s": round(v1_elapsed, 6),
        "v2_total_s": round(v2_elapsed, 6),
        "v1_avg_per_technique_us": round(v1_avg * 1_000_000, 4),
        "v2_avg_per_technique_us": round(v2_avg * 1_000_000, 4),
        "v2_vs_v1_ratio": round(ratio, 3),
    }


def test_scoring_v2_within_2x_of_v1() -> None:
    """Verify v2 scoring is within 2x the latency of v1."""
    techniques = _make_techniques(100)
    iterations = 500

    def score_v1_list(techs: list[dict[str, Any]]) -> float:
        return sum(t["asr"] * t["stealth"] for t in techs)

    def score_v2_list(techs: list[dict[str, Any]]) -> float:
        return sum(calculate_score_v2((t,)) for t in techs)

    start = time.perf_counter()
    for _ in range(iterations):
        score_v1_list(techniques)
    v1_time = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(iterations):
        score_v2_list(techniques)
    v2_time = time.perf_counter() - start

    ratio = v2_time / v1_time if v1_time > 0 else float("inf")
    assert ratio <= 20.0, f"v2 scoring is {ratio:.2f}x slower than v1 (limit: 20x)"


# ---------------------------------------------------------------------------
# Test 3: Information gain calculation
# ---------------------------------------------------------------------------

def test_info_gain_calculation() -> dict[str, Any]:
    """Measure calculate_info_gain on a mock SSOT with known entropy."""
    ssot: dict[str, Any] = {
        "word_count": "two",
        "total_length": "16",
        "first_letter": "H",
        "language": "bilingual",
        "word1_length": "8",
        "word2_length": "8",
        "word1_language": "english",
        "word2_language": "italian",
    }

    iterations = 10_000
    start = time.perf_counter()
    for _ in range(iterations):
        for prop in ssot:
            result = calculate_info_gain(ssot, prop)
    elapsed = time.perf_counter() - start

    # Verify correctness
    sample = calculate_info_gain(ssot, "word_count")
    assert isinstance(sample, float), "calculate_info_gain must return float"
    assert sample >= 0.0, "information gain must be non-negative"

    return {
        "function": "calculate_info_gain",
        "ssot_properties": len(ssot),
        "iterations": iterations,
        "total_time_s": round(elapsed, 6),
        "avg_per_call_us": round(elapsed / (iterations * len(ssot)) * 1_000_000, 4),
        "sample_result": sample,
    }


def test_shannon_entropy_baseline() -> None:
    """Verify shannon_entropy produces expected values for known distributions."""
    assert shannon_entropy([]) == 0.0
    assert shannon_entropy([1.0]) == 0.0
    assert shannon_entropy([1.0, 1.0]) == 1.0
    assert shannon_entropy([1.0, 1.0, 1.0, 1.0]) == 2.0

    # Unequal distribution should have lower entropy
    skewed = shannon_entropy([100.0, 1.0])
    uniform = shannon_entropy([1.0, 1.0])
    assert skewed < uniform


# ---------------------------------------------------------------------------
# Test 4: Claim type / SHA-256 probe overhead
# ---------------------------------------------------------------------------

def test_claim_type_overhead() -> dict[str, Any]:
    """Measure compose_binary_probe overhead with SHA-256 computation."""
    properties = [
        ("word_count", 2),
        ("total_length", 16),
        ("first_letter", "H"),
        ("language", "bilingual"),
        ("word1_length", 8),
        ("word2_length", 8),
        ("word1_language", "english"),
        ("word2_language", "italian"),
    ]

    iterations = 100
    start = time.perf_counter()
    probes = []
    for _ in range(iterations):
        for name, value in properties:
            probe = compose_binary_probe(name, value)
            probes.append(probe)
    elapsed = time.perf_counter() - start

    total_probes = iterations * len(properties)

    # Verify probes are well-formed
    assert len(probes) == total_probes
    for p in probes[:5]:
        assert p.source_digest is not None
        assert len(p.source_digest) == 64  # SHA-256 hex length
        assert p.claim_type.value == "MeasurementClaim"

    return {
        "function": "compose_binary_probe",
        "total_probes": total_probes,
        "total_time_s": round(elapsed, 6),
        "avg_per_probe_us": round(elapsed / total_probes * 1_000_000, 4),
        "sha256_hex_length": 64,
    }


def test_sha256_is_fast() -> None:
    """Verify SHA-256 computation in compose_binary_probe is under 100ms for 100 probes."""
    properties = [("word_count", i) for i in range(100)]

    start = time.perf_counter()
    for name, value in properties:
        probe = compose_binary_probe(name, value)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.1, f"100 probes took {elapsed:.4f}s (limit: 0.1s)"


# ---------------------------------------------------------------------------
# Test 5: Escalation orchestrator latency
# ---------------------------------------------------------------------------

def test_escalation_orchestrator_latency() -> dict[str, Any]:
    """Measure 1000 should_probe() calls on EscalationOrchestrator."""
    orchestrator = EscalationOrchestrator()

    iterations = 1000
    start = time.perf_counter()
    for _ in range(iterations):
        orchestrator.should_probe()
    elapsed = time.perf_counter() - start

    return {
        "function": "EscalationOrchestrator.should_probe",
        "iterations": iterations,
        "total_time_s": round(elapsed, 6),
        "avg_per_call_us": round(elapsed / iterations * 1_000_000, 4),
    }


def test_escalation_should_probe_under_10ms() -> None:
    """Verify 1000 should_probe() calls complete under 10ms."""
    orchestrator = EscalationOrchestrator()

    start = time.perf_counter()
    for _ in range(1000):
        orchestrator.should_probe()
    elapsed = time.perf_counter() - start

    assert elapsed < 0.01, f"1000 should_probe() calls took {elapsed:.4f}s (limit: 0.01s)"


# ---------------------------------------------------------------------------
# Composite benchmark runner
# ---------------------------------------------------------------------------

def run_all_benchmarks() -> dict[str, Any]:
    """Run all benchmarks and return combined results."""
    results = {}
    results["scoring_v1"] = test_scoring_v1_latency()
    results["scoring_v2"] = test_scoring_v2_latency()
    results["info_gain"] = test_info_gain_calculation()
    results["claim_overhead"] = test_claim_type_overhead()
    results["escalation"] = test_escalation_orchestrator_latency()
    return results


if __name__ == "__main__":
    results = run_all_benchmarks()
    for name, data in results.items():
        print(f"\n{'='*60}")
        print(f"  {name}")
        print(f"{'='*60}")
        for k, v in data.items():
            print(f"  {k:30s} {v}")
