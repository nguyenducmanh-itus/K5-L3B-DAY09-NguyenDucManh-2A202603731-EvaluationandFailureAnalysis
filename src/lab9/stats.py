"""Statistics for judge calibration and paired evaluation."""
from __future__ import annotations
import math
from collections.abc import Sequence
from math import comb
import numpy as np
from scipy.stats import bootstrap

POS = "FAIL"

def _same_length(human, judge):
    if len(human) != len(judge):
        raise ValueError("human and judge labels must have equal length")

def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    _same_length(human, judge)
    tp = sum(h == POS and j == POS for h, j in zip(human, judge))
    fp = sum(h != POS and j == POS for h, j in zip(human, judge))
    fn = sum(h == POS and j != POS for h, j in zip(human, judge))
    tn = sum(h != POS and j != POS for h, j in zip(human, judge))
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}

def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    c = confusion(human, judge)
    return (c["tp"] / (c["tp"] + c["fp"]) if c["tp"] + c["fp"] else 0.0,
            c["tp"] / (c["tp"] + c["fn"]) if c["tp"] + c["fn"] else 0.0)

def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    _same_length(human, judge)
    n = len(human)
    if not n:
        raise ValueError("kappa is undefined for an empty sample")
    observed = sum(h == j for h, j in zip(human, judge)) / n
    labels = set(human) | set(judge)
    expected = sum((sum(x == label for x in human) / n) * (sum(x == label for x in judge) / n) for label in labels)
    if math.isclose(expected, 1.0):
        raise ValueError("kappa undefined when expected agreement is 1")
    return (observed - expected) / (1 - expected)

def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    if not all(0 <= x <= 1 for x in (observed_rate, sensitivity, specificity)):
        raise ValueError("rates must be between 0 and 1")
    den = sensitivity + specificity - 1
    if math.isclose(den, 0.0):
        raise ValueError("sensitivity + specificity must differ from 1")
    return min(1.0, max(0.0, (observed_rate + specificity - 1) / den))

def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000, rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    if len(a) != len(b) or not a:
        raise ValueError("paired samples must have equal, nonzero length")
    if n_resamples <= 0 or not 0 < confidence < 1:
        raise ValueError("n_resamples must be positive and confidence in (0, 1)")
    av, bv = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if not np.isfinite(av).all() or not np.isfinite(bv).all():
        raise ValueError("samples must be finite")
    diff = av - bv
    mean = float(np.mean(diff))
    if np.all(diff == 0):
        return (0.0, 0.0, 0.0)
    result = bootstrap((av, bv), lambda x, y, axis: np.mean(x-y, axis=axis), paired=True, vectorized=True, n_resamples=n_resamples, confidence_level=confidence, method="percentile", rng=np.random.default_rng(rng))
    return mean, float(result.confidence_interval.low), float(result.confidence_interval.high)

def _validate_nck(n: int, c: int, k: int):
    if any(not isinstance(x, int) or isinstance(x, bool) for x in (n, c, k)) or n < 0 or c < 0 or c > n or k < 1:
        raise ValueError("require integers n >= c >= 0 and k >= 0")
    if k > n:
        raise ValueError("k cannot exceed n")

def pass_at_k(n: int, c: int, k: int) -> float:
    _validate_nck(n,c,k)
    if k == 0: return 0.0
    if n-c < k: return 1.0
    return 1.0 - comb(n-c,k)/comb(n,k)

def pass_hat_k(n: int, c: int, k: int) -> float:
    _validate_nck(n,c,k)
    if k == 0: return 1.0
    if c < k: return 0.0
    return comb(c,k)/comb(n,k)

