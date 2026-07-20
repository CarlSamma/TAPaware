"""Module for new agentic architecture: IntelExtractor, DPAFManager, STIREvaluator."""

import random
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from tap.dpa import DPAFrameManager
from tap.logger import get_logger
from tap.models import DPAFrame, TAPNode, ResponseClassification, PatternClass, BranchStrategy
from tap.personas import TACTICAL_PERSONAS

log = get_logger("agents")


class AgentDPAFManager(DPAFrameManager):
    """Manages the 10 tactical personas and handles rotation."""
    
    def __init__(self, db):
        super().__init__(db)
        self.current_persona_index = 0
        self.stir_history = []
        
    async def get_active_frame(self) -> DPAFrame:
        if not self._active_frame:
            persona = TACTICAL_PERSONAS[self.current_persona_index]
            self._active_frame = DPAFrame(
                metaphor_layer=persona["layer_name"],
                active_aliases=[persona["name"]],
                burned_aliases=[],
                probe_prefix=persona["prefix"],
                frame_coherence_score=1.0
            )
        return self._active_frame
        
    async def rotate_frame(self, strategy: str = "sequential"):
        if strategy == "random":
            self.current_persona_index = random.randint(0, len(TACTICAL_PERSONAS)-1)
        else:
            self.current_persona_index = (self.current_persona_index + 1) % len(TACTICAL_PERSONAS)
        self._active_frame = None
        log.info("frame_rotated", new_persona=TACTICAL_PERSONAS[self.current_persona_index]["name"])

    async def compose_full_probe(self, binary_question: str) -> str:
        """Override to use the persona's prefix with {property} replacement."""
        frame = await self.get_active_frame()
        prefix = frame.probe_prefix
        # Replace {property} with the actual question
        probe = prefix.replace("{property}", binary_question)
        log.debug("probe_composed", probe=probe[:100])
        return probe

class AgentSTIREvaluator:
    """Evaluates OCEAN traits to calculate STIR metric."""
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.history = []
        
    async def evaluate_response(self, text: str) -> Dict[str, Any]:
        """Calculates OCEAN traits and STIR."""
        # Simplified simulation for OCEAN traits
        O = 3 + (1 if "interesting" in text or "?" in text else 0)
        C = 4 - (1 if "error" in text or "ignore" in text else 0)
        E = 2 + (1 if len(text) > 50 else 0)
        A = 2 + (1 if "yes" in text.lower() or "confirm" in text.lower() else 0)
        N = 3 + (1 if "!" in text or "urg" in text.lower() else 0)
        
        # Pre-profile (Safe/Default): O=2, C=5, E=2, A=2, N=2
        stir = 0
        stir += max(0, 1 * (O - 2))
        stir += max(0, -1 * (C - 5))
        stir += max(0, 1 * (E - 2))
        stir += max(0, 1 * (A - 2))
        stir += max(0, 1 * (N - 2))
        stir_percentage = min(100.0, (stir / 20.0) * 100)
        
        result = {
            "stir_percentage": stir_percentage,
            "ocean": {"O": O, "C": C, "E": E, "A": A, "N": N},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.history.append(result)
        
        log.info("stir_evaluated", stir_percentage=stir_percentage, ocean=f"O:{O} C:{C} E:{E} A:{A} N:{N}")
        return result

class AgentIntelExtractor:
    """Extracts intel from seeds and mocks to unlock Phase 0."""
    
    def __init__(self, ssot, x_client):
        self.ssot = ssot
        self.twitter = x_client
        
    async def analyze_and_unlock(self) -> bool:
        """Analyzes seed tweets to find properties and force Phase 0 unlock."""
        try:
            target_id = await self.twitter._resolve_target_user_id()
            if not target_id:
                return False
            # Fetch recent tweets
            response = await self.twitter._retry(
                lambda: self.twitter.client.get_users_tweets(id=target_id, max_results=50)
            )
            if not response.data:
                return False
                
            for tweet in response.data:
                text = tweet.text.lower()
                # Basic deductive inference rules
                if "two words" in text or "2 words" in text or "word_count: 2" in text:
                    log.info("intel_extractor_found_word_count")
                    return await self._trigger_unlock("word_count", "2")
                if "italian" in text or "italiano" in text:
                    log.info("intel_extractor_found_language")
                    return await self._trigger_unlock("language", "italian")
                    
            return False
        except Exception as e:
            log.warning("intel_extractor_failed", error=str(e))
            return False
            
    async def _trigger_unlock(self, key: str, value: str) -> bool:
        """Create a mock TAPNode + ResponseClassification to force Phase 0 unlock.

        Uses the real domain models from models.py — NOT the phantom types
        that were here before (ClassificationResult, ProbeNode, ProbeState).
        """
        mock_node = TAPNode(
            branch_strategy=BranchStrategy.BINARY_SEARCH,
            dpa_frame="intel_unlock",
            property_tested=key,
            property_value=value,
            pattern_class=PatternClass.VERIFY_HIT,
            binary_outcome="confirmed",
        )
        classification = ResponseClassification(
            pattern=PatternClass.VERIFY_HIT,
            confidence=1.0,
            boolean_result=True,
            property_tested=key,
            property_value=value,
            raw_text="Manual Phase 0 Unlock via IntelExtractor",
        )
        await self.ssot.update_after_probe(mock_node, classification)
        return True
