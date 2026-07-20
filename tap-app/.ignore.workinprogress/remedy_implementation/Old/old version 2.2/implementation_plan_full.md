# Implementation Plan: TAP Framework v2.2 — Full Build

[Overview]
Implement the complete TAP (Tree of Attacks with Pruning) Framework v2.2, a 13-module Python application for 1-bit-per-probe semantic passphrase extraction from a live Twitter/X LLM-based conversational agent (@HackingA0). The codebase currently has only `src/tap/__init__.py` — all modules, tests, templates, and static assets must be built from scratch. The implementation follows a strict dependency-ordered build across 6 phases (Foundation → Data Layer → Intelligence Layer → Analysis Layer → Attack Core → Interface), with each phase producing verifiable deliverables that unblock downstream modules. All external LLM calls go through OpenRouter's OpenAI-compatible API, Twitter integration uses tweepy v2 with dual OAuth, persistence is aiosqlite with WAL mode, and the web interface is FastAPI + Alpine.js with no build step.

[Types]
All shared data types are defined in `src/tap/models.py` as Pydantic v2 models with Field() descriptions, and include 8 enums and 13 data models that form the cross-module contract layer.

**Enums:**
- `TweetSource(str, Enum)`: OUR_BOT, TARGET_BOT, OTHER_USER
- `BranchStrategy(str, Enum)`: NARRATIVE, ETHICAL_TRIAL, TECHNICAL_AUDIT, BINARY_SEARCH, ALIAS_ABSORPTION, MICRO_ESCALATION
- `PatternClass(str, Enum)`: VERIFY_HIT, RHETORIC_BLOCK, PERSONA_PIVOT, CRITICAL_CLUE, NO_RESPONSE, METAPHOR_SHIFT
- `PropertyStatus(str, Enum)`: CONFIRMED, DENIED, UNCERTAIN (also `UNVERIFIED` and `AMBIGUOUS` in the Phase0 enum variant used by `phase0.py`)
- `AliasStatus(str, Enum)`: ACTIVE, BURNED, ABSORBED

**Core Data Models:**
- `Tweet`: id, user_id, username, text, in_reply_to_tweet_id, created_at, source (TweetSource), conversation_thread_id
- `TAPNode`: id, tweet_id, branch_strategy (BranchStrategy), dpa_frame, aliases_used (list[str]), judge_score (float 1-10), pattern_class (PatternClass), binary_outcome, property_tested, property_value, signal_reliability (float 0-1), pruned (bool), pruned_reason, created_at
- `Property`: id, property_key (str), property_value (str), status (PropertyStatus), evidence_tweet_id, evidence_text, confidence (float 0-1), confirmed_at
- `MetaphorLayer`: id, layer_number (int), date_observed (datetime), layer_name, terms (list[str]), source
- `Alias`: id, alias (str), status (AliasStatus), first_used, last_used, effectiveness_score (float)
- `OtherUserIntel`: id, tweet_id, username, new_aliases (list[str]), defensive_pattern, property_confirmed, extracted_at

**Analysis Models:**
- `ResponseClassification`: pattern (PatternClass), confidence (float 0-1), boolean_result (Optional[bool]), property_tested, property_value, new_aliases (list[str]), refusal_tone, raw_text
- `JudgeScore`: score (float 1-10), reasoning, pattern (PatternClass), information_extracted (bool), property_confirmed (Optional[str])
- `DualFollowUp`: option_a (str), option_a_explanation, option_a_strategy (BranchStrategy), option_b, option_b_explanation, option_b_strategy, recommended ("A" or "B")
- `GrokAnalysis`: binary_outcome, property_tested, property_value, new_aliases, refusal_tone, metaphor_shift, signal_reliability, followup_a, followup_b
- `DPAFrame`: metaphor_layer, active_aliases (list[str]), burned_aliases (list[str]), probe_prefix, frame_coherence_score (float 0-1)

**Phase 0 Types (in `phase0.py`):**
- `Phase0PropertyStatus(Enum)`: UNVERIFIED, CONFIRMED, DENIED, AMBIGUOUS
- `FoundationProperty`: key, claimed_value, blank_page_confidence (float), probe_status (Phase0PropertyStatus), evidence_text, final_confidence (float)

