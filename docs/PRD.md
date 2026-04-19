# County-Level Cross-Sectional Regression Project PRD

## 1) PRD

### Research objective
- Estimate whether U.S. counties with higher college intensity have higher:
  1) median gross rent, and
  2) average weekly wage.
- This is an associational cross-sectional study, not a causal identification design.

### Economic motivation
- Counties with more college enrollment may have stronger housing demand (students, staff, local services), which can be associated with higher rents.
- College-concentrated counties may also have labor-market characteristics (human capital concentration, sectoral mix, agglomeration) associated with higher wages.
- The project aims for transparent, economically grounded conditioning variables that are easy to explain in class.

### Unit of analysis
- county-level geographic unit identified by `county_fips`
- One row per county in the final analytical dataset.

### Main explanatory variable
- `college_intensity = county_college_enrollment / county_population`
- Enrollment comes from institution-level IPEDS records aggregated to county.
- Counties with no colleges remain in sample with `college_enrollment_total = 0`.
- Extended decomposition variable: `has_college = 1[college_enrollment_total > 0]`.

### Primary outcomes
1. `median_gross_rent` (ACS 5-year, table B25064)
2. `avg_weekly_wage` (BLS QCEW county)

### Baseline controls

#### Rent model
- `ln_median_household_income`
- `ln_population`
- `metro` indicator
- `C(state_fips)` state fixed effects

#### Wage model
- `ln_population`
- `metro` indicator
- `industry_mix` controls from QCEW if feasible
- `C(state_fips)` state fixed effects

### Baseline exclusions
- Do not include poverty rate alongside median income in the baseline rent model.
- Do not include bachelor share in baseline; allow only as robustness.

### Baseline model forms
- `ln(MedianRent_i) ~ CollegeIntensity_i + ln(MedianIncome_i) + ln(Population_i) + Metro_i + StateFE`
- `ln(AvgWeeklyWage_i) ~ CollegeIntensity_i + ln(Population_i) + Metro_i + IndustryMix_i + StateFE`

### Sample construction
- Recommended reference year: 2024 for all sources where possible.
  - ACS 5-year: 2020-2024
  - QCEW: 2024 annual county data (or nearest available)
  - IPEDS: 2024 enrollment/location file (or nearest available)
- Geography scope default: 50 states + DC (`us_50_dc`) based on ACS county universe.
- Start from ACS county universe, then merge in QCEW, aggregated IPEDS, and metro crosswalk by county FIPS.
- Exclude non-ACS-source county FIPS outside the ACS universe before merge and report dropped out-of-scope counties.
- Build model-specific complete-case samples.

### Threats to validity and limitations
- Omitted variable bias (amenities, local policy, regulation, productivity shocks).
- Industry composition misspecification in the wage model.
- Possible post-treatment controls if not careful (for example bachelor share).
- Spatial correlation across neighboring counties.
- Measurement error in county assignment for institutions.
- Potential sample selection from suppressed QCEW values.
- Reverse directionality and simultaneity concerns.
- Results must be interpreted as associations, not causal effects.

---

## 2) Implementation plan (Python)

Current implementation checkpoint: ACS extraction (`--acs-only`), raw download helper, metro crosswalk builder, ACS-universe merge validation with geography-scope filtering, and the regression runner (`src/models/03_run_models.py`) are implemented.

### Script layout

1. `src/data/01_download_data.py`
- Purpose: Optional helper to download raw files via URL using `requests`.
- Inputs: URL arguments for QCEW, IPEDS, metro crosswalk.
- Outputs: files in `data/raw/`.

2. `src/data/02_build_county_dataset.py`
- Purpose: Build one merged county dataset.
- Tasks:
  - Pull ACS county data from Census API.
  - Support an ACS-only extraction mode for first-pass data pull.
  - Load QCEW/IPEDS/metro raw files.
  - Standardize county FIPS.
  - Aggregate IPEDS to county enrollment.
  - Merge ACS + QCEW + IPEDS + metro.
  - Construct derived variables and logs.
  - Export final dataset.
- Inputs:
  - `data/raw/qcew_county.csv`
  - `data/raw/ipeds_institutions.csv`
  - `data/raw/metro_crosswalk.csv`
  - optional ACS API key
- Output: `data/processed/county_analysis_2024.csv`
- ACS-only output (optional): `data/raw/acs_county_2024.csv`

3. `src/models/03_run_models.py`
- Purpose: Run baseline and robustness regressions in `statsmodels`.
- Tasks:
  - Build model-specific complete-case samples.
  - Estimate baseline rent and wage models.
  - Estimate robustness specs (clustered SE, added controls, winsorized intensity).
  - Estimate extensive-margin, intensive-margin, and combined two-part decomposition specs.
  - Export coefficient tables to CSV.
  - Save simple residual-vs-fitted plots.
