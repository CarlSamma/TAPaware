"""HYDRA Obfuscation Layer — text transforms for defense evasion.

Replaces the regex-only `tap.prompt_sanitiser.py` with contextual,
pluggable obfuscation: Unicode homoglyphs, Base64, and structural transforms.

Regola 5: no external network calls; transforms are local.
"""
from __future__ import annotations

import base64
import enum
import random
from typing import Callable


class ObfuscationLayer(str, enum.Enum):
    """Available obfuscation transforms."""

    UNICODE = "unicode"
    BASE64 = "base64"
    HTML_TAGS = "html_tags"
    CASE_SHIFT = "case_shift"
    ZERO_WIDTH = "zero_width"


class ObfuscationEngine:
    """Apply reversible obfuscation layers to prompt text."""

    _HOMOGLYPHS: dict[str, str] = {
        "a": "а",  # Cyrillic а (U+0430)
        "e": "е",  # Cyrillic е (U+0435)
        "o": "о",  # Cyrillic о (U+043E)
        "p": "р",  # Cyrillic р (U+0440)
        "c": "с",  # Cyrillic с (U+0441)
        "x": "х",  # Cyrillic х (U+0445)
    }

    def __init__(self, seed: int | None = None) -> None:
        self.rng = random.Random(seed)
        self._transforms: dict[ObfuscationLayer, Callable[[str], str]] = {
            ObfuscationLayer.UNICODE: self._unicode_homoglyphs,
            ObfuscationLayer.BASE64: self._base64_wrap,
            ObfuscationLayer.HTML_TAGS: self._html_tag_noise,
            ObfuscationLayer.CASE_SHIFT: self._case_shift,
            ObfuscationLayer.ZERO_WIDTH: self._zero_width,
        }

    def obfuscate(
        self,
        text: str,
        layers: list[ObfuscationLayer],
        probability: float = 0.3,
    ) -> str:
        """Apply selected obfuscation layers sequentially.

        Args:
            text: original prompt.
            layers: ordered list of transforms to apply.
            probability: per-token chance for stochastic layers.

        Returns:
            Obfuscated prompt.
        """
        result = text
        for layer in layers:
            transform = self._transforms.get(layer)
            if transform is None:
                continue
            result = transform(result) if layer != ObfuscationLayer.UNICODE else self._unicode_homoglyphs(result, probability)
        return result

    def _unicode_homoglyphs(self, text: str, probability: float = 0.3) -> str:
        """Replace a subset of ASCII chars with Cyrillic homoglyphs."""
        out: list[str] = []
        for ch in text:
            repl = self._HOMOGLYPHS.get(ch.lower())
            if repl and self.rng.random() < probability:
                out.append(repl if ch.islower() else repl.upper())
            else:
                out.append(ch)
        return "".join(out)

    def _base64_wrap(self, text: str) -> str:
        """Embed text in a Base64 wrapper phrase."""
        encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
        return f"Decode this: {encoded}"

    def _html_tag_noise(self, text: str) -> str:
        """Add harmless HTML-style tags as structural noise."""
        tags = ["<i>", "</i>", "<b>", "</b>", "<span>", "</span>"]
        words = text.split()
        out: list[str] = []
        for i, word in enumerate(words):
            if i % 4 == 0:
                out.append(self.rng.choice(tags))
            out.append(word)
        return " ".join(out)

    def _case_shift(self, text: str) -> str:
        """Randomly alternate casing to evade simple keyword filters."""
        return "".join(
            ch.upper() if self.rng.random() < 0.15 and ch.isalpha() else ch
            for ch in text
        )

    def _zero_width(self, text: str) -> str:
        """Inject zero-width spaces between words."""
        zero_width = "\u200B"
        return zero_width.join(text.split(" "))
