"""Export CiteTracer's synthetic set as pipeline inputs with oracle candidates (no network).

R1-R3 -> label 'genuine'; H1-H6 -> 'fabricated'; P1/P3 excluded (CiteTracer's 'potential').
Each citation's only candidate is its seed record. Used to exercise score.py + evaluate.py
end to end before live data exist (G2 pipeline check). NOT the main experiment.

Usage: python scripts/make_oracle_inputs.py --data /path/to/CiteTracer/data --outdir data/oracle
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from citefpr.records import Ref, write_jsonl  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--outdir", default="data/oracle")
    a = ap.parse_args()
    d = Path(a.data)
    meta = json.loads((d / "synthetic_data/v2/meta.json").read_text(encoding="utf-8"))
    items = json.loads((d / "synthetic_data/v2/_all_test.json").read_text(encoding="utf-8"))
    refs, cands = [], []
    for it in items:
        m = meta.get(it.get("citation_id"))
        if not m or m["subtype"].startswith("P"):
            continue
        cid = "synth:" + it["citation_id"]
        lab = "genuine" if m["subtype"].startswith("R") else "fabricated"
        r = Ref.from_dict({**it, "id": cid, "label": lab, "source_set": "citetracer_synth_" + lab,
                           "subtype": m["subtype"], "entry_type": "synthetic"})
        seed = Ref.from_dict({**m["seed"], "id": cid + ":seed", "source": "seed"})
        refs.append(r.to_dict())
        cands.append({"ref_id": cid, "doi_found": None, "candidates": [seed.to_dict()]})
    out = Path(a.outdir)
    print(write_jsonl(out / "refs.jsonl", refs), "refs;", write_jsonl(out / "candidates.jsonl", cands),
          "candidate rows ->", out)


if __name__ == "__main__":
    main()
