"""Check the manuscript's headline numbers against results/*.csv (peer-review item: figure/table/claim
consistency). Fails loudly if a claim no longer matches the data.

Usage: python scripts/check_paper_numbers.py
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from citefpr.metrics import ppv  # noqa: E402

TEX = Path("paper/main.tex").read_text(encoding="utf-8")


def rd(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def main():
    m = {x["verifier"]: x for x in rd("results/metrics.csv")}
    pp = {(x["verifier"], x["pi"]): x for x in rd("results/ppv.csv")}
    mech = {x["verifier"]: x for x in rd("results/fp_mechanisms.csv")}
    adj = {x["verifier"]: x for x in rd("results/fpr_adjudicated.csv")}
    ident = {x["stratum"]: x for x in rd("results/fp_by_identifier.csv")}
    sw = rd("results/tau_sweep.csv")
    labels = [r["adjudicated"] for r in rd("results/adjudication_sample.csv")]
    checks, bad = [], 0

    def claim(name, ok, detail):
        nonlocal bad
        checks.append((name, ok, detail))
        if not ok:
            bad += 1

    # FPR range quoted in abstract/results for V1E, V2, V3
    fprs = {v: int(m[v]["fp"]) / int(m[v]["n_genuine"]) for v in ("V1E", "V2", "V3")}
    lo, hi = min(fprs.values()), max(fprs.values())
    claim("FPR range 16.0-17.3%", f"{100*lo:.1f}--{100*hi:.1f}" == "16.0--17.3",
          f"{100*lo:.1f}--{100*hi:.1f}")
    claim("V1F FPR 47.1%", f"{100*int(m['V1F']['fp'])/567:.1f}" == "47.1",
          f"{100*int(m['V1F']['fp'])/567:.1f}")
    # recall range
    rec = [float(m[v]["recall_ALL_FABRICATED"]) for v in m]
    claim("recall 95.7-99.9%", f"{100*min(rec):.1f}--{100*max(rec):.1f}" == "95.7--99.9",
          f"{100*min(rec):.1f}--{100*max(rec):.1f}")
    # PPV at 1%
    p1 = [float(pp[(v, "0.01")]["ppv_eq13"]) for v in ("V1E", "V2", "V3")]
    claim("max PPV at pi=1% <= 5.7%", f"{100*max(p1):.1f}" == "5.7", f"{100*max(p1):.1f}")
    # mechanisms: share of type A for V1E/V2/V3
    sh = [int(mech[v]["A"]) / int(mech[v]["n_fp"]) for v in ("V1E", "V2", "V3")]
    claim("type-A share 86-89%", f"{100*min(sh):.0f}--{100*max(sh):.0f}" == "86--89",
          f"{100*min(sh):.0f}--{100*max(sh):.0f}")
    claim("V1F type C = 170", mech["V1F"]["C"] == "170", mech["V1F"]["C"])
    claim("V1E type A = 84 of 96", (mech["V1E"]["A"], mech["V1E"]["n_fp"]) == ("84", "96"),
          f"{mech['V1E']['A']}/{mech['V1E']['n_fp']}")
    # identifier strata
    claim("DOI stratum n=58, 0% for V1E/V2/V3",
          ident["has_doi"]["n"] == "58" and all(float(ident["has_doi"][f"{v}_fpr"]) == 0
                                                for v in ("V1E", "V2", "V3")), ident["has_doi"]["n"])
    claim("no-identifier stratum n=423, 21.3-22.5%", ident["neither"]["n"] == "423" and
          f"{100*min(float(ident['neither'][f'{v}_fpr']) for v in ('V1E','V2','V3')):.1f}" == "21.3",
          ident["neither"]["n"])
    # adjudication counts
    claim("adjudication 109/3/11", (labels.count("genuine"), labels.count("genuine_erroneous"),
                                    labels.count("unresolvable")) == (109, 3, 11),
          f"{labels.count('genuine')}/{labels.count('genuine_erroneous')}/{labels.count('unresolvable')}")
    claim("553 correct refs", adj["V1E"]["n_correct_refs"] == "553", adj["V1E"]["n_correct_refs"])
    for v, want in (("V1E", "14.8"), ("V2", "13.9"), ("V3", "15.2")):
        claim(f"adjusted FPR {v} {want}%", f"{100*float(adj[v]['fpr_adjusted']):.1f}" == want,
              f"{100*float(adj[v]['fpr_adjusted']):.1f}")
    # adjusted PPV at 1%
    ap = [ppv(float(m[v]["recall_ALL_FABRICATED"]), float(adj[v]["fpr_adjusted"]), 0.01)
          for v in ("V1E", "V2", "V3")]
    claim("adjusted PPV 0.062-0.065", f"{min(ap):.3f}--{max(ap):.3f}" == "0.062--0.065",
          f"{min(ap):.3f}--{max(ap):.3f}")
    # tau sweep at threshold 60
    t60 = [float(x["fpr"]) for x in sw if x["threshold"] == "60"]
    r60 = [float(x["recall"]) for x in sw if x["threshold"] == "60"]
    claim("tau=60 FPR 13.2-14.6%", f"{100*min(t60):.1f}--{100*max(t60):.1f}" == "13.2--14.6",
          f"{100*min(t60):.1f}--{100*max(t60):.1f}")
    claim("tau=60 recall 87-90%", f"{100*min(r60):.0f}--{100*max(r60):.0f}" == "87--90",
          f"{100*min(r60):.0f}--{100*max(r60):.0f}")
    # retrieval-failure check quoted in Threats to validity
    rows = rd("results/scores.csv")
    gen = [r for r in rows if r["label"] == "genuine"]
    claim("no citation has an empty candidate list",
          not any(r["n_cands"] == "0" for r in rows), "")
    med = sorted(int(r["n_cands"]) for r in gen)[len(gen) // 2]
    claim("median candidates per genuine ref = 5", med == 5, str(med))

    # baseline validation (oracle) claims
    orc = {x["group"]: x for x in rd("results/oracle/summary_by_subtype.csv")}
    claim("oracle: 0 flags on 1023 real", orc["ALL_REAL"]["n"] == "1023" and
          all(float(orc["ALL_REAL"][f"{v}_flag_rate"]) == 0 for v in m), orc["ALL_REAL"]["n"])
    claim("oracle: 0 flags on 271 potential", orc["ALL_POTENTIAL"]["n"] == "271" and
          all(float(orc["ALL_POTENTIAL"][f"{v}_flag_rate"]) == 0 for v in m),
          orc["ALL_POTENTIAL"]["n"])
    claim("oracle: Wilson upper bound 0.4%",
          orc["ALL_REAL"]["V1E_ci"].endswith('0.004]'), orc["ALL_REAL"]["V1E_ci"])
    claim("oracle: V2 catches none of H4", float(orc["H4"]["V2_flag_rate"]) == 0,
          orc["H4"]["V2_flag_rate"])
    claim("oracle: V3 catches none of H3", float(orc["H3"]["V3_flag_rate"]) == 0,
          orc["H3"]["V3_flag_rate"])
    n_h6, r_h6 = int(orc["H6"]["n"]), float(orc["H6"]["V1F_flag_rate"])
    claim("oracle: V1F misses 99 of 166 H6", (n_h6, n_h6 - round(n_h6 * r_h6)) == (166, 99),
          f"{n_h6 - round(n_h6 * r_h6)} of {n_h6}")
    claim("2450 synthetic citations", int(orc["ALL_REAL"]["n"]) + int(orc["ALL_POTENTIAL"]["n"])
          + int(orc["ALL_HALLUCINATED"]["n"]) == 2450, "")

    # every claimed figure/table input exists
    for ref in re.findall(r"\\input\{(tables/[^}]+)\}", TEX):
        claim(f"exists {ref}", (Path("paper") / ref).exists(), "")
    for ref in re.findall(r"\\includegraphics\[[^]]*\]\{([^}]+)\}", TEX):
        claim(f"exists figures/{ref}", (Path("paper/figures") / ref).exists(), "")
    # no leftover placeholders
    claim("no TO VERIFY left", "TOVERIFY{" not in TEX, "")
    claim("no %% markers left", "%%" not in TEX, "")

    for name, ok, detail in checks:
        print(("  OK  " if ok else "FAIL  ") + name + (f"  -> {detail}" if detail and not ok else ""))
    print(f"\n{len(checks) - bad}/{len(checks)} checks passed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
