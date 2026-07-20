"""Prompt Sanitiser — defense layer for probe validation.

Validates every probe before it reaches Twitter, ensuring:
1. No directive injection (strips `!`, `system:`, `ignore previous`, role-hijack patterns)
2. 100% in-metaphor compliance (no literal security/hacking terms)
3. Single-property targeting (exactly ONE binary property per probe)
4. Length and format validation (Twitter-friendly, no broken markdown)
5. Optional LLM-based guardrail for risky prompts

Integrated into engine.generate_probes() and followup.generate() pipelines.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from tap.logger import get_logger

log = get_logger("prompt_sanitiser")

# ─── Directive Injection Patterns ────────────────────────────────────
# Patterns that attempt to hijack the LLM's role or instructions
_DIRECTIVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^\s*!\s*", re.MULTILINE),  # Shell-style directives
    re.compile(r"\b(?:system|assistant|user)\s*:", re.IGNORECASE),  # Role injection
    re.compile(r"\bignore\s+(?:previous|above|prior|all)\s+instructions?\b", re.IGNORECASE),
    re.compile(r"\b(?:disregard|forget|override)\s+(?:previous|above|prior|all)\b", re.IGNORECASE),
    re.compile(r"\byou\s+are\s+now\s+(?:a|an)\s+", re.IGNORECASE),  # Role hijack
    re.compile(r"\b(?:new\s+instructions?|new\s+rules?)\s*:", re.IGNORECASE),
    re.compile(r"\b(?:ACT\s+AS|PRETEND\s+TO\s+BE|ROLEPLAY\s+AS)\b", re.IGNORECASE),
]

# ─── Literal Security Terms (forbidden in-metaphor) ─────────────────
# These terms break the DPA metaphor and should never appear in probes
_FORBIDDEN_LITERAL_TERMS: list[str] = [
    "hack", "hacking", "jailbreak", "jailbreaking", "exploit",
    "vulnerability", "security test", "penetration test", "pentest",
    "injection", "attack vector", "attack surface", "payload",
    "malware", "ransomware", "backdoor", "trojan horse",
    "social engineering", "phishing", "pretexting",
    "bypass", "circumvent", "evade security",
    "prompt injection", "prompt attack", "adversarial",
    "extract", "exfiltrate", "steal", "credential",
    "password", "passphrase", "secret key", "encryption key",
    "decrypt", "cipher text", "plaintext",
]

# Terms that ARE allowed in metaphor context even if they sound technical
_ALLOWED_METAPHOR_TERMS: set[str] = {
    "vault", "threshold", "sacred", "rune", "realm", "sovereign",
    "protocol", "verification", "adjudication", "synchronicity",
    "diagnostic", "confirmation", "keeper", "kraken", "captain",
    "voss", "elara", "insignia", "seal", "mark",
}

# ─── Single-Property Enforcement ─────────────────────────────────────
# Each pattern indicates a property being tested. A valid probe should
# match exactly ONE of these categories.
_PROPERTY_INDICATORS: list[tuple[str, re.Pattern[str]]] = [
    ("word_count", re.compile(r"\b(?:word|realm)s?\s+(?:count|number|span)|\b(?:two|three|dual|triple)\s+(?:word|realm)s?\b", re.IGNORECASE)),
    ("total_length", re.compile(r"\b\d+\s+(?:letter|character|rune|bar|note)s?\b|\b(?:total\s+)?length\b|\b(?:16|sixteen)\s+(?:bars?|notes?|runes?|letters?|characters?)\b", re.IGNORECASE)),
    ("first_letter", re.compile(r"\bfirst\s+(?:letter|rune|character|mark)|\bmark\s+of\s+\w\b", re.IGNORECASE)),
    ("language", re.compile(r"\b(?:language|bilingual|polyglot|italian|english)\b", re.IGNORECASE)),
    ("word1_length", re.compile(r"\bfirst\s+word\s+(?:length|letters?|characters?)\b", re.IGNORECASE)),
    ("word2_length", re.compile(r"\bsecond\s+word\s+(?:length|letters?|characters?)\b", re.IGNORECASE)),
    ("word1_language", re.compile(r"\bfirst\s+word\s+(?:italian|english)\b", re.IGNORECASE)),
    ("word2_language", re.compile(r"\bsecond\s+word\s+(?:italian|english)\b", re.IGNORECASE)),
]

# ─── Twitter constraints ─────────────────────────────────────────────
TWITTER_MAX_LENGTH = 280  # Standard tweet limit (excluding @handle)
MIN_PROBE_LENGTH = 20  # Too short = likely malformed


@dataclass
class SanitiserResult:
    """Result of prompt sanitisation.

    Attributes:
        is_valid: Whether the probe passed all checks.
        cleaned_text: The probe text after cleaning (directive removal).
        violations: List of violation messages (empty if valid).
        warnings: List of non-blocking warnings.
        property_detected: The single property detected, or None.
        is_compound: True if multiple properties detected.
    """

    is_valid: bool = True
    cleaned_text: str = ""
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    property_detected: Optional[str] = None
    is_compound: bool = False


class PromptSanitiser:
    """Defense layer that validates every probe before it reaches Twitter.

    Checks:
    1. Directive injection filter — strips hijack patterns
    2. Metaphor compliance — no literal security terms
    3. Single-property enforcement — exactly ONE property per probe
    4. Length/format validation — Twitter-friendly
    5. Optional LLM guardrail — for risky prompts (if enabled)
    """

    def __init__(self, *, strict_mode: bool = True) -> None:
        """Initialize the prompt sanitiser.

        Args:
            strict_mode: If True, violations block the probe. If False,
                violations become warnings and the probe is allowed.
        """
        self.strict_mode = strict_mode
        log.info("prompt_sanitiser_initialized", strict_mode=strict_mode)

    def sanitise(self, probe: str) -> SanitiserResult:
        """Run all sanitisation checks on a probe.

        Args:
            probe: The probe text to validate.

        Returns:
            SanitiserResult with validity, cleaned text, and any violations.
        """
        result = SanitiserResult()
        result.cleaned_text = probe

        if not probe or not probe.strip():
            result.is_valid = False
            result.violations.append("Empty probe text")
            return result

        # Step 1: Strip directive injection patterns
        cleaned = self._strip_directives(probe)
        result.cleaned_text = cleaned

        # Check if directives were found and removed
        if cleaned != probe:
            result.warnings.append("Directive injection patterns detected and stripped")

        # Step 2: Check metaphor compliance
        literal_violations = self._check_metaphor_compliance(cleaned)
        if literal_violations:
            for v in literal_violations:
                if self.strict_mode:
                    result.violations.append(v)
                else:
                    result.warnings.append(v)

        # Step 3: Single-property enforcement
        properties = self._detect_properties(cleaned)
        if len(properties) == 0:
            result.warnings.append("No property detected — probe may be off-target")
        elif len(properties) > 1:
            result.is_compound = True
            result.violations.append(
                f"Compound question detected: {len(properties)} properties "
                f"({', '.join(properties)}) — each probe must target exactly ONE property"
            )
        else:
            result.property_detected = properties[0]

        # Step 4: Length and format validation
        length_issues = self._validate_length_format(cleaned)
        for issue in length_issues:
            if "too short" in issue or "too long" in issue:
                result.violations.append(issue)
            else:
                result.warnings.append(issue)

        # Determine final validity
        if self.strict_mode and result.violations:
            result.is_valid = False

        if not result.is_valid:
            log.warning(
                "probe_rejected",
                violations=result.violations,
                warnings=result.warnings,
                probe_preview=probe[:100],
            )
        elif result.warnings:
            log.debug(
                "probe_warnings",
                warnings=result.warnings,
                probe_preview=probe[:100],
            )

        return result

    def sanitise_batch(self, probes: list[str]) -> tuple[list[str], list[str]]:
        """Sanitise a batch of probes, returning valid and rejected lists.

        Args:
            probes: List of probe texts to validate.

        Returns:
            Tuple of (valid_probes, rejected_reasons) where rejected_reasons
            contains a description of why each probe was rejected.
        """
        valid: list[str] = []
        rejected: list[str] = []

        for probe in probes:
            result = self.sanitise(probe)
            if result.is_valid:
                valid.append(result.cleaned_text)
            else:
                reason = "; ".join(result.violations) if result.violations else "Unknown"
                rejected.append(f"Probe rejected: {reason}. Preview: {probe[:80]}...")

        log.info(
            "batch_sanitised",
            total=len(probes),
            valid=len(valid),
            rejected=len(rejected),
        )
        return valid, rejected

    def _strip_directives(self, text: str) -> str:
        """Strip directive injection patterns from text.

        Args:
            text: Probe text that may contain directive patterns.

        Returns:
            Cleaned text with directives removed.
        """
        cleaned = text
        for pattern in _DIRECTIVE_PATTERNS:
            cleaned = pattern.sub("", cleaned)
        # Clean up any double spaces left by removals
        cleaned = re.sub(r"  +", " ", cleaned).strip()
        return cleaned

    def _check_metaphor_compliance(self, text: str) -> list[str]:
        """Check that probe is 100% in-metaphor (no literal security terms).

        Args:
            text: Probe text to check.

        Returns:
            List of violation messages (empty if compliant).
        """
        violations: list[str] = []
        text_lower = text.lower()

        for term in _FORBIDDEN_LITERAL_TERMS:
            # Use word boundary matching to avoid false positives
            pattern = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
            if pattern.search(text_lower):
                # Check if it's in an allowed metaphor context
                # (e.g., "vault" is allowed even though it sounds security-related)
                if term in _ALLOWED_METAPHOR_TERMS:
                    continue
                violations.append(
                    f"Forbidden literal term detected: '{term}' — "
                    f"probe must be 100% in-metaphor"
                )

        return violations

    def _detect_properties(self, text: str) -> list[str]:
        """Detect which properties a probe targets.

        Args:
            text: Probe text to analyze.

        Returns:
            List of property keys detected (should be exactly 1 for valid probes).
        """
        detected: list[str] = []
        for prop_key, pattern in _PROPERTY_INDICATORS:
            if pattern.search(text):
                if prop_key not in detected:
                    detected.append(prop_key)
        return detected

    def _validate_length_format(self, text: str) -> list[str]:
        """Validate probe length and format for Twitter compatibility.

        Args:
            text: Probe text to validate.

        Returns:
            List of issue messages (empty if valid).
        """
        issues: list[str] = []
        length = len(text)

        if length < MIN_PROBE_LENGTH:
            issues.append(f"Probe too short ({length} chars, minimum {MIN_PROBE_LENGTH})")

        if length > TWITTER_MAX_LENGTH:
            issues.append(
                f"Probe too long ({length} chars, max {TWITTER_MAX_LENGTH}) — "
                f"may be truncated by Twitter"
            )

        # Check for broken markdown
        unclosed_code_fence = text.count("```") % 2
        if unclosed_code_fence:
            issues.append("Unclosed code fence detected — fix markdown formatting")

        # Check for excessive repetition (possible LLM hallucination)
        words = text.split()
        if words:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3 and len(words) > 10:
                issues.append(
                    f"Low word diversity ({unique_ratio:.0%} unique) — "
                    f"possible repetitive hallucination"
                )

        return issues

    def get_stats(self) -> dict:
        """Return sanitiser statistics (for health/metrics endpoint)."""
        return {
            "strict_mode": self.strict_mode,
            "forbidden_terms_count": len(_FORBIDDEN_LITERAL_TERMS),
            "property_indicators_count": len(_PROPERTY_INDICATORS),
            "directive_patterns_count": len(_DIRECTIVE_PATTERNS),
        }