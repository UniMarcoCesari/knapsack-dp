#!/usr/bin/env python3
"""grafici.py — figure della sperimentazione per la relazione.

Legge i CSV prodotti da campagna.py (data/campagna/) e scrive tre PDF
vettoriali in relazione/fig/:

  tempo-vs-n.pdf    tempo al crescere di n, W fisso   (PD tabella, PD rolling, Gurobi)
  tempo-vs-W.pdf    tempo al crescere di W, n fisso   (idem)
  memoria.pdf       memoria della tabella, teorica e misurata, contro il rolling

Uso:  ./grafici.py
"""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parent
DATI = ROOT / "data" / "campagna"
FIG = ROOT / "relazione" / "fig"

# Palette validata (validate_palette.js, modalità light): banda di luminosità,
# soglia di croma, separazione per daltonismo e contrasto sul fondo, tutti PASS.
BLU, VERDE, ORO = "#2F6FBF", "#2E7D4F", "#B8860B"
INCHIOSTRO, SMORZATO, GRIGLIA = "#2B2B28", "#5A5A5A", "#DCDCD8"

plt.rcParams.update({
    # disegnate alla larghezza finale (\linewidth = 15,9 cm): incluse a scala 1:1,
    # le scritte restano a 8,5 pt contro gli 11 pt del corpo del testo
    "figure.figsize": (6.26, 3.4),
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans"],
    "font.size": 8.5,
    "axes.edgecolor": SMORZATO,
    "axes.labelcolor": INCHIOSTRO,
    "text.color": INCHIOSTRO,
    "xtick.color": SMORZATO,
    "ytick.color": SMORZATO,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.autolayout": False,
})


def leggi(nome):
    with open(DATI / nome) as f:
        return list(csv.DictReader(f))


def serie(righe, algo, x):
    r = [riga for riga in righe if riga["algo"] == algo]
    return [float(riga[x]) for riga in r], [float(riga["ms_mediana"]) for riga in r]


def telaio(ax, xlabel, ylabel):
    ax.grid(axis="y", color=GRIGLIA, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(length=3, width=0.6)


def etichetta(ax, x, y, testo, dy=0):
    """Etichetta diretta a fine curva: il testo resta in inchiostro neutro,
    l'identità la porta il segno colorato accanto."""
    ax.annotate(testo, xy=(x, y), xytext=(6, dy), textcoords="offset points",
                va="center", ha="left", fontsize=8, color=INCHIOSTRO)


def etichette_separate(fig, ax, voci, minimo=11):
    """Etichette a fine curva, scostate quanto basta a non sovrapporsi.
    `voci` = [(x, y, testo)]; `minimo` è la distanza verticale minima in punti."""
    fig.canvas.draw()
    altezze = [ax.transData.transform((x, y))[1] for x, y, _ in voci]
    ordine = sorted(range(len(voci)), key=lambda i: altezze[i])
    spostate = list(altezze)
    for k, i in enumerate(ordine):
        if k and spostate[i] - spostate[ordine[k - 1]] < minimo:
            spostate[i] = spostate[ordine[k - 1]] + minimo
    for i, (x, y, testo) in enumerate(voci):
        etichetta(ax, x, y, testo, dy=spostate[i] - altezze[i])


def grafico_tempo(sweep, xlabel, fisso, uscita):
    dp = leggi(f"dp_{sweep}.csv")
    grb = leggi(f"gurobi_{sweep}.csv")
    var = "n" if sweep == "n" else "W"

    fig, ax = plt.subplots()
    voci = []
    for algo, righe, colore, marker, nome in (
            ("base", dp, BLU, "o", "PD tabella"),
            ("rolling", dp, VERDE, "s", "PD rolling"),
            ("gurobi", grb, ORO, "^", "Gurobi")):
        xs, ys = serie(righe, algo, var)
        ax.plot(xs, ys, color=colore, linewidth=2, marker=marker,
                markersize=4.5, markeredgecolor="white", markeredgewidth=0.6,
                clip_on=False, zorder=3)
        voci.append((xs[-1], ys[-1], nome))

    telaio(ax, xlabel, "tempo (ms)")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", " ")))
    ax.text(0.0, 1.06, fisso, transform=ax.transAxes, fontsize=8, color=SMORZATO)
    fig.subplots_adjust(left=0.10, right=0.80, top=0.90, bottom=0.16)
    etichette_separate(fig, ax, voci)
    fig.savefig(FIG / uscita)
    plt.close(fig)
    print(f"  {uscita} ✓")


def grafico_memoria(uscita):
    dp = leggi("dp_n.csv")
    base = [r for r in dp if r["algo"] == "base"]
    roll = [r for r in dp if r["algo"] == "rolling"]
    ns = [float(r["n"]) for r in base]

    fig, ax = plt.subplots()
    ax.plot(ns, [float(r["mem_teorica"]) for r in base], color=BLU, linewidth=2,
            zorder=3, clip_on=False)
    ax.plot(ns, [float(r["mem_misurata"]) for r in base], color=BLU, linewidth=0,
            marker="o", markersize=5, markerfacecolor="white",
            markeredgewidth=1.4, markeredgecolor=BLU, zorder=4, clip_on=False)
    # senza marcatori: nel grafico i marcatori indicano le misure, e per il
    # rolling la misura sull'heap non è significativa (vedi limitazioni)
    ax.plot(ns, [float(r["mem_teorica"]) for r in roll], color=VERDE, linewidth=2,
            zorder=3, clip_on=False)

    etichetta(ax, ns[-1], float(base[-1]["mem_teorica"]), "tabella\nΘ(nW)", dy=6)
    etichetta(ax, ns[-1], float(roll[-1]["mem_teorica"]), "rolling\nΘ(W)", dy=0)

    ax.set_yscale("log")
    telaio(ax, "n (numero di oggetti)", "memoria")
    ax.set_yticks([1e4, 1e5, 1e6, 1e7, 1e8])
    ax.set_yticklabels(["10 KB", "100 KB", "1 MB", "10 MB", "100 MB"])
    ax.set_xlim(left=0)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", " ")))
    ax.text(0.0, 1.06, "W = 1000 fisso · scala logaritmica · linea = formula, "
            "cerchi = misura sull'heap",
            transform=ax.transAxes, fontsize=8, color=SMORZATO)
    fig.subplots_adjust(left=0.13, right=0.82, top=0.90, bottom=0.16)
    fig.savefig(FIG / uscita)
    plt.close(fig)
    print(f"  {uscita} ✓")


if __name__ == "__main__":
    FIG.mkdir(parents=True, exist_ok=True)
    print("Figure in relazione/fig/:")
    grafico_tempo("n", "n (numero di oggetti)", "W = 1000 fisso", "tempo-vs-n.pdf")
    grafico_tempo("w", "W (capacità dello zaino)", "n = 1000 fisso", "tempo-vs-W.pdf")
    grafico_memoria("memoria.pdf")
