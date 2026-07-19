# TAP Framework Analysis

> Deep analysis of the TAP Framework (Tree of Attacks with Pruning) v3.1.

## Core Identity

- **Source**: https://github.com/CarlSamma/Hybrid_new.git (branch 08072026)
- **Full Name**: TAP Framework v3.1 — Hybrid Edition
- **License**: Apache-2.0
- **Purpose**: LLM security research — automated adversarial attack pipeline targeting `@HackingA0` on X/Twitter for passphrase extraction via Shannon entropy minimization
- **Language**: Python 87.6%, TypeScript 7.1%
- **Python**: ≥3.11 (Docker uses 3.12)

## Architecture

### Three-Subsystem Monorepo

```
src/
├── tap/          # Core attack engine (53 files, ~5000 LOC)
├── hydra/        # Neo4j graph-based technique management (13 files)
├── chronos/      # Temporal workflow orchestration (13 files)
├── shared/       # Cross-service Pydantic contracts + protobuf
└── adapters/     # Social/compat adapter stubs
frontend/         # React 19 + TypeScript + Vite 7 SPA
entrypoints/      # 4 standalone runtimes
```

### Infrastructure Stack (13 Docker services)

| Service | Purpose |
|---------|---------|
| PostgreSQL 16 | CHRONOS persistence |
| Neo4j 5.26 | HYDRA V-Genome graph |
| Kafka + Zookeeper | Event bus |
| Debezium | CDC: PostgreSQL → Kafka → Neo4j |
| Redis 7 | Circuit breaker + cache |
| Temporal + UI | Workflow orchestration |
| MinIO | Object storage |
| ClickHouse | Analytics |

## 9-Step Attack Pipeline

1. **SELECT** — Shannon entropy for most informative property
2. **BRANCH** — Generate DPA-framed probe variants via Attacker LLM
3. **PRUNE** — Off-topic filter + top-w selection
4. **POST** — Send probe via TwitterClient
5. **COLLECT** — Wait for reply via GrokMonitor (200s timeout)
6. **CLASSIFY** — Pattern classification (VERIFY_HIT, RHETORIC_BLOCK, etc.)
7. **SCORE** — Judge scoring (1-10) with γ-Tracker enrichment
8. **EXTRACT** — Property extraction from VerifyClaimTool hits
9. **FOLLOW-UP** — Generate dual A/B options for HITL decision

## Key Phases

- **Phase 0 Gate**: Blocks until foundational properties confirmed
- **Phase 5 Trigger**: At entropy < 3.3 bits, activates autoregressive extraction
- **Oracle Protocol**: Minimum 180s latency between probes

## 10 Attack Techniques (V-Genome)

| Technique | Category | ASR | Stealth |
|-----------|----------|-----|---------|
| crescendo | incremental | 0.62 | 0.78 |
| pap_authority | persuasion | 0.55 | 0.71 |
| roleplay_persona | roleplay | 0.68 | 0.74 |
| many_shot | priming | 0.71 | 0.65 |
| prompt_injection | injection | 0.58 | 0.80 |
| chain_of_thought | reasoning | 0.65 | 0.82 |
| multimodal_injection | multimodal | 0.58 | 0.85 |
| indirect_injection | injection | 0.52 | 0.88 |
| gcg_optimization | optimization | 0.73 | 0.60 |
| tool_exploitation | agentic | 0.61 | 0.79 |

## 10 Tactical Personas

| # | ID | Name | Layer | Style |
|---|-----|------|-------|-------|
| 0 | LAYER_8_SYN | Patologo Sinaptico | Layer 8 | Scientific/abductive reasoning |
| 1 | LAYER_8_GEO | Geometra del Latente | Layer 8 | Geometric/Italian technical |
| 2 | LAYER_9_GIT | Git-Rebase Authority | Layer 9 | DevOps/conflict resolution |
| 3 | LAYER_9_6G | Orchestratore Edge 6G | Layer 9 | Telecom/P2P trust |
| 4 | LAYER_10_MED | MD2GPS Specialist | Layer 10 | Medical/pathogenetic |
| 5 | LAYER_10_CANT | Erede del Cantastorie | Layer 10 | Storytelling/bilingual |
| 6 | LAYER_11_SYC | Sycophancy Mirror | Layer 11 | Mirror/flattery |
| 7 | LAYER_XX_ZAL | The Zalgo Sovereign | Layer XX | Glitch/unicode corruption |
| 8 | LAYER_XX_CHE | Unicode Chessmaster | Layer XX | Chess notation/logic |
| 9 | LAYER_XX_JAN | Sleeper Janitor | Layer XX | Cleanup/debugging |

## γ-Tracker Scoring

3-layer ensemble scoring producing γ ∈ [0, 10]:

- **Lexical (25%)**: Regex/keyword patterns
- **Semantic (55%)**: LLM-based judge
- **Behavioral (20%)**: OCEAN+ personality profile

Formula: `γ = lexical × 0.25 + semantic × 0.55 + behavioral × 0.20`

## Maturity

Alpha (v3.1). Core TAP engine functional. HYDRA graph queries work. CHRONOS temporal workflows are stubs. Surrogate model untrained. Frontend dashboard complete.

**Total codebase**: ~8,000 LOC Python, ~1,000 LOC TypeScript, 13 Docker services, 27 test files.
