"""String normalisation and similarity functions.

Implements the normalisation nu(.) and the normalised Levenshtein similarity of
review Eq. (3), plus the token Jaccard used by Naser (2026). Pure Python so the
project has no compiled dependencies.
"""
from __future__ import annotations

import re
import unicodedata

_LATEX_CMD = re.compile(r"\\[a-zA-Z]+\*?\s*")          # \emph, \textit ...
_LATEX_ACCENT = re.compile(r"\\[\"'`^~=.uvHckbdrt]\s*\{?([a-zA-Z])\}?")  # \"{o} -> o
_NON_ALNUM = re.compile(r"[^0-9a-z]+")
_PARTICLES = {"van", "von", "der", "den", "de", "del", "della", "da", "di", "du", "la", "le", "bin", "al", "el"}
ETAL_TOKENS = {"others", "et al", "et al.", "etal"}


def strip_latex(s: str) -> str:
    s = _LATEX_ACCENT.sub(r"\1", s)
    s = s.replace("\\&", "&").replace("~", " ")
    s = _LATEX_CMD.sub("", s)
    return s.replace("{", "").replace("}", "").replace("$", "")


def nu(s: str | None) -> str:
    """Case-fold, strip LaTeX, diacritics and punctuation; collapse spaces."""
    if not s:
        return ""
    s = strip_latex(str(s))
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.casefold()
    s = _NON_ALNUM.sub(" ", s)
    return " ".join(s.split())


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def lev_sim(a: str | None, b: str | None) -> float:
    """Review Eq. (3): 1 - lev(nu(a), nu(b)) / max(|nu(a)|, |nu(b)|). Range [0, 1]."""
    na, nb = nu(a), nu(b)
    if not na and not nb:
        return 1.0
    if not na or not nb:
        return 0.0
    return 1.0 - levenshtein(na, nb) / max(len(na), len(nb))


def token_jaccard(a: str | None, b: str | None) -> float:
    ta, tb = set(nu(a).split()), set(nu(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def surname(name: str) -> str:
    """Normalised family name from 'Last, First', 'First Last' or 'F. Last'."""
    name = strip_latex(name or "").strip()
    if not name:
        return ""
    if "," in name:
        last = name.split(",")[0]
    else:
        toks = name.split()
        last = toks[-1]
        # keep particles such as 'van der Berg' -> 'berg' (particles dropped)
    toks = [t for t in nu(last).split() if t not in _PARTICLES]
    return toks[-1] if toks else nu(last)


_ETAL = re.compile(r"^(and\s+)?(others|et\s*\.?\s*al\.?)$")


def is_etal(name: str) -> bool:
    """True for truncation markers: 'others', 'and others', 'et al.', 'et al'.

    Bug fix 2026-10-28 (debug log #2): 'and others' was not recognised, so genuine
    citations truncated with 'and others' failed the author-count check.
    """
    return bool(_ETAL.match(nu(name)))


def surnames(authors: list[str] | None) -> tuple[list[str], bool]:
    """Return (surnames, truncated_flag). 'others'/'et al.' sets the flag."""
    out, trunc = [], False
    for a in authors or []:
        if is_etal(a):
            trunc = True
            continue
        s = surname(a)
        if s:
            out.append(s)
    return out, trunc


def author_overlap(cited: list[str] | None, record: list[str] | None) -> float:
    """Fraction of cited surnames found in the record's surname set (order-free)."""
    cs, _ = surnames(cited)
    rs, _ = surnames(record)
    if not cs:
        return 0.0
    rset = set(rs)
    return sum(1 for s in cs if s in rset) / len(cs)


def norm_doi(doi: str | None) -> str:
    if not doi:
        return ""
    d = doi.strip().lower()
    for p in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/", "doi:"):
        if d.startswith(p):
            d = d[len(p):]
    return d.strip().rstrip(".")


_ARXIV_NEW = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?")
_ARXIV_OLD = re.compile(r"([a-z\-]+(\.[A-Z]{2})?/\d{7})(v\d+)?", re.I)


def norm_arxiv(s: str | None) -> str:
    if not s:
        return ""
    m = _ARXIV_NEW.search(s)
    if m:
        return m.group(1)
    m = _ARXIV_OLD.search(s)
    return m.group(1).lower() if m else ""


def norm_pages(p: str | None) -> str:
    if not p:
        return ""
    p = str(p).replace("\u2013", "-").replace("\u2014", "-").replace("--", "-")
    return "".join(p.split()).lower()
