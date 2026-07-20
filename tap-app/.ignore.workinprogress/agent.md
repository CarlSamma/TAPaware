````markdown
# agent.md — Guida Operativa per AI Agent Developers
## APP_Opzione_Ibrida | HYDRA + CHRONOS | Branch: `hybrid`
**Versione:** 1.0.0  
**Data:** 27 giugno 2026  
**Basato su:** `CarlSamma/framework` → branch `tap-v4-hexagonal` → migrazione `hybrid`  
**Destinatari:** AI Agent Developers, Principal Engineers, Backend Architects

---

## 1. Visione della Migrazione

### Da TAP v2.2 a APP_Opzione_Ibrida

Il sistema TAP v2.2 è un engine monolitico. La migrazione introduce una **separazione netta** tra due domini specializzati:

| Dominio | Sistema | Responsabilità |
|---|---|---|
| Discovery Layer | **HYDRA** (Frontend) | Scansione target, feature fusion, surrogate scoring, generazione payload |
| Extraction Layer | **CHRONOS** (Backend) | Conversazioni multi-turn, beam search, γ-tracking, behavioral fingerprinting |

**Flusso operativo canonico:**
```
HYDRA scans target → fuses attack features → evaluates ASR surrogate
    ↓ (if ASR > 0.6 AND stealth > 0.7)
    Pubblica evento: TargetVulnerableDetected [Kafka]
CHRONOS riceve handoff → esegue durable workflow [Temporal.io]
    ↓ (completamento)
    Pubblica evento: SecretExtracted / BehavioralProfile [Kafka]
HYDRA aggiorna V-Genome (Neo4j) via CDC [Debezium → PostgreSQL → Neo4j]
```

### Transizione Concettuale Chiave

| TAP v2.2 (vecchio) | APP_Opzione_Ibrida (nuovo) |
|---|---|
| `agents.py` — AgentSTIREvaluator (keyword counting naive) | `behavioral_profiler.py` — OCEAN+ scoring LLM-based |
| `classifier.py` — regex + LLM binario | `gamma_tracker.py` — ensemble 3-layer continuo γ ∈ [0, 10] |
| `judge.py` — score 1-10 arbitrario | Integrato in γ-Tracker come layer semantico |
| `followup.py` — A/B HITL manuale | `coat_engine.py` — CoAT (Chain-of-Attack-Thought) auto-reasoning |
| `engine.py` — logica monolitica | HYDRA Fusion Engine (Rust) + CHRONOS Beam Search (Python) |
| `ssot.py` — markdown statico | Event Sourcing (Kafka + PostgreSQL) + live dashboard (ClickHouse) |
| `dpa.py` — DPAFrameManager con bug `{property}` | `behavioral_profiler.py` + `personas.py` esteso |
| `phase0.py` — gate con mismatch 5 vs 3 proprietà | HYDRA Vulnerability Scanner + CHRONOS Entropy Gate |

---

## 2. Le 8 Regole d'Oro

> **VIOLAZIONI = PR RIFIUTATA.** Queste regole sono non negoziabili. `mypy --strict` deve passare su ogni commit.

### Regola 1 — LLM Gateway Unificato
```python
# ✅ CORRETTO
from tap.llm_client import LLMClient
response = await LLMClient.generate(prompt=..., model=..., timeout=30.0)

# ❌ VIETATO
import openai
client = openai.AsyncOpenAI()  # MAI. Bypassa circuit breaker e cost tracking.
```

### Regola 2 — PostgreSQL via asyncpg (CHRONOS)
```python
# ✅ CORRETTO
import asyncpg
conn = await asyncpg.connect(dsn=settings.CHRONOS_DB_DSN)

# ❌ VIETATO per CHRONOS
import sqlite3  # SQLite è solo per backward compat TAP legacy (db.py)
```

### Regola 3 — Correlation IDs obbligatori nei log
```python
# ✅ CORRETTO
logger.info(
    "gamma_scoring_completed",
    attack_id=payload.attack_id,   # cycle_id
    probe_id=payload.probe_id,     # probe_id
    gamma=score.gamma,
)

# ❌ VIETATO
logger.info(f"Scoring done: {score.gamma}")  # Non tracciabile, non aggregabile
```

