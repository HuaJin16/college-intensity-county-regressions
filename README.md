# County College Intensity Regressions (Cross-Sectional, U.S. Counties)

This repository supports a class-oriented, reproducible Python workflow to study whether counties with higher college intensity tend to have:

1. higher median gross rent
2. higher average weekly wage

This is an **associational cross-sectional analysis**. Results should be interpreted as conditional correlations, not causal effects.

## Project scope

- Unit of analysis: U.S. county (`county_fips`)
- One row per county in final analytical dataset
- Geography scope default: 50 states + DC + Puerto Rico (`us_50_dc_pr`)
- Cross-sectional only
- Baseline models are intentionally simple and economically grounded
- Robustness checks are clearly separated from baseline specifications

## Research objective

Estimate associations between county college intensity and:

- `median_gross_rent`
- `avg_weekly_wage`

Main regressor:

- `college_intensity = college_enrollment_total / population`
- preferred reporting scale: `college_intensity_pct = 100 * college_intensity`

## Default year alignment

Unless explicitly changed:

- ACS 5-year: 2020-2024
- QCEW annual county: 2024 (or nearest available, flagged)
- IPEDS institution-level enrollment/location: 2024 (or nearest available, flagged)

## Data sources

- ACS 5-year county data
- BLS QCEW county data
- IPEDS institution-level data
- County FIPS / metro crosswalk

Note: exact raw field names can vary by release. Uncertain fields should be labeled with `TODO_VERIFY_*`.

## ACS pull variables (initial extraction)

Use the Census ACS API to extract county-level variables used directly in baseline models or robustness checks:

- `population`: `B01003_001E`
- `median_gross_rent`: `B25064_001E`
- `median_household_income`: `B19013_001E`
- `poverty_rate`: `B17001_002E / B17001_001E`
- `renter_share`: `B25003_003E / (B25003_002E + B25003_003E)`
- `vacancy_rate`: `B25002_003E / B25002_001E` (vacancy proxy)
- `vacancy_proxy`: alias of `vacancy_rate`
- `ba_share`: `(B15003_022E + B15003_023E + B15003_024E + B15003_025E) / B15003_001E`

## Baseline variables

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

### Robustness-only controls
- `renter_share` or `vacancy_rate`
- `ba_share`
- `poverty_rate` (optional robustness; do not pair with median income in baseline rent model)

In this repository, the vacancy proxy is stored as `vacancy_rate` and duplicated as `vacancy_proxy` for naming clarity.

Do not include poverty rate alongside median income in the baseline rent model unless explicitly requested.

## Model specifications

Baseline rent model:

`ln_median_gross_rent ~ college_intensity_pct + ln_median_household_income + ln_population + metro + C(state_fips)`

Baseline wage model:

`ln_avg_weekly_wage ~ college_intensity_pct + ln_population + metro + industry_mix + C(state_fips)`

Inference defaults:

- Baseline: HC1 robust standard errors
- Robustness: standard errors clustered by state (`state_fips`)

## Merge and cleaning defaults

### FIPS standardization
- Cast to string
- Trim whitespace
- Remove non-digits
- Zero-pad to 5 digits
- Keep only valid 5-digit county FIPS

### Merge order
1. ACS county universe (master)
2. Left-merge QCEW by `county_fips`
3. Left-merge county-aggregated IPEDS by `county_fips`
4. Left-merge metro crosswalk by `county_fips`

### Geography scope and out-of-scope handling
- Default scope: ACS county universe restricted to 50 states + DC + Puerto Rico (`--geography-scope us_50_dc_pr`)
- Non-ACS-source county FIPS not in the ACS universe are excluded before merge and reported in merge QC
- Merge QC report default output: `data/intermediate/merge_qc_<YEAR>.md`

### Missing and suppressed handling
- ACS missing/sentinel values -> `NaN`
- QCEW suppression tokens (`N`, `*`, blanks, etc.) -> `NaN`
- If weekly wage missing and annual pay exists, set `avg_weekly_wage = annual_pay / 52`
- Otherwise do not impute outcomes or key controls

### Counties with no colleges
- Keep in sample
- Set `college_enrollment_total = 0`
- Therefore `college_intensity = 0`

### Sample inclusion
- Keep all counties in merged dataset
- Build model-specific complete-case samples
- Report rows dropped and stage of drop (no silent dropping)

### Logs
- Log only strictly positive values
- Nonpositive values become missing for that model sample

