from citefpr.normalize import (author_overlap, is_etal, lev_sim, levenshtein, norm_arxiv,
                               norm_doi, norm_pages, nu, surname, surnames, token_jaccard)


def test_levenshtein_known_values():
    assert levenshtein("kitten", "sitting") == 3
    assert levenshtein("", "abc") == 3
    assert levenshtein("abc", "abc") == 0


def test_lev_sim_eq3():
    # Eq. (3): 1 - 3/7
    assert abs(lev_sim("kitten", "sitting") - (1 - 3 / 7)) < 1e-9
    assert lev_sim("Attention Is All You Need", "attention is all you need.") == 1.0
    assert lev_sim("", "") == 1.0 and lev_sim("a", "") == 0.0


def test_nu_strips_latex_and_diacritics():
    assert nu(r"G{\"o}del's {T}heorem") == "godel s theorem"
    assert nu("Müller–Lyer") == "muller lyer"
    assert nu(r"\emph{BERT}: Pre-training") == "bert pre training"


def test_surnames_and_etal():
    assert surname("Vaswani, Ashish") == "vaswani"
    assert surname("Ashish Vaswani") == "vaswani"
    assert surname("A. Vaswani") == "vaswani"
    assert surname("Ludwig van Beethoven") == "beethoven"
    for marker in ("others", "and others", "et al.", "et al", "Et Al."):
        assert is_etal(marker), marker
    s, trunc = surnames(["Zhijie Nie", "and others"])
    assert s == ["nie"] and trunc


def test_author_overlap_order_free():
    assert author_overlap(["B Smith", "A Jones"], ["Jones, A.", "Smith, B."]) == 1.0
    assert author_overlap(["X Fake", "A Jones"], ["A Jones"]) == 0.5
    assert author_overlap([], ["A Jones"]) == 0.0


def test_identifier_normalisation():
    assert norm_doi("https://doi.org/10.18653/V1/N19-1423.") == "10.18653/v1/n19-1423"
    assert norm_arxiv("arXiv preprint arXiv:1706.03762v5") == "1706.03762"
    assert norm_arxiv("hep-th/9901001v2") == "hep-th/9901001"
    assert norm_pages("4171--4186") == norm_pages("4171 – 4186") == "4171-4186"


def test_token_jaccard():
    assert token_jaccard("a b c", "a b d") == 0.5
