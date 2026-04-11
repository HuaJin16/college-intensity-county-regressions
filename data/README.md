# Data Directory Guide

This project keeps code and documentation in git, while raw and generated data files are ignored by default.

## Directory purpose

- `data/raw/`: source files exactly as downloaded
- `data/intermediate/`: optional temporary files from cleaning/reshaping
- `data/processed/`: final merged county-level analysis dataset(s)

Only `.gitkeep` placeholders are tracked in these folders by default.

## Expected raw files (default names)

Place these files in `data/raw/` unless you pass custom paths at runtime:

- `qcew_county.csv`: BLS QCEW county file for wages/employment
- `ipeds_institutions.csv`: IPEDS institution-level enrollment/location file
- `metro_crosswalk.csv`: county metro/nonmetro crosswalk file

## ACS input

ACS 5-year county variables are pulled from the Census API in the build script. If needed, set `ACS_API_KEY` as an environment variable.

## Recommended source alignment

- ACS 5-year: 2018-2022
- QCEW county annual: 2022
- IPEDS institution-level: 2022 (or nearest available, clearly flagged)

## Run order

1. Optional download helper:

```bash
python src/data/01_download_data.py --qcew-url "<QCEW_URL>" --ipeds-url "<IPEDS_URL>" --metro-url "<METRO_URL>"
```

2. Build merged county dataset:

```bash
python src/data/02_build_county_dataset.py --year 2022 --qcew data/raw/qcew_county.csv --ipeds data/raw/ipeds_institutions.csv --metro data/raw/metro_crosswalk.csv --output data/processed/county_analysis_2022.csv
```

## Notes on field names

Raw column names can vary by release. If a name is uncertain, use a `TODO_VERIFY_*` placeholder and document the exact field to confirm.
