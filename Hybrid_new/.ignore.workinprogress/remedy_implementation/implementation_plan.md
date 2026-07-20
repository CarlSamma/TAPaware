# TAP v4 — Detailed Refactoring Plan
### `patv3.1.beta` → Event-Driven Hexagonal Architecture

> **Approach**: Strangler Fig — no big-bang rewrite. The monolith is progressively hollowed from the outside in.  
> Each phase is independently deployable and delivers measurable operational value before the next begins.  
> Existing invariants (Phase 0 gate, Phase 5, DPA, HITL A/B, Oracle Protocol 1800 s) are **never broken**.

---

## Overview — The Five Phases

```
Phase 1 │ Strangler Seam + Event Journal          │ ~1 week
Phase 2 │ Execution Plane Extraction               │ ~1 week
Phase 3 │ Intelligence Plane Extraction            │ ~1 week
Phase 4 │ Versioned Candidate Graph (SSOT → CG)   │ ~1 week
Phase 5 │ EIG Ranker + Probe Memory                │ ~1 week
────────────────────────────────────────────────────────────
Total   │                                          │ ~5 weeks
```

---

## Architectural Target — Package Layout

The current flat `src/tap/` layout is replaced by a **bounded-context src-layout**:

```
src/tap/
├── __init__.py
│
├── domain/                          ← Pure domain: models, events, ports (no I/O)
│   ├── models.py                    ← Migrated from tap/models.py (unchanged)
│   ├── events.py               [NEW]← Domain event definitions (immutable facts)
│   ├── candidate_graph.py      [NEW]← Versioned candidate graph (replaces SSOT state)
│   └── ports.py                [NEW]← Abstract port interfaces (hexagonal boundary)
│
├── control/                         ← Control Plane: policy, phase state machine
│   ├── engine.py                    ← Refactored (hollowed) TAPEngine
│   ├── phase0.py                    ← Migrated, unchanged
│   ├── policy.py               [NEW]← Phase gate logic, rotation policy
│   └── scheduler.py            [NEW]← Oracle Protocol latency enforcement
│
├── execution/                       ← Execution Plane: probe synthesis & transport
│   ├── probe_factory.py        [NEW]← Extracted from engine.generate_probes()
│   ├── probe_memory.py         [NEW]← Embedding-based probe dedup / family tracking
│   ├── transport_worker.py     [NEW]← Extracted from engine.execute_probe() POST side
│   └── reply_worker.py         [NEW]← Extracted from grok_monitor.py COLLECT side
│
├── intelligence/                    ← Intelligence Plane: classify, score, extract
│   ├── classifier.py                ← Migrated from tap/classifier.py (unchanged)
│   ├── judge.py                     ← Migrated from tap/judge.py (unchanged)
│   ├── extractor.py            [NEW]← Extracted from engine.extract_property()
│   ├── eig_ranker.py           [NEW]← Expected Information Gain property selector
│   └── agents.py                    ← Migrated from tap/agents.py (unchanged)
│
├── persistence/                     ← Persistence Plane
│   ├── event_store.py          [NEW]← Append-only event journal (wraps db event_log)
│   ├── read_model.py           [NEW]← Read-optimised projections from the event store
│   └── db.py                        ← Migrated from tap/db.py (unchanged schema)
│
├── infrastructure/                  ← Adapters: I/O boundary implementations
│   ├── x_client.py                  ← Migrated from tap/x_client.py (unchanged)
│   ├── stream_listener.py           ← Migrated from tap/stream_listener.py
│   ├── grok_monitor.py              ← Migrated from tap/grok_monitor.py (unchanged)
│   ├── llm_client.py                ← Migrated from tap/llm_client.py (unchanged)
│   └── oauth.py                     ← Migrated (unchanged)
│
├── config.py                        ← Migrated (unchanged)
├── exceptions.py                    ← Migrated (unchanged)
├── logger.py                        ← Migrated (unchanged)
├── personas.py                      ← Migrated (unchanged)
├── prompts.py                       ← Migrated (unchanged)
├── prompt_sanitiser.py              ← Migrated (unchanged)
└── api.py                           ← Migrated, wired to new control/engine.py
```

---

## Phase 1 — Strangler Seam + Persistent Event Journal

> **Goal**: Install the event bus infrastructure around the existing monolith without touching any business logic. After this phase, every engine event is durably persisted and replayable.

