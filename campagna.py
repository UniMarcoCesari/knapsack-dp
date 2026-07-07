#!/usr/bin/env python3
"""campagna.py — campagna sperimentale completa (Compito 3).

Esegue e raccoglie in data/campagna/:
  1. sweep su n (W fisso):  DP tabella + DP rolling (Bench) e Gurobi (GurobiBench)
  2. sweep su W (n fisso):  idem
  3. esperimento "limiti":  n fisso, W molto grande — la tabella va in OOM,
     il rolling array no (la motivazione pratica della variante spaziale)
  4. report.html con i grafici e la tabella dei limiti, più tutti i CSV
     (pronti per Excel) e le caratteristiche della piattaforma.

Uso:  ./campagna.py            (~1-2 minuti)
Variabili: CAMPAGNA_NO_OPEN=1 per non aprire il report a fine corsa.
"""
import csv
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "campagna"
GUROBI_HOME = Path(os.environ.get("GUROBI_HOME", "/Library/gurobi1203/macos_universal2"))
GUROBI_JAR = GUROBI_HOME / "lib" / "gurobi.jar"

# ── parametri della campagna ──
SEED = 42
N_SWEEP = dict(fixed=1000, start=1000, stop=10000, step=1000)   # W fisso, n cresce
W_SWEEP = dict(fixed=1000, start=1000, stop=10000, step=1000)   # n fisso, W cresce
DP_REPS, GRB_REPS = 7, 3
LIMITS_N = 2000
LIMITS_W = [100_000, 300_000, 1_000_000]
LIMITS_HEAP = "2g"     # tetto di memoria per l'esperimento sui limiti

DIM, RESET, GREEN, RED = "\033[2m", "\033[0m", "\033[32m", "\033[31m"
THIN = " "


def fmt(x):
    return f"{int(x):,}".replace(",", THIN)


def fmt_bytes(b):
    b = float(b)
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024 or unit == "GB":
            return (f"{int(b)} B" if unit == "B" else f"{b:.1f} {unit}")
        b /= 1024


def sh(cmd, **kw):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, **kw)


def step_title(msg):
    print(f"\n{GREEN}▶ {msg}{RESET}")


def platform_info():
    cpu = sh(["sysctl", "-n", "machdep.cpu.brand_string"]).stdout.strip()
    mem = sh(["sysctl", "-n", "hw.memsize"]).stdout.strip()
    osv = sh(["sw_vers", "-productVersion"]).stdout.strip()
    jav = sh(["java", "-version"]).stderr.splitlines()
    return {
        "CPU": cpu or "n/d",
        "RAM": fmt_bytes(int(mem)) if mem.isdigit() else "n/d",
        "macOS": osv or "n/d",
        "Java": jav[0].strip() if jav else "n/d",
        "Data": time.strftime("%Y-%m-%d %H:%M"),
        "Metodo": f"warm-up 3 + {DP_REPS} run (DP) e warm-up 1 + {GRB_REPS} solve (Gurobi); nei grafici il MINIMO delle ripetizioni (inviluppo inferiore, insensibile a GC), nei CSV anche la mediana; seed base {SEED}",
    }


