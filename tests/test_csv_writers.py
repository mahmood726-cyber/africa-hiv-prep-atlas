"""Unit tests for deterministic CSV writers."""
from io import StringIO

from africa_hiv_prep_atlas.csv_writers import (
    write_atlas_csv,
    write_trials_csv,
    write_mas_csv,
    ATLAS_COLUMNS,
    TRIALS_COLUMNS,
    MAS_COLUMNS,
)


def test_atlas_columns_exact():
    assert ATLAS_COLUMNS == (
        "ma_id", "trial_id",
        "claimed_a", "claimed_b", "claimed_c", "claimed_union",
        "truth_d1", "truth_d2", "truth_d3",
        "tp_at_d3", "fp_at_d3", "fn_at_d3", "tn_at_d3",
        "confidence_layer_m", "confidence_layer_t",
        "source_lines",
    )


def test_atlas_writer_emits_deterministic_csv():
    rows = [
        {"ma_id": "M1", "trial_id": "T1",
         "claimed_a": True, "claimed_b": False, "claimed_c": False,
         "truth_d1": True, "truth_d2": True, "truth_d3": True,
         "confidence_layer_m": "high", "confidence_layer_t": "high",
         "source_lines": ("M1_p3l5", "T1_p1l2")},
    ]
    buf = StringIO()
    write_atlas_csv(rows, buf)
    out = buf.getvalue()
    assert out.startswith(",".join(ATLAS_COLUMNS) + "\n")
    assert "M1,T1,True,False,False,True,True,True,True,True,False,False,False,high,high,M1_p3l5;T1_p1l2" in out


def test_atlas_writer_sorts_rows():
    rows = [
        {"ma_id": "M2", "trial_id": "T1",
         "claimed_a": False, "claimed_b": False, "claimed_c": False,
         "truth_d1": False, "truth_d2": False, "truth_d3": False,
         "confidence_layer_m": "high", "confidence_layer_t": "high",
         "source_lines": ()},
        {"ma_id": "M1", "trial_id": "T2",
         "claimed_a": True, "claimed_b": True, "claimed_c": True,
         "truth_d1": True, "truth_d2": True, "truth_d3": True,
         "confidence_layer_m": "high", "confidence_layer_t": "high",
         "source_lines": ()},
    ]
    buf = StringIO()
    write_atlas_csv(rows, buf)
    lines = buf.getvalue().strip().split("\n")
    # Sorted by (ma_id, trial_id)
    assert lines[1].startswith("M1,T2,")
    assert lines[2].startswith("M2,T1,")
