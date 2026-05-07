# Prereg CHANGELOG — v0.1.0-amend-1

> Extraction freeze prior to n=30 blinded IRR audit (Task 20).
> Snapshot date: 2026-05-07.

## Purpose

This directory records the algorithmic Layer-M extraction state before the
n=30 blinded IRR audit (Task 20 — USER ACTION). Files here are frozen;
amendments require a new `prereg-v0.1.0-amend-N` tag.

## Spec changes vs v0.0.1

None — spec content is unchanged from `prereg-v0.0.1`. The spec file is
copied verbatim from `docs/superpowers/specs/2026-05-07-africa-hiv-prep-atlas-design.md`.
`sentinel:skip-file` prepended as line 1 to suppress hardcoded-path BLOCK
(Sentinel exempts `docs/superpowers/specs/**` but not `prereg/**`).

## Extraction counts

- 20 unique MAs
- 54 (MA, trial) pairs across 7 LA-PrEP trial fixtures
- 7 trials: HPTN_083, HPTN_084, ASPIRE/MTN-020, RING_STUDY/IPM-027,
  MTN_025_HOPE, PURPOSE_1, PURPOSE_2

## Pre-IRR headline numbers

**Sensitivity: 35% (95% CI 15–60%)**
**Specificity: 71% (95% CI 44–94%)**
D3 ground truth: ≥50% enrolment from African sites.
Method: clustered bootstrap, n_clusters=20.

Confusion matrix:
- TP = 13  (MA classifies trial as African; trial IS African)
- FP =  5  (MA classifies trial as African; trial is NOT African)
- FN = 24  (MA does NOT classify trial as African; trial IS African)
- TN = 12  (MA does NOT classify trial as African; trial is NOT African)

Calibration finding: MAs systematically under-detect African-cohort
coverage. 65% of actually-African long-acting PrEP trials (24/37) are cited
but NOT classified as African across any of three Layer-M layers (explicit
count, table, narrative).

These are working numbers — final values pending κ ≥ 0.80 dual-rater audit
(Task 20).

## OTS stamp status

DEFERRED — Python 3.13 env hits the opentimestamps-client 0.7.2 +
python-bitcoinlib SSL-loader bug (looks for legacy `libeay32.dll`).
See `prereg/v0.0.1/README.md` for resolution paths.
