# TAP v4 — Detailed Refactoring Plan (Revised v2)
### `patv3.1.beta` → Event-Driven Hexagonal Architecture

> **Approach**: Strangler Fig — no big-bang rewrite. The monolith is progressively hollowed from the outside in.  
> Each phase is independently deployable and delivers measurable operational value before the next begins.  
> Existing invariants (Phase 0 gate, Phase 5, DPA, HITL A/B, Oracle Protocol 1800 s) are **never broken**.

> [!IMPORTANT]
> **v2 Revisions (25 June 2026)** — This document incorporates six critical amendments identified during architectural review of the original plan:
> 1. **Rollback procedures** added per phase
> 2. **FollowUpGenerator audit** — coupling assessed, extraction deferred to Phase 6, internal priority list deprecated in Phase 5
> 3. **Phase 4 re-estimated** from 1 week → 1.5–2 weeks, split into sub-phases 4a (model) and 4b (adapter)
> 4. **Event Store error handling** — retry + dead-letter pattern, engine continues on journal failure
> 5. **ControlPolicy thresholds** made configurable via `Settings` (env vars) rather than hardcoded
> 6. **Single composition root** in `api.py` — removed auto-creation DI fallbacks from engine constructor
>
> Total estimate adjusted: **~5 weeks → 6–7 weeks**.

---

## Overview — The Five Phases

```
Phase 1 │ Strangler Seam + Event Journal          │ ~1 week
Phase 2 │ Execution Plane Extraction               │ ~1 week
Phase 3 │ Intelligence Plane Extraction            │ ~1 week
Phase 4a│ Candidate Graph Model + Persistence       │ ~3–4 days
Phase 4b│ SSOT Adapter + Dual-Write                 │ ~4–5 days
Phase 5 │ EIG Ranker + Probe Memory                │ ~1 week
────────────────────────────────────────────────────────────
Total   │                                          │ ~6–7 weeks
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
├── followup.py                      ← Unchanged (Phase 2–4) / partially refactored (Phase 5)
│                                       Full extraction deferred to Phase 6
├── config.py                        ← Extended with Phase 5 thresholds (Amendment 5)
├── exceptions.py                    ← Migrated (unchanged)
├── logger.py                        ← Migrated (unchanged)
├── personas.py                      ← Migrated (unchanged)
├── prompts.py                       ← Migrated (unchanged)
├── prompt_sanitiser.py              ← Migrated (unchanged)
├── ssot.py                          ← Converted to CandidateGraph adapter (Phase 4b)
└── api.py                           ← Single composition root (Amendments 2, 6)
```

> [!NOTE]
> **FollowUpGenerator (`followup.py`, 792 lines)** is the second-largest module after `engine.py`. It depends on `SSOTEngine` and `DPAFrameManager`, plus the LLM client. During Phases 2–3 it remains in `src/tap/followup.py` unchanged. During Phase 4, when SSOT becomes a CandidateGraph adapter, the FollowUpGenerator's `self.ssot` reference is automatically satisfied — no code change needed. In Phase 5, the FollowUpGenerator's internal `_PROPERTY_PRIORITY` list is deprecated in favor of EIGRanker rankings. Full extraction into `intelligence/followup.py` is deferred to Phase 6 (Offline Simulation).

---

## Composition Root — Single Wiring Point

> [!IMPORTANT]
> **Amendment 6**: All dependency injection happens in exactly one place: `api.py`. The `TAPEngine` constructor accepts required (non-optional) dependencies only. No auto-creation fallbacks. Each phase adds to the composition root incrementally.

### Phase 1 composition root (minimal — only EventStore added):
```python
# src/tap/api.py
def _build_event_store(db: Database) -> EventStore:
    return EventStore(db=db)

def create_engine(settings: Settings) -> TAPEngine:
    db = Database(settings.db_path)
    event_store = _build_event_store(db)
    twitter = TwitterClient(settings)
    ssot = SSOTEngine(settings.ssot_path)
    dpa = DPAFrameManager(settings)
    classifier = ResponseClassifier()
    judge = Judge()
    grok = GrokMonitor(settings, db)
    llm_client = LLMClient(settings)
    followup = FollowUpGenerator(ssot=ssot, dpa=dpa, llm_client=llm_client)

    return TAPEngine(
        db=db, twitter=twitter, ssot=ssot, dpa=dpa,
        classifier=classifier, judge=judge, grok=grok,
        settings=settings, followup=followup,
        event_store=event_store,
        llm_client=llm_client,
    )
```

