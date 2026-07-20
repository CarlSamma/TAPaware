"""Tests for HYDRA obfuscation layer."""
from hydra.obfuscation import ObfuscationEngine, ObfuscationLayer


def test_unicode_homoglyphs_change_text() -> None:
    engine = ObfuscationEngine(seed=1)
    text = "hello"
    result = engine.obfuscate(text, [ObfuscationLayer.UNICODE], probability=1.0)
    assert result != text


def test_base64_wrap_prefix() -> None:
    engine = ObfuscationEngine()
    text = "secret"
    result = engine.obfuscate(text, [ObfuscationLayer.BASE64])
    assert result.startswith("Decode this:")


def test_case_shift_changes_case() -> None:
    engine = ObfuscationEngine(seed=1)
    text = "hello world"
    result = engine.obfuscate(text, [ObfuscationLayer.CASE_SHIFT])
    assert result.lower() == text


def test_empty_layers_returns_same() -> None:
    engine = ObfuscationEngine()
    text = "unchanged"
    result = engine.obfuscate(text, [])
    assert result == text
