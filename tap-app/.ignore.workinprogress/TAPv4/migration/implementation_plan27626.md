# Creazione della Documentazione Tecnica agent.md per APP_Opzione_Ibrida

Questo piano descrive l'implementazione e la stesura del file `agent.md` per guidare gli sviluppatori (AI Agent Developers) nella migrazione e gestione degli agenti nel nuovo ecosistema ibrido HYDRA + CHRONOS. La documentazione integrerà le 8 Regole d'Oro per gli sviluppatori, le specifiche architetturali ed esagonali dei componenti e le scelte di design concordate durante la sessione di cross-examination (/grill-me).

## User Review Required

Nessun elemento bloccante rilevato. Le scelte di design concordate sono state formalizzate nel piano e saranno incorporate nel documento finale `agent.md`:
* **Handoff (HYDRA → CHRONOS):** Asincrono e guidato da eventi tramite pubblicazione su Kafka dell'evento `TargetVulnerableDetected`.
* **Contratto Dati:** Protocol Buffers (.proto) per garantire la coerenza tipologica e strutturale tra Rust (HYDRA) e Python (CHRONOS).
* **Feedback Loop (CHRONOS → HYDRA):** Scrittura di persistenza dei dati di estrazione su PostgreSQL con worker di replica / pipeline CDC (es. Debezium) per sincronizzare gli aggiornamenti su Neo4j (V-Genome).
* **Bilanciamento γ:** Calcolo dinamico dello score di Partial Compliance basato sulla strategia CoAT (Chain-of-Attack-Thought) attiva.
* **HITL in Temporal.io:** Segnali asincroni con timeout e fallback automatico per evitare il blocco permanente del workflow.
* **Circuit Breaker:** Stato centralizzato persistito su database condiviso (Redis/PostgreSQL).

## Open Questions

Non ci sono domande aperte residue. Tutte le scelte fondamentali sono state delineate ed approvate durante il colloquio `/grill-me`.

## Proposed Changes

### Documentazione Tecnica per AI Agent Developers

#### [NEW] [agent.md](file:///d:/PROGETTI/TAPv4/agent.md)
Creazione del documento completo contenente:
1. **Visione della Migrazione:** Transizione da `agents.py` (naive) al Behavioral Profiler (OCEAN+) con scaling continuo della Partial Compliance ($\gamma \in [0, 10]$).
2. **Le 8 Regole d'Oro per AI Agent Developers:**
   * Utilizzo esclusivo di `LLMClient.generate()` (mai `openai.AsyncOpenAI` direttamente).
   * Uso esclusivo di `asyncpg` per PostgreSQL (vietato SQLite per CHRONOS).
   * Correlation IDs obbligatori (`cycle_id` e `probe_id`) in tutti i log.
   * Standard Pydantic v2 con definizioni `Field()`.
   * Gestione rigorosa dei Timeout per le chiamate esterne.
   * Tipizzazione statica sicura con Mypy Strict.
   * Circuit Breaker centralizzato e persistito per il gateway LLM.
   * Event Sourcing con Kafka per CHRONOS in sostituzione dei file markdown statici.
3. **Core Components:**
   * **HYDRA (Frontend):** Dettagli sul V-Genome (Neo4j) e sul Fusion Engine in Rust.
   * **CHRONOS (Backend):** Workflow durabili di Temporal.io e il CoAT Engine per ragionamento multi-turn.
4. **Workflow di Sviluppo Feature:** Il processo a 5 fasi (Contratto, Implementazione Core, Unit Test, Integration Test, Documentazione).
5. **Metriche di Valutazione:** Analisi dell'entropia informazionale e tracking del leakage tramite $\gamma$-Tracker.
6. **Tabelle di Mapping:** Corrispondenza e transizione dei moduli da TAP v2.2 a HYDRA/CHRONOS.

---

## Verification Plan

### Automated Tests
* Validazione formale del markdown del file `agent.md` per assicurare che tutti i link interni ed esterni (ad esempio file locali e repository esagonali) siano corretti e formattati secondo le linee guida.

### Manual Verification
* Revisione della documentazione con il Principal Engineer per confermare l'allineamento con lo standard esagonale del repository `tap-v4-hexagonal` e la conformità con le 8 Regole d'Oro.