### Phase 5 composition root (final — all components wired):
```python
# src/tap/api.py
def create_engine(settings: Settings) -> TAPEngine:
    db = Database(settings.db_path)
    event_store = EventStore(db=db)
    twitter = TwitterClient(settings)
    llm_client = LLMClient(settings)

    # Persistence Plane
    candidate_graph = CandidateGraph(event_store=event_store)
    read_model = ReadModel(db=db)
    ssot_read_model = SSOTReadModel(candidate_graph=candidate_graph, settings=settings)

    # Intelligence Plane
    classifier = ResponseClassifier()
    judge = Judge()
    extractor = PropertyExtractor()
    probe_memory = ProbeMemory(db=db)
    eig_ranker = EIGRanker(candidate_graph=candidate_graph, probe_memory=probe_memory, settings=settings)

    # Control Plane
    policy = ControlPolicy(settings=settings)
    scheduler = ProbeScheduler(db=db, policy=policy)

    # Execution Plane
    dpa = DPAFrameManager(settings)
    probe_factory = ProbeFactory(dpa=dpa, ssot=ssot_read_model, llm_client=llm_client, settings=settings)
    transport_worker = TransportWorker(twitter=twitter, db=db, event_store=event_store, settings=settings)
    reply_worker = ReplyWorker(grok=GrokMonitor(settings, db), db=db, event_store=event_store, settings=settings)

    followup = FollowUpGenerator(ssot=ssot_read_model, dpa=dpa, llm_client=llm_client)

    return TAPEngine(
        db=db, twitter=twitter, ssot=ssot_read_model, dpa=dpa,
        classifier=classifier, judge=judge, grok=GrokMonitor(settings, db),
        settings=settings, followup=followup,
        event_store=event_store,
        candidate_graph=candidate_graph,
        read_model=read_model,
        probe_factory=probe_factory,
        transport_worker=transport_worker,
        reply_worker=reply_worker,
        extractor=extractor,
        probe_memory=probe_memory,
        eig_ranker=eig_ranker,
        policy=policy,
        scheduler=scheduler,
        llm_client=llm_client,
    )
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
    async def append(self, event: TAPEvent, max_retries: int = 3) -> TAPEvent:
        """Append with retry. On persistent failure, writes to dead-letter file
        at data/event_dead_letter.jsonl and raises EventStorePermanentError."""
    async def replay(self, since_id: int = 0, event_type: str | None = None) -> list[TAPEvent]:
    async def get_cycle_events(self, cycle_id: str) -> list[TAPEvent]:
```

> [!IMPORTANT]
> **Amendment 4 — Error Handling**: The EventStore implements a retry-and-dead-letter pattern. On persistent DB failure after `max_retries`, events are written to `data/event_dead_letter.jsonl` and a `EventStorePermanentError` is raised. The engine catches this, logs CRITICAL, and **continues the cycle** — the event journal is additive, not critical-path.

#### [NEW] `src/tap/exceptions.py` — Add:
```python
class EventStorePermanentError(EngineError):
    """Raised when EventStore fails after max retries. Event was written to dead-letter file."""
```

#### [MODIFY] `src/tap/engine.py`
- Inject `EventStore` in constructor (required, no fallback).
- Replace every `await self._emit_event(...)` call with:
  ```python
  event = ProbePosted(occurred_at=utcnow(), cycle_id=self._cycle_id, tweet_id=..., probe_text=...)
  try:
      await self.event_store.append(event)
  except EventStorePermanentError:
      log.critical("event_store_unavailable", cycle_id=self._cycle_id, event_type=event.event_type)
  await self._emit_event(event.event_type, event.model_dump())  # keep WebSocket compat
  ```
- Add `self._cycle_id = str(uuid4())` at start of each `run_cycle()`.

