"""Prompt 08 environment test. Prints a report and writes results/env_report.json.

Expected output type: a JSON-like report with Python/package versions, optional GPU info,
and one HTTP status per registry (200 = reachable). Share the console output in the log.

Usage: python scripts/env_test.py --mailto you@iiita.ac.in
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PROBES = {
    "crossref": "https://api.crossref.org/works?rows=1&query.bibliographic=attention+is+all+you+need",
    "arxiv": "https://export.arxiv.org/api/query?id_list=1706.03762",
    "openalex": "https://api.openalex.org/works/doi:10.18653/v1/n19-1423",
    "github": "https://github.com/aaFrostnova/CiteTracer",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mailto", default="")
    ap.add_argument("--out", default="results/env_report.json")
    a = ap.parse_args()
    rep = {"python": sys.version.split()[0], "platform": platform.platform(),
           "machine": platform.machine(), "packages": {}, "gpu": None, "network": {}}
    for p in ("requests", "matplotlib", "pytest"):
        try:
            rep["packages"][p] = importlib.import_module(p).__version__
        except Exception as exc:
            rep["packages"][p] = f"MISSING ({exc.__class__.__name__})"
    if shutil.which("nvidia-smi"):
        try:
            rep["gpu"] = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=20).stdout.strip()
        except Exception as exc:
            rep["gpu"] = f"nvidia-smi failed: {exc}"
    try:
        import requests
        for name, url in PROBES.items():
            if a.mailto and name in ("crossref", "openalex"):
                url += ("&" if "?" in url else "?") + "mailto=" + a.mailto
            key = os.environ.get("OPENALEX_API_KEY", "")
            if name == "openalex" and key:
                url += "&api_key=" + key
            try:
                r = requests.get(url, timeout=20, headers={"User-Agent": "citefpr-envtest"})
                hdr = {k: v for k, v in r.headers.items() if k.lower().startswith("x-rate")}
                rep["network"][name] = {"status": r.status_code, "rate_headers": hdr}
            except Exception as exc:
                rep["network"][name] = {"status": None, "error": exc.__class__.__name__ + ": " + str(exc)[:120]}
    except ImportError:
        rep["network"] = "requests missing"
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep, indent=2))
    ok = isinstance(rep["network"], dict) and all(
        (v.get("status") == 200) for k, v in rep["network"].items() if k != "github")
    print("\nENV TEST:", "PASS" if ok else "FAIL (see network/packages above)")
    if not rep["gpu"]:
        print("note: no NVIDIA GPU visible - fine, the main study is CPU-only")


if __name__ == "__main__":
    main()
