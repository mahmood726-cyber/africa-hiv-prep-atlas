"""Unit tests for confusion matrix and per-MA count error."""
import math
import pytest

from africa_hiv_prep_atlas.audit import (
    confusion_at,
    confusion_at_d3,
    sensitivity,
    specificity,
    per_ma_count_error,
)


def _row(ma, trial, claim, truth):
    return {
        "ma_id": ma, "trial_id": trial,
        "claimed_a": claim, "claimed_b": False, "claimed_c": False,
        "truth_d1": truth, "truth_d2": truth, "truth_d3": truth,
    }


def test_confusion_at_d3_simple():
    rows = [
        _row("M1", "T1", True, True),    # TP
        _row("M1", "T2", True, False),   # FP
        _row("M1", "T3", False, True),   # FN
        _row("M1", "T4", False, False),  # TN
    ]
    c = confusion_at_d3(rows)
    assert c == {"tp": 1, "fp": 1, "fn": 1, "tn": 1}


def test_sensitivity_correct():
    c = {"tp": 8, "fp": 2, "fn": 2, "tn": 8}
    assert sensitivity(c) == 0.8


def test_specificity_correct():
    c = {"tp": 8, "fp": 2, "fn": 2, "tn": 8}
    assert specificity(c) == 0.8


def test_sensitivity_zero_positives_returns_nan():
    c = {"tp": 0, "fp": 0, "fn": 0, "tn": 10}
    assert math.isnan(sensitivity(c))


def test_specificity_zero_negatives_returns_nan():
    c = {"tp": 5, "fp": 0, "fn": 0, "tn": 0}
    assert math.isnan(specificity(c))


def test_per_ma_count_error_simple():
    rows = [
        _row("M1", "T1", True, True),
        _row("M1", "T2", True, False),
        _row("M1", "T3", False, True),
    ]
    errs = per_ma_count_error(rows)
    # M1 claimed=2, truth=2, |diff|=0
    assert errs == {"M1": 0}


def test_per_ma_count_error_over_claim():
    rows = [
        _row("M1", "T1", True, False),
        _row("M1", "T2", True, False),
    ]
    errs = per_ma_count_error(rows)
    assert errs == {"M1": 2}


def test_confusion_at_d1_uses_truth_d1():
    """confusion_at with truth_d1 key uses the d1 column, not d3."""
    rows = [
        {"ma_id": "M1", "trial_id": "T1",
         "claimed_a": True, "claimed_b": False, "claimed_c": False,
         "truth_d1": True, "truth_d2": False, "truth_d3": False},   # TP at d1, FP at d3
        {"ma_id": "M1", "trial_id": "T2",
         "claimed_a": False, "claimed_b": False, "claimed_c": False,
         "truth_d1": True, "truth_d2": False, "truth_d3": False},   # FN at d1
    ]
    c_d1 = confusion_at(rows, "truth_d1")
    c_d3 = confusion_at(rows, "truth_d3")
    assert c_d1 == {"tp": 1, "fp": 0, "fn": 1, "tn": 0}
    assert c_d3 == {"tp": 0, "fp": 1, "fn": 0, "tn": 1}


def test_confusion_at_invalid_key_raises():
    import pytest
    rows = [_row("M1", "T1", True, True)]
    with pytest.raises(ValueError, match="truth_key"):
        confusion_at(rows, "truth_d9")