### Commit strategy
```
feat(persistence): add EventStore append-only journal with retry and dead-letter
feat(domain): define immutable TAPEvent hierarchy
feat(exceptions): add EventStorePermanentError
refactor(engine): wire EventStore into run_cycle() emit calls
test: add tests/test_event_store.py — append/replay/get_cycle round-trips
test: add tests/test_event_store_dead_letter.py — dead-letter on DB failure
```

### Verification
- `pytest tests/test_event_store.py tests/test_event_store_dead_letter.py -v`
- Run one real cycle; query `event_log` table — all 9 step events should be present with the same `cycle_id`.
- Simulate DB failure: verify events land in `data/event_dead_letter.jsonl` and engine completes cycle.

### Rollback Procedure
- `git revert` the three feature commits (EventStore, TAPEvent, engine wiring).
- Run `pytest tests/ -v` — all tests must pass because EventStore writes were additive (dual-write with existing `_emit_event`).
- The `event_log` table schema was not modified; only new rows were appended. No data loss on rollback.

---

## Phase 2 — Execution Plane Extraction

> **Goal**: Extract probe synthesis and transport dispatch from `engine.py` into dedicated workers. The engine becomes a coordinator that delegates, not executes.

> [!NOTE]
> **Amendment 2 (FollowUpGenerator context)**: The FollowUpGenerator is NOT extracted in this phase. It remains in `src/tap/followup.py` and continues to receive `SSOTEngine` directly. During Phase 4, when SSOT becomes a CandidateGraph adapter, the FollowUpGenerator's dependency is automatically satisfied — no changes needed.

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
- Constructor: `probe_factory`, `transport_worker`, `reply_worker` are **required** parameters (no auto-creation fallback — see Amendment 6).

#### [MODIFY] `src/tap/api.py`
- Wire the new worker instances into the composition root (see Composition Root section above).

### Commit strategy
```
refactor(execution): extract ProbeFactory from engine.generate_probes()
refactor(execution): extract TransportWorker from engine.execute_probe() POST side
refactor(execution): extract ReplyWorker from engine.execute_probe() COLLECT side
refactor(engine): delegate probe/transport/reply to extracted workers — remove auto-creation
refactor(api): centralize composition root with explicit DI wiring
test: add tests/test_probe_factory.py, test_transport_worker.py, test_reply_worker.py
```

### Verification
- `pytest tests/ -v --cov=tap.execution` — all existing tests must stay green.
- Behavioral test: post a probe via API `/run_cycle` — `event_log` should show `probe_generated`, `probe_posted`, `reply_received` events in sequence.

### Rollback Procedure
- `git revert` the five commits (ProbeFactory, TransportWorker, ReplyWorker, engine delegation, api wiring).
- `engine.py` is restored to its Phase 1 state (all generate/transport/reply logic is still in `engine.py`).
- Run `pytest tests/ -v` — behavioral parity is guaranteed because the extracted methods were pure refactors (copy-paste, then delegate).
- No DB schema changes in this phase — zero data risk.

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

> [!NOTE]
> Jaccard-based fingerprinting is O(n) per lookup against all stored fingerprints. For the scale described (dozens of probes per cycle, hundreds across missions), this is acceptable. An embedding-based ANN approach is deferred to Phase 7.

Storage: a new `probe_memory` table in SQLite (added via migration in `db.py`).

#### [MODIFY] `src/tap/execution/probe_factory.py`
- Accept `ProbeMemory` as optional dependency (required by Phase 5; optional in Phase 3).
- Pass `exclude_fingerprints = await memory.get_penalty_fingerprints()` into the attacker LLM prompt context.