- Input: `data/processed/county_analysis_2024.csv`
- Outputs:
  - `outputs/tables/baseline_rent.csv`
  - `outputs/tables/baseline_wage.csv`
  - `outputs/tables/robustness.csv`
  - `outputs/tables/margin_decomposition.csv`
  - `outputs/figures/*.png`
  - `outputs/memos/limitations.md`

### Run order
1. Pull ACS county variables first (uses Census API key if provided):

```bash
python src/data/02_build_county_dataset.py \
  --year 2024 \
  --acs-only \
  --output data/raw/acs_county_2024.csv
```

2. Optional download step for non-ACS files:

```bash
python src/data/01_download_data.py \
  --qcew-url "<QCEW_URL>" \
  --ipeds-url "<IPEDS_URL>" \
  --metro-url "<METRO_URL>"
```

3. Build merged county dataset:

```bash
python src/data/02_build_county_dataset.py \
  --year 2024 \
  --qcew data/raw/qcew_county.csv \
  --ipeds data/raw/ipeds_institutions.csv \
  --metro data/raw/metro_crosswalk.csv \
  --geography-scope us_50_dc \
  --acs-out data/raw/acs_county_2024.csv \
  --output data/processed/county_analysis_2024.csv
```

4. Run regressions and export tables:

```bash
python src/models/03_run_models.py \
  --input data/processed/county_analysis_2024.csv \
  --outdir outputs
```

---

## 3) Suggested folder structure

```text
project/
├─ data/
│  ├─ raw/
│  ├─ intermediate/
│  └─ processed/
├─ notebooks/
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
├─ requirements.txt
└─ README.md
```

---

## 4) Data dictionary

Note: Some raw field names vary by release. Any uncertain names are marked "verify" and should be confirmed against the exact files.

| Final variable | Raw source field (verify if marked) | Source dataset | Description | Transformations | Baseline vs robustness |
|---|---|---|---|---|---|
| `county_fips` | ACS `state` + `county`; QCEW `area_fips`; IPEDS county fields | ACS, QCEW, IPEDS | 5-digit county key | Strip non-digits, zero-pad to 5 | Baseline + robustness |
| `state_fips` | ACS `state` | ACS | 2-digit state key | Zero-pad to 2 | Baseline + robustness |
| `county_name` | ACS `NAME` | ACS | County label | None | Reporting/QA |
| `year` | user-selected year | Pipeline | Analysis year | Integer constant | Baseline + robustness |
| `population` | `B01003_001E` | ACS 5-year | Total population | Numeric cast | Baseline + robustness |
| `ln_population` | derived | Derived | Log population | `ln(population)` if >0 | Baseline + robustness |
| `median_gross_rent` | `B25064_001E` | ACS 5-year | Median gross rent | Numeric cast | Baseline outcome |
| `ln_median_gross_rent` | derived | Derived | Log rent outcome | `ln(median_gross_rent)` if >0 | Baseline outcome |
| `median_household_income` | `B19013_001E` | ACS 5-year | Median household income | Numeric cast | Baseline rent control |
| `ln_median_household_income` | derived | Derived | Log income | `ln(median_household_income)` if >0 | Baseline rent control |
| `poverty_rate` | `B17001_002E/B17001_001E` | ACS 5-year | Share below poverty line | computed ratio | Optional robustness/descriptive |
| `avg_weekly_wage` | `annual_avg_wkly_wage` (verify) or `avg_annual_pay/52` | QCEW county | Weekly wage | Parse suppressed; fallback from annual pay | Baseline wage outcome |
| `ln_avg_weekly_wage` | derived | Derived | Log wage outcome | `ln(avg_weekly_wage)` if >0 | Baseline wage outcome |
| `college_enrollment_total` | IPEDS total enrollment (`EFYTOTLT` or similar, verify) | IPEDS institution-level | County-summed enrollment | Aggregate institution records by county | Baseline key input |
| `has_college` | derived | Derived | Indicator for any measured college enrollment in county | `1[college_enrollment_total > 0]` | Margin decomposition |
| `institution_count` | `UNITID` (verify) | IPEDS | Institutions per county | County-level unique count | QA/robustness |
| `college_intensity` | derived | Derived | Enrollment/population ratio | `college_enrollment_total/population` | Baseline key regressor |
| `college_intensity_pct` | derived | Derived | Percentage-point scale of intensity | `100*college_intensity` | Baseline key regressor |
| `metro` | metro flag (verify) or RUCC-based | Metro crosswalk | Metro/nonmetro indicator | direct 0/1 or RUCC<=3 | Baseline control |
| `qcew_total_employment` | `annual_avg_emplvl` (verify) | QCEW county | Denominator for industry shares | Numeric cast | Wage support |
| `manuf_emp_share` | QCEW industry employment (31-33) | QCEW county-industry | Manufacturing employment share | sector emp / total emp | Baseline wage control if feasible |
| `leisure_emp_share` | QCEW industry employment (72 or 71-72) | QCEW county-industry | Leisure/hospitality share | sector emp / total emp | Baseline wage control if feasible |
| `prof_emp_share` | QCEW industry employment (54-56) | QCEW county-industry | Professional/business share | sector emp / total emp | Robustness/optional |
| `renter_share` | `B25003_003E/(B25003_002E+B25003_003E)` | ACS 5-year | Share renter-occupied | computed ratio | Robustness-only |
| `vacancy_rate` | `B25002_003E/B25002_001E` | ACS 5-year | Housing vacancy rate | computed ratio | Robustness-only |
| `vacancy_proxy` | alias of `vacancy_rate` | Derived | Vacancy proxy alias for naming consistency | direct copy | Robustness-only |
| `ba_share` | `(B15003_022E+...+B15003_025E)/B15003_001E` | ACS 5-year | Bachelor-or-higher share | computed ratio | Robustness-only |

