# Prossimi Passi — Progetto Knapsack (Elaborato ASD)

Priorità di lavoro, ordinate per resa rispetto ai tre compiti della traccia
(`../elaborato.pdf`). Criterio guida: **prima ciò che la traccia chiede
esplicitamente**, poi gli extra.

## Cosa chiede la traccia (promemoria)

| Compito | Richiesta |
|---|---|
| 1 | Problema, applicabilità della PD, pseudocodice dei due algoritmi, analisi asintotica del primo |
| 2 | Codificare i due algoritmi, **con varianti che migliorino le prestazioni spaziali** così da estendere le dimensioni delle istanze elaborabili |
| 3 | Istanze di dimensioni diverse, registrare **tempo e occupazione di memoria** per ogni esecuzione, confrontare la crescita empirica con quella **attesa dall'analisi asintotica** |

Gurobi non è richiesto: resta solo come oracolo di correttezza e baseline di
confronto, come dichiarato nella relazione.

## 🔴 Priorità Alta

### 1. Memoria misurata, non solo calcolata
Il Compito 3 chiede di *registrare* l'occupazione di memoria e di valutarne la
crescita empirica. Oggi la memoria è solo **calcolata analiticamente**
(`(n+1)(W+1)·8` e `(W+1)·8` byte): scelta elegante e deterministica, da tenere,
ma è un conto, non una misura.
**Da fare:** aggiungere al `Bench` il picco di heap effettivo (es.
`MemoryMXBean` / `Runtime` dopo `System.gc()`) come colonna a fianco di quella
teorica, e nel report un grafico memoria-vs-n e memoria-vs-W. Il confronto
"misurato vs teorico" è esattamente il confronto empirico-vs-asintotico chiesto.

### 2. Relazione
Le sezioni 2–7 di `relazione/relazione.tex` sono ancora segnaposto
«Da compilare». È il deliverable valutato: ha la precedenza su qualunque
aggiunta di codice.

### 3. Presentazione
Richiesta dalla traccia (slide 12: PowerPoint o PDF, pochi minuti sui punti
salienti). Non esiste ancora.

## 🟡 Priorità Media

### 4. Algoritmo di Hirschberg (divide-et-impera)
**È Compito 2 alla lettera:** variante che riduce lo spazio a Θ(W) *e*
mantiene la ricostruzione della soluzione, che il rolling array perde.
**Come fare:**
1. Nuova classe `KnapsackHirschberg.java`.
2. Rolling array in avanti e all'indietro per individuare il punto di taglio ottimo.
3. Ricorsione sulle due metà.
4. Integrare nella gara (`race.py`) per mostrare che, a pari memoria del
   rolling array, estrae la soluzione esatta come l'algoritmo base.

## ⚪️ Scartato

### Istanze "killer" per il solver ILP — rimosso il 2026-07-28
Era stata implementata la generazione di istanze *strongly correlated* con
`W = Σw_i/2` più i relativi sweep (`Bench.sweepKiller`, modalità `killer` di
`GurobiBench`, `DemoCorrelated`, terza card del report). **Rimosso** per due
motivi:

1. **Fuori scopo:** raddoppiava sull'unica parte non richiesta (Gurobi) invece
   che sul nucleo valutato.
2. **I dati smentivano la tesi:** la didascalia sosteneva che il B&B di Gurobi
   dovesse esplorare molti più nodi, ma nelle misure Gurobi vinceva in 7 punti
   su 8 (a n=800: 3.2 ms contro 153 ms della PD). A n ≤ 800 con pesi in
   [1000,1500] presolve e cover cuts risolvono quelle istanze senza fatica.

Resta in `Instance.stronglyCorrelated` il solo generatore correlato, usato da
`race.py --correlated`: serve a una tesi più modesta ma **onesta e sostenuta dai
dati**, da spendere in una riga della relazione — il tempo della PD non dipende
dalla distribuzione dei valori (resta Θ(n·W) e cresce liscio), quello del B&B sì
ed è poco prevedibile (nelle misure oscillava fra 0.5 e 208 ms in modo non
monotono). La garanzia di prevedibilità è un punto a favore della PD, e si
argomenta senza sostenere che la PD sia più veloce.
