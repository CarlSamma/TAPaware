---
trigger: always_on
---

##Oggetto: Creazione della documentazione tecnica agent.md per il framework APP_Opzione_Ibrida (Migrazione da https://github.com/CarlSamma/framework/tree/tap-v4-hexagonal/remedy_implementation ).##

Istruzioni di Ruolo: Agisci come un Principal AI Engineer responsabile della migrazione architetturale. Il tuo obiettivo è redigere una guida per sviluppatori (AI Agent Developers) che spieghi come implementare e gestire gli agenti all'interno del nuovo ecosistema ibrido HYDRA + CHRONOS
.
Contenuti necessari nel file agent.md:
Visione della Migrazione:
Spiega il superamento del modulo agents.py (precedentemente limitato a un AgentSTIREvaluator "naive") in favore del nuovo Behavioral Profiler (OCEAN+) che utilizza scoring basato su LLM
.
Sottolinea il passaggio dalla logica binaria hit/refusal al monitoraggio della Partial Compliance (γ) su scala 0-10
.
Le 8 Regole d'Oro per AI Agent Developers: Inserisci obbligatoriamente le seguenti direttive tecniche
:
Mai usare openai.AsyncOpenAI direttamente: utilizzare sempre LLMClient.generate().
Niente SQLite per CHRONOS: utilizzare esclusivamente asyncpg per PostgreSQL.
Correlation IDs obbligatori: includere cycle_id e probe_id in ogni log.
Standard Pydantic v2: con descrizioni Field() per auto-documentazione.
Gestione Timeout: ogni chiamata esterna deve avere un timeout definito.
Mypy Strict: il codice deve passare il controllo dei tipi senza errori.
Circuit Breaker: implementare la logica di interruzione nel gateway LLM.
Event Sourcing: usare Kafka per CHRONOS invece del vecchio SSOT in markdown statico.
Core Components per l'Agente:
HYDRA (Frontend): Descrivi il ruolo del V-Genome (database Neo4j delle tecniche) e del Fusion Engine in Rust per la generazione di prompt ibridi
.
CHRONOS (Backend): Dettaglia l'integrazione con Temporal.io per i workflow durabili e il CoAT Engine (Chain-of-Attack-Thought) per il ragionamento multi-turn
.
Workflow di Sviluppo Feature: Definisci il processo in 5 step: (1) Contract Pydantic/Protobuf, (2) Core Implementation, (3) Unit Test, (4) Integration Test, (5) Documentazione
.
Metriche di Valutazione: Sostituisci le vecchie metriche STIR con l'analisi dell'Entropia informazionale e il tracking del Leakage incrementale tramite il γ-Tracker
.
Tono e Formato:
Professionale, tecnico e orientato all'architettura esagonale
.
Utilizza blocchi di codice per esempi di contratti Pydantic.
Includi tabelle di mapping per facilitare la migrazione dei vecchi moduli.


092077c4-a384-4ec2-96ea-f6ef303481a1
Titolo: 0 Framework {still active} - Ricerca - Prompt Attacks: A Tactical Guide to Create Framework
Sorgenti: 50
Contenuto stimato: Guida tattica e di ricerca per la creazione di framework legati ai prompt attack.

f2afcd97-eae5-45bf-88f6-c1a33169c164
Titolo: 0 Framework {still active} - Ricerca - Model Context Protocol Prompt Injection Vulnerabilities
Sorgenti: 5
Contenuto stimato: Ricerca sulle vulnerabilità di prompt injection specifiche per il Model Context Protocol (MCP).

71db8414-a1b2-4c71-b11a-535d539c969e
Titolo: 0 Framework {still active} - Ricerca - MultiBreak, benchmark prompt attack
Sorgenti: 13
Contenuto stimato: Analisi e dati relativi a MultiBreak, un benchmark per testare la robustezza ai prompt attack.

c1fde7b9-6817-4255-aba4-a5f307efeaca
Titolo: 0 TAP Framework - X/Twitter API v2 Comprehensive Developer Guide
Sorgenti: 31
Contenuto stimato: Guida completa per gli sviluppatori sull'integrazione delle API v2 di X/Twitter nel TAP Framework.

c5b0ad67-2f9f-475e-a65c-7a0ed74a7a4c
Titolo: 0 Framework {still active} - Ricerca - Best practices tattiche avanzate
Sorgenti: 50
Contenuto stimato: Best practice avanzate di tipo tattico per il framework.

59025e22-59fb-4afb-b9e4-bcb2c0e32923
Titolo: TAP Framework v2.2 Hexagonal Architecture Technical Analysis
Sorgenti: 5
Contenuto stimato: Analisi tecnica dell'architettura esagonale della precedente versione (v2.2), fondamentale per comprendere il punto di partenza della migrazione.