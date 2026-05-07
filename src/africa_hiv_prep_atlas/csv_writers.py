"""Deterministic CSV writers for atlas / trials / mas."""
from __future__ import annotations

import csv
from typing import IO

ATLAS_COLUMNS = (
    "ma_id", "trial_id",
    "claimed_a", "claimed_b", "claimed_c", "claimed_union",
    "truth_d1", "truth_d2", "truth_d3",
    "tp_at_d3", "fp_at_d3", "fn_at_d3", "tn_at_d3",
    "confidence_layer_m", "confidence_layer_t",
    "source_lines",
)

TRIALS_COLUMNS = (
    "trial_id", "nct", "pactr", "modality", "year",
    "total_enrolled", "african_n", "african_fraction",
    "truth_d1", "truth_d2", "truth_d3", "source_id",
)

MAS_COLUMNS = (
    "ma_id", "first_author", "year", "n_cited_trials",
    "search_date", "full_text_source_id",
)


def _serialise_source_lines(value) -> str:
    if not value:
        return ""
    return ";".join(value)


def write_atlas_csv(rows: list[dict], stream: IO[str]) -> None:
    enriched: list[dict] = []
    for r in rows:
        cl = bool(r.get("claimed_a") or r.get("claimed_b") or r.get("claimed_c"))
        tr = bool(r["truth_d3"])
        enriched.append({
            "ma_id": r["ma_id"], "trial_id": r["trial_id"],
            "claimed_a": r["claimed_a"], "claimed_b": r["claimed_b"], "claimed_c": r["claimed_c"],
            "claimed_union": cl,
            "truth_d1": r["truth_d1"], "truth_d2": r["truth_d2"], "truth_d3": r["truth_d3"],
            "tp_at_d3": cl and tr,
            "fp_at_d3": cl and not tr,
            "fn_at_d3": (not cl) and tr,
            "tn_at_d3": (not cl) and (not tr),
            "confidence_layer_m": r["confidence_layer_m"],
            "confidence_layer_t": r["confidence_layer_t"],
            "source_lines": _serialise_source_lines(r["source_lines"]),
        })
    enriched.sort(key=lambda x: (x["ma_id"], x["trial_id"]))
    w = csv.DictWriter(stream, fieldnames=list(ATLAS_COLUMNS), lineterminator="\n")
    w.writeheader()
    for row in enriched:
        w.writerow(row)


def write_trials_csv(trials: list[dict], stream: IO[str]) -> None:
    sorted_rows = sorted(trials, key=lambda x: x["trial_id"])
    w = csv.DictWriter(stream, fieldnames=list(TRIALS_COLUMNS), lineterminator="\n")
    w.writeheader()
    for r in sorted_rows:
        w.writerow({k: r.get(k, "") for k in TRIALS_COLUMNS})


def write_mas_csv(mas: list[dict], stream: IO[str]) -> None:
    sorted_rows = sorted(mas, key=lambda x: x["ma_id"])
    w = csv.DictWriter(stream, fieldnames=list(MAS_COLUMNS), lineterminator="\n")
    w.writeheader()
    for r in sorted_rows:
        w.writerow({k: r.get(k, "") for k in MAS_COLUMNS})
