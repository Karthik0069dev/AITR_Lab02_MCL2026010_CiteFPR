# Viva preparation — CiteFPR (AITR Lab 02, MCL2026010)

Results-specific questions will be added once the live run finishes (§5).

## 1. The project in one minute

* **Problem.** Tools that check whether a citation is real (by looking it up in Crossref, arXiv,
  OpenAlex) are tested almost only on *fake* citations. That measures how many fakes they catch
  (recall), not how often they wrongly accuse a *real* reference (false-positive rate, FPR).
* **Why FPR matters.** Fabricated citations are rare (0.5–5%). When positives are rare, even a
  small FPR means most flags are wrong. PPV (share of flags that are correct) =
  TPR·π / (TPR·π + FPR·(1−π)) — review Eq. 13.
* **What I did.** Took genuine references from arXiv cs.CL papers written *before ChatGPT*
  (so almost certainly not AI-fabricated) and 807 real fabricated citations from ICLR 2026
  desk-rejected papers (CiteTracer data). Looked each citation up once, cached every registry
  response, then scored the *same* cached candidates with five rules:
  * **V1E** existence only, **V1F** full field check (from my review, Eqs. 2–5, 9)
  * **V2** Naser 2026 (title Jaccard + authors + year, flag < 80)
  * **V3** Neralla et al. 2026 (title + authors + journal, flag < 80)
  * **V3a** V3 + author veto (my ablation)
* **Outputs.** FPR with confidence intervals, recall, PPV at π = 0.5/1/2/5%, McNemar tests,
  threshold sweep, and a breakdown of *why* genuine references were flagged.
* **Pathway.** B (controlled comparative study) with C (one isolated modification, V3a) as
  ablation.

## 2. Pipeline (what each file does)

```
arXiv listing ─► build_genuine_set.py ─► data/genuine_refs.jsonl  (cited .bib entries only)
CiteTracer    ─► load_positives.py    ─► data/fabricated_refs.jsonl (807)
both          ─► run_retrieval.py     ─► data/cache.sqlite + data/candidates.jsonl
                 (Crossref query → DOI lookups → batched arXiv IDs → arXiv title fallback)
candidates    ─► score.py             ─► results/scores.csv (flag/score/label × 5 verifiers)
scores        ─► evaluate.py          ─► metrics, PPV, McNemar, τ sweep, FP breakdowns, figures
```

Key modules: `normalize.py` (lower-casing, LaTeX/diacritic stripping, Levenshtein, surnames,
DOI/arXiv normalisation), `scorers.py` (the five rules), `metrics.py` (Wilson CI, Eq. 13,
bootstrap, exact McNemar), `cache.py` (SQLite cache with a frozen mode).

## 3. Timeline of decisions you must be able to justify

| When | What | Why |
|---|---|---|
| 28 Oct | Protocol frozen (`configs/protocol.json`) | thresholds from the source papers, fixed before results |
| 28 Oct | Oracle validation on 2,450 synthetic citations | tests scoring alone with perfect retrieval |
| 28 Oct | Dropped CiteTracer as a comparator (D17) | its rule-based mode still needs AWS Bedrock |
| 13 Nov | 30 papers instead of 100 (D23) | time; logged before results |
| 13 Nov | Batched arXiv ID lookups (D25) | 4 requests instead of 367; same answers (unit test) |
| 13 Nov | OpenAlex title search off for all (D28) | measured keyless budget ≈ 100 searches/day; uneven use would bias against later rows |
| 13 Nov | UTF-8 fix (D29) | Windows cp1252 crash |
| 13 Nov | Corrected Badalova & Mayr numbers (D31) | full-text Table 4 differed from my earlier note |

## 4. Likely questions and answers

**Q1. What is your research question, in one sentence?**
How often do registry-based citation verifiers flag genuine references, what does that imply
for the precision of their flags at realistic fabrication rates, and why do the false flags occur?

**Q2. Why is this not just "I ran some tools"? Where is the contribution?**
I do not claim a new detector. The contribution is a *measurement under control*: all rules
see identical registry responses (frozen cache), so differences are due to scoring rules alone;
FPR is measured on a natural, pre-LLM genuine set rather than synthetic "clean" references; and
I translate FPR into PPV at realistic prevalence and explain the false positives.

**Q3. Why pre-ChatGPT papers?**
Papers submitted before 30 Nov 2022 could not contain ChatGPT-fabricated references, so a flag
on them is a false positive of the verifier — apart from ordinary human citation errors, which I
handle by hand adjudication (genuine / genuine_erroneous / unresolvable).

**Q4. Why only cited .bib entries, not the whole .bib file?**
Authors often keep large shared .bib files; uncited entries never appear in the paper and may be
sloppier. Keeping only keys used in `\cite{}` matches what a reader actually sees.

**Q5. Your synthetic validation showed 0% FPR for every verifier. Why not report that?**
Because the oracle run gives each citation its *true* record as the only candidate — perfect
retrieval and clean seed metadata. It validates the scoring code, but it cannot reveal false
positives caused by retrieval misses or messy real metadata. That is exactly why the main
experiment uses natural reference lists (D21).

