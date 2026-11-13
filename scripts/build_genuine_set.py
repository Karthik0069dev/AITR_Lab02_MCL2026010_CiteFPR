"""Build the genuine-reference set (negatives) from pre-ChatGPT arXiv cs.CL source files.

Network: arXiv API + e-print downloads, 1 request / 3.1 s. ~100 papers -> ~10-15 min.
Outputs: data/genuine_refs.jsonl, data/genuine_papers.csv (per-paper stats).

Usage: python scripts/build_genuine_set.py --contact you@iiita.ac.in [--n-papers 10 for the pilot]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import requests  # noqa: E402

from citefpr.arxiv_source import EPRINT_URL, list_candidates, read_source, refs_from_source, sample_ids  # noqa: E402
from citefpr.records import write_jsonl  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--contact", required=True, help="email for the User-Agent")
    ap.add_argument("--config", default="configs/protocol.json")
    ap.add_argument("--n-papers", type=int, default=None, help="override (pilot: 10)")
    ap.add_argument("--out", default="data/genuine_refs.jsonl")
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text(encoding="utf-8"))["genuine_set"]
    n = a.n_papers or cfg["n_papers"]
    s = requests.Session()
    s.headers["User-Agent"] = f"citefpr/0.1 (mailto:{a.contact})"
    cands = list_candidates(s, cfg["n_candidate_pages"], cfg["page_size"],
                            cfg["start_date"], cfg["end_date"])
    ids = sample_ids(cands, n, cfg["sampling_seed"])
    Path("data").mkdir(exist_ok=True)
    Path("data/genuine_paper_ids.txt").write_text("\n".join(ids) + "\n", encoding="utf-8")
    print(f"{len(cands)} candidate papers listed; sampled {len(ids)} (seed {cfg['sampling_seed']})")
    all_refs, stats = [], []
    for i, aid in enumerate(ids, 1):
        time.sleep(3.1)
        try:
            r = s.get(EPRINT_URL.format(aid), timeout=120)
            r.raise_for_status()
            files = read_source(r.content)
            refs, st = refs_from_source(aid, files)
        except Exception as exc:
            refs, st = [], {"arxiv_id": aid, "error": f"{exc.__class__.__name__}: {exc}"[:200]}
        all_refs += refs
        stats.append(st)
        print(f"[{i}/{len(ids)}] {aid}: {st.get('n_refs_kept', 0)} refs "
              f"(bib entries {st.get('n_bib_entries', 0)}, cited keys {st.get('n_cited_keys', 0)})"
              + (f" ERROR {st['error']}" if 'error' in st else ""))
    n_out = write_jsonl(a.out, (r.to_dict() for r in all_refs))
    keys = sorted({k for st in stats for k in st})
    with open("data/genuine_papers.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader(); w.writerows(stats)
    with_bib = sum(1 for st in stats if st.get("has_bib"))
    print(f"\n{n_out} genuine references written to {a.out}; {with_bib}/{len(ids)} papers had a .bib")


if __name__ == "__main__":
    main()