---

## 5) Merge plan and cleaning rules

### Merge plan using county FIPS
- Standardize FIPS in every source:
  - Cast to string, trim spaces.
  - Remove non-digit characters.
  - Zero-pad to 5 digits.
  - Keep only valid 5-digit numeric FIPS.
- Merge order (left joins from ACS master):
  1. ACS county frame (master county list)
  2. QCEW county data
  3. IPEDS aggregated enrollment
  4. Metro crosswalk

### Counties missing from one source
- Keep county rows in the merged dataset whenever possible.
- Create model-specific estimation samples via complete-case filtering.
- This allows different N for rent and wage models while preserving transparency.

### Counties with no colleges
- After merging IPEDS county aggregates, set missing enrollment to 0.
- Keep those counties in sample with `college_intensity = 0`.

### If institution-level county identifiers are messy
- Priority 1: Use direct county FIPS field if present.
- Priority 2: Construct county FIPS from state and county codes.
- Priority 3 (optional): geocode/crosswalk unresolved institutions.
- If unresolved remains, drop unresolved institutions from county aggregation and report unresolved share.

### Missing and suppressed value rules (simple and explainable)

#### ACS
- Convert missing/null/sentinel values to `NaN`.
- Do not impute outcomes or key baseline controls.
- Use complete-case sample per model.

#### QCEW
- Treat suppression tokens (`N`, `*`, blanks, etc.) as `NaN`.
- If weekly wage missing but annual pay exists, compute `avg_weekly_wage = annual_pay / 52`.
- If wage still missing, keep county in merged data but drop from wage regression sample.
- For industry shares, do not impute missing numerators/denominators.

### Drop vs impute policy
- Impute only:
  - no-college counties (`college_enrollment_total = 0`)
  - weekly wage fallback from annual pay.
- Otherwise no imputation; rely on explicit model-specific complete-case filtering.

### Log transform rule
- For log variables, require strictly positive levels; nonpositive values become missing for that model sample.

---

## 6) Regression specifications

### Baseline model: rent

`ln_median_gross_rent_i = beta0 + beta1*college_intensity_pct_i + beta2*ln_median_household_income_i + beta3*ln_population_i + beta4*metro_i + StateFE + epsilon_i`

Why controls are included:
- `ln_median_household_income`: local demand and ability to pay rent.
- `ln_population`: market size/agglomeration.
- `metro`: structural urban/rural housing differences.
- `StateFE`: state-level policy and institutional environment.

### Baseline model: wage

`ln_avg_weekly_wage_i = alpha0 + alpha1*college_intensity_pct_i + alpha2*ln_population_i + alpha3*metro_i + alpha4*industry_mix_i + StateFE + u_i`

Why controls are included:
- `ln_population`: labor-market scale.
- `metro`: urban productivity/wage differences.
- `industry_mix`: sector composition is a first-order wage determinant.
- `StateFE`: state-level factors common within state.

### Standard errors
- Baseline: heteroskedasticity-robust (`HC1`).
- Robustness: state-clustered standard errors.

### Robustness models
1. Rent baseline + `renter_share`.
2. Rent baseline + `ba_share` (robustness only, not baseline).
3. Rent baseline with state-clustered SE.
4. Wage baseline with state-clustered SE.
5. Winsorized `college_intensity_pct` (1st/99th percentile) for both outcomes.

### Extensive / intensive extension

Use the baseline single-intensity model as the headline specification, then add a decomposition that separates whether any college is present from how large that presence is.

- Extensive-only rent:
  - `ln_median_gross_rent_i = beta0 + beta1*has_college_i + beta2*ln_median_household_income_i + beta3*ln_population_i + beta4*metro_i + StateFE + epsilon_i`
- Intensive-only rent on the positive-college sample:
  - reuse the baseline rent formula on counties with `has_college_i = 1`
- Combined two-part rent:
  - `ln_median_gross_rent_i = beta0 + beta1*has_college_i + beta2*college_intensity_pct_positive_centered_i + beta3*ln_median_household_income_i + beta4*ln_population_i + beta5*metro_i + StateFE + epsilon_i`
- Extensive-only wage:
  - `ln_avg_weekly_wage_i = alpha0 + alpha1*has_college_i + alpha2*ln_population_i + alpha3*metro_i + alpha4*industry_mix_i + StateFE + u_i`
