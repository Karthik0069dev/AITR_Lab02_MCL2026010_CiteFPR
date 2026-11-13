"""Minimal BibTeX parser and LaTeX citation-key extraction (no external dependency).

Handles brace- and quote-delimited values, nested braces, numbers, @string macros used
as bare words (kept as text), comments and @preamble/@comment blocks.
"""
from __future__ import annotations

import re

from .normalize import norm_arxiv, norm_doi, strip_latex
from .records import Ref

_ENTRY = re.compile(r"@\s*([A-Za-z]+)\s*([{(])")
_CITE = re.compile(r"\\(?:no)?cite[a-zA-Z]*\*?\s*(?:\[[^\]]*\]\s*){0,2}\{([^}]*)\}")


def _read_value(s: str, i: int) -> tuple[str, int]:
    while i < len(s) and s[i].isspace():
        i += 1
    if i >= len(s):
        return "", i
    if s[i] == "{":
        depth, j = 0, i
        while j < len(s):
            if s[j] == "{":
                depth += 1
            elif s[j] == "}":
                depth -= 1
                if depth == 0:
                    return s[i + 1:j], j + 1
            j += 1
        return s[i + 1:], len(s)
    if s[i] == '"':
        j, depth = i + 1, 0
        while j < len(s):
            if s[j] == "{":
                depth += 1
            elif s[j] == "}":
                depth -= 1
            elif s[j] == '"' and depth == 0:
                return s[i + 1:j], j + 1
            j += 1
        return s[i + 1:], len(s)
    m = re.match(r"[^,}\s#]+", s[i:])
    return (m.group(0), i + m.end()) if m else ("", i)


def parse_bib(text: str) -> list[dict]:
    entries = []
    pos = 0
    while True:
        m = _ENTRY.search(text, pos)
        if not m:
            break
        etype = m.group(1).lower()
        start = m.end()
        if etype in ("comment", "preamble", "string"):
            _, pos = _read_value(text, m.end() - 1)
            continue
        close = "}" if m.group(2) == "{" else ")"
        km = re.match(r"\s*([^,\s]+)\s*,", text[start:])
        if not km:
            pos = start
            continue
        key = km.group(1)
        i = start + km.end()
        fields = {}
        while i < len(text):
            while i < len(text) and text[i] in " \t\r\n,":
                i += 1
            if i >= len(text) or text[i] == close:
                i += 1
                break
            fm = re.match(r"([A-Za-z_\-]+)\s*=\s*", text[i:])
            if not fm:
                nxt = text.find("\n@", i)
                i = len(text) if nxt == -1 else nxt
                break
            name = fm.group(1).lower()
            i += fm.end()
            parts = []
            while True:
                val, i = _read_value(text, i)
                parts.append(val)
                while i < len(text) and text[i].isspace():
                    i += 1
                if i < len(text) and text[i] == "#":
                    i += 1
                    continue
                break
            fields[name] = " ".join(p for p in parts)
        entries.append({"type": etype, "key": key, "fields": fields})
        pos = i
    return entries


def split_authors(a: str) -> list[str]:
    a = " ".join(a.split())
    return [x.strip() for x in re.split(r"\s+and\s+", a) if x.strip()]


def entry_to_ref(e: dict, rid: str, source_set: str = "") -> Ref:
    f = e["fields"]
    title = " ".join(strip_latex(f.get("title", "")).split())
    venue = f.get("journal") or f.get("booktitle") or f.get("publisher") or f.get("howpublished") \
        or f.get("school") or f.get("institution") or ""
    venue = " ".join(strip_latex(venue).split())
    arx = ""
    if f.get("archiveprefix", "").lower() == "arxiv" or "arxiv" in f.get("journal", "").lower() \
            or f.get("eprint"):
        arx = norm_arxiv(f.get("eprint", "") + " " + f.get("journal", "") + " " + f.get("volume", ""))
    if not arx:
        arx = norm_arxiv(f.get("url", "")) if "arxiv.org" in f.get("url", "") else ""
    year = None
    ym = re.search(r"(19|20)\d{2}", f.get("year", "") or f.get("date", ""))
    if ym:
        year = int(ym.group(0))
    return Ref(id=rid, title=title, authors=[strip_latex(x) for x in split_authors(f.get("author", ""))],
               year=year, venue=venue, doi=norm_doi(f.get("doi", "")), arxiv_id=arx,
               pages=f.get("pages", ""), volume=f.get("volume", ""), entry_type=e["type"],
               label="genuine", source_set=source_set, extra={"bibkey": e["key"]})


def cited_keys(tex: str) -> set[str]:
    tex = re.sub(r"(?<!\\)%.*", "", tex)  # drop comments
    keys = set()
    for m in _CITE.finditer(tex):
        for k in m.group(1).split(","):
            k = k.strip()
            if k:
                keys.add(k)
    return keys
