"""Collect independent evidence for the adjudication sample (not used by any verifier).

For each row of results/adjudication_sample.csv: OpenAlex title search (keyless budget, up to
--oa-budget searches), falling back to the Semantic Scholar match endpoint (keyless, slow retries).
Responses are cached in data/adjudication_cache.sqlite (separate from the frozen experiment cache).
Output: results/adjudication_evidence.csv with the closest record and its similarity to the citation.

Usage: python scripts/adjudication_evidence.py --mailto you@example.org
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from citefpr.cache import ResponseCache  # noqa: E402
from citefpr.normalize import author_overlap, lev_sim  # noqa: E402
from citefpr.records import Ref, read_jsonl  # noqa: E402
from citefpr.registry.clients import OpenAlex, _Http, parse_openalex_work  # noqa: E402


def s2_match(http: _Http, title: str) -> list[Ref]:
    st, body = http.get_json_or_text(
        "https://api.semanticscholar.org/graph/v1/paper/search/match",
        {"query": title[:300], "fields": "title,authors,year,venue,externalIds"})
    if st != 200 or not body:
        return []
    out = []
    for p in body.get("data", []):
        ext = p.get("externalIds") or {}
        out.append(Ref(id=p.get("paperId", ""), title=p.get("title") or "",
                       authors=[a.get("name", "") for a in p.get("authors") or []],
                       year=p.get("year"), venue=p.get("venue") or "", doi=ext.get("DOI") or "",
                       arxiv_id=ext.get("ArXiv") or "", source="s2"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mailto", required=True)
    ap.add_argument("--oa-budget", type=int, default=95)
    ap.add_argument("--sample", default="results/adjudication_sample.csv")
    ap.add_argument("--out", default="results/adjudication_evidence.csv")
    a = ap.parse_args()
    cache = ResponseCache("data/adjudication_cache.sqlite")
    oa = OpenAlex(cache, mailto=a.mailto, max_searches=a.oa_budget)
    s2 = _Http(cache, "s2", 3.5, "citefpr-adjudication/0.1", max_retries=0, timeout=15)
    refs = {d["id"]: Ref.from_dict(d) for d in read_jsonl("data/genuine_refs.jsonl")}
    rows = list(csv.DictReader(open(a.sample, encoding="utf-8")))
    out = []
    for i, r in enumerate(rows, 1):
        ref = refs[r["ref_id"]]
        cands = oa.search(ref.title, n=5) if ref.title else []
        src = "openalex"
        best = max(cands, key=lambda c: lev_sim(ref.title, c.title), default=None)
        if best is None or lev_sim(ref.title, best.title) < 0.9:
            more = s2_match(s2, ref.title) if ref.title else []
            b2 = max(more, key=lambda c: lev_sim(ref.title, c.title), default=None)
            if b2 is not None and (best is None or lev_sim(ref.title, b2.title) > lev_sim(ref.title, best.title)):
                best, src = b2, "s2"
        t = lev_sim(ref.title, best.title) if best else 0.0
        au = author_overlap(ref.authors, best.authors) if best and ref.authors and best.authors else None
        out.append({"ref_id": r["ref_id"], "evidence_source": src if best else "",
                    "ev_title_sim": round(t, 3), "ev_author_overlap": "" if au is None else round(au, 3),
                    "ev_year": best.year if best else "", "cited_year": ref.year,
                    "ev_title": best.title if best else "",
                    "ev_authors": "; ".join(best.authors[:4]) if best else "",
                    "ev_venue": best.venue if best else "", "ev_doi": best.doi if best else ""})
        if i % 10 == 0:
            print(f"[{i}/{len(rows)}] openalex searches left {oa.searches_left}; "
                  f"s2 failed {s2.n_failed}", flush=True)
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader(); w.writerows(out)
    print(f"wrote {a.out}; rows without evidence: {sum(not o['evidence_source'] for o in out)}")


if __name__ == "__main__":
    main()
