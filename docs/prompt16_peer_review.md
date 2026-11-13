# Prompt 16 — Critical technical review of the draft (paper/main.tex, 13 Nov 2026)

Reviewer: Claude (AI), asked to review critically. The author must read, accept or reject each
point; responses below are proposals until the author fills the last column.

## MAJOR concerns

| # | Location | Concern | Why it matters | Proposed remedy |
|---|---|---|---|---|
| M1 | §Results RQ1, Abstract | FPR reported before hand adjudication. Some flagged pre-2022 references may be genuinely wrong. | The headline number may overstate verifier error. | Complete the 123-row adjudication; report adjusted FPR (`evaluate.py --adjudication`). Keep the abstract wording "before adjudication" until then. |
| M2 | §Results RQ3, Discussion | 86–89% of FPs are retrieval misses, so the study partly measures *this retrieval pipeline* (5 Crossref rows, no OpenAlex search) rather than the published verifiers as deployed. | Generalising "verifiers have 17% FPR" would be an unsupported claim. | Discussion already says so; tighten the Abstract/Conclusion to "with this registry pipeline". Follow-up 1 (OpenAlex key) directly tests it. |
| M3 | §Setup | 19 papers, one quarter, one field; `.bbl`-only papers excluded. | External validity; possible selection bias. | Stated in Limitations; add per-paper spread (0–35%) to Results (done). |
| M4 | §Discussion "Identifiers" | The identifier analysis was not pre-registered. | Post-hoc strata can mislead. | Labelled exploratory (done). Do not put it in the Conclusion as a confirmed effect — current Conclusion says "almost never misjudged": soften to "were not flagged in this sample (0/58)". |
| M5 | §Results Recall | Recall 95.7–99.9% on positives found by similar tools is optimistic. | Readers may read it as detector quality. | Discussion paragraph "Why recall is high" (done); add to Limitations (done). |

## MINOR concerns

| # | Location | Concern | Remedy |
|---|---|---|---|
| m1 | Table 1 | Recall rows share a table with FPR rows using `\multicolumn`; may be hard to read. | Kept as one table; Fig. 1 (FPR with CIs) now carries the FPR comparison visually. |
| m2 | Fig. 1 | `fpr_by_verifier.pdf` is generated but not used. | Used in RQ1. |
| m3 | Related Work | Badalova & Mayr numbers corrected (71 genuine, 28–75%); check Table 4 once more yourself. | Re-check. |
| m4 | §Method V3 | Flag rule S < 80 includes "partial"; state that Neralla et al. also count partial as flagged (94/100). | One sentence (done in Related Work). |
| m5 | refs.bib | Metadata fetched by AI from arXiv pages. | Author to re-check each entry. |
| m6 | §Experimental Setup | Retrieval phasing (D32) not mentioned in the paper. | Add one sentence: "retrieval ran in two phases with identical final candidates because the arXiv API timed out". |
| m7 | Length | Check 6–10 page target after compiling on Overleaf. | Compile; trim Related Work if over. |

## Unsupported or risky claims found

* "references with a DOI are almost never misjudged" (Conclusion) — based on 58 refs, exploratory → soften (M4).
* "Both failures would affect any verifier using the same registries" (Discussion) — plausible but
  INFERRED; rephrase as "would affect any verifier that relies on the same records".

## Prioritised revision checklist

1. [x] Adjudicate 123 rows; re-run evaluate with `--adjudication`; insert counts (M1).
2. [x] Soften Conclusion identifier sentence (M4) and the "any verifier" sentence.
3. [x] Add retrieval-phasing sentence to Setup (m6).
4. [ ] Compile on Overleaf; fix layout; check page count (m7). Structure pre-checked with
   `scripts/check_tex.py` (environments, braces, refs, cite keys, inputs) and all numbers with
   `scripts/check_paper_numbers.py` (30/30) — no TeX engine available locally.
5. [x] Re-check refs.bib and Badalova & Mayr Table 4 (m3, m5).

## Second pass on the compiled PDF (13 Nov 2026)

Reviewing the first Overleaf build turned up presentation defects that the source alone did not show:

| # | Defect in the compiled PDF | Fix |
|---|---|---|
| p1 | McNemar p-values printed as `0.0e+00`, which reads as "p = 0" | exact p below 1e-4 now prints as $<10^{-10}$ (`make_tables.py`) |
| p2 | Figure legends used internal names ("V1-E review Eq. 2", "V3 AtomGPT") not matching the paper's V1E/V3 | `plots.py` NAMES aligned with the paper |
| p3 | H1–H3 were discussed but never stated in the paper | hypotheses added to the Introduction with their contradiction conditions |
| p4 | No pipeline figure, although the design is the contribution | `make_pipeline_figure.py`; Fig. 1 (full width) |
| p5 | References showed no arXiv IDs; IEEEtran lower-cased titles ("aI Tools", "LLM" → "llm") | `refs.bib`: braces protect capitalisation, `howpublished` carries the arXiv ID |
| p6 | Registries (Crossref, OpenAlex, arXiv) and the Neralla repository were named but not cited | four entries added and cited |
| p7 | Error analysis, identifier strata and adjudication existed only as prose | Tables V–VII generated from CSVs (`make_tables_extra.py`) |
| p8 | V2 FPR printed 16.1% in the table and 16.0% in the figure | double rounding; table now computes from counts (91/567 = 16.0%) |
| p9 | `kalai2025` in the bib but uncited, so BibTeX dropped it | cited in the Introduction |

| p10 | Body ran ~5 pages excluding references, under the 6--10 page target, while two items the assignment requires as evidence (baseline validation, reproducibility) were compressed to a few lines | added §IV-B Baseline validation with the oracle table (Table VIII) and §IV-C Reproducibility (frozen checksums, the two offline commands, seeds) |
| p11 | Limitations cited amendments as D23--D32; D33--D35 were added later | corrected to D23--D35 |

| p12 | A measured validity check was never reported: **no citation in either set finished with an empty candidate list** (median 5, the Crossref row limit). Without it, a reader cannot tell whether type-A errors are ranking failures or a broken query | added §VI Threats to validity, which uses it to rule out retrieval failure as the explanation |
| p13 | No pointer to the code: the assignment requires a GitHub repository, and the draft had none after the Environment paragraph was rewritten | added a Code and data availability statement with a red `[INSERT GITHUB URL]` placeholder |
| p14 | The reproducibility command block wrapped with inconsistent indentation | re-set with explicit hanging indents |

## Author-response table

| Concern | Response | Change made |
|---|---|---|
| M1 | Accepted | Adjudication done (AI-assisted, D34); adjusted FPR 13.9–15.2% added to Results, Abstract, Limitations |
| M2 | Accepted | Discussion states FPR is a property of this pipeline; follow-up 1 proposed |
| M3 | Accepted | Limitations; per-paper spread 0–35% reported |
| M4 | Accepted | Conclusion softened to "0 of 58, exploratory" |
| M5 | Accepted | Discussion + Limitations |
| m1–m7 | m2, m4, m6 applied; m1 addressed with the new FPR figure; m3, m5 re-checked by me; m7 after Overleaf compile | FPR figure added to RQ1; phasing sentence in Setup; bib capitalisation braced and arXiv IDs now shown |
