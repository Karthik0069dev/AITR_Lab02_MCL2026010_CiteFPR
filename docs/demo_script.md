# Five-minute demonstration script

Measured on this laptop, 13 Nov 2026: `pytest` 2 s, `score.py` **43 s**, `evaluate.py` 14 s,
`check_paper_numbers.py` instant. About 60 s of compute, so you talk through most of it.
Everything below runs **offline** from the frozen cache; nothing touches a registry.

**Before you start.** Open a terminal in the project folder, maximise the font, and have these
ready in tabs: `results/metrics.csv`, `docs/viva_prep.md`, and the paper PDF at Table II.

```bash
cd "C:\Users\karth\Downloads\cladue\AITR_Lab02_MCL2026010_CiteFPR"
```

Then activate the environment **once**, so every command below is just `python`:

```bash
.venv\Scripts\activate
```

Use **backslashes**. `.venv/Scripts/python` is Git Bash syntax, and the normal Windows prompt
answers *"'.venv' is not recognized as an internal or external command"*. In PowerShell the line
is `.\.venv\Scripts\Activate.ps1`. Your prompt should then start with `(.venv)`; confirm with
`python --version` → `Python 3.12.10`.

---

## 0:00–0:45 — The question (no commands)

> "Tools that check whether a citation is real look it up in Crossref, arXiv and OpenAlex and flag
> what they can't match. They're almost always tested on *known fakes*, which measures recall. Nobody
> reports how often they flag a reference that is perfectly genuine.
>
> That matters because fabricated citations are rare — around 1%. When positives are rare, the
> false-positive rate decides whether a flag means anything. So I measured it: five published
> scoring rules, on genuine references from papers written *before* ChatGPT existed, so they can't
> be AI-fabricated."

Point at the pipeline figure (Fig. 1) while saying this.

---

## 0:45–1:00 — Tests

```bash
python -m pytest -q
```

> "33 unit tests — the similarity function, the Wilson interval, the exact McNemar test, and
> Eq. 13, which reproduces the worked example from my review."

---

## 1:00–2:00 — Scoring (start it, then talk for 43 s)

```bash
python scripts/score.py --refs data/genuine_refs.jsonl data/fabricated_refs.jsonl --candidates data/frozen/candidates_20261113.jsonl --out results/scores.csv
```

**Start the command, then keep talking — it takes 43 seconds.** Fill the silence with the control:

> "This is scoring 1,374 citations: 567 genuine references from 19 pre-ChatGPT arXiv papers, and
> 807 fabricated ones from desk-rejected ICLR 2026 submissions.
>
> The important bit is what it's reading — a **frozen** file. I ran retrieval once, then copied the
> response cache and the candidate list and hashed them with SHA-256. All five verifiers see
> byte-identical candidates, so any difference between them comes from the scoring rule, not from
> one of them getting luckier with the registry on a different day. That's the whole point of the
> design: it's a controlled comparison, not five tools run separately."

When it finishes, note `0 had no candidate record`.

---

## 2:00–3:00 — Evaluation and the headline

```bash
python scripts/evaluate.py --scores results/scores.csv --adjudication results/adjudication_sample.csv --out results
```

It prints the five verifiers. Read the contrast straight off the screen:

> "Recall 96–99% — they catch nearly every fake. But the false-positive rate is 16–17%, and 47% for
> the strict one. About one in six genuine references gets flagged.
>
> Put that through Eq. 13 at a 1% fabrication rate: **fewer than 6% of the flags are correct.**
> Ninety-four out of a hundred flags would be a real citation wrongly accused."

---

## 3:00–4:00 — Why (the part that makes it research, not benchmarking)

Open `results/fp_mechanisms.csv` and `results/fp_by_identifier.csv`.

> "I classified every false positive by what was in its candidate list. For V1E, **84 of 96** are
> type A — the real paper was never among the candidates. So this is mostly a *retrieval* failure,
> not a scoring failure; the three main rules agree with each other to within 1.2 points.
>
> And it isn't that retrieval returned nothing — **no citation finished with an empty candidate
> list**; the median got 5. It returned the wrong things.
>
> The strongest predictor isn't the rule, it's the identifier: **no reference carrying a DOI was
> flagged at all**, 0 of 58. Without a DOI or arXiv ID, 22%."

If asked for a concrete case:

> "Kingma and Welling's VAE paper. Crossref returned a *2024* paper with the identical title by
> different authors. A candidate already scored above the 0.8 similarity bar, so the arXiv fallback
> never fired and the real paper never entered the list. I read the raw cached JSON to confirm it."

---

## 4:00–5:00 — Honesty, then stop

```bash
python scripts/check_paper_numbers.py
```

> "40 checks: every number in the paper is re-derived from the result files, and it fails if the
> text disagrees. It caught a real bug — one false-positive rate printed as 16.1% in a table and
> 16.0% in a figure, from rounding twice.
>
> Three things I want to be straight about:
> **The ablation did nothing.** The author veto changed zero flags out of 1,374. Negative result,
> reported as one.
> **My third hypothesis was wrong.** I predicted arXiv-cited entries would be worst; they're the
> *best* for three of the five rules.
> **The adjudication was AI-assisted.** I checked all 123 flagged references against independent
> sources, but the labelling was done with AI help from recorded evidence and I accepted it — that's
> stated in the paper, not buried. The evidence for every row is in the repo.
>
> So the conclusion is narrow and I'd defend it: on this pipeline, in this field, a flag from these
> verifiers is a *request to check by hand*, not evidence of fabrication."

---

## Likely interruptions

| Question | One-line answer |
|---|---|
| "Only 19 papers?" | 30 sampled, 11 shipped only `.bbl`; it widens the intervals and I report the paper-cluster CI (V1E 12.2–21.7%). |
| "Isn't 17% just your pipeline being bad?" | Partly, yes — I say so in §VI. That's exactly why follow-up 1 is an OpenAlex key, to measure how much type-A error disappears. |
| "Did you tune the thresholds?" | No. They're fixed from the source papers and frozen since 28 Oct. The τ sweep is reported as sensitivity only. |
| "How do I know the results are real?" | The command you just watched regenerates `scores.csv` byte-for-byte from the checksummed cache. |
| "What did the AI get wrong?" | 18 logged entries. Three good ones: a unit test whose arithmetic was wrong; a plan that would have biased the comparison via an OpenAlex budget that didn't exist; and a client that cached rate-limit errors as "not found". |

## If something fails live

* Scoring is slow but offline — it cannot fail on the network.
* If a command errors, fall back to `results/metrics.csv`, which is committed and is the same data.
* Have the repo open in a browser as a backup:
  <https://github.com/Karthik0069dev/AITR_Lab02_MCL2026010_CiteFPR>
