# ai_assistance_log.md

Tool: Claude (Anthropic), web search, and a Linux sandbox (Python 3.13.18) in which code was
written and run. Sandbox network: GitHub reachable; Crossref, arXiv, OpenAlex and PyPI blocked.
Human decisions: all steps reviewed and accepted by me on 28 Oct 2026.

## Prompt-to-code log

| Step | Prompt | AI proposal / action | Verification | Human decision |
|---|---|---|---|---|
| 7 | 05 | Research brief, RQ1–RQ3, hypotheses, decision rules | read against Phase I | Accepted (28 Oct) |
| 8 | 06 | Dataset + comparator sheet | CiteTracer repo cloned and inspected | Accepted (28 Oct) |
| 9 | 07 | Frozen protocol `configs/protocol.json`, Mermaid diagram | — | Accepted (28 Oct) |
| 10 | 08 | `env_test.py`; repo structure | executed in sandbox: FAIL on network (expected) | run on laptop |
| 11 | 09 | normalize, records, bibparse, cache, clients, retrieve, scorers, metrics, plots, scripts | 27 unit tests pass | Code reviewed and accepted (28 Oct) |
| 12 | 10 | Oracle validation + end-to-end pipeline run | executed; numbers in baseline_validation.md | Accepted (28 Oct) |
| 13 | 11 | Debugging of the failures below | each fix re-tested | Accepted (28 Oct) |

## Debugging log (real failures, in order)

1. **PyPI unreachable.** `pip install rapidfuzz` failed with `NameResolutionError` for pypi.org.
   Cause: sandbox egress policy. Fix: wrote Levenshtein (Eq. 3) and a BibTeX parser in plain
   Python (D20). Verification: `test_levenshtein_known_values`, `test_parse_bib_and_cited_keys`.
   Earlier results affected: none (fix before first run).
2. **"and others" not treated as et al.** First oracle run: V1F flagged 59/343 (17.2%) of
   CiteTracer's genuine R3 citations; all 59 failed the author check. Inspection showed author
   lists ending in "and others", which `is_etal()` did not match, so the author-count test
   failed. Fix: regex `^(and\s+)?(others|et\s*\.?\s*al\.?)$`. Verification: R3 flag rate 0.0%
   on rerun; new unit test. Earlier results affected: the first oracle table (rerun).
3. **Wrong expectation in my own test.** `test_v3_missing_author_substitution_and_veto` expected
   a citation with entirely wrong authors to be "verified" under V3; the code correctly returned
   75 = "partial". The test was wrong, not the code (0.60·100 + 0.25·0 + 0.15·100 = 75). Fixed the
   test and added a one-wrong-author case (93.75 = verified).
4. **Loader crash.** `load_positives.py` called the record constructor to parse a year and hit
   `missing 1 required positional argument: 'id'`. Fix: `parse_year()` helper. Verification:
   807 citations loaded, 6 without a parsed title.
5. **Not a bug, but a scope finding.** 99 of 166 H6 cases unflagged by V1F: all changed
   publisher (67) or location (32), fields outside review Eq. 4. Left as specified; reported.
6. **Not a bug: missing resolver offline.** 46 of 200 H5 (fabricated DOI) unflagged; in every
   one the seed has no DOI, so nothing can refute the cited DOI without a lookup. Added a
   `doi_found` argument that live retrieval fills.

## Laptop session, 13 Nov 2026 (Windows 11, Python 3.12.10, Claude Code on my laptop)

| Step | Prompt | AI proposal / action | Verification | Human decision |
|---|---|---|---|---|
| 14 | 08 | venv + `pip install -r requirements.txt pytest`; env test | 27 passed; `ENV TEST: PASS` (Crossref, arXiv, OpenAlex, GitHub 200) | Accepted |
| 15 | 07 | Fast-plan amendments D23–D27 to save time | logged before any live result | Approved by me in chat ("go with the fast plan") |
| 16 | 09 | `prefetch_arxiv` (batched arXiv IDs) + `--fast` flag; 3 new unit tests | 30 passed | Accepted |
| 17 | 10 | Oracle re-run on laptop vs 28 Oct sandbox outputs | `summary_by_subtype.csv` identical | — |

7. **Windows encoding crash.** `oracle_validation.py` and `load_positives.py` raised
   `UnicodeDecodeError: 'charmap' codec can't decode byte 0x81` — `read_text()` without an
   encoding uses cp1252 on Windows; the sandbox (Linux, UTF-8) never showed it. Fix: explicit
   `encoding="utf-8"` in every script's file I/O (D29). Verification: oracle re-run identical to the
   sandbox output; 807 positives loaded. Earlier results affected: none.