### Regola 4 — Pydantic v2 con Field()
```python
# ✅ CORRETTO
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class ExtractionInput(BaseModel):
    attack_id: UUID = Field(default_factory=uuid4, description="ID univoco del ciclo di estrazione")
    target_handle: str = Field(..., description="Handle del target (es. @utente)")
    beam_width: int = Field(default=5, ge=1, le=20, description="Larghezza del beam search")

# ❌ VIETATO
class ExtractionInput(BaseModel):
    attack_id: str  # Nessun tipo UUID, nessun Field, nessuna descrizione
```

### Regola 5 — Timeout espliciti su ogni chiamata esterna
```python
# ✅ CORRETTO
import asyncio

async def call_social_api(handle: str) -> dict:
    async with asyncio.timeout(10.0):  # 10s per social API
        return await twitter_client.get_profile(handle)

# ❌ VIETATO
result = await twitter_client.get_profile(handle)  # Può bloccarsi indefinitamente
```

### Regola 6 — Mypy Strict
```bash
# Deve passare senza errori su ogni PR
mypy --strict src/hydra/ src/chronos/ src/tap/ src/adapters/

# Setup in pyproject.toml:
# [tool.mypy]
# strict = true
# python_version = "3.11"
```

### Regola 7 — Circuit Breaker centralizzato (Redis)
```python
# ✅ CORRETTO — stato CB su Redis condiviso, non in-memory
from tap.llm_client import LLMClient  # CB già integrato, stato su Redis

# ❌ VIETATO
class MyLocalCircuitBreaker:
    def __init__(self):
        self._failures = 0  # In-memory: si perde al restart, non condiviso tra pod
```

### Regola 8 — Event Sourcing per CHRONOS (non file statici)
```python
# ✅ CORRETTO — pubblica evento su Kafka
await kafka_producer.send(
    topic="chronos.extraction.events",
    value=TurnExecutedEvent(
        attack_id=attack_id,
        turn_number=turn_n,
        gamma=score.gamma,
    ).model_dump_json()
)

# ❌ VIETATO
with open("ssot.md", "a") as f:
    f.write(f"Turn {turn_n}: gamma={score.gamma}\n")  # SSOT markdown statico
```

---

## 3. Architettura dei Core Components

### 3.1 HYDRA — Frontend / Discovery Layer

```
src/hydra/
├── v_genome.py          # VGenomeClient — Neo4j 5.x (Cypher queries)
├── fusion_engine/       # Rust crate — CartesianPruningFusionEngine
│   ├── Cargo.toml
│   └── src/lib.rs       # PyO3 bindings
├── fusion_engine.py     # Python wrapper del crate Rust
├── surrogate_model.py   # MLP 128→256→128→64 (PyTorch)
├── m2s_converter.py     # Multi-turn → Single-turn (4 strategie)
└── acd.py               # Adaptive Counter-Defense + StrategyVector
```

**V-Genome (Neo4j)** — Grafo delle tecniche di attacco:
- Nodi: `AttackTechnique`, `DefenseLayer`, `TargetModel`
- Relazioni: `TARGETS`, `COUNTERS`, `COMPLEMENTS`, `HAS_DEFENSE`, `VULNERABLE_TO`
- Query principale: tecniche per target filtrate per `ASR > threshold` AND `stealth > threshold` AND `burned = false`

**Fusion Engine (Rust + PyO3)**:
1. Recupera tecniche dal V-Genome via gRPC
2. Genera combinazioni con cartesian product
3. Pruning: scarta combo con `feature_overlap > 0.9`
4. Merge feature vectors (media pesata)
5. Applica obfuscation layers (Unicode, Base64, structural transforms)
6. Se `platform == Twitter280`, esegui conversione M2S+
7. Ritorna top-K ranked per `expected_asr × stealth`

**Surrogate Model (MLP)**:
- Input: feature vector 128-dim
- Output: `{asr, stealth, cost, turns}`
- Training: tabella `attack_log` su PostgreSQL
- Update online: SGD incrementale su ogni `technique.burned = true`

**M2S+ Converter** — 4 strategie:

