# Contributing to africa-hiv-prep-atlas

Thanks for your interest. The most-needed contribution right now is **a co-rater for the n=30 inter-rater-reliability (IRR) audit** that gates the v0.1.0 release.

## What this project is

A methodology-calibration audit. We took 20 published meta-analyses of long-acting HIV PrEP (cabotegravir, lenacapavir, dapivirine ring) and asked: *do the MAs accurately classify African-cohort trials?* Pre-IRR finding (working): **35% sensitivity (95% CI 15-60%)** at the D3 ground truth (>=50% African enrolment). MAs miss roughly two-thirds of actually-African long-acting PrEP trials.

The v0.1.0 release needs an independent human IRR audit before that headline can be reported as final.

## How to be the co-rater (estimated 60-90 min)

You will independently re-classify 30 randomly-sampled (MA, trial) pairs. Your work is **blinded** to the algorithmic answers. The two raters' answers are then compared via Cohen's kappa; the v0.1.0 release requires kappa >= 0.80 on both layers.

### Step 1: Open the verification UI

[https://mahmood726-cyber.github.io/africa-hiv-prep-atlas/outputs/verification.html](https://mahmood726-cyber.github.io/africa-hiv-prep-atlas/outputs/verification.html)

The page presents 30 pairs, one at a time. For each pair, you see:

- A short MA-side excerpt (verbatim quotes from the meta-analysis full text)
- A short trial-side excerpt (verbatim quotes from the primary publication)

You answer two yes/no questions:

1. **Did the MA classify this trial as African-cohort?** (Yes if any explicit count, table, or narrative mention names this trial in an Africa-context.)
2. **Is the trial actually African-cohort under D3?** (Yes if >=50% of trial enrolment is from African sites.)

You are blinded to the algorithmic answer. There is no "correct answer" displayed.

### Step 2: Export and send results

After answering all 30 pairs, click **Export JSON**. Save the output to a file (your name + date in the filename is fine, e.g. `irr_rater_X_2026-05-10.json`).

Send it to MA via email (mahmood726@gmail.com) or open a GitHub issue with the JSON attached. **Do not commit the JSON file directly to a public PR** until kappa is computed - that would unblind future auditors.

### Step 3: We compute kappa

```
python scripts/compute_kappa.py outputs/irr_rater_A.json outputs/irr_rater_X.json
```

Acceptance gate: claim_kappa >= 0.80 AND truth_kappa >= 0.80. If either is below 0.80, we discuss disagreements pair-by-pair, refine the protocol, increment to `prereg-v0.1.0-amend-2`, and re-run the audit (you would not be asked to redo it).

## What you'll be co-author on

A Synthesis Methods Note (~400 words) reporting the calibration headline. Author block to be confirmed at submission. The co-rater is acknowledged in the Methods section as the independent IRR rater. CRediT contribution: Validation, Investigation.

## Other contributions welcome

- Spot a bug in Layer-M extraction for a specific MA - file a GitHub issue with the (MA, trial) pair and the expected vs actual classification.
- Suggest an MA we missed - we searched PubMed only for v0.1.0; Cochrane CDSR and Epistemonikos searches are deferred to v0.2.0.
- Replicate the pipeline on a different therapeutic class (e.g., long-acting ART) - fork-and-adapt is encouraged.

## Code of conduct

Be kind. The Makerere E156 cohort and the broader African evidence-equity community are core stakeholders. Critique the methods, not the people.

## Questions

Open a GitHub issue or email mahmood726@gmail.com.