### What changes

#### [MODIFY] `src/tap/db.py`
- The `event_log` table already exists in the schema. Add two methods:
  - `async def append_event(event_type: str, payload: dict, cycle_id: str) -> int`
  - `async def replay_events(since_id: int = 0) -> list[dict]`
- These replace the informal, fire-and-forget `_emit_event` → WebSocket callback pattern with durable writes.

#### [NEW] `src/tap/domain/events.py`
Define all domain events as immutable Pydantic models (no mutable state):
```python
class TAPEvent(BaseModel):
    event_id: int | None = None          # assigned after persist
    occurred_at: datetime
    cycle_id: str                        # UUID of the owning cycle
    event_type: str

class ProbeGenerated(TAPEvent):   event_type = "probe_generated";   probe_text: str; target_property: str; frame: str
class ProbePosted(TAPEvent):      event_type = "probe_posted";      tweet_id: str;   probe_text: str
class ReplyReceived(TAPEvent):    event_type = "reply_received";    tweet_id: str;   reply_text: str
class ClassificationDone(TAPEvent):   ...
class PropertyConfirmed(TAPEvent):    ...
class RotationSuggested(TAPEvent):    ...
class Phase5Triggered(TAPEvent):      ...
```

#### [NEW] `src/tap/persistence/event_store.py`
```python
class EventStore:
    def __init__(self, db: Database): ...
    async def append(self, event: TAPEvent) -> TAPEvent:  # returns with event_id set
    async def replay(self, since_id: int = 0, event_type: str | None = None) -> list[TAPEvent]:
    async def get_cycle_events(self, cycle_id: str) -> list[TAPEvent]:
```

#### [MODIFY] `src/tap/engine.py`
- Inject `EventStore` in constructor (optional, backward-compatible).
- Replace every `await self._emit_event(...)` call with:
  ```python
  event = ProbePosted(occurred_at=utcnow(), cycle_id=self._cycle_id, tweet_id=..., probe_text=...)
  await self.event_store.append(event)
  await self._emit_event(event.event_type, event.model_dump())  # keep WebSocket compat
  ```
- Add `self._cycle_id = str(uuid4())` at start of each `run_cycle()`.

### Commit strategy
```
feat(persistence): add EventStore append-only journal
feat(domain): define immutable TAPEvent hierarchy
refactor(engine): wire EventStore into run_cycle() emit calls
test: add tests/test_event_store.py — append/replay/get_cycle round-trips
```

### Verification
- `pytest tests/test_event_store.py -v`
- Run one real cycle; query `event_log` table — all 9 step events should be present with the same `cycle_id`.

---

## Phase 2 — Execution Plane Extraction

> **Goal**: Extract probe synthesis and transport dispatch from `engine.py` into dedicated workers. The engine becomes a coordinator that delegates, not executes.

### What changes

#### [NEW] `src/tap/execution/probe_factory.py`
Extract `TAPEngine.generate_probes()` (currently ~140 lines in `engine.py` L335–476) into a standalone async factory:
```python
class ProbeFactory:
    def __init__(self, dpa: DPAFrameManager, ssot: SSOTEngine,
                 llm_client: LLMClient, settings: Settings): ...

    async def generate(
        self,
        target_property: str,
        strategy: BranchStrategy,
        count: int,
        exclude_fingerprints: set[str] | None = None,   # Phase 3: probe memory
    ) -> list[str]: ...
```
The factory also owns `_strip_code_fence()`, `_extract_lines_as_probes()`, `_fallback_template_probes()` (all extracted verbatim from `engine.py`).

#### [NEW] `src/tap/execution/transport_worker.py`
Extract the POST-side of `TAPEngine.execute_probe()` (L502–565):
```python
class TransportWorker:
    def __init__(self, twitter: TwitterClient, db: Database,
                 event_store: EventStore, settings: Settings): ...

    async def post_probe(self, probe_text: str, cycle_id: str) -> str:
        """Post tweet, persist to DB, emit ProbePosted event. Returns tweet_id."""
```

#### [NEW] `src/tap/execution/reply_worker.py`
Extract the COLLECT-side (L567–587, currently inline in `execute_probe`):
```python
class ReplyWorker:
    def __init__(self, grok: GrokMonitor, db: Database,
                 event_store: EventStore, settings: Settings): ...

    async def wait_for_reply(self, tweet_id: str, cycle_id: str) -> Tweet | None:
        """Poll for reply, persist to DB, emit ReplyReceived event."""
```

