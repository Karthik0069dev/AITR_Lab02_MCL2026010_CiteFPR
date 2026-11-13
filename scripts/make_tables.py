"""Generate LaTeX tables for the paper from results/*.csv (no number is typed by hand).

Usage: python scripts/make_tables.py --results results --out paper/tables
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

V = ["V1E", "V1F", "V2", "V3", "V3a"]


def rd(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def pct(x, d=1):
    return f"{100 * float(x):.{d}f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--out", default="paper/tables")
    a = ap.parse_args()
    r, out = Path(a.results), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    m = {x["verifier"]: x for x in rd(r / "metrics.csv")}
    lines = [r"\begin{tabular}{lrrrr}", r"\toprule",
             r"Verifier & FP / $n$ & FPR (\%) & 95\% Wilson & Paper-cluster CI \\",
             r"\midrule"]
    for v in V:
        x = m[v]
        # from the counts, not the 4-dp 'fpr' field: double rounding shifted 91/567 to 16.1
        fpr = int(x["fp"]) / int(x["n_genuine"])
        lines.append(f"{v} & {x['fp']} / {x['n_genuine']} & {pct(fpr)} & "
                     f"[{pct(x['fpr_ci_lo'])}, {pct(x['fpr_ci_hi'])}] & "
                     f"[{pct(x['fpr_cluster_ci_lo'])}, {pct(x['fpr_cluster_ci_hi'])}] \\\\")
    lines += [r"\midrule", r"Verifier & \multicolumn{2}{r}{Recall (\%)} & \multicolumn{2}{r}{95\% Wilson} \\",
              r"\midrule"]
    for v in V:
        x = m[v]
        lo, hi = [float(t) for t in x["recall_ALL_FABRICATED_ci"].strip("[]").split(",")]
        lines.append(f"{v} & \\multicolumn{{2}}{{r}}{{{pct(x['recall_ALL_FABRICATED'])}}} & "
                     f"\\multicolumn{{2}}{{r}}{{[{pct(lo)}, {pct(hi)}]}} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (out / "tab_fpr_recall.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    pp = rd(r / "ppv.csv")
    pis = sorted({float(x["pi"]) for x in pp})
    lines = [r"\begin{tabular}{l" + "r" * len(pis) + "}", r"\toprule",
             "Verifier & " + " & ".join(f"$\\pi={100 * p:g}\\%$" for p in pis) + r" \\", r"\midrule"]
    for v in V:
        row = {float(x["pi"]): x for x in pp if x["verifier"] == v}
        lines.append(v + " & " + " & ".join(f"{float(row[p]['ppv_eq13']):.3f}" for p in pis) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (out / "tab_ppv.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    bt = rd(r / "fp_by_entry_type.csv")
    lines = [r"\begin{tabular}{lr" + "r" * len(V) + "}", r"\toprule",
             "Entry type & $n$ & " + " & ".join(V) + r" \\", r"\midrule"]
    for x in bt:
        et = x["entry_type"].replace("_", r"\_")
        lines.append(f"{et} & {x['n']} & " + " & ".join(pct(x[f'{v}_fpr']) for v in V) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (out / "tab_fp_by_type.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    mc = rd(r / "mcnemar_fpr.csv")
    lines = [r"\begin{tabular}{lrrrrc}", r"\toprule",
             r"Pair & $a$ only & $b$ only & Gap (pts) & $p$ (exact) & Rule met \\", r"\midrule"]
    for x in mc:
        p = float(x["p_exact"])
        # exact binomial p underflows to 0 for 169+ one-sided pairs; report a bound, never "0"
        ps = f"{p:.3g}" if p >= 1e-4 else r"$<10^{-10}$"
        lines.append(f"{x['a']} vs {x['b']} & {x['a_only']} & {x['b_only']} & "
                     f"{100 * float(x['fpr_gap_a_minus_b']):+.1f} & {ps} & "
                     f"{'yes' if x['meets_rule'] == '1' else 'no'} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (out / "tab_mcnemar.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote 4 tables to {out}")


if __name__ == "__main__":
    main()
