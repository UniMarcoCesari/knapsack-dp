# knapsack-dp

<p align="center">
  <img src="docs/zaino.png" width="230" alt="Zaino 0/1">
</p>

Zaino 0/1 (*0/1 Knapsack*) risolto con **programmazione dinamica** in Java:

> dati n oggetti con peso `w[i]` e valore `v[i]` e una capacità `W`,
> scegliere il sottoinsieme di valore massimo con peso totale ≤ W.

Elaborato del corso di **Algoritmi e Strutture Dati**, a.a. 2025-26, sul
paradigma della programmazione dinamica.

**La relazione è [`relazione/relazione.pdf`](relazione/relazione.pdf)**: è il
documento da leggere per primo — problema, applicabilità del paradigma,
pseudocodice dei due algoritmi, analisi asintotica e sperimentazione. Questo
repository ne è il codice.

## Dove sta cosa

| Compito della traccia | Dove |
|---|---|
| **1** — descrivere il problema, dimostrare l'applicabilità del paradigma, pseudocodice dell'algoritmo per il valore ottimo e di quello che ricostruisce la soluzione, analisi asintotica | relazione, §§1–4 |
| **2** — codificare i due algoritmi, con la variante che ne migliora le prestazioni spaziali | `src/knapsack/`, relazione §5 |
| **3** — sperimentazione su istanze crescenti: tempo, memoria, crescita empirica contro analisi asintotica | `campagna.py`, relazione §6 |

Il progetto contiene i due algoritmi di PD (calcolo del valore ottimo e
ricostruzione della soluzione), la variante a spazio ridotto, la verifica di
correttezza contro un enumeratore esaustivo e contro Gurobi, e i benchmark
che confrontano tempo e memoria dei vari approcci.

## Requisiti

