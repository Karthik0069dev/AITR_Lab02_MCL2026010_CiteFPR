"""Score every citation with every verifier, reading only the frozen candidate file.

Output: results/scores.csv (one row per citation, flags + scores + labels per verifier).

Usage: python scripts/score.py --refs data/genuine_refs.jsonl data/fabricated_refs.jsonl \
          --candidates data/candidates.jsonl
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from citefpr.records import Ref, read_jsonl  # noqa: E402
from citefpr.scorers import SCORERS  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refs", nargs="+", required=True)
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--out", default="results/scores.csv")
    a = ap.parse_args()
    cand = {r["ref_id"]: r for r in read_jsonl(a.candidates)}
    rows, missing = [], 0
    for f in a.refs:
        for d in read_jsonl(f):
            ref = Ref.from_dict(d)
            c = cand.get(ref.id)
            if c is None:
                missing += 1
                continue
            cands = [Ref.from_dict(x) for x in c["candidates"]]
            row = {"ref_id": ref.id, "label": ref.label, "source_set": ref.source_set,
                   "entry_type": ref.entry_type, "subtype": ref.subtype,
                   "has_doi": int(bool(ref.doi)), "has_arxiv": int(bool(ref.arxiv_id)),
                   "n_cands": len(cands)}
            for name, fn in SCORERS.items():
                v = fn(ref, cands, doi_found=c.get("doi_found"))
                row[f"{name}_flag"] = int(v.flagged)
                row[f"{name}_score"] = v.score
                row[f"{name}_label"] = v.label
                if name == "V1F":
                    det = v.details
                    row["V1F_failed"] = "|".join(det.get("failed_fields", [])) + \
                        ("|H" if det.get("H") == 0 else "") + ("|E" if det.get("E") == 0 else "")
                    row["best_source"] = cands[v.best].source if v.best is not None else ""
            rows.append(row)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"scored {len(rows)} citations -> {a.out}; {missing} had no candidate record (run retrieval)")


if __name__ == "__main__":
    main()
