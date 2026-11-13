---
title: "AI Tools for Research — Lab 02, Phases I–III: Prompts 03 to 11"
subtitle: "From Literature Review to Implementation"
author:
  - "Satyala Murali Karthik (MCL2026010)"
  - "Department of Information Technology, IIIT Allahabad"
date: "28 October 2026"
papersize: letter
fontsize: 10pt
geometry: margin=0.9in
mainfont: DejaVu Serif
monofont: DejaVu Sans Mono
colorlinks: true
linkcolor: black
urlcolor: blue
header-includes:
  - \usepackage{etoolbox}
  - \AtBeginEnvironment{longtable}{\small}
  - \usepackage{float}
  - \floatplacement{figure}{H}
---

# Summary

This report covers Prompts 03–11 of the assignment: the literature-to-experiment map (03), the feasibility and novelty check (04), the research brief (05), the dataset and protocol design (06–07), and the coding and baseline validation (08–11). The selected study is gap **G-A** from Phase I: *how often do registry-based citation verifiers wrongly flag genuine references, and what does that imply at realistic fabrication rates?*

| Item | Status on 28 Oct 2026 |
|:--------------------|:---------------------------------------------------------------|
| Research question, pathway, protocol | Fixed and frozen (`configs/protocol.json`) |
| Code repository | 9 modules, 8 scripts, **27 unit tests pass** |
| Baseline validation (offline) | Executed on CiteTracer's 2,450 synthetic citations; results in §Prompt 10 |
| Environment test | Executed in the development sandbox: FAIL on network (registries blocked there); laptop run pending |
| Pilot and full run (live registries) | Pending on my laptop — commands in §Next steps |

Every number in this report comes from code I ran or from a source I opened; nothing is projected. All AI proposals were reviewed and accepted by me on 28 Oct 2026.

**Labels.** VERIFIED = checked in an original source or by execution · INFERRED = plausible, to be tested · UNKNOWN = no evidence yet.

# Phase I — from review to research question

## Prompt 03 — literature-to-experiment map

**Inputs.** Phase I shortlist G-A, G-B, G-C (D6); hardware: Ryzen 7 260, RTX 5050 laptop GPU (8 GB), Colab free tier; free registries only (D3); 3 weeks remaining (D16); full review PDF read 28 Oct.

**Three implementable methods from my review.**

| | M1 — CiteTracer [16] | M2 — registry matcher (Eqs. 2–5, Crossref [10]) | M3 — trie-constrained decoding [8] |
|:-------------|:-----------------------------|:-----------------------------|:-----------------------------|
| Algorithm | Parse PDF/BibTeX → evidence cascade (cache, URL, 8 scholar connectors, web agent) → field matching → LLM judges; 12 codes | Query registry → score candidates (Levenshtein title, Eq. 3; surname sets) → threshold τ | Beam search restricted to a prefix trie of valid identifiers |
| Data | 2,450 synthetic + real fabricated set (paper: 957; repo: 807, see V12) | Any reference list | Index to build (e.g. arXiv cs.CL titles; arXiv metadata CC0) |
| Access (VERIFIED) | Code MIT; data in repo and Hugging Face | Crossref, arXiv free; OpenAlex free key | GENRE repo archived, CC-BY-NC 4.0; Qwen3-8B Apache-2.0 |
| Limitation | Real set positives-only; LLM stages need paid cloud APIs | Registry coverage; noisy metadata [5] | Ensures existence, not support (§8.2); untested on citations (§6.1) |
| Compute | CPU + paid API | CPU + network | GPU, 8B in 4-bit |

**Three candidate studies.** (A) reproduce CiteTracer and extend it to natural genuine bibliographies — blocked by its cloud-API dependency; (B) controlled comparison of registry-matching rules on one frozen retrieval cache — CPU only, 3–4 h of throttled API calls; (C) targeted modification — used as the ablation inside B (author veto) or, for G-C, trie decoding (high engineering risk).

**Recommended minimum viable experiment: Study B.** Compare five scoring rules on genuine references from pre-ChatGPT arXiv cs.CL papers mixed with 807 real fabricated citations, measuring FPR, recall and PPV at prevalence π.

