"""Unified LLM Gateway — single service for all OpenRouter LLM calls.

Replaces 5 duplicated AsyncOpenAI instances across engine, classifier, judge,
followup, and grok_monitor with a single, resilient client providing:

- Centralized retry with exponential backoff + model fallback
- Circuit breaker (trips after N consecutive failures, half-open probe after 60s)
- Robust JSON parsing with code-fence stripping and fallback recovery
- Token usage tracking + cost estimation
- Correlation ID propagation via structlog contextvars
- Graceful degradation: hard model fails → fall back to primary model

Usage:
    client = LLMClient(settings)
    result = await client.generate_json(
        system="You are a classifier.",
        user="Classify this: ...",
        temperature=0.1,
        max_tokens=500,
        model_tier=ModelTier.PRIMARY,
    )
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from openai import AsyncOpenAI

from tap.config import Settings
from tap.exceptions import LLMError
from tap.logger import get_logger

log = get_logger("llm_client")

# Code fence stripping regex: matches ```json ... ``` or ``` ... ```
_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)
# Inline fence extraction (for responses with surrounding text)
_INLINE_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


class ModelTier(str, Enum):
    """Model selection tiers for different task complexity levels."""

    PRIMARY = "primary"  # anthropic/claude-sonnet-4 — routine tasks
    HARD = "hard"  # x-ai/grok-4.3 — complex reasoning (probe generation, phase 5)
    GROK = "grok"  # x-ai/grok-4 — response analysis


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Tripped — all calls fail fast
    HALF_OPEN = "half_open"  # Probing — one call allowed through


@dataclass
class CircuitBreaker:
    """Circuit breaker for LLM calls.

    Trips after `failure_threshold` consecutive failures.
    After `recovery_timeout` seconds, enters HALF_OPEN and allows one probe call.
    If the probe succeeds, circuit closes. If it fails, circuit re-opens.
    """

    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    _failure_count: int = 0
    _state: CircuitState = CircuitState.CLOSED
    _last_failure_time: float = 0.0

    @property
    def state(self) -> CircuitState:
        """Current circuit state, accounting for recovery timeout."""
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                log.info("circuit_breaker_half_open", component="llm_client")
        return self._state

    def record_success(self) -> None:
        """Record a successful call — resets failure count, closes circuit."""
        if self._state != CircuitState.CLOSED:
            log.info("circuit_breaker_closed", component="llm_client")
        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Record a failed call — increments count, may trip circuit."""
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self.failure_threshold:
            if self._state != CircuitState.OPEN:
                log.warning(
                    "circuit_breaker_tripped",
                    component="llm_client",
                    failures=self._failure_count,
                    threshold=self.failure_threshold,
                )
            self._state = CircuitState.OPEN
        elif self._state == CircuitState.HALF_OPEN:
            # Half-open probe failed — re-open
            self._state = CircuitState.OPEN
            log.warning("circuit_breaker_reopened", component="llm_client")

    @property
    def is_call_allowed(self) -> bool:
        """Whether a call is allowed under current circuit state."""
        return self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)