8. **AI plan contradicted by measurement.** The AI's fast plan (D24) moved the title-search
   fallback to OpenAlex. The laptop env test then showed the keyless OpenAlex budget is
   $0.10/day with one search costing $0.001 (~100 searches/day). The plan would have run out of
   budget part-way and treated later citations (the fabricated file) differently from earlier ones.
   Fix: D24/D26 withdrawn; OpenAlex search off for all citations, arXiv title fallback kept (D28).

9. **Wrong secondary figure carried from Phase I.** Checking Badalova & Mayr's full text (Tables 3–4)
   for the paper showed 71 genuine references and 20–53 false positives (28–75%), not the
   "26–62 of 84 (31–74%)" recorded on 28 Oct. Fix: paper and V17 corrected (D31). Lesson: numbers
   copied between AI-assisted documents need re-checking against the table itself.

10. **Run crashed on arXiv throttling; transient errors could be cached.** At citation 250 the run
    died with `requests.exceptions.ReadTimeout` (export.arxiv.org, 30 s, after 4 retries); a probe
    showed arXiv answering `429` after 31 s, and 200 again two minutes later. Reading `_Http` showed a
    second, silent flaw: a final 429/5xx was **cached** as a permanent empty answer, which would have
    made that citation look unfindable (a false flag). Fix: persistent network errors and transient
    statuses return no answer, are counted and are not cached; the script lists incomplete
    citations and exits 2; a wrapper re-runs until every request has a definitive answer
    (2 new unit tests, 32 pass). Cache audit before the fix: one non-200 entry, a genuine Crossref
    404, so no earlier response was contaminated. Crash log kept as
    `results/logs/run_retrieval_attempt1_crash.log`.

11. **arXiv API degraded (not a code bug).** After the restart, progress fell to ~10 s/citation:
    only 1 arXiv response cached in 10 min while Crossref returned 68; probes to export.arxiv.org
    timed out at 40 s in 2 of 3 tries. Each arXiv title search then spent minutes in retries.
    Change: retrieval split into two phases with **identical final candidates**: phase 1
    (`--defer-arxiv-title`) runs Crossref + DOI lookups for all citations and lists those still
    lacking a candidate with title similarity >= 0.8; phase 2 (normal run) adds the arXiv title
    search for exactly those, reusing the cache. Phase-1 output is never scored. arXiv timeout made
    configurable (`--arxiv-timeout`). Logs: `run_retrieval_attempt2_stopped.log`,
    `run_retrieval_phase1.log`.

12. **Wrong cluster IDs in the paper-level bootstrap.** First evaluation printed per-paper groups
    such as `2003.04970:Reed` and `2003.04970:Miller`: `evaluate.py` took the paper ID with
    `ref_id.rsplit(":", 1)`, but BibTeX keys contain colons (`DBLP:conf/...`, `maas-EtAl:2011`),
    so one paper became dozens of "clusters" and the cluster CI was too narrow. Fix: `paper_id()`
    splits on the first colon (19 papers, as expected); unit test added (33 pass). Point estimates
    unchanged; cluster CIs widened slightly (V1E 12.2–21.7%). Pre-fix file kept as
    `results/logs/metrics_before_debug12.csv`. The 28 Oct oracle run was unaffected (single prefix).

Laptop session, results stage (13 Nov):