| Original source | Component | Executable baseline (G2) | Planned test (G3) |
|:--------------------|:----------------------|:----------------------|:----------------------|
| Review §5.1, Eq. 13 | PPV at prevalence π | PPV function; reproduces review's 0.246 | PPV curve, π = 0.5–5% |
| Review Eqs. 2–5, §6.2, §7; Crossref [10] | V1E / V1F | Unit-tested scorer; oracle run | FPR, recall, τ sweep, FP by type |
| Naser 2026 (new) | V2: 0.6 Jaccard + 0.2 authors + 0.2 year, ≥ 80 | Re-implemented, unit-tested | Same cache as V1 |
| Neralla et al. 2026 (new) | V3: 0.60 title + 0.25 authors + 0.15 journal, ≥ 80 | Re-implemented, unit-tested | Same cache; V3a author-veto ablation |
| Li et al. [16] (CiteTracer) | 807 ICLR 2026 positives | Loaded and audited | Recall on natural fabrications |
| Zhao et al. [29]; review §8.5 | Pre-LLM genuine lists | Source reader tested offline | FPR denominator |

**Pre-coding checks.** Done: CiteTracer cloned (the README's clone command names a different repository; the GitHub URL works); rule-based flags read in code (they still require AWS Bedrock, D17). Open: dataset licence (V14); `.bib` availability in the pilot; OpenAlex key; Crossref rate headers; Naser/AtomGPT repositories (V16); fix the [6] attribution in review §5.3 (D15).

## Prompt 04 — feasibility, novelty and resource access

**Search strings** (to run in arXiv, Semantic Scholar, Google Scholar, ACL Anthology, DBLP; S1, S5, S6 already run):

- S1 ("hallucinated citation\*" OR "fabricated reference\*") AND ("false positive\*" OR precision OR specificity)
- S2 ("reference verification" OR "citation verification") AND (Crossref OR OpenAlex OR "Semantic Scholar") AND evaluat\*
- S3 ("reference matching" OR "record linkage") AND (bibliographic OR scholarly) AND (threshold OR fuzzy)
- S4 ("non-existent citation\*") AND (baseline OR "pre-LLM")
- S5 ("constrained decoding" OR trie) AND (citation\* OR bibliograph\*)
- S6 ("prompt framing" OR "prompt sensitivity") AND ("citation fabrication" OR "hallucinated reference\*")
- S7 (coverage OR "metadata quality") AND (Crossref OR OpenAlex)

Neighbouring categories: detectors reporting precision/FPR; pre-LLM reference-matching studies (incl. Crossref's own); registry coverage comparisons; human citation-error studies; in-the-wild audits with a pre-LLM baseline; trie-constrained generative retrieval; multi-model fabrication audits.

**Novelty matrix.** G-A is not a new problem; my contribution is scale, prevalence-aware PPV and an explanation of false positives.

| Published method | VERIFIED contribution | Limitation | My difference | Missing |
|:--------------|:--------------------------|:--------------------|:--------------------|:--------------|
| CiteTracer [16] | 12-code detector; class F1 97.0/95.8/98.5; 97.1% of real fabrications caught | Real set positives-only; clean seeds | FPR on natural bibliographies | Dataset licence |
| Badalova & Mayr 2026 | 5 open tools on 104 references; 26–62 of 84 genuine flagged (FPR 31–74%, my arithmetic) | 3 documents; no prevalence or threshold analysis | 20–30× larger genuine set; PPV; τ sweep; causes | Tool code not run |
| Neralla et al. 2026 | Flags 94/100 NeurIPS fabrications; author mismatch decisive | Positives only; single source | The balanced evaluation they call for | Repo not opened |
| Naser 2026 | 10 models, 69,557 citations; effect sizes model 0.236 > domain 0.193 > framing 0.115 | Precision checked on 225 citations; 8/75 "hallucinated" were real | Scorer used as V2; makes G-B redundant (D10) | Repo not opened |
| Zhao et al. [29] | 111 M references; ≥ 146,932 hallucinated in 2025 | Population estimate | Pre-LLM lists as FPR denominator | Thresholds |
| GENRE [8] (G-C) | Trie-constrained entity names | Entities only; archived; CC-BY-NC | Scholarly titles | No citation evaluation found (V6) |

**Resource access.** Crossref: free; polite pool 3 req/s for queries, 10 for single DOIs (VERIFIED). OpenAlex: key required since 13 Feb 2026; free key $1/day; DOI lookups unlimited; ~1,000 searches/day (VERIFIED). arXiv: ≤ 1 request / 3 s; research use allowed (VERIFIED). CiteTracer: code MIT (VERIFIED), data licence UNKNOWN. PyTorch on RTX 5050 needs CUDA 12.8+ builds — not needed, the study is CPU-only.

**Compute and time.** About 4,000 references → Crossref ≈ 25 min at the polite ceiling (plan 2–3 h); arXiv lookups < 1 h; scoring minutes; hand adjudication of ≤ 300 flagged references ≈ 7–8 h (all INFERRED until the pilot). **Plan:** week 1 (28 Oct–4 Nov) G1+G2; week 2 (4–11 Nov) G3 full run; week 3 (11–18 Nov) G4 paper, repository, audit, demo.

**Go / no-go.** G-A: **GO** if by 4 Nov a Crossref query works, ≥ 200 genuine references are cached and V1 gives a pilot FPR. G-B: **dropped** (D10). G-C: fallback only (D11). Fallbacks: drop CiteTracer as comparator (done, D17); if the positives' licence forbids reuse, use rule-based mutations of genuine references; if few papers ship `.bib`, hand-curate 20 bibliographies; if OpenAlex budget runs out, Crossref + arXiv only.

## Prompt 05 — research problem, questions and success criteria

**Problem.** Registry-based citation verifiers are evaluated mostly on known fabrications, so their false-positive rate on ordinary genuine reference lists — and therefore how many of their flags are right in practice — is largely unmeasured (review §5.1–§5.2, Eq. 13).

| | RQ1 — false positives | RQ2 — realistic prevalence | RQ3 — causes |
|:---------------|:-------------------------|:-------------------------|:-------------------------|
| Question | FPR of V1E, V1F, V2, V3, V3a on genuine references from pre-ChatGPT arXiv cs.CL papers? | PPV of each when 0.5–5% of citations are fabricated? | Which reference types and failed checks cause false positives? |
| Data | 2,000–3,000 cited `.bib` entries, ~100 papers (2020 – 29 Nov 2022) | + 807 ICLR 2026 fabricated citations | Flagged genuine references |
| Variables | IV: verifier; DV: FPR | IV: verifier, π; DV: PPV | IV: entry type, DOI, arXiv-only, failed field; DV: FPR |
| Metric | FPR, Wilson 95% CI, paper-level bootstrap; exact McNemar between verifiers | Eq. 13 PPV; bootstrap PPV | FPR per stratum |
| Decision rule | McNemar p < 0.05 **and** gap ≥ 2 points | Useful = PPV ≥ 0.5 at π = 1% | Stratum FPR ≥ 2× overall, n ≥ 30 |
| Hypothesis | H1: V1F FPR > V1E FPR | H2: no verifier reaches PPV ≥ 0.5 at 1% (needs FPR ≤ recall/99) | H3: misc, book, thesis, arXiv-cited entries highest |
| Contradiction | V1F within 1 point of V1E | Any verifier with PPV ≥ 0.5 at 1% | Roughly equal FPR across types |

The ablation V3 vs V3a (author veto) is a sub-question of RQ1. **Out of scope:** "which verifier is best" in general, claim-level support (SM), commercial tools, fields other than cs.CL.

| Brief field (§11 template) | Entry |
|:----------------------|:----------------------------------------------------------|
| Review topic, key papers | Citation fabrication (my survey); Li et al. [16], Ansari [2], Zhao et al. [29], Naser 2026, Neralla et al. 2026 |
| Gap | Detectors report recall on known fabrications, rarely FPR on genuine lists (§5.1–§5.2) |
| Pathway | Controlled comparative study (B) with one ablation |
| Data | Genuine: cited `.bib` entries of pre-30-Nov-2022 arXiv cs.CL papers. Positives: 807 ICLR 2026 citations |
| Comparators | V1E, V1F (review), V2 (Naser), V3 (Neralla et al.), V3a ablation |
| Metric and control | FPR with CIs; one frozen cache for all verifiers |
| Computing, risks | CPU; 3–4 h API calls; risks: missing `.bib`, coverage, licence |
| First milestone | Done: oracle validation, pipeline run, 27 tests. Next: laptop env test + 10-paper pilot |

# Phase II — experiment plan

## Prompt 06 — dataset and comparator validation

| Item | Structure (inspected) | Access | Pitfalls |
|:----------------|:-------------------------------------|:------------------|:-------------------------------|
| Positives: CiteTracer ICLR 2026 | 647 papers, **807** citations; title, authors, venue, year, DOI, arXiv ID, raw text | Code MIT; data terms UNKNOWN | 807 ≠ 957 reported; noisy venue field; label includes real papers with major errors |
| Synthetic set (G2 only) | 2,450 citations; `meta.json` holds each seed record and mutation | as above | One field mutated at a time; clean seeds |
| Negatives: arXiv sources | Built by `build_genuine_set.py`; only `.bib` entries the `.tex` cites | arXiv terms, 1 req / 3 s | Some papers ship only `.bbl`; human errors; references clustered by paper |
| V1E, V1F / V2 / V3, V3a | `scorers.py`, re-implemented from the papers | — | Thresholds fixed from papers; V3 "fuzzy" function unspecified |

**Design.** Nothing is trained, so there is no train/test split: thresholds come from the papers and are fixed before results; the τ sweep is sensitivity only. **Leakage and bias:** citing papers cannot be in both sets (2020–22 arXiv vs 2026 ICLR; audited by ID prefix); references of one paper are clustered (paper-level bootstrap); positives were partly found with registry tools, so recall is optimistic; registries change, so responses are cached with fetch times; the genuine set is never filtered by "found in a registry". **Simplest credible baseline:** V1E.

## Prompt 07 — frozen evaluation protocol

![Pipeline (Mermaid source: `docs/architecture_compact.mmd`). All verifiers read the same frozen cache.](pipeline_tworow.png){width=88%}

| Setting | Frozen value (28 Oct 2026) |
|:--------------------|:------------------------------------------------------------|
| Input → output | Citation fields + registry candidates → flag (1 = fabricated), score, label per verifier |
| Preprocessing | ν: case-fold, strip LaTeX, diacritics, punctuation; surname sets; normalised DOI/arXiv IDs |
| Control | One retrieval pass; cache frozen and checksummed before scoring |
| V1 | τ = 0.85 on 0.7·title + 0.3·authors; title ≥ 0.90; all cited surnames; year exact; venue ≥ 0.5; locators exact |
| V2 / V3 | Flag below 80 (secondary 65 / 60), as published |
| Primary metric | FPR on genuine references (lower is better) |
| Secondary | Recall (higher better); PPV at π = 0.5, 1, 2, 5% (higher better); exact McNemar |
| Uncertainty | Wilson 95% CI; paper-level cluster bootstrap, 2,000 resamples |
| Seed | 20261028 (paper sampling, bootstraps, adjudication sample) |
| Deep analysis | τ sweep 50–95; FP by entry type and failed field; ablation V3 vs V3a |
| Outputs | Table 1 FPR/recall/CIs; Table 2 PPV by π; Table 3 FP by type; Figures FPR, PPV, τ sweep |

**Threats to validity.** Construct: pre-2022 references can still be wrong (hand adjudication). Internal: retrieval failure looks like fabrication (zero-candidate count reported). External: one field, three registries. Positives: selection bias. Re-implementation: V2/V3 details underspecified. **Pre-experiment checklist:** protocol unchanged or changes logged; thresholds not touched after the pilot; cache frozen; genuine set built with the fixed seed; pilot reported separately. **Legitimate changes** (bug or access fixes only) get a dated D-entry; superseded result files are kept.

# Phase III — AI coding and baseline validation

## Prompt 08 — environment

Python 3.13.18, requests 2.34.2, matplotlib 3.11.2, pytest 9.1.1 (versions the tests passed with); no GPU, CUDA or PyTorch needed. Set-up: `pip install -r requirements.txt`, `python -m pytest -q` (27 passed), `python scripts/env_test.py --mailto <email>`. **Sandbox run (real):** packages present, no GPU, Crossref/arXiv/OpenAlex `ProxyError`, GitHub reachable → `ENV TEST: FAIL` (`results/env_report_sandbox.json`). The laptop run is the next step. Repository: `src/citefpr/` (code), `scripts/`, `tests/`, `configs/`, `results/` (real outputs only), `data/README.md` (raw data never committed), `research_decisions.md`, `baseline_validation.md`, `ai_assistance_log.md`, `docs/`. Secrets come only from environment variables and never enter the cache key.

## Prompt 09 — baseline modules

| Module | Function | Tests | Executed |
|:----------------------|:-----------------------------------------------|:------------|:------------|
| `normalize.py` | ν, Eq. 3 similarity, surnames, et-al markers, identifiers | 7 | yes |
| `bibparse.py`, `arxiv_source.py` | BibTeX parser, `\cite` keys, in-memory archive reader | 3 | offline |
| `cache.py` | SQLite response cache with frozen mode | 1 | yes |
| `registry/clients.py`, `retrieve.py` | Crossref, arXiv, OpenAlex clients; one retrieval pass | 3 (parsers) | parsers only |
| `scorers.py` | V1E, V1F, V2, V3, V3a | 7 | yes |
| `metrics.py`, `plots.py` | FPR, recall, Wilson, Eq. 13, bootstrap, McNemar; figures | 6 | yes |

Deliberate deviations: V2/V3 re-implemented from the papers' text; CiteTracer used for data only (D17); no compiled dependencies (D20); V1 split into existence and full fidelity (D18).

## Prompt 10 — baseline validation report

Each of CiteTracer's 2,450 synthetic citations was scored against its own seed record as the only candidate ("oracle retrieval"), isolating the scoring stage. No published numbers exist for these rules on these data.

| CiteTracer subtype (n) | V1E | V1F | V2 | V3 | V3a |
|:-----------------------------------------|----:|----:|----:|----:|----:|
| Real R1–R3, flagged = false positive (1,023) | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Potential P1, P3 (271) | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| H1 title (200) | 75.5% | 91.5% | 77.0% | 65.5% | 65.5% |
| H2 authors (198) | 33.3% | 67.2% | 0.0% | 33.3% | 33.3% |
| H3 venue (197) | 0.0% | 98.0% | 0.0% | 0.0% | 0.0% |
| H4 year (195) | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% |
| H5 DOI (200) | 0.0% | 77.0% | 0.0% | 0.0% | 0.0% |
| H6 pages/volume/publisher/location (166) | 0.0% | 40.4% | 0.0% | 0.0% | 0.0% |
| **All hallucinated — recall (1,156)** | **18.8%** | **80.0%** | **13.3%** | **17.0%** | **17.0%** |

The 95% Wilson interval for 0/1,023 is 0–0.37%.

![Share of synthetic fabrications flagged under perfect retrieval (`results/oracle/`).](oracle_detection_by_subtype.png){width=78%}

![Threshold sweep on the synthetic set: recall (solid) and FPR (dashed). V2 recall jumps from 13.3% to 45.1% between thresholds 80 and 81 (`results/oracle_pipeline/`).](tau_sweep.png){width=100%}

**VERIFIED.** Similarity, normalisation, Wilson CI and McNemar match hand-computed values; the PPV function reproduces the review's 0.246; V1 labels follow Eq. 9; the pipeline runs end to end on 2,179 citations with a clean audit. Properties of the published rules: V2 passes a year-only error (score exactly 80); V3 passes a venue-only error (85) and one wrong author in four; the V3a veto changes no synthetic outcome. **UNCERTAIN.** Parsers tested on hand-written fixtures; V3 "fuzzy" function and V2's missing-year rule are my readings; V1 venue rule is my choice (frozen). **Out of scope / not fixed.** V1F misses 99/166 H6 cases, all publisher (67) or location (32) changes outside review Eq. 4; 46/200 H5 cases cannot be refuted offline (seed has no DOI) — live retrieval adds a DOI lookup. **Finding for the study:** CiteTracer's synthetic "Real" class is too clean to measure false positives, which supports measuring FPR on natural reference lists.

## Prompt 11 — debugging log (real failures)

| # | Actual output | Confirmed cause | Fix and verification |
|:--|:-----------------------------|:-----------------------------|:-----------------------------|
| 1 | `pip install rapidfuzz` → `NameResolutionError` | Sandbox blocks PyPI | Pure-Python Levenshtein and BibTeX parser (D20); unit tests |
| 2 | V1F flagged 59/343 genuine R3 citations, all on the author check | `is_etal()` missed "and others" | Regex fix; R3 0.0% on rerun; first oracle table discarded |
| 3 | Test expected "verified", got "partial" | **The AI's test was wrong**: 0.60·100 + 0.25·0 + 0.15·100 = 75 | Expectation corrected; one-wrong-author case added |
| 4 | `TypeError: missing ... 'id'` in loader | Year parsed via record constructor | `parse_year()`; 807 citations load |
| 5 | V1F missed 99/166 H6 | Not a bug: fields outside Eq. 4 | Reported as scope limit |
| 6 | V1F missed 46/200 H5 | Not a bug offline: no DOI to compare | `doi_found` filled by live lookup |

# Next steps (laptop) — closes G2

```bash
pip install -r requirements.txt && python -m pytest -q   # 27 passed
python scripts/env_test.py --mailto <email>              # ENV TEST: PASS
git clone --depth 1 \
    https://github.com/aaFrostnova/CiteTracer.git ../CiteTracer
CT=../CiteTracer/data
python scripts/oracle_validation.py --data $CT    # reproduces Prompt 10
python scripts/load_positives.py --citetracer-data $CT
python scripts/build_genuine_set.py --contact <email> --n-papers 10 \
    --out data/genuine_pilot.jsonl
python scripts/run_retrieval.py \
    --refs data/genuine_pilot.jsonl data/fabricated_refs.jsonl \
    --mailto <email> --limit 200 --out data/candidates_pilot.jsonl
python scripts/score.py \
    --refs data/genuine_pilot.jsonl data/fabricated_refs.jsonl \
    --candidates data/candidates_pilot.jsonl \
    --out results/pilot/scores.csv
python scripts/evaluate.py --scores results/pilot/scores.csv \
    --out results/pilot
```

\newpage

# Research decisions, verification queue and AI-assistance log

| # | Decision | Evidence | Label |
|:----|:----------------------------------------|:--------------------------------|:-------------|
| D1–D7 | Phase I set-up (area, free tools, hardware, shortlist) | Phase I submission | — |
| D8 | Main study = G-A, controlled comparison | Prompts 03–04 | INFERRED |
| D9 | Claim scale, PPV and FP causes, not a new problem | Badalova & Mayr; Neralla et al. | VERIFIED |
| D10 | Drop G-B | Naser 2026 covers it | My decision |
| D11 | G-C fallback only | V6, time | INFERRED |
| D12 | All verifiers read one frozen cache | Protocol | INFERRED |
| D13 | Genuine set = cited `.bib` entries, pre-30-Nov-2022 arXiv cs.CL | Zhao et al. [29]; review §8.5 | INFERRED |
| D14 | Crossref polite pool, arXiv, OpenAlex DOI lookups; cache all | 2026 rate limits | VERIFIED |
| D15 | Fix the [6] attribution in review §5.3 | Linardon et al. 2025, not [6] | VERIFIED for [6] |
| D16 | 3-week plan, G1+G2 merged | Week 1 used | My decision |
| D17 | Drop CiteTracer as comparator | Rule-based flags need Bedrock (code l.136–171) | VERIFIED |
| D18 | Split V1 into V1E and V1F | Separates FP kinds | INFERRED |
| D19 | Ablation V3a (author veto) | Neralla et al. §4.1 | INFERRED |
| D20 | No compiled dependencies | PyPI blocked; simpler install | VERIFIED |
| D21 | Oracle run is a scoring check, never a headline | Candidates are true seeds | — |
| D22 | Positives = 807 ICLR citations | Counted | VERIFIED |

| Item | Status |
|:-------------------------|:-------------------------------------------------------|
| V3 positives-only sets | VERIFIED for CiteTracer and the NeurIPS set; CiteAudit has negatives (review Table 8) |
| V4 prompt sensitivity [6] | VERIFIED for prompt variation; "topic familiarity, prompt specificity" belong to Linardon et al. 2025 |
| V6 trie decoding on citations | UNKNOWN; none found in three searches |
| V10 Kalai et al. bound | VERIFIED (base models, arbitrary facts) — review §2.2 consistent |
| V11 CiteAudit authors [24] | VERIFIED correct |
| V12 CiteTracer real set | VERIFIED 807 citations / 647 papers shipped; INFERRED the gap to 957 is the unshipped second venue |
| V14 CiteTracer data licence | UNKNOWN (code is MIT) |
| V15 NeurIPS 2025 list | UNKNOWN |
| V16 Neralla et al. fuzzy function | UNKNOWN |

| Step | Prompt | AI action | Verification | My decision |
|:----|:------|:------------------------------------|:------------------------|:--------------|
| 4–6 | 03, 04, V-checks | Methods, studies, MVE, novelty matrix, access, V-updates | Sources opened | Accepted 28 Oct |
| 7–9 | 05–07 | Brief, dataset sheet, frozen protocol | Read against Phase I | Accepted 28 Oct |
| 10 | 08 | Environment test, repository | Sandbox FAIL (expected) | Laptop run pending |
| 11 | 09 | 9 modules, 8 scripts | 27 tests pass | Code reviewed, accepted |
| 12–13 | 10–11 | Oracle validation; 6 debugging entries | Executed; fixes re-tested | Accepted 28 Oct |

Tools: Claude (Anthropic) with web search and a Linux sandbox in which the code was written and run. AI limitations observed: a wrong test expectation (debug #3); Zhao et al. first mislabelled as not in my review; registry parsers written without live responses.

# References

Review references as numbered in my survey: [2] Ansari 2026; [5] Besançon et al. 2024; [6] Bhattacharyya et al. 2023; [8] De Cao et al. 2021; [10] Hendricks et al. 2020; [16] Li, Lin, Ma 2026 (arXiv:2605.08583); [24] Shi et al. 2026; [29] Zhao et al. 2026 (arXiv:2605.07723). New at this stage: Badalova & Mayr 2026 (arXiv:2607.22693); Naser 2026 (arXiv:2603.03299); Neralla et al. 2026 (arXiv:2607.09774); Kalai et al. 2025 (arXiv:2509.04664). Resources: CiteTracer repository (github.com/aaFrostnova/CiteTracer); arXiv API terms (info.arxiv.org/help/api/tou.html); Crossref REST API rate limits (crossref.org blog, Nov 2025; community post, Jul 2026); OpenAlex API keys and pricing (blog.openalex.org, Feb 2026). All were opened on 28 Oct 2026.

# Appendix A — prompts used (filled)

**Prompt 03.** My literature review [*Benchmarking Citation Fabrication Rates Across LLMs and Agentic Search Tools* — attached] identified these candidate gaps: [G-A detector FPR/PPV at realistic prevalence; G-B prompt/protocol sensitivity; G-C constrained decoding over a verified index]. Identify three published methods … recommend one minimum viable research experiment for [Ryzen 7 260, RTX 5050 8 GB, Colab free tier] and [3 weeks remaining] … (assignment text otherwise verbatim).

**Prompt 04.** My candidate study is [a controlled comparison of registry-based citation verifiers on genuine pre-2022 reference lists mixed with real fabricated citations at controlled prevalence] … for [the same hardware] and [3 weeks] … (verbatim otherwise).

**Prompt 05.** Here is my verified gap [G-A, review §5.1–§5.2], selected study [Study B above] and source evidence [Li et al. [16]; Badalova & Mayr 2026; Neralla et al. 2026; Naser 2026; Zhao et al. [29]] …

**Prompt 06.** My question is [RQ1–RQ3] in [citation verification for scholarly references] …

**Prompt 07.** Design a reproducible protocol for [RQ1–RQ3] on [pre-2022 arXiv cs.CL genuine references + 807 ICLR 2026 fabricated citations] comparing [V1E, V1F, V2, V3] with [the V3a ablation] …

**Prompt 08.** Set up [local laptop, CPU-only] for [registry-based citation verification] using [Python 3.13, requests, matplotlib, pytest] …

**Prompt 09.** I am reproducing [the review's Eqs. 2–5 matcher and the scoring rules of Naser 2026 and Neralla et al. 2026] for [the frozen candidate cache] to produce [per-citation flags, scores and labels] …

**Prompt 10.** I have implemented [V1E, V1F, V2, V3, V3a] based on [review Eqs. 2–5; Naser 2026 §3.4; Neralla et al. 2026 Eq. 1]. Here are the code, data, configurations, logs and results: [repository; `results/oracle*`] …

**Prompt 11.** My code failed or behaved unexpectedly: [the six cases in the debugging log, with their actual outputs] …
