"""Confusion matrix + per-MA count error."""
from __future__ import annotations

import math
from collections import defaultdict

_VALID_TRUTH_KEYS = frozenset({"truth_d1", "truth_d2", "truth_d3"})


def _claimed(row: dict) -> bool:
    return bool(row.get("claimed_a") or row.get("claimed_b") or row.get("claimed_c"))


def confusion_at(rows: list[dict], truth_key: str) -> dict:
    """Confusion matrix parameterised by truth column.

    truth_key must be one of 'truth_d1', 'truth_d2', 'truth_d3'.
    """
    if truth_key not in _VALID_TRUTH_KEYS:
        raise ValueError(f"truth_key must be one of {sorted(_VALID_TRUTH_KEYS)}, got {truth_key!r}")
    out = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    for r in rows:
        cl = _claimed(r)
        tr = bool(r[truth_key])
        if cl and tr:
            out["tp"] += 1
        elif cl and not tr:
            out["fp"] += 1
        elif (not cl) and tr:
            out["fn"] += 1
        else:
            out["tn"] += 1
    return out


def confusion_at_d3(rows: list[dict]) -> dict:
    """Thin wrapper around confusion_at for backward compatibility."""
    return confusion_at(rows, "truth_d3")


def sensitivity(c: dict) -> float:
    pos = c["tp"] + c["fn"]
    if pos == 0:
        return float("nan")
    return c["tp"] / pos


def specificity(c: dict) -> float:
    neg = c["tn"] + c["fp"]
    if neg == 0:
        return float("nan")
    return c["tn"] / neg


def per_ma_count_error(rows: list[dict]) -> dict:
    by_ma: dict[str, dict[str, int]] = defaultdict(lambda: {"claimed": 0, "truth": 0})
    for r in rows:
        by_ma[r["ma_id"]]["claimed"] += int(_claimed(r))
        by_ma[r["ma_id"]]["truth"] += int(bool(r["truth_d3"]))
    return {ma: abs(d["claimed"] - d["truth"]) for ma, d in by_ma.items()}
