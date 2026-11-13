import copy

from citefpr.records import Ref
from citefpr.scorers import SCORERS, v1_review, v2_naser, v3_atomgpt

REAL = Ref(id="r", title="BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
           authors=["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee", "Kristina Toutanova"], year=2019,
           venue="Proceedings of NAACL-HLT", doi="10.18653/v1/n19-1423", pages="4171-4186")


def mutate(**kw):
    r = copy.deepcopy(REAL)
    for k, v in kw.items():
        setattr(r, k, v)
    return r


def test_identical_citation_passes_every_scorer():
    for name, fn in SCORERS.items():
        assert not fn(REAL, [REAL]).flagged, name


def test_no_candidates_is_flagged_everywhere():
    for name, fn in SCORERS.items():
        assert fn(REAL, []).flagged, name


def test_v1_labels_follow_eq9():
    assert v1_review(mutate(title="Placeholder: Title here"), [REAL]).label == "PH"
    assert v1_review(mutate(year=2017), [REAL]).label == "PAC"            # fidelity fails
    assert v1_review(mutate(doi="10.9999/fake"), [REAL]).label == "IH"   # identifier fails
    fake = Ref(id="f", title="Quantum gardening of recursive ontologies", authors=["Q Nobody"], year=2021)
    assert v1_review(fake, [REAL]).label == "TF"


def test_v1_doi_lookup_evidence():
    cand = mutate(doi="")
    assert not v1_review(REAL, [cand]).flagged                  # no evidence either way
    assert v1_review(REAL, [cand], doi_found=False).label == "IH"


def test_v1_et_al_citation_is_valid():
    cite = mutate(authors=["Jacob Devlin", "and others"])
    assert v1_review(cite, [REAL]).label == "valid"


def test_v2_year_change_alone_stays_confirmed():
    # documented property of Naser's weights: 60 + 20 + 0 = 80 -> still 'confirmed'
    v = v2_naser(mutate(year=2017), [REAL])
    assert v.score == 80.0 and v.label == "confirmed" and not v.flagged


def test_v3_missing_author_substitution_and_veto():
    cite = mutate(authors=[])
    assert v3_atomgpt(cite, [REAL]).details["sa"] == 100.0          # substituted by title score
    assert v3_atomgpt(cite, [REAL], veto=True).details["sa"] == 0.0
    wrong = mutate(authors=["Q Nobody", "Z Nobody"])
    # 0.60*100 + 0.25*0 + 0.15*100 = 75 -> 'partial' (flagged). Debug log #3: the first
    # version of this test wrongly expected 'verified'.
    v = v3_atomgpt(wrong, [REAL])
    assert v.score == 75.0 and v.label == "partial" and v.flagged
    # one fabricated author out of four still passes: 60 + 18.75 + 15 = 93.75
    one_wrong = mutate(authors=["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee", "Q Nobody"])
    assert v3_atomgpt(one_wrong, [REAL]).label == "verified"
