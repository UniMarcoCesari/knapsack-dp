package knapsack;

import java.util.List;
import java.util.Random;

/**
 * Test di correttezza, senza dipendenze esterne (si lancia con `Main test`).
 * Confronta DP base, rolling e brute force su istanze casuali piccole,
 * controlla la soluzione ricostruita e qualche caso limite.
 */
public final class CorrectnessTest {

    private CorrectnessTest() {}

    public static boolean runAll() {
        int failures = 0;

        // istanze casuali piccole contro l'oracolo
        Random rnd = new Random(20260707);
        int randomCases = 300;
        for (int t = 0; t < randomCases; t++) {
            int n = 1 + rnd.nextInt(14);          // n in 1..14 (brute force veloce)
            int W = rnd.nextInt(81);              // W in 0..80
            int wMax = 1 + rnd.nextInt(Math.max(1, W + 10));
            Instance ist = Instance.random(n, W, rnd.nextLong(), wMax, 1000);

            long expected = BruteForce.value(ist);
            long[][] K = KnapsackValue.table(ist);
            long base = KnapsackValue.optimum(K, ist);
            long rolling = KnapsackRolling.value(ist);

            if (base != expected) {
                System.out.printf("FAIL [%s]: base=%d, brute=%d%n", ist.name, base, expected);
                failures++;
                continue;
            }
            if (rolling != expected) {
                System.out.printf("FAIL [%s]: rolling=%d, brute=%d%n", ist.name, rolling, expected);
                failures++;
                continue;
            }
            try {
                List<Integer> sol = KnapsackSolution.reconstruct(K, ist);
                KnapsackSolution.check(sol, expected, ist);
            } catch (IllegalStateException e) {
                System.out.printf("FAIL [%s]: %s%n", ist.name, e.getMessage());
                failures++;
            }
        }

        // casi limite
        failures += edge("W=0 → valore 0",
                Instance.random(8, 0, 1, 5, 100), 0);

        failures += edge("n=0 → valore 0",
                new Instance(0, 50, new int[1], new long[1], "vuota"), 0);

        Instance heavy = new Instance(3, 10,
                new int[]{0, 11, 12, 13}, new long[]{0, 5, 6, 7}, "tutti-troppo-pesanti");
        failures += edge("nessun oggetto entra → 0", heavy, 0);

        Instance allFit = new Instance(4, 100,
                new int[]{0, 10, 20, 5, 15}, new long[]{0, 1, 2, 3, 4}, "tutti-entrano");
        failures += edge("tutti entrano → somma valori", allFit, 1 + 2 + 3 + 4);

        Instance single = new Instance(1, 7,
                new int[]{0, 7}, new long[]{0, 42}, "singolo-esatto");
        failures += edge("peso esattamente W", single, 42);

        int total = randomCases + 5;
        if (failures == 0) {
            System.out.println("Correttezza: " + total + " test superati "
                    + "(base = rolling = brute force, soluzioni ammissibili e ottime).");
            return true;
        }
        System.out.println("Correttezza: " + failures + " test FALLITI su " + total + ".");
        return false;
    }

    private static int edge(String label, Instance ist, long expected) {
        long[][] K = KnapsackValue.table(ist);
        long base = KnapsackValue.optimum(K, ist);
        long rolling = KnapsackRolling.value(ist);
        if (base != expected || rolling != expected) {
            System.out.printf("FAIL caso limite «%s»: base=%d rolling=%d atteso=%d%n",
                    label, base, rolling, expected);
            return 1;
        }
        try {
            KnapsackSolution.check(KnapsackSolution.reconstruct(K, ist), expected, ist);
        } catch (IllegalStateException e) {
            System.out.printf("FAIL caso limite «%s»: %s%n", label, e.getMessage());
            return 1;
        }
        return 0;
    }
}
