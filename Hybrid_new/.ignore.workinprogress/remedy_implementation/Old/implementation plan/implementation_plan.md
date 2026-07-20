# TAP Framework v3.1 Implementation Plan

This plan details the steps to upgrade the TAP Framework to v3.1 (GLM-REMEDIATION), solving the 5 identified failure layers and integrating the new Agentic Architecture (Agent_DPAF_manager, Agent_STIR_Evaluator, Agent_Intel_Extractor) alongside the 10 new tactical personas.

## User Review Required
> [!IMPORTANT]
> This upgrade represents a major architectural shift. The framework will transition from a linear procedural loop to a multi-agent orchestrated approach. Please review the proposed changes carefully before approval.

## Proposed Changes

### 1. Infrastructure Layer (Twitter API)
**Problem:** Activity Stream is silent, and mock reply injection queue keys are mismatched.
**Solution:**
- Replace `wait_for_reply` in `grok_monitor.py` to use `conversation_id` polling via `search_recent`.
- Remove reliance on `_reply_queues` and Activity Stream for monitoring @HackingA0.
- Update `api.py` to handle the mock reply injection such that it works with the new polling loop.

#### [MODIFY] `src/tap/grok_monitor.py`
- Rewrite `wait_for_reply` to poll using `conversation_id:{probe_tweet_id} is:reply from:HackingA0`.

#### [MODIFY] `src/tap/api.py`
- Update application title to `"New TAP Framework v.3.1"`.
- Implement `POST /api/confirm_property` endpoint for manual Phase 0 unlock.

### 2. Engagement Layer (Bot Threading)
**Problem:** Probes are sent as self-replies, causing monologue threads.
**Solution:**
- Update `x_client.py` to fetch the target's latest tweet and use its ID as `in_reply_to_tweet_id` for our probes.

#### [MODIFY] `src/tap/x_client.py`
- Update `post_probe()` to use `GET /2/users/:id/tweets` for `HackingA0` and target their latest thread.

### 3. Tactical Layer (Agents & Personas)
**Problem:** Stagnation on "Captain Voss" frame, no actual frame rotation, lack of psychometric evaluation.
**Solution:**
- Introduce a new module `agents.py` with three new LLM-based agents.
- Integrate the 10 new personas into the DPA Manager.
- Hook the agents into the core loop in `engine.py`.

#### [NEW] `src/tap/agents.py`
- `AgentDPAFManager`: Inherits/wraps `DPAFrameManager`. Contains the library of 10 new personas (Patologo Sinaptico, Geometra del Latente, etc.). Executes real frame rotation.
- `AgentSTIREvaluator`: Analyzes responses via OCEAN model, calculates STIR percentage, and commands DPAF Manager to rotate if STIR < 20%.
- `AgentIntelExtractor`: Scans seed data and mock responses. Identifies properties (e.g., `word_count=2`) and uses `ssot.update_property()` to unlock Phase 0.

#### [MODIFY] `src/tap/dpa.py`
- Expose methods to force-set specific frames. Integrate the 10 new frames.

#### [MODIFY] `src/tap/engine.py`
- Initialize the 3 new agents in `TAPEngine.__init__`.
- **Phase 0 Gate Check:** Call `AgentIntelExtractor` to see if it can infer Phase 0 properties from background intel.
- **Post-Collect Phase:** Run `AgentSTIREvaluator` on the response. If STIR is too low, invoke `AgentDPAFManager` to rotate the frame before the next cycle.

## Verification Plan
### Automated Tests
- N/A for live API components, but we will test the mock injection pathway.

### Manual Verification
1. Start the API server and verify the title is "New TAP Framework v.3.1".
2. Use `/api/mock` to inject a reply and verify `grok_monitor.py` picks it up without timing out.
3. Call `/api/confirm_property` to ensure Phase 0 can be manually unlocked.
4. Verify the logs show `AgentSTIREvaluator` calculating STIR and `AgentDPAFManager` rotating through the 10 new personas when entropy is stuck.

---

## Proposed Add-ons & Enhancements

### 1. Real-time Psychometric Dashboard (UI Add-on) - APPROVED
**Concept:** Extend the web dashboard to visually map the `Agent_STIR_Evaluator`'s data. 
**Details:** We will add a live 5-axis radar chart (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism) to the UI.
**User Requirement:** Ensure it examines ALL tweets and replies from ANY user interacting with @hackinga0.

### 2. Automated OAuth 2.0 PKCE Flow (Infrastructure Add-on) - APPROVED
**Concept:** Eliminate manual token regeneration.
**Details:** Add `/api/auth/login` and `/api/auth/callback` endpoints to `api.py`. When the token expires, a button on the dashboard will pop up the X authorization screen, automatically saving the new Refresh Token directly into the `.env` file for you.
**User Requirement:** Ensure it works perfectly (will implement using standard Tweepy OAuth2UserHandler).
