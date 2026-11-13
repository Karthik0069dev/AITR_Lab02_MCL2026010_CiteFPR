"""Detector metrics: review Eqs. (12)-(13), Wilson intervals, bootstrap mixing.

Positive class = fabricated citation (a flag is a positive prediction).
"""
from __future__ import annotations

import math
import random
from typing import Sequence


def confusion(flags: Sequence[bool], is_fab: Sequence[bool]) -> dict:
    if len(flags) != len(is_fab):
        raise ValueError("flags and labels differ in length")
    tp = sum(f and y for f, y in zip(flags, is_fab))
    fp = sum(f and not y for f, y in zip(flags, is_fab))
    fn = sum((not f) and y for f, y in zip(flags, is_fab))
    tn = sum((not f) and (not y) for f, y in zip(flags, is_fab))
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def safe_div(a: float, b: float) -> float:
    return a / b if b else float("nan")


def prf(c: dict) -> dict:
    p = safe_div(c["tp"], c["tp"] + c["fp"])
    r = safe_div(c["tp"], c["tp"] + c["fn"])
    f1 = safe_div(2 * p * r, p + r) if not (math.isnan(p) or math.isnan(r)) else float("nan")
    fpr = safe_div(c["fp"], c["fp"] + c["tn"])
    return {"precision": p, "recall": r, "f1": f1, "fpr": fpr}


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion k/n."""
    if n == 0:
        return (float("nan"), float("nan"))
    phat = k / n
    den = 1 + z * z / n
    centre = (phat + z * z / (2 * n)) / den
    half = z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def ppv(recall: float, fpr: float, pi: float) -> float:
    """Review Eq. (13): PPV(pi) = R pi / (R pi + FPR (1 - pi))."""
    num = recall * pi
    den = num + fpr * (1 - pi)
    return safe_div(num, den)


def mcnemar_exact(a_flags: Sequence[bool], b_flags: Sequence[bool]) -> dict:
    """Exact (binomial) McNemar test on paired flags for the same items.

    b = items flagged by A only, c = flagged by B only; two-sided p from Binomial(b+c, 0.5).
    """
    if len(a_flags) != len(b_flags):
        raise ValueError("paired lists differ in length")
    b = sum(1 for x, y in zip(a_flags, b_flags) if x and not y)
    c = sum(1 for x, y in zip(a_flags, b_flags) if y and not x)
    n = b + c
    if n == 0:
        return {"a_only": 0, "b_only": 0, "p": 1.0}
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return {"a_only": b, "b_only": c, "p": min(1.0, 2 * tail)}


def cluster_bootstrap_rate(flags: Sequence[bool], clusters: Sequence[str], n_boot: int = 2000,
                           seed: int = 20261028) -> tuple[float, float]:
    """95% percentile CI of a rate, resampling whole clusters (e.g. citing papers)."""
    groups: dict[str, list[int]] = {}
    for f, g in zip(flags, clusters):
        groups.setdefault(g, []).append(int(f))
    keys = sorted(groups)
    if not keys:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    vals = []
    for _ in range(n_boot):
        k = n = 0
        for g in (rng.choice(keys) for _ in keys):
            k += sum(groups[g]); n += len(groups[g])
        vals.append(k / n if n else 0.0)
    vals.sort()
    return (vals[int(0.025 * (n_boot - 1))], vals[int(0.975 * (n_boot - 1))])


def bootstrap_ppv(genuine_flags: Sequence[bool], fab_flags: Sequence[bool], pi: float,
                  n_mix: int = 2000, mix_size: int = 1000, seed: int = 20261028) -> dict:
    """Empirical PPV by repeatedly mixing genuine and fabricated items at prevalence pi.

    Each mixture draws round(pi*mix_size) fabricated and the rest genuine items with
    replacement; returns mean precision and a 2.5-97.5 percentile band.
    """
    rng = random.Random(seed)
    n_fab = max(1, round(pi * mix_size))
    n_gen = mix_size - n_fab
    vals = []
    g, f = list(genuine_flags), list(fab_flags)
    if not g or not f:
        return {"mean": float("nan"), "lo": float("nan"), "hi": float("nan"), "n_mix": 0}
    for _ in range(n_mix):
        tp = sum(rng.choice(f) for _ in range(n_fab))
        fp = sum(rng.choice(g) for _ in range(n_gen))
        if tp + fp:
            vals.append(tp / (tp + fp))
    vals.sort()
    if not vals:
        return {"mean": float("nan"), "lo": float("nan"), "hi": float("nan"), "n_mix": 0}
    lo = vals[int(0.025 * (len(vals) - 1))]
    hi = vals[int(0.975 * (len(vals) - 1))]
    return {"mean": sum(vals) / len(vals), "lo": lo, "hi": hi, "n_mix": len(vals)}