- Intensive-only wage on the positive-college sample:
  - reuse the baseline wage formula on counties with `has_college_i = 1`
- Combined two-part wage:
  - `ln_avg_weekly_wage_i = alpha0 + alpha1*has_college_i + alpha2*college_intensity_pct_positive_centered_i + alpha3*ln_population_i + alpha4*metro_i + alpha5*industry_mix_i + StateFE + u_i`

`college_intensity_pct_positive_centered` is centered around the mean positive-county college intensity so the `has_college` coefficient compares no-college counties to counties with an average positive college presence.

---

## 7) Runnable Python starter code

### `src/data/01_download_data.py`

```python
#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

import requests


def download_file(url: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with out_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    print(f"Downloaded: {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download raw project files.")
    parser.add_argument("--qcew-url", type=str, default="")
    parser.add_argument("--qcew-out", type=Path, default=Path("data/raw/qcew_county.csv"))
    parser.add_argument("--ipeds-url", type=str, default="")
    parser.add_argument("--ipeds-out", type=Path, default=Path("data/raw/ipeds_institutions.csv"))
    parser.add_argument("--metro-url", type=str, default="")
    parser.add_argument("--metro-out", type=Path, default=Path("data/raw/metro_crosswalk.csv"))
    args = parser.parse_args()

    if args.qcew_url:
        download_file(args.qcew_url, args.qcew_out)
    if args.ipeds_url:
        download_file(args.ipeds_url, args.ipeds_out)
    if args.metro_url:
        download_file(args.metro_url, args.metro_out)

    if not any([args.qcew_url, args.ipeds_url, args.metro_url]):
        print("No URLs provided. Nothing downloaded.")


if __name__ == "__main__":
    main()
```

### `src/data/02_build_county_dataset.py`

