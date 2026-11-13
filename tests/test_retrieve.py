"""Amendment D24/D25: batched arXiv lookups and the arXiv-title switch."""
from citefpr.records import Ref
from citefpr.retrieve import prefetch_arxiv, retrieve


class FakeCR:
    def search(self, ref): return []
    def doi(self, d): return []


class FakeAX:
    def __init__(self): self.id_calls, self.title_calls = [], 0
    def ids(self, ids):
        self.id_calls.append(list(ids))
        return [Ref(id=i, title=f"paper {i}", arxiv_id=i, source="arxiv") for i in ids]
    def title(self, t):
        self.title_calls += 1
        return []


class FakeOA:
    def __init__(self): self.searches = 0
    def doi(self, d): return []
    def search(self, t):
        self.searches += 1
        return []


def test_prefetch_batches_and_dedupes():
    ax = FakeAX()
    refs = [Ref(id=f"r{i}", title="x", arxiv_id=f"2101.{i:05d}v2") for i in range(250)]
    refs.append(Ref(id="dup", title="x", arxiv_id="arXiv:2101.00001"))
    pre = prefetch_arxiv(refs, ax, batch=100)
    assert [len(c) for c in ax.id_calls] == [100, 100, 50]
    assert len(pre) == 250 and pre["2101.00001"].title == "paper 2101.00001"


def test_prefetch_replaces_id_calls_and_title_switch_works():
    ax, oa = FakeAX(), FakeOA()
    ref = Ref(id="r", title="something unrelated", arxiv_id="2101.00007")
    pre = {"2101.00007": Ref(id="2101.00007", title="paper", arxiv_id="2101.00007")}
    cands = retrieve(ref, FakeCR(), ax, oa, arxiv_title=False, arxiv_prefetch=pre)
    assert [c.arxiv_id for c in cands] == ["2101.00007"]
    assert ax.id_calls == [] and ax.title_calls == 0 and oa.searches == 1


def test_default_path_unchanged():
    ax, oa = FakeAX(), FakeOA()
    ref = Ref(id="r", title="something unrelated", arxiv_id="2101.00007")
    retrieve(ref, FakeCR(), ax, oa)
    assert ax.id_calls == [["2101.00007"]] and ax.title_calls == 1


# ---- debug #10: transient failures are not cached and do not crash -------------------
import requests as _rq  # noqa: E402

from citefpr.cache import ResponseCache  # noqa: E402
from citefpr.registry import clients as _cl  # noqa: E402


class _Resp:
    def __init__(self, code, text="ok"):
        self.status_code, self.text, self.headers = code, text, {}

    def json(self):
        return {"ok": 1}


def _http(tmp_path):
    h = _cl._Http(ResponseCache(str(tmp_path / "c.sqlite")), "x", 0.0, "ua", max_retries=1)
    return h


def test_network_error_returns_none_and_is_not_cached(tmp_path, monkeypatch):
    monkeypatch.setattr(_cl.time, "sleep", lambda s: None)
    def boom(*a, **k): raise _rq.exceptions.ReadTimeout("t")
    monkeypatch.setattr(_cl.requests, "get", boom)
    h = _http(tmp_path)
    assert h.get_json_or_text("u", {"q": 1}) == (None, None)
    assert h.n_failed == 1
    monkeypatch.setattr(_cl.requests, "get", lambda *a, **k: _Resp(200))
    assert h.get_json_or_text("u", {"q": 1}) == (200, {"ok": 1})   # retried, not a cache hit


def test_final_429_not_cached_but_404_is(tmp_path, monkeypatch):
    monkeypatch.setattr(_cl.time, "sleep", lambda s: None)
    monkeypatch.setattr(_cl.requests, "get", lambda *a, **k: _Resp(429))
    h = _http(tmp_path)
    assert h.get_json_or_text("u", {"q": 2}) == (None, None) and h.n_failed == 1
    monkeypatch.setattr(_cl.requests, "get", lambda *a, **k: _Resp(404))
    assert h.get_json_or_text("u", {"q": 2}) == (404, None)
    monkeypatch.setattr(_cl.requests, "get", lambda *a, **k: _Resp(200))
    assert h.get_json_or_text("u", {"q": 2}) == (404, None)          # definitive answer cached
