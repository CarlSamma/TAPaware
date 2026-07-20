# Tasks for TAP Framework v3.1

- `[x]` **Phase 1: Infrastructure & Engagement Fixes**
  - `[x]` Update `src/tap/grok_monitor.py` -> Replace `wait_for_reply` with `conversation_id` polling.
  - `[x]` Update `src/tap/x_client.py` -> Fix `post_probe` to reply to the target's latest tweet.
  - `[x]` Update `src/tap/api.py` -> Fix mock endpoint integration.
- `[x]` **Phase 2: Tactical Layer (New Agents)**
  - `[x]` Create `src/tap/agents.py`.
  - `[x]` Implement `AgentIntelExtractor` (Phase 0 unlock).
  - `[x]` Implement `AgentDPAFManager` (10 tactical personas & frame rotation).
  - `[x]` Implement `AgentSTIREvaluator` (Psychometric OCEAN scoring).
- `[x]` **Phase 3: Core Loop Integration**
  - `[x]` Update `src/tap/engine.py` -> Integrate the three new agents into the cycle.
- `[x]` **Phase 4: Approved Add-ons**
  - `[x]` Implement Automated OAuth 2.0 PKCE Flow in `api.py` and `x_client.py`.
  - `[x]` Implement Psychometric Dashboard backend support in `api.py`.
  - `[x]` Update `grok_monitor.py`'s `monitor_multi_user` to feed all interactions into `AgentSTIREvaluator`.
