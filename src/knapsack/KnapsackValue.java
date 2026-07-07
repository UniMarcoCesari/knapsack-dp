package knapsack;

/**
 * Primo algoritmo: calcolo bottom-up del valore ottimo.
 *
 * K[i][c] = valore ottimo usando i primi i oggetti con capacità c:
 *   K[0][c] = 0
 *   K[i][c] = K[i-1][c]                              se w[i] > c
 *   K[i][c] = max(K[i-1][c], K[i-1][c-w[i]] + v[i])  altrimenti
 *
 * Tempo e spazio Θ(n·W). La tabella completa viene restituita perché
 * serve a KnapsackSolution per ricostruire la soluzione.
 */
public final class KnapsackValue {

    private KnapsackValue() {}

    public static long[][] table(Instance ist) {
        long[][] K = new long[ist.n + 1][ist.W + 1];
        // K[0][c] = 0 per ogni c: gli array Java nascono già azzerati
        for (int i = 1; i <= ist.n; i++) {
            long[] prev = K[i - 1];
            long[] cur = K[i];
            int wi = ist.w[i];
            long vi = ist.v[i];
            for (int c = 0; c <= ist.W; c++) {
                cur[c] = (wi > c) ? prev[c] : Math.max(prev[c], prev[c - wi] + vi);
            }
        }
        return K;
    }

    /** Valore ottimo dell'istanza: K[n][W]. */
    public static long optimum(long[][] K, Instance ist) {
        return K[ist.n][ist.W];
    }
}
