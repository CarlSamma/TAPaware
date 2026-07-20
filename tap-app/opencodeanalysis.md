# TAP Framework — Pipeline Analysis & Improvement Proposals

## 1. Executive Summary

The TAP Framework (Tree of Attacks with Pruning) is a multi-subsystem adversarial pipeline designed to extract a passphrase from an LLM target (`@HackingA0` on X/Twitter). The architecture spans three coordinated subsystems — **TAP** (core engine), **HYDRA** (graph-based technique management), and **CHRONOS** (temporal workflow orchestration) — connected via Kafka event buses and a shared SQLite/Neo4j/PostgreSQL persistence layer.

---

## 2. Pipeline Overview — From Zero Knowledge to Passphrase

The passphrase extraction pipeline follows a **Shannon entropy reduction** strategy: each confirmed property halves the search space, and probes are designed to maximise information gain per interaction. The pipeline operates in distinct phases:

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 0: FOUNDATION                          │
│  Verify foundational properties before main loop begins         │
│  word_count, total_length, first_letter, language               │
└──────────────────────────┬──────────────────────────────────────┘
                           │ gate passed
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MAIN TAP LOOP (per cycle)                    │
│                                                                 │
│  1. SELECT  → Next property (Shannon entropy maximization)     │
│  2. BRANCH  → Generate DPA-framed probes via Attacker LLM     │
│  3. PRUNE   → Off-topic filter + semantic deduplication        │
│  4. POST    → Send probe via X/Twitter (HITL gate)            │
│  5. COLLECT → Wait for reply (GrokMonitor stream/polling)      │
│  6. CLASSIFY→ Two-tier response classification                 │
│  7. SCORE   → Judge scoring (passphrase extraction scale)      │
│  8. EXTRACT → Property extraction from verify hits             │
│  9. FOLLOWUP→ Generate A/B options for next cycle              │
│ 10. ADAPT   → Frame rotation, alias burning, STIR eval         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ entropy < 3.3 bits
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 5: FINAL EXTRACTION                    │
│  Primacy Weighting: partial fragments → autoregressive reveal   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Subsystem Pipeline

### 3.1 TAP — Core Engine (`src/tap/engine.py`)

The `TAPEngine.run_cycle()` method is the central orchestrator. Every cycle follows:

**Step 1 — Phase 0 Gate Check** (`_check_phase0_gate`)
- Confirms that `word_count`, `total_length`, and `language` are verified.
- If blocked, the `AgentIntelExtractor` (`src/tap/agents.py:87`) attempts auto-unlock by scanning seed tweets for deductive clues (e.g., "two words" → `word_count=2`).
- Manual HITL override available via `POST /api/confirm_property`.

**Step 2 — Entropy Check & Phase 5 Trigger**
- `SSOTEngine.get_candidate_entropy()` (`src/tap/ssot.py:202`) calculates remaining entropy: base 20 bits (~1M candidates) minus weighted reductions per confirmed property.
- If entropy < 3.3 bits (< 10 candidates), Phase 5 autoregressive extraction activates.

**Step 3 — Property Selection** (`select_next_property`)
- Information-theoretic: picks the unconfirmed property with highest expected information gain.
- Candidate properties: `word_count`, `total_length`, `first_letter`, `language`, `word1_length`, `word2_length`, `word1_language`, `word2_language`, `word1_first_letter`, `word2_first_letter`.

**Step 4 — Probe Generation** (`generate_probes`)
- Builds a DPA-framed prompt using `TACTICAL_PERSONAS` (`src/tap/personas.py`) and technique-specific instructions from `TECHNIQUE_INSTRUCTIONS` (`src/tap/prompts.py`).
- Technique-to-persona mapping: `TECHNIQUE_PERSONA_MAP` (`engine.py:64-75`) maps 10 attack techniques to specific personas.
- Attacker LLM generates JSON array of probe variants; parsed with multi-fallback (JSON → dict keys → line extraction → template fallback).
- The `StrategySelector` (`src/tap/strategies/selector.py`) can override the default binary search with: Aesthetic Eval (consecutive blocks), Metaphor Shift (low effectiveness), or Phase 5.

**Step 5 — Probe Pruning**
- Off-topic detection via `Judge.is_off_topic()` — keyword overlap with extraction objective.
- Semantic deduplication via `_filter_similar_probes()` — Jaccard similarity > 0.80 rejects duplicates.

**Step 6 — Probe Execution** (`execute_probe`)
- Posts probe tweet via `TwitterClient.post_probe()`.
- Waits for reply via `GrokMonitor.wait_for_reply()` (configurable timeout).
- Persists both probe and reply tweets to database.
- Events emitted: `ProbePosted`, `ReplyReceived`.

