"""Layer-M (MA-claim) extraction from committed MA fixtures."""
from __future__ import annotations

VALID_LAYERS = ("a", "b", "c")


def extract_layer_m_from_fixture(fixture: dict) -> list[dict]:
    out: list[dict] = []
    for trial_id, raw in fixture.get("claims", {}).items():
        out.append({
            "ma_id": fixture["ma_id"],
            "trial_id": trial_id,
            "claimed_a": bool(raw.get("a", False)),
            "claimed_b": bool(raw.get("b", False)),
            "claimed_c": bool(raw.get("c", False)),
            "source_lines": tuple(raw.get("source_lines", ())),
        })
    return out


def layer_stripped_union(row: dict, layers: tuple) -> bool:
    if not layers:
        return False
    for L in layers:
        if L not in VALID_LAYERS:
            raise ValueError(f"unknown layer {L!r}; valid: {VALID_LAYERS}")
    return any(row.get(f"claimed_{L}", False) for L in layers)
