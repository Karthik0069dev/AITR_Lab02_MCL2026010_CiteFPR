"""One retrieval pass per citation; the union of candidates is what every scorer sees.

Order (cheap and specific first): Crossref bibliographic query -> Crossref/OpenAlex DOI
lookup if the citation carries a DOI -> arXiv ID lookup if it carries an arXiv ID ->
arXiv title search and OpenAlex title search only if no candidate yet has title
similarity >= 0.8 (saves the rate-limited budgets).

Amendment D24/D25 (2026-11-13): `arxiv_title=False` turns off the arXiv title search, and
`arxiv_prefetch` (from `prefetch_arxiv`) replaces per-citation arXiv ID requests with one
batched request per 100 IDs. Defaults keep the original behaviour.
"""
from __future__ import annotations

from .normalize import lev_sim, norm_arxiv, norm_doi
from .records import Ref
from .registry.clients import Arxiv, Crossref, OpenAlex


def _dedupe(cands: list[Ref]) -> list[Ref]:
    seen, out = set(), []
    for c in cands:
        k = (c.source, norm_doi(c.doi) or c.arxiv_id or c.title.lower()[:80])
        if k not in seen:
            seen.add(k)
            out.append(c)
    return out


def prefetch_arxiv(refs: list[Ref], ax: Arxiv, batch: int = 100) -> dict[str, Ref]:
    """Look up every distinct arXiv ID in `refs` with batched id_list requests."""
    ids = sorted({norm_arxiv(r.arxiv_id) for r in refs if norm_arxiv(r.arxiv_id)})
    found: dict[str, Ref] = {}
    for i in range(0, len(ids), batch):
        for rec in ax.ids(ids[i:i + batch]):
            found[norm_arxiv(rec.arxiv_id)] = rec
    return found


def retrieve(ref: Ref, cr: Crossref, ax: Arxiv | None, oa: OpenAlex | None,
             arxiv_title: bool = True, arxiv_prefetch: dict[str, Ref] | None = None) -> list[Ref]:
    cands: list[Ref] = []
    cands += cr.search(ref)
    if ref.doi:
        cands += cr.doi(ref.doi)
        if oa is not None:
            cands += oa.doi(ref.doi)
    if ref.arxiv_id:
        if arxiv_prefetch is not None:
            hit = arxiv_prefetch.get(norm_arxiv(ref.arxiv_id))
            cands += [hit] if hit else []
        elif ax is not None:
            cands += ax.ids([ref.arxiv_id])
    good = any(lev_sim(ref.title, c.title) >= 0.8 for c in cands)
    if not good and ref.title:
        if ax is not None and arxiv_title:
            cands += ax.title(ref.title)
        if oa is not None and not any(lev_sim(ref.title, c.title) >= 0.8 for c in cands):
            cands += oa.search(ref.title)
    return _dedupe(cands)
