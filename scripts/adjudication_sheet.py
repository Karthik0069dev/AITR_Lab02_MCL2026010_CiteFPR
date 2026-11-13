"""Add citation and best-candidate fields to results/adjudication_sample.csv for hand labelling.

Only display columns are added; evaluate.py reads just `ref_id` and `adjudicated`.
Labels: genuine (the reference is correct and the verifier was wrong) |
        genuine_erroneous (the paper exists but the .bib entry has a real error) |
        unresolvable (cannot decide from public sources).

Usage: python scripts/adjudication_sheet.py
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from citefpr.normalize import lev_sim  # noqa: E402
from citefpr.records import Ref, read_jsonl  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", default="results/adjudication_sample.csv")
    ap.add_argument("--refs", default="data/genuine_refs.jsonl")
    ap.add_argument("--candidates", default="data/candidates.jsonl")
    ap.add_argument("--scores", default="results/scores.csv")
    a = ap.parse_args()
    refs = {d["id"]: Ref.from_dict(d) for d in read_jsonl(a.refs)}
    cands = {r["ref_id"]: [Ref.from_dict(x) for x in r["candidates"]] for r in read_jsonl(a.candidates)}
    scores = {r["ref_id"]: r for r in csv.DictReader(open(a.scores, encoding="utf-8"))}
    rows = list(csv.DictReader(open(a.sample, encoding="utf-8")))
    out = []
    for r in rows:
        ref = refs[r["ref_id"]]
        cl = cands.get(r["ref_id"], [])
        best = max(cl, key=lambda c: lev_sim(ref.title, c.title), default=None)
        s = scores[r["ref_id"]]
        out.append({
            "ref_id": r["ref_id"], "first_flagged_by": r["first_flagged_by"],
            "adjudicated": r.get("adjudicated", ""), "note": r.get("note", ""),
            "flagged_by": " ".join(v for v in ["V1E", "V1F", "V2", "V3", "V3a"] if s[f"{v}_flag"] == "1"),
            "V1F_failed": s["V1F_failed"], "entry_type": ref.entry_type,
            "cited_title": ref.title, "cited_authors": "; ".join(ref.authors[:4]),
            "cited_year": ref.year, "cited_venue": ref.venue, "cited_doi": ref.doi,
            "cited_arxiv": ref.arxiv_id, "n_candidates": len(cl),
            "best_cand_title": best.title if best else "", "best_cand_authors":
                "; ".join(best.authors[:4]) if best else "",
            "best_cand_year": best.year if best else "", "best_cand_venue": best.venue if best else "",
            "best_cand_source": best.source if best else ""})
    with open(a.sample, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader(); w.writerows(out)
    print(f"{len(out)} rows written to {a.sample}; fill the 'adjudicated' column by hand")


if __name__ == "__main__":
    main()
