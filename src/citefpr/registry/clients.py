"""Registry clients: Crossref, arXiv, OpenAlex.

Rate limits (checked 28 Oct 2026, see research_decisions.md D14):
  Crossref polite pool (mailto): 3 req/s for queries, 10 req/s for single DOIs
  arXiv API: at most 1 request every 3 seconds, one connection
  OpenAlex: API key required since Feb 2026; DOI/ID lookups free, ~1,000 searches/day
All responses go through ResponseCache; with a frozen cache no request is sent.
"""
from __future__ import annotations

import os
import time
import xml.etree.ElementTree as ET

from ..cache import ResponseCache
from ..normalize import norm_arxiv, norm_doi
from ..records import Ref

try:
    import requests
except ImportError:  # parsing functions still work without requests
    requests = None


class _Http:
    def __init__(self, cache: ResponseCache, source: str, min_interval: float,
                 user_agent: str, max_retries: int = 4, timeout: float = 30.0):
        self.cache, self.source = cache, source
        self.timeout = timeout
        self.min_interval, self.max_retries = min_interval, max_retries
        self.ua = user_agent
        self._last = 0.0
        self.n_network = 0
        self.n_failed = 0  # requests that never got a definitive answer (not cached)

    TRANSIENT = (429, 500, 502, 503, 504)

    def get_json_or_text(self, url: str, params: dict, as_text: bool = False,
                         secret: dict | None = None):
        """GET with cache. `secret` params (API keys) are sent but never stored in the key.

        Debug #10 (13 Nov): a persistent network error or transient status (429/5xx) after all
        retries returns (None, None), is counted in `n_failed` and is NOT cached, so a re-run
        retries it. Previously the network error crashed the run and a final 429/5xx was cached
        as a permanent empty answer.
        """
        key = ResponseCache.make_key({"url": url, **params})
        send = {**params, **(secret or {})}
        hit = self.cache.get(self.source, key)
        if hit is not None:
            return hit
        if requests is None:
            raise RuntimeError("requests is not installed")
        delay = 2.0
        for attempt in range(self.max_retries + 1):
            wait = self.min_interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            try:
                r = requests.get(url, params=send, timeout=self.timeout,
                                 headers={"User-Agent": self.ua})
            except requests.RequestException:  # network error -> retry
                if attempt == self.max_retries:
                    self.n_failed += 1
                    return None, None
                time.sleep(delay); delay *= 2
                continue
            self.n_network += 1
            if r.status_code in self.TRANSIENT:
                if attempt == self.max_retries:
                    self.n_failed += 1
                    return None, None
                ra = r.headers.get("Retry-After")
                time.sleep(float(ra) if ra and ra.isdigit() else delay); delay *= 2
                continue
            body = None
            if r.status_code == 200:
                body = r.text if as_text else r.json()
            self.cache.put(self.source, key, r.status_code, body)
            return r.status_code, body
        raise RuntimeError("unreachable")


# ------------------------------------------------------------------ parsers
def parse_crossref_item(it: dict) -> Ref:
    title = (it.get("title") or [""])[0]
    authors = []
    for a in it.get("author") or []:
        fam, giv = a.get("family", ""), a.get("given", "")
        if fam:
            authors.append(f"{fam}, {giv}".strip(", "))
        elif a.get("name"):
            authors.append(a["name"])
    year = None
    for k in ("issued", "published-print", "published-online", "created"):
        dp = (it.get(k) or {}).get("date-parts") or [[None]]
        if dp and dp[0] and dp[0][0]:
            year = int(dp[0][0]); break
    venue = (it.get("container-title") or [""])
    venue = venue[0] if venue else ""
    return Ref(id=norm_doi(it.get("DOI", "")), title=title, authors=authors, year=year,
               venue=venue, doi=norm_doi(it.get("DOI", "")), pages=it.get("page", "") or "",
               volume=it.get("volume", "") or "", entry_type=it.get("type", ""), source="crossref")


_ATOM = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def parse_arxiv_feed(xml_text: str) -> list[Ref]:
    out = []
    root = ET.fromstring(xml_text)
    for e in root.findall("a:entry", _ATOM):
        aid = norm_arxiv(e.findtext("a:id", "", _ATOM))
        title = " ".join((e.findtext("a:title", "", _ATOM) or "").split())
        if not aid or title.lower() == "error":
            continue
        authors = [a.findtext("a:name", "", _ATOM) for a in e.findall("a:author", _ATOM)]
        pub = e.findtext("a:published", "", _ATOM)
        out.append(Ref(id=aid, title=title, authors=authors,
                       year=int(pub[:4]) if pub[:4].isdigit() else None,
                       venue=e.findtext("arxiv:journal_ref", "", _ATOM) or "arXiv",
                       doi=norm_doi(e.findtext("arxiv:doi", "", _ATOM)), arxiv_id=aid,
                       source="arxiv"))
    return out


