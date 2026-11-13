# Data

Nothing in this folder is committed except this file (see `.gitignore`); regenerate with the
commands in the main README. Checksums of the frozen inputs: `results/frozen_checksums.txt`.

## Kept locally (13 Nov 2026)

| File | Made by | Contents |
|------|---------|----------|
| `fabricated_refs.jsonl` | `load_positives.py` | 807 ICLR 2026 fabricated citations from CiteTracer (commit 8c47ca5) |
| `genuine_paper_ids.txt`, `genuine_papers.csv` | `build_genuine_set.py` | 30 sampled arXiv IDs (seed 20261028) and per-paper stats |
| `genuine_refs.jsonl` | `build_genuine_set.py` | 567 cited .bib entries of the 19 papers with a .bib, label `genuine` |
| `frozen/cache_20261113.sqlite` | `run_retrieval.py` | every registry response of the reported run (frozen) |
| `frozen/candidates_20261113.jsonl` | `run_retrieval.py` | candidate records per citation (frozen); input to `score.py` |

With these files, everything from `score.py` onward reproduces offline:

```bash
python scripts/score.py --refs data/genuine_refs.jsonl data/fabricated_refs.jsonl --candidates data/frozen/candidates_20261113.jsonl --out results/scores.csv
python scripts/evaluate.py --scores results/scores.csv --adjudication results/adjudication_sample.csv --out results
```

## Removed after the run (regenerable)

Working copies `cache.sqlite` / `candidates.jsonl` (byte-identical to `frozen/`), phase-1 retrieval
intermediates, and `adjudication_cache.sqlite` (the evidence used is kept in
`results/adjudication_evidence.csv`). The CiteTracer clone is not kept; re-clone it to re-run
`load_positives.py` or `oracle_validation.py`.

Leakage note: genuine papers come from 2020 arXiv cs.CL; positives come from 2026 ICLR
submissions. A citing paper can never be in both sets; `evaluate.py` audits ID prefixes.
Privacy: references contain author names only; no personal data beyond published metadata.