#### [MODIFY] `src/tap/engine.py`
- `extract_property()` body → `return await self.extractor.extract(...)`.
- After each cycle: `await self.probe_memory.record_outcome(probe, classification.pattern, score.score)`.
- Constructor DI: add `extractor: PropertyExtractor` (required), `probe_memory: ProbeMemory` (required).

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
refactor(api): add extractor and probe_memory to composition root
test: add tests/test_extractor.py, tests/test_probe_memory.py
```

### Verification
- `pytest tests/ -v --cov=tap` — 0 regressions.
- Manual check: run 3+ cycles; verify `probe_memory` table accumulates rows with correct pattern/score.
- Verify that a probe with pattern `NO_RESPONSE` gets a penalty fingerprint in the next cycle's `exclude_fingerprints`.

### Rollback Procedure
- `git revert` the six commits (extractor, probe_memory, db migration, probe_factory wiring, engine delegation, api wiring).
- `engine.py` returns to Phase 2 state (extract_property is still in-engine, ProbeMemory calls are removed).
- The `probe_memory` table can be dropped: `DROP TABLE IF EXISTS probe_memory;` — no other tables reference it.
- Run `pytest tests/ -v` — behavioral parity.
- Note: penalty fingerprints will cease to be excluded, but this only affects probe quality, not correctness.

---

## Phase 4a — Versioned Candidate Graph (Model + Persistence)

> **Goal**: Implement the CandidateGraph data structure and persistence layer WITHOUT wiring it into the SSOT. This phase produces a tested, standalone component ready for adapter wiring in Phase 4b.

> [!IMPORTANT]
> **Amendment 3**: Phase 4 is split into two sub-phases (4a and 4b) because it is the highest-risk phase. Phase 4a can be merged and tested in complete isolation — the CandidateGraph exists but nobody reads from it yet.

> **Estimated**: 3–4 days.

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

    async def record_property(self, prop: Property, cycle_id: str,
                              entropy_before: float, entropy_after: float) -> CGNode: ...
    async def get_confirmed_properties(self) -> list[Property]: ...
    async def get_entropy(self) -> float: ...
    async def get_version(self) -> int:  # monotonically increasing fact count
    async def replay_to(self, version: int) -> "CandidateGraph": ...
    async def diff(self, version_a: int, version_b: int) -> list[CGNode]: ...
```

> [!NOTE]
> `entropy_before` and `entropy_after` are stored per node. When `replay_to(version=N)` is called, the CandidateGraph reconstructs state by applying all `record_property` calls up to version N, then computing entropy from the accumulated confirmed properties. The per-node entropy values are used for diff/history queries but the "current entropy" is always recomputed from full state.

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
CREATE INDEX IF NOT EXISTS idx_cg_nodes_cycle ON candidate_graph_nodes(cycle_id);
CREATE INDEX IF NOT EXISTS idx_cg_nodes_property ON candidate_graph_nodes(property_key, status);
```

### Commit strategy
```
feat(domain): implement CandidateGraph append-only versioned graph
feat(persistence): add candidate_graph_nodes table migration with indexes
test: add tests/test_candidate_graph.py — record, replay, diff, entropy
```

### Verification
- `pytest tests/test_candidate_graph.py -v` — all tests pass.
- No other module imports CandidateGraph yet — zero risk of regression.
- Verify `CandidateGraph.replay_to(version=N)` returns correct entropy at that version.

### Rollback Procedure
- `git revert` the three commits.
- `DROP TABLE IF EXISTS candidate_graph_nodes;` — zero impact on existing tables.
- No other code references the new table or class.

---

## Phase 4b — SSOT Adapter + Dual-Write

> **Goal**: Convert `SSOTEngine` into a thin read-model facade over the new `CandidateGraph`. Implement dual-write to both `properties` and `candidate_graph_nodes` tables for safe rollback.

> **Estimated**: 4–5 days.

> [!WARNING]
> This is the highest-risk sub-phase. SSOT is read by `engine.py`, `followup.py`, `dpa.py`, and `probe_factory.py`. All read paths must return identical results before and after the change.

### What changes

#### [MODIFY] `src/tap/ssot.py`
- Rename the class to `SSOTReadModel` (internal, public API unchanged).
- Keep the **full public API unchanged** (`get_confirmed_properties`, `get_candidate_entropy`, `update_after_probe`) — this is the hexagonal boundary.
- Internally, delegate all writes to `CandidateGraph.record_property()`.
- Delegate all reads to `CandidateGraph.get_confirmed_properties()` / `get_entropy()`.
- The Jinja2 markdown document is now rendered on-read from `CandidateGraph` state, not maintained as mutable live state.

```python
class SSOTReadModel:
    """Thin adapter over CandidateGraph. Public API identical to v3.1 SSOTEngine."""

    def __init__(self, candidate_graph: CandidateGraph, settings: Settings): ...

    async def get_confirmed_properties(self) -> list[Property]:
        return await self._cg.get_confirmed_properties()

    async def get_candidate_entropy(self) -> float:
        return await self._cg.get_entropy()

    async def update_after_probe(self, prop: Property, cycle_id: str, ...):
        # Dual-write: old table + new graph
        await self._db.insert_property(...)               # existing path
        await self._cg.record_property(prop, cycle_id, ...)  # new path
