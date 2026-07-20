# Audit Moduli TAP v2.2 → APP_Opzione_Ibrida

**Data:** 27 giugno 2026  
**Branch target:** `hybrid`  
**Fonte:** `framework/agent.md`, `framework/TAPv4/migration/APP_Opzione_Ibrida_Tech_Specs.md`

---

## Scopo

Documentare lo stato dei moduli TAP v2.2, identificare debito tecnico e mappare ogni componente al nuovo sistema ibrido HYDRA + CHRONOS.

---

## 1. Moduli Riutilizzabili (minime modifiche)

| Modulo | Path | Destinazione | Modifica richiesta |
|---|---|---|---|
| `llm_client.py` | `src/tap/llm_client.py` | LLM Gateway condiviso | + gRPC streaming + Circuit Breaker su Redis/PostgreSQL |
| `config.py` | `src/tap/config.py` | Settings unificati | + sezioni `[HYDRA]` e `[CHRONOS]` |
| `logger.py` | `src/tap/logger.py` | Structured logging | + Kafka appender opzionale |
| `x_client.py` | `src/tap/x_client.py` | `TwitterXPort(SocialPort)` | Estrarre come Hexagonal Port in `src/adapters/social/` |
| `stream_listener.py` | `src/tap/stream_listener.py` | CHRONOS reply detection | Minimal; integrare con bus eventi |
| `prompts.py` | `src/tap/prompts.py` | Template base | HYDRA: + M2S+ templates; CHRONOS: + CoAT templates |
| `models.py` | `src/tap/models.py` | Pydantic contracts legacy | + nuovi modelli in `src/shared/models.py`; import compat |
| `db.py` | `src/tap/db.py` | Backward compat TAP | Mantenere; CHRONOS usa asyncpg/PostgreSQL |
| `oauth.py` | `src/tap/oauth.py` | OAuth per tutti gli adapter | Riutilizzare as-is |
| `api.py` | `src/tap/api.py` | API Gateway | Refactor: router `/hydra/*` + `/chronos/*` |

---

## 2. Moduli da Refactor Significativo

| Modulo | Problema chiave | Destinazione ibrida |
|---|---|---|
| `engine.py` | Monolitico, no beam search, no γ | HYDRA Fusion Engine + CHRONOS Beam Search |
| `dpa.py` | Bug `{property}` placeholder, stato in-memory | `behavioral_profiler.py` + `personas.py` esteso |
| `followup.py` | A/B HITL manuale | `coat_engine.py` + Strategy Selector |
| `classifier.py` | Regex + LLM binario | γ-Tracker layer 1 (lexical) |
| `judge.py` | Score arbitrario 1-10 | γ-Tracker layer 2 (semantic) |
| `grok_monitor.py` | AsyncOpenAI diretto (viola Regola 1) | Unificare via LLM Gateway |
| `phase0.py` | Gate mismatch 5 vs 3 proprietà, AsyncOpenAI diretto | HYDRA Vulnerability Scanner + CHRONOS Entropy Gate |
| `ssot.py` | Markdown statico (viola Regola 8) | Event Sourcing Kafka + PostgreSQL + ClickHouse |
| `agents.py` | Keyword counting naive per OCEAN | `behavioral_profiler.py` OCEAN+ LLM-based |
| `strategies/*.py` | Non collegati all’engine | Feature providers per HYDRA Fusion Engine |
| `prompt_sanitiser.py` | Regex-based, no contestuale | HYDRA Obfuscation Layer |

---

## 3. Moduli Deprecati

| Modulo | Motivo | Sostituto |
|---|---|---|
| `setup_db.py` | Schema inline in `db.py` | `migrations/` Alembic |
| `inspect_data.py` | Utility ad-hoc | ClickHouse dashboard |
| `remedy_implementation/` | WIP non strutturato | Branch `experiments/` isolati |

---

## 4. Debito Tecnico Critico

1. **Viola Regola 1:** `grok_monitor.py` inizializza `AsyncOpenAI` diretto.
2. **Viola Regola 2:** `db.py` usa SQLite come primary DB; CHRONOS richiede PostgreSQL/asyncpg.
3. **Viola Regola 8:** `ssot.py` persiste lo stato in markdown (`hackinga0_analysis.md`).
4. **Viola Regola 3:** molti log usano f-string invece di chiavi strutturate con `attack_id`/`probe_id`.
5. **Dipendenze circolari:** `engine.py` importa molti moduli e mantiene stato globale.
6. **Mancanza di contract layer chiaro:** modelli Pydantic sparsi tra `models.py` e singoli moduli.

---

## 5. Note per Implementazione

- Iniziare sempre da `src/shared/models.py` e `src/shared/proto/` per chiudere i contratti.
- Non modificare logica `src/tap/` esistente finché i bridge adapter in `src/adapters/compat/` non sono stabili.
- Il Circuit Breaker di `llm_client.py` è in-memory; deve diventare distribuito tramite Redis/PostgreSQL.
- Il `Settings` attuale deve espandersi con sezioni HYDRA/CHRONOS senza rompere i campi esistenti.
