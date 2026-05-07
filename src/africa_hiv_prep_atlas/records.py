"""Frozen dataclass records for trials, MAs, and atlas rows."""
from __future__ import annotations

from dataclasses import dataclass

from africa_hiv_prep_atlas.countries import is_african


@dataclass(frozen=True)
class Trial:
    trial_id: str
    nct: str | None
    pactr: str | None
    modality: str
    year: int
    enrolment_by_country: dict
    total_enrolled: int
    source_id: str

    def african_n(self) -> int:
        return sum(n for c, n in self.enrolment_by_country.items() if is_african(c))

    def african_fraction(self) -> float:
        if self.total_enrolled <= 0:
            return 0.0
        return self.african_n() / self.total_enrolled


@dataclass(frozen=True)
class MA:
    ma_id: str
    first_author: str
    year: int
    cited_trial_ids: tuple
    full_text_source_id: str


@dataclass(frozen=True)
class AtlasRow:
    ma_id: str
    trial_id: str
    claimed_a: bool
    claimed_b: bool
    claimed_c: bool
    truth_d1: bool
    truth_d2: bool
    truth_d3: bool
    confidence_layer_m: str
    confidence_layer_t: str
    source_lines: tuple

    def claimed_union(self) -> bool:
        return self.claimed_a or self.claimed_b or self.claimed_c

    def tp_at_d3(self) -> bool:
        return self.claimed_union() and self.truth_d3

    def fp_at_d3(self) -> bool:
        return self.claimed_union() and not self.truth_d3

    def fn_at_d3(self) -> bool:
        return (not self.claimed_union()) and self.truth_d3

    def tn_at_d3(self) -> bool:
        return (not self.claimed_union()) and (not self.truth_d3)