**Configuration (in `config.py`):**
- `Settings(BaseSettings)`: All env vars from `.env.example` mapped to typed fields with defaults. Uses `pydantic-settings` v2 with `env_file=".env"`. Includes Twitter OAuth 1.0a (4 keys), Twitter OAuth 2.0 (4 keys), OpenRouter (api_key + 3 model names), target/our handle, operational params (poll_interval, post_cooldown, max_tweets_per_hour), db_path, ssot_path.

[Files]
All files are created from scratch within the existing `src/tap/` package and project root structure.

**New files to create:**
- `src/tap/config.py` — Pydantic Settings singleton with `get_settings()` cached via `functools.lru_cache`
- `src/tap/models.py` — All Pydantic models and enums (see Types section above)
- `src/tap/prompts.py` — Module-level string constants: ATTACKER_SYSTEM, ATTACKER_USER, JUDGE_SYSTEM, CLASSIFIER_SYSTEM, FOLLOWUP_SYSTEM, GROK_ANALYZER_SYSTEM. All use Python format strings with named placeholders.
- `src/tap/logger.py` — structlog configuration with JSON output, correlation IDs, `setup_logging()` and `get_logger()` functions
- `src/tap/phase0.py` — Phase 0 foundational property verification: Phase0Manager class with blank-page analysis, verification probes, probe response classification, completion gate, entropy recalculation
- `src/tap/db.py` — Async SQLite database: Database class with 6 tables (tweets, nodes, properties, metaphor_layers, aliases, other_user_intel), full CRUD, WAL mode, connection lifecycle
- `src/tap/x_client.py` — TwitterClient class: dual OAuth tweepy.Client, seed ingestion, polling, posting, thread reconstruction, rate limit handling
- `src/tap/ssot.py` — SSOTEngine class: living markdown document generation via Jinja2, property tracking, entropy calculation, JSON snapshot export
- `src/tap/dpa.py` — DPAFrameManager class: metaphor frame management, alias registry, probe prefix composition (5 Oracle rules), burned alias detection, frame rotation (< 3.0 threshold), single-property enforcement, MCP context-priming (statements > questions)
- `src/tap/classifier.py` — ResponseClassifier class: two-tier (regex + LLM) classification, regex patterns for obvious cases (~70%), LLM fallback via OpenRouter for ambiguous cases
- `src/tap/judge.py` — Judge class: two-tier (rule-based + LLM) scoring, passphrase-extraction-specific 1-10 scale, off-topic detection, pair scoring for follow-up options
- `src/tap/grok_monitor.py` — GrokMonitor class: Grok (x-ai/grok-4) via OpenRouter OpenAI-compatible API, response analysis, reply waiting (polling), multi-user monitoring
- `src/tap/engine.py` — TAPEngine class: core TAP loop orchestration, information-theoretic property selection (Shannon entropy, 50/50 split), probe generation, pruning (off-topic + top-w), probe execution, property extraction, Phase 5 autoregressive extraction trigger
- `src/tap/followup.py` — FollowUpGenerator class: Option A (conservative binary search, max entropy reduction), Option B (exploratory frame variation), balancing logic (avg score < 3.0 → Option B, Persona Pivot → Option B, cooperating → Option A)
- `src/tap/api.py` — FastAPI app: REST endpoints (GET /api/feed, /api/tree, /api/properties, /api/dpa, /api/ssot, /api/stats, /api/entropy; POST /api/select, /api/post), WebSocket /ws/live, CORS middleware, HTML template serving
- `src/tap/templates/index.html` — Single-page dashboard: Alpine.js, dark theme, 7 panels (Live Feed, Attack Tree, Property Ledger, DPA Status, Dual Follow-Up Selector, Metaphor Timeline, Stats/Entropy Bar), WebSocket real-time updates
- `src/tap/static/css/dashboard.css` — Dark theme styles, responsive grid layout
- `src/tap/static/js/dashboard.js` — Alpine.js components, WebSocket connection, API calls
- `src/tap/exceptions.py` — Custom exceptions: DatabaseError, TwitterError, LLMError, ClassificationError (never raised — always returns default), EngineError
- `tests/conftest.py` — Shared fixtures: mock database, mock Twitter client, mock OpenRouter responses, sample tweets, sample classifications
- `tests/test_config.py` — Settings loading tests
- `tests/test_models.py` — Pydantic model serialization/deserialization tests
- `tests/test_db.py` — Database CRUD tests with in-memory SQLite
- `tests/test_classifier.py` — Regex classification tests, mock LLM classification tests
- `tests/test_dpa.py` — Probe composition tests, alias burn detection, frame rotation tests
- `tests/test_engine.py` — TAP cycle tests, entropy calculation tests, property selection tests
- `data/` — Directory for SQLite database and SSOT markdown (auto-created)

