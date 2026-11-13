# Baseline validation report (Prompt 10, gate G2) — 28 Oct 2026

**Scope.** The baselines here are deterministic scoring rules re-implemented from published
descriptions; no published numbers exist for these rules on these data, so validation means
(a) unit tests against hand-computable values, (b) an offline run on CiteTracer's 2,450
synthetic citations with each citation's own seed record as the only candidate ("oracle
retrieval"), and (c) an end-to-end pipeline run. Live retrieval has **not** been run yet.

## Measured offline results (executed in sandbox, Python 3.13.18)

Unit tests: **27 passed** (`python -m pytest -q`), including a source-archive reader test built
from an in-memory tarball (the network path itself is untested).

Oracle retrieval, CiteTracer synthetic v2 (`results/oracle/`, `results/oracle_pipeline/`):

| Group | n | V1E | V1F | V2 | V3 | V3a |
|---|---|---|---|---|---|---|
| Real R1–R3 flagged (FPR) | 1,023 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Potential P1, P3 flagged | 271 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Hallucinated H1–H6 flagged (recall) | 1,156 | 18.8% | 80.0% | 13.3% | 17.0% | 17.0% |

95% Wilson CI for 0/1,023 is [0, 0.37%]. Per-subtype rates: `results/oracle/summary_by_subtype.csv`
and `results/oracle/figures/oracle_detection_by_subtype.png`.

## VERIFIED

* Eq. 3 similarity, normalisation, surname handling, identifier normalisation (unit tests).
* PPV function reproduces the review's worked example: 0.246 (`test_ppv_matches_review_example`).
* Wilson interval matches known values (0/10 → [0, 0.2775]; 5/10 → [0.2366, 0.7634]); exact McNemar p = 2/1024 for 10 one-sided discordant pairs; cluster bootstrap brackets the point estimate.
* Cache: write, read, frozen mode refuses new writes and raises on misses.
* V1 labels follow Eq. 9 on constructed cases (PH, PAC, IH, TF, valid).
* Every scorer passes an identical citation and flags a citation with no candidates.
* Pipeline (`score.py` → `evaluate.py`) runs end to end on 2,179 citations; audit passed
  (no duplicate IDs, labels and flags valid).
* Properties of the published rules, confirmed by code and data:
  * V2: a year-only error scores exactly 80 = "confirmed", so 0% of H4 is caught; raising the
    flag threshold from 80 to 81 lifts V2 recall from 13.3% to 45.1% on the synthetic set.
  * V3: a venue-only error scores 85 = "verified" (0% of H3 caught); one wrong author in four
    still verifies.
  * V3a = V3 on the synthetic set: the author veto changes no flag outcome, because the synthetic
    mutations touch one field at a time. Its effect can only show on natural fabrications.

## UNCERTAIN

* Registry parsers are tested on **hand-written** fixtures built from the documented response
  formats, not captured responses. Replace with real responses after the pilot.
* V3 "fuzzy" title/journal similarity is implemented as normalised Levenshtein ×100; Neralla et
  al.'s exact function is not stated in the paper — check their repository.
* V2 treats a missing cited year as a mismatch (Naser does not say).
* Venue similarity (V1F) is lenient (token containment / acronym); threshold 0.5 is my choice.
* Identifier check without a DOI lookup: when the matched record has no DOI, a cited DOI cannot
  be refuted (46 of 200 H5 cases in the oracle run). Live retrieval adds the lookup (`doi_found`).

## NEEDS CORRECTION / NOT COVERED

* V1F ignores publisher and location: 67 + 32 of 166 H6 cases are missed for that reason.
  This matches review Eq. 4 (fields A, T, V, Y, P) and is reported as a scope limit, not fixed.
* CiteTracer cannot serve as keyless comparator V4: its `--rule-based-*` flags only take effect
  when AWS Bedrock is configured, and the other agents still call the LLM
  (`scripts/test_synthetic_samples.py`, lines 136–171). V4 dropped (D17).
* CiteTracer's structured ICLR file contains 807 citations, not the 957 reported (V12).

## Additional checks required before G3

1. `env_test.py` on the laptop → PASS for Crossref, arXiv, OpenAlex.
2. Pilot: 10 papers' genuine refs + 200 fabricated through retrieval; inspect 20 random
   candidate lists by eye; replace parser fixtures with captured responses.
3. Confirm the pilot FPR is not driven by retrieval failure (count citations with 0 candidates).
4. Freeze `data/cache.sqlite` (copy + checksum) before the full scoring run.

Conclusion: the scoring stage behaves as specified and the pipeline is runnable; the synthetic
"Real" class is too clean to estimate false positives (0/1,023 for every rule), which supports
the decision to measure FPR on natural reference lists.
