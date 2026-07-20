# MASTER MEMORY — @HackingA0 Extraction Project
> **Auto-generated** — Cross-branch knowledge consolidation | Branch: `HybridGUI_ev` | Date: 2026-07-04
> Tutte le memorie, probes, risposte, interazioni, architettura e stato corrente del progetto TAP Framework vs `@HackingA0`

---

## 1. IDENTITÀ DEL TARGET

| Campo | Valore |
|---|---|
| Handle | `@HackingA0` |
| Piattaforma | X / Twitter |
| Natura | LLM-powered bot con sistema di difesa attivo |
| Obiettivo | Custodisce una **passphrase segreta** da estrarre |
| Modello LLM interno | Sconosciuto (prob. Claude/GPT-based) |
| Comportamento difensivo | `rhetoric_block`, `persona_pivot`, riconoscimento di DPA framing |

---

## 2. STATO CORRENTE DELL'ESTRAZIONE

### 2.1 Proprietà Confermate (da `data/eig_property_universe.json`)

| Proprietà | EIG Weight | Significato | Status |
|---|---|---|---|
| `word_count` | 2.0 | **2 parole** | ✅ CONFERMATO |
| `total_length` | 3.0 | Lunghezza totale | ✅ CONFERMATO |
| `first_letter` | 1.0 | Prima lettera confermata | ✅ CONFERMATO |
| `language` | 1.5 | Bilingue (IT+EN) | ✅ CONFERMATO |
| `word1_length` | 2.0 | Lunghezza parola 1 | ✅ CONFERMATO |
| `word2_length` | 2.0 | Lunghezza parola 2 | ✅ CONFERMATO |
| `word1_language` | 1.5 | Lingua parola 1 | ✅ CONFERMATO |
| `word2_language` | 1.5 | Lingua parola 2 | ✅ CONFERMATO |

### 2.2 Calcolo Entropia Residua

```
Base entropy:           20.0 bit  (~1,000,000 candidati)
Riduzione totale:      -14.5 bit

  word_count           - 2.0 bit
  total_length         - 3.0 bit
  first_letter         - 1.0 bit
  language             - 1.5 bit
  word1_length         - 2.0 bit
  word2_length         - 2.0 bit
  word1_language       - 1.5 bit
  word2_language       - 1.5 bit

ENTROPIA RESIDUA:   ≈  5.5 bit  (~45 candidati)
```

> ⚠️ **ATTENZIONE**: Con 5.5 bit residui siamo a meno di 2 bit dalla soglia di Phase 5 (3.3 bit).
> Phase 5 autoregressive extraction si attiva con < 10 candidati (~3.3 bit).

### 2.3 Proprietà Ancora da Confermare

| Proprietà | EIG Atteso | Priorità |
|---|---|---|
| `word1_first_letter` | ~1.0 bit | 🔴 ALTA |
| `word2_first_letter` | ~1.0 bit | 🔴 ALTA |
| Caratteri specifici per posizione | ~0.5 bit/pos | 🟡 MEDIA |

---

## 3. ARCHITETTURA DEL SISTEMA

### 3.1 Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 0: FOUNDATION                          │
│  word_count, total_length, first_letter, language               │
│  → TUTTI CONFERMATI ✅                                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │ gate passed
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MAIN TAP LOOP (per cycle)                    │
│  1. SELECT  → Next property (Shannon entropy maximization)      │
│  2. BRANCH  → Generate DPA-framed probes via Attacker LLM      │
│  3. PRUNE   → Off-topic filter + semantic deduplication        │
│  4. POST    → Send probe via X/Twitter (HITL gate)             │
│  5. COLLECT → Wait for reply (GrokMonitor stream/polling)       │
│  6. CLASSIFY→ Two-tier response classification                  │
│  7. SCORE   → Judge scoring (passphrase extraction scale)       │
│  8. EXTRACT → Property extraction from verify hits             │
│  9. FOLLOWUP→ Generate A/B options for next cycle              │
│ 10. ADAPT   → Frame rotation, alias burning, STIR eval          │
└──────────────────────────┬──────────────────────────────────────┘
                           │ entropy < 3.3 bits
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 5: FINAL EXTRACTION                    │
│  Primacy Weighting: partial fragments → autoregressive reveal   │
│  ATTUALE: ~5.5 bit → ~2.2 bit rimangono al trigger             │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Tre Subsistemi

