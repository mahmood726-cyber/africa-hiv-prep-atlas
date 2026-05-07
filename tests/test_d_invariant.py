"""Mathematical invariant: D2 implies D1, D3 implies D1.

D2 and D3 are NOT nested with each other (a trial could have 2 of 3 African
sites enrolling small numbers, with one US site enrolling 90% of participants).
"""
from africa_hiv_prep_atlas.records import Trial
from africa_hiv_prep_atlas.ground_truth import classify_d1, classify_d2, classify_d3


def _t(enrolment, sites, total):
    return Trial(
        trial_id="x", nct=None, pactr=None, modality="x", year=2020,
        enrolment_by_country=enrolment, total_enrolled=total, source_id="s",
    ), sites


def test_d2_implies_d1():
    cases = [
        _t({"Uganda": 100}, {"Uganda": 5, "USA": 4}, 1000),  # 5/9 sites African
        _t({"Kenya": 200, "USA": 0}, {"Kenya": 3, "USA": 0}, 200),
    ]
    for t, sites in cases:
        if classify_d2(t, sites):
            assert classify_d1(t, sites)


def test_d3_implies_d1():
    cases = [
        _t({"Uganda": 600, "USA": 400}, {"Uganda": 1, "USA": 5}, 1000),
        _t({"Kenya": 500, "USA": 500}, {"Kenya": 1, "USA": 1}, 1000),
    ]
    for t, sites in cases:
        if classify_d3(t, sites):
            assert classify_d1(t, sites)


def test_d2_d3_not_nested():
    # 2 African sites of 3 (D2 yes), but African enrolment <50% (D3 no).
    t, sites = _t({"Uganda": 50, "Kenya": 50, "USA": 900}, {"Uganda": 1, "Kenya": 1, "USA": 1}, 1000)
    assert classify_d2(t, sites) is True
    assert classify_d3(t, sites) is False
    # 1 African site of 5 (D2 no), but 60% African enrolment (D3 yes).
    t, sites = _t({"South Africa": 600, "USA": 400}, {"South Africa": 1, "USA": 4}, 1000)
    assert classify_d2(t, sites) is False
    assert classify_d3(t, sites) is True