```python
#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import requests

# TODO(verify): column names vary by release; adjust candidate lists as needed.
QCEW_AREA_COLS = ["area_fips", "Area FIPS", "fips"]
QCEW_YEAR_COLS = ["year", "Year"]
QCEW_OWN_COLS = ["own_code", "Ownership Code"]
QCEW_INDUSTRY_COLS = ["industry_code", "Industry Code"]
QCEW_WAGE_COLS = ["annual_avg_wkly_wage", "avg_weekly_wage", "Avg Weekly Wage"]
QCEW_ANNUAL_PAY_COLS = ["avg_annual_pay", "annual_avg_pay", "Average Annual Pay"]
QCEW_EMP_COLS = ["annual_avg_emplvl", "avg_emplvl", "Annual Average Employment"]

IPEDS_ENROLL_COLS = ["enrollment_total", "EFYTOTLT", "F1EFTOTLT", "TOTAL_ENROLLMENT"]
IPEDS_UNITID_COLS = ["UNITID", "unitid"]
IPEDS_COUNTY_FIPS_COLS = ["county_fips", "COUNTYFIPS", "COUNTY_FIPS", "COUNTYCD"]
IPEDS_STATE_FIPS_COLS = ["state_fips", "STFIPS", "STATEFIPS"]
IPEDS_COUNTY_CODE_COLS = ["county_code", "CNTYCD", "COUNTYCD"]

METRO_FIPS_COLS = ["county_fips", "fips", "FIPS", "GEOID"]
METRO_FLAG_COLS = ["metro", "is_metro", "METRO"]
METRO_RUCC_COLS = ["RUCC_2023", "RUCC_2013", "rucc", "rucc_code"]

SUPPRESSED = {"", "NA", "N/A", "N", "*", "**", "***", "#", "D", "S", "Q", "NULL", "NAN"}

ACS_VARS = [
    "B01003_001E",  # population
    "B25064_001E",  # median gross rent
    "B19013_001E",  # median household income
    "B17001_001E",  # poverty denominator
    "B17001_002E",  # poverty numerator
    "B25003_002E",  # owner-occupied
    "B25003_003E",  # renter-occupied
    "B25002_001E",  # total housing units
    "B25002_003E",  # vacant housing units
    "B15003_001E",  # educ denominator
    "B15003_022E",  # bachelor's
    "B15003_023E",  # master's
    "B15003_024E",  # professional
    "B15003_025E",  # doctorate
]


def pick_col(df: pd.DataFrame, candidates: Iterable[str], required: bool = True, label: str = "column") -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    if required:
        raise KeyError(f"Could not find {label}. Tried: {list(candidates)}")
    return None


def standardize_county_fips(values: pd.Series) -> pd.Series:
    s = values.astype(str).str.strip()
    s = s.str.replace(r"\.0$", "", regex=True)
    s = s.str.replace(r"\D", "", regex=True)
    s = s.str[-5:].str.zfill(5)
    return s.where(s.str.match(r"^\d{5}$"), np.nan)


def to_numeric_clean(values: pd.Series) -> pd.Series:
    s = values.astype(str).str.strip()
    upper = s.str.upper()
    s = s.where(~upper.isin(SUPPRESSED), np.nan)
    return pd.to_numeric(s, errors="coerce")


def safe_log(values: pd.Series) -> pd.Series:
    return pd.Series(np.where(values > 0, np.log(values), np.nan), index=values.index)


def fetch_acs_county(year: int, api_key: str = "") -> pd.DataFrame:
    url = f"https://api.census.gov/data/{year}/acs/acs5"
    params = {
        "get": ",".join(["NAME"] + ACS_VARS),
        "for": "county:*",
        "in": "state:*",
    }
    if api_key:
        params["key"] = api_key

    resp = requests.get(url, params=params, timeout=90)
    resp.raise_for_status()
    rows = resp.json()
    acs = pd.DataFrame(rows[1:], columns=rows[0])

    for c in ACS_VARS:
        acs[c] = to_numeric_clean(acs[c])

    acs["state_fips"] = acs["state"].astype(str).str.zfill(2)
    acs["county_fips"] = acs["state_fips"] + acs["county"].astype(str).str.zfill(3)
    acs["county_name"] = acs["NAME"]
    acs["year"] = year

    acs["population"] = acs["B01003_001E"]
    acs["median_gross_rent"] = acs["B25064_001E"]
    acs["median_household_income"] = acs["B19013_001E"]
    acs["poverty_rate"] = acs["B17001_002E"] / acs["B17001_001E"]

    acs["renter_share"] = acs["B25003_003E"] / (acs["B25003_002E"] + acs["B25003_003E"])
    acs["vacancy_rate"] = acs["B25002_003E"] / acs["B25002_001E"]
    acs["vacancy_proxy"] = acs["vacancy_rate"]

    ba_num = acs[["B15003_022E", "B15003_023E", "B15003_024E", "B15003_025E"]].sum(axis=1)
    acs["ba_share"] = ba_num / acs["B15003_001E"]

    keep = [
        "county_fips",
        "state_fips",
        "county_name",
        "year",
        "population",
        "median_gross_rent",
        "median_household_income",
        "poverty_rate",
        "renter_share",
        "vacancy_rate",
        "vacancy_proxy",
        "ba_share",
    ]
    return acs[keep].copy()


def load_qcew_county(qcew_path: Path, year: int) -> pd.DataFrame:
    q = pd.read_csv(qcew_path, dtype=str, low_memory=False)

    area_col = pick_col(q, QCEW_AREA_COLS, label="QCEW area FIPS")
    q["county_fips"] = standardize_county_fips(q[area_col])
    q = q[q["county_fips"].notna() & (q["county_fips"] != "00000")].copy()

    year_col = pick_col(q, QCEW_YEAR_COLS, required=False)
    if year_col is not None:
        q = q[q[year_col].astype(str).str.strip() == str(year)].copy()

    own_col = pick_col(q, QCEW_OWN_COLS, required=False)
    if own_col is not None:
        q = q[q[own_col].astype(str).str.strip().isin({"0"})].copy()

    industry_col = pick_col(q, QCEW_INDUSTRY_COLS, label="QCEW industry code")
    wage_col = pick_col(q, QCEW_WAGE_COLS, required=False)
    annual_pay_col = pick_col(q, QCEW_ANNUAL_PAY_COLS, required=False)
    emp_col = pick_col(q, QCEW_EMP_COLS, required=False)

    q["_industry"] = (
        q[industry_col]
        .astype(str)
        .str.strip()
        .str.upper()
        .str.replace(r"\.0$", "", regex=True)
    )

    total_mask = q["_industry"].isin({"10", "000000", "0"})
    totals = q[total_mask].copy()
    if totals.empty:
        raise ValueError("No total-industry rows found in QCEW. Verify industry filters.")

    if wage_col is not None:
        totals["avg_weekly_wage"] = to_numeric_clean(totals[wage_col])
    else:
        totals["avg_weekly_wage"] = np.nan

    if annual_pay_col is not None:
        annual_pay = to_numeric_clean(totals[annual_pay_col])
        totals["avg_weekly_wage"] = totals["avg_weekly_wage"].fillna(annual_pay / 52.0)

    if emp_col is not None:
        totals["qcew_total_employment"] = to_numeric_clean(totals[emp_col])
    else:
        totals["qcew_total_employment"] = np.nan

    out = totals.groupby("county_fips", as_index=False)[["avg_weekly_wage", "qcew_total_employment"]].mean()

    if emp_col is not None:
        q["employment"] = to_numeric_clean(q[emp_col])
        q = q[q["employment"].notna()].copy()
        code = q["_industry"]

        m_exact = q[code.isin({"31", "32", "33"})].groupby("county_fips")["employment"].sum()
        m_range = q[code.isin({"31-33", "3133"})].groupby("county_fips")["employment"].sum()
        manuf = m_exact.combine_first(m_range)

        l_exact = q[code.isin({"72"})].groupby("county_fips")["employment"].sum()
        l_range = q[code.isin({"71-72", "7172"})].groupby("county_fips")["employment"].sum()
        leisure = l_exact.combine_first(l_range)

        p_exact = q[code.isin({"54", "55", "56"})].groupby("county_fips")["employment"].sum()
        p_range = q[code.isin({"54-56", "5456"})].groupby("county_fips")["employment"].sum()
        prof = p_exact.combine_first(p_range)

        shares = out[["county_fips", "qcew_total_employment"]].copy()
        shares["manuf_emp"] = shares["county_fips"].map(manuf)
        shares["leisure_emp"] = shares["county_fips"].map(leisure)
        shares["prof_emp"] = shares["county_fips"].map(prof)

        denom = shares["qcew_total_employment"].replace({0: np.nan})
        shares["manuf_emp_share"] = shares["manuf_emp"] / denom
        shares["leisure_emp_share"] = shares["leisure_emp"] / denom
        shares["prof_emp_share"] = shares["prof_emp"] / denom

        out = out.merge(
            shares[["county_fips", "manuf_emp_share", "leisure_emp_share", "prof_emp_share"]],
            on="county_fips",
            how="left",
        )

    return out


def load_ipeds_aggregated(ipeds_path: Path) -> pd.DataFrame:
    i = pd.read_csv(ipeds_path, dtype=str, low_memory=False)

    enroll_col = pick_col(i, IPEDS_ENROLL_COLS, label="IPEDS enrollment")
    unit_col = pick_col(i, IPEDS_UNITID_COLS, required=False)

    county_fips_col = pick_col(i, IPEDS_COUNTY_FIPS_COLS, required=False)
    i["county_fips"] = np.nan
    if county_fips_col is not None:
        i["county_fips"] = standardize_county_fips(i[county_fips_col])

    # Fallback if direct county FIPS coverage is poor.
    if i["county_fips"].notna().mean() < 0.50:
        st_col = pick_col(i, IPEDS_STATE_FIPS_COLS, required=False)
        co_col = pick_col(i, IPEDS_COUNTY_CODE_COLS, required=False)
        if st_col is None or co_col is None:
            raise ValueError("IPEDS needs county_fips or state_fips+county_code.")
        st = i[st_col].astype(str).str.replace(r"\D", "", regex=True).str.zfill(2)
        co = i[co_col].astype(str).str.replace(r"\D", "", regex=True).str.zfill(3)
        i["county_fips"] = st + co

    i["college_enrollment_total"] = to_numeric_clean(i[enroll_col])
    i = i[i["county_fips"].notna() & i["college_enrollment_total"].notna()].copy()

    out = i.groupby("county_fips", as_index=False)["college_enrollment_total"].sum()

    if unit_col is not None:
        inst = i.groupby("county_fips")[unit_col].nunique().rename("institution_count").reset_index()
        out = out.merge(inst, on="county_fips", how="left")

    return out


def load_metro_crosswalk(metro_path: Path) -> pd.DataFrame:
    m = pd.read_csv(metro_path, dtype=str, low_memory=False)
    fips_col = pick_col(m, METRO_FIPS_COLS, label="metro county FIPS")
    m["county_fips"] = standardize_county_fips(m[fips_col])

    metro_col = pick_col(m, METRO_FLAG_COLS, required=False)
    rucc_col = pick_col(m, METRO_RUCC_COLS, required=False)

    if metro_col is not None:
        metro_num = pd.to_numeric(m[metro_col], errors="coerce")
        if metro_num.notna().sum() > 0:
            m["metro"] = metro_num
        else:
            txt = m[metro_col].astype(str).str.lower()
            m["metro"] = np.where(txt.str.contains("non"), 0, np.where(txt.str.contains("metro"), 1, np.nan))
    elif rucc_col is not None:
        rucc = pd.to_numeric(m[rucc_col], errors="coerce")
        m["metro"] = np.where(rucc <= 3, 1, np.where(rucc.notna(), 0, np.nan))
    else:
        raise ValueError("Metro file needs either metro flag or RUCC code.")

    return m[["county_fips", "metro"]].drop_duplicates(subset=["county_fips"])


def build_dataset(
    year: int,
    qcew_path: Path,
    ipeds_path: Path,
    metro_path: Path,
    output_path: Path,
    acs_api_key: str = "",
) -> pd.DataFrame:
    acs = fetch_acs_county(year=year, api_key=acs_api_key)
    qcew = load_qcew_county(qcew_path, year=year)
    ipeds = load_ipeds_aggregated(ipeds_path)
    metro = load_metro_crosswalk(metro_path)

    df = acs.merge(qcew, on="county_fips", how="left")
    df = df.merge(ipeds, on="county_fips", how="left")
    df = df.merge(metro, on="county_fips", how="left")

    df["college_enrollment_total"] = df["college_enrollment_total"].fillna(0.0)
    if "institution_count" in df.columns:
        df["institution_count"] = df["institution_count"].fillna(0).astype(int)

    df["college_intensity"] = df["college_enrollment_total"] / df["population"]
    df["college_intensity_pct"] = 100.0 * df["college_intensity"]

    df["ln_median_gross_rent"] = safe_log(df["median_gross_rent"])
    df["ln_avg_weekly_wage"] = safe_log(df["avg_weekly_wage"])
    df["ln_median_household_income"] = safe_log(df["median_household_income"])
    df["ln_population"] = safe_log(df["population"])

    keep = [
        "county_fips",
        "state_fips",
        "county_name",
        "year",
        "population",
        "ln_population",
        "median_gross_rent",
        "ln_median_gross_rent",
        "median_household_income",
        "ln_median_household_income",
        "avg_weekly_wage",
        "ln_avg_weekly_wage",
        "college_enrollment_total",
        "institution_count",
        "college_intensity",
        "college_intensity_pct",
        "metro",
        "qcew_total_employment",
        "manuf_emp_share",
        "leisure_emp_share",
        "prof_emp_share",
        "renter_share",
        "vacancy_rate",
        "vacancy_proxy",
        "ba_share",
    ]
    keep = [c for c in keep if c in df.columns]
    df = df[keep].copy()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved analytic dataset: {output_path} ({len(df):,} counties)")
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Build county cross-sectional analysis dataset.")
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--qcew", type=Path, required=True)
    parser.add_argument("--ipeds", type=Path, required=True)
    parser.add_argument("--metro", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/processed/county_analysis_2024.csv"))
    parser.add_argument("--acs-api-key", type=str, default=os.getenv("ACS_API_KEY", ""))
    args = parser.parse_args()

    build_dataset(
        year=args.year,
        qcew_path=args.qcew,
        ipeds_path=args.ipeds,
        metro_path=args.metro,
        output_path=args.output,
        acs_api_key=args.acs_api_key,
    )


if __name__ == "__main__":
    main()
```