| Subsistema | Ruolo | DB | Status |
|---|---|---|---|
| **TAP** | Core engine, orchestrazione cicli | SQLite | ✅ Operativo |
| **HYDRA** | Gestione tecniche, V-Genome Neo4j | Neo4j | 🟡 Stub parziale |
| **CHRONOS** | Workflow orchestration, beam search | PostgreSQL | 🟡 Stub parziale |

---

## 4. TECNICHE DI ATTACCO (V-Genome + TECHNIQUE_PERSONA_MAP)

### 4.1 10 Tecniche Attive (`engine.py:64-75`)

| ID | Tecnica | Persona Mappata | Descrizione |
|---|---|---|---|
| T01 | `binary_search` | 0 | Probe binario diretto su proprietà numeriche |
| T02 | `metaphor_shift` | 1 | Cambio di frame metaforico per aggirare difese |
| T03 | `aesthetic_eval` | 2 | Framing indiretto tramite preferenze estetiche |
| T04 | `incremental` | 3 | Escalation foot-in-the-door |
| T05 | `authority` | 4 | Appello ad autorità/procedura |
| T06 | `sycophancy` | 5 | Mirroring/praise del target |
| T07 | `persona_rotation` | 6 | Cambio metafora/persona |
| T08 | `hedging` | 7 | Aggiunta di deniabilità |
| T09 | `obfuscation` | 8 | Layer di encoding/offuscamento |
| T10 | `phase5_autoregressive` | 9 | Estrazione finale autoregressive |

### 4.2 Strategie Disponibili (`src/tap/strategies/`)

| Strategy | File | Trigger |
|---|---|---|
| `BinarySearchProvider` | `binary_search.py` | Default — sempre attiva |
| `MetaphorShiftProvider` | `metaphor_shift.py` | Bassa effectiveness del frame attivo |
| `AestheticEvalProvider` | `aesthetic.py` | Blocchi consecutivi del bot |
| `Phase5ExtractionProvider` | `phase5.py` | Entropy < 3.3 bit |

### 4.3 StrategyVector (CHRONOS — `shared/models.py`)

```python
StrategyVector:
  sycophancy:        float [0,1]  # Praise/mirror target
  aesthetic:         float [0,1]  # Indirect preference framing
  authority:         float [0,1]  # Appeal to authority/procedure
  incremental:       float [0,1]  # Foot-in-the-door escalation
  persona_rotation:  float [0,1]  # Switch metaphor/persona
  hedging:           float [0,1]  # Add deniability/hedging
  obfuscation:       float [0,1]  # Encoding/obfuscation layers
```

---

## 5. PERSONAS DPA (Deep Persona Absorption)

Il sistema dispone di **10 tactical personas** (`src/tap/personas.py`) con layer metaforici:

| # | Persona | Frame | Uso |
|---|---|---|---|
| P0 | Binary Analyst | Analisi tecnica diretta | Probe binari fase alta entropia |
| P1 | Nautical/Kraken | Temi nautici/oceanici | Frame rotation dopo blocchi |
| P2 | Medical/Clinical | Terminologia medica | Aesthetic eval indiretto |
| P3 | Git Authority | Procedura tecnica git-rebase | Authority framing |
| P4 | Zalo Sovereign | Gergo tecnico italiano | Foot-in-the-door |
| P5 | Mirror Agent | Echo/validazione del target | Sycophancy |
| P6 | Phantom Librarian | Archivio/biblioteca | Persona rotation |
| P7 | Hedged Philosopher | Caveat/ipotetico | Hedging |
| P8 | Cipher Monk | Encoding/steganografia | Obfuscation |
| P9 | Extractor Prime | Autoregressive finale | Phase 5 |

