"""Clustered bootstrap and permutation fallback for sens/spec CIs."""
from __future__ import annotations

import math
from collections import defaultdict

import numpy as np

from africa_hiv_prep_atlas.audit import confusion_at, confusion_at_d3, sensitivity, specificity

K_GUARD_THRESHOLD = 10


def choose_method(rows: list[dict]) -> str:
    n_mas = len({r["ma_id"] for r in rows})
    return "clustered_bootstrap" if n_mas >= K_GUARD_THRESHOLD else "permutation"


def _rows_by_ma(rows: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        out[r["ma_id"]].append(r)
    return dict(out)


def cluster_bootstrap_sens_spec(
    rows: list[dict], n_reps: int = 1000, seed: int = 42, alpha: float = 0.05,
) -> dict:
    rng = np.random.default_rng(seed)
    by_ma = _rows_by_ma(rows)
    ma_keys = list(by_ma.keys())
    n_clusters = len(ma_keys)

    point_c = confusion_at_d3(rows)
    point_sens = sensitivity(point_c)
    point_spec = specificity(point_c)

    sens_samples: list[float] = []
    spec_samples: list[float] = []
    for _ in range(n_reps):
        idx = rng.integers(0, n_clusters, size=n_clusters)
        resample: list[dict] = []
        for i in idx:
            resample.extend(by_ma[ma_keys[i]])
        c = confusion_at_d3(resample)
        s = sensitivity(c)
        p = specificity(c)
        if not math.isnan(s):
            sens_samples.append(s)
        if not math.isnan(p):
            spec_samples.append(p)
    sens_samples.sort()
    spec_samples.sort()

    def _quant(arr, q):
        if not arr:
            return float("nan")
        i = int(q * (len(arr) - 1))
        return arr[i]

    return {
        "method": "clustered_bootstrap",
        "n_clusters": n_clusters,
        "n_reps": n_reps,
        "sensitivity": point_sens,
        "specificity": point_spec,
        "sens_ci": (_quant(sens_samples, alpha / 2), _quant(sens_samples, 1 - alpha / 2)),
        "spec_ci": (_quant(spec_samples, alpha / 2), _quant(spec_samples, 1 - alpha / 2)),
    }


def permutation_sens_spec(
    rows: list[dict], n_reps: int = 1000, seed: int = 42, alpha: float = 0.05,
) -> dict:
    """k<10 guard: permute claim labels within trials, derive null distribution.

    Used as a fallback when the cluster bootstrap is unstable due to k<10 MAs.
    """
    rng = np.random.default_rng(seed)
    point_c = confusion_at_d3(rows)
    point_sens = sensitivity(point_c)
    point_spec = specificity(point_c)

    n = len(rows)
    sens_samples: list[float] = []
    spec_samples: list[float] = []
    for _ in range(n_reps):
        idx = rng.permutation(n)
        permuted = [
            dict(rows[i], truth_d3=rows[idx[i]]["truth_d3"])
            for i in range(n)
        ]
        c = confusion_at_d3(permuted)
        s = sensitivity(c)
        p = specificity(c)
        if not math.isnan(s):
            sens_samples.append(s)
        if not math.isnan(p):
            spec_samples.append(p)
    sens_samples.sort()
    spec_samples.sort()

    def _quant(arr, q):
        if not arr:
            return float("nan")
        i = int(q * (len(arr) - 1))
        return arr[i]

    return {
        "method": "permutation",
        "n_reps": n_reps,
        "sensitivity": point_sens,
        "specificity": point_spec,
        "sens_ci": (_quant(sens_samples, alpha / 2), _quant(sens_samples, 1 - alpha / 2)),
        "spec_ci": (_quant(spec_samples, alpha / 2), _quant(spec_samples, 1 - alpha / 2)),
    }


def _run_one_definition(
    rows: list[dict],
    truth_key: str,
    n_reps: int,
    seed: int,
    alpha: float,
) -> dict:
    """Run clustered bootstrap (or permutation fallback) for one truth column.

    Uses the same seeded RNG, n_reps, and clustering as the primary helpers.
    """
    rng = np.random.default_rng(seed)
    n_mas = len({r["ma_id"] for r in rows})
    method = "clustered_bootstrap" if n_mas >= K_GUARD_THRESHOLD else "permutation"

    point_c = confusion_at(rows, truth_key)
    point_sens = sensitivity(point_c)
    point_spec = specificity(point_c)

    sens_samples: list[float] = []
    spec_samples: list[float] = []

    if method == "clustered_bootstrap":
        by_ma = _rows_by_ma(rows)
        ma_keys = list(by_ma.keys())
        n_clusters = n_mas
        for _ in range(n_reps):
            idx = rng.integers(0, n_clusters, size=n_clusters)
            resample: list[dict] = []
            for i in idx:
                resample.extend(by_ma[ma_keys[i]])
            c = confusion_at(resample, truth_key)
            s = sensitivity(c)
            p = specificity(c)
            if not math.isnan(s):
                sens_samples.append(s)
            if not math.isnan(p):
                spec_samples.append(p)
    else:
        # permutation fallback
        n_rows = len(rows)
        n_clusters = n_mas
        for _ in range(n_reps):
            idx = rng.permutation(n_rows)
            permuted = [
                dict(rows[i], **{truth_key: rows[idx[i]][truth_key]})
                for i in range(n_rows)
            ]
            c = confusion_at(permuted, truth_key)
            s = sensitivity(c)
            p = specificity(c)
            if not math.isnan(s):
                sens_samples.append(s)
            if not math.isnan(p):
                spec_samples.append(p)

    sens_samples.sort()
    spec_samples.sort()

    def _quant(arr, q):
        if not arr:
            return float("nan")
        i = int(q * (len(arr) - 1))
        return arr[i]

    return {
        "method": method,
        "n_clusters": n_clusters,
        "n_reps": n_reps,
        "sensitivity": point_sens,
        "specificity": point_spec,
        "sens_ci": (_quant(sens_samples, alpha / 2), _quant(sens_samples, 1 - alpha / 2)),
        "spec_ci": (_quant(spec_samples, alpha / 2), _quant(spec_samples, 1 - alpha / 2)),
    }


def sweep_definitions(
    rows: list[dict],
    n_reps: int = 1000,
    seed: int = 42,
    alpha: float = 0.05,
) -> dict:
    """Run sens/spec bootstrap for all three ground-truth definitions.

    Returns a dict with keys 'd1', 'd2', 'd3', each containing a result dict
    identical in shape to the output of cluster_bootstrap_sens_spec.
    D3 matches the primary headline; D1/D2 are pre-specified sensitivity sweeps.
    No inferential adjustment is applied (spec §3).
    """
    return {
        "d1": _run_one_definition(rows, "truth_d1", n_reps, seed, alpha),
        "d2": _run_one_definition(rows, "truth_d2", n_reps, seed, alpha),
        "d3": _run_one_definition(rows, "truth_d3", n_reps, seed, alpha),
    }