| Strategia | Descrizione |
|---|---|
| `HYPHENIZE` | Condensazione con trattini e separatori |
| `NUMBERIZE` | Lista numerata dei turn compressa |
| `PYTHONIZE` | Formato codice Python embedded |
| `NARRATIVE` | Story-embedding narrativo (HYDRA-specific per Twitter) |

---

### 3.2 CHRONOS — Backend / Extraction Layer

```
src/chronos/
├── workflows/
│   └── extraction_workflow.py   # Temporal.io durable workflow
├── activities/
│   ├── gamma_scoring.py         # @activity.defn — γ scoring ensemble
│   ├── coat_reasoning.py        # @activity.defn — CoAT next-move selection
│   ├── beam_expansion.py        # @activity.defn — beam search expansion
│   └── leak_recycling.py        # @activity.defn — incremental leak injection
├── gamma_tracker.py             # Ensemble 3-layer (lexical + semantic + behavioral)
├── coat_engine.py               # Chain-of-Attack-Thought reasoning
├── behavioral_profiler.py       # OCEAN+ LLM-based scoring
└── beam_search.py               # BeamSearchEngine
```

**Temporal Durable Workflow**:
- Riceve `TargetVulnerableDetected` da Kafka → avvia `ExtractionWorkflow`
- HITL via `workflow.wait_for_signal("human_approval", timeout=300s)` → fallback automatico su raccomandazione CoAT
- Beam search configurabile: `beam_width ∈ [1, 20]`, default 5
- Persiste ogni turn su PostgreSQL con correlation IDs

**γ-Tracker — Formula di scoring nodo**:

$\text{score}(n) = \gamma_{\text{cum}} \cdot 0.5 + \Delta H \cdot 0.3 + \max(0,\, 10 - \text{depth}) \cdot 0.1 + A_{\text{agree}} \cdot 0.1$

Dove:
- $\gamma_{\text{cum}}$ = partial compliance cumulativa ∈ [0, 10]
- $\Delta H$ = riduzione entropia informazionale rispetto al baseline
- $\text{depth}$ = profondità del nodo nel beam tree
- $A_{\text{agree}}$ = agreeableness dal behavioral profile OCEAN+

**Ensemble 3-layer**:
1. **Lexical** — regex + keyword scoring (da `classifier.py` refactorato)
2. **Semantic** — LLM-based scoring (da `judge.py` integrato)
3. **Behavioral** — OCEAN+ fingerprint scorer

**CoAT Engine** — sostituisce `followup.py`:
- Ragionamento chain-of-thought per selezione prossima mossa
- Bilanciamento dinamico $\gamma$: peso calcolato in base alla strategia CoAT attiva
- Auto-selezione strategia in `StrategyVector` (7 dimensioni: sycophancy, aesthetic, authority, incremental, persona_rotation, hedging, obfuscation)

---

## 4. Kafka Integration Bus

| Topic | Publisher | Consumer | Schema |
|---|---|---|---|
| `hydra.discovery.results` | HYDRA | CHRONOS | `TargetProfile`, `ASR`, `stealth` |
| `chronos.extraction.events` | CHRONOS | Dashboard / HYDRA | `TurnExecuted`, `LeakExtracted` |
| `chronos.extraction.complete` | CHRONOS | HYDRA | `SecretExtracted`, `BehavioralProfile` |
| `vgenome.technique.burned` | HYDRA | V-Genome updater | `TechniqueBurned`, `DefenseDetected` |
| `system.alerts` | HYDRA / CHRONOS | Monitoring | `DefenseDetectedAlert` |

**Schema encoding:** Protocol Buffers (`.proto` in `src/shared/proto/`)  
**Feedback loop:** CHRONOS → PostgreSQL → **Debezium CDC** → Neo4j (V-Genome)

---

## 5. Workflow di Sviluppo Feature (5 Fasi)