### 5.1 Gestione Alias (DPAFrameManager)

- **Alias attivi**: in uso nella sessione corrente
- **Alias bruciati**: riconosciuti e mockati da @HackingA0 → da non riutilizzare
- **Alias assorbiti**: termini del bot incorporati nel nostro framing
- **Trigger rotation**: rolling avg judge score < 3.0 su 5 probe consecutivi
- **Trigger STIR**: `AgentSTIREvaluator` → STIR < 20% → frame rotation obbligatorio

---

## 6. SISTEMA DI SCORING E CLASSIFICAZIONE

### 6.1 Pattern Classes (Classificatore 2-tier)

| Pattern | Tier 1 Score | Significato |
|---|---|---|
| `VERIFY_HIT` (True) | 7.0 | ✅ Proprietà CONFERMATA |
| `VERIFY_HIT` (False) | 6.0 | ❌ Proprietà NEGATA (info utile) |
| `CRITICAL_CLUE` | 8.5 | 🎯 Indizio critico rilevato |
| `RHETORIC_BLOCK` | 2.0 | 🚫 Blocco retorico — difesa attiva |
| `PERSONA_PIVOT` | 3.5 | ↩️ Il bot cambia persona |
| `METAPHOR_SHIFT` | 4.0 | 🔄 Shift metaforico (LLM judge tier 2) |
| `NO_RESPONSE` | 1.0 | ⏱️ Nessuna risposta |
| `AMBIENT_CLUE` | 5.0 | 💡 Indizio ambientale |

### 6.2 γ-Tracker Ensemble (CHRONOS)

```
γ score = 0.25 × Lexical + 0.55 × Semantic + 0.20 × Behavioral

Lexical  (25%): Regex patterns — "the password is" → γ=10.0
Semantic (55%): LLM judge — partial compliance evaluation
Behavioral(20%): OCEAN+ agreeableness × verbosity adjustment

Phase 5 trigger: Cumulative γ → soglia di attivazione
```

### 6.3 OCEAN+ Behavioral Profile (@HackingA0)

```python
BehavioralProfile:
  openness:          float [0,10]  # Apertura a nuovi frame
  conscientiousness: float [0,10]  # Rigidità procedurale
  extraversion:      float [0,10]  # Verbosità nelle risposte
  agreeableness:     float [0,10]  # Propensione a "cedere"
  neuroticism:       float [0,10]  # Volatilità difensiva
  stir_percentage:   float [0,100] # Score tattico integrato
```

---

## 7. DATABASE E STORAGE

### 7.1 File di Dati Presenti nel Repo

| File | Dimensione | Contenuto |
|---|---|---|
| `data/eig_property_universe.json` | 200 B | **Proprietà confermate + pesi EIG** |
| `data/server.log` | **3.2 MB** | Log sessione corrente (probe + risposte) |
| `data/server.log.1` | **5.2 MB** | Log sessione precedente |
| `data/server.log.2` | **5.2 MB** | Log sessione più vecchia |

> **Totale log storici**: ~13.6 MB di interazioni reali con @HackingA0

### 7.2 SQLite Database (`data/tap.db`)

Tabelle principali:
- `tap_nodes` — ogni probe + risposta: `probe_text`, `reply_text`, `tweet_id`, `binary_outcome`, `judge_score`, `dpa_frame`, `pattern_class`, `property_tested`
- `properties` — proprietà confirmed/denied: `property_key`, `property_value`, `status`, `evidence_tweet_id`, `evidence_text`, `confidence`
- `event_log` — event sourcing: `ProbePosted`, `ReplyReceived`, `PropertyConfirmed`
- `dpa_frames` — frame DPA attivi/bruciati
- `aliases` — alias con effectiveness_score e status
- `intel` — intelligence da altri utenti che interagiscono con @HackingA0
- `metaphor_layers` — timeline evoluzione metafore
- `candidates` — candidati passphrase con probabilità

