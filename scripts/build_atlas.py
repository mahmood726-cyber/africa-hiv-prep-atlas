"""Build trials.csv, mas.csv, atlas.csv from committed fixtures."""
from __future__ import annotations

import csv as _csv
import io
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from africa_hiv_prep_atlas.records import Trial
from africa_hiv_prep_atlas.ground_truth import classify_trial
from africa_hiv_prep_atlas.confidence import classify_confidence, Confidence
from africa_hiv_prep_atlas.csv_writers import (
    write_atlas_csv, write_trials_csv, write_mas_csv,
)
from africa_hiv_prep_atlas.bootstrap import (
    cluster_bootstrap_sens_spec, permutation_sens_spec, choose_method, sweep_definitions,
)
from africa_hiv_prep_atlas.dashboard import render_dashboard
from africa_hiv_prep_atlas.verification import render_verification_ui

TRIAL_FIXTURES = REPO / "fixtures" / "trials"
MA_FIXTURES = REPO / "fixtures" / "mas"
DATA = REPO / "data"


def load_trials() -> tuple[list[dict], dict]:
    trials_records: list[dict] = []
    truth_by_trial: dict[str, dict] = {}
    for f in sorted(TRIAL_FIXTURES.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        t = Trial(
            trial_id=d["trial_id"], nct=d["nct"], pactr=d["pactr"],
            modality=d["modality"], year=d["year"],
            enrolment_by_country=d["enrolment_by_country"],
            total_enrolled=d["total_enrolled"], source_id=d["source_id"],
        )
        flags = classify_trial(t, d["sites_by_country"])
        trials_records.append({
            "trial_id": t.trial_id, "nct": t.nct or "", "pactr": t.pactr or "",
            "modality": t.modality, "year": t.year,
            "total_enrolled": t.total_enrolled,
            "african_n": t.african_n(),
            "african_fraction": round(t.african_fraction(), 4),
            "truth_d1": flags["d1"], "truth_d2": flags["d2"], "truth_d3": flags["d3"],
            "source_id": t.source_id,
        })
        truth_by_trial[t.trial_id] = flags
    return trials_records, truth_by_trial


def load_mas_and_atlas(truth_by_trial: dict) -> tuple[list[dict], list[dict]]:
    mas_records: list[dict] = []
    atlas_rows: list[dict] = []
    for d in sorted(p for p in MA_FIXTURES.iterdir() if p.is_dir()):
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        claims = json.loads((d / "claims.json").read_text(encoding="utf-8"))
        mas_records.append({
            "ma_id": meta["ma_id"], "first_author": meta["first_author"],
            "year": meta["year"], "n_cited_trials": len(meta["cited_trial_ids"]),
            "search_date": meta["search_date"],
            "full_text_source_id": meta["full_text_source_id"],
        })
        for trial_id, layers in claims["claims"].items():
            truth = truth_by_trial.get(trial_id, {"d1": False, "d2": False, "d3": False})
            atlas_rows.append({
                "ma_id": meta["ma_id"], "trial_id": trial_id,
                "claimed_a": bool(layers.get("a", False)),
                "claimed_b": bool(layers.get("b", False)),
                "claimed_c": bool(layers.get("c", False)),
                "truth_d1": truth["d1"], "truth_d2": truth["d2"], "truth_d3": truth["d3"],
                # Layer-M is manual-only in v0.1.0 -> high confidence (with verbatim quote).
                "confidence_layer_m": Confidence.HIGH.value,
                # Layer-T is manual-only in v0.1.0 -> high confidence.
                "confidence_layer_t": Confidence.HIGH.value,
                "source_lines": tuple(layers.get("source_lines", ())),
            })
    return mas_records, atlas_rows


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    trials_records, truth_by_trial = load_trials()
    mas_records, atlas_rows = load_mas_and_atlas(truth_by_trial)

    with (DATA / "trials.csv").open("w", encoding="utf-8", newline="") as f:
        write_trials_csv(trials_records, f)
    with (DATA / "mas.csv").open("w", encoding="utf-8", newline="") as f:
        write_mas_csv(mas_records, f)
    with (DATA / "atlas.csv").open("w", encoding="utf-8", newline="") as f:
        write_atlas_csv(atlas_rows, f)
    print(f"wrote {len(trials_records)} trials, {len(mas_records)} MAs, "
          f"{len(atlas_rows)} (MA, trial) pairs")

    # Generate dashboard.html
    method = choose_method(atlas_rows)
    fn = cluster_bootstrap_sens_spec if method == "clustered_bootstrap" else permutation_sens_spec
    headline = fn(atlas_rows, n_reps=1000, seed=42)

    # Pre-specified sensitivity sweep (D1/D2/D3) -- spec §3, no inferential adjustment.
    sweep = sweep_definitions(atlas_rows, n_reps=1000, seed=42)

    # Re-derive enriched rows (with claimed_union + cell flags) for the dashboard.
    buf = io.StringIO()
    write_atlas_csv(atlas_rows, buf)
    buf.seek(0)
    enriched = [
        {**r, **{k: r[k] == "True" for k in (
            "claimed_a", "claimed_b", "claimed_c", "claimed_union",
            "truth_d1", "truth_d2", "truth_d3",
            "tp_at_d3", "fp_at_d3", "fn_at_d3", "tn_at_d3",
        )}}
        for r in _csv.DictReader(buf)
    ]
    (REPO / "outputs").mkdir(parents=True, exist_ok=True)
    (REPO / "outputs" / "dashboard.html").write_text(
        render_dashboard(enriched, headline, sweep=sweep), encoding="utf-8",
    )
    print(f"wrote outputs/dashboard.html (method={headline['method']})")
    for defn in ("d1", "d2", "d3"):
        d = sweep[defn]
        lo_s, hi_s = d["sens_ci"]
        lo_p, hi_p = d["spec_ci"]
        print(
            f"  sweep {defn.upper()}: sens={d['sensitivity']:.2f} ({lo_s:.2f}-{hi_s:.2f})"
            f"  spec={d['specificity']:.2f} ({lo_p:.2f}-{hi_p:.2f})"
        )

    # Generate verification.html
    verification_pairs: list[dict] = []
    for d in sorted(p for p in MA_FIXTURES.iterdir() if p.is_dir()):
        claims = json.loads((d / "claims.json").read_text(encoding="utf-8"))
        for trial_id, layers in claims["claims"].items():
            ma_quotes = layers.get("verbatim_quotes", [])
            trial_path = TRIAL_FIXTURES / f"{trial_id}.json"
            if trial_path.exists():
                tdata = json.loads(trial_path.read_text(encoding="utf-8"))
                trial_quotes = tdata.get("verbatim_excerpts", [])
            else:
                trial_quotes = []
            verification_pairs.append({
                "ma_id": claims["ma_id"], "trial_id": trial_id,
                "ma_quotes": ma_quotes, "trial_quotes": trial_quotes,
            })

    # Random n=30 sample, seeded.
    rng = random.Random(20260507)
    n_sample = min(30, len(verification_pairs))
    audit_sample = rng.sample(verification_pairs, n_sample) if verification_pairs else []

    (REPO / "outputs" / "verification.html").write_text(
        render_verification_ui(audit_sample, rater_id="REPLACE_AT_RUNTIME"),
        encoding="utf-8",
    )
    print(f"wrote outputs/verification.html (n={n_sample} pairs)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
