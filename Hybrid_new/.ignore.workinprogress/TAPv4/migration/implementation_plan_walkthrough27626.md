# Walkthrough — Migrazione Architetturale a APP_Opzione_Ibrida

Questo documento riassume le attività completate per descrivere le linee guida di sviluppo destinate agli AI Agent Developers all'interno del framework ibrido HYDRA + CHRONOS.

## Cambiamenti Effettuati

### 1. Creazione delle Linee Guida di Sviluppo
* Creato il file locale [agent.md](file:///d:/PROGETTI/TAPv4/agent.md) che funge da riferimento principale per la progettazione, sviluppo e manutenzione degli agenti nell'architettura ibrida.
* Il documento dettaglia:
  * **La transizione concettuale:** Il superamento di `agents.py` in favore del **Behavioral Profiler (OCEAN+)** e del tracciamento continuo della **Partial Compliance ($\gamma$)**.
  * **Le 8 Regole d'Oro per gli sviluppatori:** Standard e vincoli tecnici rigorosi per evitare regressioni o violazioni architetturali.
  * **I Core Components:** Il funzionamento dettagliato di HYDRA (Rust Fusion Engine, V-Genome in Neo4j) e CHRONOS (Temporal Workflows, CoAT Engine).
  * **Il Workflow in 5 Fasi:** Dalla stesura dei contratti dati (Pydantic/Protobuf) fino alla documentazione finale.
  * **La Valutazione Matematica:** Formule per il calcolo della riduzione dell'Entropia e la ponderazione dinamica del $\gamma$-Tracker basata sulla strategia CoAT attiva.
  * **La Tabella di Mapping:** Una guida file-per-file per la migrazione del vecchio codice di TAP v2.2.

### 2. Consolidamento delle Decisioni di Design (tramite /grill-me)
Le seguenti decisioni strutturali sono state integrate e documentate direttamente all'interno delle specifiche:
* **Handoff Event-Driven:** HYDRA lancia l'evento `TargetVulnerableDetected` via Protobuf su Kafka.
* **Database CDC & Replication:** CHRONOS persiste i dati su PostgreSQL e una pipeline CDC (es. Debezium) sincronizza periodicamente le modifiche verso il database Neo4j (V-Genome) di HYDRA.
* **Temporal Signals con Timeout:** HITL non bloccante in Temporal che esegue automaticamente la raccomandazione del CoAT Engine in caso di inattività dell'utente.
* **Circuit Breaker Distribuito:** Sincronizzazione dello stato del Circuit Breaker di `LLMClient` su Redis/PostgreSQL condiviso.

---

## Validazione ed Ispezione
Il file `agent.md` è stato ispezionato e validato localmente:
1. **Verifica dei Link:** Tutti i riferimenti interni ed i collegamenti con i file di schema o di specifica sono cliccabili e corretti.
2. **Coerenza Sintattica:** La sintassi Protobuf, Pydantic v2 e le formule matematiche $\text{\LaTeX}$ inserite nel testo sono state convalidate per assicurare la massima leggibilità.
