"""LaTeX tables for the error analysis and the adjudication (paper Tables V and VI).

Reads results/fp_mechanisms.csv, fp_by_identifier.csv and fpr_adjudicated.csv; writes
paper/tables/tab_mechanisms.tex and tab_adjudication.tex. No number is typed by hand.

Usage: python scripts/make_tables_extra.py --results results --out paper/tables
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

V = ["V1E", "V1F", "V2", "V3", "V3a"]
NL = r" \\"


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

    mech = {x["verifier"]: x for x in rd(r / "fp_mechanisms.csv")}
    ident = rd(r / "fp_by_identifier.csv")
    L = [r"\begin{tabular}{lrrrrr}", r"\toprule",
         r"Verifier & FP & A: not retrieved & B: authors differ & C: field differs & D: near miss" + NL,
         r"\midrule"]
    for v in V:
        x = mech[v]
        L.append(f"{v} & {x['n_fp']} & {x['A']} & {x['B']} & {x['C']} & {x['D']}" + NL)
    L += [r"\bottomrule", r"\end{tabular}"]
    (out / "tab_mechanisms.tex").write_text("\n".join(L) + "\n", encoding="utf-8")

    L = [r"\begin{tabular}{lr" + "r" * len(V) + "}", r"\toprule",
         r"Citation carries & $n$ & " + " & ".join(V) + NL, r"\midrule"]
    names = {"has_doi": "a DOI", "has_arxiv_id": "an arXiv ID", "neither": "no identifier"}
    for x in ident:
        L.append(f"{names[x['stratum']]} & {x['n']} & "
                 + " & ".join(pct(x[f"{v}_fpr"]) for v in V) + NL)
    L += [r"\bottomrule", r"\end{tabular}"]
    (out / "tab_identifier.tex").write_text("\n".join(L) + "\n", encoding="utf-8")

    # baseline validation (gate G2): oracle retrieval on CiteTracer's synthetic set
    orc = {x["group"]: x for x in rd(r / "oracle" / "summary_by_subtype.csv")}
    rows = [("ALL_REAL", "Real R1--R3 (false positives)"),
            ("ALL_POTENTIAL", "Potential P1, P3 (false positives)"),
            ("H1", "H1 title altered"), ("H2", "H2 authors altered"),
            ("H3", "H3 venue altered"), ("H4", "H4 year altered"),
            ("H5", "H5 DOI fabricated"),
            ("H6", "H6 pages/volume/publisher/location"),
            ("ALL_HALLUCINATED", "All fabricated (recall)")]
    L = [r"\begin{tabular}{lr" + "r" * len(V) + "}", r"\toprule",
         r"Subtype & $n$ & " + " & ".join(V) + NL, r"\midrule"]
    for key, label in rows:
        x = orc[key]
        if key == "ALL_HALLUCINATED":
            L.append(r"\midrule")
        L.append(f"{label} & {x['n']} & "
                 + " & ".join(pct(x[f"{v}_flag_rate"]) for v in V) + NL)
    L += [r"\bottomrule", r"\end{tabular}"]
    (out / "tab_oracle.tex").write_text("\n".join(L) + "\n", encoding="utf-8")

    adj = rd(r / "fpr_adjudicated.csv")
    L = [r"\begin{tabular}{lrrrrl}", r"\toprule",
         r"Verifier & FP & Adjudicated & Correct & Adjusted FPR (\%) & 95\% Wilson" + NL, r"\midrule"]
    for x in adj:
        ok = bool(x["fpr_adjusted"])
        cell = pct(x["fpr_adjusted"]) if ok else r"n/a$^{*}$"
        ci = f"[{pct(x['ci_lo'])}, {pct(x['ci_hi'])}]" if ok else "---"
        L.append(f"{x['verifier']} & {x['fp_raw']} & {x['fp_adjudicated']} & "
                 f"{x['fp_true_genuine']} & {cell} & {ci}" + NL)
    L += [r"\bottomrule", r"\end{tabular}"]
    (out / "tab_adjudication.tex").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote tab_mechanisms, tab_identifier, tab_oracle, tab_adjudication to {out}")


if __name__ == "__main__":
    main()
