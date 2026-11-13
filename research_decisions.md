# research_decisions.md

Labels: VERIFIED (checked in a source or by execution) · INFERRED (plausible, to test) ·
UNKNOWN (no evidence). Full Phase I tables live in the Lab 02 submissions; this file keeps the
decisions that shape the code.

## Decisions

| # | Date | Decision | Reason | Evidence | Label | Next action |
|---|---|---|---|---|---|---|
| D1–D7 | 2026-10-22 | Phase I set-up: stay in the review's area; open models + free registries; hardware; shortlist G-A, G-B, G-C | see Phase I PDF | Phase I | — | done |
| D8 | 2026-10-28 | Main study = G-A, controlled comparison | no GPU; access verified; review §5.1 | Prompts 03–04 | INFERRED | done (brief written) |
| D9 | 2026-10-28 | Claim scale, PPV at prevalence and FP causes, not a new problem | Badalova & Mayr 2026; Neralla et al. 2026 | Prompt 04 §2 | VERIFIED | — |
| D10 | 2026-10-28 | Drop G-B entirely | Naser 2026 covers it | full text | VERIFIED (my decision) | — |
| D11 | 2026-10-28 | G-C fallback only | time, novelty unconfirmed | V6 | INFERRED | only if G-A fails |
| D12 | 2026-10-28 | All verifiers read one frozen cache | isolate scoring from retrieval | protocol | INFERRED | freeze cache before G3 |
| D13 | 2026-10-28 | Genuine set = cited .bib entries of pre-30-Nov-2022 arXiv cs.CL papers | pre-LLM baseline, Zhao et al. [29]; review §8.5 | — | INFERRED | pilot 10 papers |
| D14 | 2026-10-28 | Crossref polite pool first, arXiv, OpenAlex DOI lookups + limited search; cache all | 2026 rate limits | Crossref, OpenAlex announcements | VERIFIED | record headers in env test |
| D15 | 2026-10-28 | Fix the V4 attribution in review §5.3 | Linardon et al. 2025, not [6] | V4 | VERIFIED for [6] | edit review |
| D16 | 2026-10-28 | 3-week plan, G1+G2 merged | week 1 already used | my statement | VERIFIED | confirm deadline |
| D17 | 2026-10-28 | Drop CiteTracer as comparator V4 | rule-based flags need Bedrock; other agents call the LLM | `scripts/test_synthetic_samples.py` l.136–171 | VERIFIED (code read) | report in limitations |
| D18 | 2026-10-28 | Split V1 into V1E (existence) and V1F (full Eqs. 2–5) | separates "does it exist" from "is every field right"; FP causes differ | design | INFERRED | — |
| D19 | 2026-10-28 | Add ablation V3a (author veto) | Neralla et al. §4.1 name missing-field substitution as a cause of misses | their limitations | INFERRED | compare V3 vs V3a in G3 |
| D20 | 2026-10-28 | No compiled dependencies (pure-Python Levenshtein and BibTeX parser) | PyPI unreachable in the sandbox; simpler install on the laptop | debug log #1 | VERIFIED (executed) | — |
| D21 | 2026-10-28 | Use the oracle run as a scoring-stage check only, never as the headline result | candidates are the true seeds; retrieval not tested | baseline_validation.md | — | — |
| D22 | 2026-10-28 | Positives = 807 ICLR citations (not 957) | structured file count | executed load | VERIFIED | ask the authors whether the second venue's set can be shared |

## Verification queue (open items only)

| # | Claim | Status |
|---|---|---|
| V6 | constrained decoding untested on citations | UNKNOWN, no counter-evidence |
| V7 | CiteCheck baseline ranges | PARTLY VERIFIED |
| V12 | CiteTracer real set size/provenance | VERIFIED: repo ships 807 structured ICLR citations from 647 papers. INFERRED: the gap to the paper's 957 is the second (anonymous) venue, not shipped |
| V14 | CiteTracer dataset licence | UNKNOWN (code MIT) |
| V15 | NeurIPS 2025 list downloadable | UNKNOWN |
| V16 | Neralla et al. exact fuzzy function | VERIFIED not released: repo (commit 7e7d019, opened 13 Nov) has evaluation notebooks/CSVs only; paper describes 0–100 fuzzy similarity without naming a function. Levenshtein×100 stays my reading |
| V17 | Badalova & Mayr false positives | CORRECTED 13 Nov: Table 3 = 104 refs, 71 verified + 33 problematic; Table 4 FP 20–53 of 71 (28–75%). Earlier note "26–62 of 84 (31–74%)" was wrong |
| V18 | Neralla et al. 94/100 | VERIFIED: 94 flagged = likely hallucinated (66) + partial; consistent with V3 flagging S < 80 |

