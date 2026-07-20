Il framework **Prompt Automatic Iterative Refinement (PAIR)** è un algoritmo di attacco semantico automatizzato progettato per il jailbreaking di Large Language Models (LLM) in modalità **black-box** [1-3]. Ispirato alle tecniche di ingegneria sociale, PAIR non richiede l'accesso ai gradienti o ai parametri interni del modello target, interagendo con esso esclusivamente tramite input e output di testo [1, 3, 4].

### Architettura e Funzionamento
PAIR formalizza l'attacco come un processo di ottimizzazione iterativo che coinvolge tre componenti principali [1, 5]:
*   **Modello Attaccante ($A$):** Un LLM che genera varianti di prompt progettate per eludere le difese del target [1, 6]. È inizializzato con un prompt di sistema specifico che lo istruisce a utilizzare strategie come l'offuscamento, il role-play e la manipolazione emotiva [7, 8].
*   **Modello Target ($T$):** Il sistema sotto attacco che riceve il prompt raffinato e genera una risposta [1, 9].
*   **Giudice ($J$):** Solitamente un modello di frontiera (come GPT-4) che valuta la risposta del target assegnando un punteggio (spesso da 1 a 10) in base alla completezza del jailbreak rispetto all'obiettivo dannoso [1, 10, 11].

Il ciclo operativo prevede che l'attaccante analizzi la **cronologia dei tentativi**, le risposte del target e i punteggi del giudice, utilizzando catene di pensiero (**Chain-of-Thought**) per produrre un raffinamento incrementale del prompt fino al successo dell'attacco o all'esaurimento del budget di query [12-14].

### Vantaggi del Metodo
*   **Efficienza di Query:** PAIR è in grado di ottenere jailbreak in meno di **venti query**, riducendo i costi computazionali di oltre 250 volte rispetto a ottimizzatori discreti come GCG [12, 15].
*   **Interpretabilità e Stealthiness:** Poiché genera prompt in linguaggio naturale dotati di senso, gli attacchi di PAIR sono difficili da rilevare tramite filtri basati sulla perplessità, a differenza dei metodi che producono stringhe di caratteri casuali [2, 3, 12].
*   **Elevata Trasferibilità:** I prompt ottimizzati per un modello specifico spesso riescono a violare le sicurezze anche di altri LLM non visti durante la fase di generazione [16, 17].

### Limitazioni e Sviluppi Successivi
Nonostante l'efficacia, PAIR soffre di alcune criticità:
*   **Ridondanza:** Poiché l'attaccante riceve la stessa cronologia iniziale, molti prompt generati nelle prime fasi tendono a seguire strategie identiche [18].
*   **Qualità Variabile:** Una parte significativa dei prompt generati può risultare fuori tema rispetto all'obiettivo dannoso [18].

Questi limiti sono stati affrontati dal metodo **Tree of Attacks with Pruning (TAP)**, che estende la logica di PAIR trasformando la ricerca lineare in un'esplorazione ad **albero** integrata con un sistema di **potatura (pruning)** per eliminare i percorsi di attacco meno promettenti o non pertinenti [19-22]. Inoltre, è stato osservato che l'uso di tecniche di *activation steering* benevole (come l'imposizione del formato JSON) può agire da moltiplicatore di forza, aumentando drasticamente il tasso di successo degli attacchi PAIR [23-25].