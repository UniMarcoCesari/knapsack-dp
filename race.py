#!/usr/bin/env python3
"""race.py — genera un'istanza dello zaino e fa gareggiare gli algoritmi
IN PARALLELO: PD tabella, PD rolling, brute force, Gurobi (ILP).

Uso:
    ./race.py <n> <W> [seed] [--plot]

    --plot   genera anche una pagina HTML con due grafici a barre
             (tempo e memoria) e la apre nel browser.

Output: una riga per algoritmo (valore ottimo, tempo del solo algoritmo,
memoria delle strutture dati, durata del processo) e il verdetto.
Solo libreria standard; richiede il progetto compilato (./compile.sh).
"""
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parent
BIN = ROOT / "bin"
GUROBI_HOME = Path(os.environ.get("GUROBI_HOME", "/Library/gurobi1203/macos_universal2"))
GUROBI_JAR = GUROBI_HOME / "lib" / "gurobi.jar"

DIM, RESET, GREEN, RED, YELLOW = "\033[2m", "\033[0m", "\033[32m", "\033[31m", "\033[33m"
THIN = " "  # spazio sottile: separatore delle migliaia


def die(msg):
    print(RED + msg + RESET, file=sys.stderr)
    sys.exit(1)


def run_job(cmd):
    """Esegue un processo, ritorna (wall_ms, returncode, stdout+stderr)."""
    t0 = time.perf_counter()
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    wall = (time.perf_counter() - t0) * 1000
    return wall, p.returncode, (p.stdout + p.stderr).strip()


def parse_kv(text, key):
    m = re.search(rf"{key}=([0-9.]+)", text)
    return float(m.group(1)) if m else None


def fmt(x):
    """Separatore delle migliaia con spazio sottile (solo sul numero)."""
    return f"{int(x):,}".replace(",", THIN)


def fmt_bytes(b):
    """Byte in forma leggibile (B/KB/MB/GB)."""
    b = float(b)
    for unit in ("B", "KB", "MB"):
        if b < 1024:
            return f"{int(b)} B" if unit == "B" else f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.2f} GB"