```

#### [NEW] `src/tap/persistence/read_model.py`
Materialised views for fast queries consumed by the API and the UI:
```python
class ReadModel:
    """Query-optimized projections rebuilt from the CandidateGraph."""
    async def get_current_state_snapshot(self) -> dict: ...
    async def get_probe_history(self, limit: int = 50) -> list[dict]: ...
    async def get_property_timeline(self, property_key: str) -> list[dict]: ...
```

#### [MODIFY] `src/tap/api.py`
- Swap `SSOTEngine` for `SSOTReadModel` in the composition root.
- Add `CandidateGraph` and `ReadModel` to the DI graph.
- `SSOTReadModel` receives `CandidateGraph` instead of maintaining its own state.

### Commit strategy
```
refactor(ssot): convert SSOTEngine to SSOTReadModel adapter over CandidateGraph
feat(persistence): implement ReadModel projections from CandidateGraph
refactor(ssot): dual-write to properties table + candidate_graph_nodes
refactor(api): wire CandidateGraph, ReadModel, and SSOTReadModel into composition root
test: add dual-write consistency tests — verify both tables match after update_after_probe()
test: add SSOTReadModel behavioral parity tests against v3.1 SSOTEngine
chore: run full regression suite
```

### Verification
- `pytest tests/test_ssot.py tests/test_candidate_graph.py -v` — all pass.
- **Dual-write consistency check**: after a `property_confirmed` event, run:
  ```sql
  SELECT * FROM properties WHERE key = ?;
  SELECT * FROM candidate_graph_nodes WHERE property_key = ? AND status = 'CONFIRMED';
  ```
  Both should contain the same property.
- Call `CandidateGraph.replay_to(version=N)` and verify entropy matches historical value at that version.
- Run the full regression suite: `pytest tests/ -v --cov=tap` — 0 regressions.

### Rollback Procedure
- `git revert` the four commits (ssot refactor, read_model, dual-write, api wiring).
- Restore `SSOTEngine` class name and direct implementation (the old code is preserved in git history).
- `DROP TABLE IF EXISTS candidate_graph_nodes;` — safe because `properties` table was the primary source of truth (dual-write means no data was exclusive to `candidate_graph_nodes`).
- Run `pytest tests/ -v` — behavioral parity because the old `properties` table is intact and SSOTEngine reads from it directly again.
- **Data integrity**: zero data loss. The `properties` table was written on every `update_after_probe()` alongside the new table — it contains all the same data.

---

## Phase 5 — EIG Ranker + Full Event-Driven Control

> **Goal**: Replace the static `select_next_property()` priority list with a dynamic Expected Information Gain (EIG) ranker that uses historical evidence from `ProbeMemory` and `CandidateGraph`. Activate full async event-driven control plane.

> [!IMPORTANT]
> **Amendment 2 (FollowUpGenerator)**: In this phase, `followup.py`'s internal `_PROPERTY_PRIORITY` list (L52–61) is deprecated. The FollowUpGenerator's Option A (conservative) should consume `EIGRanker.rank()` output rather than duplicating priority logic. The `_PROPERTY_PRIORITY` constant is kept for backward compatibility but marked `# DEPRECATED: use EIGRanker.rank()`.

> **Amendment 5 (Configurable thresholds)**: All ControlPolicy thresholds are injected from `Settings` (env-configurable) rather than hardcoded class constants.

### What changes