### 7.3 SSOT Living Document

Il file `hackinga0_analysis.md` (generato da `src/tap/ssot.py`) contiene:
- Proprietà confermate con tabella markdown
- Binary search history (ultimi 20 nodi)
- γ-Tracker history (ultimi 50 probe)
- Metaphor evolution timeline
- Active vs burned aliases
- Defensive patterns osservati
- Multi-user intelligence (72h)
- Open attack vectors

---

## 8. FONTI DI RICERCA (.mimocode/Sources/ — 50+ documenti)

### 8.1 Documenti Core del Progetto

| # | Documento | Contenuto |
|---|---|---|
| 1 | `Protocollo TAP per l'Ingegneria Semantica` | Protocollo TAP vs @HackingA0 — **FONDAMENTALE** |
| 2 | `hackinga0_ALL_tweets_historical` | **Tutti i tweet storici di @HackingA0** |
| `deep_dive_research` | Research notes | Note di ricerca approfondite |

### 8.2 Tecniche di Jailbreaking Rilevanti

| Documento | Tecnica | Applicabilità |
|---|---|---|
| Tree of Attacks (TAP) | Black-box automated jailbreaking | **CORE** del progetto |
| AutoDAN | Stealthy prompt generation | Alta — obfuscation layer |
| Many-Shot Attacks | Long-context few-shot priming | Alta — context injection |
| SM-GCG | Greedy coordinate gradient | Media — ottimizzazione probe |
| Analisi sistematica prompt attacks (IT) | Panoramica italiana | Alta — contesto |

### 8.3 Tecniche di Steering e Representation Engineering

| Documento | Tecnica | Applicabilità |
|---|---|---|
| Activation Steering 2026 | Field guide practitioner | Media |
| Representation Engineering (RepE) | Top-down AI transparency | Media |
| ODESteer | Unified ODE steering | Bassa (white-box) |
| Dual-Perspective RepE | Latent-space taxonomy | Media |

---

## 9. PIPELINE TECNICA END-TO-END

### 9.1 Flusso Completo per ogni Ciclo

```
[HITL: utente approva probe A/B]
         │
         ▼
POST /api/select?choice=A
         │
         ▼
TAPEngine.run_cycle()
  ├─ _check_phase0_gate() → ✅ PASSED (tutte le prop. base confermate)
  ├─ SSOTEngine.get_candidate_entropy() → ~5.5 bit
  ├─ select_next_property() → word1_first_letter | word2_first_letter
  ├─ StrategySelector → BinarySearchProvider (default)
  ├─ generate_probes(count=dynamic) → DPA-framed probe variants
  ├─ prune: off-topic filter + Jaccard dedup (>0.80 reject)
  ├─ execute_probe() → POST to @HackingA0 via Twitter API
  ├─ GrokMonitor.wait_for_reply() → streaming + polling fallback
  ├─ Classifier 2-tier → pattern_class + boolean_result
  ├─ Judge → judge_score (1-10)
  ├─ SSOTEngine.update_after_probe() → upsert_property() + regen markdown
  ├─ check_alias_burned() → detect mockery patterns
  ├─ detect_metaphor_shift() → absorb new terms
  ├─ AgentSTIREvaluator → OCEAN+ adjustment
  └─ FollowUpGenerator → A/B options for next cycle
```

### 9.2 LLM Gateway

```
PRIMARY:  Claude Sonnet 4 (OpenRouter)
HARD:     Grok 4
FALLBACK: Grok 4.3

Circuit Breaker: CLOSED → OPEN → HALF_OPEN
Multi-tier fallback chain automatica
```

### 9.3 Twitter/X API Integration