def fmt_ms(ms):
    return f"{ms:,.2f}".replace(",", THIN) + " ms"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    unknown = flags - {"--plot"}
    if unknown:
        die("flag sconosciuti: " + " ".join(sorted(unknown)))
    if len(args) < 2:
        print(__doc__)
        sys.exit(2)
    n, W = int(args[0]), int(args[1])
    seed = int(args[2]) if len(args) > 2 else 42
    want_plot = "--plot" in flags

    if not BIN.is_dir():
        die("bin/ non trovato: compila prima con ./compile.sh")

    # ── istanza: nome univoco dai parametri; se esiste già la riusiamo
    #    (stesso seed → stessa istanza, la generazione è deterministica) ──
    inst = ROOT / "data" / f"race_n{n}_W{W}_s{seed}.txt"
    if inst.exists():
        origin = "già presente, riusata"
    else:
        gen = subprocess.run(
            ["java", "-cp", "bin", "knapsack.Main", "generate", str(n), str(W), str(seed),
             "-o", str(inst)], cwd=ROOT, capture_output=True, text=True)
        if gen.returncode != 0:
            die("generazione fallita:\n" + gen.stderr)
        origin = "generata"

    print(f"Istanza: n={n}  W={W}  seed={seed}   ({inst.relative_to(ROOT)}, {origin})")
    print(f"{DIM}avvio in parallelo: PD tabella · PD rolling · brute force · Gurobi …{RESET}\n")

    # ── i concorrenti ──
    jobs = {
        "dp": ["java", "-Xmx4g", "-cp", "bin", "knapsack.Main", "dp", str(inst)],
        "rolling": ["java", "-cp", "bin", "knapsack.Main", "rolling", str(inst)],
        "brute": ["java", "-cp", "bin", "knapsack.Main", "brute", str(inst)],
        "gurobi": ["java", "-cp", f"bin:{GUROBI_JAR}",
                   "knapsack.gurobi.GurobiSolver", "--porcelain", str(inst)],
    }
    gurobi_ok = GUROBI_JAR.is_file() and (BIN / "knapsack" / "gurobi").is_dir()
    if not gurobi_ok:
        jobs.pop("gurobi")

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {name: pool.submit(run_job, cmd) for name, cmd in jobs.items()}
        results = {name: f.result() for name, f in futures.items()}

    # ── righe di esito ──
    values = {}
    plotrows = []   # per --plot: {key,label,ms,mem,note}

    def line(label, name, time_key, memo_note="—"):
        if name not in results:
            print(f"{label:<26} {YELLOW}non disponibile (gurobi.jar o modulo mancante){RESET}")
            plotrows.append(dict(key=name, label=label, ms=None, mem=None, note="non disponibile"))
            return
        wall, rc, out = results[name]
        if name == "brute" and rc == 3:
            print(f"{label:<26} {YELLOW}saltato: n={n} > 25, 2^n intrattabile{RESET}"
                  f"   {DIM}(è il motivo per cui esiste la PD){RESET}")
            plotrows.append(dict(key=name, label=label, ms=None, mem=None,
                                 note="saltato: 2ⁿ intrattabile"))
            return
        if rc != 0:
            tail = out.splitlines()[-1] if out else ""
            print(f"{label:<26} {RED}errore (exit {rc}){RESET}  {DIM}{tail}{RESET}")
            plotrows.append(dict(key=name, label=label, ms=None, mem=None, note="errore"))
            return
        val = parse_kv(out, "valore")
        ms = parse_kv(out, time_key)
        mem = parse_kv(out, "mem")
        mem_txt = fmt_bytes(mem) if mem is not None else memo_note
        values[name] = int(val) if val is not None else None
        print(f"{label:<26} valore = {fmt(val):<12} algoritmo {ms:>10.2f} ms"
              f"   memoria {mem_txt:>9}   {DIM}(processo {fmt(wall)} ms){RESET}")
        plotrows.append(dict(key=name, label=label, ms=ms, mem=mem,
                             note=None if mem is not None else memo_note))

    line("PD tabella   spazio Θ(nW)", "dp", "ms")
    line("PD rolling   spazio Θ(W)", "rolling", "ms")
    line("Brute force  Θ(2ⁿ·n)", "brute", "ms", memo_note="O(1)")
    line("Gurobi       ILP, B&B", "gurobi", "solve_ms", memo_note="n/d")

    # ── verdetto ──
    print()
    vals = {v for v in values.values() if v is not None}
    if len(values) >= 2 and len(vals) == 1:
        verdict = f"{len(values)} algoritmi, stesso valore ottimo: {fmt(vals.pop())}"
        print(f"{GREEN}✓ {verdict}{RESET}")
        exit_code = 0
    elif len(vals) > 1:
        print(f"{RED}✗ DISACCORDO: {values} — qualcosa è rotto!{RESET}")
        verdict = "DISACCORDO tra gli algoritmi!"
        exit_code = 1
    else:
        verdict = "un solo algoritmo eseguito: nessun confronto"
        print(f"{DIM}({verdict}){RESET}")
        exit_code = 0

    if want_plot:
        html = build_plot_html(n, W, seed, plotrows, verdict, exit_code == 0)
        out = ROOT / "data" / f"race_n{n}_W{W}_s{seed}.html"
        out.write_text(html, encoding="utf-8")
        print(f"{DIM}grafico: {out.relative_to(ROOT)}{RESET}")
        if not os.environ.get("RACE_NO_OPEN"):
            subprocess.run(["open", str(out)], check=False)

    sys.exit(exit_code)


# ---- --plot: pagina HTML con i due grafici a barre (tempo, memoria) ----

