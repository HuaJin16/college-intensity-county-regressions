# Data Directory Guide

This project keeps code and documentation in git, while raw and generated data files are ignored by default.

## Directory purpose

- `data/raw/`: source files exactly as downloaded
- `data/intermediate/`: optional temporary files from cleaning/reshaping
- `data/processed/`: final merged county-level analysis dataset(s)

Only `.gitkeep` placeholders are tracked in these folders by default.

## Expected raw files (default names)

Place these files in `data/raw/` unless you pass custom paths at runtime:

- `acs_county_2024.csv`: ACS county extract built from Census API (default-year filename)
- `qcew_county.csv`: BLS QCEW county file for wages/employment
- `ipeds_institutions.csv`: IPEDS institution-level enrollment/location file
- `qcew_county_msa_csa_crosswalk.txt` (or `.csv`): raw QCEW county-MSA-CSA crosswalk source
- `metro_crosswalk.csv`: canonical county metro/nonmetro file used in model merges

## Metro mapping from QCEW county-MSA-CSA crosswalk

Use `src/data/02_build_metro_crosswalk.py` to convert the raw crosswalk into `data/raw/metro_crosswalk.csv`.

Exact mapping used for baseline control:

- CBSA title contains `MSA` (metropolitan) -> `metro = 1`
- CBSA title contains `MicroSA` or is blank/unassigned -> `metro = 0`

Command:

```bash
python src/data/02_build_metro_crosswalk.py --input data/raw/qcew_county_msa_csa_crosswalk.txt --output data/raw/metro_crosswalk.csv --county-universe data/raw/acs_county_2024.csv
```

Using `--county-universe` is recommended when you want `metro_crosswalk.csv` to contain every county in your ACS master list. Any county not listed in the QCEW crosswalk is assigned `cbsa_type = none` and `metro = 0`.

## ACS input

ACS 5-year county variables are pulled from the Census API in `src/data/02_build_county_dataset.py`.

Vacancy proxy naming: the output includes both `vacancy_rate` and `vacancy_proxy` (alias).

If needed, set `ACS_API_KEY` as an environment variable:

```bash
# PowerShell
$env:ACS_API_KEY="<YOUR_KEY>"
```

Or use `.env` in the repository root:

```bash
# PowerShell
Copy-Item .env.example .env
# then set ACS_API_KEY in .env
```

`src/data/02_build_county_dataset.py` auto-loads `.env` when present.

To build ACS-only county data first:

```bash
python src/data/02_build_county_dataset.py --year 2024 --acs-only --output data/raw/acs_county_2024.csv
```

If `--year` is omitted, the script default is `2024`.

Default geography scope in `02_build_county_dataset.py` is `us_50_dc_pr` (50 states + DC + Puerto Rico). Non-ACS-source county FIPS outside that ACS universe are excluded before merge and logged.

## Recommended source alignment

- ACS 5-year: 2020-2024
- QCEW county annual: 2024 (or nearest available, clearly flagged)
- IPEDS institution-level: 2024 (or nearest available, clearly flagged)

## Run order

1. Optional download helper:

```bash
python src/data/01_download_data.py --qcew-url "<QCEW_URL>" --ipeds-url "<IPEDS_URL>" --metro-url "<METRO_URL>"
```

2. Build merged county dataset:

```bash
python src/data/02_build_county_dataset.py --year 2024 --qcew data/raw/qcew_county.csv --ipeds data/raw/ipeds_institutions.csv --metro data/raw/metro_crosswalk.csv --acs-out data/raw/acs_county_2024.csv --output data/processed/county_analysis_2024.csv --geography-scope us_50_dc_pr
```

By default, a merge QC report is written to `data/intermediate/merge_qc_2024.md` (or `merge_qc_<year>.md`). Override with `--qc-out` if needed.

The processed county dataset now includes `has_college = 1[college_enrollment_total > 0]` for extensive-margin analysis.

Regression execution is available via `src/models/03_run_models.py` and writes outputs to `outputs/tables/`, `outputs/figures/`, and `outputs/memos/`, including `outputs/tables/margin_decomposition.csv` for the extensive/intensive decomposition.

## Notes on field names

Raw column names can vary by release. If a name is uncertain, use a `TODO_VERIFY_*` placeholder and document the exact field to confirm.
