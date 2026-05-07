from africa_hiv_prep_atlas.records import Trial
from africa_hiv_prep_atlas.ground_truth import classify_trial, classify_d1, classify_d2, classify_d3


def _trial(enrolment, sites_by_country, total):
    return Trial(
        trial_id="X", nct=None, pactr=None, modality="x", year=2020,
        enrolment_by_country=enrolment, total_enrolled=total, source_id="src",
    ), sites_by_country


def test_d1_one_african_site_qualifies():
    t, sites = _trial({"South Africa": 100}, {"South Africa": 1, "USA": 5}, 1000)
    assert classify_d1(t, sites) is True


def test_d1_zero_african_sites_fails():
    t, sites = _trial({"USA": 1000}, {"USA": 5}, 1000)
    assert classify_d1(t, sites) is False


def test_d2_at_50_percent_sites():
    t, sites = _trial({"Kenya": 200}, {"Kenya": 3, "USA": 3}, 800)
    assert classify_d2(t, sites) is True
    t, sites = _trial({"Kenya": 200}, {"Kenya": 2, "USA": 4}, 800)
    assert classify_d2(t, sites) is False


def test_d3_at_50_percent_enrolment():
    t, sites = _trial({"Uganda": 600, "USA": 400}, {"Uganda": 1, "USA": 1}, 1000)
    assert classify_d3(t, sites) is True
    t, sites = _trial({"Uganda": 400, "USA": 600}, {"Uganda": 1, "USA": 1}, 1000)
    assert classify_d3(t, sites) is False


def test_d3_exactly_50_percent_qualifies():
    t, sites = _trial({"Kenya": 500, "USA": 500}, {"Kenya": 1, "USA": 1}, 1000)
    assert classify_d3(t, sites) is True


def test_classify_trial_returns_all_three_flags():
    t, sites = _trial({"South Africa": 700, "USA": 300}, {"South Africa": 4, "USA": 2}, 1000)
    res = classify_trial(t, sites)
    assert res == {"d1": True, "d2": True, "d3": True}


def test_classify_trial_zero_enrolment_returns_all_false():
    t, sites = _trial({}, {"USA": 5}, 0)
    res = classify_trial(t, sites)
    assert res == {"d1": False, "d2": False, "d3": False}