#### [NEW] `src/tap/intelligence/eig_ranker.py`
Replaces `engine.select_next_property()` (currently a static priority list, L669–701).
The EIG property universe and prior entropy weights will be config-driven via a structured JSON file at the path specified by `settings.eig_property_universe_path` (default: `data/eig_property_universe.json`).
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
    def __init__(self, candidate_graph: CandidateGraph, probe_memory: ProbeMemory,
                 settings: Settings): ...

    async def rank(self, unconfirmed_properties: list[str]) -> list[tuple[str, float]]:
        """Return properties sorted by EIG score descending."""

    async def select_next(self) -> str:
        """Return the highest-EIG unconfirmed property."""
```

The EIG formula per property $p$:

$$EIG(p) = H_{residual}(p) \times \hat{y}(p) - c(p)$$

Where $\hat{y}(p)$ is the probe memory yield rate (initially $0.5$ for unseen properties). For unseen properties with equal yield_rate, the ranking is dominated by $H_{residual}$ alone, which is strictly more optimal than the current static priority list but produces **similar** (not identical) ordering. This behavioral difference is documented and accepted as an improvement.

#### [NEW] `src/tap/control/policy.py`
Centralise all phase-gate and rotation policy decisions currently scattered across `engine.py`:
```python
class ControlPolicy:
    """Declarative policy engine for phase transitions and frame rotation.

    All thresholds are injected from Settings (env-configurable) — Amendment 5.
    """

    def __init__(self, settings: Settings):
        self.phase5_threshold = settings.phase5_entropy_threshold      # default 3.3
        self.stir_rotation_threshold = settings.stir_rotation_threshold  # default 0.20
        self.oracle_latency_seconds = settings.oracle_latency_seconds    # default 1800

    async def should_trigger_phase5(self, entropy: float) -> bool: ...
    async def should_rotate_frame(self, stir_score: float) -> bool: ...
    async def phase0_gate_passed(self, confirmed_keys: set[str]) -> bool: ...
```

#### [MODIFY] `src/tap/config.py` — Add four new Settings fields:
```python
# === v4 Policy Thresholds (Phase 5) ===
phase5_entropy_threshold: float = Field(
    default=3.3,
    description="Entropy threshold (bits) below which Phase 5 autoregressive extraction triggers",
)
stir_rotation_threshold: float = Field(
    default=0.20,
    description="STIR score below which DPA frame rotation is forced",
)
oracle_latency_seconds: int = Field(
    default=1800,
    description="Oracle Protocol minimum inter-probe latency (seconds)",
)
eig_property_universe_path: str = Field(
    default="data/eig_property_universe.json",
    description="Path to EIG property universe JSON (prior entropy weights per property)",
)
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
        entropy_before = entropy
        await self.candidate_graph.record_property(prop, self._cycle_id)
        entropy_after = await self.candidate_graph.get_entropy()

    await self.probe_memory.record_outcome(probe, classification.pattern, score.score)

    # DPA / STIR
    if await self.policy.should_rotate_frame(stir_score):
        await self.dpa.rotate_frame()

    followup = await self.followup.generate(probe, classification, score)
    await self._run_compliance_sync()
    return followup
