"""Unit tests for clustered bootstrap and permutation fallback."""
import math
import pytest

from africa_hiv_prep_atlas.bootstrap import (
    cluster_bootstrap_sens_spec,
    permutation_sens_spec,
    choose_method,
)


def _rows(spec):
    """spec = list of (ma, claim, truth)."""
    return [
        {"ma_id": ma, "trial_id": f"T{i}",
         "claimed_a": claim, "claimed_b": False, "claimed_c": False,
         "truth_d1": truth, "truth_d2": truth, "truth_d3": truth}
        for i, (ma, claim, truth) in enumerate(spec)
    ]


def test_choose_method_clustered_for_k_ge_10():
    mas = [f"M{i}" for i in range(11)]
    rows = [{"ma_id": m, "trial_id": "T1",
             "claimed_a": True, "claimed_b": False, "claimed_c": False,
             "truth_d1": True, "truth_d2": True, "truth_d3": True}
            for m in mas]
    assert choose_method(rows) == "clustered_bootstrap"


def test_choose_method_permutation_for_k_lt_10():
    mas = [f"M{i}" for i in range(5)]
    rows = [{"ma_id": m, "trial_id": "T1",
             "claimed_a": True, "claimed_b": False, "claimed_c": False,
             "truth_d1": True, "truth_d2": True, "truth_d3": True}
            for m in mas]
    assert choose_method(rows) == "permutation"


def test_cluster_bootstrap_returns_point_and_ci():
    rows = _rows([
        ("M1", True, True), ("M1", True, False),
        ("M2", False, True), ("M2", True, True),
        ("M3", True, True), ("M3", False, False),
    ] * 5)
    result = cluster_bootstrap_sens_spec(rows, n_reps=200, seed=42)
    assert "sensitivity" in result
    assert "specificity" in result
    assert "sens_ci" in result
    assert "spec_ci" in result
    s_lo, s_hi = result["sens_ci"]
    assert 0.0 <= s_lo <= s_hi <= 1.0


def test_permutation_returns_point_and_ci():
    rows = _rows([
        ("M1", True, True), ("M1", False, False),
        ("M2", True, True), ("M2", True, False),
    ])
    result = permutation_sens_spec(rows, n_reps=500, seed=42)
    assert "sensitivity" in result
    assert "specificity" in result