def bar_rows(rows, kind):
    """kind = 'ms' | 'mem'. Barre orizzontali; riga senza dato → nota muta."""
    present = [r[kind] for r in rows if r[kind] is not None]
    top = max(present) if present else 1
    out = []
    for r in rows:
        v = r[kind]
        if v is None:
            reason = r["note"] or "—"
            if kind == "mem" and r["key"] == "brute" and r["ms"] is not None:
                reason = "O(1) — nessuna struttura dati"
            if kind == "mem" and r["key"] == "gurobi" and r["ms"] is not None:
                reason = "n/d — memoria interna del solver"
            out.append(
                f'<div class="row muted"><span class="lbl">{r["label"]}</span>'
                f'<span class="track"></span><span class="val">{reason}</span></div>')
            continue
        pct = max(0.8, v / top * 100)
        shown = fmt_ms(v) if kind == "ms" else fmt_bytes(v)
        tip = f'{r["label"]} — {shown}' + (f' ({fmt(v)} byte esatti)' if kind == "mem" else "")
        out.append(
            f'<div class="row" data-tip="{tip}"><span class="lbl">{r["label"]}</span>'
            f'<span class="track"><span class="fill c-{r["key"]}" style="width:{pct:.2f}%"></span></span>'
            f'<span class="val">{shown}</span></div>')
    return "\n".join(out)


def table_rows(rows):
    out = []
    for r in rows:
        ms = fmt_ms(r["ms"]) if r["ms"] is not None else (r["note"] or "—")
        mem = fmt_bytes(r["mem"]) + f" ({fmt(r['mem'])} B)" if r["mem"] is not None else "—"
        out.append(f"<tr><td><span class='dot c-{r['key']}'></span>{r['label']}</td>"
                   f"<td>{ms}</td><td>{mem}</td></tr>")
    return "\n".join(out)


def build_plot_html(n, W, seed, rows, verdict, ok):
    # etichette brevi per i grafici
    short = {"dp": "PD tabella", "rolling": "PD rolling", "brute": "Brute force", "gurobi": "Gurobi (ILP)"}
    rows = [dict(r, label=short.get(r["key"], r["label"])) for r in rows]

    notes_time = []
    if any(r["key"] == "brute" and r["ms"] is None for r in rows):
        notes_time.append("Brute force saltato: con n = " + str(n) +
                          " i 2ⁿ sottoinsiemi sono intrattabili.")
    notes_mem = ["Memoria PD calcolata esatta: tabella (n+1)(W+1)·8 byte, rolling (W+1)·8 byte."]

    tpl = Template(r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Zaino 0/1 — n=$n W=$W</title>
<style>
.viz-root {
  --page:      #f9f9f7;
  --surface:   #fcfcfb;
  --ink:       #0b0b0b;
  --ink-2:     #52514e;
  --muted:     #898781;
  --baseline:  #c3c2b7;
  --ring:      rgba(11,11,11,0.10);
  --ok:        #006300;
  --c-dp:      #2a78d6;
  --c-rolling: #1baf7a;
  --c-brute:   #eda100;
  --c-gurobi:  #008300;
}
@media (prefers-color-scheme: dark) {
  .viz-root {
    --page:      #0d0d0d;
    --surface:   #1a1a19;
    --ink:       #ffffff;
    --ink-2:     #c3c2b7;
    --muted:     #898781;
    --baseline:  #383835;
    --ring:      rgba(255,255,255,0.10);
    --ok:        #0ca30c;
    --c-dp:      #3987e5;
    --c-rolling: #199e70;
    --c-brute:   #c98500;
    --c-gurobi:  #008300;
  }
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  background: var(--page);
  color: var(--ink);
  padding: 2rem 1.5rem 3rem;
}
.wrap { max-width: 980px; margin: 0 auto; }
h1 { font-size: 1.25rem; font-weight: 700; }
.sub { color: var(--ink-2); font-size: .85rem; margin-top: .3rem; }
.sub .mono { font-variant-numeric: tabular-nums; }
.verdict { margin-top: .5rem; font-size: .85rem; font-weight: 600; color: $verdict_color; }
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 1rem;
  margin-top: 1.5rem;
}
.card {
  background: var(--surface);
  border: 1px solid var(--ring);
  border-radius: 10px;
  padding: 1.1rem 1.2rem 1rem;
}
.card h2 { font-size: .8rem; font-weight: 600; color: var(--ink-2); margin-bottom: .9rem; }
.row {
  display: grid;
  grid-template-columns: 92px 1fr auto;
  align-items: center;
  gap: .6rem;
  padding: .3rem 0;
}
.lbl { font-size: .78rem; color: var(--ink-2); }
.track {
  height: 22px;
  border-left: 2px solid var(--baseline);
  display: flex;
  align-items: center;
}
.fill {
  height: 100%;
  border-radius: 0 4px 4px 0;   /* arrotondata solo sul lato del valore */
  min-width: 2px;
}
.val { font-size: .8rem; font-variant-numeric: tabular-nums; color: var(--ink); white-space: nowrap; }
.row.muted .val { color: var(--muted); font-size: .74rem; }
.c-dp      { background: var(--c-dp); }
.c-rolling { background: var(--c-rolling); }
.c-brute   { background: var(--c-brute); }
.c-gurobi  { background: var(--c-gurobi); }
.note { margin-top: .8rem; font-size: .7rem; color: var(--muted); line-height: 1.5; }
details { margin-top: 1.2rem; }
summary { font-size: .8rem; color: var(--ink-2); cursor: pointer; }
table { border-collapse: collapse; margin-top: .6rem; font-size: .8rem; width: 100%; }
th { text-align: left; color: var(--muted); font-weight: 600; font-size: .7rem;
     padding: .3rem .6rem; border-bottom: 1px solid var(--ring); }
