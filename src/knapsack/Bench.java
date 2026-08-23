package knapsack;

import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.function.Supplier;

/**
 * Misure per la sperimentazione: sweep su n (W fisso) e su W (n fisso).
 * Output CSV: sweep,algo,n,W,seed,reps,ms_mediana,ms_min,mem_teorica,mem_misurata
 *
 * Accorgimenti: warm-up per il JIT, System.gc() prima di ogni misura,
 * mediana e minimo di più ripetizioni, seed fisso per punto (riproducibile).
 * Della memoria si registrano sia il valore teorico delle strutture
 * ((n+1)(W+1)*8 e (W+1)*8 byte) sia quello misurato sull'heap.
 */
public final class Bench {

    private Bench() {}

    public static final int WARMUP = 3;

    /** Letture dell'heap per punto: se ne prende la mediana. */
    private static final int MEM_REPS = 3;

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
        csv.println("sweep,algo,n,W,seed,reps,ms_mediana,ms_min,mem_teorica,mem_misurata,valore");
        return csv;
    }

    private static void point(PrintWriter csv, String sweep, Instance ist, int reps, long seedTag) {
        // valore ottimo del punto: finisce nel CSV, cosi' il confronto con il
        // solver (GurobiBench) resta documentato istanza per istanza.
        // Prima pero' i due algoritmi di programmazione dinamica si controllano
        // a vicenda: se divergessero, il confronto col solver non direbbe quale
        // dei due ha sbagliato
        long ottimo = KnapsackRolling.value(ist);
        long ottimoTabella = KnapsackValue.optimum(KnapsackValue.table(ist), ist);
        if (ottimo != ottimoTabella)
            throw new IllegalStateException("valori diversi su n=" + ist.n + " W=" + ist.W
                    + ": tabella=" + ottimoTabella + " rolling=" + ottimo);
        double[] base = measure(reps, () -> {
            long[][] K = KnapsackValue.table(ist);
            sink += K[ist.n][ist.W];
        });
        long baseMem = measureHeap(() -> KnapsackValue.table(ist));
        // Locale.ROOT: punto decimale sempre, la virgola è il separatore del CSV
        csv.printf(java.util.Locale.ROOT, "%s,base,%d,%d,%d,%d,%.3f,%.3f,%d,%d,%d%n",
                sweep, ist.n, ist.W, seedTag, reps, base[0], base[1], ist.tableBytes(), baseMem, ottimo);

        double[] roll = measure(reps, () -> sink += KnapsackRolling.value(ist));
        // il rolling rende garbage il suo array al ritorno: si rialloca per misurarlo
        long rollMem = measureHeap(() -> new long[ist.W + 1]);
        csv.printf(java.util.Locale.ROOT, "%s,rolling,%d,%d,%d,%d,%.3f,%.3f,%d,%d,%d%n",
                sweep, ist.n, ist.W, seedTag, reps, roll[0], roll[1], ist.rollingBytes(), rollMem, ottimo);
        csv.flush();
    }

    // impedisce al JIT di eliminare il calcolo come codice morto
    private static volatile long sink;

    // senza, il collector può liberare la struttura fra le due letture dell'heap
    private static volatile Object keepAlive;

    /**
     * Byte di heap occupati dalla struttura allocata da alloc: GC, lettura,
     * allocazione, rilettura; mediana di MEM_REPS letture.
     *
     * I valori risultano quantizzati a 512 KB, perché l'heap cresce a blocchi:
     * la misura vale sulla tabella completa, non sul rolling da pochi KB.
     */
    private static long measureHeap(Supplier<Object> alloc) {
        Runtime rt = Runtime.getRuntime();
        long[] bytes = new long[MEM_REPS];
        for (int i = 0; i < MEM_REPS; i++) {
            keepAlive = null;
            System.gc();
            System.gc();   // la prima passata può lasciare oggetti ancora in coda
            long before = rt.totalMemory() - rt.freeMemory();
            keepAlive = alloc.get();
            long after = rt.totalMemory() - rt.freeMemory();
            bytes[i] = Math.max(0, after - before);
        }
        keepAlive = null;
        Arrays.sort(bytes);
        return bytes[MEM_REPS / 2];
    }

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
