"""Unit tests for Layer-M (MA-claim) extraction from fixtures."""
from africa_hiv_prep_atlas.ma_claim import (
    extract_layer_m_from_fixture,
    layer_stripped_union,
)


def test_extract_returns_three_booleans_per_trial():
    fixture = {
        "ma_id": "smith2024",
        "claims": {
            "HPTN_084": {"a": True, "b": True, "c": True, "source_lines": ["p3l5"]},
            "HPTN_083": {"a": False, "b": True, "c": False, "source_lines": ["p3l8"]},
        },
    }
    rows = extract_layer_m_from_fixture(fixture)
    by_trial = {r["trial_id"]: r for r in rows}
    assert by_trial["HPTN_084"]["claimed_a"] is True
    assert by_trial["HPTN_084"]["claimed_b"] is True
    assert by_trial["HPTN_084"]["claimed_c"] is True
    assert by_trial["HPTN_083"]["claimed_a"] is False
    assert by_trial["HPTN_083"]["claimed_b"] is True
    assert by_trial["HPTN_083"]["claimed_c"] is False


def test_extract_handles_missing_layers_as_false():
    fixture = {"ma_id": "x", "claims": {"HPTN_084": {"a": True, "source_lines": ["x"]}}}
    rows = extract_layer_m_from_fixture(fixture)
    r = rows[0]
    assert r["claimed_a"] is True
    assert r["claimed_b"] is False
    assert r["claimed_c"] is False


def test_layer_stripped_a_only():
    row = {"claimed_a": True, "claimed_b": False, "claimed_c": False}
    assert layer_stripped_union(row, layers=("a",)) is True


def test_layer_stripped_a_b_only():
    row = {"claimed_a": False, "claimed_b": True, "claimed_c": True}
    assert layer_stripped_union(row, layers=("a", "b")) is True
    row = {"claimed_a": False, "claimed_b": False, "claimed_c": True}
    assert layer_stripped_union(row, layers=("a", "b")) is False


def test_layer_stripped_full_union():
    row = {"claimed_a": False, "claimed_b": False, "claimed_c": True}
    assert layer_stripped_union(row, layers=("a", "b", "c")) is True


def test_layer_stripped_empty_layers_returns_false():
    row = {"claimed_a": True, "claimed_b": True, "claimed_c": True}
    assert layer_stripped_union(row, layers=()) is False
