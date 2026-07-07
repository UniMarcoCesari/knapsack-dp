package knapsack;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Secondo algoritmo: ricostruzione di una soluzione ottima dalla tabella K.
 * Si parte da K[n][W] e si torna indietro: l'oggetto i è stato preso
 * se e solo se K[i][c] != K[i-1][c]. Tempo Θ(n), ma serve la tabella completa.
 */
public final class KnapsackSolution {

    private KnapsackSolution() {}

    /** Restituisce gli indici (1-based, crescenti) degli oggetti scelti. */
    public static List<Integer> reconstruct(long[][] K, Instance ist) {
        List<Integer> chosen = new ArrayList<>();
        int c = ist.W;
        for (int i = ist.n; i >= 1; i--) {
            if (K[i][c] != K[i - 1][c]) {   // l'oggetto i appartiene alla soluzione
                chosen.add(i);
                c -= ist.w[i];
            }
        }
        Collections.reverse(chosen);
        return chosen;
    }

    /** Controlla che la soluzione sia ammissibile e valga esattamente l'ottimo. */
    public static void check(List<Integer> sol, long expectedValue, Instance ist) {
        long weight = 0, value = 0;
        for (int i : sol) {
            weight += ist.w[i];
            value += ist.v[i];
        }
        if (weight > ist.W)
            throw new IllegalStateException("soluzione NON ammissibile: peso " + weight + " > W=" + ist.W);
        if (value != expectedValue)
            throw new IllegalStateException("valore soluzione " + value + " != ottimo " + expectedValue);
    }
}
