package knapsack;

import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

/**
 * CLI del progetto (I/O batch da file, nessuna GUI).
 *
 *   generate n W seed [opzioni]               genera un'istanza casuale
 *   solve file [--rolling] [--dump-table f]   risolve e stampa valore+soluzione
 *   test                                      suite di correttezza
 *   bench nsweep|wsweep [opzioni]             misure -> CSV
 *   dp|rolling|brute file                     output a una riga, per gli script
 */
public final class Main {

    public static void main(String[] args) throws IOException {
        if (args.length == 0) { usage(); return; }
        switch (args[0]) {
            case "generate" -> generate(args);
            case "solve"    -> solve(args);
            case "test"     -> { if (!CorrectnessTest.runAll()) System.exit(1); }
            case "bench"    -> bench(args);
            case "dp"       -> dpPorcelain(args);
            case "rolling"  -> rollingPorcelain(args);
            case "brute"    -> brutePorcelain(args);
            default -> usage();
        }
    }

    /** DP completa, output a una riga chiave=valore (usato da race.py). */
    private static void dpPorcelain(String[] a) throws IOException {
        Instance ist = Instance.load(Path.of(a[1]));
        long t0 = System.nanoTime();
        long[][] K = KnapsackValue.table(ist);
        long best = KnapsackValue.optimum(K, ist);
        double ms = (System.nanoTime() - t0) / 1e6;
        List<Integer> sol = KnapsackSolution.reconstruct(K, ist);
        KnapsackSolution.check(sol, best, ist);
        System.out.printf(java.util.Locale.ROOT,
                "DP valore=%d ms=%.3f mem=%d oggetti_scelti=%d%n",
                best, ms, ist.tableBytes(), sol.size());
    }

    /** Rolling array, output a una riga chiave=valore. */
    private static void rollingPorcelain(String[] a) throws IOException {
        Instance ist = Instance.load(Path.of(a[1]));
        long t0 = System.nanoTime();
        long best = KnapsackRolling.value(ist);
        double ms = (System.nanoTime() - t0) / 1e6;
        System.out.printf(java.util.Locale.ROOT,
                "ROLLING valore=%d ms=%.3f mem=%d%n", best, ms, ist.rollingBytes());
    }

    /** Brute force, output a una riga; exit 3 se n supera il limite. */
    private static void brutePorcelain(String[] a) throws IOException {
        Instance ist = Instance.load(Path.of(a[1]));
        if (ist.n > BruteForce.MAX_N) {
            System.out.println("BRUTE skip n=" + ist.n + " max=" + BruteForce.MAX_N);
            System.exit(3);
        }
        long t0 = System.nanoTime();
        long best = BruteForce.value(ist);
        double ms = (System.nanoTime() - t0) / 1e6;
        System.out.printf(java.util.Locale.ROOT, "BRUTE valore=%d ms=%.3f%n", best, ms);
    }

    /* ── generate ─────────────────────────────────────── */
    private static void generate(String[] a) throws IOException {
        if (a.length < 4) { usage(); return; }
        int n = Integer.parseInt(a[1]);
        int W = Integer.parseInt(a[2]);
        long seed = Long.parseLong(a[3]);
        int wMax = W > 0 ? W : 1;
        long vMax = 1000;
        Path out = null;
        for (int i = 4; i < a.length; i++) {
            switch (a[i]) {
                case "-o" -> out = Path.of(a[++i]);
                case "--wmax" -> wMax = Integer.parseInt(a[++i]);
                case "--vmax" -> vMax = Long.parseLong(a[++i]);
                default -> { System.err.println("opzione sconosciuta: " + a[i]); return; }
            }
        }
        Instance ist = Instance.random(n, W, seed, wMax, vMax);
        if (out == null) out = Path.of("data/istanza_n" + n + "_W" + W + "_s" + seed + ".txt");
        Files.createDirectories(out.toAbsolutePath().getParent());
        ist.save(out);
        System.out.println("Istanza scritta: " + out + "  (" + ist.name + ")");
    }

