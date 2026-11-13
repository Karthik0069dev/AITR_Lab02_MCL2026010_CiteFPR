"""Adjusted FPR after adjudication: false positives among references confirmed correct.

Denominator: genuine refs minus those labelled genuine_erroneous or unresolvable.
Numerator: flagged refs labelled genuine. Only exact for verifiers whose false positives were all
adjudicated (fp_adjudicated == fp); otherwise reported as not computed.
Usage: python scripts/adjusted_fpr.py
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from citefpr.metrics import wilson  # noqa: E402

m = list(csv.DictReader(open("results/metrics.csv", encoding="utf-8")))
adj = {r["ref_id"]: r["adjudicated"] for r in csv.DictReader(open("results/adjudication_sample.csv", encoding="utf-8"))}
excluded = sum(v in ("genuine_erroneous", "unresolvable") for v in adj.values())
out = []
for r in m:
    n = int(r["n_genuine"]) - excluded
    complete = r["fp_adjudicated"] == r["fp"]
    k = int(r["fp_true_genuine"])
    lo, hi = wilson(k, n)
    out.append({"verifier": r["verifier"], "fp_raw": r["fp"], "fp_adjudicated": r["fp_adjudicated"],
                "fp_true_genuine": k, "n_correct_refs": n,
                "fpr_adjusted": round(k / n, 4) if complete else "",
                "ci_lo": round(lo, 4) if complete else "", "ci_hi": round(hi, 4) if complete else "",
                "share_of_flags_on_correct_refs": round(k / int(r["fp_adjudicated"]), 4)})
with open("results/fpr_adjudicated.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
for o in out:
    print(o)