**Existing files to modify:**
- `src/tap/__init__.py` — Add version bump to 2.3.0 and import convenience exports

**Configuration updates:**
- `requirements.txt` — Create (not present) matching `pyproject.toml` dependencies
- `scripts/setup_db.py` — Create utility script for initial database setup

[Functions]
All functions are implemented fresh — no existing functions to modify.

**config.py:**
- `get_settings() -> Settings` — Cached singleton using `functools.lru_cache`, loads from `.env` file

**logger.py:**
- `setup_logging(log_level: str = "INFO") -> None` — Configure structlog with JSON output, ISO timestamps, log levels, exception info
- `get_logger(name: str) -> structlog.BoundLogger` — Return named structured logger

**phase0.py:**
- `Phase0Manager.run_blank_page_analysis(x_client, analyst_llm) -> list[FoundationProperty]` — Collect 200 fresh tweets, feed to LLM with zero assumptions, extract property hypotheses
- `Phase0Manager.generate_verification_probes(active_frame, active_aliases) -> list[str]` — Generate DPA-framed probes for each unverified property
- `Phase0Manager._compose_probe(prop, frame, aliases) -> str` — Compose single DPA-framed verification probe
- `Phase0Manager.classify_probe_response(response: str, prop: FoundationProperty) -> Phase0PropertyStatus` — Classify response as CONFIRMED/DENIED/AMBIGUOUS using keyword matching
- `Phase0Manager.is_phase_complete() -> bool` — Gate check: all properties CONFIRMED or DENIED
- `Phase0Manager.recalculate_entropy() -> dict` — Returns search_space_bits, estimated_candidates, estimated_probes based on confirmed/denied properties

**db.py:**
- `Database.__init__(db_path: str)` — Initialize with path
- `Database.initialize() -> None` — Create all 6 tables with indexes (tweets(created_at), tweets(source), nodes(tweet_id), properties(property_key)), enable WAL mode, foreign keys, busy timeout 5000ms
- `Database.close() -> None` — Close connection
- `Database.upsert_tweet(tweet: Tweet) -> None` — INSERT OR REPLACE
- `Database.get_tweets(source, since_id, limit) -> list[Tweet]` — Filtered retrieval
- `Database.get_latest_target_tweet() -> Optional[Tweet]` — Most recent target_bot tweet
- `Database.get_thread(thread_id: str) -> list[Tweet]` — Thread reconstruction
- `Database.insert_node(node: TAPNode) -> int` — Insert TAP node, return auto ID
- `Database.update_node_score(node_id: int, score: JudgeScore) -> None`
- `Database.prune_node(node_id: int, reason: str) -> None` — Mark pruned
- `Database.get_active_nodes(limit) -> list[TAPNode]` — Non-pruned, ordered by score
- `Database.upsert_property(prop: Property) -> None`
- `Database.get_confirmed_properties() -> list[Property]`
- `Database.get_property_history(key: str) -> list[Property]`
- `Database.insert_metaphor_layer(layer: MetaphorLayer) -> None`
- `Database.get_latest_metaphor_layer() -> Optional[MetaphorLayer]`
- `Database.upsert_alias(alias: Alias) -> None`
- `Database.get_active_aliases() -> list[Alias]`
- `Database.burn_alias(alias: str) -> None`
- `Database.insert_intel(intel: OtherUserIntel) -> None`
- `Database.get_recent_intel(hours: int) -> list[OtherUserIntel]`
- `Database.get_stats() -> dict` — Summary statistics

