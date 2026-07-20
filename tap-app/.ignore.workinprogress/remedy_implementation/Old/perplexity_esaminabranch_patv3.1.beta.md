<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# esamina la branch "patv3.1.beta" di questo mio repo: [https://github.com/CarlSamma/framework](https://github.com/CarlSamma/framework) . Genera overview architetturale dettagliato

Ecco l'overview architetturale completo del branch [`patv3.1.beta`](https://github.com/CarlSamma/framework/tree/patv3.1.beta). Il documento è allegato sopra.

***

## Cos'è TAP Framework

**TAP Framework** è un sistema automatizzato di adversarial probing che implementa il metodo *Tree of Attacks with Pruning* per estrarre una passphrase da `@HackingA0`, un bot Agent Zero su Twitter/X con architettura difensiva a 3 agenti (Governor → Analyst → Rhetoric). Il metodo centrale è la **ricerca binaria guidata dall'entropia di Shannon**: ogni sonda estrae 1 bit, portando alla ricostruzione della passphrase in ~20–30 turni riusciti.

## Struttura a 10 Layer

Il codebase è tutto in `src/tap/` — un singolo package Python con responsabilità nettamente separate:


| Layer | Modulo chiave | Responsabilità |
| :-- | :-- | :-- |
| **API/Transport** | `api.py` | FastAPI ASGI, WebSocket real-time, dashboard HTML |
| **Core Engine** | `engine.py` | Orchestratore ciclo TAP a 9 step (42 KB) |
| **LLM Gateway** | `llm_client.py` | Unified OpenRouter client con circuit breaker e fallback |
| **DPA Framing** | `dpa.py` + `agents.py` | Deep Persona Absorption, 10 Tactical Personas Layer 8–11 |
| **Intelligence** | `classifier.py` + `judge.py` | Classificazione 2-tier (regex → LLM) + scoring 1-10 |
| **SSOT** | `ssot.py` | Stato epistemico, calcolo entropia Shannon, Markdown gen |
| **Persistence** | `db.py` | SQLite WAL asincrono via aiosqlite |
| **Twitter/X** | `x_client.py` + `stream_listener.py` | Triple OAuth, posting, streaming API |
| **Strategie** | `strategies/` | BinarySearch, MetaphorShift, Phase5, PropertySelector |
| **HITL** | `followup.py` | Genera opzioni A/B per la decisione umana |

## Novità del Branch `patv3.1.beta`

Il branch introduce l'**architettura multi-agent v3.1** con tre nuovi agenti in `agents.py`: `AgentIntelExtractor` (sblocca automaticamente il Phase 0 Gate analizzando tweet storici), `AgentSTIREvaluator` (valutazione semantica della minaccia), `AgentDPAFManager` (versione agentizzata del gestore frame). In parallelo, `LLMClient` unificato sostituisce 5 istanze `AsyncOpenAI` sparse introducendo circuit breaker, retry con exponential backoff e model fallback (Grok-4.3 → Claude Sonnet-4).

## ⚠️ Nota Sicurezza Urgente

Il file `Copia.env.txt` nel branch contiene **credenziali live in chiaro**: Twitter OAuth 1.0a tokens, OAuth 2.0 tokens e l'API key OpenRouter. È necessario **invalidare e ruotare immediatamente tutte le chiavi** esposte e aggiungere `Copia.env.txt` al `.gitignore`.

