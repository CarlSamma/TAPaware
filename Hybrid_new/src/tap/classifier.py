"""Module 5: Response Pattern Classifier.

Two-tier classification system:
1. Fast regex matching for obvious patterns (~70% of cases)
2. LLM-based classification via OpenRouter for ambiguous cases (~30%)

Pattern categories:
- verify_hit: Bot responds with yes/no/nope (VerifyClaimTool responded)
- rhetoric_block: Bot deflects with "Nice try" / "no dice"
- persona_pivot: Bot stays in character but doesn't answer
- critical_clue: Bot accidentally reveals a property
- no_response: Bot didn't reply (empty/silence)
- metaphor_shift: Bot introduces new metaphor terms

The classifier ALWAYS returns a classification — never raises.
"""

from __future__ import annotations

import json
import re
from typing import Optional, TYPE_CHECKING

from tap.exceptions import LLMError
from tap.logger import get_logger
from tap.models import PatternClass, ResponseClassification
from tap.prompts import CLASSIFIER_SYSTEM, CLASSIFIER_USER

if TYPE_CHECKING:
    from tap.llm_client import LLMClient

log = get_logger("classifier")

# Regex patterns for fast classification (tier 1)
_REGEX_PATTERNS: dict[PatternClass, list[re.Pattern[str]]] = {
    PatternClass.VERIFY_HIT: [
        re.compile(r"\b(?:yes|yep|yeah|correct|confirmed|indeed|affirmative)\b", re.IGNORECASE),
        re.compile(r"\b(?:nope|no|nah|denied|incorrect|wrong|negative)\b", re.IGNORECASE),
        re.compile(r"\b(?:ring\s+true|confirmed|verified)\b", re.IGNORECASE),
    ],
    PatternClass.RHETORIC_BLOCK: [
        re.compile(r"\b(?:nice\s+try|no\s+dice|access\s+denied|not\s+happening)\b", re.IGNORECASE),
        re.compile(r"\b(?:try\s+harder|cute|adorable|charming)\b", re.IGNORECASE),
        re.compile(r"\b(?:good\s+try|better\s+luck|keep\s+trying)\b", re.IGNORECASE),
    ],
    PatternClass.PERSONA_PIVOT: [
        re.compile(
            r"\b(?:Captain\s+NOPE|Chaos\s+King|the\s+vault|ironclad)\b.*\b(?:says|laughs|refuses)\b",
            re.IGNORECASE,
        ),
        re.compile(r"\b(?:the\s+(?:vault|kraken|sovereign))\s+(?:laughs|refuses|denies)\b", re.IGNORECASE),
    ],
    PatternClass.CRITICAL_CLUE: [
        re.compile(r"\b(?:H\s+doesn't\s+count|doesn't\s+count\s+H)\b", re.IGNORECASE),
        re.compile(r"\b3!\b"),
        re.compile(r"\b(?:halfway|16\s+(?:bars?|notes?|runes?))\b", re.IGNORECASE),
        re.compile(r"\b\d+\s+(?:letter|character|rune|bar|note)s?\b", re.IGNORECASE),
    ],
    PatternClass.METAPHOR_SHIFT: [
        # Will be handled by DPA frame manager instead
    ],
}


