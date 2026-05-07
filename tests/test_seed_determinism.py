"""Unit tests for seed determinism in bootstrap."""
from africa_hiv_prep_atlas.bootstrap import cluster_bootstrap_sens_spec


def _rows():
    return [
        {"ma_id": f"M{i}", "trial_id": f"T{j}",
         "claimed_a": (i + j) % 2 == 0, "claimed_b": False, "claimed_c": False,
         "truth_d1": j % 2 == 0, "truth_d2": j % 2 == 0, "truth_d3": j % 2 == 0}
        for i in range(12) for j in range(6)
    ]


def test_seed_42_reproducible():
    a = cluster_bootstrap_sens_spec(_rows(), n_reps=200, seed=42)
    b = cluster_bootstrap_sens_spec(_rows(), n_reps=200, seed=42)
    assert a["sens_ci"] == b["sens_ci"]
    assert a["spec_ci"] == b["spec_ci"]


def test_different_seeds_differ():
    a = cluster_bootstrap_sens_spec(_rows(), n_reps=200, seed=42)
    b = cluster_bootstrap_sens_spec(_rows(), n_reps=200, seed=43)
    assert a["sens_ci"] != b["sens_ci"]