## Repository layout (recommended)

```text
.
├─ AGENTS.md
├─ README.md
├─ docs/
│  └─ PRD.md
├─ data/
│  ├─ raw/
│  ├─ intermediate/
│  └─ processed/
├─ src/
│  ├─ data/
│  │  ├─ 01_download_data.py
│  │  └─ 02_build_county_dataset.py
│  ├─ features/
│  └─ models/
│     └─ 03_run_models.py
├─ outputs/
│  ├─ tables/
│  ├─ figures/
│  └─ memos/
└─ notebooks/
```

## Python stack

Use lightweight, common libraries:

- `pandas`
- `numpy`
- `requests`
- `pathlib`
- `statsmodels`
- `matplotlib` (simple diagnostics only)

## Quick start

1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install pandas numpy requests statsmodels matplotlib`
   - or `pip install -r requirements.txt` (if present)
3. Set your ACS key (recommended):
   - Option A (PowerShell): `$env:ACS_API_KEY="<YOUR_KEY>"`
   - Option B (`.env`): copy `.env.example` to `.env` and set `ACS_API_KEY` there (auto-loaded by the build script)
4. Pull ACS county data first:

```bash
python src/data/02_build_county_dataset.py --year <ACS_YEAR> --acs-only
```

- Example used in this repo session: `python src/data/02_build_county_dataset.py --year 2024 --acs-only`
- The script auto-saves to `data/raw/acs_county_<ACS_YEAR>.csv` if `--output` is not provided.
- If `--year` is omitted, the script default is `2024`.

5. Place non-ACS source files in `data/raw/`.

- Exact QCEW 2024 download command used in this repository session:

```bash
python src/data/01_download_data.py --qcew-url "https://data.bls.gov/cew/data/files/2024/csv/2024_annual_singlefile.zip" --qcew-out data/raw/qcew_2024_annual_singlefile.zip --overwrite
```

- This download is then prepared into the default build input file: `data/raw/qcew_county.csv`.
- Build the canonical metro crosswalk from the QCEW County-MSA-CSA crosswalk using the baseline mapping:
  - `MSA` -> `metro = 1`
  - `MicroSA` or blank/unassigned CBSA -> `metro = 0`

```bash
python src/data/02_build_metro_crosswalk.py --input data/raw/qcew_county_msa_csa_crosswalk.txt --output data/raw/metro_crosswalk.csv --county-universe data/raw/acs_county_2024.csv
```

- `--county-universe data/raw/acs_county_2024.csv` ensures one row for every county in the ACS master county list; counties not present in the QCEW crosswalk are treated as non-CBSA (`metro = 0`).

6. After adding non-ACS sources and the model script, run scripts in order for full merged dataset + models:

```bash
python src/data/01_download_data.py --qcew-url "<QCEW_URL>" --ipeds-url "<IPEDS_URL>" --metro-url "<METRO_URL>"
python src/data/02_build_metro_crosswalk.py --input data/raw/qcew_county_msa_csa_crosswalk.txt --output data/raw/metro_crosswalk.csv --county-universe data/raw/acs_county_<YEAR>.csv
python src/data/02_build_county_dataset.py --year <YEAR> --qcew data/raw/qcew_county.csv --ipeds data/raw/ipeds_institutions.csv --metro data/raw/metro_crosswalk.csv --geography-scope us_50_dc_pr
python src/models/03_run_models.py --input data/processed/county_analysis_<YEAR>.csv --outdir outputs
```

## Current status

- Implemented now: ACS county extraction (`--acs-only`), raw download helper, metro crosswalk builder, ACS-universe merge validation with geography scope filtering, and `src/models/03_run_models.py` for baseline + robustness regressions.

## Expected outputs

- `data/processed/county_analysis_<YEAR>.csv` (default example: `data/processed/county_analysis_2024.csv`)
- `outputs/tables/baseline_rent.csv`
- `outputs/tables/baseline_wage.csv`
- `outputs/tables/robustness.csv`
- `outputs/memos/limitations.md`

## Minimum class deliverable

- one clean merged county dataset
- one baseline rent table
- one baseline wage table
- one robustness table
- one short limitations memo

## Open decisions to confirm

- Exact raw field names by source release
- Final metro/nonmetro definition source
- Final industry-mix control set in wage model
- Unresolved IPEDS county assignments
- Any instructor-required override to default geography scope (`us_50_dc_pr`)
