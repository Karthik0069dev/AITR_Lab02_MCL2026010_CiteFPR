"""Draw the study pipeline (paper Fig. 1) with matplotlib; replaces the hand-made Mermaid export.

Usage: python scripts/make_pipeline_figure.py --out paper/figures/pipeline
"""
import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

BOX, EDGE, INK, ACC = "#f2f2f2", "#888888", "#222222", "#1f6fb2"


def box(ax, x, y, w, h, text, fill=BOX, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                                fc=fill, ec=EDGE, lw=0.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=7.2, color=INK,
            fontweight="bold" if bold else "normal", linespacing=1.25)


def arrow(ax, x0, y0, x1, y1, style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, mutation_scale=8,
                                 color=EDGE, lw=0.9, linestyle=ls))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="paper/figures/pipeline")
    out = ap.parse_args().out
    fig, ax = plt.subplots(figsize=(7.0, 2.55))
    ax.set_xlim(0, 10); ax.set_ylim(-0.22, 3.6); ax.axis("off")
    # row 1: data and retrieval
    ax.text(0.05, 3.45, "Data and retrieval (network, run once)", fontsize=7, color=ACC, fontweight="bold")
    box(ax, 0.05, 2.45, 2.15, 0.75, "arXiv cs.CL 2020\n30 papers (seed 20261028)")
    box(ax, 0.05, 1.55, 2.15, 0.75, "CiteTracer ICLR 2026\n(commit 8c47ca5)")
    box(ax, 2.65, 2.45, 1.65, 0.75, "567 genuine refs\ncited .bib entries")
    box(ax, 2.65, 1.55, 1.65, 0.75, "807 fabricated\ncitations")
    box(ax, 4.9, 1.9, 2.55, 0.95, "retrieval, one pass per citation\nCrossref query + DOI lookups\nbatched arXiv IDs, arXiv title fallback")
    box(ax, 8.05, 1.9, 1.85, 0.95, "frozen cache\n+ candidates\n(SHA-256)", fill="#e3edf7", bold=True)
    for y in (2.82, 1.92):
        arrow(ax, 2.2, y, 2.65, y)
        arrow(ax, 4.3, y, 4.9, 2.37)
    arrow(ax, 7.45, 2.37, 8.05, 2.37)
    # frozen cache feeds the offline stage: route down the right margin, then left under the heading
    arrow(ax, 8.97, 1.9, 8.97, 1.0, style="-")
    arrow(ax, 8.97, 1.0, 1.2, 1.0, style="-")
    arrow(ax, 1.2, 1.0, 1.2, 0.95)
    # row 2: offline scoring and evaluation
    ax.text(0.05, 1.12, "Scoring and evaluation (offline, reproducible from the frozen files)", fontsize=7,
            color=ACC, fontweight="bold")
    box(ax, 0.05, 0.1, 2.3, 0.85, "score: V1E, V1F, V2,\nV3, V3a on identical\ncandidate lists")
    box(ax, 2.9, 0.1, 2.45, 0.85, "evaluate: FPR (Wilson,\npaper-cluster bootstrap), recall,\nPPV(π), exact McNemar, τ sweep")
    box(ax, 5.9, 0.1, 1.85, 0.85, "error analysis\nmechanisms A-D,\nidentifier strata")
    box(ax, 8.15, 0.1, 1.75, 0.85, "adjudication vs\nindependent sources\n(AI-assisted)")
    arrow(ax, 2.35, 0.52, 2.9, 0.52)
    arrow(ax, 5.35, 0.52, 5.9, 0.52)
    arrow(ax, 7.75, 0.52, 8.15, 0.52)
    arrow(ax, 9.1, -0.04, 4.15, -0.04, style="-|>", ls=(0, (2, 2)))   # adjudication feeds back into evaluate
    fig.tight_layout(pad=0.2)
    for ext in ("pdf", "png"):
        fig.savefig(f"{out}.{ext}", dpi=220)
    print(f"wrote {out}.pdf/.png")


if __name__ == "__main__":
    main()