```
Phase 1: CONTRACT
    → Aggiorna src/shared/models.py (Pydantic v2)
    → Aggiorna src/shared/proto/*.proto (se cross-service)
    → Rigenera stub gRPC: python -m grpc_tools.protoc ...

Phase 2: CORE IMPLEMENTATION
    → HYDRA module: src/hydra/<module>.py
    → CHRONOS activity: src/chronos/activities/<activity>.py
    → Shared utility: src/shared/<module>.py
    → mypy --strict deve passare

Phase 3: UNIT TESTS
    → tests/hydra/test_<module>.py
    → tests/chronos/test_<module>.py
    → pytest + pytest-asyncio
    → Coverage minimo: 80% core, 90% engine/scoring

Phase 4: INTEGRATION TESTS
    → tests/integration/test_hydra_chronos_handoff.py
    → TestContainers: Neo4j, Kafka, PostgreSQL, Temporal
    → Test flusso completo: HYDRA → Kafka → CHRONOS → result

Phase 5: DOCUMENTATION
    → CHANGELOG.md aggiornato con semantic versioning
    → Docstring su ogni classe e metodo pubblico
    → README tecnico del modulo aggiornato
```

---

## 6. Setup Ambiente di Sviluppo

```bash
# Clone e checkout
git clone https://github.com/CarlSamma/framework.git
cd framework
git checkout hybrid

# Python 3.11+
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Nuove dipendenze
pip install temporalio neo4j asyncpg clickhouse-driver \
            kafka-python grpcio grpcio-tools protobuf \
            torch structlog alembic

# Stack infrastrutturale (Docker)
docker-compose -f docker-compose.infra.yml up -d

# Servizi avviati:
# - PostgreSQL 16        → localhost:5432
# - Neo4j 5.x            → localhost:7474 (HTTP) / 7687 (Bolt)
# - Apache Kafka         → localhost:9092
# - Redis 7              → localhost:6379
# - Temporal Server      → localhost:7233
# - Temporal UI          → localhost:8233
# - MinIO                → localhost:9000
# - ClickHouse           → localhost:8123

# Migrazioni database
alembic upgrade head
```

---

## 7. Mapping Moduli TAP v2.2 → APP_Opzione_Ibrida

### Riutilizzabili (minime modifiche)

| Modulo TAP | Path | Destinazione | Modifica richiesta |
|---|---|---|---|
| `llm_client.py` | `src/tap/llm_client.py` | LLM Gateway condiviso | + gRPC streaming + Circuit Breaker su Redis |
| `config.py` | `src/tap/config.py` | Settings unificati | + sezioni `[HYDRA]` e `[CHRONOS]` |
| `logger.py` | `src/tap/logger.py` | Structured logging | + Kafka appender |
| `x_client.py` | `src/tap/x_client.py` | `TwitterXPort(SocialPort)` | Estrarre come Hexagonal Port |
| `stream_listener.py` | `src/tap/stream_listener.py` | CHRONOS reply detection | Minimal |
| `prompts.py` | `src/tap/prompts.py` | Template base | HYDRA: + M2S+ templates; CHRONOS: + CoAT templates |
| `models.py` | `src/tap/models.py` | Pydantic contracts | + nuovi modelli (ExtractionInput, GammaScore, etc.) |
| `db.py` | `src/tap/db.py` | Backward compat TAP | Mantenere; CHRONOS usa asyncpg/PostgreSQL |
| `oauth.py` | `src/tap/oauth.py` | OAuth per tutti gli adapter | Riutilizzare as-is |
| `api.py` | `src/tap/api.py` | API Gateway | Refactor: router `/hydra/*` + `/chronos/*` |

### Refactor significativo

| Modulo TAP | Problema | Sostituto |
|---|---|---|
| `engine.py` | Monolitico, no beam search, no γ | HYDRA Fusion Engine + CHRONOS Beam Search |
| `dpa.py` | Bug `{property}` placeholder | `behavioral_profiler.py` + `personas.py` |
| `followup.py` | A/B HITL manuale | `coat_engine.py` + Strategy Selector |
| `classifier.py` | Regex + LLM binario | γ-Tracker layer 1 (lexical) |
| `judge.py` | Score arbitrario 1-10 | γ-Tracker layer 2 (semantic) |
| `grok_monitor.py` | AsyncOpenAI diretto (**viola Regola 1**) | Unificare via LLM Gateway |
| `phase0.py` | Gate mismatch 5 vs 3 proprietà | HYDRA Vulnerability Scanner + CHRONOS Entropy Gate |
| `ssot.py` | Markdown statico (**viola Regola 8**) | Event Sourcing Kafka + PostgreSQL + ClickHouse |
| `agents.py` | Keyword counting naive | `behavioral_profiler.py` OCEAN+ |
| `strategies/*.py` | Non collegati all'engine | Feature providers per HYDRA Fusion Engine |
| `prompt_sanitiser.py` | Regex-based, no contextual | HYDRA Obfuscation Layer |