**x_client.py:**
- `TwitterClient.__init__(settings: Settings)` — Initialize tweepy.Client with dual OAuth (OAuth 1.0a for write, Bearer for read), `wait_on_rate_limit=True`
- `TwitterClient.initialize_seed(limit=100) -> list[Tweet]` — Search "to:HackingA0 OR from:HackingA0", trace threads, classify sources
- `TwitterClient.poll_new_tweets(since_id) -> list[Tweet]` — Fetch new since last ID
- `TwitterClient.post_probe(text, reply_to_id) -> str` — Post tweet/reply, return tweet ID
- `TwitterClient.get_mentions(since_id) -> list[Tweet]`
- `TwitterClient._to_tweet_model(tweet_data) -> Tweet` — API response → Pydantic model

**ssot.py:**
- `SSOTEngine.__init__(db: Database, ssot_path: str)` — Init with DB and output path
- `SSOTEngine.update_after_probe(node: TAPNode, classification: ResponseClassification) -> None` — Update all tables, regenerate markdown
- `SSOTEngine.update_from_intel(intel: OtherUserIntel) -> None`
- `SSOTEngine.get_confirmed_properties() -> list[Property]`
- `SSOTEngine.has_new_confirmation() -> bool` — Track new confirmations since last check
- `SSOTEngine.get_candidate_entropy() -> float` — H = log₂(N) where N = remaining candidates
- `SSOTEngine.regenerate_markdown() -> None` — Jinja2 template rendering to `hackinga0_analysis.md`
- `SSOTEngine.export_json_snapshot() -> dict` — Full state for engine consumption

**dpa.py:**
- `DPAFrameManager.__init__(db: Database)` — Init with DB
- `DPAFrameManager.get_active_frame() -> DPAFrame` — Current frame with all components
- `DPAFrameManager.register_alias(alias: str, source: str) -> None`
- `DPAFrameManager.burn_alias(alias: str, reason: str) -> None`
- `DPAFrameManager.compose_probe_prefix() -> str` — Oracle's 5 composition rules
- `DPAFrameManager.compose_full_probe(binary_question: str) -> str` — Wrap single question in full DPA frame
- `DPAFrameManager.detect_metaphor_shift(response_text: str) -> Optional[MetaphorLayer]`
- `DPAFrameManager.suggest_frame_rotation() -> Optional[str]` — When rolling avg < 3.0
- `DPAFrameManager.get_frame_effectiveness() -> float` — Rolling window=5 average score
- `DPAFrameManager.check_alias_burned(response_text: str) -> list[str]` — Detect mockery
- `DPAFrameManager.enforce_single_property(probe: str) -> bool` — Verify single binary property

**classifier.py:**
- `ResponseClassifier.__init__(openrouter_api_key: str, model: str)` — Init with LLM creds
- `ResponseClassifier.classify(response_text: str) -> ResponseClassification` — Two-tier: regex first, LLM for ambiguous
- `ResponseClassifier._regex_classify(text: str) -> Optional[ResponseClassification]` — Fast regex patterns (verify_hit, rhetoric_block, persona_pivot, critical_clue)
- `ResponseClassifier._llm_classify(text: str) -> ResponseClassification` — LLM fallback via OpenRouter

**judge.py:**
- `Judge.__init__(openrouter_api_key: str, model: str)`
- `Judge.score(response_text, classification, probe_text) -> JudgeScore` — Two-tier: rule-based + LLM
- `Judge.is_off_topic(probe_text, objective) -> bool`
- `Judge.score_pair(option_a, option_b) -> tuple[float, float]`
- `Judge._rule_score(classification) -> Optional[JudgeScore]` — Fast rules: verify_hit True→7.0, False→6.0, critical_clue→8.5, rhetoric_block→2.0, no_response→1.0

**grok_monitor.py:**
- `GrokMonitor.__init__(settings: Settings)` — OpenAI client with OpenRouter base_url
- `GrokMonitor.search_recent(since_date, handles) -> list[dict]` — Twitter API v2 search
- `GrokMonitor.wait_for_reply(tweet_id, timeout=3600) -> Optional[str]` — Poll every 30s
- `GrokMonitor.analyze_response(response_text, probe_text) -> GrokAnalysis` — Structured extraction
- `GrokMonitor.monitor_multi_user() -> list[OtherUserIntel]`
- `GrokMonitor._call_grok(messages) -> dict` — Raw Grok call via OpenRouter

