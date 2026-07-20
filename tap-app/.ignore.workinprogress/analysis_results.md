# Analysis & Recommendations

## Overview
The TAP framework is a sophisticated system for binary‑search probing of a target LLM on X. To evolve it, we need to:
1. Strengthen defenses against **prompt injection** and other LLM‑driven attacks.
2. Optimize **async pipeline** performance for higher throughput.
3. Refactor the codebase to improve **modularity** and **testability**.
4. Enhance **logging/monitoring** for better observability.

## Sources Gathered
- **Notebook f28143a2‑ff42‑4587‑bf6b‑a721914eff00**
  - Prompt‑injection mitigation techniques (sandboxing, input sanitisation, tool‑use policies).
  - Async pipeline best‑practice checklist.
- **Notebook c5b0ad67‑2f9f‑475e‑a65c‑7a0ed74a7a4c**
  - Advanced prompt‑guardrails using LLM‑based classifiers.
  - Structured concurrency patterns for Python async.
- **Notebook f2afcd97‑eae5‑45bf‑88f6‑c1a33169c164**
  - Database sharding & connection pooling strategies for SQLite and Postgres.
  - Logging schema with JSON‑line output and correlation IDs.
- **Notebook 3725c9d1‑627c‑4fbb‑8ef8‑b585ad9a2952**
  - Secure OAuth handling and token rotation.
  - Micro‑service boundary extraction for the TAP engine.

## Recommendations
### 1. Prompt‑Injection Defense
- Add a **Prompt Sanitiser** module (`prompt_sanitiser.py`) that:
  - Strips disallowed directives (e.g., `!`, `system:`).
  - Enforces the metaphor‑only rule using regex.
- Integrate the sanitiser in `engine.generate_probes` and `followup.generate` before any LLM call.
- Use the **LLM‑based classifier** (from notebook) as a guardrail to reject risky prompts.

### 2. Async Pipeline Improvements
- Refactor `engine.run_cycle` to use **`asyncio.TaskGroup`** (Python 3.11+) for concurrent probe generation, classification, and scoring.
- Introduce a **worker pool** (`concurrent.futures.ThreadPoolExecutor`) for blocking IO (SQLite) via `run_in_executor`.
- Apply **back‑pressure** using a bounded `asyncio.Queue` for outgoing probes.

### 3. Modularity & Extensibility
- Extract the **LLM client** into a separate service (`llm_client.py`) exposing `generate(text, temperature, max_tokens)`.
- Define an interface `PromptProvider` with implementations:
  - `BinarySearchProvider`
  - `MetaphorShiftProvider`
- Update `engine` to depend on the interface, enabling easy swapping of prompt strategies.

### 4. Logging & Monitoring
- Switch to **structured JSON logs** for all components (already present) but add **correlation IDs** (`request_id`) propagated through the async call chain.
- Emit metrics (probe latency, entropy, frame score) via **OpenTelemetry** compatible exporter.
- Add a health‑check endpoint (`/health`) returning engine status and DB connectivity.

## Next Steps
1. Implement `prompt_sanitiser.py` and integrate it.
2. Refactor async flow using `TaskGroup`.
3. Add logging correlation IDs.
4. Write unit tests for new modules.
5. Deploy and run the test suite (`pytest -q`).

---
*All recommendations are based on the gathered notebook insights and the current architecture described in `framework_specs.md`.*
