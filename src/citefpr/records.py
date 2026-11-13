"""Common record type for citations and registry candidates."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Iterator


def parse_year(y) -> int | None:
    """First 4-digit year in y, or None."""
    if y in (None, ""):
        return None
    import re
    m = re.search(r"(1[89]|20)\d{2}", str(y))
    return int(m.group(0)) if m else None


@dataclass
class Ref:
    id: str
    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    venue: str = ""
    doi: str = ""
    arxiv_id: str = ""
    pages: str = ""
    volume: str = ""
    raw: str = ""
    entry_type: str = ""          # bib entry type for genuine refs (article, book, misc ...)
    label: str = ""               # 'genuine' | 'fabricated' | '' for candidates
    source_set: str = ""          # e.g. 'arxiv_pre2022', 'iclr2026', 'citetracer_synth'
    subtype: str = ""             # e.g. CiteTracer code R1..H6
    source: str = ""              # registry name for candidates
    extra: dict = field(default_factory=dict)

    @staticmethod
    def from_dict(d: dict) -> "Ref":
        year = parse_year(d.get("year"))
        authors = d.get("authors") or []
        if isinstance(authors, str):
            authors = [a.strip() for a in authors.split(" and ") if a.strip()]
        known = {k for k in Ref.__dataclass_fields__}
        base = {k: d.get(k) for k in known if k in d and k not in ("year", "authors", "extra")}
        extra = {k: v for k, v in d.items() if k not in known}
        extra.update(d.get("extra") or {})
        return Ref(year=year, authors=list(authors), extra=extra,
                   **{k: ("" if v is None else v) for k, v in base.items()})

    def to_dict(self) -> dict:
        return asdict(self)


def read_jsonl(path: str | Path) -> Iterator[dict]:
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_jsonl(path: str | Path, rows: Iterable[dict]) -> int:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += 1
    return n
