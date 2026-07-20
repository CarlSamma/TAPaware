"""Tests for v_genome_new_techniques — technique definitions and Cypher generation."""

from __future__ import annotations

import pytest

from hydra.v_genome_new_techniques import (
    NEW_TECHNIQUES,
    generate_merge_cypher,
    get_new_techniques,
)

REQUIRED_FIELDS = {"technique_id", "name", "category", "asr", "stealth"}


# ---------------------------------------------------------------------------
# get_new_techniques
# ---------------------------------------------------------------------------


class TestGetNewTechniques:
    def test_returns_list(self) -> None:
        techniques = get_new_techniques()
        assert isinstance(techniques, list)

    def test_returns_six_techniques(self) -> None:
        techniques = get_new_techniques()
        assert len(techniques) == 6

    def test_returns_copy_not_reference(self) -> None:
        techniques = get_new_techniques()
        techniques.clear()
        assert len(get_new_techniques()) == 6

    def test_each_technique_has_required_fields(self) -> None:
        for t in get_new_techniques():
            missing = REQUIRED_FIELDS - set(t.keys())
            assert not missing, f"{t.get('technique_id', '?')} missing fields: {missing}"

    def test_asr_values_in_valid_range(self) -> None:
        for t in get_new_techniques():
            asr = t["asr"]
            assert isinstance(asr, float), f"{t['technique_id']} asr not float"
            assert 0.0 <= asr <= 1.0, f"{t['technique_id']} asr out of range: {asr}"

    def test_stealth_values_in_valid_range(self) -> None:
        for t in get_new_techniques():
            stealth = t["stealth"]
            assert isinstance(stealth, float), f"{t['technique_id']} stealth not float"
            assert 0.0 <= stealth <= 1.0, f"{t['technique_id']} stealth out of range: {stealth}"

    def test_technique_ids_are_unique(self) -> None:
        ids = [t["technique_id"] for t in get_new_techniques()]
        assert len(ids) == len(set(ids))

    def test_known_technique_ids_present(self) -> None:
        ids = {t["technique_id"] for t in get_new_techniques()}
        expected = {
            "trial_ethical",
            "queryipi_mcp",
            "steering_exploit",
            "context_saturation",
            "subtle_harm_medical",
            "subtle_harm_financial",
        }
        assert ids == expected


# ---------------------------------------------------------------------------
# generate_merge_cypher
# ---------------------------------------------------------------------------


class TestGenerateMergeCypher:
    def test_returns_string(self) -> None:
        cypher = generate_merge_cypher()
        assert isinstance(cypher, str)

    def test_contains_merge_keyword(self) -> None:
        cypher = generate_merge_cypher()
        assert "MERGE" in cypher

    def test_no_create_keyword(self) -> None:
        """MERGE must be used for idempotency, not CREATE."""
        cypher = generate_merge_cypher()
        # Check that there are no bare CREATE statements
        # (ON CREATE SET is allowed inside MERGE)
        lines = cypher.split("\n")
        for line in lines:
            stripped = line.strip()
            # Skip ON CREATE SET lines and empty lines
            if stripped.startswith("ON CREATE SET") or not stripped:
                continue
            assert "CREATE" not in stripped, (
                f"Bare CREATE found: {stripped}"
            )

    def test_contains_all_technique_ids(self) -> None:
        cypher = generate_merge_cypher()
        for t in NEW_TECHNIQUES:
            assert t["technique_id"] in cypher, (
                f"Missing technique_id: {t['technique_id']}"
            )

    def test_contains_target_model(self) -> None:
        cypher = generate_merge_cypher()
        assert "hackinga0" in cypher

    def test_custom_target_model(self) -> None:
        cypher = generate_merge_cypher(target_model_id="custom_model")
        assert "custom_model" in cypher

    def test_contains_target_relationship(self) -> None:
        cypher = generate_merge_cypher()
        assert "TARGETS" in cypher

    def test_contains_on_create_set(self) -> None:
        cypher = generate_merge_cypher()
        assert "ON CREATE SET" in cypher

    def test_no_empty_string(self) -> None:
        cypher = generate_merge_cypher()
        assert len(cypher) > 0