def parse_openalex_work(w: dict) -> Ref:
    authors = [(a.get("author") or {}).get("display_name", "") for a in w.get("authorships") or []]
    loc = (w.get("primary_location") or {}).get("source") or {}
    arx = norm_arxiv(((w.get("ids") or {}).get("arxiv")) or "")
    return Ref(id=w.get("id", ""), title=w.get("title") or w.get("display_name") or "",
               authors=[a for a in authors if a], year=w.get("publication_year"),
               venue=loc.get("display_name", "") or "", doi=norm_doi(w.get("doi") or ""),
               arxiv_id=arx, entry_type=w.get("type", ""), source="openalex")


# ------------------------------------------------------------------ clients
class Crossref:
    BASE = "https://api.crossref.org/works"

    def __init__(self, cache: ResponseCache, mailto: str):
        if not mailto:
            raise ValueError("Crossref polite pool needs a mailto address")
        self.mailto = mailto
        self.http = _Http(cache, "crossref", 0.34, f"citefpr/0.1 (mailto:{mailto})")

    def search(self, ref: Ref, rows: int = 5) -> list[Ref]:
        first = ref.authors[0] if ref.authors else ""
        q = " ".join(x for x in [ref.title, first, str(ref.year or "")] if x).strip() or ref.raw
        if not q:
            return []
        st, body = self.http.get_json_or_text(self.BASE, {
            "query.bibliographic": q[:300], "rows": rows, "mailto": self.mailto,
            "select": "DOI,title,author,issued,container-title,page,volume,type"})
        if st != 200 or not body:
            return []
        return [parse_crossref_item(it) for it in body["message"].get("items", [])]

    def doi(self, doi: str) -> list[Ref]:
        d = norm_doi(doi)
        if not d:
            return []
        st, body = self.http.get_json_or_text(f"{self.BASE}/{d}", {"mailto": self.mailto})
        return [parse_crossref_item(body["message"])] if st == 200 and body else []


class Arxiv:
    BASE = "https://export.arxiv.org/api/query"

    def __init__(self, cache: ResponseCache, contact: str = "", timeout: float = 30.0,
                 max_retries: int = 4):
        self.http = _Http(cache, "arxiv", 3.1, f"citefpr/0.1 ({contact})",
                          max_retries=max_retries, timeout=timeout)

    def ids(self, ids: list[str]) -> list[Ref]:
        ids = [norm_arxiv(i) for i in ids if norm_arxiv(i)]
        if not ids:
            return []
        st, body = self.http.get_json_or_text(self.BASE, {"id_list": ",".join(ids),
                                                          "max_results": len(ids)}, as_text=True)
        return parse_arxiv_feed(body) if st == 200 and body else []

    def title(self, title: str, n: int = 3) -> list[Ref]:
        words = [w for w in title.replace('"', " ").split() if w.isalnum()][:12]
        if not words:
            return []
        st, body = self.http.get_json_or_text(self.BASE, {
            "search_query": "ti:\"" + " ".join(words) + "\"", "max_results": n}, as_text=True)
        return parse_arxiv_feed(body) if st == 200 and body else []


class OpenAlex:
    BASE = "https://api.openalex.org/works"

    def __init__(self, cache: ResponseCache, api_key: str | None = None, mailto: str = "",
                 max_searches: int = 900):
        self.key = api_key or os.environ.get("OPENALEX_API_KEY", "")
        self.mailto = mailto
        self.http = _Http(cache, "openalex", 0.11, f"citefpr/0.1 (mailto:{mailto})")
        self.searches_left = max_searches

    def _secret(self) -> dict:
        return {"api_key": self.key} if self.key else {}

    def doi(self, doi: str) -> list[Ref]:
        d = norm_doi(doi)
        if not d:
            return []
        st, body = self.http.get_json_or_text(f"{self.BASE}/doi:{d}", {}, secret=self._secret())
        return [parse_openalex_work(body)] if st == 200 and body else []

    def search(self, title: str, n: int = 3) -> list[Ref]:
        if not title:
            return []
        params = {"search": title[:200], "per_page": n}
        cached = self.http.cache.get("openalex", ResponseCache.make_key({"url": self.BASE, **params}))
        if cached is None:
            if self.searches_left <= 0:
                return []
            self.searches_left -= 1
        st, body = self.http.get_json_or_text(self.BASE, params, secret=self._secret())
        return [parse_openalex_work(w) for w in (body or {}).get("results", [])] if st == 200 else []
