"""Load fabricated citations (positives) into data/fabricated_refs.jsonl.

Sources: CiteTracer's ICLR 2026 desk-reject set (structured version). The NeurIPS 2025 set
is optional: pass --neurips-csv with columns title,authors,venue,year,doi,raw if you obtain it.

Usage: python scripts/load_positives.py --citetracer-data /path/to/CiteTracer/data
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from citefpr.normalize import norm_arxiv, norm_doi  # noqa: E402
from citefpr.records import Ref, parse_year, write_jsonl  # noqa: E402


def iclr(data_dir: Path):
    papers = json.loads((data_dir / "iclr2026_hallucinated/hallucinated_refs_structured.json").read_text(encoding="utf-8"))
    for p in papers:
        for c in p.get("hallucinated_citations", []):
            authors = c.get("authors") or []
            if isinstance(authors, str):
                authors = [x.strip() for x in authors.replace(";", ",").split(",") if x.strip()]
            yield Ref(id=f"iclr:{p['paper_id']}:{c.get('citation_id','')}", title=c.get("title") or "",
                      authors=authors, year=parse_year(c.get("year")),
                      venue=c.get("venue") or "", doi=norm_doi(c.get("doi") or ""),
                      arxiv_id=norm_arxiv(c.get("arxiv_id") or ""), pages=c.get("pages") or "",
                      volume=str(c.get("volume") or ""), raw=c.get("raw_text") or "",
                      label="fabricated", source_set="iclr2026",
                      extra={"paper_id": p["paper_id"]})


def neurips(path: Path):
    with open(path, newline="", encoding="utf-8") as fh:
        for i, row in enumerate(csv.DictReader(fh)):
            d = {**row, "id": f"neurips:{i}", "label": "fabricated", "source_set": "neurips2025"}
            d["authors"] = [x.strip() for x in (row.get("authors") or "").split(";") if x.strip()]
            yield Ref.from_dict(d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--citetracer-data", required=True)
    ap.add_argument("--neurips-csv", default=None)
    ap.add_argument("--out", default="data/fabricated_refs.jsonl")
    a = ap.parse_args()
    refs = list(iclr(Path(a.citetracer_data)))
    n_iclr = len(refs)
    if a.neurips_csv:
        refs += list(neurips(Path(a.neurips_csv)))
    n = write_jsonl(a.out, (r.to_dict() for r in refs))
    no_title = sum(1 for r in refs if not r.title)
    print(f"{n} fabricated refs written ({n_iclr} ICLR 2026, {n - n_iclr} NeurIPS 2025); "
          f"{no_title} without a parsed title")


if __name__ == "__main__":
    main()