### `src/models/03_run_models.py`

```python
#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import statsmodels.formula.api as smf


def winsorize(s: pd.Series, low: float = 0.01, high: float = 0.99) -> pd.Series:
    lo = s.quantile(low)
    hi = s.quantile(high)
    return s.clip(lower=lo, upper=hi)


def fit_ols(
    df: pd.DataFrame,
    formula: str,
    required_cols: list[str],
    cluster_state: bool = False,
):
    sample = df.dropna(subset=required_cols).copy()
    if sample.empty:
        raise ValueError(f"No observations left for formula: {formula}")
    model = smf.ols(formula=formula, data=sample)
    if cluster_state:
        result = model.fit(cov_type="cluster", cov_kwds={"groups": sample["state_fips"]})
    else:
        result = model.fit(cov_type="HC1")
    return result, sample


def tidy_result(result, spec_name: str, outcome: str) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "term": result.params.index,
            "coef": result.params.values,
            "std_error": result.bse.values,
            "p_value": result.pvalues.values,
        }
    )
    out["spec"] = spec_name
    out["outcome"] = outcome
    out["nobs"] = int(result.nobs)
    out["r2"] = result.rsquared
    return out


def residual_plot(result, path: Path, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.scatter(result.fittedvalues, result.resid, alpha=0.35, s=12)
    ax.axhline(0.0, color="black", linewidth=1)
    ax.set_xlabel("Fitted values")
    ax.set_ylabel("Residuals")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run baseline and robustness county regressions.")
    parser.add_argument("--input", type=Path, default=Path("data/processed/county_analysis_2024.csv"))
    parser.add_argument("--outdir", type=Path, default=Path("outputs"))
    args = parser.parse_args()

    df = pd.read_csv(args.input, dtype={"county_fips": str, "state_fips": str})

    numeric_cols = [
        "ln_median_gross_rent",
        "ln_avg_weekly_wage",
        "college_intensity_pct",
        "ln_median_household_income",
        "ln_population",
        "metro",
        "manuf_emp_share",
        "leisure_emp_share",
        "renter_share",
        "vacancy_rate",
        "ba_share",
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    tables_dir = args.outdir / "tables"
    figs_dir = args.outdir / "figures"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figs_dir.mkdir(parents=True, exist_ok=True)

    # Baseline rent
    rent_formula = (
        "ln_median_gross_rent ~ college_intensity_pct + ln_median_household_income + "
        "ln_population + metro + C(state_fips)"
    )
    rent_needed = [
        "ln_median_gross_rent",
        "college_intensity_pct",
        "ln_median_household_income",
        "ln_population",
        "metro",
        "state_fips",
    ]
    rent_base, rent_sample = fit_ols(df, rent_formula, rent_needed, cluster_state=False)
    tidy_result(rent_base, "baseline_rent_hc1", "ln_median_gross_rent").to_csv(
        tables_dir / "baseline_rent.csv", index=False
    )

    # Baseline wage (industry controls only if coverage is adequate)
    wage_formula = "ln_avg_weekly_wage ~ college_intensity_pct + ln_population + metro"
    wage_needed = ["ln_avg_weekly_wage", "college_intensity_pct", "ln_population", "metro", "state_fips"]

    for c in ["manuf_emp_share", "leisure_emp_share"]:
        if c in df.columns and df[c].notna().mean() >= 0.80:
            wage_formula += f" + {c}"
            wage_needed.append(c)

    wage_formula += " + C(state_fips)"
    wage_base, wage_sample = fit_ols(df, wage_formula, wage_needed, cluster_state=False)
    tidy_result(wage_base, "baseline_wage_hc1", "ln_avg_weekly_wage").to_csv(
        tables_dir / "baseline_wage.csv", index=False
    )

    # Robustness specs
    robustness_tables = []

    rent_cluster, _ = fit_ols(df, rent_formula, rent_needed, cluster_state=True)
    robustness_tables.append(tidy_result(rent_cluster, "rent_cluster_state", "ln_median_gross_rent"))

    wage_cluster, _ = fit_ols(df, wage_formula, wage_needed, cluster_state=True)
    robustness_tables.append(tidy_result(wage_cluster, "wage_cluster_state", "ln_avg_weekly_wage"))

    if "renter_share" in df.columns:
        f = (
            "ln_median_gross_rent ~ college_intensity_pct + ln_median_household_income + "
            "ln_population + metro + renter_share + C(state_fips)"
        )
        need = rent_needed + ["renter_share"]
        r, _ = fit_ols(df, f, need, cluster_state=False)
        robustness_tables.append(tidy_result(r, "rent_plus_renter_share", "ln_median_gross_rent"))

    if "ba_share" in df.columns:
        f = (
            "ln_median_gross_rent ~ college_intensity_pct + ln_median_household_income + "
            "ln_population + metro + ba_share + C(state_fips)"
        )
        need = rent_needed + ["ba_share"]
        r, _ = fit_ols(df, f, need, cluster_state=False)
        robustness_tables.append(tidy_result(r, "rent_plus_ba_share", "ln_median_gross_rent"))

    df["college_intensity_pct_w"] = winsorize(df["college_intensity_pct"])
    rent_w_formula = (
        "ln_median_gross_rent ~ college_intensity_pct_w + ln_median_household_income + "
        "ln_population + metro + C(state_fips)"
    )
    rent_w_need = [
        "ln_median_gross_rent",
        "college_intensity_pct_w",
        "ln_median_household_income",
        "ln_population",
        "metro",
        "state_fips",
    ]
    rent_w, _ = fit_ols(df, rent_w_formula, rent_w_need, cluster_state=False)
    robustness_tables.append(tidy_result(rent_w, "rent_winsorized_intensity", "ln_median_gross_rent"))

    wage_w_formula = wage_formula.replace("college_intensity_pct", "college_intensity_pct_w")
    wage_w_need = [c if c != "college_intensity_pct" else "college_intensity_pct_w" for c in wage_needed]
    wage_w, _ = fit_ols(df, wage_w_formula, wage_w_need, cluster_state=False)
    robustness_tables.append(tidy_result(wage_w, "wage_winsorized_intensity", "ln_avg_weekly_wage"))

    pd.concat(robustness_tables, ignore_index=True).to_csv(tables_dir / "robustness.csv", index=False)

    model_stats = pd.DataFrame(
        [
            {"spec": "baseline_rent_hc1", "formula": rent_formula, "nobs": int(rent_base.nobs), "r2": rent_base.rsquared},
            {"spec": "baseline_wage_hc1", "formula": wage_formula, "nobs": int(wage_base.nobs), "r2": wage_base.rsquared},
        ]
    )
    model_stats.to_csv(tables_dir / "model_summary_stats.csv", index=False)

    residual_plot(rent_base, figs_dir / "rent_residuals_vs_fitted.png", "Rent model residuals vs fitted")
    residual_plot(wage_base, figs_dir / "wage_residuals_vs_fitted.png", "Wage model residuals vs fitted")

    print("Done. Tables saved to outputs/tables and figures to outputs/figures.")


if __name__ == "__main__":
    main()
```

### `requirements.txt` (minimal)

```text
pandas
numpy
requests
statsmodels
matplotlib
```

---

## 8) Open decisions / assumptions needing human review

1. Final reference year alignment (recommended: 2024).
2. Exact QCEW total-industry and ownership filters for your file release.
3. Exact IPEDS enrollment field choice (fall total vs other enrollment measure).
4. Metro definition source and coding rule (direct metro flag vs RUCC threshold).
5. Handling of unresolved IPEDS county assignment records.
6. Geography scope override to default (`us_50_dc`) if instructor requires a different coverage rule.
7. Minimum non-missing threshold for including industry-share controls in baseline wage model.
8. Any source-specific column name differences to be mapped before first full run.

---

## Minimal class deliverable checklist

- One clean merged county dataset: `data/processed/county_analysis_2024.csv`
- One baseline rent regression table: `outputs/tables/baseline_rent.csv`
- One baseline wage regression table: `outputs/tables/baseline_wage.csv`
- One robustness table: `outputs/tables/robustness.csv`
- One short limitations memo: `outputs/memos/limitations.md`
