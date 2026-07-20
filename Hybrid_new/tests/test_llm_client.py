"""Tests for LLMClient (v3.0)."""

from __future__ import annotations

import pytest

from tap.config import Settings
from tap.llm_client import CircuitBreaker, CircuitState, LLMClient, ModelTier, TokenUsage


class TestCircuitBreaker:
    def test_initial_state_is_closed(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.is_call_allowed is True

    def test_trips_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_success_resets(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert cb._failure_count == 0

    def test_half_open_after_timeout(self):
        import time
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        cb.record_failure()
        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN


class TestTokenUsage:
    def test_record_success(self):
        usage = TokenUsage()
        usage.record("test-model", prompt_tokens=100, completion_tokens=50)
        assert usage.total_calls == 1
        assert usage.total_prompt_tokens == 100
        assert usage.total_cost_usd > 0

    def test_record_failure(self):
        usage = TokenUsage()
        usage.record("test-model", success=False)
        assert usage.total_failures == 1
        assert usage.total_prompt_tokens == 0

    def test_snapshot(self):
        usage = TokenUsage()
        usage.record("test-model", prompt_tokens=100)
        snap = usage.snapshot()
        assert snap["total_calls"] == 1


class TestLLMClient:
    @pytest.fixture
    def settings(self):
        return Settings(
            openrouter_api_key="test-key",
            openrouter_model_primary="anthropic/claude-sonnet-4",
            openrouter_model_hard="x-ai/grok-4.3",
            openrouter_model_grok="x-ai/grok-4",
        )

    @pytest.fixture
    def client(self, settings):
        return LLMClient(settings)

    def test_model_resolution(self, client):
        assert client._resolve_model(ModelTier.PRIMARY) == "anthropic/claude-sonnet-4"
        assert client._resolve_model(ModelTier.HARD) == "x-ai/grok-4.3"

    def test_explicit_model_override(self, client):
        assert client._resolve_model(ModelTier.PRIMARY, "custom/model") == "custom/model"

    def test_fence_stripping(self, client):
        assert LLMClient._strip_fences("no fences") == "no fences"
        bt = chr(96) * 3
        assert LLMClient._strip_fences(bt + "json" + chr(10) + "{x: 1}" + chr(10) + bt) == "{x: 1}"

    def test_parse_json(self, client):
        result = client._parse_json(chr(123) + chr(34) + "key" + chr(34) + ": " + chr(34) + "value" + chr(34) + chr(125))
        assert result["key"] == "value"

    def test_parse_json_list(self, client):
        result = client._parse_json_list(chr(91) + chr(34) + "a" + chr(34) + ", " + chr(34) + "b" + chr(34) + chr(93))
        assert result == ["a", "b"]

    def test_health_status(self, client):
        status = client.get_health_status()
        assert "circuit_state" in status
        assert "models" in status

    @pytest.mark.asyncio
    async def test_circuit_open_raises(self, client):
        import time; client._circuit._state = CircuitState.OPEN; client._circuit._last_failure_time = time.monotonic() + 999
        client._circuit._failure_count = 10
        from tap.exceptions import LLMError
        with pytest.raises(LLMError):
            await client.generate("sys", "user")