def read_rows(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def run_dp_sweeps():
    step_title("Sweep DP (tabella + rolling) — Bench")
    for mode, cfg, out in (("nsweep", N_SWEEP, OUT / "dp_n.csv"),
                           ("wsweep", W_SWEEP, OUT / "dp_w.csv")):
        r = sh(["java", "-Xms2g", "-Xmx2g", "-cp", "bin", "knapsack.Main", "bench", mode,
                "--fixed", str(cfg["fixed"]), "--from", str(cfg["start"]),
                "--to", str(cfg["stop"]), "--step", str(cfg["step"]),
                "--reps", str(DP_REPS), "--seed", str(SEED), "-o", str(out)])
        if r.returncode != 0:
            sys.exit(RED + "Bench fallito:\n" + r.stderr + RESET)
        print(f"  {out.relative_to(ROOT)} ✓")


def run_gurobi_sweeps():
    if not GUROBI_JAR.is_file():
        print(f"{DIM}Gurobi non disponibile: curve saltate{RESET}")
        return False
    step_title("Sweep Gurobi (stesse istanze) — GurobiBench")
    for mode, cfg, out in (("nsweep", N_SWEEP, OUT / "gurobi_n.csv"),
                           ("wsweep", W_SWEEP, OUT / "gurobi_w.csv")):
        r = sh(["java", "-cp", f"bin:{GUROBI_JAR}", "knapsack.gurobi.GurobiBench",
                mode, str(cfg["fixed"]), str(cfg["start"]), str(cfg["stop"]),
                str(cfg["step"]), str(GRB_REPS), str(SEED), str(out)])
        if r.returncode != 0:
            sys.exit(RED + "GurobiBench fallito:\n" + r.stderr + r.stdout + RESET)
        print(f"  {out.relative_to(ROOT)} ✓")
    return True


def run_limits():
    step_title(f"Limiti pratici: n={LIMITS_N}, heap {LIMITS_HEAP}, W crescente")
    rows = []
    for W in LIMITS_W:
        inst = OUT / f"lim_n{LIMITS_N}_W{W}.txt"
        if not inst.exists():
            g = sh(["java", "-cp", "bin", "knapsack.Main", "generate",
                    str(LIMITS_N), str(W), str(SEED), "-o", str(inst)])
            if g.returncode != 0:
                sys.exit(RED + g.stderr + RESET)

        table_bytes = (LIMITS_N + 1) * (W + 1) * 8
        rolling_bytes = (W + 1) * 8

        base = sh(["java", f"-Xmx{LIMITS_HEAP}", "-cp", "bin", "knapsack.Main", "dp", str(inst)])
        if base.returncode == 0:
            ms = float(base.stdout.split("ms=")[1].split()[0])
            base_out = f"{ms/1000:.2f} s"
        elif "OutOfMemoryError" in (base.stdout + base.stderr):
            base_out = "OOM"
        else:
            base_out = "errore"

        roll = sh(["java", "-Xmx1g", "-cp", "bin", "knapsack.Main", "rolling", str(inst)])
        roll_out = f"{float(roll.stdout.split('ms=')[1].split()[0])/1000:.2f} s" if roll.returncode == 0 else "errore"

        rows.append(dict(W=W, table_bytes=table_bytes, rolling_bytes=rolling_bytes,
                         base=base_out, rolling=roll_out))
        print(f"  W={fmt(W):>10}   tabella {fmt_bytes(table_bytes):>8} → {base_out:<7}"
              f"   rolling {fmt_bytes(rolling_bytes):>7} → {roll_out}")
    return rows


def merge_all(gurobi_ok):
    files = [OUT / "dp_n.csv", OUT / "dp_w.csv"]
    if gurobi_ok:
        files += [OUT / "gurobi_n.csv", OUT / "gurobi_w.csv"]
    out = OUT / "tutti.csv"
    with open(out, "w", newline="") as fh:
        w = None
        for f in files:
            for i, line in enumerate(f.read_text().splitlines()):
                if i == 0:
                    if w is None:
                        fh.write(line + "\n")
                        w = True
                    continue
                fh.write(line + "\n")
    print(f"{DIM}unione: {out.relative_to(ROOT)}{RESET}")


# ---- report HTML ----

SERIES = [("dp", "PD tabella"), ("rolling", "PD rolling"), ("gurobi", "Gurobi")]


def nice_max(v):
    import math
    if v <= 0:
        return 1
    mag = 10 ** math.floor(math.log10(v))
    for m in (1, 2, 2.5, 5, 10):
        if v <= m * mag:
            return m * mag
    return 10 * mag


def line_chart(title, series, xlabel):
    """series: {key: [(x, y_ms), ...]} — SVG a linee, y in ms da 0."""
    W_, H, L, R, T, B = 460, 250, 56, 78, 12, 34
    pw, ph = W_ - L - R, H - T - B
    xs = sorted({x for pts in series.values() for x, _ in pts})
    if not xs:
        return ""
    x0, x1 = min(xs), max(xs)
    ymax = nice_max(max(y for pts in series.values() for _, y in pts) * 1.05)

    def X(x): return L + (x - x0) / (x1 - x0 or 1) * pw
    def Y(y): return T + ph - y / ymax * ph

    svg = [f'<svg viewBox="0 0 {W_} {H}" role="img" aria-label="{title}">']
    # griglia orizzontale + tick y
    for i in range(5):
        y = ymax * i / 4
        yy = Y(y)
        svg.append(f'<line x1="{L}" y1="{yy:.1f}" x2="{L+pw}" y2="{yy:.1f}" class="grid"/>')
        lbl = f"{y:g}" if ymax < 100 else fmt(y)
        svg.append(f'<text x="{L-7}" y="{yy+3:.1f}" class="tick" text-anchor="end">{lbl}</text>')
    # tick x
    for x in xs[1::2] if len(xs) > 6 else xs:
        svg.append(f'<text x="{X(x):.1f}" y="{T+ph+16}" class="tick" text-anchor="middle">{fmt(x)}</text>')
    svg.append(f'<text x="{L+pw/2}" y="{H-4}" class="tick" text-anchor="middle">{xlabel}</text>')
    svg.append(f'<text x="{L-40}" y="{T+2}" class="tick">ms</text>')
    svg.append(f'<line x1="{L}" y1="{T}" x2="{L}" y2="{T+ph}" class="axis"/>')
    svg.append(f'<line x1="{L}" y1="{T+ph}" x2="{L+pw}" y2="{T+ph}" class="axis"/>')

    endlbl = []
    for key, label in SERIES:
        pts = series.get(key)
        if not pts:
            continue
        path = " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in pts)
        svg.append(f'<polyline points="{path}" class="ln s-{key}"/>')
        endlbl.append([key, label, X(pts[-1][0]) + 6, Y(pts[-1][1]) + 3])
        for x, y in pts:
            tip = f"{label} — {xlabel.split()[0]}={fmt(x)}: {y:.2f} ms"
            svg.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="3" class="pt s-{key}"/>')
            svg.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="10" class="hit" data-tip="{tip}"/>')
    # anti-collisione: etichette di fine linea distanziate di almeno 13 px
    endlbl.sort(key=lambda e: e[3])
    for i in range(1, len(endlbl)):
        if endlbl[i][3] - endlbl[i - 1][3] < 13:
            endlbl[i][3] = endlbl[i - 1][3] + 13
    for key, label, lx, ly in endlbl:
        svg.append(f'<circle cx="{lx}" cy="{ly-3}" r="3.5" class="dot s-{key}"/>')
        svg.append(f'<text x="{lx+7}" y="{ly}" class="slabel">{label}</text>')
    svg.append("</svg>")
    return "\n".join(svg)


def build_report(charts, limits_rows, plat, gurobi_ok):
    legend = "".join(
        f'<span class="leg"><span class="dot s-{k}"></span>{l}</span>'
        for k, l in SERIES if gurobi_ok or k != "gurobi")

    lim_html = "".join(
        f"<tr><td>{fmt(r['W'])}</td>"
        f"<td>{fmt_bytes(r['table_bytes'])}</td>"
        f"<td class=\"{'bad' if r['base'] == 'OOM' else ''}\">{r['base']}</td>"
        f"<td>{fmt_bytes(r['rolling_bytes'])}</td><td>{r['rolling']}</td></tr>"
        for r in limits_rows)

    plat_html = " · ".join(f"<b>{k}</b> {v}" for k, v in plat.items() if k != "Metodo")

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Campagna sperimentale — Zaino 0/1</title>
<style>
.viz-root {{
  --page:#f9f9f7; --surface:#fcfcfb; --ink:#0b0b0b; --ink-2:#52514e;
  --muted:#898781; --gridln:#e1e0d9; --axis:#c3c2b7; --ring:rgba(11,11,11,.10);
  --bad:#d03b3b;
  --c-dp:#2a78d6; --c-rolling:#1baf7a; --c-gurobi:#008300;
}}
@media (prefers-color-scheme: dark) {{
  .viz-root {{
    --page:#0d0d0d; --surface:#1a1a19; --ink:#fff; --ink-2:#c3c2b7;
    --muted:#898781; --gridln:#2c2c2a; --axis:#383835; --ring:rgba(255,255,255,.10);
    --bad:#e66767;
    --c-dp:#3987e5; --c-rolling:#199e70; --c-gurobi:#008300;
  }}
}}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
       background:var(--page); color:var(--ink); padding:2rem 1.5rem 3rem; }}