    /* ── solve ────────────────────────────────────────── */
    private static void solve(String[] a) throws IOException {
        if (a.length < 2) { usage(); return; }
        Instance ist = Instance.load(Path.of(a[1]));
        boolean rolling = false;
        Path dump = null;
        for (int i = 2; i < a.length; i++) {
            switch (a[i]) {
                case "--rolling" -> rolling = true;
                case "--dump-table" -> dump = Path.of(a[++i]);
                default -> { System.err.println("opzione sconosciuta: " + a[i]); return; }
            }
        }

        System.out.println("Istanza: " + ist.name + "  (n=" + ist.n + ", W=" + ist.W + ")");
        if (rolling) {
            long t0 = System.nanoTime();
            long best = KnapsackRolling.value(ist);
            double ms = (System.nanoTime() - t0) / 1e6;
            System.out.printf("Rolling array:  valore ottimo = %d   [%.2f ms, %d byte di tabella]%n",
                    best, ms, ist.rollingBytes());
            System.out.println("(variante Θ(W): il valore c'è, la soluzione non è ricostruibile)");
            if (dump != null)
                System.err.println("--dump-table ignorato: la variante Θ(W) non costruisce la tabella");
            return;
        }

        long t0 = System.nanoTime();
        long[][] K = KnapsackValue.table(ist);                    // primo algoritmo
        double msTable = (System.nanoTime() - t0) / 1e6;
        long best = KnapsackValue.optimum(K, ist);

        long t1 = System.nanoTime();
        List<Integer> sol = KnapsackSolution.reconstruct(K, ist); // secondo algoritmo
        double msSol = (System.nanoTime() - t1) / 1e6;
        KnapsackSolution.check(sol, best, ist);

        long weight = sol.stream().mapToLong(i -> ist.w[i]).sum();
        System.out.printf("Valore ottimo:  %d   [tabella: %.2f ms, %d byte]%n",
                best, msTable, ist.tableBytes());
        System.out.printf("Soluzione:      %s   (peso %d/%d)   [ricostruzione: %.3f ms]%n",
                sol, weight, ist.W, msSol);

        if (dump != null) {
            dumpTable(K, ist, dump);
            System.out.println("Tabella K salvata per ispezione: " + dump);
        }
    }

    /** Esporta la tabella K in CSV, per poterla ispezionare. */
    private static void dumpTable(long[][] K, Instance ist, Path out) throws IOException {
        Files.createDirectories(out.toAbsolutePath().getParent());
        try (PrintWriter csv = new PrintWriter(Files.newBufferedWriter(out))) {
            StringBuilder head = new StringBuilder("i\\c");
            for (int c = 0; c <= ist.W; c++) head.append(',').append(c);
            csv.println(head);
            for (int i = 0; i <= ist.n; i++) {
                StringBuilder row = new StringBuilder();
                row.append(i == 0 ? "0 (nessun oggetto)" : i + " (w=" + ist.w[i] + " v=" + ist.v[i] + ")");
                for (int c = 0; c <= ist.W; c++) row.append(',').append(K[i][c]);
                csv.println(row);
            }
        }
    }

    /* ── bench ────────────────────────────────────────── */
    private static void bench(String[] a) throws IOException {
        if (a.length < 2) { usage(); return; }
        String mode = a[1];
        int fixed = 1000;   // fattore tenuto costante durante lo sweep
        int from = 1000, to = 10000, step = 1000, reps = 5;
        long seed = 42;
        Path out = null;
        for (int i = 2; i < a.length; i++) {
            switch (a[i]) {
                case "--fixed" -> fixed = Integer.parseInt(a[++i]);
                case "--from" -> from = Integer.parseInt(a[++i]);
                case "--to"   -> to = Integer.parseInt(a[++i]);
                case "--step" -> step = Integer.parseInt(a[++i]);
                case "--reps" -> reps = Integer.parseInt(a[++i]);
                case "--seed" -> seed = Long.parseLong(a[++i]);
                case "-o"     -> out = Path.of(a[++i]);
                default -> { System.err.println("opzione sconosciuta: " + a[i]); return; }
            }
        }
        if (out == null) out = Path.of("data/bench_" + mode + ".csv");
        Files.createDirectories(out.toAbsolutePath().getParent());

        System.out.println("Piattaforma: " + System.getProperty("os.name") + " "
                + System.getProperty("os.arch") + ", Java " + System.getProperty("java.version")
                + ", heap max " + (Runtime.getRuntime().maxMemory() >> 20) + " MB");
        System.out.println("Sweep " + mode + " da " + from + " a " + to + " (passo " + step
                + "), fattore fisso = " + fixed + ", " + reps + " ripetizioni + "
                + Bench.WARMUP + " warm-up.");

        if (mode.equals("nsweep")) Bench.sweepN(fixed, from, to, step, reps, seed, out);
        else if (mode.equals("wsweep")) Bench.sweepW(fixed, from, to, step, reps, seed, out);
        else usage();
    }

    private static void usage() {
        System.out.println("""
            Zaino 0/1 in programmazione dinamica

            Uso:
              generate <n> <W> <seed> [--wmax X] [--vmax X] [-o file]
              solve <file-istanza> [--rolling] [--dump-table tabella.csv]
              test
              bench nsweep|wsweep [--fixed X] [--from X] [--to X] [--step X]
                                  [--reps X] [--seed X] [-o out.csv]

            Consigliato per le misure: java -Xms2g -Xmx2g -cp bin knapsack.Main bench ...
            (heap fissa: niente ridimensionamenti del GC durante le misure)""");
    }
}
