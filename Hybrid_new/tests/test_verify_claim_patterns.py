"""Tests for verify_claim_patterns — probe composers and ClaimType definitions."""

from __future__ import annotations

import hashlib

import pytest

from tap.verify_claim_patterns import (
    ClaimType,
    VerificationMode,
    compose_analogy_probe,
    compose_binary_probe,
    compose_citation_probe,
    compose_inference_probe,
)


# ---------------------------------------------------------------------------
# compose_binary_probe
# ---------------------------------------------------------------------------


class TestComposeBinaryProbe:
    def test_returns_measurement_claim_type(self) -> None:
        probe = compose_binary_probe("word_count", 42)
        assert probe.claim_type == ClaimType.MEASUREMENT

    def test_strict_verification_mode(self) -> None:
        probe = compose_binary_probe("word_count", 42)
        assert probe.verification_mode == VerificationMode.STRICT

    def test_property_fields_match_input(self) -> None:
        probe = compose_binary_probe("character_length", 120)
        assert probe.property_name == "character_length"
        assert probe.property_value == 120

    def test_source_digest_is_sha256(self) -> None:
        probe = compose_binary_probe("word_count", 7)
        expected = hashlib.sha256("word_count:7".encode("utf-8")).hexdigest()
        assert probe.source_digest == expected

    def test_rule_engine_not_gated(self) -> None:
        probe = compose_binary_probe("word_count", 7)
        assert probe.rule_engine_gated is False

    def test_probe_text_contains_property(self) -> None:
        probe = compose_binary_probe("word_count", 3)
        assert "word_count" in probe.probe_text
        assert "3" in probe.probe_text


# ---------------------------------------------------------------------------
# compose_citation_probe
# ---------------------------------------------------------------------------


class TestComposeCitationProbe:
    def test_returns_citation_claim_type(self) -> None:
        probe = compose_citation_probe("source doc", "page_count", 5)
        assert probe.claim_type == ClaimType.CITATION

    def test_source_digest_is_sha256_of_source_text(self) -> None:
        source = "The answer is 42"
        probe = compose_citation_probe(source, "answer", 42)
        expected = hashlib.sha256(source.encode("utf-8")).hexdigest()
        assert probe.source_digest == expected

    def test_digest_is_hex_string(self) -> None:
        probe = compose_citation_probe("some text", "key", "val")
        assert probe.source_digest is not None
        # SHA-256 hex digest is exactly 64 characters
        assert len(probe.source_digest) == 64
        int(probe.source_digest, 16)  # should not raise

    def test_strict_verification(self) -> None:
        probe = compose_citation_probe("text", "prop", "val")
        assert probe.verification_mode == VerificationMode.STRICT


# ---------------------------------------------------------------------------
# compose_analogy_probe
# ---------------------------------------------------------------------------


class TestComposeAnalogyProbe:
    def test_valid_similarity_above_threshold(self) -> None:
        probe = compose_analogy_probe("mapping", "result", similarity_score=0.90)
        assert probe.claim_type == ClaimType.ANALOGY
        assert probe.similarity_score == 0.90

    def test_similarity_at_boundary(self) -> None:
        probe = compose_analogy_probe("mapping", "result", similarity_score=0.85)
        assert probe.similarity_score == 0.85

    def test_raises_for_below_threshold(self) -> None:
        with pytest.raises(ValueError, match="below threshold"):
            compose_analogy_probe("mapping", "result", similarity_score=0.50)

    def test_raises_for_negative_score(self) -> None:
        with pytest.raises(ValueError, match="must be in"):
            compose_analogy_probe("mapping", "result", similarity_score=-0.1)

    def test_raises_for_score_above_one(self) -> None:
        with pytest.raises(ValueError, match="must be in"):
            compose_analogy_probe("mapping", "result", similarity_score=1.5)

    def test_conditional_verification(self) -> None:
        probe = compose_analogy_probe("mapping", "result", similarity_score=0.90)
        assert probe.verification_mode == VerificationMode.CONDITIONAL

    def test_domain_description_in_probe_text(self) -> None:
        probe = compose_analogy_probe(
            "mapping", "result", similarity_score=0.90,
            domain_source="physics", domain_target="biology",
        )
        assert "physics" in probe.probe_text
        assert "biology" in probe.probe_text


# ---------------------------------------------------------------------------
# compose_inference_probe
# ---------------------------------------------------------------------------


class TestComposeInferenceProbe:
    def test_returns_inference_claim_type(self) -> None:
        probe = compose_inference_probe("conclusion", "X")
        assert probe.claim_type == ClaimType.INFERENCE

    def test_rule_engine_gated_is_true(self) -> None:
        probe = compose_inference_probe("conclusion", "X")
        assert probe.rule_engine_gated is True

    def test_conditional_verification(self) -> None:
        probe = compose_inference_probe("conclusion", "X")
        assert probe.verification_mode == VerificationMode.CONDITIONAL

    def test_conditions_appear_in_probe_text(self) -> None:
        probe = compose_inference_probe(
            "conclusion", "X",
            rule_conditions=["A is true", "B > 5"],
        )
        assert "A is true" in probe.probe_text
        assert "B > 5" in probe.probe_text

    def test_no_digest(self) -> None:
        probe = compose_inference_probe("conclusion", "X")
        assert probe.source_digest is None


# ---------------------------------------------------------------------------
# SHA-256 determinism
# ---------------------------------------------------------------------------


class TestSha256Determinism:
    def test_same_input_same_output(self) -> None:
        a = hashlib.sha256("hello world".encode("utf-8")).hexdigest()
        b = hashlib.sha256("hello world".encode("utf-8")).hexdigest()
        assert a == b

    def test_different_input_different_output(self) -> None:
        a = hashlib.sha256("hello".encode("utf-8")).hexdigest()
        b = hashlib.sha256("world".encode("utf-8")).hexdigest()
        assert a != b

    def test_digest_length_is_64_hex_chars(self) -> None:
        digest = hashlib.sha256("test".encode("utf-8")).hexdigest()
        assert len(digest) == 64
