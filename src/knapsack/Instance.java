package knapsack;

import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * Istanza dello zaino 0/1: n oggetti (pesi w[1..n], valori v[1..n]) e
 * capacità W. Array 1-based per seguire la notazione K(i,c): l'indice 0
 * non si usa.
 *
 * Formato file (le righe che iniziano con # sono commenti):
 *   n W
 *   w1 v1
 *   ...
 *   wn vn
 */
public final class Instance {

    public final int n;
    public final int W;
    public final int[] w;   // pesi, w[i] >= 1
    public final long[] v;  // valori; long perché la somma può superare int
    public final String name;

    public Instance(int n, int W, int[] w, long[] v, String name) {
        if (n < 0 || W < 0) throw new IllegalArgumentException("n e W devono essere >= 0");
        this.n = n;
        this.W = W;
        this.w = w;
        this.v = v;
        this.name = name;
    }

    /** Genera un'istanza casuale riproducibile (stesso seed → stessa istanza). */
    public static Instance random(int n, int W, long seed, int wMax, long vMax) {
        Random rnd = new Random(seed);
        int[] w = new int[n + 1];
        long[] v = new long[n + 1];
        for (int i = 1; i <= n; i++) {
            w[i] = 1 + rnd.nextInt(Math.max(1, wMax));
            v[i] = 1 + (long) (rnd.nextDouble() * vMax);
        }
        return new Instance(n, W, w, v, "rand(n=" + n + ",W=" + W + ",seed=" + seed + ")");
    }

    /**
     * Genera un'istanza strongly correlated: v_i = w_i + correlationCost.
     * Serve a mostrare che il tempo della PD non dipende dalla distribuzione
     * dei valori (resta Θ(n·W)), mentre quello di un solver ILP sì: il suo
     * Branch & Bound perde i bound del rilassamento LP quando valore e peso
     * sono proporzionali, e i tempi diventano poco prevedibili.
     */
    public static Instance stronglyCorrelated(int n, int W, long seed, int wMax, int correlationCost) {
        Random rnd = new Random(seed);
        int[] w = new int[n + 1];
        long[] v = new long[n + 1];
        for (int i = 1; i <= n; i++) {
            w[i] = 1 + rnd.nextInt(Math.max(1, wMax));
            v[i] = w[i] + correlationCost;
        }
        return new Instance(n, W, w, v,
                "stronglyCorrelated(n=" + n + ",W=" + W + ",seed=" + seed + ",c=" + correlationCost + ")");
    }

    public static Instance load(Path file) throws IOException {
        List<String> rows = new ArrayList<>();
        for (String line : Files.readAllLines(file)) {
            String s = line.trim();
            if (!s.isEmpty() && !s.startsWith("#")) rows.add(s);
        }
        if (rows.isEmpty()) throw new IOException("file istanza vuoto: " + file);

        String[] head = rows.get(0).split("\\s+");
        int n = Integer.parseInt(head[0]);
        int W = Integer.parseInt(head[1]);
        if (rows.size() - 1 < n) throw new IOException("attese " + n + " righe oggetto, trovate " + (rows.size() - 1));

        int[] w = new int[n + 1];
        long[] v = new long[n + 1];
        for (int i = 1; i <= n; i++) {
            String[] p = rows.get(i).split("\\s+");
            w[i] = Integer.parseInt(p[0]);
            v[i] = Long.parseLong(p[1]);
        }
        return new Instance(n, W, w, v, file.getFileName().toString());
    }

    public void save(Path file) throws IOException {
        try (PrintWriter out = new PrintWriter(Files.newBufferedWriter(file))) {
            out.println("# istanza zaino 0/1 — " + name);
            out.println(n + " " + W);
            for (int i = 1; i <= n; i++) out.println(w[i] + " " + v[i]);
        }
    }

    /** Occupazione teorica in byte della tabella completa (n+1)(W+1) celle long. */
    public long tableBytes() {
        return (long) (n + 1) * (W + 1) * Long.BYTES;
    }

    /** Occupazione teorica in byte della variante rolling array: (W+1) celle long. */
    public long rollingBytes() {
        return (long) (W + 1) * Long.BYTES;
    }
}
