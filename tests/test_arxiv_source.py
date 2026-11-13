import gzip
import io
import tarfile

from citefpr.arxiv_source import read_source, refs_from_source

BIB = b"""@inproceedings{a, title={Paper A}, author={Doe, Jane and Roe, Rick}, year={2019}}
@article{b, title={Paper B (never cited)}, author={Poe, Edgar}, year={2018}}"""
TEX = rb"Text \citep{a}. \input{x}"


def _tar(members: dict) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, data in members.items():
            ti = tarfile.TarInfo(name)
            ti.size = len(data)
            tf.addfile(ti, io.BytesIO(data))
    return buf.getvalue()


def test_read_source_tar_keeps_only_bib_and_tex_in_memory():
    blob = _tar({"main.tex": TEX, "refs.bib": BIB, "fig.png": b"\x89PNG", "../evil.tex": TEX})
    files = read_source(blob)
    assert set(files) == {"main.tex", "refs.bib", "../evil.tex"}   # read, never written to disk
    refs, st = refs_from_source("2101.00001", files)
    assert [r.extra["bibkey"] for r in refs] == ["a"]                # only cited entries kept
    assert st["n_bib_entries"] == 2 and st["n_refs_kept"] == 1
    assert refs[0].label == "genuine" and refs[0].id == "2101.00001:a"


def test_read_source_single_gzip_tex_has_no_bib():
    files = read_source(gzip.compress(TEX))
    refs, st = refs_from_source("2101.00002", files)
    assert refs == [] and st["has_bib"] is False
