# Fixture Seeding Protocol — africa-hiv-prep-atlas v0.1.0

This document is the USER ACTION handoff for Tasks 13 and 14 of the v0.1.0 plan.
The pipeline (Tasks 0-12) is complete; what remains is the empirical data extraction.

## Task 13 — Trial fixtures (≥6)

For each long-acting HIV PrEP trial in scope, create
`fixtures/trials/<trial_id>.json` matching this schema:

```json
{
  "trial_id": "HPTN_084",
  "nct": "NCT03164564",
  "pactr": null,
  "modality": "cabotegravir-LA",
  "year": 2020,
  "enrolment_by_country": { "South Africa": 0, "Uganda": 0, "..." },
  "sites_by_country": { "South Africa": 0, "Uganda": 0, "..." },
  "total_enrolled": 0,
  "source_id": "delany-moretlwe-2022-lancet",
  "verbatim_excerpts": [
    {
      "source_id": "delany-moretlwe-2022-lancet-table1",
      "locator": "Table 1, p. e1335",
      "text": "VERBATIM TEXT FROM PUBLICATION"
    }
  ]
}
```

### Required trials (v0.1.0 acceptance: ≥6)

- `HPTN_083` — Landovitz et al., NEJM 2021 (cabotegravir-LA, MSM/TGW, sites in Argentina/Brazil/Peru/USA/Vietnam/Thailand/South Africa)
- `HPTN_084` — Delany-Moretlwe et al., Lancet 2022 (cabotegravir-LA, cisgender women in 7 African countries)
- `ASPIRE` (MTN-020) — Baeten et al., NEJM 2016 (dapivirine ring, 4 African countries)
- `RING_STUDY` (IPM 027) — Nel et al., NEJM 2016 (dapivirine ring, African sites)
- `MTN_025_HOPE` — Baeten et al., JID 2021 (dapivirine ring open-label extension)
- One more from PURPOSE-1 / PURPOSE-2 / lenacapavir programmes if data is available

### Guards (enforced by tests)

- All `verbatim_excerpts[*].text` must be a real quote from the cited publication. No paraphrase.
- `total_enrolled >= sum(enrolment_by_country.values())` (slack permitted for un-allocated enrolment).
- Every fixture must classify under at least D1 (≥1 African site) — this is part of the v0.1.0 inclusion criterion.

## Task 14 — MA fixtures (≥10 MAs, ≥50 (MA, trial) pairs)

For each long-acting PrEP MA published 2020+, create directory
`fixtures/mas/<ma_id>/` with two files:

### meta.json

```json
{
  "ma_id": "smith2024-cabotegravir-prep",
  "first_author": "Smith",
  "year": 2024,
  "doi": "10.xxxx/yyyy",
  "pmid": "12345678",
  "search_date": "2026-05-15",
  "cited_trial_ids": ["HPTN_083", "HPTN_084", "PURPOSE_1"],
  "full_text_source_id": "smith2024_pdf_oa",
  "search_strategy_excerpt": {
    "source_id": "smith2024-methods",
    "locator": "Methods §2.1 p.3",
    "text": "VERBATIM SEARCH STRING"
  }
}
```

### claims.json

```json
{
  "ma_id": "smith2024-cabotegravir-prep",
  "claims": {
    "HPTN_084": {
      "a": false,
      "b": true,
      "c": true,
      "source_lines": ["smith2024-table2-p5", "smith2024-discussion-p9"],
      "verbatim_quotes": [
        {"source_id": "smith2024-table2-p5", "text": "HPTN 084 (South Africa, Uganda, ...)"},
        {"source_id": "smith2024-discussion-p9", "text": "...findings from HPTN 084 in sub-Saharan Africa..."}
      ]
    }
  }
}
```

Layer `a` = explicit count claim. `b` = implicit-from-table. `c` = narrative. Each TRUE
boolean MUST be backed by a `verbatim_quotes` entry. `cited_trial_ids` in meta.json must
be a subset of the trial fixtures created in Task 13.

### Search strategy

Search Cochrane CDSR + PubMed + Epistemonikos for MAs of long-acting HIV PrEP modalities
published 2020-01-01 onwards. Inclusion criteria:
1. Title or abstract names a long-acting modality
2. Reports a pooled effect estimate from ≥2 trials
3. Full text accessible

Document the search strings + record counts in `docs/prisma_flow.md`.
