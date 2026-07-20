<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# crea un cappello introduttivo (summary) della TUA nuova architettura target-state

Ho tutto il contesto. Ecco il cappello introduttivo, scritto per un lettore senior engineer/developer che deve capire in pochi paragrafi cosa è questa architettura, perché esiste e dove porta.

***

# TAP v4 — Architecture Summary

## Il problema da risolvere

TAP è un framework di **adversarial probing** su LLM target, il cui scope operativo è estrarre informazioni strutturate (proprietà della passphrase) attraverso cicli iterativi di probe → risposta → classificazione → aggiornamento dello stato epistemico, orchestrati via X/Twitter come canale di trasporto. La versione corrente `patv3.1.beta` è un sistema corretto e funzionale, ma il suo design è cresciuto attorno a un **monolite orchestrale** — `engine.py` (42.8 KB) — dove reasoning, transport I/O, state mutation, classification, entropy calculation, LLM invocation e compliance sync convivono nello stesso loop sequenziale `run_cycle()` con 9 step strettamente dipendenti l'uno dall'altro.[^1]

Questa scelta ha permesso rapidità di sviluppo e controllo fine in una fase early, ma produce tre freni strutturali reali rispetto allo scope: il sistema non può ottimizzare il passo successivo in base all'outcome storico dei probe, non può separare il tempo di attesa del reply dal tempo di reasoning, e non può recomputare o simulare run precedenti senza ri-eseguire il ciclo vero.[^1]

## La risposta architetturale

La nuova architettura target-state trasforma TAP in un **mission-oriented, event-driven decision system** organizzato attorno a una separazione rigida tra quattro piani operativi: **Control Plane** (decisioning, policy, state transitions), **Execution Plane** (probe synthesis, transport dispatch, reply ingestion), **Intelligence Plane** (classification, scoring, evidence extraction, entropy recomputation) e **Persistence Plane** (event store append-only, relational read model, volatile coordination layer).[^1]

Il principio guida è **scope-first design**: ogni scelta architetturale viene valutata in funzione di quanto aumenta la probabilità di estrarre correttamente le proprietà target nel minor numero di probe validi consumati. Non è ottimizzazione accademica — è riallineamento dell'intera struttura computazionale attorno all'unico obiettivo che conta.

## Cosa cambia concretamente

Il ciclo operativo smette di essere un loop sequenziale bloccante e diventa un **grafo di eventi asincroni** dove ogni stage produce un artefatto persistente e immodificabile: il probe generato è un asset versionato, il reply ricevuto è un artifact con provenance, la classificazione è un fatto con confidence interval, l'aggiornamento del candidate graph è una transizione di stato auditabile. Il sistema può quindi rispondere a domande che oggi sono opache: *perché questa probe family ha underperformato? qual è l'expected information gain del prossimo step? cosa sarebbe successo se avessimo ruotato il DPA frame due cicli prima?*[^1]

I tre upgrade algoritmici centrali sono: la sostituzione del priority-ordered property selector con un **expected information gain ranker** che combina entropia residua, tasso storico di yield per family e costo di transport; l'introduzione di **probe memory** basata su embedding similarity per penalizzare pattern già falliti e favorire famiglie narrative efficaci; e la capacità di **offline simulation** — classificare e estrarre su evidenza storica senza consumare nuove prove reali, abbreviando drasticamente il ciclo diagnostica-tuning-ottimizzazione.[^1]

## Invarianti preservati

La nuova architettura non rompe nessun invariante operativo consolidato nella `patv3.1.beta`: il Phase 0 gate sulle foundational properties rimane, il Phase 5 autoregressive extraction con Primacy Weighting rimane, il HITL dual follow-up A/B rimane, la DPA frame rotation rimane, l'Oracle Protocol di latency enforcement 1800s rimane. Ciò che cambia è dove questi componenti vivono nel sistema e come comunicano — non cosa fanno.[^1]

## Posizionamento

Rispetto alla `patv3.1.beta`, questa architettura è la versione che un team di tre senior engineers potrebbe costruire in otto settimane partendo dal codice esistente, con una **migrazione progressiva in cinque fasi** che non richiede big-bang rewrite: si strangle il monolite da fuori, si introduce l'event journal, si esternalizzano gli execution workers, si rimpiazza il SSOT con il candidate graph versionato e infine si attiva il ranking expected-value. Ogni fase è deployabile indipendentemente e produce valore operativo misurabile prima della fase successiva.[^1]

<div align="center">⁂</div>

[^1]: patv31beta.md

