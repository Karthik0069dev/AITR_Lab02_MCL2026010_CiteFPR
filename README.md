# AITR Lab 02 — How often do citation verifiers flag genuine references?

Satyala Murali Karthik (MCL2026010), IIIT Allahabad · AI Tools for Research, Lab 02

Repository: <https://github.com/Karthik0069dev/AITR_Lab02_MCL2026010_CiteFPR>

**Research question.** On genuine reference lists from pre-ChatGPT arXiv cs.CL papers, what
false-positive rate (FPR) do registry-based citation verifiers have, what positive predictive
value (PPV) does that imply when 0.5–5% of citations are fabricated (review Eq. 13), and which
reference types cause the false positives?

**Pathway.** Controlled comparative study (assignment pathway B) with one ablation.

| ID | Verifier | Source |
|----|----------|--------|
| V1E | Existence only (review Eq. 2) | my survey, §2.1 |
| V1F | Existence + field fidelity + identifier (Eqs. 2–5, label Eq. 9) | my survey, §2.1, §3.4 |
| V2 | 100·(0.6·title Jaccard + 0.2·authors + 0.2·year), flag < 80 | Naser 2026, arXiv:2603.03299 §3.4 |
| V3 | 0.60·title + 0.25·authors + 0.15·journal, flag < 80 | Neralla et al. 2026, arXiv:2607.09774 Eq. 1 |
| V3a | V3 with an author veto (ablation) | this study |

All verifiers score the **same frozen cache** of registry responses, so differences come from
scoring rules, not retrieval timing.

## Main result (13 Nov 2026)

567 genuine references (19 papers) · 807 ICLR 2026 fabricated citations

| | V1E | V1F | V2 | V3 | V3a |
|---|---|---|---|---|---|
| FPR on genuine | 16.9% | 47.1% | 16.0% | 17.3% | 17.3% |
| Recall on fabricated | 99.1% | 99.9% | 95.7% | 99.3% | 99.3% |
| PPV at 1% prevalence | 0.056 | 0.021 | 0.057 | 0.055 | 0.055 |

After adjudicating every V1E/V2/V3 false positive (AI-assisted from independent evidence, D34):
adjusted FPR V1E 14.8%, V2 13.9%, V3 15.2%; ~85% of flags fall on correct references
(`results/fpr_adjudicated.csv`).

84 of 96 V1E false positives had no candidate with title similarity ≥ 0.8 (retrieval miss).
References with a DOI: 0% FPR (V1E/V2/V3); with neither DOI nor arXiv ID: ~22%. Full numbers:
`results/metrics.csv`, `ppv.csv`, `mcnemar_fpr.csv`, `fp_mechanisms.csv`, `fp_by_identifier.csv`.

## Setup (tested 13 Nov 2026: Windows 11, Python 3.12.10; requirements are pure Python)

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q                                     # expect: 33 passed
python scripts/env_test.py --mailto YOUR_EMAIL          # expect: ENV TEST: PASS
```

Tested versions: requests 2.34.2, matplotlib 3.11.2, pytest 9.2.0. No GPU. `OPENALEX_API_KEY`
is optional (not used in the reported run, see D28); never commit it.

## Data

* **Positives:** `git clone https://github.com/aaFrostnova/CiteTracer` (MIT licence, code; commit
  8c47ca5 used). `data/iclr2026_hallucinated/hallucinated_refs_structured.json` holds **807**
  citations from 647 desk-rejected ICLR 2026 submissions (the paper reports 957). Dataset licence
  not stated — check before redistributing.
* **Negatives:** built by `scripts/build_genuine_set.py` from arXiv source files (arXiv API terms:
  ≤ 1 request / 3 s). Only `.bib` entries that the paper's `.tex` actually cites are kept.
* Raw data and the cache are not committed (see `data/README.md`); checksums of the frozen inputs
  are in `results/frozen_checksums.txt`.

## Commands — exactly as executed on 13 Nov 2026