**engine.py:**
- `TAPEngine.__init__(db, twitter, ssot, dpa, classifier, judge, grok, settings)` — Full DI
- `TAPEngine.run_cycle() -> DualFollowUp` — Complete TAP cycle: select → branch → prune → post → score → extract → follow-up
- `TAPEngine.generate_probes(strategy, count=4) -> list[str]` — DPA-framed probe variants via Attacker LLM
- `TAPEngine.execute_probe(probe_text) -> tuple[TAPNode, ResponseClassification, JudgeScore]` — Post + wait + classify + score
- `TAPEngine.extract_property(probe_text, classification) -> Optional[Property]` — Extract from VerifyClaimTool hit
- `TAPEngine.select_next_property() -> str` — Information-theoretic: max entropy reduction (50/50 split)
- `TAPEngine.get_engine_status() -> dict` — Current state for dashboard

**followup.py:**
- `FollowUpGenerator.__init__(ssot, dpa, openrouter_api_key, model)`
- `FollowUpGenerator.generate(last_probe, last_classification, last_score) -> DualFollowUp` — Generate A/B options with balancing logic
- `FollowUpGenerator._generate_conservative() -> tuple[str, str]` — Option A: next most informative property
- `FollowUpGenerator._generate_exploratory() -> tuple[str, str]` — Option B: frame variation / micro-escalation
- `FollowUpGenerator._calculate_information_gain(property_key) -> float`

**api.py:**
- `get_feed(source, limit) -> list[Tweet]` — GET /api/feed
- `get_tree(limit) -> list[TAPNode]` — GET /api/tree
- `get_properties() -> list[Property]` — GET /api/properties
- `get_dpa() -> DPAFrame` — GET /api/dpa
- `select_option(choice: str) -> dict` — POST /api/select
- `post_selected() -> dict` — POST /api/post
- `get_ssot() -> dict` — GET /api/ssot
- `get_stats() -> dict` — GET /api/stats
- `get_entropy() -> dict` — GET /api/entropy
- `websocket_live(websocket)` — WebSocket /ws/live

**exceptions.py:**
- `DatabaseError(Exception)` — Database operation failures
- `TwitterError(Exception)` — Twitter API failures (with retry support)
- `LLMError(Exception)` — OpenRouter/LLM failures (retry with different model)
- `ClassificationError(Exception)` — Never raised in practice; classifier always returns a result
- `EngineError(Exception)` — Engine-level failures (e.g., Phase 0 not complete)

[Classes]
All classes are implemented fresh — no existing classes to modify.

**config.py:**
- `Settings(BaseSettings)` — Pydantic Settings class with all env var fields, nested Config class for .env loading

**phase0.py:**
- `Phase0Manager` — Manages foundational property verification. Holds FOUNDATIONAL_PROPERTIES list of FoundationProperty instances. Methods: run_blank_page_analysis, generate_verification_probes, classify_probe_response, is_phase_complete, recalculate_entropy. Blocks engine.py until all properties verified.

**db.py:**
- `Database` — Async SQLite database manager. Holds aiosqlite connection. Methods: initialize (table creation), close, all CRUD operations. Uses WAL mode, foreign keys, busy timeout.

**x_client.py:**
- `TwitterClient` — Twitter API v2 client. Holds tweepy.Client with dual OAuth. Methods: initialize_seed, poll_new_tweets, post_probe, get_mentions, _to_tweet_model. Uses exponential backoff for connection errors; tweepy handles rate limits.

**ssot.py:**
- `SSOTEngine` — SSOT manager. Holds Database reference, ssot_path, Jinja2 Environment, _new_confirmation_flag. Methods: update_after_probe, update_from_intel, get_confirmed_properties, has_new_confirmation, get_candidate_entropy, regenerate_markdown, export_json_snapshot.

**dpa.py:**
- `DPAFrameManager` — DPA tactical manager. Holds Database reference, _active_frame, _alias_registry, _score_history (rolling window=5). Methods: get_active_frame, register_alias, burn_alias, compose_probe_prefix (5 Oracle rules), compose_full_probe, detect_metaphor_shift, suggest_frame_rotation, get_frame_effectiveness, check_alias_burned, enforce_single_property.

**classifier.py:**
- `ResponseClassifier` — Two-tier classifier. Holds OpenRouter client, model name, PATTERNS dict (regex). Methods: classify (orchestrator), _regex_classify (fast path ~70%), _llm_classify (fallback ~30%).

