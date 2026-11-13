"""Publication figures (PNG + PDF). Fixed categorical order per verifier; one axis per chart."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# fixed categorical order (validated reference palette, light mode); colour follows the verifier
COLORS = {"V1E": "#2a78d6", "V1F": "#eb6834", "V2": "#1baf7a", "V3": "#eda100", "V3a": "#e87ba4"}
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
NAMES = {"V1E": "V1E (review Eq. 2)", "V1F": "V1F (review Eqs. 2-5)", "V2": "V2 (Naser)",
         "V3": "V3 (Neralla et al.)", "V3a": "V3a (author veto)"}


def _style(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _save(fig, out: Path, stem: str):
    out.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(out / f"{stem}.{ext}", dpi=200, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)


def rate_with_ci(rows: list[dict], title: str, ylabel: str, out: Path, stem: str):
    """rows: [{'v': 'V1E', 'rate': .., 'lo': .., 'hi': ..}] -> dot + whisker per verifier."""
    fig, ax = plt.subplots(figsize=(6.2, 3.2))
    _style(ax)
    for i, r in enumerate(rows):
        c = COLORS[r["v"]]
        ax.plot([i, i], [r["lo"], r["hi"]], color=c, linewidth=2, solid_capstyle="round")
        ax.plot(i, r["rate"], "o", color=c, markersize=8, markeredgecolor=SURFACE, markeredgewidth=2)
        ax.annotate(f"{100*r['rate']:.1f}%", (i, r["hi"]), textcoords="offset points",
                    xytext=(0, 5), ha="center", fontsize=8, color=INK)
    ax.set_xticks(range(len(rows)), [NAMES[r["v"]] for r in rows], rotation=15, ha="right")
    ax.set_ylabel(ylabel, color=INK2, fontsize=9)
    ax.set_ylim(0, max(0.05, max(r["hi"] for r in rows) * 1.25))
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.set_title(title, loc="left", fontsize=10, color=INK)
    _save(fig, out, stem)


def ppv_curves(curves: dict, pis: list[float], out: Path, stem: str = "ppv_by_prevalence"):
    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    _style(ax)
    for v, ys in curves.items():
        ax.plot([100 * p for p in pis], ys, "-o", color=COLORS[v], linewidth=2, markersize=5,
                label=NAMES[v])
    ax.set_xlabel("share of citations that are fabricated, π (%)", color=INK2, fontsize=9)
    ax.set_ylabel("PPV (share of flags that are correct)", color=INK2, fontsize=9)
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_title("PPV at realistic prevalence (review Eq. 13)", loc="left", fontsize=10, color=INK)
    _save(fig, out, stem)


def tau_sweep(sweeps: dict, out: Path, stem: str = "tau_sweep"):
    """sweeps: {verifier: {'t': [...], 'fpr': [...], 'recall': [...]}} -> one panel per verifier."""
    vs = list(sweeps)
    fig, axes = plt.subplots(1, len(vs), figsize=(3.1 * len(vs), 3.0), sharey=True)
    axes = axes if len(vs) > 1 else [axes]
    for ax, v in zip(axes, vs):
        _style(ax)
        s = sweeps[v]
        ax.plot(s["t"], s["recall"], color=COLORS[v], linewidth=2, label="recall")
        ax.plot(s["t"], s["fpr"], color=COLORS[v], linewidth=2, linestyle=(0, (4, 2)), label="FPR")
        ax.set_title(NAMES[v], loc="left", fontsize=9, color=INK)
        ax.set_xlabel("flag threshold (score)", color=INK2, fontsize=8)
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    axes[0].legend(frameon=False, fontsize=8, loc="center left")
    _save(fig, out, stem)


def heatmap(row_labels, col_labels, values, title: str, out: Path, stem: str):
    """Sequential single-hue heatmap with value labels (values in [0, 1])."""
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("blue", ["#f4f8fd", "#86b6ef", "#2a78d6", "#0d366b"])
    fig, ax = plt.subplots(figsize=(1.1 * len(col_labels) + 1.6, 0.36 * len(row_labels) + 1.0))
    ax.imshow(values, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    for i, row in enumerate(values):
        for j, x in enumerate(row):
            ax.text(j, i, f"{100*x:.0f}%", ha="center", va="center", fontsize=8,
                    color="#ffffff" if x > 0.55 else INK)
    ax.set_xticks(range(len(col_labels)), col_labels, fontsize=8, color=INK2)
    ax.set_yticks(range(len(row_labels)), row_labels, fontsize=8, color=INK2)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(title, loc="left", fontsize=10, color=INK)
    _save(fig, out, stem)
