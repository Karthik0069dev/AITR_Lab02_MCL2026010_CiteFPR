"""Error analysis (deep analysis, Prompt 13/14): classify each genuine false positive by the
retrieval/metadata situation that produced it. Automatic and INFERRED; hand adjudication is separate.

  A  no candidate with title similarity >= 0.8 -> paper not retrieved (coverage / ranking miss)
  B  best-title candidate >= 0.9 but author overlap < 0.5 -> same title, authors disagree
     (title twin by other authors, or malformed registry author metadata)
  C  best-title candidate >= 0.9, authors agree -> flagged on year/venue/locator/score details
  D  best-title candidate in [0.8, 0.9) -> near-miss title (subtitle, punctuation, version)

Usage: python scripts/fp_mechanisms.py
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from citefpr.normalize import author_overlap, lev_sim  # noqa: E402
from citefpr.records import Ref, read_jsonl  # noqa: E402

V = ["V1E", "V1F", "V2", "V3", "V3a"]


def mechanism(ref: Ref, cands: list[Ref]) -> str:
    if not cands:
        return "A"
    best = max(cands, key=lambda c: lev_sim(ref.title, c.title))
    t = lev_sim(ref.title, best.title)
    if t < 0.8:
        return "A"
    if t < 0.9:
        return "D"
    a = author_overlap(ref.authors, best.authors) if (ref.authors and best.authors) else 1.0
    return "B" if a < 0.5 else "C"


def main():
    refs = {d["id"]: Ref.from_dict(d) for d in read_jsonl("data/genuine_refs.jsonl")}
    cands = {r["ref_id"]: [Ref.from_dict(c) for c in r["candidates"]]
             for r in read_jsonl("data/frozen/candidates_20261113.jsonl")}
    rows = [r for r in csv.DictReader(open("results/scores.csv", encoding="utf-8"))
            if r["label"] == "genuine"]
    out, per = [], {}
    for v in V:
        fps = [r for r in rows if r[f"{v}_flag"] == "1"]
        cnt = Counter(mechanism(refs[r["ref_id"]], cands[r["ref_id"]]) for r in fps)
        per[v] = cnt
        out.append({"verifier": v, "n_fp": len(fps), **{k: cnt.get(k, 0) for k in "ABCD"}})
    with open("results/fp_mechanisms.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["verifier", "n_fp", "A", "B", "C", "D"])
        w.writeheader(); w.writerows(out)
    # genuine refs with a cited arXiv ID / DOI vs none (V1E)
    strat = []
    for name, f in [("has_doi", lambda r: r["has_doi"] == "1"),
                    ("has_arxiv_id", lambda r: r["has_arxiv"] == "1"),
                    ("neither", lambda r: r["has_doi"] == "0" and r["has_arxiv"] == "0")]:
        s = [r for r in rows if f(r)]
        strat.append({"stratum": name, "n": len(s),
                      **{f"{v}_fpr": round(sum(r[f"{v}_flag"] == "1" for r in s) / max(1, len(s)), 4)
                         for v in V}})
    with open("results/fp_by_identifier.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(strat[0].keys()))
        w.writeheader(); w.writerows(strat)
    for o in out:
        print(o)
    for s in strat:
        print(s)


if __name__ == "__main__":
    main()