.wrap {{ max-width:1040px; margin:0 auto; }}
h1 {{ font-size:1.25rem; }}
.sub {{ color:var(--ink-2); font-size:.8rem; margin-top:.35rem; line-height:1.5; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(420px,1fr));
        gap:1rem; margin-top:1.4rem; }}
.card {{ background:var(--surface); border:1px solid var(--ring);
        border-radius:10px; padding:1rem 1.1rem; }}
.card h2 {{ font-size:.8rem; font-weight:600; color:var(--ink-2); margin-bottom:.2rem; }}
.card .legend {{ margin:.3rem 0 .5rem; }}
.leg {{ font-size:.72rem; color:var(--ink-2); margin-right:.9rem; }}
.leg .dot {{ margin-right:.35rem; }}
.dot {{ display:inline-block; width:9px; height:9px; border-radius:50%; vertical-align:baseline; }}
svg {{ width:100%; height:auto; display:block; }}
line.grid {{ stroke:var(--gridln); stroke-width:1; }}
line.axis {{ stroke:var(--axis); stroke-width:1.5; }}
.tick {{ font-size:9.5px; fill:var(--muted); font-variant-numeric:tabular-nums; }}
.slabel {{ font-size:10px; fill:var(--ink-2); }}
.ln {{ fill:none; stroke-width:2; }}
.pt {{ stroke-width:2; fill:var(--surface); }}
.hit {{ fill:transparent; }}
.s-dp.ln,.s-dp.pt {{ stroke:var(--c-dp); }}     .dot.s-dp {{ background:var(--c-dp); fill:var(--c-dp); }}
.s-rolling.ln,.s-rolling.pt {{ stroke:var(--c-rolling); }} .dot.s-rolling {{ background:var(--c-rolling); fill:var(--c-rolling); }}
.s-gurobi.ln,.s-gurobi.pt {{ stroke:var(--c-gurobi); }} .dot.s-gurobi {{ background:var(--c-gurobi); fill:var(--c-gurobi); }}
.note {{ margin-top:.6rem; font-size:.7rem; color:var(--muted); line-height:1.5; }}
table {{ border-collapse:collapse; width:100%; font-size:.8rem; margin-top:.6rem; }}
th {{ text-align:left; color:var(--muted); font-weight:600; font-size:.68rem;
     padding:.3rem .55rem; border-bottom:1px solid var(--ring); }}