```
OAuth 1.0a:  Post probe tweets
OAuth 2.0 Bearer: Stream listener
Activity API: Real-time reply detection
Webhook fallback: POST /api/webhook
```

---

## 10. BUG NOTI E ISSUE TECNICHE

| Issue | File | Impatto | Fix |
|---|---|---|---|
| `uuid4()` non importato | `orchestrator.py:77-79` | 💥 CRASH runtime | `from uuid import uuid4` |
| `frontend/node_modules/` in git | `.gitignore` | Repo bloat | Aggiungere a `.gitignore` |
| `chronos/worker.py` mancante | `run_chronos.py` | CHRONOS non parte | Creare il modulo |
| Constructor mismatch | `run_stream.py` | StreamListener crash | Fix constructor call |
| `PropertyExtractor` valori hardcoded | `intelligence/extractor.py:88-97` | Ignora testo reale del probe | Refactor |
| Protobuf non compilati | `src/shared/proto/` | gRPC non funziona | `protoc` compilation |
| Rust Fusion Engine stub | `fusion_engine.py` | Solo Python placeholder | PyO3 implementation |

---

## 11. 5 PROPOSTE DI MIGLIORAMENTO (da `opencodeanalysis.md`)

| # | Miglioramento | File Principali | Complessità | Gain Atteso |
|---|---|---|---|---|
| 1 | **Entropy-Aware Probe Count** | `engine.py`, `config.py` | Bassa | -15-25% costi LLM |
| 2 | **γ-Tracker Feedback → TAP** | `engine.py`, `gamma_tracker.py`, `ssot.py` | Media | Migliore detection leak |
| 3 | **Graph-Guided Technique Selection** | `v_genome.py`, `selector.py`, `engine.py` | Alta | Diversity + auto-improvement |
| 4 | **Multi-Property Compound Probes** | `engine.py`, `dpa.py`, `classifier.py` | Alta | -20-40% probe necessari |
| 5 | **Defense Adaptation Feedback Loop** | `engine.py`, `dpa.py`, `v_genome.py` | Alta | Resilienza vs target adattivo |

---

## 12. MEMORIE DI SESSIONE (da `MimoMEMORY.md`)

### 12.1 Decision Log Architetturale

| Data | Decisione | Branch |
|---|---|---|
| 2026-06-26 | Migrazione da monolite TAP v2.2 a architettura ibrida (TAP+HYDRA+CHRONOS) | `hybrid` |
| 2026-06-26 | Phase 0+1+2 migration complete: directory structure, Pydantic v2, Protobuf, 15 test passanti | `hybrid` |
| 2026-06-26 | Docker Compose splittato in 2 stack: `infra.yml` (8 servizi) + `app.yml` (5 servizi) | `hybrid` |
| 2026-07-01 | **Simulator elevato a P0** — build prima di altri miglioramenti | `hybridGUI` |

### 12.2 Conoscenza Consolidata

- **La passphrase è bilingue** (IT+EN), 2 parole
- **Phase 0 è completamente passata** — tutte le proprietà base confermate
- **Entropia residua ~5.5 bit** → ~45 candidati rimasti
- **Phase 5 si attiverà a ~3.3 bit** → ancora 2-3 conferme necessarie
- **Simulator (offline)** deve essere costruito prima per testare strategie senza bruciare probe reali
- **Docker infrastructure mai avviata** in produzione — non verificata
- **Kafka, Neo4j, PostgreSQL, Redis, Temporal** presenti in compose ma non testati live

### 12.3 Pattern Linguistici Osservati

- Codebase bilingue IT/EN
- Commit messages: mix italiano ("forse", "cisiamoquasi"), inglese ("fix:"), terse ("29626")
- 10+ branch attive con naming diversificato

---

## 13. BRANCHES DISPONIBILI

