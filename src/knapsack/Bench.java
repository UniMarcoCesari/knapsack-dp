package knapsack;

import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

/**
 * Misure per la sperimentazione: sweep su n (W fisso) e su W (n fisso).
 * Output CSV: sweep,algo,n,W,seed,reps,ms_mediana,ms_min,mem_bytes
 *
 * Accorgimenti: warm-up per il JIT, System.gc() prima di ogni misura,
 * mediana e minimo di più ripetizioni, seed fisso per punto (riproducibile).
 * La memoria è quella teorica delle strutture: (n+1)(W+1)*8 e (W+1)*8 byte.
 */
public final class Bench {

    private Bench() {}

    public static final int WARMUP = 3;

    public static void sweepN(int wFixed, int from, int to, int step,
                              int reps, long seed, Path out) throws IOException {
        try (PrintWriter csv = writer(out)) {
            for (int n = from; n <= to; n += step) {
                Instance ist = Instance.random(n, wFixed, seed + n, Math.max(1, wFixed), 1000);
                point(csv, "n", ist, reps, seed + n);
                System.out.printf("  n=%-7d W=%-7d fatto%n", n, wFixed);
            }
        }
        System.out.println("CSV scritto: " + out);
    }

    public static void sweepW(int nFixed, int from, int to, int step,
                              int reps, long seed, Path out) throws IOException {
        try (PrintWriter csv = writer(out)) {
            for (int W = from; W <= to; W += step) {
                Instance ist = Instance.random(nFixed, W, seed + W, Math.max(1, W), 1000);
                point(csv, "W", ist, reps, seed + W);
                System.out.printf("  n=%-7d W=%-7d fatto%n", nFixed, W);
            }
        }
        System.out.println("CSV scritto: " + out);
    }

    private static PrintWriter writer(Path out) throws IOException {
        PrintWriter csv = new PrintWriter(Files.newBufferedWriter(out));
        csv.println("sweep,algo,n,W,seed,reps,ms_mediana,ms_min,mem_bytes");
        return csv;
    }

    private static void point(PrintWriter csv, String sweep, Instance ist, int reps, long seedTag) {
        double[] base = measure(reps, () -> {
            long[][] K = KnapsackValue.table(ist);
            sink += K[ist.n][ist.W];
        });
        // Locale.ROOT: punto decimale sempre, la virgola è il separatore del CSV
        csv.printf(java.util.Locale.ROOT, "%s,base,%d,%d,%d,%d,%.3f,%.3f,%d%n",
                sweep, ist.n, ist.W, seedTag, reps, base[0], base[1], ist.tableBytes());

        double[] roll = measure(reps, () -> sink += KnapsackRolling.value(ist));
        csv.printf(java.util.Locale.ROOT, "%s,rolling,%d,%d,%d,%d,%.3f,%.3f,%d%n",
                sweep, ist.n, ist.W, seedTag, reps, roll[0], roll[1], ist.rollingBytes());
        csv.flush();
    }

    // impedisce al JIT di eliminare il calcolo come codice morto
    private static volatile long sink;

    /** Esegue WARMUP volte senza misurare, poi reps volte; ritorna {mediana, minimo} in ms. */
    private static double[] measure(int reps, Runnable body) {
        for (int i = 0; i < WARMUP; i++) body.run();
        double[] ms = new double[reps];
        for (int i = 0; i < reps; i++) {
            System.gc();   // colleziona i rifiuti del run precedente FUORI dal cronometro
            long t0 = System.nanoTime();
            body.run();
            ms[i] = (System.nanoTime() - t0) / 1e6;
        }
        Arrays.sort(ms);
        double median = (reps % 2 == 1) ? ms[reps / 2] : (ms[reps / 2 - 1] + ms[reps / 2]) / 2;
        return new double[]{median, ms[0]};
    }
}
