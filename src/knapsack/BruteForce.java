package knapsack;

/**
 * Enumerazione di tutti i 2^n sottoinsiemi. Serve solo come oracolo nei test
 * per verificare la DP; usabile fino a n = 25.
 */
public final class BruteForce {

    public static final int MAX_N = 25;

    private BruteForce() {}

    public static long value(Instance ist) {
        if (ist.n > MAX_N)
            throw new IllegalArgumentException("brute force limitato a n <= " + MAX_N);
        long best = 0;
        for (long mask = 0; mask < (1L << ist.n); mask++) {
            long weight = 0, value = 0;
            for (int i = 1; i <= ist.n; i++) {
                if (((mask >> (i - 1)) & 1) == 1) {
                    weight += ist.w[i];
                    value += ist.v[i];
                }
            }
            if (weight <= ist.W && value > best) best = value;
        }
        return best;
    }
}
