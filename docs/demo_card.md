# Demo card — keep this on screen

One screen. Commands to paste, numbers to quote. Full wording: `demo_script.md`.

```
cd "C:\Users\karth\Downloads\cladue\AITR_Lab02_MCL2026010_CiteFPR"
```

| # | Paste this | While it runs, say |
|---|---|---|
| 1 | `.venv/Scripts/python -m pytest -q` | 33 tests: similarity, Wilson, McNemar, Eq. 13 |
| 2 | `.venv/Scripts/python scripts/score.py --refs data/genuine_refs.jsonl data/fabricated_refs.jsonl --candidates data/frozen/candidates_20261113.jsonl --out results/scores.csv` | **43 s — talk here.** 1,374 citations. All five verifiers read one *frozen, SHA-256 hashed* cache, so differences come from the rule, not from a luckier registry day |
| 3 | `.venv/Scripts/python scripts/evaluate.py --scores results/scores.csv --adjudication results/adjudication_sample.csv --out results` | reads out the five verifiers |
| 4 | `.venv/Scripts/python scripts/check_paper_numbers.py` | 40 checks: every number in the paper re-derived from the CSVs |

## Numbers to quote

| | V1E | V1F | V2 | V3 | V3a |
|---|---|---|---|---|---|
| FPR | 16.9% | 47.1% | 16.0% | 17.3% | 17.3% |
| Recall | 99.1% | 99.9% | 95.7% | 99.3% | 99.3% |
| PPV @ 1% | 0.056 | 0.021 | 0.057 | 0.055 | 0.055 |

* **The headline:** catches 96–99% of fakes, but **fewer than 6% of its flags are correct** at 1% prevalence.
* **Why:** 84 of 96 V1E false positives — the real paper was never in the candidate list.
* **But not a broken query:** *no* citation got an empty list; median 5 candidates.
* **Strongest predictor is the identifier, not the rule:** DOI → **0 of 58** flagged. No identifier → 22%.
* **Example:** Kingma & Welling VAE — Crossref returned a *2024* paper with the identical title by other authors.

## Say these out loud (don't wait to be asked)

1. **The ablation did nothing** — author veto changed 0 of 1,374 flags.
2. **H3 was wrong** — I predicted arXiv-cited entries worst; they're the *best*.
3. **Adjudication was AI-assisted** — evidence recorded for all 123 rows, stated in the paper.

## Closing line

> "On this pipeline, in this field, a flag from these verifiers is a request to check by hand — not evidence of fabrication."

## If asked / if it breaks

| | |
|---|---|
| "Are these numbers real?" | That run just rewrote `scores.csv` — `git status` shows no change. Byte-identical. |
| "Did you tune thresholds?" | No. Fixed from the source papers, frozen 28 Oct. τ sweep is sensitivity only. |
| "Only 19 papers?" | 30 sampled, 11 had no `.bib`. Paper-cluster CI reported: V1E 12.2–21.7%. |
| Command fails | `results/metrics.csv` is committed — same data. Repo open in a browser as backup. |