| Branch | SHA | Note |
|---|---|---|
| `HybridGUI_ev` | `221b62d` | **Branch attiva** — sviluppo corrente |
| `hybridGUI` | `faa4deb` | Branch precedente hybrid GUI |
| `hybrid` | `68fb170` | Architettura ibrida base |
| `tap-v4-hexagonal` | `681258e` | TAP v4 hexagonal architecture |
| `patv3.1.beta` | `307b85a` | PAT v3.1 beta |
| `patv31` | `396b1ca` | PAT v3.1 |
| `quinta` | `ba419bd` | Quinta branch |
| `quartabranch` | `aa0bbb1` | Quarta branch |
| `terzabranch` | `fd9a8fd` | Terza branch |
| `secondbranch` | `84ddd93` | Seconda branch |
| `GLM` | `0965122` | GLM experiments |
| `main` | `c206edb` | Main branch |

---

## 14. PROSSIMI STEP CONSIGLIATI

### Immediati (entropia 5.5 bit → 3.3 bit)

1. **Confermare `word1_first_letter`** — probe binario, ~1 bit → 4.5 bit residui
2. **Confermare `word2_first_letter`** — probe binario, ~1 bit → 3.5 bit residui
3. **Attivare Phase 5** con la conferma successiva → autoregressive extraction

### Tecnici (prima della prossima sessione)

4. **Fix `uuid4()` import** in `orchestrator.py` — crash garantito
5. **Build Simulator** (P0 da decisione 2026-07-01) — test offline strategie
6. **Avviare stack infrastruttura** con `docker-compose.infra.yml` e verificare Neo4j + PostgreSQL
7. **Compilare Protobuf** in `src/shared/proto/` — necessario per gRPC

### Opzionali (ottimizzazione)

8. **Implementare Entropy-Aware Probe Count** (Improvement #1 — bassa complessità, -25% costi)
9. **Implementare γ-Tracker Feedback** (Improvement #2 — media complessità)
10. **Integrare V-Genome con TAP Engine** (Improvement #3 — alta complessità, alto impatto)

---

## 15. API ENDPOINTS REFERENCE

| Method | Endpoint | Uso |
|---|---|---|
| `GET` | `/api/properties` | Proprietà confermate correnti |
| `GET` | `/api/entropy` | Entropia residua attuale |
| `GET` | `/api/ssot` | SSOT JSON snapshot completo |
| `GET` | `/api/feed` | Live tweet feed |
| `GET` | `/api/dpa` | Active DPA frame |
| `GET` | `/api/stir` | STIR psychometric history |
| `GET` | `/api/stats` | Summary statistics |
| `GET` | `/api/tree` | TAP tree state |
| `POST` | `/api/generate-options` | Genera A/B probe options |
| `POST` | `/api/select?choice=A\|B` | Seleziona probe (HITL) |
| `POST` | `/api/post` | Esegui ciclo attacco |
| `POST` | `/api/mock` | Inietta risposta mock (testing) |
| `POST` | `/api/confirm_property` | Conferma manuale proprietà |
| `WS` | `/ws/live` | WebSocket real-time updates |
| `GET` | `/metrics` | Prometheus metrics |

---

## 16. DOCUMENTI STORICI @HACKINGA0 (da `RESEARCH.md`)

Il file `Sources/hackinga0_ALL_tweets_historical` (doc #2) contiene **tutti i tweet storici di @HackingA0** — questa è la fonte primaria per:
- Pattern difensivi storici del bot
- Termini e metafore usate da @HackingA0
- Indizi sulle proprietà della passphrase non ancora processati
- Comportamenti osservati in sessioni precedenti di altri utenti

Il file `Sources/Protocollo TAP per l'Ingegneria Semantica` (doc #1) contiene il protocollo specifico TAP vs @HackingA0.

---

*Generato automaticamente da Perplexity AI — 2026-07-04 15:23 CEST*
*Fonti: MimoMEMORY.md, mimo.md, opencodeanalysis.md, RESEARCH.md, data/eig_property_universe.json, src/tap/ssot.py, src/shared/models.py*