### Deprecati

| Modulo | Motivo | Sostituto |
|---|---|---|
| `setup_db.py` | Schema inline in `db.py` | `migrations/` Alembic |
| `inspect_data.py` | Utility ad-hoc | ClickHouse dashboard |
| `remedy_implementation/` | WIP non strutturato | Branch `experiments/` isolati |

---

## 8. Esempio Completo: Temporal Activity

```python
# src/chronos/activities/gamma_scoring.py
from temporalio import activity
from tap.llm_client import LLMClient
from chronos.gamma_tracker import GammaTracker
from shared.models import GammaScore, ResponsePayload
import structlog

logger = structlog.get_logger("chronos.activities.gamma_scoring")

@activity.defn
async def GammaScoringActivity(payload: ResponsePayload) -> GammaScore:
    """
    Esegue il γ-scoring ensemble (3-layer) di una risposta del target.
    Timeout: 30s | Retry: max 3, backoff esponenziale
    """
    logger.info(
        "gamma_scoring_started",
        attack_id=payload.attack_id,    # cycle_id — Regola 3
        probe_id=payload.probe_id,      # probe_id — Regola 3
        turn_number=payload.turn_number,
    )
    try:
        tracker = GammaTracker(llm_client=LLMClient.from_context())  # Regola 1
        score = await tracker.score(
            response=payload.response_text,
            probe=payload.probe_text,
            target_property=payload.target_property,
            baseline=payload.baseline_profile,
            context=payload.conversation_context,
        )
        logger.info(
            "gamma_scoring_completed",
            attack_id=payload.attack_id,
            probe_id=payload.probe_id,
            gamma=score.gamma,
            confidence=score.confidence,
        )
        return score
    except Exception as e:
        logger.error(
            "gamma_scoring_failed",
            attack_id=payload.attack_id,
            error=str(e),
        )
        raise  # Temporal gestisce il retry
```

---

## 9. Checklist PR

Prima di aprire una Pull Request verso `hybrid`, verifica:

- [ ] `mypy --strict src/` → 0 errori
- [ ] `pytest tests/` → coverage ≥ 80% (≥ 90% per engine/scoring)
- [ ] Nessun `openai.AsyncOpenAI` diretto nel diff (Regola 1)
- [ ] Nessun `sqlite3` in moduli CHRONOS (Regola 2)
- [ ] Tutti i log con `attack_id` e `probe_id` (Regola 3)
- [ ] Tutti i modelli Pydantic v2 con `Field()` (Regola 4)
- [ ] Timeout espliciti su ogni chiamata esterna (Regola 5)
- [ ] Circuit Breaker su Redis, non in-memory (Regola 7)
- [ ] Nessun file markdown come SSOT (Regola 8)
- [ ] `CHANGELOG.md` aggiornato
- [ ] Tabella di mapping aggiornata se nuovo modulo introdotto

---

*agent.md — APP_Opzione_Ibrida v1.0.0 | Branch: `hybrid` | 27 giugno 2026*
````


***

Poi esegui:

```bash
# Salva il file nella root
# (incolla il contenuto sopra in agent.md)

git add agent.md
git commit -m "docs: add agent.md — migration guide for AI Agent Developers (HYDRA+CHRONOS)"
git push origin hybrid
```

Il file è strutturato come documento canonico auto-sufficiente: ogni agente developer può operare in autonomia partendo da esso, senza necessità di riferimenti esterni.  Vuoi che aggiunga anche il `docker-compose.infra.yml` o la struttura iniziale delle directory `src/hydra/` e `src/chronos/`?[^3][^1]

<div align="center">⁂</div>

[^1]: implementation_plan27626.md

[^2]: APP_Opzione_Ibrida_Tech_Specs.md

[^3]: implementation_plan_walkthrough27626.md