## Amendments after freeze (logged 2026-11-13, before any live result was seen)

| # | Date | Decision | Reason | Evidence | Label | Next action |
|---|---|---|---|---|---|---|
| D23 | 2026-11-13 | Genuine set 100 → 30 papers | time before submission; ~1,000 refs still bound FPR to about ±1.4 pts at 5% | estimate from rate limits | VERIFIED (my decision) | report wider CIs in Limitations |
| D24 | 2026-11-13 | ~~Title-search fallback via OpenAlex only; arXiv title search off~~ **withdrawn, see D28** | arXiv's 3.1 s/request limit dominated the run time (est. 2.5–4 h) | `clients.py` intervals | VERIFIED (my decision) | report as a retrieval-coverage limitation |
| D25 | 2026-11-13 | arXiv ID lookups batched (≤100 IDs/request) before the per-citation loop | same answers, ~100× fewer arXiv requests | code change + unit test | INFERRED until test passes | — |
| D26 | 2026-11-13 | ~~OpenAlex search budget 900 → 3000~~ **withdrawn, see D28** | fallback now carries all title searches | — | VERIFIED (my decision) | record searches used |
| D27 | 2026-11-13 | Adjudication 100 → 30 per verifier | my labelling time | — | VERIFIED (my decision) | report as limitation |

| D28 | 2026-11-13 | OpenAlex title search off for every citation (budget 0); arXiv title fallback kept as frozen | env test on laptop: keyless OpenAlex = $0.10/day, one search = $0.001 → ~100 searches/day; a budget that runs out mid-run would treat later citations (the fabricated file) differently | `X-RateLimit-*` headers, 13 Nov | VERIFIED (measured) | report reduced fallback coverage in Limitations |
| D29 | 2026-11-13 | Explicit UTF-8 in every script's file I/O | Windows default cp1252 crashed on CiteTracer JSON (debug #7) | traceback | VERIFIED (executed) | — |
| D30 | 2026-11-13 | Keep n = 30 papers although only 567 refs (19/30 papers had a `.bib`) | time; changing n after seeing counts invites drift | `results/logs/build_genuine_set.log` | VERIFIED (my decision) | report: CI wider; `.bbl`-only papers excluded (possible selection bias); sample window is Jan–Mar 2020 only (first 4×200 listing pages) |
| D31 | 2026-11-13 | Correct Badalova & Mayr figures in the paper (71 genuine, FPR 28–75%) | full text Tables 3–4 | arXiv:2607.22693 v2 HTML | VERIFIED (re-check by me) | also fix review/report wording if reused |
| D32 | 2026-11-13 | Two-phase retrieval (defer arXiv title fallback to phase 2) | arXiv API timing out (debug #10–11); final candidate sets unchanged | logs | VERIFIED (logic) | if arXiv stays down, decide whether to drop the fallback for all citations (would be a real protocol change) |
| D33 | 2026-11-13 | Add exploratory error analysis by retrieval mechanism and identifier presence (`fp_mechanisms.py`) | 84/96 V1E FPs had no matching candidate; needed to interpret FPR | `results/fp_mechanisms.csv`, `fp_by_identifier.csv` | VERIFIED (executed); labelled exploratory, not pre-registered | report as such |
| D34 | 2026-11-13 | Adjudication performed with AI assistance from recorded evidence instead of fully by hand | my time; disclosed in paper and audit | `results/adjudication_evidence.csv`, `scripts/apply_adjudication.py` | VERIFIED (my decision) | spot-check before viva |
| D35 | 2026-11-13 | Report adjusted FPR only where all false positives were adjudicated (V1E, V2, V3) | V1F has 144 unlabelled FPs | `results/fpr_adjudicated.csv` | VERIFIED | — |

The primary metric, thresholds, positive set, seeds and test (exact McNemar) are unchanged.