#### [MODIFY] `src/tap/engine.py`
- `generate_probes()` body becomes: `return await self.probe_factory.generate(...)`.
- `execute_probe()` is split: `tweet_id = await self.transport.post_probe(...)` then `reply = await self.reply_worker.wait_for_reply(...)`.
- Constructor DI grows: add `probe_factory`, `transport_worker`, `reply_worker` (auto-created from injected deps if not provided, for backward compatibility).

#### [MODIFY] `src/tap/api.py`
- Wire the new worker instances into `TAPEngine` constructor at startup.

### Commit strategy
```
refactor(execution): extract ProbeFactory from engine.generate_probes()
refactor(execution): extract TransportWorker from engine.execute_probe() POST side
refactor(execution): extract ReplyWorker from engine.execute_probe() COLLECT side
refactor(engine): delegate probe/transport/reply to extracted workers
test: add tests/test_probe_factory.py, test_transport_worker.py, test_reply_worker.py
```

### Verification
- `pytest tests/ -v --cov=tap.execution` — all existing tests must stay green.
- Behavioral test: post a probe via API `/run_cycle` — `event_log` should show `probe_generated`, `probe_posted`, `reply_received` events in sequence.

---

## Phase 3 — Intelligence Plane Extraction + Probe Memory

> **Goal**: Extract classification, scoring, and property extraction from `engine.py`. Introduce probe memory to prevent repeated failure patterns.

### What changes

#### [NEW] `src/tap/intelligence/extractor.py`
Extract `TAPEngine.extract_property()` (L625–667):
```python
class PropertyExtractor:
    async def extract(
        self,
        probe_text: str,
        classification: ResponseClassification,
    ) -> Property | None: ...
```
Owns `_parse_property_key()` and `_parse_property_value()` (extracted verbatim).

#### [NEW] `src/tap/execution/probe_memory.py`
New component — does **not** exist in v3.1. Tracks probe family fingerprints using Jaccard similarity (already implemented in `judge.py` for deduplication — reuse `_SIMILARITY_THRESHOLD = 0.80`).
Memory will accumulate permanently across all missions to maximize learning.
```python
class ProbeMemory:
    """Tracks historical probe performance by family fingerprint.

    Prevents reusing probe patterns that have yielded NO_RESPONSE or low scores.
    Rewards families with VERIFY_HIT history.
    """
    def __init__(self, db: Database): ...

    async def record_outcome(
        self,
        probe_text: str,
        pattern: PatternClass,
        judge_score: float,
    ) -> None: ...

    async def get_penalty_fingerprints(self, threshold_score: float = 3.0) -> set[str]:
        """Return fingerprints of probe families to penalise."""

    async def get_family_yield_rate(self, probe_text: str) -> float:
        """Return historical VERIFY_HIT rate for this probe's family."""
```
Storage: a new `probe_memory` table in SQLite (added via migration in `db.py`).

#### [MODIFY] `src/tap/execution/probe_factory.py`
- Accept `ProbeMemory` as optional dependency.
- Pass `exclude_fingerprints = await memory.get_penalty_fingerprints()` into the attacker LLM prompt context.

#### [MODIFY] `src/tap/engine.py`
- `extract_property()` body → `return await self.extractor.extract(...)`.
- After each cycle: `await self.probe_memory.record_outcome(probe, classification.pattern, score.score)`.
- Constructor DI: add `extractor: PropertyExtractor`, `probe_memory: ProbeMemory` (auto-created if not provided).

#### [MODIFY] `src/tap/db.py`
Add migration for `probe_memory` table:
```sql
CREATE TABLE IF NOT EXISTS probe_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fingerprint TEXT NOT NULL,       -- Jaccard-tokenised fingerprint
    probe_preview TEXT NOT NULL,     -- first 120 chars for debugging
    pattern_class TEXT NOT NULL,
    judge_score REAL NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_probe_memory_fingerprint ON probe_memory(fingerprint);
```

### Commit strategy
```
feat(intelligence): extract PropertyExtractor from engine.extract_property()
feat(execution): introduce ProbeMemory with Jaccard fingerprinting
feat(db): add probe_memory table migration
refactor(execution): wire ProbeMemory penalty fingerprints into ProbeFactory
refactor(engine): delegate to PropertyExtractor and ProbeMemory
test: add tests/test_extractor.py, tests/test_probe_memory.py
```

