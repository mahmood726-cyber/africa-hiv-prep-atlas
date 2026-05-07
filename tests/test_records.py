import pytest
from africa_hiv_prep_atlas.records import Trial, MA, AtlasRow


def test_trial_frozen():
    t = Trial(
        trial_id="HPTN_084", nct="NCT03164564", pactr=None,
        modality="cabotegravir", year=2020,
        enrolment_by_country={"South Africa": 700, "Uganda": 600},
        total_enrolled=3224, source_id="hptn084_publication_2022",
    )
    with pytest.raises((AttributeError, Exception)):
        t.trial_id = "X"


def test_trial_african_n():
    t = Trial(
        trial_id="HPTN_084", nct="NCT03164564", pactr=None,
        modality="cabotegravir", year=2020,
        enrolment_by_country={"South Africa": 700, "USA": 100},
        total_enrolled=800, source_id="src1",
    )
    assert t.african_n() == 700


def test_trial_african_fraction():
    t = Trial(
        trial_id="HPTN_084", nct="NCT03164564", pactr=None,
        modality="cabotegravir", year=2020,
        enrolment_by_country={"South Africa": 700, "USA": 100},
        total_enrolled=800, source_id="src1",
    )
    assert abs(t.african_fraction() - 0.875) < 1e-9


def test_trial_zero_total_returns_zero_fraction():
    t = Trial(
        trial_id="X", nct=None, pactr=None, modality="x", year=2020,
        enrolment_by_country={}, total_enrolled=0, source_id="src1",
    )
    assert t.african_fraction() == 0.0


def test_ma_frozen_with_cited_trial_ids():
    m = MA(
        ma_id="abc2024", first_author="Smith", year=2024,
        cited_trial_ids=("HPTN_083", "HPTN_084"),
        full_text_source_id="abc2024_pdf",
    )
    assert m.cited_trial_ids == ("HPTN_083", "HPTN_084")


def test_atlas_row_layers():
    r = AtlasRow(
        ma_id="abc2024", trial_id="HPTN_084",
        claimed_a=True, claimed_b=True, claimed_c=False,
        truth_d1=True, truth_d2=True, truth_d3=True,
        confidence_layer_m="high", confidence_layer_t="medium",
        source_lines=("abc2024_p3l5", "hptn084_p1l2"),
    )
    assert r.claimed_union() is True
    assert r.tp_at_d3() is True
    assert r.fp_at_d3() is False
    assert r.fn_at_d3() is False
    assert r.tn_at_d3() is False
