"""Verifier scoring rules compared in the study.

V1  review Eqs. (2)-(5) and labelling function Eq. (9) (existence-only and full variants)
V2  Naser (2026, arXiv:2603.03299) sec. 3.4: 100*(0.6 Jaccard(title) + 0.2 authors + 0.2 year)
V3  Neralla et al. (2026, arXiv:2607.09774) Eq. (1): 0.60 title + 0.25 authors + 0.15 journal
V3a ablation of V3: author veto, no title substitution for missing authors

Every scorer takes the citation and the list of registry candidates and returns
a Verdict. All scorers read the same candidate list, so differences between them
come from scoring alone (frozen-cache control, protocol sec. 3).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .normalize import (author_overlap, lev_sim, norm_arxiv, norm_doi, norm_pages,
                        nu, surnames, token_jaccard)
from .records import Ref

# ---------------------------------------------------------------- defaults
V1_DEFAULTS = dict(tau=0.85, tau_title=0.90, tau_author=1.0, tau_venue=0.5, year_tol=0,
                   w_title=0.7, w_author=0.3)
V2_DEFAULTS = dict(confirmed=80.0, probable=65.0)
V3_DEFAULTS = dict(verified=80.0, partial=60.0)

_PLACEHOLDER = re.compile(
    r"(\[\s*author\s*,?\s*year\s*\]|title of (the )?paper|title here|lorem ipsum|"
    r"example\.(com|org)|\bauthor[s]?\s+name\b|\bxxxx?\b|john doe|jane (doe|smith))", re.I)


@dataclass
class Verdict:
    flagged: bool
    score: float
    label: str
    best: int | None = None          # index of best candidate
    details: dict = field(default_factory=dict)


def is_placeholder(ref: Ref) -> bool:
    text = " ".join([ref.title or "", " ".join(ref.authors or []), ref.venue or "", ref.raw or ""])
    return bool(_PLACEHOLDER.search(text))


# ---------------------------------------------------------------- V1
def venue_sim(a: str, b: str) -> float:
    na, nb = nu(a), nu(b)
    if not na or not nb:
        return 1.0
    ta, tb = set(na.split()), set(nb.split())
    short, long_ = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    contain = len(short & long_) / max(1, len(short))
    acr_a = "".join(w[0] for w in na.split() if w not in {"of", "the", "on", "and", "in", "for"})
    acr_b = "".join(w[0] for w in nb.split() if w not in {"of", "the", "on", "and", "in", "for"})
    acr = 1.0 if (na.replace(" ", "") in acr_b or nb.replace(" ", "") in acr_a) else 0.0
    return max(lev_sim(a, b), contain, acr)


def _v1_sim(ref: Ref, cand: Ref, p: dict) -> tuple[float, float, float]:
    t = lev_sim(ref.title, cand.title)
    cs, _ = surnames(ref.authors)
    a = author_overlap(ref.authors, cand.authors) if cs else None
    if a is None:
        return t, t, 0.0
    return p["w_title"] * t + p["w_author"] * a, t, a


def v1_review(ref: Ref, cands: list[Ref], **kw) -> Verdict:
    """Review Eqs. (2)-(5) + Eq. (9). flagged = primary label != 'valid'."""
    p = {**V1_DEFAULTS, **kw}
    if is_placeholder(ref):
        return Verdict(True, 0.0, "PH", None, {"E": 0})
    best, best_sim, bt, ba = None, -1.0, 0.0, 0.0
    for i, c in enumerate(cands):
        s, t, a = _v1_sim(ref, c, p)
        if s > best_sim:
            best, best_sim, bt, ba = i, s, t, a
    if best is None:
        return Verdict(True, 0.0, "TF", None, {"E": 0, "rho": 0, "n_cands": 0})
    r = cands[best]
    E = int(best_sim >= p["tau"])
    rho = int(bt >= 0.6 or ba >= 0.5)
    # Eq. (4): field fidelity; a field is checked only when both sides carry it
    cs, trunc = surnames(ref.authors)
    rs, _ = surnames(r.authors)
    checks = {}
    checks["T"] = int(bt >= p["tau_title"])
    if cs and rs:
        need = p["tau_author"]
        ov = author_overlap(ref.authors, r.authors)
        len_ok = trunc or len(cs) == len(rs)
        checks["A"] = int(ov >= need and len_ok)
    if ref.year and r.year:
        checks["Y"] = int(abs(ref.year - r.year) <= p["year_tol"])
    if ref.venue and r.venue:
        checks["V"] = int(venue_sim(ref.venue, r.venue) >= p["tau_venue"])
    loc = []
    if ref.pages and r.pages:
        loc.append(norm_pages(ref.pages) == norm_pages(r.pages))
    if ref.volume and r.volume:
        loc.append(nu(str(ref.volume)) == nu(str(r.volume)))
    if loc:
        checks["P"] = int(all(loc))
    F = int(all(checks.values()))
    # Eq. (5): identifier must resolve to the matched record (checked if both carry it).
    # doi_found: result of a DOI lookup done at retrieval (True/False), None if not done.
    H = 1
    doi_found = p.get("doi_found")
    if ref.doi and r.doi:
        H = int(norm_doi(ref.doi) == norm_doi(r.doi))
    elif ref.doi and doi_found is False:
        H = 0
    elif ref.doi and not r.doi:
        # identifier given but matched record has none: look for any candidate carrying it
        H = int(any(norm_doi(c.doi) == norm_doi(ref.doi) for c in cands if c.doi) or
                not any(c.doi for c in cands))
    if H and ref.arxiv_id and r.arxiv_id:
        H = int(norm_arxiv(ref.arxiv_id) == norm_arxiv(r.arxiv_id))
    if E == 0:
        label = "PAC" if rho else "TF"
    elif H == 0:
        label = "IH"
    elif F == 0:
        label = "PAC"
    else:
        label = "valid"
    det = {"E": E, "F": F, "H": H, "rho": rho, "sim": round(best_sim, 4),
           "title_sim": round(bt, 4), "author_ov": round(ba, 4), "fields": checks,
           "failed_fields": [k for k, v in checks.items() if not v], "n_cands": len(cands)}
    return Verdict(label != "valid", round(100 * best_sim, 2), label, best, det)


def v1_existence(ref: Ref, cands: list[Ref], **kw) -> Verdict:
    """V1-E: flag only when existence (Eq. 2) fails or a placeholder is found."""
    v = v1_review(ref, cands, **kw)
    flagged = v.label in ("PH", "TF") or v.details.get("E", 0) == 0
    return Verdict(flagged, v.score, "not_found" if flagged else "exists", v.best, v.details)


# ---------------------------------------------------------------- V2 Naser
def v2_naser(ref: Ref, cands: list[Ref], **kw) -> Verdict:
    p = {**V2_DEFAULTS, **kw}
    best, best_s = None, 0.0
    for i, c in enumerate(cands):
        j = token_jaccard(ref.title, c.title)
        a = author_overlap(ref.authors, c.authors)
        y = 1.0 if (ref.year and c.year and ref.year == c.year) else 0.0
        s = 100 * (0.6 * j + 0.2 * a + 0.2 * y)
        if s > best_s:
            best, best_s = i, s
    label = ("confirmed" if best_s >= p["confirmed"] else
             "probable" if best_s >= p["probable"] else "hallucinated")
    return Verdict(best_s < p["confirmed"], round(best_s, 2), label, best,
                   {"flag_at_probable": best_s < p["probable"]})


# ---------------------------------------------------------------- V3 AtomGPT
def _v3_score(ref: Ref, c: Ref, veto: bool) -> tuple[float, dict]:
    st = 100 * lev_sim(ref.title, c.title)
    cs, _ = surnames(ref.authors)
    if cs:
        sa = 100 * author_overlap(ref.authors, c.authors)
    else:
        sa = 0.0 if veto else st          # missing-field rule of Neralla et al.
    if ref.venue:
        sj = 100 * lev_sim(ref.venue, c.venue) if c.venue else 0.0
    else:
        sj = st
    s = 0.60 * st + 0.25 * sa + 0.15 * sj
    return s, {"st": round(st, 1), "sa": round(sa, 1), "sj": round(sj, 1)}


def v3_atomgpt(ref: Ref, cands: list[Ref], veto: bool = False, **kw) -> Verdict:
    p = {**V3_DEFAULTS, **kw}
    best, best_s, best_d = None, 0.0, {}
    for i, c in enumerate(cands):
        s, d = _v3_score(ref, c, veto)
        if s > best_s:
            best, best_s, best_d = i, s, d
    if veto and best is not None and surnames(ref.authors)[0] and best_d["sa"] < 50:
        label = "partial" if best_s >= p["partial"] else "likely_hallucinated"
        return Verdict(True, round(best_s, 2), label, best, {**best_d, "veto": True})
    label = ("verified" if best_s >= p["verified"] else
             "partial" if best_s >= p["partial"] else "likely_hallucinated")
    return Verdict(best_s < p["verified"], round(best_s, 2), label, best,
                   {**best_d, "flag_at_partial": best_s < p["partial"]})


def v3a_author_veto(ref: Ref, cands: list[Ref], **kw) -> Verdict:
    return v3_atomgpt(ref, cands, veto=True, **kw)


SCORERS = {
    "V1E": v1_existence,
    "V1F": v1_review,
    "V2": v2_naser,
    "V3": v3_atomgpt,
    "V3a": v3a_author_veto,
}
