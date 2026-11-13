"""Compute all metrics from results/scores.csv (Prompt 13 audits included).

Checks first: duplicate IDs, labels in {genuine, fabricated}, flag columns binary.
Outputs (results/): metrics.csv, ppv.csv, tau_sweep.csv, fp_by_entry_type.csv,
fp_by_failed_field.csv, figures/*.png|pdf, adjudication_sample.csv (to label by hand).
With --adjudication, genuine refs labelled 'genuine_erroneous' or 'unresolvable' are
reported separately and an adjusted FPR is added.

Usage: python scripts/evaluate.py --scores results/scores.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from citefpr.metrics import (bootstrap_ppv, cluster_bootstrap_rate, mcnemar_exact, ppv,  # noqa: E402
                             wilson)
from citefpr.plots import ppv_curves, rate_with_ci, tau_sweep  # noqa: E402

VERIFIERS = ["V1E", "V1F", "V2", "V3", "V3a"]
SWEEPABLE = ["V1E", "V2", "V3"]


def paper_id(ref_id: str) -> str:
    """Citing paper of a reference. Genuine IDs are '<arXiv id>:<bib key>' and bib keys may
    contain colons (e.g. 'DBLP:conf/acl/...'), so split on the FIRST colon (debug #12).
    Fabricated IDs are 'iclr:<forum id>:ref:<n>' -> 'iclr:<forum id>'."""
    parts = ref_id.split(":")
    return ":".join(parts[:2]) if parts[0] == "iclr" else parts[0]


def audit(rows):
    ids = Counter(r["ref_id"] for r in rows)
    dups = [k for k, n in ids.items() if n > 1]
    bad_label = [r["ref_id"] for r in rows if r["label"] not in ("genuine", "fabricated")]
    bad_flag = [r["ref_id"] for r in rows for v in VERIFIERS if r[f"{v}_flag"] not in ("0", "1")]
    leak = {r["ref_id"].split(":")[0] for r in rows if r["label"] == "genuine"} & \
           {r["ref_id"].split(":")[0] for r in rows if r["label"] == "fabricated"}
    problems = {"duplicate_ids": dups[:10], "bad_labels": bad_label[:10], "bad_flags": bad_flag[:10],
                "id_prefix_overlap_between_sets": sorted(leak)[:10]}
    if dups or bad_label or bad_flag:
        raise SystemExit(f"AUDIT FAILED: {json.dumps(problems)}")
    return problems


def write_csv(path, rows, fieldnames=None):
    """Write rows; an empty result still gets a header so its absence is visible."""
    if not rows and not fieldnames:
        return
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames or list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", default="results/scores.csv")
    ap.add_argument("--config", default="configs/protocol.json")
    ap.add_argument("--adjudication", default=None)
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text(encoding="utf-8"))
    rows = list(csv.DictReader(open(a.scores, newline="", encoding="utf-8")))
    out = Path(a.out); fig = out / "figures"
    audit_report = audit(rows)
    adj = {}
    if a.adjudication:
        adj = {r["ref_id"]: r["adjudicated"] for r in csv.DictReader(open(a.adjudication, encoding="utf-8"))
               if r.get("adjudicated")}
    gen = [r for r in rows if r["label"] == "genuine"]
    fab_sets = defaultdict(list)
    for r in rows:
        if r["label"] == "fabricated":
            fab_sets[r["source_set"]].append(r)
            fab_sets["ALL_FABRICATED"].append(r)
    metrics, ppv_rows, ci_rows = [], [], []
    pis = cfg["pi_grid"]
    curves = {}
    for v in VERIFIERS:
        k = sum(int(r[f"{v}_flag"]) for r in gen)
        lo, hi = wilson(k, len(gen))
        m = {"verifier": v, "n_genuine": len(gen), "fp": k, "fpr": round(k / len(gen), 4) if gen else "",
             "fpr_ci_lo": round(lo, 4), "fpr_ci_hi": round(hi, 4)}
        # paper-level (cluster) bootstrap: references of one citing paper move together
        clus = [paper_id(r["ref_id"]) for r in gen]
        clo, chi = cluster_bootstrap_rate([r[f"{v}_flag"] == "1" for r in gen], clus,
                                          cfg["bootstrap"]["n_mix"], cfg["bootstrap"]["seed"])
        m["fpr_cluster_ci_lo"], m["fpr_cluster_ci_hi"] = round(clo, 4), round(chi, 4)
        if adj:
            flagged = [r for r in gen if r[f"{v}_flag"] == "1"]
            labelled = [r for r in flagged if r["ref_id"] in adj]
            m["fp_adjudicated"] = len(labelled)
            m["fp_true_genuine"] = sum(adj[r["ref_id"]] == "genuine" for r in labelled)
            m["fp_genuine_erroneous"] = sum(adj[r["ref_id"]] == "genuine_erroneous" for r in labelled)
            m["fp_unresolvable"] = sum(adj[r["ref_id"]] == "unresolvable" for r in labelled)
        for s, rs in fab_sets.items():
            kk = sum(int(r[f"{v}_flag"]) for r in rs)
            l2, h2 = wilson(kk, len(rs))
            m[f"recall_{s}"] = round(kk / len(rs), 4)
            m[f"recall_{s}_ci"] = f"[{l2:.3f}, {h2:.3f}]"
        metrics.append(m)
        ci_rows.append({"v": v, "rate": k / len(gen) if gen else 0, "lo": lo, "hi": hi})
        rec = m.get("recall_ALL_FABRICATED", float("nan"))
        curves[v] = []
        gflags = [int(r[f"{v}_flag"]) for r in gen]
        fflags = [int(r[f"{v}_flag"]) for r in fab_sets["ALL_FABRICATED"]]
        b = cfg["bootstrap"]
        for p in pis:
            val = ppv(rec, m["fpr"], p) if gen and fab_sets["ALL_FABRICATED"] else float("nan")
            bs = bootstrap_ppv(gflags, fflags, p, b["n_mix"], b["mix_size"], b["seed"])
            ppv_rows.append({"verifier": v, "pi": p, "ppv_eq13": round(val, 4),
                             "ppv_bootstrap": round(bs["mean"], 4),
                             "ppv_boot_lo": round(bs["lo"], 4), "ppv_boot_hi": round(bs["hi"], 4)})
            curves[v].append(val)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "metrics.csv", metrics)
    # paired McNemar tests on genuine references (FPR differences), decision rule in Prompt 05
    pairs = []
    for i, va in enumerate(VERIFIERS):
        for vb in VERIFIERS[i + 1:]:
            t = mcnemar_exact([r[f"{va}_flag"] == "1" for r in gen], [r[f"{vb}_flag"] == "1" for r in gen])
            gap = (sum(r[f"{va}_flag"] == "1" for r in gen) - sum(r[f"{vb}_flag"] == "1" for r in gen)) \
                / max(1, len(gen))
            pairs.append({"a": va, "b": vb, "a_only": t["a_only"], "b_only": t["b_only"],
                          "fpr_gap_a_minus_b": round(gap, 4), "p_exact": round(t["p"], 6),
                          "meets_rule": int(t["p"] < 0.05 and abs(gap) >= 0.02)})
    write_csv(out / "mcnemar_fpr.csv", pairs)
    write_csv(out / "ppv.csv", ppv_rows)
    # tau sweep (sensitivity): flag = score < t
    sw, sweeps = [], {}
    t0, t1, st = cfg["tau_sweep"]["min"], cfg["tau_sweep"]["max"], cfg["tau_sweep"]["step"]
    fab = fab_sets["ALL_FABRICATED"]
    for v in SWEEPABLE:
        sweeps[v] = {"t": [], "fpr": [], "recall": []}
        for t in range(t0, t1 + 1, st):
            f = sum(float(r[f"{v}_score"]) < t for r in gen) / max(1, len(gen))
            rc = sum(float(r[f"{v}_score"]) < t for r in fab) / max(1, len(fab))
            sw.append({"verifier": v, "threshold": t, "fpr": round(f, 4), "recall": round(rc, 4)})
            for k_, x in (("t", t), ("fpr", f), ("recall", rc)):
                sweeps[v][k_].append(x)
    write_csv(out / "tau_sweep.csv", sw)
    # false positives by entry type and by failed V1 field
    by_type = []
    types = Counter(r["entry_type"] or "unknown" for r in gen)
    for t, n in types.most_common():
        row = {"entry_type": t, "n": n}
        for v in VERIFIERS:
            k = sum(1 for r in gen if (r["entry_type"] or "unknown") == t and r[f"{v}_flag"] == "1")
            row[f"{v}_fpr"] = round(k / n, 4)
        by_type.append(row)
    write_csv(out / "fp_by_entry_type.csv", by_type)
    fields = Counter()
    for r in gen:
        if r["V1F_flag"] == "1":
            for f in [x for x in r["V1F_failed"].split("|") if x]:
                fields[f] += 1
    write_csv(out / "fp_by_failed_field.csv",
              [{"failed_check": f, "n_genuine_refs": n} for f, n in fields.most_common()],
              ["failed_check", "n_genuine_refs"])
    # adjudication sample (stratified by verifier, fixed seed)
    ac = cfg["adjudication"]
    rng = random.Random(ac["seed"])
    picked, seen = [], set()
    for v in VERIFIERS:
        pool = sorted(r["ref_id"] for r in gen if r[f"{v}_flag"] == "1" and r["ref_id"] not in seen)
        k = ac.get("sample_per_verifier_amended", ac["sample_per_verifier"])  # D27
        for rid in rng.sample(pool, min(k, len(pool))):
            if len(picked) < ac["max_total"]:
                seen.add(rid); picked.append({"ref_id": rid, "first_flagged_by": v, "adjudicated": "",
                                              "note": ""})
    # debug #13: never overwrite a sheet that already holds labels
    sheet = out / "adjudication_sample.csv"
    has_labels = sheet.exists() and any(
        r.get("adjudicated") for r in csv.DictReader(open(sheet, encoding="utf-8")))
    if a.adjudication or has_labels:
        print(f"kept existing {sheet} (labels present or --adjudication given)")
    else:
        write_csv(sheet, picked, ["ref_id", "first_flagged_by", "adjudicated", "note"])
    # figures
    if gen:
        rate_with_ci(ci_rows, "False-positive rate on genuine references (95% Wilson CI)",
                     "FPR", fig, "fpr_by_verifier")
    if gen and fab:
        ppv_curves(curves, pis, fig)
        tau_sweep(sweeps, fig)
    (out / "evaluation_audit.json").write_text(json.dumps(
        {"n_rows": len(rows), "n_genuine": len(gen),
         "n_fabricated": {k: len(v) for k, v in fab_sets.items()}, **audit_report}, indent=2), encoding="utf-8")
    print(json.dumps({"n_genuine": len(gen), "n_fabricated": len(fab)}, indent=None))
    for m in metrics:
        print(f"{m['verifier']:4s} FPR {m['fpr']} [{m['fpr_ci_lo']}, {m['fpr_ci_hi']}]  "
              f"recall {m.get('recall_ALL_FABRICATED', '')}")
    print(f"wrote metrics, ppv, tau sweep, FP breakdowns, adjudication sample and figures to {out}/")


if __name__ == "__main__":
    main()
