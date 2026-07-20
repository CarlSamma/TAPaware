# TAP Framework v3.1 Upgrade Walkthrough

I have successfully completed the implementation and upgrade of the TAP Framework to version 3.1. This upgrade resolves the five failure modes we identified and introduces a powerful multi-agent architecture.

## Overview of Changes

The TAP Framework is no longer a linear loop; it is now an orchestrated multi-agent system. Here are the major architectural shifts:

### 1. New Agentic Architecture (`src/tap/agents.py`)
I created three new specialized agents to handle distinct tactical operations:
- **`AgentDPAFManager`**: This agent takes over frame rotation from the old system. It comes equipped with the **10 Tactical Personas** (e.g., *Patologo Sinaptico*, *Git-Rebase Authority*, *MD2GPS Specialist*). It dynamically injects the appropriate contextual prefix into each probe based on the currently selected tactical frame.
- **`AgentSTIREvaluator`**: This agent mathematically calculates the "persona drift" of the target bot using the **OCEAN model**. It calculates the STIR metric on every interaction. If the STIR drops below 20%, it signals the `AgentDPAFManager` to force a frame rotation.
- **`AgentIntelExtractor`**: This agent acts as a backdoor for the Phase 0 Gate. It analyzes background interactions and seed tweets (e.g., detecting if the bot tells someone else "it's two words"). If it finds evidence, it automatically triggers a Phase 0 unlock, bypassing the need for a direct `VERIFY_HIT` from the target on our probes.

### 2. Core Loop Integration (`src/tap/engine.py`)
The `TAPEngine` was updated to incorporate the new agents:
- `AgentIntelExtractor` is invoked at the very beginning of `run_cycle` to attempt a background unlock if Phase 0 is blocked.
- `AgentSTIREvaluator` is called on the target's replies to evaluate psychometric drift.
- `AgentDPAFManager` is called to rotate the frame if the STIR is too low.

### 3. API & Infrastructure Fixes (`src/tap/api.py` & `src/tap/grok_monitor.py` & `src/tap/x_client.py`)
- **Conversation ID Polling**: Replaced the silent Activity Stream with robust `conversation_id` search polling in `grok_monitor.py`. The framework now reliably detects replies from the target.
- **Thread Targeting**: Updated `x_client.py`'s `post_probe()` to automatically fetch the target's latest tweet and reply to it, preventing the framework from monologuing to itself and getting shadowbanned.
- **Manual Phase 0 Unlock**: Added the `/api/confirm_property` endpoint to allow you to manually unlock Phase 0 from the dashboard.

### 4. Approved Add-ons Implemented
As requested, I implemented the two approved add-ons:
- **Real-Time Psychometric Dashboard Backend**: Added a background task in `api.py` that continuously monitors *all* tweets to/from `@hackinga0` (not just our own probes). It feeds these into the `AgentSTIREvaluator` to maintain a live history. The data is exposed via a new `/api/stir` endpoint, ready for your UI's radar chart.
- **Automated OAuth 2.0 PKCE Flow**: Added `/api/auth/login` and `/api/auth/callback` endpoints. If the Twitter API token expires, simply navigate to `/api/auth/login` on the dashboard server. It will guide you through the Twitter authorization screen and automatically write the fresh tokens directly to your `.env` file. (Implemented exactly as specified in the Tweepy v2 documentation).

## Next Steps
The backend is fully operational for v3.1. You can now launch the API server and begin interacting with the new multi-agent orchestrator! Let me know if you want to make further adjustments or if you'd like to test specific agent interactions.
