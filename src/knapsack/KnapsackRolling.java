package knapsack;

/**
 * Variante a spazio ridotto: una sola riga di W+1 celle invece della tabella.
 * Tempo Θ(n·W) come la versione base, spazio Θ(W); in cambio si perde la
 * ricostruzione della soluzione (resta solo il valore ottimo).
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