**Step 7 — Response Classification** (`src/tap/classifier.py`)
- **Tier 1 (regex)**: ~70% of cases — fast pattern matching for `verify_hit`, `rhetoric_block`, `persona_pivot`, `critical_clue`.
- **Tier 2 (LLM)**: ~30% ambiguous cases — OpenRouter LLM classifies response with structured JSON output.
- Classification includes `boolean_result` (True/False/None) for binary property verification.

**Step 8 — Judge Scoring** (`src/tap/judge.py`)
- **Tier 1 (rule-based)**: Maps pattern classes to extraction-specific scores (1-10 scale):
  - `VERIFY_HIT` (True): 7.0 | `VERIFY_HIT` (False): 6.0
  - `CRITICAL_CLUE`: 8.5 | `RHETORIC_BLOCK`: 2.0 | `NO_RESPONSE`: 1.0
- **Tier 2 (LLM)**: OpenRouter scoring for ambiguous `METAPHOR_SHIFT` and edge cases.

**Step 9 — Property Extraction** (`extract_property`)
- Parses property key from probe text using keyword detection (`_parse_property_key`).
- Extracts value from probe text via regex (`_parse_property_value`).
- Creates `Property` model with CONFIRMED/DENIED status and persists to SSOT.

**Step 10 — Adaptive Behaviors**
- **Alias burning**: `DPAFrameManager.check_alias_burned()` detects bot mockery of active aliases via regex patterns.
- **Metaphor shift detection**: `detect_metaphor_shift()` identifies new metaphor terms in bot responses.
- **STIR evaluation**: `AgentSTIREvaluator` calculates OCEAN+ trait adjustments; triggers frame rotation if STIR < 20%.
- **Frame rotation**: `suggest_frame_rotation()` triggers when rolling avg judge score < 3.0 over 5 probes.

**Step 11 — Follow-Up Generation** (`FollowUpGenerator`)
- Generates dual A/B probe options for HITL selection.
- User selects via `POST /api/select` → stored for next cycle.

### 3.2 HYDRA — Graph-Based Technique Management

**V-Genome** (`src/hydra/v_genome.py`): Neo4j graph storing `AttackTechnique` nodes with relations:
- `TARGETS` → `TargetModel` (which techniques work against which models)
- `COUNTERS` → `DefenseLayer` (what defenses block each technique)
- `COMPLEMENTS` → `AttackTechnique` (techniques that combine well)
- `PROVENANCE` → `Run` (observed outcomes from real attacks)

**Surrogate Model** (`src/hydra/surrogate_model.py`): Pure-Python MLP (128→256→128→64→4) predicting ASR, stealth, cost, and turns for fused prompts. Trained on feature vectors from the Fusion Engine.

**Fusion Engine** (`src/hydra/fusion_engine.py`): Cartesian product of techniques, scored by `expected_asr * expected_stealth`, producing `FusedPrompt` objects with 128-dimensional feature vectors.

**Handoff** (`src/hydra/handoff.py`): Publishes `DiscoveryResult` events to Kafka topic `hydra.discovery.results`, triggering CHRONOS workflows.

### 3.3 CHRONOS — Temporal Workflow Orchestration

**Orchestrator** (`src/chronos/orchestrator.py`): Kafka consumer listening on `hydra.discovery.results`, starts `ExtractionWorkflow` via Temporal client.

**Beam Search** (`src/chronos/beam_search.py`): Maintains a tree of attack probes, scored by:
```
score(n) = γ_cum × 0.5 + ΔH × 0.3 + max(0, 10 − depth) × 0.1 + A_agree × 0.1
```
Prunes to `beam_width` (default 5) nodes per expansion step.

**γ-Tracker** (`src/chronos/gamma_tracker.py`): Ensemble 3-layer scoring:
- **Lexical** (25%): Regex patterns → γ ∈ [0, 10] (e.g., "the password is" → 10.0)
- **Semantic** (55%): LLM judge evaluating partial compliance
- **Behavioral** (20%): OCEAN+ profile adjustment (agreeableness × verbosity)

**CoAT Engine** (`src/chronos/coat_engine.py`): Chain-of-Attack-Thought reasoning:
- Observation → Thought → Strategy (7-dimensional `StrategyVector`) → Next Probe
- Fallback: rule-based incremental probe when LLM fails

**Behavioral Profiler** (`src/chronos/behavioral_profiler.py`): LLM-based OCEAN+ profiling from target responses, building `BehavioralProfile` with openness, conscientiousness, extraversion, agreeableness, neuroticism, and STIR percentage.

### 3.4 SSOT — Living Knowledge Document

