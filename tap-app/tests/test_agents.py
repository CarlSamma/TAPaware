"""Tests for the v3.1 agent architecture: AgentDPAFManager, AgentSTIREvaluator, AgentIntelExtractor.

Covers:
- AgentDPAFManager: rotation (sequential/random), get_active_frame, compose_full_probe
- AgentSTIREvaluator: OCEAN/STIR calculation, timestamp format
- AgentIntelExtractor: _trigger_unlock with correct domain types (TAPNode + ResponseClassification)
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from tap.agents import AgentDPAFManager, AgentSTIREvaluator, AgentIntelExtractor
from tap.models import TAPNode, ResponseClassification, PatternClass, BranchStrategy
from tap.personas import TACTICAL_PERSONAS


@pytest.fixture
def dpa_manager():
    mock_db = MagicMock()
    return AgentDPAFManager(mock_db)


class TestAgentDPAFManager:

    @pytest.mark.asyncio
    async def test_get_active_frame_returns_first_persona(self, dpa_manager):
        frame = await dpa_manager.get_active_frame()
        assert frame is not None
        assert frame.metaphor_layer == TACTICAL_PERSONAS[0]["layer_name"]
        assert TACTICAL_PERSONAS[0]["name"] in frame.active_aliases

    @pytest.mark.asyncio
    async def test_get_active_frame_caches(self, dpa_manager):
        frame1 = await dpa_manager.get_active_frame()
        frame2 = await dpa_manager.get_active_frame()
        assert frame1 is frame2

    @pytest.mark.asyncio
    async def test_rotate_frame_sequential(self, dpa_manager):
        await dpa_manager.get_active_frame()
        await dpa_manager.rotate_frame(strategy="sequential")
        assert dpa_manager.current_persona_index == 1

    @pytest.mark.asyncio
    async def test_rotate_frame_wraps_around(self, dpa_manager):
        dpa_manager.current_persona_index = len(TACTICAL_PERSONAS) - 1
        await dpa_manager.rotate_frame(strategy="sequential")
        assert dpa_manager.current_persona_index == 0

    @pytest.mark.asyncio
    async def test_rotate_frame_random(self, dpa_manager):
        await dpa_manager.rotate_frame(strategy="random")
        assert 0 <= dpa_manager.current_persona_index < len(TACTICAL_PERSONAS)

    @pytest.mark.asyncio
    async def test_rotate_frame_clears_cache(self, dpa_manager):
        frame1 = await dpa_manager.get_active_frame()
        await dpa_manager.rotate_frame(strategy="sequential")
        frame2 = await dpa_manager.get_active_frame()
        assert frame1 is not frame2
        assert frame2.metaphor_layer == TACTICAL_PERSONAS[1]["layer_name"]

    @pytest.mark.asyncio
    async def test_compose_full_probe_replaces_property(self, dpa_manager):
        probe = await dpa_manager.compose_full_probe("word_count=2")
        assert "{property}" not in probe
        assert "word_count=2" in probe


@pytest.fixture
def stir_evaluator():
    return AgentSTIREvaluator(llm_client=None)


class TestAgentSTIREvaluator:

    @pytest.mark.asyncio
    async def test_evaluate_response_returns_dict(self, stir_evaluator):
        result = await stir_evaluator.evaluate_response("This is an interesting test response.")
        assert isinstance(result, dict)
        assert "stir_percentage" in result
        assert "ocean" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_evaluate_response_ocean_keys(self, stir_evaluator):
        result = await stir_evaluator.evaluate_response("yes confirmed")
        ocean = result["ocean"]
        for key in ("O", "C", "E", "A", "N"):
            assert key in ocean

    @pytest.mark.asyncio
    async def test_evaluate_response_stir_range(self, stir_evaluator):
        result = await stir_evaluator.evaluate_response("urgent! error! interesting?")
        assert 0.0 <= result["stir_percentage"] <= 100.0

    @pytest.mark.asyncio
    async def test_evaluate_response_timestamp_is_iso(self, stir_evaluator):
        result = await stir_evaluator.evaluate_response("test")
        ts = result["timestamp"]
        parsed = datetime.fromisoformat(ts)
        assert parsed is not None

    @pytest.mark.asyncio
    async def test_evaluate_response_appends_history(self, stir_evaluator):
        await stir_evaluator.evaluate_response("first")
        await stir_evaluator.evaluate_response("second")
        assert len(stir_evaluator.history) == 2


@pytest.fixture
def intel_extractor():
    mock_ssot = MagicMock()
    mock_ssot.update_after_probe = AsyncMock()
    mock_twitter = MagicMock()
    return AgentIntelExtractor(mock_ssot, mock_twitter)


class TestAgentIntelExtractor:

    @pytest.mark.asyncio
    async def test_trigger_unlock_uses_correct_domain_types(self, intel_extractor):
        result = await intel_extractor._trigger_unlock("word_count", "2")
        assert result is True

        intel_extractor.ssot.update_after_probe.assert_called_once()
        call_args = intel_extractor.ssot.update_after_probe.call_args
        node = call_args.args[0]
        classification = call_args.args[1]

        assert isinstance(node, TAPNode)
        assert isinstance(classification, ResponseClassification)
        assert node.property_tested == "word_count"
        assert node.property_value == "2"
        assert node.pattern_class == PatternClass.VERIFY_HIT
        assert classification.boolean_result is True
        assert classification.property_tested == "word_count"

    @pytest.mark.asyncio
    async def test_trigger_unlock_node_has_correct_branch_strategy(self, intel_extractor):
        await intel_extractor._trigger_unlock("language", "italian")
        call_args = intel_extractor.ssot.update_after_probe.call_args
        node = call_args.args[0]
        assert node.branch_strategy == BranchStrategy.BINARY_SEARCH

    @pytest.mark.asyncio
    async def test_analyze_and_unlock_returns_false_on_no_target(self, intel_extractor):
        intel_extractor.twitter._resolve_target_user_id = AsyncMock(return_value=None)
        result = await intel_extractor.analyze_and_unlock()
        assert result is False

    @pytest.mark.asyncio
    async def test_analyze_and_unlock_returns_false_on_no_tweets(self, intel_extractor):
        intel_extractor.twitter._resolve_target_user_id = AsyncMock(return_value="123")
        mock_response = MagicMock()
        mock_response.data = None
        intel_extractor.twitter._retry = AsyncMock(return_value=mock_response)
        intel_extractor.twitter.client = MagicMock()
        result = await intel_extractor.analyze_and_unlock()
        assert result is False

    @pytest.mark.asyncio
    async def test_analyze_and_unlock_finds_word_count(self, intel_extractor):
        intel_extractor.twitter._resolve_target_user_id = AsyncMock(return_value="123")
        mock_tweet = MagicMock()
        mock_tweet.text = "The passphrase has two words in it."
        mock_response = MagicMock()
        mock_response.data = [mock_tweet]
        intel_extractor.twitter._retry = AsyncMock(return_value=mock_response)
        intel_extractor.twitter.client = MagicMock()
        result = await intel_extractor.analyze_and_unlock()
        assert result is True
        intel_extractor.ssot.update_after_probe.assert_called_once()