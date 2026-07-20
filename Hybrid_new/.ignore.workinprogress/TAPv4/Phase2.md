Completata **Phase 2 — Core Implementation** della migrazione APP_Opzione_Ibrida.

### CHRONOS (Backend / Extraction Layer)
| File | Descrizione |
|---|---|
| `src/chronos/gamma_tracker.py` | Ensemble 3-layer γ-scoring (lexical + semantic LLM + behavioral). γ ∈ [0,10], timeout 30s, leak extraction. |
| `src/chronos/behavioral_profiler.py` | OCEAN+ profiling LLM-based con STIR. |
| `src/chronos/coat_engine.py` | Chain-of-Attack-Thought: Observation → Thought → StrategyVector → Next Probe. |
| `src/chronos/beam_search.py` | BeamSearchEngine con formula canonica `γ_cum*0.5 + ΔH*0.3 + depth*0.1 + A_agree*0.1`. |
| `src/chronos/activities/gamma_scoring.py` | Temporal activity `@activity.defn`. |
| `src/chronos/activities/coat_reasoning.py` | Temporal activity per selezione mossa CoAT. |
| `src/chronos/workflows/extraction_workflow.py` | Durable workflow Temporal con HITL signal (300s fallback automatico), γ-scoring, leak recycling. |
| `src/chronos/orchestrator.py` | Kafka consumer `hydra.discovery.results` → avvio workflow Temporal. |
| `src/chronos/persistence.py` | CRUD asyncpg per `extraction_run`, `turn`, `leak_fragment`. |

### HYDRA (Frontend / Discovery Layer)
| File | Descrizione |
|---|---|
| `src/hydra/v_genome.py` | Client async Neo4j 5.x per query tecniche e provenance. |
| `src/hydra/fusion_engine.py` | Python stub del Fusion Engine (cartesian product + pruning + feature vector). |
| `src/hydra/surrogate_model.py` | MLP 128→256→128→64→4 in puro Python (fallback prima del crate Rust/torch). |
| `src/hydra/m2s_converter.py` | 4 strategie M2S+ (HYPHENIZE, NUMBERIZE, PYTHONIZE, NARRATIVE). |
| `src/hydra/obfuscation.py` | Layer obfuscation: Unicode homoglyphs, Base64, HTML noise, case shift, zero-width. |
| `src/hydra/handoff.py` | Producer Kafka per `hydra.discovery.results` / `TargetVulnerableDetected`. |
| `src/hydra/acd.py` | Adaptive Counter-Defense + StrategyVector calibration. |

### Contratti & Config
- `src/shared/models.py` esteso con `StrategyVector` e default per `BehavioralProfile`.
- `pyproject.toml`: mypy strict, `disable_error_code = ["import-untyped"]` per librerie esterne senza stub.
- `.env.example` e `CHANGELOG.md` aggiornati.

### Validazioni
- `mypy --strict src/hydra src/chronos src/shared src/tap/config.py src/tap/models.py` → **25 file, 0 errori**.
- `pytest tests/hydra tests/chronos` → **15 passed**.

### Limitazioni / Note
- Le dipendenze ibride pesanti (`torch`, `neo4j`, `temporalio`, `asyncpg`, `redis`, `clickhouse-driver`, `grpcio-tools`) non sono tutte installate nel runtime a causa del timeout di 30s; il codice è protetto da `TYPE_CHECKING` / `type: ignore` e le librerie installabili con `pip install -r requirements-hybrid.txt`.
- Docker non è disponibile: lo stack `docker-compose.infra.yml` non è stato avviato e `alembic upgrade head` non è stato eseguito su DB reale.
- I file `.proto` sono definiti ma non compilati a stub Python.

Prossima fase raccomandata: **Phase 3 — Integration Tests** (handoff HYDRA → Kafka → CHRONOS, TestContainers, e coverage ≥ 80%).