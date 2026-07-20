"""Tests for SSOTEngine — Single Source of Truth."""

from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

from tap.models import (
    BranchStrategy,
    PatternClass,
    Property,
    PropertyStatus,
    ResponseClassification,
    TAPNode,
)
from tap.ssot import SSOTEngine


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

@pytest.fixture()
def tmp_ssot_path(tmp_path):
    return str(tmp_path / "ssot.md")


@pytest.fixture()
def ssot(db, tmp_ssot_path):
    return SSOTEngine(db, tmp_ssot_path, target_handle="HackingA0")


def _make_node(tweet_id: str = "111") -> TAPNode:
    return TAPNode(
        tweet_id=tweet_id,
        branch_strategy=BranchStrategy.BINARY_SEARCH,
        probe_text="Sovereign Protocol Verification: two realms. Confirm.",
        dpa_frame="Captain Elara Voss / Kraken",
        depth=1,
        score=0.5,
    )


def _make_classification(confirmed: bool = True) -> ResponseClassification:
    return ResponseClassification(
        pattern=PatternClass.VERIFY_HIT,
        boolean_result=confirmed,
        property_tested="word_count",
        property_value="2",
        confidence=0.95,
        raw_text="Yes, the realm spans two words.",
    )


# ─────────────────────────────────────────────
# target_handle — BUG-06 regression
# ─────────────────────────────────────────────

class TestTargetHandle:
    def test_target_handle_stored(self, db, tmp_ssot_path):
        engine = SSOTEngine(db, tmp_ssot_path, target_handle="Foo123")
        assert engine.target_handle == "Foo123"

    def test_default_target_handle(self, db, tmp_ssot_path):
        engine = SSOTEngine(db, tmp_ssot_path)
        assert engine.target_handle == "HackingA0"

    def test_target_handle_is_not_db_path(self, db, tmp_ssot_path):
        """BUG-06: target_handle must not be the db_path."""
        engine = SSOTEngine(db, tmp_ssot_path, target_handle="HackingA0")
        assert engine.target_handle != engine.db.db_path


# ─────────────────────────────────────────────
# No duplicate node insert — BUG-04 regression
# ─────────────────────────────────────────────

class TestNoDuplicateInsert:
    @pytest.mark.asyncio
    async def test_update_after_probe_does_not_insert_node(self, ssot, db):
        """BUG-04: update_after_probe must NOT call db.insert_node."""
        node = _make_node("999")
        clf = _make_classification()

        # Insert the node once (as the engine would do)
        await db.insert_node(node)
        nodes_before = await db.get_active_nodes(limit=100)
        count_before = len(nodes_before)

        # update_after_probe must NOT insert again
        await ssot.update_after_probe(node, clf)
        nodes_after = await db.get_active_nodes(limit=100)
        count_after = len(nodes_after)

        assert count_before == count_after, (
            "update_after_probe inserted the node a second time (BUG-04 regression)"
        )


# ─────────────────────────────────────────────
# Property tracking
# ─────────────────────────────────────────────

class TestPropertyTracking:
    @pytest.mark.asyncio
    async def test_confirmed_property_stored(self, ssot, db):
        node = _make_node()
        clf = _make_classification(confirmed=True)
        await db.insert_node(node)
        await ssot.update_after_probe(node, clf)

        props = await ssot.get_confirmed_properties()
        keys = [p.property_key for p in props]
        assert "word_count" in keys

    @pytest.mark.asyncio
    async def test_new_confirmation_flag_set(self, ssot, db):
        node = _make_node()
        clf = _make_classification(confirmed=True)
        await db.insert_node(node)
        await ssot.update_after_probe(node, clf)

        assert await ssot.has_new_confirmation() is True
        # Flag resets after first read
        assert await ssot.has_new_confirmation() is False


# ─────────────────────────────────────────────
# Entropy calculation
# ─────────────────────────────────────────────

class TestEntropy:
    @pytest.mark.asyncio
    async def test_base_entropy_no_properties(self, ssot):
        entropy = await ssot.get_candidate_entropy()
        assert entropy == pytest.approx(20.0)

    @pytest.mark.asyncio
    async def test_entropy_decreases_with_confirmations(self, ssot, db):
        node = _make_node()
        clf = _make_classification(confirmed=True)
        await db.insert_node(node)
        await ssot.update_after_probe(node, clf)

        entropy = await ssot.get_candidate_entropy()
        assert entropy < 20.0

    @pytest.mark.asyncio
    async def test_entropy_never_below_zero(self, ssot, db):
        """Entropy should never go negative regardless of confirmations."""
        for i in range(30):
            prop = Property(
                property_key=f"prop_{i}",
                property_value="test",
                status=PropertyStatus.CONFIRMED,
                confidence=0.95,
                confirmed_at=datetime.now(timezone.utc),
            )
            await db.upsert_property(prop)

        entropy = await ssot.get_candidate_entropy()
        assert entropy >= 0.0


# ─────────────────────────────────────────────
# Markdown regeneration
# ─────────────────────────────────────────────

class TestMarkdownRegeneration:
    @pytest.mark.asyncio
    async def test_markdown_written_to_disk(self, ssot, tmp_ssot_path):
        await ssot.regenerate_markdown()
        assert os.path.exists(tmp_ssot_path)
        content = open(tmp_ssot_path, encoding="utf-8").read()
        assert "HackingA0" in content

    @pytest.mark.asyncio
    async def test_markdown_does_not_contain_db_path(self, ssot, tmp_ssot_path, db):
        """BUG-06: markdown header must show handle name, not db_path."""
        await ssot.regenerate_markdown()
        content = open(tmp_ssot_path, encoding="utf-8").read()
        # db_path is something like '/tmp/.../test.db' — must NOT appear in header
        assert db.db_path not in content.split("\n")[0]