| Step | Prompt | AI action | Verification | Human decision |
|---|---|---|---|---|
| 18 | 13 | Froze cache + candidates (SHA-256 in `results/frozen_checksums.txt`); score + evaluate | audit clean; 0 citations without candidates | Accepted by me (13 Nov) |
| 19 | 13/14 | `fp_mechanisms.py` error analysis; inspected raw cache for two cases | raw Crossref JSON read | Accepted by me (13 Nov) |
| 20 | 15 | Results/Discussion/Limitations/Abstract drafted; every number from `make_tables.py` or results CSVs, cross-checked by hand | numbers re-derived once (per-paper range corrected 39→35% after debug #12) | Accepted by me (13 Nov) |
| 21 | 13 | **Adjudication done by the AI at my request** (I was short of time): independent evidence from OpenAlex search + Semantic Scholar (`adjudication_evidence.py`), rule for 90 rows, web checks of the primary source for 33 (`apply_adjudication.py` lists each with its evidence) | every label traceable to `results/adjudication_evidence.csv` or a named source | Accepted by me (13 Nov); disclosed in the paper as AI-assisted |
| 22 | 16 | Peer review of the draft; quick text fixes applied | — | Accepted by me (13 Nov) |
| 23 | 16 | **Second review pass on the compiled PDF**: 9 defects (p1-p9 in the review) fixed - p-value formatting, figure legends, hypotheses, pipeline figure, bib capitalisation and arXiv IDs, registry citations, 3 new tables, V2 rounding | `check_paper_numbers.py` 30/30, `check_tex.py` clean, 33 tests | Accepted by me (13 Nov) |

13. **Evaluation overwrote the labelled adjudication sheet.** `evaluate.py --adjudication` read the
    labels and then rewrote `adjudication_sample.csv` with empty labels (it always regenerated the
    sample). Metrics were computed from the labels, but the file lost them. Fix: the sheet is never
    rewritten when `--adjudication` is given or labels exist; labels restored with
    `apply_adjudication.py`; re-run gave identical metrics (`results/logs/metrics_adjudicated_run1.csv`).
14. **Evidence collection stalled on rate limits.** DBLP served a bot-check page (not bypassed);
    Semantic Scholar answered 429 to keyless requests; OpenAlex's daily keyless budget ran out after
    99 searches and the client slept on `Retry-After` (no write for 33 min). Fix: OpenAlex budget 0
    on the re-run (cached answers reused), single-try Semantic Scholar, web search for the 14 rows
    without any record. Log: `results/logs/adjudication_evidence_run1_stalled.log`.

15. **Defects only the compiled PDF revealed.** Reviewing the first Overleaf build (Prompt 16,
    second pass) found nine presentation faults invisible in the source: McNemar p-values printed as
    `0.0e+00`; figure legends using internal names ("V3 AtomGPT") instead of the paper's; H1-H3
    discussed but never stated; no pipeline figure; references with no arXiv IDs and titles
    lower-cased by IEEEtran ("aI Tools"); registries cited by name only; error analysis and
    adjudication left as prose; and the V2 FPR shown as 16.1% in a table but 16.0% in a figure
    (double rounding of 91/567 = 16.049%). All fixed; the rounding one was a genuine inconsistency,
    the rest presentation. Lesson: a manuscript is not checked until it is read as a PDF.
16. **Guarding against it happening again.** Added `scripts/check_paper_numbers.py`, which
    re-derives every headline claim from `results/*.csv` and fails if the prose disagrees (30/30), and
    `scripts/check_tex.py`, which checks environments, braces, cross-references, citation keys and
    \input/graphics paths without a TeX engine (installing one was not permitted on this machine).

17. **Second compiled-PDF pass.** The rebuilt PDF was correct but the body ran about five pages
    excluding references, under the 6--10 page target, and the two items the assignment names as
    required evidence -- the baseline validation (gate G2) and reproducibility -- were three lines in
    the setup section. Added §IV-B (oracle table, properties of the published rules it exposes) and
    §IV-C (frozen checksums, the two offline commands, seeds), both from files already in `results/`;
    no claim was invented to fill space. Also corrected the amendment range D23--D32 to D23--D35.
    Seven new assertions were added to `check_paper_numbers.py` (38/38).

18. **A measured result left out of the paper.** While re-reading the third compiled PDF I checked
    `scores.csv` for citations with no candidates: there are none, in either set, and the median genuine
    reference drew 5 candidates (the Crossref row limit). This matters -- it separates "the pipeline
    returned nothing" from "the pipeline returned the wrong things" and so supports the paper's main
    claim -- yet it had sat unreported in the data since the run. Added as §VI Threats to validity with
    two new assertions in `check_paper_numbers.py` (40/40). Also found the manuscript had lost its only
    pointer to the code when the Environment paragraph was rewritten; a Code and data availability
    statement now carries a placeholder for the GitHub URL.

## AI limitations seen so far (for Prompt 18)

* The AI's first test expectation for V3 was arithmetically wrong (item 3).
* The AI initially mislabelled Zhao et al. as "not in my review" until the review PDF was read.
* The AI's time-saving retrieval plan (D24) assumed an OpenAlex search budget that did not exist
  without a key; caught by reading the rate-limit headers (item 8).
* The AI estimated ~1,000 genuine references from 30 papers; the run gave 567 because 11 of 30
  papers ship only a `.bbl` (D30).
* The original HTTP client (AI-written, 28 Oct) cached a final 429/5xx as a real answer and
  crashed on persistent timeouts; never exercised in the sandbox because the registries were
  blocked there (item 10).
* The AI-written evaluation split IDs on the last colon, which BibTeX keys break (item 12).
* Registry parsers were written from documented formats without live responses; they remain
  UNCERTAIN until the pilot.
