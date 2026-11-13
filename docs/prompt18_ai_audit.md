# Prompt 18 — AI-use and research-integrity report

Author: Satyala Murali Karthik (MCL2026010). Sources: `ai_assistance_log.md` (prompt-to-code log
and debugging entries 1–9), `research_decisions.md` (D1–D31, V-queue), `results/logs/`,
`results/env_report*.json`. Nothing below is reconstructed from memory alone.

**Tools.** Claude (Anthropic) in two settings: (1) 22–28 Oct 2026, chat with web search and a Linux
sandbox (Python 3.13.18; registries blocked); (2) 13 Nov 2026, Claude Code running on my Windows 11
laptop (Python 3.12.10), executing commands in my project folder with my approval of the plan.
No other generative tool was used.

## Significant AI-assisted activities

| # | Task | Tool / prompt | AI proposal | Human decision | Verification | Code / result change | Outcome |
|---|---|---|---|---|---|---|---|
| 1 | Gap → experiment | Claude chat, P03–P05 | Three studies; recommended B | Chose G-A / Study B; dropped G-B (D10) | Read Naser 2026 full text | — | Research brief |
| 2 | Comparator choice | P06 | CiteTracer as comparator V4 | Rejected after reading its code (D17) | `test_synthetic_samples.py` l.136–171 | V4 removed | Data use only |
| 3 | Protocol | P07 | Frozen protocol + Mermaid diagram | Accepted; added V1E/V1F split, V3a ablation (D18, D19) | — | `configs/protocol.json` | Frozen 28 Oct |
| 4 | Baseline code | P09 | 9 modules, 8 scripts | Reviewed, accepted | 27 unit tests | `src/`, `scripts/` | Runs end to end |
| 5 | Baseline validation | P10 | Oracle retrieval check | Accepted as scoring check only, never headline (D21) | Executed | `results/oracle*` | 0/1,023 FPR, recalls per rule |
| 6 | Debugging | P11 | Fixes for 6 failures | Accepted each after re-test | Re-runs, new tests | see log 1–6 | — |
| 7 | Time-saving plan | Claude Code, 13 Nov | 30 papers, OpenAlex fallback, batched arXiv, 30 adjudications | Approved in chat | — | D23–D27 | Partly withdrawn (row 9) |
| 8 | Laptop environment | P08 | venv, tests, env test | — | 27→30 tests pass; `ENV TEST: PASS` | `results/env_report.json` | G2 closed |
| 9 | OpenAlex fallback | P11 | (AI's own D24) | Withdrawn (D28) | Rate-limit headers: $0.10/day, $0.001/search | `run_retrieval.py --fast` | arXiv fallback kept |
| 10 | Windows crash | P11 | explicit UTF-8 | Accepted | oracle re-run identical to sandbox | 7 scripts | D29 |
| 11 | Reference check | web fetch, 13 Nov | Metadata of 6 arXiv papers; Neralla repo inspected | **To re-check by me** | arXiv abstract + HTML pages | `paper/refs.bib`, V16–V18 | Badalova & Mayr figure corrected (D31) |
| 12 | Evaluation & figures | P13 | `evaluate.py`, `make_tables.py`, `fp_mechanisms.py`, `adjusted_fpr.py` | Accepted | audit clean; numbers re-derived by hand | `results/` | FPR 16–47%, PPV@1% ≤ 0.057 |
| 12b | Adjudication | Claude Code + web search | Labels for 123 flagged refs from independent evidence | Accepted; **AI-assisted, not hand-labelled** (D34) | evidence per row | `results/adjudication_sample.csv` | adjusted FPR 13.9–15.2% |
| 13 | Manuscript | P15–P16 | LaTeX draft, tables generated from CSV; AI peer review | Accepted by me (13 Nov) | numbers only via scripts; cross-checked | `paper/` | Draft complete; compile on Overleaf |

## Real examples of AI limitations, corrections and verification

1. **Wrong test expectation (debug #3).** The AI expected V3 to "verify" a citation whose authors
   were all wrong; 0.60·100 + 0.25·0 + 0.15·100 = 75 = "partial". The code was right, the AI's test
   was wrong. Caught because the test failed and I did the arithmetic.
2. **Plan contradicted by measurement (debug #8).** The AI proposed moving the title-search
   fallback to OpenAlex to save time. Reading the live `X-RateLimit-*` headers showed the keyless
   budget allows ~100 searches/day. Running out mid-run would have given later citations (the
   fabricated file) less retrieval than earlier ones — an unfair comparison. Withdrawn before the run.
3. **Untested platform assumption (debug #7).** Code written and tested on Linux crashed on Windows
   (`UnicodeDecodeError`, cp1252). The sandbox could not reveal it; only running on my laptop did.
4. **Numbers drifting between documents (debug #9).** "26–62 of 84 genuine flagged (31–74%)" for
   Badalova & Mayr, carried from the 28 Oct notes, did not match their Table 4 (20–53 of 71, 28–75%).
5. **Over-optimistic estimate.** The AI estimated ~1,000 genuine references from 30 papers; the run
   gave 567 because 11 papers ship only `.bbl` (D30).
7. **AI tooling overwrote its own labelled output (debug #13)** and stalled on API limits during
   adjudication (debug #14).
6. **Mislabelled source (28 Oct).** Zhao et al. was first described as "not in my review" until the
   review PDF was read.

## Conclusions that depended on human reasoning

* Choosing the question and rejecting G-B as already answered (D10).
* Rejecting CiteTracer as a comparator after reading its code (D17).
* Treating the oracle run as a code check, not a result (D21).
* Accepting the time-saving amendments, and accepting the withdrawal of D24 once the measured
  budget showed a fairness problem.
* Accepting the AI-assisted adjudication (labels are the AI's from recorded evidence; I accepted them
  and must be able to explain any row).
* The interpretation in the Discussion (to be reviewed by me against `results/`).

## What I learned about vibe coding

* Running code is not validated code: the "and others" bug (debug #2) passed every run and was only
  found by inspecting why genuine citations were flagged.
* AI-written plans should be checked against live measurements (rate limits, counts) before being
  executed, not after.
* Asking the AI to generate tables from CSVs (`make_tables.py`) instead of typing numbers removes a
  whole class of transcription errors.

## Remaining risks

* Registry parsers were validated on live responses only indirectly (the run completes); no
  per-field audit of captured responses yet.
* V2/V3 are re-implementations; V3's fuzzy function is not public.
* Manuscript prose drafted with AI; every claim must be traced to `results/` before submission.
