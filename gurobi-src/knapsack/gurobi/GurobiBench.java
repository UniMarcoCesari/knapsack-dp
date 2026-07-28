package knapsack.gurobi;

import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

import knapsack.Instance;

/**
 * Sweep di benchmark per Gurobi sugli stessi punti (stesse istanze e seed)
 * degli sweep DP di knapsack.Bench.
 *
 * Uso: java -cp bin:gurobi.jar knapsack.gurobi.GurobiBench \
 *          nsweep|wsweep <fixed> <from> <to> <step> <reps> <seed> <out.csv>
 *
 * Per punto: 1 solve di warm-up, poi mediana e minimo di reps solve;
 * si registra solo il tempo di soluzione (attributo Runtime).
 * Le due colonne di memoria valgono 0 (quella del solver sta nella libreria
 * nativa): servono ad avere le stesse colonne degli sweep di knapsack.Bench.
 */
public final class GurobiBench {

    public static void main(String[] args) throws Exception {
        if (args.length < 8) {
            System.err.println("uso: nsweep|wsweep fixed from to step reps seed out.csv");
            System.exit(2);
        }
        String mode = args[0];
        int fixed = Integer.parseInt(args[1]);
        int from = Integer.parseInt(args[2]);
        int to = Integer.parseInt(args[3]);
        int step = Integer.parseInt(args[4]);
        int reps = Integer.parseInt(args[5]);
        long seed = Long.parseLong(args[6]);
        Path out = Path.of(args[7]);

        Files.createDirectories(out.toAbsolutePath().getParent());
        try (PrintWriter csv = new PrintWriter(Files.newBufferedWriter(out))) {
            csv.println("sweep,algo,n,W,seed,reps,ms_mediana,ms_min,mem_teorica,mem_misurata");
            for (int x = from; x <= to; x += step) {
                int n = mode.equals("nsweep") ? x : fixed;
                int W = mode.equals("nsweep") ? fixed : x;
                long s = seed + x;
                // identica alla generazione di knapsack.Bench
                Instance ist = Instance.random(n, W, s, Math.max(1, W), 1000);

                GurobiSolver.solve(ist);               // warm-up (scartato)
                double[] ms = new double[reps];
                for (int r = 0; r < reps; r++) {
                    ms[r] = GurobiSolver.solve(ist).solveSeconds() * 1000;
                }
                Arrays.sort(ms);
                double med = (reps % 2 == 1) ? ms[reps / 2] : (ms[reps / 2 - 1] + ms[reps / 2]) / 2;
                csv.printf(java.util.Locale.ROOT, "%s,gurobi,%d,%d,%d,%d,%.3f,%.3f,0,0%n",
                        mode.equals("nsweep") ? "n" : "W", n, W, s, reps, med, ms[0]);
                csv.flush();
                System.out.printf("  gurobi %s=%d fatto%n", mode.equals("nsweep") ? "n" : "W", x);
            }
        }
        System.out.println("CSV scritto: " + out);
    }

    private GurobiBench() {}
}
