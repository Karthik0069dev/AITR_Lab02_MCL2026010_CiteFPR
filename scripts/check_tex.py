"""Structural check of paper/main.tex without a TeX engine: balanced environments and braces,
resolvable cross-references, citation keys present in refs.bib, and existing \\input files.

Not a substitute for compiling, but it catches the errors that break an Overleaf build.
Usage: python scripts/check_tex.py
"""
from __future__ import annotations

import collections
import re
from pathlib import Path

TEX = Path("paper/main.tex")
BIB = Path("paper/refs.bib")
failures = 0


def rep(ok: bool, msg: str) -> None:
    global failures
    print(("  OK  " if ok else "FAIL  ") + msg)
    if not ok:
        failures += 1


def main() -> int:
    tex = TEX.read_text(encoding="utf-8")
    body = re.sub(r"(?<!\\)%.*", "", tex)

    stack, mismatched = [], []
    for m in re.finditer(r"\\(begin|end)\{([^}]+)\}", body):
        kind, env = m.group(1), m.group(2)
        if kind == "begin":
            stack.append(env)
        elif stack and stack[-1] == env:
            stack.pop()
        else:
            mismatched.append(env)
    rep(not stack and not mismatched,
        f"environments balanced (unclosed={stack}, mismatched={mismatched})")

    depth, stray, i = 0, None, 0
    while i < len(body):
        c = body[i]
        if c == "\\" and i + 1 < len(body):
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth < 0 and stray is None:
                stray = i
        i += 1
    rep(depth == 0 and stray is None, f"braces balanced (depth={depth}, stray close at {stray})")

    found = re.findall(r"\\label\{([^}]+)\}", body)
    labels, refs = set(found), set(re.findall(r"\\ref\{([^}]+)\}", body))
    dups = [k for k, n in collections.Counter(found).items() if n > 1]
    rep(not (refs - labels), f"every \\ref resolves (missing={sorted(refs - labels)})")
    rep(not dups, f"no duplicate labels ({dups})")
    rep(not (labels - refs), f"every label is used (unused={sorted(labels - refs)})")

    keys = set(re.findall(r"@\w+\{([^,]+),", BIB.read_text(encoding="utf-8")))
    cited = {k.strip() for m in re.findall(r"\\cite\{([^}]+)\}", body) for k in m.split(",")}
    rep(not (cited - keys), f"every \\cite key is in refs.bib (missing={sorted(cited - keys)})")
    print(f"  --  bib entries not cited, dropped by BibTeX: {sorted(keys - cited)}")

    for f in re.findall(r"\\input\{([^}]+)\}", body):
        p = TEX.parent / (f if f.endswith(".tex") else f + ".tex")
        rep(p.exists(), f"\\input exists: {f}")
    for g in re.findall(r"\\includegraphics\[[^\]]*\]\{([^}]+)\}", body):
        rep((TEX.parent / "figures" / g).exists(), f"graphic exists: {g}")

    print("\nSTRUCTURE OK" if not failures else f"\n{failures} PROBLEM(S) FOUND")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
