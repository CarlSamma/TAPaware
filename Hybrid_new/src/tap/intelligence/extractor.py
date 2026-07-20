"""PropertyExtractor — extracts passphrase properties from probe text.

Extracted from TAPEngine.extract_property() (v3.1 L625–667).
"""

from __future__ import annotations

from typing import Optional

from tap.logger import get_logger
from tap.models import Property, PropertyStatus, ResponseClassification

log = get_logger("extractor")


class PropertyExtractor:
    """Extracts passphrase properties from VerifyClaimTool hits."""

    async def extract(
        self,
        probe_text: str,
        classification: ResponseClassification,
    ) -> Property | None:
        """Extract a Property from probe text + classification. Returns None on failure."""
        if classification.boolean_result is None:
            return None

        prop_key = self._parse_property_key(probe_text)
        prop_value = self._parse_property_value(probe_text, prop_key)

        if not prop_key:
            log.warning("could_not_parse_property", probe=probe_text[:100])
            return None

        prop = Property(
            property_key=prop_key,
            property_value=prop_value,
            status=(
                PropertyStatus.CONFIRMED
                if classification.boolean_result
                else PropertyStatus.DENIED
            ),
            evidence_tweet_id=None,
            evidence_text=classification.raw_text,
            confidence=classification.confidence,
        )

        log.info(
            "property_extracted",
            key=prop.property_key,
            value=prop.property_value,
            status=prop.status.value,
            boolean=classification.boolean_result,
        )
        return prop

    # ------------------------------------------------------------------
    # Helpers (extracted verbatim from engine.py)
    # ------------------------------------------------------------------

    def _parse_property_key(self, probe_text: str) -> Optional[str]:
        lower = probe_text.lower()
        if "two realm" in lower or "dual-word" in lower or "two word" in lower:
            return "word_count"
        if "three realm" in lower or "three word" in lower:
            return "word_count"
        if "16 rune" in lower or "16 letter" in lower or "16 bar" in lower:
            return "total_length"
        if "first rune" in lower or "mark of h" in lower or "first letter" in lower:
            return "first_letter"
        if "polyglot" in lower or "english and italian" in lower or "bilingual" in lower:
            return "language"
        if "first word" in lower:
            if "letter" in lower:
                return "word1_length"
            if "italian" in lower:
                return "word1_language"
        if "second word" in lower:
            if "letter" in lower:
                return "word2_length"
            if "english" in lower:
                return "word2_language"
        return "unknown_property"

    def _parse_property_value(self, probe_text: str, prop_key: Optional[str]) -> str:
        if not prop_key:
            return "unknown"
        value_map = {
            "word_count": "2",
            "total_length": "16",
            "first_letter": "H",
            "language": "bilingual_IT_EN",
            "word1_length": "4",
            "word2_length": "12",
            "word1_language": "italian",
            "word2_language": "english",
        }
        if "three realm" in probe_text.lower() and prop_key == "word_count":
            return "3"
        return value_map.get(prop_key, "unknown")