td {{ padding:.32rem .55rem; border-bottom:1px solid var(--ring);
     font-variant-numeric:tabular-nums; }}
td.bad {{ color:var(--bad); font-weight:700; }}
.plat {{ margin-top:1.3rem; font-size:.72rem; color:var(--muted); line-height:1.6; }}
.plat b {{ color:var(--ink-2); font-weight:600; }}
#tip {{ position:fixed; display:none; background:var(--ink); color:var(--page);
       font-size:.74rem; padding:.3rem .55rem; border-radius:6px;
       pointer-events:none; z-index:10; }}
</style>
</head>
<body class="viz-root">
<div class="wrap">
  <h1>Campagna sperimentale — Zaino 0/1 in PD</h1>
  <div class="sub">Verifica empirica dell'analisi Θ(n·W): tempo al crescere di n e di W
  (separatamente), confronto con Gurobi sugli stessi punti, limiti di memoria della
  tabella completa. Mediane su più ripetizioni, istanze riproducibili (seed {SEED}).</div>

  <div class="grid">
    <section class="card">
      <h2>Tempo vs n — W fisso a {fmt(N_SWEEP['fixed'])}</h2>
      <div class="legend">{legend}</div>
      {charts['n']}
      <p class="note">Atteso: crescita lineare in n per le due PD (Θ(n·W) con W costante).</p>
    </section>
    <section class="card">
      <h2>Tempo vs W — n fisso a {fmt(W_SWEEP['fixed'])}</h2>
      <div class="legend">{legend}</div>
      {charts['w']}
      <p class="note">Atteso: crescita lineare in W per le due PD; Gurobi è
      quasi insensibile a W — è qui che si vede la pseudo-polinomialità.</p>
    </section>
  </div>

  <section class="card" style="margin-top:1rem;">
    <h2>Limiti pratici — n = {fmt(LIMITS_N)}, heap {LIMITS_HEAP}, W molto grande</h2>
    <table>
      <thead><tr><th>W</th><th>Tabella (n+1)(W+1)·8</th><th>Esito tabella</th>
      <th>Rolling (W+1)·8</th><th>Esito rolling</th></tr></thead>
      <tbody>{lim_html}</tbody>
    </table>
    <p class="note">La variante rolling estende le dimensioni delle istanze elaborabili
    (richiesta del Compito 2): dove la tabella supera la memoria disponibile (OOM),
    il rolling array continua a funzionare — al prezzo della sola perdita della
    ricostruzione della soluzione.</p>
  </section>

  <div class="plat">
    <b>Piattaforma</b> · {plat_html}<br>
    <b>Metodo</b> · {plat['Metodo']}<br>
    Dati grezzi: <b>data/campagna/*.csv</b> (anche uniti in <b>tutti.csv</b>, pronti per Excel).
  </div>
</div>
<div id="tip"></div>
<script>
'use strict';
var tip = document.getElementById('tip');
document.querySelectorAll('.hit[data-tip]').forEach(function (el) {{
  el.addEventListener('mousemove', function (e) {{
    tip.textContent = el.getAttribute('data-tip');
    tip.style.display = 'block';
    tip.style.left = Math.min(e.clientX + 14, window.innerWidth - 260) + 'px';
    tip.style.top = (e.clientY + 14) + 'px';
  }});
  el.addEventListener('mouseleave', function () {{ tip.style.display = 'none'; }});
}});
</script>
</body>
</html>
"""


def main():
    if not (ROOT / "bin").is_dir():
        sys.exit(RED + "bin/ non trovato: ./compile.sh prima" + RESET)
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    run_dp_sweeps()
    gurobi_ok = run_gurobi_sweeps()
    limits_rows = run_limits()
    merge_all(gurobi_ok)

    # ── grafici ──
    step_title("Report")
    charts = {}
    for tag, dp_file, g_file, xlabel in (
            ("n", OUT / "dp_n.csv", OUT / "gurobi_n.csv", "n (oggetti)"),
            ("w", OUT / "dp_w.csv", OUT / "gurobi_w.csv", "W (capacità)")):
        series = {"dp": [], "rolling": [], "gurobi": []}
        xcol = "n" if tag == "n" else "W"
        for r in read_rows(dp_file):
            series[r["algo"] if r["algo"] != "base" else "dp"].append(
                (int(r[xcol]), float(r["ms_min"])))
        if gurobi_ok and g_file.exists():
            for r in read_rows(g_file):
                series["gurobi"].append((int(r[xcol]), float(r["ms_min"])))
        for pts in series.values():
            pts.sort()
        charts[tag] = line_chart(tag, series, xlabel)

    plat = platform_info()
    report = OUT / "report.html"
    report.write_text(build_report(charts, limits_rows, plat, gurobi_ok), encoding="utf-8")
    print(f"  {report.relative_to(ROOT)} ✓   {DIM}(campagna completata in {time.time()-t0:.0f} s){RESET}")
    if not os.environ.get("CAMPAGNA_NO_OPEN"):
        subprocess.run(["open", str(report)], check=False)


if __name__ == "__main__":
    main()
