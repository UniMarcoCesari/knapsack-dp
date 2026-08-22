# Prossimi Passi — Progetto Knapsack (Elaborato ASD)

Stato al 22 agosto 2026. I tre compiti della traccia (`../elaborato.pdf`) sono
svolti; relazione, presentazione e demo esistono. Quel che resta è rilettura,
consegna e un'estensione facoltativa.

## Fatto

| Compito | Dove |
|---|---|
| 1 — problema, applicabilità, pseudocodice, analisi asintotica | relazione §§1–4 |
| 2 — codifica dei due algoritmi + variante spaziale | `src/`, relazione §5 |
| 3 — sperimentazione, tempo e memoria, empirico vs asintotico | `campagna.py`, relazione §6 |

Inoltre: 305 test di correttezza, Gurobi come oracolo esterno, `demo.sh` per la
prova orale, `presentazione/presentazione.tex` (11 slide), figure vettoriali
rigenerabili con `grafici.py`.

## Da fare

### 1. Rilettura della relazione
Le §§2–7 non sono ancora state rilette da Marco. La §1 è validata dal 4 agosto.

### 2. Consegna su Moodle (entro il 3 settembre 2026)
La traccia chiede una cartella con:
- relazione in formato **sorgente e PDF** (`relazione/relazione.tex` + `.pdf`);
- codice sorgente e, possibilmente, eseguibile (`src/`, `gurobi-src/`, `bin/`);
- i file usati per valutare le prestazioni: i CSV di `data/campagna/`.

La presentazione può essere caricata anche dopo, purché entro il giorno prima
dell'orale (10 settembre).

### 3. Prova della demo
`./demo.sh` gira in una decina di minuti; conviene provarla una volta di seguito
prima dell'orale, e decidere se ridurre il passo 6 (la gara con la forza bruta).

## Facoltativo

### Algoritmo di Hirschberg
Recupererebbe la ricostruzione della soluzione in spazio Θ(W), che il rolling
array perde: rolling in avanti e all'indietro per trovare il punto di taglio,
poi ricorsione sulle due metà. È dichiarato fra le limitazioni della relazione
come sviluppo naturale; non serve a completare la traccia.

## Scartato

### Istanze "killer" per il solver ILP — rimosso il 2026-07-28
Generazione di istanze *strongly correlated* con `W = Σw_i/2` più i relativi
sweep. Rimosso perché fuori scopo (raddoppiava sull'unica parte non richiesta) e
perché i dati smentivano la tesi: Gurobi vinceva in 7 punti su 8. Resta il solo
generatore correlato (`race.py --correlated`), per la tesi più modesta e onesta
che il tempo della PD non dipende dalla distribuzione dei valori mentre quello
del branch and bound sì.