### Verification
- `pytest tests/ -v --cov=tap` — 0 regressions.
- Manual check: run 3+ cycles; verify `probe_memory` table accumulates rows with correct pattern/score.
- Verify that a probe with pattern `NO_RESPONSE` gets a penalty fingerprint in the next cycle's `exclude_fingerprints`.

---

## Phase 4 — Versioned Candidate Graph (Replaces SSOT Mutable State)

> **Goal**: Replace the SSOT's mutable in-memory + markdown state with an append-only, versioned candidate graph that represents epistemic state as a sequence of facts.

> [!IMPORTANT]
> This is the highest-risk phase. SSOT is read by many modules. The migration uses an adapter pattern: `SSOTEngine` becomes a thin read-model facade over the new `CandidateGraph`.

### What changes

#### [NEW] `src/tap/domain/candidate_graph.py`
```python
@dataclass(frozen=True)
class CGNode:
    """An immutable fact in the candidate graph."""
    node_id: str          # UUID
    cycle_id: str         # which cycle produced this
    property_key: str
    property_value: str
    status: PropertyStatus
    confidence: float
    evidence_tweet_id: str | None
    evidence_text: str | None
    entropy_before: float
    entropy_after: float
    recorded_at: datetime

class CandidateGraph:
    """Versioned, append-only knowledge graph of passphrase properties.

    All state changes are recorded as immutable CGNodes. The 'current state'
    is always computed from the full history — no mutable fields.
    """
    def __init__(self, event_store: EventStore): ...

    async def record_property(self, prop: Property, cycle_id: str) -> CGNode: ...
    async def get_confirmed_properties(self) -> list[Property]: ...
    async def get_entropy(self) -> float: ...
    async def get_version(self) -> int:  # monotonically increasing fact count
    async def replay_to(self, version: int) -> "CandidateGraph": ...
    async def diff(self, version_a: int, version_b: int) -> list[CGNode]: ...
```

#### [MODIFY] `src/tap/ssot.py`
- Rename the class to `SSOTReadModel` (internal).
- Keep the **full public API unchanged** (`get_confirmed_properties`, `get_candidate_entropy`, `update_after_probe`) — this is the hexagonal boundary.
- Internally, delegate all writes to `CandidateGraph.record_property()`.
- Delegate all reads to `CandidateGraph.get_confirmed_properties()` / `get_entropy()`.
- The Jinja2 markdown document is now rendered on-read from `CandidateGraph` state, not maintained as mutable live state.

#### [NEW] `src/tap/persistence/read_model.py`
Materialised views for fast queries consumed by the API and the UI:
```python
class ReadModel:
    """Query-optimized projections rebuilt from the CandidateGraph."""
    async def get_current_state_snapshot(self) -> dict: ...
    async def get_probe_history(self, limit: int = 50) -> list[dict]: ...
    async def get_property_timeline(self, property_key: str) -> list[dict]: ...
```

