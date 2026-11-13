import math

from citefpr.metrics import (bootstrap_ppv, cluster_bootstrap_rate, confusion, mcnemar_exact,
                             ppv, prf, wilson)


def test_mcnemar_exact():
    # 10 discordant pairs all one way: p = 2 * 0.5**10
    a = [1] * 10 + [0] * 5
    b = [0] * 10 + [0] * 5
    r = mcnemar_exact(a, b)
    assert r["a_only"] == 10 and r["b_only"] == 0 and abs(r["p"] - 2 / 1024) < 1e-12
    assert mcnemar_exact([1, 0], [1, 0])["p"] == 1.0


def test_cluster_bootstrap_rate_brackets_point_estimate():
    flags = [1, 0, 0, 0] * 25
    clusters = [f"p{i // 4}" for i in range(100)]
    lo, hi = cluster_bootstrap_rate(flags, clusters, n_boot=500, seed=3)
    assert lo <= 0.25 <= hi


def test_ppv_matches_review_example():
    # review sec. 5.1: R = 0.97, FPR = 0.03, pi = 0.01 -> PPV ~ 0.246
    assert abs(ppv(0.97, 0.03, 0.01) - 0.0097 / (0.0097 + 0.0297)) < 1e-12
    assert round(ppv(0.97, 0.03, 0.01), 3) == 0.246


def test_confusion_and_prf():
    c = confusion([1, 1, 0, 0], [1, 0, 1, 0])
    assert c == {"tp": 1, "fp": 1, "fn": 1, "tn": 1}
    m = prf(c)
    assert m["precision"] == 0.5 and m["recall"] == 0.5 and m["fpr"] == 0.5


def test_wilson_known_values():
    lo, hi = wilson(0, 10)
    assert lo == 0.0 and abs(hi - 0.2775) < 1e-3
    lo, hi = wilson(5, 10)
    assert abs(lo - 0.2366) < 1e-3 and abs(hi - 0.7634) < 1e-3
    assert all(math.isnan(x) for x in wilson(0, 0))


def test_bootstrap_ppv_close_to_formula():
    gen = [1] * 3 + [0] * 97          # FPR 0.03
    fab = [1] * 97 + [0] * 3          # recall 0.97
    b = bootstrap_ppv(gen, fab, pi=0.05, n_mix=400, mix_size=2000, seed=1)
    assert abs(b["mean"] - ppv(0.97, 0.03, 0.05)) < 0.03
    assert b["lo"] <= b["mean"] <= b["hi"]


def test_paper_id_handles_colons_in_bib_keys():
    import importlib.util, pathlib
    p = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "evaluate.py"
    spec = importlib.util.spec_from_file_location("evaluate", p)
    ev = importlib.util.module_from_spec(spec); spec.loader.exec_module(ev)
    assert ev.paper_id("2003.04970:DBLP:conf/acl/Reed") == "2003.04970"
    assert ev.paper_id("2003.11520:maas-EtAl:2011") == "2003.11520"
    assert ev.paper_id("2002.07339:smith2019") == "2002.07339"
    assert ev.paper_id("iclr:LGmO9VvuP5:ref:1") == "iclr:LGmO9VvuP5"