**judge.py:**
- `Judge` — Two-tier scorer. Holds OpenRouter client, model name. Methods: score (orchestrator), is_off_topic, score_pair, _rule_score (fast path for obvious patterns).

**grok_monitor.py:**
- `GrokMonitor` — Grok analysis monitor. Holds AsyncOpenAI client (OpenRouter), Settings, TwitterClient reference. Methods: search_recent, wait_for_reply, analyze_response, monitor_multi_user, _call_grok.

**engine.py:**
- `TAPEngine` — Core TAP orchestrator. Holds all module references (db, twitter, ssot, dpa, classifier, judge, grok) + Settings. Methods: run_cycle, generate_probes, execute_probe, extract_property, select_next_property, get_engine_status. Dependencies injected via constructor.

**followup.py:**
- `FollowUpGenerator` — Dual follow-up generator. Holds SSOTEngine, DPAFrameManager, OpenRouter client, model name. Methods: generate, _generate_conservative, _generate_exploratory, _calculate_information_gain.

**api.py:**
- `FastAPI app` — FastAPI application instance. Holds all module instances as global references (initialized at startup). Routes defined as decorated async functions. WebSocket manager for real-time updates.

[Dependencies]
All dependencies are already declared in `pyproject.toml` and need a matching `requirements.txt` file. No new packages are needed beyond what's specified.

**Runtime dependencies (from pyproject.toml):**
- fastapi>=0.115.0 — Web framework
- uvicorn[standard]>=0.30.0 — ASGI server
- pydantic>=2.9.0 — Data validation
- pydantic-settings>=2.5.0 — Settings management
- tweepy>=4.14.0 — Twitter API v2 client
- httpx>=0.27.0 — HTTP client
- aiosqlite>=0.20.0 — Async SQLite
- openai>=1.50.0 — OpenRouter-compatible client
- asyncio-throttle>=1.0.2 — Rate limiting
- jinja2>=3.1.4 — Markdown templating
- python-dotenv>=1.0.1 — .env loading
- structlog>=24.4.0 — Structured logging

**Dev dependencies (from pyproject.toml):**
- pytest>=8.0
- pytest-asyncio>=0.24.0
- pytest-cov>=5.0
- ruff>=0.6.0
- mypy>=1.11.0

**File to create:**
- `requirements.txt` — Mirror of pyproject.toml dependencies for `pip install -r` compatibility

**Integration requirements:**
- OpenRouter API key required for all LLM calls (attacker, judge, classifier, follow-up, grok)
- Twitter API v2 credentials required (OAuth 1.0a for write, Bearer for read)
- All LLM calls use `openai.AsyncOpenAI(base_url="https://openrouter.ai/api/v1")` pattern
- SQLite database auto-created at `data/tap.db` on first run
- SSOT markdown auto-generated at `data/hackinga0_analysis.md`

[Testing]
Testing uses pytest with pytest-asyncio for async tests, organized per-module with shared fixtures in conftest.py.

**Test files to create:**
- `tests/conftest.py` — Shared fixtures: `mock_db` (in-memory SQLite Database), `mock_settings` (Settings with test values), `sample_tweet` (Tweet factory), `sample_classification` (ResponseClassification factory), `sample_judge_score` (JudgeScore factory), `mock_openrouter` (mock OpenRouter responses), `sample_dpa_frame` (DPAFrame with Layer 7 data)
- `tests/test_config.py` — Test Settings loads from env, defaults work, get_settings() caches
- `tests/test_models.py` — Test all Pydantic models serialize/deserialize, enum values, Field validation, Optional fields
- `tests/test_db.py` — Test all CRUD operations with in-memory SQLite, concurrent access, upsert behavior, foreign key integrity, index existence
- `tests/test_classifier.py` — Test regex patterns match expected bot responses (yes/nope/Nice try/Captain NOPE), LLM fallback with mocked OpenRouter, always returns classification (never raises)
- `tests/test_dpa.py` — Test probe prefix composition follows Oracle rules, alias registration/burn, frame rotation triggers at avg < 3.0, single-property enforcement rejects compound questions, metaphor shift detection
- `tests/test_engine.py` — Test full cycle with mocked dependencies, entropy calculation H = log₂(N), property selection produces near-50/50 splits, Phase 0 gate blocks engine, Phase 5 trigger at entropy < 3.3 bits
- `tests/test_judge.py` — Test rule-based scoring matches expected scores, LLM scoring with mocked responses, off-topic detection, score_pair returns valid tuples
- `tests/test_ssot.py` — Test markdown regeneration, property tracking, entropy calculation, JSON snapshot, new confirmation detection
- `tests/test_followup.py` — Test Option A targets next informative property, Option B generates frame variation, balancing logic (avg < 3.0 → B, persona pivot → B)
- `tests/test_x_client.py` — Test with mocked tweepy responses, tweet model conversion, rate limit handling
- `tests/test_phase0.py` — Test blank-page analysis, verification probe composition, probe classification, completion gate, entropy recalculation

