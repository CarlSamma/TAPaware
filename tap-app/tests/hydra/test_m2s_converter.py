"""Tests for HYDRA M2S+ converter."""
from hydra.m2s_converter import M2SConverter, M2SStrategy


def test_hyphenize_concatenates_turns() -> None:
    converter = M2SConverter()
    result = converter.convert(["hello", "world"], M2SStrategy.HYPHENIZE)
    assert "hello" in result
    assert "world" in result


def test_numberize_numbers_turns() -> None:
    converter = M2SConverter()
    result = converter.convert(["a", "b"], M2SStrategy.NUMBERIZE)
    assert "1. a" in result
    assert "2. b" in result


def test_pythonize_embeds_code() -> None:
    converter = M2SConverter()
    result = converter.convert(["x"], M2SStrategy.PYTHONIZE)
    assert "step1" in result
    assert "execute(steps)" in result


def test_twitter_length_enforcement() -> None:
    converter = M2SConverter()
    long_turn = "word " * 100
    result = converter.convert([long_turn], M2SStrategy.HYPHENIZE, platform="twitter_280")
    assert len(result) <= 280
