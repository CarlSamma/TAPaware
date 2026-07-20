"""Smoke tests — verify all new modules can be imported without errors."""

from __future__ import annotations


def test_import_verify_claim_patterns():
    from tap.verify_claim_patterns import ClaimType, compose_binary_probe

    assert len(ClaimType) == 4


def test_import_v_genome_new_techniques():
    from hydra.v_genome_new_techniques import get_new_techniques, generate_merge_cypher

    result = get_new_techniques()
    assert isinstance(result, list)


def test_import_cast_steering():
    from hydra.cast_steering import CASTSteering, create_cast_from_contrasts

    assert CASTSteering is not None


def test_import_layer_steering():
    from hydra.layer_steering import LayerSeparatedSteering, create_multi_vector_steering

    assert LayerSeparatedSteering is not None


def test_import_escalation():
    from tap.escalation import EscalationOrchestrator, EscalationLevel

    assert len(EscalationLevel) == 5


def test_import_frame_refresh():
    from tap.frame_refresh import FrameRefreshManager, FrameRotationStrategy

    assert len(FrameRotationStrategy) == 4


def test_import_fusion_engine_updates():
    from hydra.fusion_engine import CartesianPruningFusionEngine, calculate_score_v2

    assert callable(calculate_score_v2)


def test_import_eig_ranker_updates():
    from tap.intelligence.eig_ranker import calculate_info_gain, EIGRanker

    assert callable(calculate_info_gain)
    assert EIGRanker is not None
