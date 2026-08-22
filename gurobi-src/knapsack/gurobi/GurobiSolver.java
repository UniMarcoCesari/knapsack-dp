package knapsack.gurobi;

import com.gurobi.gurobi.*;

import knapsack.Instance;

/**
 * Lo stesso problema come ILP risolto con Gurobi: usato come oracolo di
 * correttezza e termine di paragone nei benchmark, non fa parte della
 * soluzione. Per un confronto onesto: Threads=1 e si misura solo il solve
 * time (attributo Runtime), senza build del modello ne' startup.
 *
 * Compilato solo se gurobi.jar e' presente (vedi compile.sh).
 * Con Gurobi <= 10 il package era gurobi.* invece di com.gurobi.gurobi.*.
 */
public final class GurobiSolver {

    public record Result(long value, double solveSeconds) {}

    private GurobiSolver() {}

    public static Result solve(Instance ist) throws GRBException {
        GRBEnv env = new GRBEnv(true);
        env.set(GRB.IntParam.OutputFlag, 0);   // silenzioso
        env.set(GRB.IntParam.Threads, 1);      // confronto leale con DP single-thread
        env.set(GRB.DoubleParam.MIPGap, 0.0);  // oracolo esatto: niente tolleranza di ottimalita'
        env.set(GRB.DoubleParam.MIPGapAbs, 0.0);
        env.start();
        try {
            GRBModel model = new GRBModel(env);

            GRBVar[] x = new GRBVar[ist.n + 1];
            GRBLinExpr obj = new GRBLinExpr();
            GRBLinExpr weight = new GRBLinExpr();
            for (int i = 1; i <= ist.n; i++) {
                x[i] = model.addVar(0, 1, 0, GRB.BINARY, "x" + i);
                obj.addTerm(ist.v[i], x[i]);
                weight.addTerm(ist.w[i], x[i]);
            }
            model.setObjective(obj, GRB.MAXIMIZE);
            model.addConstr(weight, GRB.LESS_EQUAL, ist.W, "capacita");

            model.optimize();
            if (model.get(GRB.IntAttr.Status) != GRB.OPTIMAL)
                throw new IllegalStateException("Gurobi non ha chiuso all'ottimo: status "
                        + model.get(GRB.IntAttr.Status));

            long value = Math.round(model.get(GRB.DoubleAttr.ObjVal));
            double runtime = model.get(GRB.DoubleAttr.Runtime);
            model.dispose();
            return new Result(value, runtime);
        } finally {
            env.dispose();
        }
    }

    /**
     * Verifica che l'ottimo DP coincida con quello ILP sull'istanza data.
     * Con --porcelain stampa solo una riga chiave=valore (per race.py).
     */
    public static void main(String[] args) throws Exception {
        boolean porcelain = false;
        String file = null;
        for (String a : args) {
            if (a.equals("--porcelain")) porcelain = true;
            else file = a;
        }
        Instance ist = file != null
                ? Instance.load(java.nio.file.Path.of(file))
                : Instance.random(200, 5000, 42, 5000, 1000);

        if (porcelain) {
            Result g = solve(ist);
            System.out.printf(java.util.Locale.ROOT,
                    "GUROBI valore=%d solve_ms=%.3f%n", g.value(), g.solveSeconds() * 1000);
            return;
        }

        long dp = knapsack.KnapsackRolling.value(ist);
        Result g = solve(ist);
        System.out.printf("DP = %d, Gurobi = %d (%s)  [solve time %.4f s]%n",
                dp, g.value(), dp == g.value() ? "COINCIDONO ✓" : "DIVERGONO ✗", g.solveSeconds());
        if (dp != g.value()) System.exit(1);
    }
}