td { padding: .35rem .6rem; border-bottom: 1px solid var(--ring);
     font-variant-numeric: tabular-nums; }
.dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%;
       margin-right: .45rem; vertical-align: baseline; }
#tip {
  position: fixed;
  display: none;
  background: var(--ink);
  color: var(--page);
  font-size: .74rem;
  padding: .3rem .55rem;
  border-radius: 6px;
  pointer-events: none;
  z-index: 10;
  max-width: 320px;
}
</style>
</head>
<body class="viz-root">
<div class="wrap">
  <h1>Zaino 0/1 — gara degli algoritmi</h1>
  <div class="sub mono">istanza: n = $n · W = $W · seed = $seed</div>
  <div class="verdict">$verdict_mark $verdict</div>

  <div class="grid">
    <section class="card">
      <h2>Tempo dell'algoritmo</h2>
      $time_rows
      <p class="note">$notes_time</p>
    </section>
    <section class="card">
      <h2>Memoria delle strutture dati</h2>
      $mem_rows
      <p class="note">$notes_mem</p>
    </section>
  </div>

  <details>
    <summary>Dati in tabella</summary>
    <table>
      <thead><tr><th>Algoritmo</th><th>Tempo</th><th>Memoria</th></tr></thead>
      <tbody>
      $table_rows
      </tbody>
    </table>
  </details>
</div>
<div id="tip"></div>
<script>
'use strict';
var tip = document.getElementById('tip');
document.querySelectorAll('.row[data-tip]').forEach(function (row) {
  row.addEventListener('mousemove', function (e) {
    tip.textContent = row.getAttribute('data-tip');
    tip.style.display = 'block';
    tip.style.left = Math.min(e.clientX + 14, window.innerWidth - 330) + 'px';
    tip.style.top = (e.clientY + 14) + 'px';
  });
  row.addEventListener('mouseleave', function () { tip.style.display = 'none'; });
});
</script>
</body>
</html>
""")
    return tpl.substitute(
        n=fmt(n), W=fmt(W), seed=seed,
        verdict=verdict,
        verdict_mark="✓" if ok else "✗",
        verdict_color="var(--ok)" if ok else "#d03b3b",
        time_rows=bar_rows(rows, "ms"),
        mem_rows=bar_rows(rows, "mem"),
        notes_time=" ".join(notes_time) or "Tempo del solo algoritmo (esclusi avvio JVM e I/O).",
        notes_mem=" ".join(notes_mem),
        table_rows=table_rows(rows),
    )


if __name__ == "__main__":
    main()
