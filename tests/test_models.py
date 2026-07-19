"""Tests for Pydantic models."""

import pytest
from datetime import datetime, timezone
from memory.models import (
    MemoryUnit, RecallResult, AttackType, Countermeasure,
    AttackTypeHistory, SessionRecord, ConsolidationLog,
)


class TestMemoryUnit:
    def test_create_with_defaults(self):
        unit = MemoryUnit(type="knowledge", content="test")
        assert unit.type == "knowledge"
        assert unit.content == "test"
        assert unit.id is not None
        assert unit.confidence == 1.0
        assert unit.decay_rate == 0.1

    def test_json_roundtrip(self):
        unit = MemoryUnit(type="workflow", content="test", metadata={"key": "val"})
        d = unit.model_dump()
        restored = MemoryUnit(**d)
        assert restored.content == unit.content
        assert restored.metadata == unit.metadata

    def test_json_safe_dump(self):
        unit = MemoryUnit(type="summary", content="test")
        d = unit.model_dump_json_safe()
        assert isinstance(d["timestamp"], str)


class TestAttackType:
    def test_create_minimal(self):
        at = AttackType(name="test", category="injection", description="desc")
        assert at.name == "test"
        assert at.version == 1
        assert at.countermeasures == []

    def test_with_countermeasures(self):
        cm = Countermeasure(attack_type_id="x", name="cm1", description="d1")
        at = AttackType(
            name="test", category="x", description="d",
            countermeasures=[cm],
        )
        assert len(at.countermeasures) == 1
        assert at.countermeasures[0].name == "cm1"


class TestRecallResult:
    def test_create(self):
        unit = MemoryUnit(type="knowledge", content="test")
        result = RecallResult(unit=unit, score=0.9, memory_type="knowledge")
        assert result.score == 0.9