**Q6. What is the frozen cache and why does it matter?**
Every registry response is stored in SQLite. Retrieval runs once; scoring reads only the cached
candidates. Registries change over time and rate-limit, so without the cache two verifiers run
at different times could see different data. It also makes the scoring step fully reproducible
offline.

**Q7. Why Wilson intervals and a cluster bootstrap?**
Wilson behaves well for rates near 0 (the normal approximation gives negative bounds). References
from one paper are correlated (same author habits, same .bib style), so I also resample whole
papers; that interval is wider and more honest.

**Q8. Why McNemar and not a chi-square on two proportions?**
The verifiers are evaluated on the *same* references, so the samples are paired. McNemar uses only
discordant pairs (flagged by one, not the other). I use the exact binomial version and require
both p < 0.05 and a gap ≥ 2 points, so tiny but "significant" differences do not count.

**Q9. Explain PPV with a number.**
If a verifier has recall 80% and FPR 5%, at π = 1%: PPV = 0.8·0.01 / (0.8·0.01 + 0.05·0.99)
= 0.008 / 0.0575 ≈ 0.14. Only 14% of its flags would be real fabrications.

**Q10. What does V3a test and what did you expect?**
V3 lets a perfect title and journal outweigh wrong authors (0.60·100 + 0.15·100 = 75 even with
0 author score; one wrong author in four still verifies). V3a vetoes when author similarity < 50.
On synthetic data it changed nothing because each mutation touches one field; only natural
fabrications can show an effect — and the veto may also raise FPR on genuine refs with messy
author lists. It is a single isolated change, so the comparison is a clean ablation.

**Q11. Why did you reduce from 100 to 30 papers? Isn't that changing the protocol?**
Yes, and it is logged (D23) with the reason (time), *before* any result was seen. The primary
metric, thresholds, seeds and test are unchanged. The cost is wider confidence intervals, which I
report. Changing a protocol is legitimate; changing it silently or after seeing results is not.

**Q12. Only 567 genuine references from 19 papers — why not 30?**
11 papers shipped only a compiled .bbl, no .bib; the frozen rule uses .bib entries. This is a
possible selection bias (authors who share .bib may be tidier) and is reported (D30).

**Q13. What are the main threats to validity?**
(1) Retrieval failure looks like fabrication — I report how many genuine refs got zero candidates.
(2) Human errors in genuine bibliographies — hand adjudication. (3) One field (cs.CL), one
quarter (Jan–Mar 2020), three registries — external validity. (4) Positives were partly found
with registry tools, so recall may be optimistic. (5) V2/V3 are re-implemented from text; V3's
fuzzy function is not public (checked their repo).

**Q14. Is there data leakage?**
There is no training, so no train/test leakage. The risk is overlap between sets; genuine papers
are 2020 arXiv and positives are 2026 ICLR, and `evaluate.py` audits duplicate IDs and ID-prefix
overlap. Thresholds come from the papers; the τ sweep is reported as sensitivity only, never used
to pick a threshold.

