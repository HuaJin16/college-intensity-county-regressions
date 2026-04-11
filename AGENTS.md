# AGENTS.md

## Purpose

This repository is a county-level, cross-sectional regression project studying associations between college intensity and two county outcomes:

1. Median gross rent
2. Average weekly wage

This is a class-oriented, reproducible Python workflow. Prioritize transparent, explainable empirical work over advanced causal methods.

## Non-Negotiable Framing

- Unit of analysis: U.S. county (`county_fips`)
- One row per county in the final analytical dataset
- Cross-sectional only
- Associational interpretation only (not causal)
- Keep baseline models simple and economically grounded
- Clearly separate baseline controls from robustness-only controls

## Research Objective

Estimate whether counties with higher college intensity tend to have:

- higher median gross rent
- higher average weekly wage

while conditioning on a small set of economically motivated controls.

Main explanatory variable:

- `college_intensity = college_enrollment_total / population`
- preferred reporting scale: `college_intensity_pct = 100 * college_intensity`

## Preferred Year Alignment (Default)

Unless explicitly changed by the user, use:

- ACS 5-year: 2018-2022
- QCEW annual county data: 2022
- IPEDS institution-level enrollment/location: 2022 (or nearest available, flagged)

If source years differ, state the assumption clearly and mark for human review.

## Data Sources

Use these sources when available:

- ACS 5-year county data
- BLS QCEW county data
- IPEDS institution-level data
- County FIPS/metro crosswalk data

Do not fabricate exact raw field names. If uncertain, mark as `TODO_VERIFY_*` and document what to check.

## Baseline Variables

### Outcomes
- `median_gross_rent` (ACS B25064)
- `avg_weekly_wage` (QCEW county)

### Main regressor
- `college_intensity_pct`

### Rent model baseline controls
- `ln_median_household_income`
- `ln_population`
- `metro`
- `C(state_fips)` state fixed effects

### Wage model baseline controls
- `ln_population`
- `metro`
- industry mix controls if feasible (for example `manuf_emp_share`, `leisure_emp_share`)
- `C(state_fips)` state fixed effects

## Robustness-Only Controls

Use as robustness checks, not baseline:
- `renter_share` or `vacancy_rate`
- `ba_share`

Do not include poverty rate alongside median income in the baseline rent model unless explicitly requested.

## Merge and Cleaning Rules (Required Defaults)

### FIPS standardization
- Cast to string
- Trim whitespace
- Remove non-digits
- Zero-pad to 5 digits
- Keep only valid 5-digit county FIPS

### Merge plan
1. Start from ACS county universe (master)
2. Left-merge QCEW by `county_fips`
3. Left-merge county-aggregated IPEDS by `county_fips`
4. Left-merge metro/nonmetro crosswalk by `county_fips`

### Counties with no colleges
- Keep in sample
- Set `college_enrollment_total = 0`
- Therefore `college_intensity = 0`

### Missing/suppressed values
- ACS missing/sentinel values -> `NaN`
- QCEW suppression tokens (`N`, `*`, blanks, etc.) -> `NaN`
- If weekly wage missing and annual pay exists, set `avg_weekly_wage = annual_pay / 52`
- Otherwise do not impute outcomes or key controls

### Sample inclusion
- Keep all counties in merged dataset
- Build model-specific complete-case samples for regressions
- Do not silently drop rows; report counts dropped and stage of drop

### Log transforms
- Only log strictly positive values
- Nonpositive values become missing for that model sample

## Regression Specifications

### Baseline rent model
`ln_median_gross_rent ~ college_intensity_pct + ln_median_household_income + ln_population + metro + C(state_fips)`

### Baseline wage model
`ln_avg_weekly_wage ~ college_intensity_pct + ln_population + metro + industry_mix + C(state_fips)`

### Inference defaults
- Baseline: HC1 robust SE
- Robustness: cluster by state (`state_fips`)

## Required Script Workflow

Preferred script order:

1. `src/data/01_download_data.py` (optional download helper)
2. `src/data/02_build_county_dataset.py` (build merged county dataset)
3. `src/models/03_run_models.py` (run baseline + robustness regressions)

## Expected Outputs

- `data/processed/county_analysis_2022.csv`
- `outputs/tables/baseline_rent.csv`
- `outputs/tables/baseline_wage.csv`
- `outputs/tables/robustness.csv`
- `outputs/memos/limitations.md`

## Coding Standards for Agents

- Use: `pandas`, `numpy`, `requests`, `pathlib`, `statsmodels`, `matplotlib` (simple diagnostics only)
- Prefer modular scripts over notebook-only workflows
- Keep functions small and readable
- Add comments only for non-obvious logic
- Avoid overengineering and heavy frameworks

## Out of Scope (Unless Explicitly Requested)

- IV designs
- Panel models
- DiD/event-study
- Spatial econometrics as core method
- ML prediction framing

These can be mentioned only as limitations or future work.

## Interpretation Rules

Never present coefficients as causal effects.
Use language like "associated with" and "conditional correlation."

## Open Decisions to Flag for Human Review

- exact raw field names by source release
- final metro/nonmetro definition source
- final industry-mix control set in wage model
- unresolved IPEDS county assignments
- geography coverage choices (for example territories inclusion)
