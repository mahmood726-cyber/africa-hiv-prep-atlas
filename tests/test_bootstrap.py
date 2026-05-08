"""Unit tests for clustered bootstrap and permutation fallback."""
import math
import pytest

from africa_hiv_prep_atlas.bootstrap import (
    cluster_bootstrap_sens_spec,
    permutation_sens_spec,
    choose_method,
    sweep_definitions,
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


# ---------------------------------------------------------------------------
# sweep_definitions tests
# ---------------------------------------------------------------------------

def _rows_with_separate_truths(spec):
    """spec = list of (ma, claim, truth_d1, truth_d2, truth_d3)."""
    return [
        {"ma_id": ma, "trial_id": f"T{i}",
         "claimed_a": claim, "claimed_b": False, "claimed_c": False,
         "truth_d1": td1, "truth_d2": td2, "truth_d3": td3}
        for i, (ma, claim, td1, td2, td3) in enumerate(spec)
    ]


def test_sweep_definitions_returns_three_keys():
    rows = _rows([
        ("M1", True, True), ("M1", True, False),
        ("M2", False, True), ("M2", True, True),
    ] * 6)
    result = sweep_definitions(rows, n_reps=200, seed=42)
    assert set(result.keys()) == {"d1", "d2", "d3"}
    for key in ("d1", "d2", "d3"):
        d = result[key]
        assert "sensitivity" in d
        assert "specificity" in d
        assert "sens_ci" in d
        assert "spec_ci" in d
        assert "method" in d


def test_sweep_d1_sensitivity_lower_bound_for_known_data():
    """D1 is loosest: on data where D1 superset-includes D3 positives, D1 sens >= D3 sens."""
    # All D3=True are also D1=True. Some D1=True are D3=False (extra positives in D1).
    # This means the D1 denominator (TP+FN) can only be >= D3 denominator.
    # With claim=True for all rows that are truth, D1 sens should be >= D3 sens.
    rows = _rows_with_separate_truths([
        # ma,  claim, d1,    d2,    d3
        ("M1", True,  True,  True,  True),   # TP for all
        ("M1", True,  True,  True,  True),
        ("M1", True,  True,  False, False),  # TP at D1, FP at D2/D3
        ("M2", False, True,  True,  True),   # FN for all
        ("M2", True,  True,  True,  True),
        ("M2", True,  True,  False, False),
        ("M3", False, True,  True,  True),
        ("M3", True,  True,  True,  True),
        ("M3", True,  True,  False, False),
    ] * 4)
    result = sweep_definitions(rows, n_reps=300, seed=42)
    d1_sens = result["d1"]["sensitivity"]
    d3_sens = result["d3"]["sensitivity"]
    # D1 has more true positives in denominator via the extra d1-only rows;
    # here claim=True on those extra d1-only rows contributes TP to D1 but FP to D3.
    # D3 positives are a strict subset of D1 positives on this synthetic input.
    assert not math.isnan(d1_sens)
    assert not math.isnan(d3_sens)
    # The point estimate at D1 must be >= D3 on this synthetic dataset
    # because D1 includes all D3 positives and adds more (FN cannot exceed D3's FN count).
    assert d1_sens >= d3_sens - 1e-9, (
        f"Expected D1 sensitivity ({d1_sens:.4f}) >= D3 sensitivity ({d3_sens:.4f})"
    )


def test_sweep_seed_reproducible():
    """Same seed and data must produce identical results."""
    rows = _rows([
        ("M1", True, True), ("M1", False, False),
        ("M2", True, True), ("M2", True, False),
        ("M3", False, True), ("M3", True, True),
    ] * 5)
    r1 = sweep_definitions(rows, n_reps=300, seed=42)
    r2 = sweep_definitions(rows, n_reps=300, seed=42)
    for key in ("d1", "d2", "d3"):
        assert r1[key]["sensitivity"] == r2[key]["sensitivity"]
        assert r1[key]["specificity"] == r2[key]["specificity"]
        assert r1[key]["sens_ci"] == r2[key]["sens_ci"]
        assert r1[key]["spec_ci"] == r2[key]["spec_ci"]