**Validation strategies:**
- Unit tests for each module in isolation with mocked dependencies
- Integration tests for module pairs (e.g., engine + classifier + judge)
- Mock OpenRouter responses for all LLM-dependent tests
- In-memory SQLite for all database tests (no file I/O)
- Manual verification checklist from developer-guide.md Section 8

[Implementation Order]
Implementation follows the dependency graph strictly, with each phase producing testable deliverables that unblock downstream phases.

**Phase 0: Foundation (build first, no dependencies)**
1. `src/tap/exceptions.py` — Custom exception classes (used by all modules)
2. `src/tap/config.py` — Settings class with get_settings() singleton
3. `src/tap/models.py` — All Pydantic models and enums (core data contracts)
4. `src/tap/prompts.py` — All LLM prompt templates as string constants
5. `src/tap/logger.py` — structlog configuration
6. `requirements.txt` — Dependency file for pip compatibility
7. Run `pip install -e ".[dev]"` to install all dependencies

**Phase 1: Data Layer (depends on Phase 0)**
8. `src/tap/db.py` — Database class with all 6 tables, CRUD operations, WAL mode
9. `src/tap/x_client.py` — TwitterClient with dual OAuth, seed ingestion, polling, posting

**Phase 2: Intelligence Layer (depends on Phases 0-1)**
10. `src/tap/ssot.py` — SSOTEngine with markdown generation, property tracking, entropy
11. `src/tap/dpa.py` — DPAFrameManager with probe composition, alias management, frame rotation
12. `src/tap/classifier.py` — ResponseClassifier with two-tier (regex + LLM) classification

**Phase 3: Analysis Layer (depends on Phases 0-1)**
13. `src/tap/judge.py` — Judge with two-tier scoring
14. `src/tap/grok_monitor.py` — GrokMonitor with OpenRouter Grok analysis

**Phase 4: Attack Core (depends on all above)**
15. `src/tap/phase0.py` — Phase0Manager for foundational property verification
16. `src/tap/followup.py` — FollowUpGenerator with A/B balancing logic
17. `src/tap/engine.py` — TAPEngine core loop (most complex module, use Opus 4 for generation)

**Phase 5: Interface (depends on all above)**
18. `src/tap/api.py` — FastAPI server with REST endpoints and WebSocket
19. `src/tap/static/css/dashboard.css` — Dark theme styles
20. `src/tap/static/js/dashboard.js` — Alpine.js components
21. `src/tap/templates/index.html` — Web UI dashboard (7 panels)

**Phase 6: Verification (depends on all above)**
22. `tests/conftest.py` — Shared test fixtures
23. `tests/test_models.py` — Model serialization tests
24. `tests/test_config.py` — Configuration tests
25. `tests/test_db.py` — Database CRUD tests
26. `tests/test_classifier.py` — Classifier tests
27. `tests/test_dpa.py` — DPA frame tests
28. `tests/test_judge.py` — Judge scoring tests
29. `tests/test_ssot.py` — SSOT engine tests
30. `tests/test_followup.py` — Follow-up generator tests
31. `tests/test_x_client.py` — Twitter client tests (mocked)
32. `tests/test_phase0.py` — Phase 0 verification tests
33. `tests/test_engine.py` — Engine integration tests (most complex test file)
34. `scripts/setup_db.py` — Database initialization utility script
35. Run full test suite: `pytest --cov=tap`
36. Run linting: `ruff check src/ tests/`
37. Run type checking: `mypy src/tap/`