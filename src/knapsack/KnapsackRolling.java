package knapsack;

/**
 * Variante a spazio ridotto: una sola riga di W+1 celle invece della tabella.
 * Spazio Θ(W); in cambio si perde la ricostruzione della soluzione (resta
 * solo il valore ottimo). Il tempo è O(n·W) e Θ(n·W) nel caso peggiore: il
 * ciclo interno parte da W e si ferma a w[i], quindi il numero di iterazioni
 * dipende dai pesi (con pesi uniformi in [1,W] sono circa la metà di n·W).
 */
public final class KnapsackRolling {

    private KnapsackRolling() {}

    public static long value(Instance ist) {
        long[] K = new long[ist.W + 1];
        for (int i = 1; i <= ist.n; i++) {
            int wi = ist.w[i];
            long vi = ist.v[i];
            // c decrescente: K[c - wi] deve essere ancora il valore dell'iterazione
            // precedente, altrimenti l'oggetto i verrebbe contato più volte
            for (int c = ist.W; c >= wi; c--) {
                long take = K[c - wi] + vi;
                if (take > K[c]) K[c] = take;
            }
        }
        return K[ist.W];
    }
}
