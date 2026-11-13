"""One retrieval pass for every citation; responses cached in data/cache.sqlite.

Re-running is safe: cached requests are not sent again, so an interrupted run resumes.
Output: data/candidates.jsonl with {ref_id, candidates: [...], doi_found}.

Usage:
  export OPENALEX_API_KEY=...   (optional but recommended)
  python scripts/run_retrieval.py --refs data/genuine_refs.jsonl data/fabricated_refs.jsonl \
      --mailto you@iiita.ac.in [--limit 200 for the pilot]
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from citefpr.cache import ResponseCache  # noqa: E402
from citefpr.normalize import lev_sim, norm_doi  # noqa: E402
from citefpr.records import Ref, read_jsonl, write_jsonl  # noqa: E402
from citefpr.registry.clients import Arxiv, Crossref, OpenAlex  # noqa: E402
from citefpr.retrieve import prefetch_arxiv, retrieve  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refs", nargs="+", required=True)
    ap.add_argument("--mailto", required=True)
    ap.add_argument("--cache", default="data/cache.sqlite")
    ap.add_argument("--out", default="data/candidates.jsonl")
    ap.add_argument("--limit", type=int, default=None, help="first N refs per file (pilot)")
    ap.add_argument("--no-openalex", action="store_true")
    ap.add_argument("--fast", action="store_true",
                    help="amendments D25/D28: batched arXiv ID lookups; OpenAlex title search "
                         "off (keyless budget ~100/day would cover only the first citations)")
    ap.add_argument("--oa-max-searches", type=int, default=None)
    ap.add_argument("--defer-arxiv-title", action="store_true",
                    help="phase 1 (debug #11): skip the arXiv title fallback and list the citations "
                         "that need it; output is NOT for scoring. Re-run without the flag (phase 2)")
    ap.add_argument("--arxiv-timeout", type=float, default=30.0)
    a = ap.parse_args()
    cache = ResponseCache(a.cache)
    cr = Crossref(cache, a.mailto)
    ax = Arxiv(cache, a.mailto, timeout=a.arxiv_timeout)
    budget = a.oa_max_searches if a.oa_max_searches is not None else (0 if a.fast else 900)
    oa = None if a.no_openalex else OpenAlex(cache, mailto=a.mailto, max_searches=budget)
    refs = []
    for f in a.refs:
        rows = list(read_jsonl(f))
        refs += [Ref.from_dict(r) for r in (rows[:a.limit] if a.limit else rows)]
    out, t0 = [], time.time()
    pre = None
    if a.fast:
        pre = prefetch_arxiv(refs, ax)
        print(f"arXiv prefetch: {len(pre)} records for "
              f"{len({r.arxiv_id for r in refs if r.arxiv_id})} cited IDs "
              f"({ax.http.n_network} requests)", flush=True)
    clients = [cr.http, ax.http] + ([oa.http] if oa else [])
    prefetch_failed = ax.http.n_failed > 0
    incomplete = []
    for i, ref in enumerate(refs, 1):
        before = sum(h.n_failed for h in clients)
        cands = retrieve(ref, cr, ax, oa, arxiv_title=not a.defer_arxiv_title, arxiv_prefetch=pre)
        if sum(h.n_failed for h in clients) > before or (prefetch_failed and ref.arxiv_id):
            incomplete.append(ref.id)
        elif a.defer_arxiv_title and ref.title and \
                not any(lev_sim(ref.title, c.title) >= 0.8 for c in cands):
            incomplete.append(ref.id)   # needs the arXiv title fallback in phase 2
        doi_found = None
        if ref.doi:
            doi_found = any(norm_doi(c.doi) == norm_doi(ref.doi) for c in cands)
        out.append({"ref_id": ref.id, "doi_found": doi_found,
                    "candidates": [c.to_dict() for c in cands]})
        if i % 25 == 0 or i == len(refs):
            net = cr.http.n_network + ax.http.n_network + (oa.http.n_network if oa else 0)
            print(f"[{i}/{len(refs)}] network requests so far {net}; {time.time()-t0:.0f}s elapsed",
                  flush=True)
    write_jsonl(a.out, out)
    print(f"wrote {a.out}; cache now holds {cache.count()}")
    if oa:
        print(f"OpenAlex searches left in budget: {oa.searches_left}")
    inc = Path(a.out).with_suffix(".incomplete.txt")
    inc.write_text("".join(f"{x}\n" for x in incomplete), encoding="utf-8")
    if incomplete:
        print(f"INCOMPLETE: {len(incomplete)} citations had a failed request (listed in {inc}); "
              f"re-run the same command - cached answers are reused, only failures are retried")
        sys.exit(2)
    print("COMPLETE: every request got a definitive answer")


if __name__ == "__main__":
    main()
