# Prompt 12 — Contribution pathway and comparison plan

Written 13 Nov 2026, **before** any live result was seen (retrieval still running).
Baseline status: scoring stage validated offline (`baseline_validation.md`; 30 unit tests;
oracle run reproduced identically on the laptop on 13 Nov).

## Three pathways compared

| | A. Reproduction under a new condition | B. Controlled comparative study | C. Targeted modification |
|---|---|---|---|
| Scientific question | Does CiteTracer's reported accuracy hold on natural genuine bibliographies? | What FPR / PPV do published registry-matching rules have on genuine pre-LLM reference lists, and why do they flag them? | Does one change to a published rule (author veto in V3) reduce misses without raising FPR? |
| Code changes | Run CiteTracer end-to-end | None to the scorers; one frozen retrieval cache shared by all | One isolated rule in `scorers.py` (V3a) |
| Compute | Paid cloud LLM (AWS Bedrock) — not available (D17) | CPU + free registries, ~1 h on the laptop | Negligible on top of B |
| Advantages | Directly tests a headline number | Answers the review's gap (§5.1–5.2, Eq. 13); all comparators runnable | Clean causal contrast |
| Failure risks | Blocked by API cost; non-deterministic LLM stages | Registry coverage gaps look like fabrication; genuine lists contain human errors | Synthetic set showed no effect (V3a = V3), may also show none on natural data |
| Evidence needed | Bedrock access | FPR with CIs, McNemar, PPV curve, FP breakdown, adjudication | V3 vs V3a paired on the same citations |

## Decision

**Pathway B, with C as an embedded ablation (V3 vs V3a).** A is infeasible without paid APIs.
B is the most defensible for the resources and directly answers RQ1–RQ3. The contribution is
*measurement* (scale, prevalence-aware PPV, causes of false positives), not a new detector
(D9) — a routine comparison is not claimed as novel.

## Fair test plan (unchanged from the frozen protocol except D23–D30)

1. One retrieval pass for every citation, genuine and fabricated, through the same code path
   (`run_retrieval.py --fast`); OpenAlex title search off for all (D28).
2. Freeze `data/cache.sqlite` and `data/candidates.jsonl` (SHA-256 recorded) before scoring.
3. Score all five verifiers on the identical candidate lists (`score.py`).
4. Primary: FPR on genuine refs with Wilson 95% CI and paper-level cluster bootstrap.
   Pairwise exact McNemar; a difference counts only if p < 0.05 **and** |gap| ≥ 2 points.
5. Secondary: recall on 807 ICLR fabrications; PPV at π ∈ {0.5, 1, 2, 5}% (Eq. 13 + bootstrap).
6. Deep analyses: τ sweep 50–95 (sensitivity); FP by entry type and failed field (error
   analysis); V3 vs V3a (ablation); count of genuine refs with zero candidates (retrieval-failure
   check, threat to internal validity).
7. Hand adjudication of 30 flagged genuine refs per verifier (D27) into genuine /
   genuine_erroneous / unresolvable — reported separately, never used to tune thresholds.

No gain is promised: H2 predicts that no verifier is useful (PPV ≥ 0.5) at π = 1%, which would
be a negative but informative result.