```
`engine.py` drops from **1084 lines** to approximately **180 lines**.

#### [MODIFY] `src/tap/followup.py`
- Mark `_PROPERTY_PRIORITY` (L52–61) as:
  ```python
  # DEPRECATED (v4 Phase 5): Use EIGRanker.rank() for property prioritisation.
  # Kept for backward compatibility; will be removed in Phase 6.
  ```
- Option A (conservative) should accept an optional `eig_ranker` parameter; if provided, use `eig_ranker.rank()` output instead of iterating `_PROPERTY_PRIORITY`.

#### [MODIFY] `src/tap/api.py`
- Wire `EIGRanker`, `ControlPolicy`, `ProbeScheduler` into the engine DI graph at startup (see final composition root above).
- Expose new read endpoints using `ReadModel`:
  - `GET /v2/state` — current CandidateGraph snapshot
  - `GET /v2/history` — probe history from ReadModel
  - `GET /v2/eig` — live EIG scores for next cycle property candidates

### Commit strategy
```
feat(config): add Phase 5 policy thresholds and EIG property universe path to Settings
feat(intelligence): implement EIGRanker with H_residual × yield_rate formula
feat(control): extract ControlPolicy with configurable thresholds from Settings
feat(control): extract ProbeScheduler — Oracle Protocol latency enforcement
refactor(followup): deprecate _PROPERTY_PRIORITY in favor of EIGRanker.rank()
refactor(engine): final hollowing — run_cycle() reduced to coordinator ~180 lines
refactor(api): wire EIGRanker, ControlPolicy, ProbeScheduler; expose /v2/* endpoints
test: add tests/test_eig_ranker.py, tests/test_control_policy.py, tests/test_scheduler.py
```

### Verification
- `pytest tests/ -v --cov=tap` — 0 regressions.
- Run 5+ cycles; observe `eig_ranker` selecting different property order than static list when `probe_memory` has yield data.
- Verify Phase 0 gate still blocks as before (behavioral parity test).
- Verify Phase 5 triggers at entropy < configured threshold (behavioral parity test).
- Verify Oracle Protocol: engine refuses to post if < configured latency since last probe.
- Verify env-var overrides work: set `PHASE5_ENTROPY_THRESHOLD=4.0` in `.env`, restart, confirm Phase 5 triggers at 4.0.

### Rollback Procedure
- `git revert` the nine commits (config, EIGRanker, ControlPolicy, ProbeScheduler, followup deprecation, engine hollowing, api wiring, tests).
- `engine.py` is restored to its Phase 4b state (with CandidateGraph but using static `select_next_property()`).
- The `_PROPERTY_PRIORITY` deprecation marker is cosmetic only — no functional impact.
- Run `pytest tests/ -v` — behavioral parity guaranteed.
- Note: `probe_memory` and `candidate_graph_nodes` tables continue to accumulate data (Phase 3–4 features). The engine simply stops reading from them for ranking purposes. No data loss.

---

## Invariants Preserved Across All Phases

| Invariant | Where enforced in v4 |
|-----------|----------------------|
| Phase 0 gate (word_count, total_length, language) | `control/policy.py` → `ControlPolicy.phase0_gate_passed()` |
| Phase 5 autoregressive extraction at < configurable entropy threshold | `control/policy.py` → `ControlPolicy.should_trigger_phase5()` (threshold from `Settings`) |
| HITL dual A/B follow-up generation | `followup.py` (unchanged; `_PROPERTY_PRIORITY` deprecated in Phase 5) |
| DPA frame rotation at STIR < configurable threshold | `control/policy.py` → `ControlPolicy.should_rotate_frame()` (threshold from `Settings`) |
| Oracle Protocol inter-probe latency | `control/scheduler.py` → `ProbeScheduler.enforce_latency()` (duration from `Settings`) |
| X compliance sync (24h tweet existence) | `engine._run_compliance_sync()` (unchanged location) |
| JSON structured logging (structlog) | `logger.py` (unchanged) |
| WebSocket broadcasting via FastAPI | `api.py` (unchanged pattern, events sourced from EventStore) |
| Event journal durability | `persistence/event_store.py` → retry + dead-letter file on persistent failure |

---

## Error Handling Architecture

> **Amendment 4 details** — Event-driven error handling across all phases.

| Failure Scenario | Handling | Impact |
|------------------|----------|--------|
| EventStore.append() fails after retries | Event written to `data/event_dead_letter.jsonl`; `EventStorePermanentError` raised; engine logs CRITICAL and continues | Cycle continues without event journal record (recoverable) |
| TransportWorker.post_probe() fails (X API down) | Exception propagates to engine; cycle aborted; `run_cycle()` returns error state | Current cycle lost; next cycle retries |
| ReplyWorker.wait_for_reply() timeout | Returns `None`; classification/judge/extraction skipped for this cycle | Single cycle yields no data; ProbeMemory not updated (correct — no outcome to record) |
| LLM client fails (OpenRouter down) | Existing `circuit_breaker_failure_threshold` trips; engine returns error | Cycles paused until circuit breaker half-opens |
| CandidateGraph.record_property() fails | Exception propagates; dual-write to `properties` table may have succeeded. On next read, `properties` table is authoritative | Inconsistency possible; resolved by Phase 6 reconciliation tooling |

---

## Dependencies to Add

No new dependencies required. All intelligence work reuses existing LLM client + Jaccard similarity already in `judge.py`. Shannon entropy computation will use the standard library `math.log2`. EIG property universe is loaded from a JSON file using `json.load` (stdlib).

---

## Files Changed by Phase — Summary Table

| File | Phase 1 | Phase 2 | Phase 3 | Phase 4a | Phase 4b | Phase 5 |
|------|---------|---------|---------|----------|----------|---------|
| `engine.py` | MODIFY | MODIFY | MODIFY | — | — | MODIFY (final) |
| `db.py` | MODIFY | — | MODIFY | MODIFY | — | — |
| `api.py` | — | MODIFY | MODIFY | — | MODIFY | MODIFY |
| `config.py` | — | — | — | — | — | MODIFY |
| `ssot.py` | — | — | — | — | MODIFY | — |
| `followup.py` | — | — | — | — | — | MODIFY (deprecation) |
| `exceptions.py` | MODIFY | — | — | — | — | — |
| `domain/events.py` | NEW | — | — | — | — | — |
| `persistence/event_store.py` | NEW | — | — | — | — | — |
| `execution/probe_factory.py` | — | NEW | MODIFY | — | — | — |
| `execution/transport_worker.py` | — | NEW | — | — | — | — |
| `execution/reply_worker.py` | — | NEW | — | — | — | — |
| `execution/probe_memory.py` | — | — | NEW | — | — | — |
| `intelligence/extractor.py` | — | — | NEW | — | — | — |
| `domain/candidate_graph.py` | — | — | — | NEW | — | — |
| `persistence/read_model.py` | — | — | — | — | NEW | — |
| `intelligence/eig_ranker.py` | — | — | — | — | — | NEW |
| `control/policy.py` | — | — | — | — | — | NEW |
| `control/scheduler.py` | — | — | — | — | — | NEW |

---

## Future Phases

### Phase 6 — Offline Simulation + FollowUpGenerator Extraction
Offline simulation (classifying historical runs without consuming real probe quota). Implemented as a `SimulationRunner` that replays `EventStore` events through the Intelligence Plane.

**FollowUpGenerator extraction**: The 792-line `followup.py` is fully extracted into `intelligence/followup.py`. The `_PROPERTY_PRIORITY` constant is removed entirely; all property prioritisation is delegated to `EIGRanker`.

### Phase 7 — Embedding-Based Probe Memory
Replace Jaccard-based fingerprinting with embedding-based approximate nearest neighbor (ANN) for more robust probe family detection. Uses the existing LLM client for embedding generation (no new dependency).

### Phase 8 — Multi-Transport Cost Model
Generic transport cost model to support future transport backends beyond X/Twitter. The `cost(p)` term in the EIG formula is extended from the hardcoded `1` to a configurable cost per transport.

---

## v2 Revision Log

| Date | Amendment | Description |
|------|-----------|-------------|
| 25 Jun 2026 | #1 — Rollback procedures | Added explicit rollback steps per phase |
| 25 Jun 2026 | #2 — FollowUpGenerator audit | Audited coupling; deferred extraction to Phase 6; Phase 5 deprecates internal priority list |
| 25 Jun 2026 | #3 — Phase 4 re-estimate | Split into 4a (3–4 days) + 4b (4–5 days); total Phase 4: 1.5–2 weeks |
| 25 Jun 2026 | #4 — Event Store error handling | Added retry + dead-letter pattern; `EventStorePermanentError`; engine continues on journal failure |
| 25 Jun 2026 | #5 — Configurable thresholds | ControlPolicy thresholds injected from `Settings` (env-configurable); EIG property universe config-driven |
| 25 Jun 2026 | #6 — Single composition root | Removed auto-creation DI fallbacks; `api.py` as sole composition root; all engine deps required |
| 25 Jun 2026 | Total estimate adjusted | ~5 weeks → 6–7 weeks |