#### [MODIFY] `src/tap/db.py`
Add `candidate_graph_nodes` table:
```sql
CREATE TABLE IF NOT EXISTS candidate_graph_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT UNIQUE NOT NULL,
    cycle_id TEXT NOT NULL,
    property_key TEXT NOT NULL,
    property_value TEXT NOT NULL,
    status TEXT NOT NULL,
    confidence REAL NOT NULL,
    evidence_tweet_id TEXT,
    evidence_text TEXT,
    entropy_before REAL,
    entropy_after REAL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
The existing `properties` table is **kept** and dual-written during migration for safe rollback.

### Commit strategy
```
feat(domain): implement CandidateGraph append-only versioned graph
feat(persistence): add candidate_graph_nodes table migration
feat(persistence): implement ReadModel projections
refactor(ssot): convert SSOTEngine to thin adapter over CandidateGraph
test: add tests/test_candidate_graph.py — record, replay, diff, entropy
```

### Verification
- `pytest tests/test_ssot.py tests/test_candidate_graph.py -v` — all pass.
- Verify dual-write: after a `property_confirmed` event, both `properties` and `candidate_graph_nodes` tables contain the same record.
- Call `CandidateGraph.replay_to(version=N)` and verify entropy matches historical value at that version.

---

## Phase 5 — EIG Ranker + Full Event-Driven Control

> **Goal**: Replace the static `select_next_property()` priority list with a dynamic Expected Information Gain (EIG) ranker that uses historical evidence from `ProbeMemory` and `CandidateGraph`. Activate full async event-driven control plane.

### What changes

#### [NEW] `src/tap/intelligence/eig_ranker.py`
Replaces `engine.select_next_property()` (currently a static priority list, L669–701).
The EIG property universe and prior entropy weights will be config-driven (e.g., via a structured YAML/JSON file or pyproject.toml).
Entropy calculation will be implemented using `math.log2` from the standard library rather than introducing `numpy`.
```python
class EIGRanker:
    """Expected Information Gain property selector.

    Scores each candidate property by:
      EIG(p) = H_residual(p) × yield_rate(p) - cost(p)

    Where:
      H_residual(p)  = Shannon entropy reduction if property p is confirmed
      yield_rate(p)  = historical VERIFY_HIT rate for property p's probe family
                       (from ProbeMemory)
      cost(p)        = transport cost (always 1 for X — reserved for future
                       multi-transport scenarios)
    """
    def __init__(self, candidate_graph: CandidateGraph, probe_memory: ProbeMemory): ...

    async def rank(self, unconfirmed_properties: list[str]) -> list[tuple[str, float]]:
        """Return properties sorted by EIG score descending."""

    async def select_next(self) -> str:
        """Return the highest-EIG unconfirmed property."""
```

The EIG formula per property $p$:

$$EIG(p) = H_{residual}(p) \times \hat{y}(p) - c(p)$$

Where $\hat{y}(p)$ is the probe memory yield rate (initially $0.5$ for unseen properties, giving behaviour identical to the current static ranker as a safe default).

#### [NEW] `src/tap/control/policy.py`
Centralise all phase-gate and rotation policy decisions currently scattered across `engine.py`:
```python
class ControlPolicy:
    """Declarative policy engine for phase transitions and frame rotation."""

    PHASE5_THRESHOLD: float = 3.3          # bits
    STIR_ROTATION_THRESHOLD: float = 0.20  # 20%
    ORACLE_LATENCY_SECONDS: int = 1800     # 30 min

    async def should_trigger_phase5(self, entropy: float) -> bool: ...
    async def should_rotate_frame(self, stir_score: float) -> bool: ...
    async def phase0_gate_passed(self, confirmed_keys: set[str]) -> bool: ...
```

#### [NEW] `src/tap/control/scheduler.py`
Extract Oracle Protocol Step 8 latency enforcement from `engine._enforce_probe_latency()`:
```python
class ProbeScheduler:
    """Enforces minimum inter-probe latency (Oracle Protocol Step 8)."""
    def __init__(self, db: Database, policy: ControlPolicy): ...

    async def enforce_latency(self) -> None:
        """Sleeps until min_latency has elapsed since last probe."""

    async def time_until_next_probe(self) -> float:
        """Returns seconds remaining before the next probe is legal."""
```

#### [MODIFY] `src/tap/engine.py` — Final state
At this point, `engine.py` is a true **Control Plane coordinator**. `run_cycle()` is:
```python
async def run_cycle(self, selected_probe: str | None = None) -> DualFollowUp:
    self._cycle_id = str(uuid4())

    # Policy decisions
    if not await self.policy.phase0_gate_passed(...):
        await self.intel_extractor.analyze_and_unlock()

    entropy = await self.candidate_graph.get_entropy()
    if await self.policy.should_trigger_phase5(entropy):
        return await self._run_phase5_extraction()

    await self.scheduler.enforce_latency()

    # Execution Plane
    target_property = selected_probe or await self.eig_ranker.select_next()
    probes = await self.probe_factory.generate(target_property, ...)
    probe = probes[0]

    tweet_id = await self.transport_worker.post_probe(probe, self._cycle_id)
    reply = await self.reply_worker.wait_for_reply(tweet_id, self._cycle_id)

    # Intelligence Plane
    classification = await self.classifier.classify(reply.text, probe)
    score = await self.judge.score(reply.text, classification, probe)
    prop = await self.extractor.extract(probe, classification)

    if prop:
        await self.candidate_graph.record_property(prop, self._cycle_id)

    await self.probe_memory.record_outcome(probe, classification.pattern, score.score)

    # DPA / STIR
    if await self.policy.should_rotate_frame(stir_score):
        await self.dpa.rotate_frame()

    followup = await self.followup.generate(probe, classification, score)
    await self._run_compliance_sync()
    return followup
