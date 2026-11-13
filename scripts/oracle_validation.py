"""G2 offline validation: score CiteTracer's 2,450 synthetic citations against their own seed record.

The seed is the real record each synthetic citation was made from, so it plays the role of
a perfect registry candidate ("oracle retrieval"). This isolates the SCORING stage of each
verifier from retrieval errors. It is NOT the main experiment: genuine natural reference
lists and live retrieval come later (protocol sec. 3).

Usage:
  python scripts/oracle_validation.py --data /path/to/CiteTracer/data --out results/oracle
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from citefpr.metrics import wilson  # noqa: E402
from citefpr.records import Ref  # noqa: E402
from citefpr.scorers import SCORERS  # noqa: E402

REAL = {"R1", "R2", "R3"}
POT = {"P1", "P3"}


def load(data_dir: Path):
    meta = json.loads((data_dir / "synthetic_data/v2/meta.json").read_text(encoding="utf-8"))
    items = json.loads((data_dir / "synthetic_data/v2/_all_test.json").read_text(encoding="utf-8"))
    for it in items:
        cid = it.get("citation_id")
        m = meta.get(cid)
        if not m:
            continue
        cite = Ref.from_dict({**it, "id": cid, "subtype": m["subtype"]})
        seed = Ref.from_dict({**m["seed"], "id": cid + ":seed", "source": "seed"})
        yield cid, m, cite, seed


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="CiteTracer data/ directory")
    ap.add_argument("--out", default="results/oracle")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for cid, m, cite, seed in load(Path(a.data)):
        r = {"citation_id": cid, "subtype": m["subtype"], "label": m["label"],
             "mutation": m.get("mutation_type", "")}
        for name, fn in SCORERS.items():
            v = fn(cite, [seed])
            r[f"{name}_flag"] = int(v.flagged)
            r[f"{name}_score"] = v.score
            r[f"{name}_label"] = v.label
            if name == "V1F":
                r["V1F_failed"] = "|".join(v.details.get("failed_fields", [])) + \
                    ("|H" if v.details.get("H") == 0 else "")
        rows.append(r)
    with open(out / "per_citation.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    # summary by subtype and by class
    by = defaultdict(list)
    for r in rows:
        by[r["subtype"]].append(r)
        cls = "REAL" if r["subtype"] in REAL else "POTENTIAL" if r["subtype"] in POT else "HALLUCINATED"
        by["ALL_" + cls].append(r)
    summ = []
    order = ["R1", "R2", "R3", "ALL_REAL", "P1", "P3", "ALL_POTENTIAL",
             "H1", "H2", "H3", "H4", "H5", "H6", "ALL_HALLUCINATED"]
    for g in order:
        rs = by.get(g, [])
        if not rs:
            continue
        row = {"group": g, "n": len(rs)}
        for name in SCORERS:
            k = sum(x[f"{name}_flag"] for x in rs)
            lo, hi = wilson(k, len(rs))
            row[f"{name}_flag_rate"] = round(k / len(rs), 4)
            row[f"{name}_ci"] = f"[{lo:.3f}, {hi:.3f}]"
        summ.append(row)
    with open(out / "summary_by_subtype.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summ[0].keys()))
        w.writeheader(); w.writerows(summ)
    from citefpr.plots import heatmap
    hrows = [s for s in summ if s["group"].startswith("H")]
    heatmap([s["group"] for s in hrows], list(SCORERS),
            [[s[f"{n}_flag_rate"] for n in SCORERS] for s in hrows],
            "Share of synthetic fabrications flagged, perfect retrieval", out / "figures",
            "oracle_detection_by_subtype")
    # print a compact table
    names = list(SCORERS)
    print("group".ljust(18), "n".rjust(5), *[n.rjust(7) for n in names])
    for s in summ:
        print(s["group"].ljust(18), str(s["n"]).rjust(5),
              *[f"{100*s[f'{n}_flag_rate']:6.1f}%" for n in names])
    print(f"\nwrote {out/'per_citation.csv'} ({len(rows)} rows) and {out/'summary_by_subtype.csv'}")


if __name__ == "__main__":
    main()
