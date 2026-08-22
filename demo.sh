#!/bin/sh
# Demo per la prova orale: i due algoritmi all'opera, con la tabella K
# disponibile per l'ispezione (richiesta esplicita della traccia).
#
# Uso:  ./demo.sh          (invio fra un passo e l'altro)
#       ./demo.sh -q       (senza pause)
set -e
cd "$(dirname "$0")"

PAUSA=1
[ "$1" = "-q" ] && PAUSA=0
titolo() {
    printf '\n\033[1;34m── %s\033[0m\n\n' "$1"
    [ "$PAUSA" = 1 ] && { printf '\033[2m(invio per continuare)\033[0m'; read -r _; }
    return 0
}

titolo "1. Compilazione e batteria di correttezza"
./compile.sh
java -cp bin knapsack.Main test

titolo "2. Istanza didattica: il greedy per densita' fallisce, la PD no"
cat data/didattica.txt

titolo "3. Primo algoritmo: valore ottimo, e secondo algoritmo: soluzione"
java -cp bin knapsack.Main solve data/didattica.txt --dump-table data/tabella_didattica.csv

titolo "4. La tabella K, disponibile per l'ispezione"
cat data/tabella_didattica.csv

titolo "5. La variante a spazio ridotto: stesso valore, una riga sola"
java -cp bin knapsack.Main solve data/didattica.txt --rolling

titolo "6. Istanza vera: PD tabella, PD rolling, forza bruta e solver a confronto"
./race.py 20 300 7

titolo "7. Il limite pratico: W grande, la tabella non ci sta, il rolling si'"
java -cp bin knapsack.Main generate 2000 300000 42 -o data/demo_grande.txt
printf '\033[2mtabella (heap 2 GB):\033[0m  '
if USCITA=$(java -Xmx2g -cp bin knapsack.Main dp data/demo_grande.txt 2>&1); then
    printf '%s\n' "$USCITA"
else
    printf 'memoria esaurita (OutOfMemoryError)\n'
fi
printf '\033[2mrolling (heap 1 GB):\033[0m  '
java -Xmx1g -cp bin knapsack.Main rolling data/demo_grande.txt

printf '\n\033[1;32mFine della demo.\033[0m\n'
