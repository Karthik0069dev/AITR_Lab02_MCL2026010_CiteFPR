"""Parser fixtures below are HAND-WRITTEN from the documented response formats, not
captured responses. Replace them with real captured responses after the first live run
(tracked as UNCERTAIN in baseline_validation.md)."""
import pytest

from citefpr.bibparse import cited_keys, entry_to_ref, parse_bib
from citefpr.cache import CacheMiss, ResponseCache
from citefpr.registry.clients import parse_arxiv_feed, parse_crossref_item, parse_openalex_work

BIB = r"""
% a comment
@string{acl = "ACL"}
@inproceedings{devlin2019bert,
  title = {{BERT}: Pre-training of Deep Bidirectional Transformers for Language Understanding},
  author = {Devlin, Jacob and Chang, Ming-Wei and Lee, Kenton and Toutanova, Kristina},
  booktitle = "Proceedings of NAACL-HLT",
  year = 2019, pages = {4171--4186}, doi = {10.18653/v1/N19-1423}
}
@article{vaswani2017,
  title={Attention is all you need},
  author={Vaswani, Ashish and others},
  journal={arXiv preprint arXiv:1706.03762}, year={2017}
}
@misc{unused, title={Never cited}, year={2020}}
"""
TEX = r"As shown \citep{devlin2019bert} and \cite[p.~3]{vaswani2017, devlin2019bert}. % \cite{unused}"


def test_parse_bib_and_cited_keys():
    es = parse_bib(BIB)
    assert [e["key"] for e in es] == ["devlin2019bert", "vaswani2017", "unused"]
    assert cited_keys(TEX) == {"devlin2019bert", "vaswani2017"}
    r = entry_to_ref(es[0], "x:devlin2019bert")
    assert r.title.startswith("BERT: Pre-training") and r.year == 2019
    assert r.authors[0] == "Devlin, Jacob" and r.doi == "10.18653/v1/n19-1423"
    r2 = entry_to_ref(es[1], "x:vaswani2017")
    assert r2.arxiv_id == "1706.03762" and r2.authors[-1] == "others"


def test_cache_roundtrip_and_frozen(tmp_path):
    c = ResponseCache(tmp_path / "c.sqlite")
    k = ResponseCache.make_key({"q": "x"})
    assert c.get("crossref", k) is None
    c.put("crossref", k, 200, {"a": 1})
    assert c.get("crossref", k) == (200, {"a": 1})
    c.close()
    f = ResponseCache(tmp_path / "c.sqlite", frozen=True)
    assert f.get("crossref", k) == (200, {"a": 1})
    with pytest.raises(CacheMiss):
        f.get("crossref", ResponseCache.make_key({"q": "y"}))
    with pytest.raises(RuntimeError):
        f.put("crossref", k, 200, {})


def test_parse_crossref_item():
    it = {"DOI": "10.18653/v1/N19-1423", "title": ["BERT: Pre-training ..."],
          "author": [{"given": "Jacob", "family": "Devlin"}],
          "issued": {"date-parts": [[2019, 6]]}, "container-title": ["Proceedings of NAACL"],
          "page": "4171-4186", "type": "proceedings-article"}
    r = parse_crossref_item(it)
    assert r.doi == "10.18653/v1/n19-1423" and r.year == 2019 and r.authors == ["Devlin, Jacob"]


def test_parse_arxiv_feed():
    xml = """<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
    <entry><id>http://arxiv.org/abs/1706.03762v7</id><published>2017-06-12T17:57:34Z</published>
    <title>Attention Is All
      You Need</title><author><name>Ashish Vaswani</name></author></entry></feed>"""
    (r,) = parse_arxiv_feed(xml)
    assert r.arxiv_id == "1706.03762" and r.title == "Attention Is All You Need" and r.year == 2017


def test_parse_openalex_work():
    w = {"id": "https://openalex.org/W1", "title": "Attention Is All You Need",
         "authorships": [{"author": {"display_name": "Ashish Vaswani"}}], "publication_year": 2017,
         "doi": "https://doi.org/10.48550/arxiv.1706.03762",
         "primary_location": {"source": {"display_name": "arXiv"}}, "ids": {}}
    r = parse_openalex_work(w)
    assert r.doi == "10.48550/arxiv.1706.03762" and r.authors == ["Ashish Vaswani"]