**Q15. Show me an example where the AI was wrong.**
(a) It wrote a unit test expecting V3 to "verify" a citation with all-wrong authors; the
arithmetic gives 75 = partial — the test was wrong, not the code (debug #3). (b) Its time-saving
plan routed title searches through OpenAlex; the live rate-limit headers showed ~100 searches/day
without a key, which would have biased the comparison — withdrawn (debug #8, D28). (c) A
Badalova & Mayr figure carried from earlier notes didn't match their Table 4 (debug #9, D31).

**Q16. How do I reproduce your main result?**
`pip install -r requirements.txt`, `pytest`, `env_test.py`, then the commands in the README in
order. With the frozen cache, `score.py` + `evaluate.py` reproduce every table offline in under a
minute; without it, retrieval takes ~45 min because of arXiv's 1 request / 3 s rule.

**Q17. Why no GPU / no LLM?**
The research question is about deterministic registry-matching rules. LLM-based checkers
(CiteTracer's judges) need paid cloud APIs and are non-deterministic, which would break the
controlled comparison.

**Q18. What would you do with more time?**
(1) Full 100-paper sample and other fields (biomedicine, physics). (2) Add an OpenAlex key so the
title fallback covers all citations, and measure how much FPR falls. (3) Calibrate thresholds on a
held-out set and test on a separate one.

**Q19. What does "VERIFIED / INFERRED / UNKNOWN" mean in your logs?**
VERIFIED = checked in the original source or by running code; INFERRED = plausible but not yet
tested; UNKNOWN = no evidence. It stops AI-produced plausible statements from being treated as facts.

**Q20. Explain Levenshtein similarity.**
Edit distance = minimum insertions, deletions, substitutions to turn one string into another.
Similarity = 1 − distance / max(len). Titles are normalised first (case, LaTeX, accents,
punctuation), so "BERT: Pre-training…" and "{BERT}: pre-training…" score 1.0.

## 5. Results questions (numbers from `results/`, 13 Nov 2026, before adjudication)

**Headline.** FPR on 567 genuine refs: V1E 16.9%, V1F 47.1%, V2 16.0%, V3 17.3%, V3a 17.3%.
Recall on 807 fabrications: 95.7–99.9%. PPV at π = 1%: 0.055–0.057 (V1F 0.021).

**Q21. What is your main finding in one sentence?**
The verifiers catch nearly every fabricated citation but also flag about one in six genuine
references, so at a realistic 1% fabrication rate only ~6% of their flags are correct — and most
false flags happen because the real paper was never retrieved, not because of the scoring rule.

**Q22. Your recall is 99%. Isn't that great?**
It is on an easy, selected set: the ICLR positives were found by tools like these, and many
resemble no real paper at all. The point of the study is that recall alone hides the FPR.

**Q23. Which verifier is best?**
None is meaningfully better among V1E, V2, V3: the largest gap is 1.2 points (V2 vs V3, McNemar
p = 0.039) and my frozen rule needs ≥ 2 points, so I call it no difference. V1F is clearly worse on
FPR (+30 points, 169–176 one-directional discordant pairs).

**Q24. Why is V1F so bad?**
It requires exact year, venue and pages. 170 of its 267 false positives found the *right* paper
but a field differed — typically the citation names the conference while the matched record is
the arXiv preprint (arXiv-ID references: 63.6% V1F FPR).

**Q25. How do you know the false positives are retrieval failures?**
`fp_mechanisms.py` checks each flagged reference's candidate list: for 84 of 96 V1E false
positives no candidate had title similarity ≥ 0.8. References with a DOI were never flagged
(0/58); with neither DOI nor arXiv ID, ~22% were. This analysis was not pre-registered — I call it
exploratory.

**Q26. Give a concrete example.**
(a) Kingma & Welling "Auto-Encoding Variational Bayes": Crossref returned a 2024 paper with the
*same title* by other authors; since a candidate already had title ≥ 0.8, the arXiv fallback was
skipped and the original paper never appeared. (b) "AIFdb: Infrastructure for the Argument Web":
the Crossref record stores "Lawrence John" in the family-name field, so surname matching fails on
the right record. I read the raw cached JSON to confirm it.

**Q27. Did the ablation (V3a) do anything?**
No — identical flags on all 1,374 citations (McNemar V3 vs V3a: 0 discordant pairs). So no citation
that V3 verified had author similarity below 50. A negative result, reported as such; it suggests
the "wrong authors, right title" case is rare in both sets.

**Q28. Would changing the threshold fix it?**
No. At threshold 60 instead of 80/85, FPR is still 13–15% while recall falls to 87–90%. The false
positives score far below the threshold because the right record is missing.

**Q29. Which hypotheses held?**
H1 (V1F > V1E FPR) supported. H2 (no verifier useful at 1%) supported. H3 (misc/book/thesis/
arXiv-cited highest) not supported as stated: arXiv-cited refs are *lowest*; small entry-type
strata (< 30) can't be tested under my rule.

**Q30. Why are your CIs two kinds?**
Wilson treats the 567 references as independent; the paper-cluster bootstrap resamples the 19
papers, because one paper's references share habits. Cluster CI for V1E is 12.2–21.7% vs Wilson
14.1–20.2%. Per-paper V1E FPR ranges from 0% to 35%.

**Q31. Is 17% the "true" FPR? How did you adjudicate?**
Every V1E/V2/V3 false positive was checked against independent sources not used by the verifiers
(OpenAlex search, Semantic Scholar; web search of the primary source for 33). 109 of 123 were correct
references, 3 had real .bib errors, 11 were non-scholarly (repos, web pages). Adjusted FPR: V1E 14.8%,
V2 13.9%, V3 15.2%; ~85% of flags hit correct references. Be open: the labelling was **AI-assisted
from recorded evidence and accepted by me**, not done fully by hand (D34) — know 2–3 rows by heart,
e.g. CSTR VCTK (names swapped: 'Christophe, Veaux', 'Yarnagishi') and the GPT-1 title mismatch.
It is still pipeline-specific: with an OpenAlex key fewer real papers would be missed.

**Q32b. The paper's numbers all come from scripts — how do you know the prose matches?**
`scripts/check_paper_numbers.py` re-derives every headline claim (FPR range, recall, PPV, mechanism
shares, adjudication counts, adjusted FPR, τ=60 values) from `results/*.csv` and fails if the text
disagrees; 30/30 pass. `scripts/check_tex.py` checks the LaTeX structure. One real catch: the V2 FPR
printed as 16.1% in a table and 16.0% in a figure — double rounding of 91/567 = 16.049%. Fixed to
compute from the counts.

**Q32. What went wrong during the run?**
arXiv throttled (429) and timed out; the client crashed and — worse — would have cached transient
errors as "no result" (debug #10). Fixed so failures are retried, not cached; retrieval split into
two phases with identical final candidates (debug #11). Evaluation split paper IDs on the wrong
colon (debug #12) — fixed before writing the paper.