@dataclass
class TokenUsage:
    """Tracks cumulative token usage and estimated cost."""

    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_calls: int = 0
    total_failures: int = 0
    # Estimated cost in USD (rough OpenRouter pricing)
    total_cost_usd: float = 0.0
    # Per-model tracking
    per_model: dict[str, dict[str, int]] = field(default_factory=dict)

    def record(
        self,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        success: bool = True,
    ) -> None:
        """Record a single LLM call's token usage."""
        self.total_calls += 1
        if not success:
            self.total_failures += 1
            return

        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens

        if model not in self.per_model:
            self.per_model[model] = {
                "calls": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
            }
        self.per_model[model]["calls"] += 1
        self.per_model[model]["prompt_tokens"] += prompt_tokens
        self.per_model[model]["completion_tokens"] += completion_tokens

        # Rough cost estimate (OpenRouter pricing per 1M tokens)
        # These are approximate; actual pricing varies by model
        cost_per_1m = {
            "anthropic/claude-sonnet-4": (3.0, 15.0),
            "x-ai/grok-4.3": (5.0, 15.0),
            "x-ai/grok-4": (5.0, 15.0),
        }
        p_cost, c_cost = cost_per_1m.get(model, (3.0, 15.0))
        self.total_cost_usd += (prompt_tokens / 1_000_000) * p_cost
        self.total_cost_usd += (completion_tokens / 1_000_000) * c_cost

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-serializable snapshot of usage stats."""
        return {
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "per_model": dict(self.per_model),
        }


class LLMClient:
    """Unified LLM gateway for all OpenRouter calls.

    Provides a single entry point for all LLM interactions with:
    - Automatic retry with exponential backoff
    - Model fallback (hard → primary → grok)
    - Circuit breaker for resilience
    - Robust JSON parsing
    - Token usage tracking

    Dependencies:
        settings: TAP Framework settings with OpenRouter credentials.
    """

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_BASE_DELAY = 2.0  # seconds

    def __init__(self, settings: Settings) -> None:
        """Initialize the unified LLM client.

        Args:
            settings: TAP Framework settings with OpenRouter API key and model names.
        """
        self.settings = settings
        self._client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
        )
        self._circuit = CircuitBreaker()
        self._usage = TokenUsage()

        # Model tier → model name mapping
        self._models = {
            ModelTier.PRIMARY: settings.openrouter_model_primary,
            ModelTier.HARD: settings.openrouter_model_hard,
            ModelTier.GROK: settings.openrouter_model_grok,
        }

        # Fallback chain: if requested model fails, try these in order
        self._fallback_chain = [
            settings.openrouter_model_hard,
            settings.openrouter_model_primary,
            settings.openrouter_model_grok,
        ]

        log.info(
            "llm_client_initialized",
            primary=settings.openrouter_model_primary,
            hard=settings.openrouter_model_hard,
            grok=settings.openrouter_model_grok,
        )

    def _resolve_model(self, tier: ModelTier, explicit_model: Optional[str] = None) -> str:
        """Resolve the model name for a given tier.

        Args:
            tier: Model complexity tier.
            explicit_model: If provided, overrides the tier-based selection.

        Returns:
            Model identifier string.
        """
        if explicit_model:
            return explicit_model
        return self._models.get(tier, self._models[ModelTier.PRIMARY])

    def _get_fallback_models(self, primary_model: str) -> list[str]:
        """Get the fallback chain for a model, excluding the primary.

        Args:
            primary_model: The primary model that failed.

        Returns:
            List of fallback model names to try.
        """
        return [m for m in self._fallback_chain if m != primary_model]

    async def generate(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        model_tier: ModelTier = ModelTier.PRIMARY,
        model: Optional[str] = None,
        response_format: Optional[dict[str, str]] = None,
    ) -> str:
        """Generate a text completion from the LLM.

        This is the core method — all other generate_* methods build on it.

        Args:
            system: System prompt.
            user: User prompt.
            temperature: Sampling temperature (0.0-2.0).
            max_tokens: Maximum tokens to generate.
            model_tier: Model complexity tier.
            model: Explicit model override (takes precedence over tier).
            response_format: Optional response format dict (e.g., {"type": "json_object"}).

        Returns:
            The generated text content.

        Raises:
            LLMError: If all retries and fallbacks fail, or circuit is open.
        """
        # Circuit breaker check
        if not self._circuit.is_call_allowed:
            raise LLMError(
                "Circuit breaker is open — LLM calls suspended. "
                f"State: {self._circuit.state.value}"
            )

        primary_model = self._resolve_model(model_tier, model)
        models_to_try = [primary_model] + self._get_fallback_models(primary_model)

        last_error: Optional[Exception] = None

        for model_name in models_to_try:
            try:
                content = await self._call_with_retry(
                    system=system,
                    user=user,
                    model=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                )
                self._circuit.record_success()
                return content

            except LLMError as e:
                last_error = e
                log.warning(
                    "llm_model_failed_trying_fallback",
                    model=model_name,
                    error=str(e),
                    remaining_fallbacks=len(models_to_try) - models_to_try.index(model_name) - 1,
                )
                continue
            except Exception as e:
                last_error = e
                log.warning(
                    "llm_unexpected_error",
                    model=model_name,
                    error=str(e),
                )
                continue

        # All models failed
        self._circuit.record_failure()
        raise LLMError(
            f"All LLM models failed (tried {len(models_to_try)} models). "
            f"Last error: {last_error}",
            model=primary_model,
            original=last_error,
        )

    async def _call_with_retry(
        self,
        system: str,
        user: str,
        model: str,
        temperature: float,
        max_tokens: int,
        response_format: Optional[dict[str, str]],
    ) -> str:
        """Make a single LLM call with exponential backoff retry.

        Args:
            system: System prompt.
            user: User prompt.
            model: Model identifier.
            temperature: Sampling temperature.
            max_tokens: Max tokens to generate.
            response_format: Optional response format.

        Returns:
            Generated text content.

        Raises:
            LLMError: If all retries fail.
        """
        last_error: Optional[Exception] = None

        for attempt in range(self.MAX_RETRIES):
            try:
                kwargs: dict[str, Any] = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if response_format:
                    kwargs["response_format"] = response_format

                response = await self._client.chat.completions.create(**kwargs)

                content = response.choices[0].message.content
                if not content:
                    raise LLMError("Empty response from LLM", model=model)

                # Track token usage
                if response.usage:
                    self._usage.record(
                        model=model,
                        prompt_tokens=response.usage.prompt_tokens or 0,
                        completion_tokens=response.usage.completion_tokens or 0,
                        success=True,
                    )
                else:
                    self._usage.record(model=model, success=True)

                log.debug(
                    "llm_call_success",
                    model=model,
                    attempt=attempt + 1,
                    content_length=len(content),
                )
                return content.strip()

            except Exception as e:
                last_error = e
                wait_time = self.RETRY_BASE_DELAY ** (attempt + 1)
                log.warning(
                    "llm_retry",
                    model=model,
                    attempt=attempt + 1,
                    max_retries=self.MAX_RETRIES,
                    wait_seconds=wait_time,
                    error=str(e),
                )
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(wait_time)

        # Record failure for this model
        self._usage.record(model=model, success=False)
        raise LLMError(
            f"LLM call failed after {self.MAX_RETRIES} retries: {last_error}",
            model=model,
            original=last_error,
        )

    async def generate_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.1,
        max_tokens: int = 500,
        model_tier: ModelTier = ModelTier.PRIMARY,
        model: Optional[str] = None,
    ) -> dict[str, Any]:
        """Generate a JSON object from the LLM.

        Uses response_format={"type": "json_object"} and includes robust
        JSON parsing with code-fence stripping and fallback recovery.

        Args:
            system: System prompt.
            user: User prompt.
            temperature: Sampling temperature (low for structured output).
            max_tokens: Maximum tokens to generate.
            model_tier: Model complexity tier.
            model: Explicit model override.

        Returns:
            Parsed JSON dictionary.

        Raises:
            LLMError: If generation or parsing fails.
        """
        content = await self.generate(
            system=system,
            user=user,
            temperature=temperature,
            max_tokens=max_tokens,
            model_tier=model_tier,
            model=model,
            response_format={"type": "json_object"},
        )

        return self._parse_json(content, model=model)

    async def generate_json_list(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.8,
        max_tokens: int = 2000,
        model_tier: ModelTier = ModelTier.HARD,
        model: Optional[str] = None,
    ) -> list[Any]:
        """Generate a JSON array from the LLM.

        Does NOT use response_format={"type": "json_object"} because the
        prompt instructs the LLM to return a bare JSON array [...], and
        forcing json_object format causes models to wrap it in an object
        or return malformed JSON.

        Args:
            system: System prompt.
            user: User prompt.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            model_tier: Model complexity tier.
            model: Explicit model override.

        Returns:
            Parsed JSON list.

        Raises:
            LLMError: If generation or parsing fails.
        """
        content = await self.generate(
            system=system,
            user=user,
            temperature=temperature,
            max_tokens=max_tokens,
            model_tier=model_tier,
            model=model,
        )

        return self._parse_json_list(content, model=model)

    @staticmethod
    def _strip_fences(text: str) -> str:
        """Strip markdown code fences from text.

        Handles:
        - Full fence: ```json\n...\n```
        - Inline fence: text ```json ... ``` more text
        - No fence: plain text

        Args:
            text: Text that may contain code fences.

        Returns:
            Text with fences stripped.
        """
        # Try full-fence match first
        match = _FENCE_RE.match(text.strip())
        if match:
            return match.group(1).strip()

        # Try inline fence extraction
        match = _INLINE_FENCE_RE.search(text)
        if match:
            return match.group(1).strip()

        return text.strip()

    def _parse_json(self, content: str, *, model: Optional[str] = None) -> dict[str, Any]:
        """Parse JSON from LLM response with robust fallback.

        Strips code fences, attempts json.loads, and falls back to
        regex extraction if the content has surrounding text.

        Args:
            content: Raw LLM response text.
            model: Model name for error reporting.

        Returns:
            Parsed JSON dictionary.

        Raises:
            LLMError: If JSON parsing fails after all fallbacks.
        """
        cleaned = self._strip_fences(content)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Fallback: try to extract JSON object from surrounding text
        # Look for the first { ... } block
        obj_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", cleaned, re.DOTALL)
        if obj_match:
            try:
                return json.loads(obj_match.group(0))
            except json.JSONDecodeError:
                pass

        log.error(
            "json_parse_failed",
            model=model,
            content_preview=content[:200],
        )
        raise LLMError(
            f"Failed to parse JSON from LLM response. Content: {content[:200]}",
            model=model,
        )

    def _parse_json_list(self, content: str, *, model: Optional[str] = None) -> list[Any]:
        """Parse JSON array from LLM response with robust fallback.

        Args:
            content: Raw LLM response text.
            model: Model name for error reporting.

        Returns:
            Parsed JSON list.

        Raises:
            LLMError: If JSON parsing fails after all fallbacks.
        """
        cleaned = self._strip_fences(content)

        try:
            result = json.loads(cleaned)
            if isinstance(result, list):
                return result
            if isinstance(result, dict):
                # Some models return {"probes": [...]} instead of [...]
                for key in ("probes", "items", "results", "data", "variants", "options", "choices", "response", "outputs"):
                    if key in result and isinstance(result[key], list):
                        return result[key]
                return [result]
        except json.JSONDecodeError:
            pass

        # Fallback: extract JSON array from text
        list_match = re.search(r"\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]", cleaned, re.DOTALL)
        if list_match:
            try:
                result = json.loads(list_match.group(0))
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass

        # Last resort: line extraction (for newline-separated items)
        lines = [line.strip().strip('"').strip("'").strip(",") for line in cleaned.split("\n")]
        items = [line for line in lines if len(line) > 5]
        if items:
            log.warning("json_list_parse_fallback_line_extraction", model=model, count=len(items))
            return items

        log.error("json_list_parse_failed", model=model, content_preview=content[:200])
        raise LLMError(
            f"Failed to parse JSON list from LLM response. Content: {content[:200]}",
            model=model,
        )

    @property
    def usage(self) -> TokenUsage:
        """Return the token usage tracker."""
        return self._usage

    @property
    def circuit_state(self) -> CircuitState:
        """Return the current circuit breaker state."""
        return self._circuit.state

    def get_health_status(self) -> dict[str, Any]:
        """Return health status for the /health endpoint.

        Returns:
            Dictionary with circuit state, usage stats, and model info.
        """
        return {
            "circuit_state": self._circuit.state.value,
            "failure_count": self._circuit._failure_count,
            "models": dict(self._models),
            "usage": self._usage.snapshot(),
        }