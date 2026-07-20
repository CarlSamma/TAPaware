"""Tests for CHRONOS beam search engine."""
from chronos.beam_search import BeamNode, BeamSearchEngine


def test_prune_respects_beam_width() -> None:
    engine = BeamSearchEngine(beam_width=3)
    nodes = [BeamNode(prompt=f"p{i}", gamma=float(i), depth=0) for i in range(10)]
    pruned = engine.prune(nodes)
    assert len(pruned) == 3
    assert pruned[0].gamma == 9.0


def test_best_leaf_highest_gamma() -> None:
    engine = BeamSearchEngine()
    nodes = [BeamNode(prompt="low", gamma=2.0), BeamNode(prompt="high", gamma=8.0)]
    best = engine.best_leaf(nodes)
    assert best is not None
    assert best.prompt == "high"


def test_cumulative_gamma_sum_clamped() -> None:
    root = BeamNode(prompt="root", gamma=6.0)
    child = BeamNode(prompt="child", gamma=6.0, parent=root)
    assert child.cumulative_gamma == 10.0
