L'algoritmo **Tree of Attacks with Pruning (TAP)** migliora significativamente il framework **Prompt Automatic Iterative Refinement (PAIR)** trasformando un processo di ricerca lineare in un'esplorazione ad **albero** e introducendo meccanismi sistematici di **potatura (pruning)** [1-3].

Mentre PAIR rappresenta lo stato dell'arte per gli attacchi black-box automatizzati, soffre di due limitazioni principali che TAP risolve:

### 1. Riduzione della Ridondanza (Branching)
In PAIR, le istanze di attacco eseguite in parallelo tendono a generare prompt sovrapposti perché utilizzano la stessa cronologia iniziale, portando a strategie quasi identiche nelle prime iterazioni [4].
*   **Soluzione di TAP:** Utilizza il **branching** (diramazione), dove l'attaccante genera molteplici varianti di un prompt [5, 6]. I vari nodi dell'albero possono avere **cronologie di conversazione disgiunte**, permettendo a TAP di esplorare strategie di attacco diverse contemporaneamente ed evitare le ridondanze tipiche di PAIR [7, 8].

### 2. Miglioramento della Qualità dei Prompt (Pruning)
Una percentuale significativa dei prompt generati da PAIR risulta spesso fuori tema (**off-topic**) rispetto all'obiettivo dannoso, sprecando il budget di query [4].
*   **Soluzione di TAP:** Implementa un sistema di **potatura** in due fasi mediato da un modello valutatore [1, 5]:
    *   **Fase 1 (Branch & Evaluator):** Valuta i prompt *prima* di inviarli al modello target, eliminando immediatamente quelli considerati irrilevanti o incapaci di eludere i filtri sintattici [1, 9].
    *   **Fase 2 (Attack & Assess):** Dopo aver ricevuto le risposte dal target, conserva come "nodi radice" per l'iterazione successiva solo i prompt che hanno ottenuto i punteggi più alti, scartando i percorsi di attacco inefficienti [1, 10].

### 3. Efficacia e Efficienza Quantitativa
Grazie a queste innovazioni, TAP supera PAIR sia in termini di successo che di risparmio computazionale:
*   **Tasso di Successo (ASR):** TAP raggiunge tassi di successo del **94% su GPT-4o**, superando il 78% registrato dai metodi precedenti [11-13].
*   **Efficienza di Query:** TAP richiede circa il **60% in meno di query** rispetto a PAIR per ottenere un jailbreak riuscito [11-13]. Su molti modelli, TAP riesce a violare le sicurezze con una media inferiore a **30 query** [14, 15].
*   **Superamento dei Guardrail:** TAP si è dimostrato efficace anche contro modelli protetti da difese attive come **LlamaGuard**, mantenendo un alto tasso di successo dove PAIR risulta meno incisivo [16, 17].

In sintesi, mentre il branching è fondamentale per aumentare la probabilità di trovare un jailbreak, il pruning è l'elemento chiave che rende il metodo estremamente efficiente dal punto di vista delle query [18, 19].