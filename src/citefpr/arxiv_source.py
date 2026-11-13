"""Build the genuine-reference set from pre-ChatGPT arXiv cs.CL source files.

Source archives are untrusted input: members are read in memory only (never extracted
to disk), and only *.bib and *.tex members are opened.
"""
from __future__ import annotations

import gzip
import io
import random
import tarfile
import time

from .bibparse import cited_keys, entry_to_ref, parse_bib
from .records import Ref
from .registry.clients import parse_arxiv_feed

LIST_URL = "https://export.arxiv.org/api/query"
EPRINT_URL = "https://arxiv.org/e-print/{}"


def list_candidates(session, n_pages: int, page_size: int, start_date: str, end_date: str,
                    category: str = "cs.CL", pause: float = 3.1) -> list[Ref]:
    """Page through arXiv for papers submitted in [start_date, end_date] (YYYYMMDDHHMM)."""
    out = []
    q = f"cat:{category} AND submittedDate:[{start_date} TO {end_date}]"
    for p in range(n_pages):
        r = session.get(LIST_URL, params={"search_query": q, "start": p * page_size,
                                          "max_results": page_size, "sortBy": "submittedDate",
                                          "sortOrder": "ascending"}, timeout=60)
        r.raise_for_status()
        out += parse_arxiv_feed(r.text)
        time.sleep(pause)
    return out


def sample_ids(cands: list[Ref], k: int, seed: int) -> list[str]:
    ids = sorted({c.arxiv_id for c in cands})
    rng = random.Random(seed)
    return sorted(rng.sample(ids, min(k, len(ids))))


def read_source(blob: bytes) -> dict[str, str]:
    """Return {member_name: text} for .bib/.tex members of an e-print blob."""
    files: dict[str, str] = {}
    try:
        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:*") as tf:
            for m in tf.getmembers():
                if not m.isfile() or m.size > 20_000_000:
                    continue
                name = m.name.lower()
                if name.endswith((".bib", ".tex")):
                    fh = tf.extractfile(m)
                    if fh:
                        files[m.name] = fh.read().decode("utf-8", errors="replace")
        return files
    except tarfile.TarError:
        pass
    try:  # single gzipped .tex file
        files["main.tex"] = gzip.decompress(blob).decode("utf-8", errors="replace")
    except OSError:
        pass
    return files


def refs_from_source(arxiv_id: str, files: dict[str, str]) -> tuple[list[Ref], dict]:
    """Cited .bib entries of one paper. Returns (refs, stats)."""
    tex = "\n".join(v for k, v in files.items() if k.lower().endswith(".tex"))
    bib = "\n".join(v for k, v in files.items() if k.lower().endswith(".bib"))
    keys = cited_keys(tex)
    entries = parse_bib(bib) if bib else []
    stats = {"arxiv_id": arxiv_id, "n_bib_entries": len(entries), "n_cited_keys": len(keys),
             "has_bib": bool(bib)}
    refs, seen = [], set()
    for e in entries:
        if keys and e["key"] not in keys:
            continue
        if e["key"] in seen:
            continue
        seen.add(e["key"])
        r = entry_to_ref(e, f"{arxiv_id}:{e['key']}", "arxiv_pre2022")
        if r.title:
            r.extra["citing_paper"] = arxiv_id
            refs.append(r)
    stats["n_refs_kept"] = len(refs)
    return refs, stats