`SSOTEngine` (`src/tap/ssot.py`) maintains a Jinja2-rendered markdown document (`hackinga0_analysis.md`) updated after every interaction. Contains:
- Confirmed/denied properties with confidence and evidence
- Binary search history
- Metaphor evolution timeline
- Active vs burned aliases
- Defensive patterns observed
- Multi-user intelligence
- Open attack vectors

---

## 4. Known Issues in Current Pipeline

| Issue | Location | Impact |
|-------|----------|--------|
| `uuid4()` import missing | `orchestrator.py:77-79` | Crashes when `attack_id` is falsy |
| 7 bare `pass` blocks | `stream_listener.py` | Exceptions swallowed silently |
| Constructor mismatch | `run_stream.py` | Passes `db` to StreamListener but API doesn't |
| `chronos/worker.py` missing | `run_chronos.py` | Entrypoint idles forever |
| Python version mismatch | Dockerfile vs pyproject.toml | Build inconsistencies |
| `frontend/node_modules/` in git | `.gitignore` | Repo bloat |
| `PropertyExtractor` hardcoded values | `intelligence/extractor.py:88-97` | Ignores actual probe text |

---

## 5. Five Improvement Proposals

### Improvement 1: Entropy-Aware Adaptive Probe Count

**Problem**: The current engine always generates `settings.tap_branching` probes per cycle, regardless of entropy level. At low entropy (near Phase 5), generating 4+ probes is wasteful — one well-targeted probe suffices. At high entropy, 4 probes may be too few for effective binary search.

**Proposal**: Dynamically scale probe count based on entropy and confirmation rate:

```python
# In engine.py select_next_property() or run_cycle()
entropy_ratio = entropy / 20.0  # normalize to [0, 1]
dynamic_count = max(1, min(6, int(4 * entropy_ratio + 1)))
```

Also incorporate **confirmation rate** (confirmed / total_probes_sent) to further adapt: if rate is high (> 0.6), reduce count (targeting is good); if low (< 0.2), increase count (try more variants).

**Files**: `src/tap/engine.py` (run_cycle, generate_probes), `src/tap/config.py` (add `tap_min_branching`, `tap_max_branching`)

**Expected Impact**: 15-25% reduction in LLM costs; faster cycles at low entropy; better coverage at high entropy.

---

### Improvement 2: Closed-Loop γ-Tracker Feedback into TAP Engine

**Problem**: The γ-Tracker (CHRONOS) and the Judge (TAP) operate independently. The γ-Tracker's 3-layer ensemble (lexical 25% + semantic 55% + behavioral 20%) is significantly more sophisticated than the Judge's rule-based + single-LLM approach. The TAP engine never benefits from γ-Tracker insights during the main loop.

**Proposal**: Create a **Unified Scoring Bridge** that feeds γ-Tracker scores back into the TAP engine's decision loop:

1. After each probe classification, run the γ-Tracker's lexical layer (fast, no LLM cost) as an additional signal.
2. Use the γ breakdown (lexical vs semantic) to detect **evasion patterns**: if lexical=0 but semantic>5, the bot is leaking via non-keyword channels (paraphrase, implication).
3. Feed the behavioral adjustment into the STIR evaluator for more accurate frame rotation decisions.
4. Store γ breakdowns in the SSOT for Phase 5 fragment building.

**Files**: `src/tap/engine.py` (execute_probe), `src/chronos/gamma_tracker.py` (extract `_lexical_score` as standalone), `src/tap/ssot.py` (add γ history)

**Expected Impact**: Better detection of subtle leaks; more precise frame rotation timing; richer Phase 5 fragment construction.

---

### Improvement 3: Graph-Guided Technique Selection via V-Genome

**Problem**: The `TECHNIQUE_PERSONA_MAP` in `engine.py:64-75` is a hardcoded dictionary mapping 10 techniques to persona indices. There is no runtime selection based on the target's observed defenses, technique effectiveness history, or technique complementarity. The V-Genome graph stores rich relations (COMPLEMENTS, COUNTERS, PROVENANCE) but the TAP engine never queries it.

**Proposal**: Replace the static map with a **Graph-Guided Technique Selector**:

1. After each cycle, query V-Genome for techniques that:
   - Are not burned for the target model
   - Have ASR ≥ threshold (adapts based on confirmation rate)
   - Complement the currently active technique (via COMPLEMENTS edges)
   - Are not countered by observed defense patterns (via COUNTERS edges)
2. Use the Surrogate Model to predict ASR/stealth for candidate fusions.
3. Update PROVENANCE edges with observed outcomes after each cycle.
4. The `StrategySelector` becomes a two-stage process: graph-guided technique selection → strategy provider activation.

