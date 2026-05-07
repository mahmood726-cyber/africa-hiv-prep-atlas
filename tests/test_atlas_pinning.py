"""Byte-pinning: atlas.csv is reproducible bit-for-bit on rerun."""
import hashlib
from io import StringIO

from africa_hiv_prep_atlas.csv_writers import write_atlas_csv


def _sample_rows():
    return [
        {"ma_id": "M1", "trial_id": "T1",
         "claimed_a": True, "claimed_b": False, "claimed_c": False,
         "truth_d1": True, "truth_d2": True, "truth_d3": True,
         "confidence_layer_m": "high", "confidence_layer_t": "high",
         "source_lines": ("a", "b")},
        {"ma_id": "M1", "trial_id": "T2",
         "claimed_a": False, "claimed_b": True, "claimed_c": False,
         "truth_d1": True, "truth_d2": False, "truth_d3": False,
         "confidence_layer_m": "medium", "confidence_layer_t": "high",
         "source_lines": ("c",)},
    ]


def test_byte_identical_on_rerun():
    a = StringIO(); write_atlas_csv(_sample_rows(), a)
    b = StringIO(); write_atlas_csv(_sample_rows(), b)
    assert hashlib.sha256(a.getvalue().encode()).hexdigest() == hashlib.sha256(b.getvalue().encode()).hexdigest()


def test_byte_identical_under_input_reorder():
    rows = _sample_rows()
    a = StringIO(); write_atlas_csv(rows, a)
    b = StringIO(); write_atlas_csv(list(reversed(rows)), b)
    assert a.getvalue() == b.getvalue()