- JDK 17+ (testato con Temurin 21)
- Python 3 (solo per gli script `race.py` e `campagna.py`, libreria standard)
- Gurobi con licenza (opzionale: serve solo per il confronto con l'ILP)

## Partire subito

```sh
./compile.sh                    # compila in bin/
java -cp bin knapsack.Main test # 305 test di correttezza
./race.py 22 60                 # i quattro algoritmi in gara sulla stessa istanza
```

`race.py <n> <W> [seed] [--plot]` genera un'istanza e lancia **in parallelo**
PD tabella, PD rolling, brute force e Gurobi: una riga ciascuno con valore
ottimo, tempo e memoria, più il verdetto di concordanza. Con n > 25 il brute
force si ritira da solo. Con `--plot` apre una pagina con due grafici a barre
(tempo e memoria). I file hanno nome univoco dai parametri
(`data/race_<tipo>_n<n>_W<W>_s<seed>.txt` e `data/race_n<n>_W<W>_s<seed>.html`): l'istanza viene riusata, il grafico
sovrascritto.

Per capire l'algoritmo c'è un'istanza minuscola verificabile a mano
(il greedy per densità ci casca, la PD no):

```sh
java -cp bin knapsack.Main solve data/didattica.txt --dump-table data/tabella_didattica.csv
column -s, -t data/tabella_didattica.csv
```

## Struttura

| File | Cosa fa |
|---|---|
| `src/knapsack/KnapsackValue.java` | valore ottimo bottom-up, tabella completa — Θ(nW) tempo e spazio |
| `src/knapsack/KnapsackSolution.java` | ricostruzione della soluzione dalla tabella — Θ(n) |
| `src/knapsack/KnapsackRolling.java` | variante a una riga — O(nW) tempo, Θ(W) spazio di lavoro, solo valore |
| `src/knapsack/BruteForce.java` | enumerazione dei 2ⁿ sottoinsiemi (oracolo nei test, n ≤ 25) |
| `src/knapsack/Instance.java` | istanza + generatore casuale riproducibile (seed) |
| `src/knapsack/Bench.java` | misure: sweep su n e su W, warm-up JIT, mediana/minimo, CSV |
| `src/knapsack/Main.java` | CLI (vedi sotto) |
| `gurobi-src/` | stesso problema come ILP con Gurobi (modulo opzionale) |
| `race.py` | i quattro algoritmi in parallelo sulla stessa istanza |
| `campagna.py` | tutta la campagna di benchmark + report con grafici |

## Comandi

```sh
java -cp bin knapsack.Main generate <n> <W> <seed> [--wmax X] [--vmax X] [-o file]
java -cp bin knapsack.Main solve <file> [--rolling] [--dump-table tab.csv]
java -cp bin knapsack.Main test
java -cp bin knapsack.Main bench nsweep|wsweep [--fixed X] [--from X] [--to X]
                                               [--step X] [--reps X] [--seed X] [-o out.csv]
# output a una riga chiave=valore (usati dagli script):
java -cp bin knapsack.Main dp <file>
java -cp bin knapsack.Main rolling <file>
java -cp bin knapsack.Main brute <file>
```

Formato istanza (le righe che iniziano con `#` sono commenti):

```
n W
w1 v1
...
wn vn
```

## Benchmark

```sh
./campagna.py     # ~10 s: sweep su n e su W per PD tabella/rolling e Gurobi
                  # (stesse istanze), esperimento sui limiti di memoria,
                  # CSV + report.html con i grafici
```

Risultati in `data/campagna/`: un CSV per serie, `tutti.csv` unito (si apre
in Excel) e `report.html`. Non sono versionati — si rigenerano in una decina
di secondi con `./campagna.py`; i CSV della campagna citata nella relazione
fanno parte del materiale consegnato. Metodologia: heap fissa, warm-up per il JIT,
`System.gc()` prima di ogni run misurata, mediana e minimo di più ripetizioni,
seed fisso per punto. Di Gurobi si misura solo il *solve time* a thread singolo.

Della memoria si registrano **due** valori: quello calcolato dalla formula
(`(n+1)(W+1)·8` byte la tabella, `(W+1)·8` il rolling) e quello misurato
sull'heap; il confronto verifica l'analisi Θ(nW) invece di darla per buona.
La misura è quantizzata a 512 KB, quindi vale sulla tabella completa ma non
sul rolling array: per quello la prova è l'esperimento sui limiti.

L'esperimento sui limiti mostra il senso della variante rolling: a parità di
istanza la tabella completa esaurisce la memoria (OOM) dove il rolling array
continua a funzionare in pochi MB — al prezzo della sola perdita della
ricostruzione.

## Gurobi (opzionale)

Il modulo viene compilato da `./compile.sh` solo se trova `gurobi.jar`
(variabile `GUROBI_HOME`, oppure copia del jar in `lib/`). Con Gurobi ≤ 10 il
package Java è `gurobi.*` anziché `com.gurobi.gurobi.*`: adeguare l'import.

```sh
GUROBI_HOME=/percorso/di/gurobi ./compile.sh
java -cp bin:$GUROBI_HOME/lib/gurobi.jar knapsack.gurobi.GurobiSolver data/demo.txt
```

L'ultimo comando confronta l'ottimo della PD con quello dell'ILP sulla
stessa istanza.

## Note implementative

- Celle della tabella in `long`: la somma dei valori può superare `int`.
- Array 1-based (`w[1..n]`, `v[1..n]`): il codice segue la notazione K(i, c).
- Nel rolling array il ciclo su c è **decrescente**: con c crescente si
  leggerebbe la riga già aggiornata e ogni oggetto potrebbe essere preso più
  volte (diventerebbe lo zaino illimitato).
- La complessità Θ(nW) è **pseudo-polinomiale**: lineare nel valore di W,
  quindi esponenziale nel numero di bit con cui W si scrive. Nei benchmark si vede: il tempo
  della PD cresce con W, quello di Gurobi no.