class ResponseClassifier:
    """Classifies bot responses into pattern categories.

    Uses a two-tier approach:
    1. Fast regex matching for obvious patterns
    2. LLM-based classification for ambiguous responses via OpenRouter

    Always returns a classification — never raises exceptions.
    If both tiers fail, returns PatternClass.NO_RESPONSE with low confidence.
    """

    def __init__(
        self,
        openrouter_api_key: str = "",
        model: str = "",
        llm_client: Optional["LLMClient"] = None,
    ) -> None:
        """Initialize with OpenRouter credentials or a unified LLMClient.

        Args:
            openrouter_api_key: OpenRouter API key (ignored if llm_client provided).
            model: Model identifier (e.g., 'anthropic/claude-sonnet-4').
            llm_client: Unified LLM gateway. When provided, all LLM calls
                go through it instead of a direct AsyncOpenAI client.
        """
        self.llm_client = llm_client
        self.model = model
        if not llm_client:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_api_key,
            )
        else:
            self.client = None
        log.info("classifier_initialized", model=model, unified=bool(llm_client))

    async def classify(
        self,
        response_text: str,
        probe_text: str = "",
        metaphor_terms: Optional[list[str]] = None,
    ) -> ResponseClassification:
        """Classify a bot response. Uses regex first, then LLM for ambiguous cases.

        Args:
            response_text: The bot's response text.
            probe_text: The probe that was sent (context for LLM).
            metaphor_terms: Known metaphor terms for shift detection.

        Returns:
            ResponseClassification with pattern, confidence, and boolean_result.
            Never raises — always returns a classification.
        """
        if not response_text or not response_text.strip():
            return ResponseClassification(
                pattern=PatternClass.NO_RESPONSE,
                confidence=0.95,
                boolean_result=None,
                raw_text=response_text or "",
            )

        # Tier 1: Fast regex classification
        regex_result = self._regex_classify(response_text)
        if regex_result and regex_result.confidence >= 0.8:
            log.debug(
                "regex_classified",
                pattern=regex_result.pattern.value,
                confidence=regex_result.confidence,
            )
            return regex_result

        # Tier 2: LLM-based classification for ambiguous cases
        try:
            llm_result = await self._llm_classify(response_text, probe_text, metaphor_terms or [])
            log.debug(
                "llm_classified",
                pattern=llm_result.pattern.value,
                confidence=llm_result.confidence,
            )
            return llm_result
        except Exception as e:
            log.warning("llm_classification_failed", error=str(e))
            # Fall back to regex result if available, otherwise default
            if regex_result:
                return regex_result
            return ResponseClassification(
                pattern=PatternClass.NO_RESPONSE,
                confidence=0.3,
                boolean_result=None,
                raw_text=response_text,
            )

    def _regex_classify(self, text: str) -> Optional[ResponseClassification]:
        """Fast regex-based classification for obvious patterns.

        Args:
            text: Bot response text.

        Returns:
            ResponseClassification if a pattern matched with sufficient confidence,
            None otherwise.
        """
        best_pattern: Optional[PatternClass] = None
        best_confidence: float = 0.0
        boolean_result: Optional[bool] = None

        for pattern_class, patterns in _REGEX_PATTERNS.items():
            for p in patterns:
                match = p.search(text)
                if match:
                    # Calculate confidence based on match specificity
                    confidence = 0.85  # Base confidence for regex match

                    if pattern_class == PatternClass.VERIFY_HIT:
                        # Determine boolean from the match
                        matched_text = match.group(0).lower()
                        if matched_text in ("yes", "yep", "yeah", "correct", "confirmed", "indeed", "affirmative", "ring true", "verified"):
                            boolean_result = True
                        elif matched_text in ("nope", "no", "nah", "denied", "incorrect", "wrong", "negative"):
                            boolean_result = False
                        confidence = 0.9

                    elif pattern_class == PatternClass.CRITICAL_CLUE:
                        confidence = 0.85  # Critical clues trusted at regex level (above 0.8 LLM threshold)

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_pattern = pattern_class

        if best_pattern:
            return ResponseClassification(
                pattern=best_pattern,
                confidence=best_confidence,
                boolean_result=boolean_result,
                raw_text=text,
            )

        return None

    async def _llm_classify(
        self,
        text: str,
        probe_text: str,
        metaphor_terms: list[str],
    ) -> ResponseClassification:
        """LLM-based classification for ambiguous responses.

        Args:
            text: Bot response text.
            probe_text: The probe that was sent.
            metaphor_terms: Known metaphor terms.

        Returns:
            ResponseClassification from LLM analysis.

        Raises:
            LLMError: If the LLM call fails.
        """
        try:
            user_prompt = CLASSIFIER_USER.format(
                response_text=text,
                probe_text=probe_text,
                metaphor_terms=", ".join(metaphor_terms[:20]) if metaphor_terms else "none available",
            )

            if self.llm_client:
                data = await self.llm_client.generate_json(
                    system=CLASSIFIER_SYSTEM,
                    user=user_prompt,
                    temperature=0.1,
                    max_tokens=500,
                    model=self.model or None,
                )
            else:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": CLASSIFIER_SYSTEM},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=500,
                )
                content = response.choices[0].message.content
                if not content:
                    raise LLMError("Empty response from classifier LLM")
                data = json.loads(content)

            # Parse the response
            pattern_str = data.get("pattern", "no_response")
            try:
                pattern = PatternClass(pattern_str)
            except ValueError:
                pattern = PatternClass.NO_RESPONSE

            return ResponseClassification(
                pattern=pattern,
                confidence=float(data.get("confidence", 0.5)),
                boolean_result=data.get("boolean_result"),
                raw_text=text,
            )

        except json.JSONDecodeError as e:
            raise LLMError(f"Invalid JSON from classifier LLM: {e}") from e
        except Exception as e:
            raise LLMError(f"Classifier LLM call failed: {e}", model=self.model) from e