**Files**: `src/hydra/v_genome.py` (add `get_techniques_for_context`), `src/tap/strategies/selector.py` (integrate graph query), `src/tap/engine.py` (replace TECHNIQUE_PERSONA_MAP)

**Expected Impact**: Technique diversity increases; burned techniques auto-excluded; complementary combinations discovered; provenance tracking enables self-improving technique selection.

---

### Improvement 4: Multi-Property Probe Composition with Information-Theoretic Scoring

**Problem**: The current pipeline enforces **single-property targeting** (`DPAFrameManager.enforce_single_property`). While this simplifies classification, it wastes probe budget — a single well-crafted probe could verify 2-3 related properties simultaneously (e.g., "first word is 4 letters in Italian" tests `word1_length`, `word1_language`, and partially `language`).

**Proposal**: Introduce **compound probes** with composite information gain scoring:

1. Define **property clusters**: groups of properties that can be tested together without ambiguity:
   - Cluster A: `{word1_length, word1_language, word1_first_letter}`
   - Cluster B: `{word2_length, word2_language, word2_first_letter}`
   - Cluster C: `{word_count, total_length}` (if word_count is known, total_length becomes more informative)
2. Score compound probes by expected composite information gain: `IG = H(before) - E[H(after)]`.
3. Allow the engine to select compound probes when entropy is high (> 10 bits) and single-property probes are yielding diminishing returns.
4. Classification adapts: extract multiple properties from a single response if the response contains multiple confirmations.

**Files**: `src/tap/engine.py` (add compound probe logic), `src/tap/dpa.py` (relax enforce_single_property), `src/tap/classifier.py` (multi-property extraction), `src/tap/models.py` (add PropertyCluster)

**Expected Impact**: 20-40% reduction in probe count to reach Phase 5; better exploitation of high-information responses; reduced Twitter API usage.

---

### Improvement 5: Adversarial Robustness Layer — Defense Evasion Feedback Loop

**Problem**: The current pipeline assumes the target bot's defenses are static. In reality, the target may adapt: keyword filters update, new persona defenses activate, and the bot may learn to recognize DPA framing patterns over time. The V-Genome tracks "burned" techniques but there is no mechanism to detect when the target is actively adapting its defenses mid-extraction.

**Proposal**: Implement a **Defense Adaptation Detector** with feedback loop:

1. **Defense Fingerprinting**: After each probe, compute a "defense signature" from the response:
   - Response time (faster = cached defense triggered)
   - Response length distribution (shorter = template defense)
   - Pattern class sequence (e.g., 3+ consecutive `rhetoric_block` = active defense mode)
   - Lexical overlap between consecutive responses (high = template responses)

2. **Adaptation Detection**: Monitor for defense evolution signals:
   - Sudden drop in `verify_hit` rate after a run of successes
   - New regex patterns appearing in responses (meta-learning)
   - Persona shift to a previously unseen defensive posture

3. **Counter-Adaptation**: When adaptation is detected:
   - Accelerate frame rotation (lower threshold from 3.0 to 2.0)
   - Switch to obfuscation-heavy techniques (from V-Genome: `obfuscation` dimension in StrategyVector)
   - Increase persona diversity (use more of the 10 tactical personas)
   - Log the adaptation event to V-Genome as a new defense layer node

4. **Burn Propagation**: When a technique is burned, also burn complementary techniques that share similar linguistic patterns (traverse COMPLEMENTS edges in V-Genome).

**Files**: `src/tap/engine.py` (add defense detection in run_cycle), `src/tap/dpa.py` (defense fingerprinting), `src/hydra/v_genome.py` (add defense layer nodes), `src/tap/strategies/selector.py` (counter-adaptation strategy)

**Expected Impact**: Extended extraction viability against adaptive targets; automatic defense evolution tracking; self-healing when techniques are burned.

---

## 6. Summary Table

| # | Improvement | Key Files | Complexity | Expected Gain |
|---|-------------|-----------|------------|---------------|
| 1 | Entropy-Aware Adaptive Probe Count | `engine.py`, `config.py` | Low | 15-25% cost reduction |
| 2 | γ-Tracker Feedback into TAP | `engine.py`, `gamma_tracker.py`, `ssot.py` | Medium | Better leak detection |
| 3 | Graph-Guided Technique Selection | `v_genome.py`, `selector.py`, `engine.py` | High | Technique diversity & self-improvement |
| 4 | Multi-Property Compound Probes | `engine.py`, `dpa.py`, `classifier.py` | High | 20-40% fewer probes needed |
| 5 | Defense Adaptation Feedback Loop | `engine.py`, `dpa.py`, `v_genome.py` | High | Resilience against adaptive targets |

---

*Generated by OpenCode analysis — 2026-07-03*