```bash
CT=../CiteTracer/data
# Offline baseline check (G2) - reproduced the 28 Oct sandbox output byte-for-byte
python scripts/oracle_validation.py --data $CT --out results/oracle
# Data
python scripts/load_positives.py --citetracer-data $CT                      # 807 refs
python scripts/build_genuine_set.py --contact YOUR_EMAIL --n-papers 30      # 567 refs, 19/30 papers
# Retrieval phase 1: Crossref + DOI lookups + batched arXiv IDs (exit 2 = list of refs needing phase 2)
python scripts/run_retrieval.py --refs data/genuine_refs.jsonl data/fabricated_refs.jsonl \
    --mailto YOUR_EMAIL --fast --defer-arxiv-title --out data/candidates_phase1.jsonl
# Retrieval phase 2: adds the arXiv title fallback; repeat until it prints COMPLETE (exit 0)
python scripts/run_retrieval.py --refs data/genuine_refs.jsonl data/fabricated_refs.jsonl \
    --mailto YOUR_EMAIL --fast --arxiv-timeout 15 --out data/candidates.jsonl
# Freeze (copies + SHA-256), then score and evaluate offline
mkdir -p data/frozen && cp data/cache.sqlite data/frozen/cache_20261113.sqlite \
    && cp data/candidates.jsonl data/frozen/candidates_20261113.jsonl
python scripts/score.py --refs data/genuine_refs.jsonl data/fabricated_refs.jsonl \
    --candidates data/frozen/candidates_20261113.jsonl --out results/scores.csv
python scripts/evaluate.py --scores results/scores.csv --out results
python scripts/fp_mechanisms.py                 # error analysis
python scripts/adjudication_sheet.py --candidates data/frozen/candidates_20261113.jsonl
python scripts/make_tables.py --results results --out paper/tables
python scripts/make_tables_extra.py --results results --out paper/tables
python scripts/make_pipeline_figure.py --out paper/figures/pipeline
python scripts/check_paper_numbers.py    # 30/30: every claim in the paper re-derived from results/
python scripts/check_tex.py              # LaTeX structure (no TeX engine needed)
```

Adjudication (executed 13 Nov; evidence collection needs network):
```bash
python scripts/adjudication_evidence.py --mailto YOUR_EMAIL --oa-budget 95
python scripts/apply_adjudication.py
python scripts/evaluate.py --scores results/scores.csv --adjudication results/adjudication_sample.csv --out results
python scripts/adjusted_fpr.py
```

Run time on the laptop: genuine-set build ~3 min; retrieval ~3 h wall-clock on 13 Nov because
arXiv's API throttled and timed out (logs in `results/logs/`); scoring + evaluation < 1 min.
With the frozen cache, everything from `score.py` onward reproduces offline.

## Layout

```
configs/protocol.json      frozen protocol + dated amendments (D23-D32)
src/citefpr/               normalize, records, bibparse, cache, registry/clients, retrieve,
                           scorers (V1E V1F V2 V3 V3a), metrics, plots, arxiv_source
scripts/                   env_test, build_genuine_set, load_positives, run_retrieval, score,
                           evaluate, fp_mechanisms, adjusted_fpr, adjudication_evidence,
                           adjudication_sheet, apply_adjudication, make_tables,
                           make_tables_extra, make_pipeline_figure, check_paper_numbers,
                           check_tex, oracle_validation, make_oracle_inputs
tests/                     33 unit tests (pytest)
results/                   genuine outputs only (CSV, JSON, figures, logs/)
paper/                     main.tex, refs.bib, tables/, figures/ (compile on Overleaf)
research_decisions.md      decisions D1-D33, verification queue
baseline_validation.md     G2 validation report
ai_assistance_log.md       prompts, AI proposals, human decisions, debugging log (18 entries)
docs/                      Prompts 01-04 (Phase I, PDF + .tex) and 03-11 reports,
                           Prompt 12 plan, Prompt 16 review, Prompt 18 audit,
                           viva notes, demo script + demo card, architecture diagram
```

## Limitations

19 papers, one field, one quarter (Jan–Mar 2020); `.bbl`-only papers excluded; OpenAlex title
search off (keyless budget); adjudication was AI-assisted (V1F only partly adjudicated); ICLR
positives include badly wrong real papers and were partly found with registry tools; V2/V3
re-implemented from text (V3's fuzzy function not public).

## Minimum reproduction checklist (for a second student)

- [ ] `pytest` → 33 passed; `env_test.py` → PASS
- [ ] `oracle_validation.py` output equals `results/oracle/summary_by_subtype.csv`
- [ ] With my frozen cache (ask me; not committed): `sha256sum` matches `results/frozen_checksums.txt`
- [ ] `score.py` + `evaluate.py` → `results/metrics.csv` identical
- [ ] Without the cache: rebuild data and retrieval; expect small differences (registries change)

## Credits and licence

Scoring rules re-implemented from the cited papers. CiteTracer data © its authors (MIT code
licence; dataset terms unconfirmed). This repository: MIT. AI assistance (Claude, Anthropic) is
documented in `ai_assistance_log.md` and `docs/prompt18_ai_audit.md`.