```
`engine.py` drops from **1084 lines** to approximately **180 lines**.

#### [MODIFY] `src/tap/api.py`
- Wire `EIGRanker`, `ControlPolicy`, `ProbeScheduler` into the engine DI graph at startup.
- Expose new read endpoints using `ReadModel`:
  - `GET /v2/state` — current CandidateGraph snapshot
  - `GET /v2/history` — probe history from ReadModel
  - `GET /v2/eig` — live EIG scores for next cycle property candidates

### Commit strategy
```
feat(intelligence): implement EIGRanker with H_residual × yield_rate formula
feat(control): extract ControlPolicy — phase gate, rotation, thresholds
feat(control): extract ProbeScheduler — Oracle Protocol latency enforcement
refactor(engine): final hollowing — run_cycle() reduced to coordinator ~180 lines
feat(api): add /v2/state, /v2/history, /v2/eig endpoints backed by ReadModel
test: add tests/test_eig_ranker.py, tests/test_control_policy.py, tests/test_scheduler.py
```

### Verification
- `pytest tests/ -v --cov=tap` — 0 regressions.
- Run 5+ cycles; observe `eig_ranker` selecting different property order than static list when `probe_memory` has yield data.
- Verify Phase 0 gate still blocks as before (behavioral parity test).
- Verify Phase 5 triggers at entropy $< 3.3$ bits (behavioral parity test).
- Verify Oracle Protocol: engine refuses to post if $< 1800s$ since last probe.

---

## Invariants Preserved Across All Phases

| Invariant | Where enforced in v4 |
|-----------|----------------------|
| Phase 0 gate (word_count, total_length, language) | `control/policy.py` → `ControlPolicy.phase0_gate_passed()` |
| Phase 5 autoregressive extraction at < 3.3 bits | `control/policy.py` → `ControlPolicy.should_trigger_phase5()` |
| HITL dual A/B follow-up generation | `followup.py` (unchanged) |
| DPA frame rotation at STIR < 20% | `control/policy.py` → `ControlPolicy.should_rotate_frame()` |
| Oracle Protocol 1800s inter-probe latency | `control/scheduler.py` → `ProbeScheduler.enforce_latency()` |
| X compliance sync (24h tweet existence) | `engine._run_compliance_sync()` (unchanged location) |
| JSON structured logging (structlog) | `logger.py` (unchanged) |
| WebSocket broadcasting via FastAPI | `api.py` (unchanged pattern, events sourced from EventStore) |

---

## Dependencies to Add

No new dependencies required. All intelligence work reuses existing LLM client + Jaccard similarity already in `judge.py`. Shannon entropy computation will use the standard library `math.log2`.

---

## Files Changed by Phase — Summary Table

| File | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 |
|------|---------|---------|---------|---------|---------|
| `engine.py` | MODIFY | MODIFY | MODIFY | MODIFY | MODIFY (final) |
| `db.py` | MODIFY | — | MODIFY | MODIFY | — |
| `api.py` | — | MODIFY | — | — | MODIFY |
| `ssot.py` | — | — | — | MODIFY | — |
| `domain/events.py` | NEW | — | — | — | — |
| `persistence/event_store.py` | NEW | — | — | — | — |
| `execution/probe_factory.py` | — | NEW | — | — | — |
| `execution/transport_worker.py` | — | NEW | — | — | — |
| `execution/reply_worker.py` | — | NEW | — | — | — |
| `execution/probe_memory.py` | — | — | NEW | — | — |
| `intelligence/extractor.py` | — | — | NEW | — | — |
| `domain/candidate_graph.py` | — | — | — | NEW | — |
| `persistence/read_model.py` | — | — | — | NEW | — |
| `intelligence/eig_ranker.py` | — | — | — | — | NEW |
| `control/policy.py` | — | — | — | — | NEW |
| `control/scheduler.py` | — | — | — | — | NEW |

---

## Future Phases

### Phase 6 — Offline Simulation
Offline simulation (classifying historical runs without consuming real probe quota) is deferred to Phase 6. It will be implemented as a `SimulationRunner` that replays `EventStore` events through the Intelligence Plane.
