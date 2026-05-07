# African HIV PrEP/PEP Long-Acting Trial Atlas

> Methodology-calibration audit: do meta-analyses of long-acting HIV PrEP modalities accurately classify African-cohort trials?

**Status:** v0.1.0 (in development).
**Spec:** [`docs/superpowers/specs/2026-05-07-africa-hiv-prep-atlas-design.md`](docs/superpowers/specs/2026-05-07-africa-hiv-prep-atlas-design.md).
**Plan:** [`docs/superpowers/plans/2026-05-07-africa-hiv-prep-atlas-v0.1.0-plan.md`](docs/superpowers/plans/2026-05-07-africa-hiv-prep-atlas-v0.1.0-plan.md).

## Headline calibration

Across N (MA, trial) pairs, MAs of long-acting HIV PrEP classified African-cohort trials with X% sensitivity / Y% specificity vs the ground-truth definition (≥50% enrolment from African sites).

## Quick start

```
pip install -e .
python scripts/preflight.py
python scripts/build_atlas.py
pytest -q
```

## Layout

- `src/africa_hiv_prep_atlas/` — pipeline modules
- `fixtures/` — committed source-line-attributed extraction fixtures
- `data/` — generated CSVs (atlas.csv pinned byte-for-byte)
- `outputs/` — dashboard.html, verification.html, extraction_audit.md
- `prereg/` — frozen spec snapshots per release tag
- `.ots/` — OpenTimestamps proof files

## License

MIT.
