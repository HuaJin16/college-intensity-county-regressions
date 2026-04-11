#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import requests

# TODO_VERIFY_*: raw column names may vary across source releases.
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
    "B25003_002E",  # owner-occupied housing units
    "B25003_003E",  # renter-occupied housing units
    "B25002_001E",  # total housing units
    "B25002_003E",  # vacant housing units
    "B15003_001E",  # education denominator
    "B15003_022E",  # bachelor's
    "B15003_023E",  # master's
    "B15003_024E",  # professional
    "B15003_025E",  # doctorate
]


def pick_col(
    df: pd.DataFrame,
    candidates: Iterable[str],
    required: bool = True,
    label: str = "column",
) -> str | None:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    if required:
        raise KeyError(f"Could not find {label}. Tried: {list(candidates)}")
    return None


def standardize_county_fips(values: pd.Series) -> pd.Series:
    series = values.astype(str).str.strip()
    series = series.str.replace(r"\.0$", "", regex=True)
    series = series.str.replace(r"\D", "", regex=True)
    series = series.str[-5:].str.zfill(5)
    return series.where(series.str.match(r"^\d{5}$"), np.nan)


def to_numeric_clean(values: pd.Series, nonnegative_only: bool = False) -> pd.Series:
    series = values.astype(str).str.strip()
    upper = series.str.upper()
    series = series.where(~upper.isin(SUPPRESSED), np.nan)
    out = pd.to_numeric(series, errors="coerce")
    if nonnegative_only:
        out = out.where(out >= 0, np.nan)
    return out


def safe_divide(numer: pd.Series, denom: pd.Series) -> pd.Series:
    valid_denom = denom.where(denom > 0, np.nan)
    return numer / valid_denom


def clean_share(series: pd.Series) -> pd.Series:
    return series.where((series >= 0) & (series <= 1), np.nan)


def safe_log(values: pd.Series) -> pd.Series:
    return pd.Series(np.where(values > 0, np.log(values), np.nan), index=values.index)


def save_csv(df: pd.DataFrame, out_path: Path, label: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Saved {label}: {out_path} ({len(df):,} rows)")


def require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")


def load_env_file(env_path: Path = Path(".env")) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


def fetch_acs_county(year: int, api_key: str = "") -> pd.DataFrame:
    url = f"https://api.census.gov/data/{year}/acs/acs5"
    params = {
        "get": ",".join(["NAME"] + ACS_VARS),
        "for": "county:*",
        "in": "state:*",
    }
    if api_key:
        params["key"] = api_key

    response = requests.get(url, params=params, timeout=90)
    response.raise_for_status()
    rows = response.json()

    if len(rows) < 2:
        raise ValueError("ACS API returned no county rows.")

    acs = pd.DataFrame(rows[1:], columns=rows[0])

    for column in ACS_VARS:
        acs[column] = to_numeric_clean(acs[column], nonnegative_only=True)

    acs["state_fips"] = acs["state"].astype(str).str.zfill(2)
    acs["county_fips"] = acs["state_fips"] + acs["county"].astype(str).str.zfill(3)
    acs["county_name"] = acs["NAME"]
    acs["year"] = year

    acs["population"] = acs["B01003_001E"]
    acs["median_gross_rent"] = acs["B25064_001E"]
    acs["median_household_income"] = acs["B19013_001E"]

    acs["poverty_rate"] = clean_share(safe_divide(acs["B17001_002E"], acs["B17001_001E"]))
    acs["renter_share"] = clean_share(
        safe_divide(acs["B25003_003E"], acs["B25003_002E"] + acs["B25003_003E"])
    )
    acs["vacancy_rate"] = clean_share(safe_divide(acs["B25002_003E"], acs["B25002_001E"]))
    acs["vacancy_proxy"] = acs["vacancy_rate"]

    ba_numerator = acs[["B15003_022E", "B15003_023E", "B15003_024E", "B15003_025E"]].sum(axis=1)
    acs["ba_share"] = clean_share(safe_divide(ba_numerator, acs["B15003_001E"]))

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
    qcew = pd.read_csv(qcew_path, dtype=str, low_memory=False)

    area_col = pick_col(qcew, QCEW_AREA_COLS, label="QCEW area FIPS")
    qcew["county_fips"] = standardize_county_fips(qcew[area_col])
    qcew = qcew[qcew["county_fips"].notna() & (qcew["county_fips"] != "00000")].copy()

    year_col = pick_col(qcew, QCEW_YEAR_COLS, required=False)
    if year_col is not None:
        qcew = qcew[qcew[year_col].astype(str).str.strip() == str(year)].copy()

    own_col = pick_col(qcew, QCEW_OWN_COLS, required=False)
    if own_col is not None:
        qcew = qcew[qcew[own_col].astype(str).str.strip().isin({"0"})].copy()

    industry_col = pick_col(qcew, QCEW_INDUSTRY_COLS, label="QCEW industry code")
    wage_col = pick_col(qcew, QCEW_WAGE_COLS, required=False)
    annual_pay_col = pick_col(qcew, QCEW_ANNUAL_PAY_COLS, required=False)
    emp_col = pick_col(qcew, QCEW_EMP_COLS, required=False)

    qcew["_industry"] = (
        qcew[industry_col].astype(str).str.strip().str.upper().str.replace(r"\.0$", "", regex=True)
    )

    totals = qcew[qcew["_industry"].isin({"10", "000000", "0"})].copy()
    if totals.empty:
        raise ValueError("No total-industry rows found in QCEW. Verify industry filters.")

    if wage_col is not None:
        totals["avg_weekly_wage"] = to_numeric_clean(totals[wage_col], nonnegative_only=True)
    else:
        totals["avg_weekly_wage"] = np.nan

    if annual_pay_col is not None:
        annual_pay = to_numeric_clean(totals[annual_pay_col], nonnegative_only=True)
        totals["avg_weekly_wage"] = totals["avg_weekly_wage"].fillna(annual_pay / 52.0)

    if emp_col is not None:
        totals["qcew_total_employment"] = to_numeric_clean(totals[emp_col], nonnegative_only=True)
    else:
        totals["qcew_total_employment"] = np.nan

    out = totals.groupby("county_fips", as_index=False)[["avg_weekly_wage", "qcew_total_employment"]].mean()

    if emp_col is not None:
        qcew["employment"] = to_numeric_clean(qcew[emp_col], nonnegative_only=True)
        qcew = qcew[qcew["employment"].notna()].copy()
        code = qcew["_industry"]

        manuf_exact = qcew[code.isin({"31", "32", "33"})].groupby("county_fips")["employment"].sum()
        manuf_range = qcew[code.isin({"31-33", "3133"})].groupby("county_fips")["employment"].sum()
        manuf = manuf_exact.combine_first(manuf_range)

        leisure_exact = qcew[code.isin({"72"})].groupby("county_fips")["employment"].sum()
        leisure_range = qcew[code.isin({"71-72", "7172"})].groupby("county_fips")["employment"].sum()
        leisure = leisure_exact.combine_first(leisure_range)

        prof_exact = qcew[code.isin({"54", "55", "56"})].groupby("county_fips")["employment"].sum()
        prof_range = qcew[code.isin({"54-56", "5456"})].groupby("county_fips")["employment"].sum()
        prof = prof_exact.combine_first(prof_range)

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
    ipeds = pd.read_csv(ipeds_path, dtype=str, low_memory=False)

    enroll_col = pick_col(ipeds, IPEDS_ENROLL_COLS, label="IPEDS enrollment")
    unit_col = pick_col(ipeds, IPEDS_UNITID_COLS, required=False)

    county_fips_col = pick_col(ipeds, IPEDS_COUNTY_FIPS_COLS, required=False)
    ipeds["county_fips"] = np.nan
    if county_fips_col is not None:
        ipeds["county_fips"] = standardize_county_fips(ipeds[county_fips_col])

    if ipeds["county_fips"].notna().mean() < 0.50:
        state_col = pick_col(ipeds, IPEDS_STATE_FIPS_COLS, required=False)
        county_col = pick_col(ipeds, IPEDS_COUNTY_CODE_COLS, required=False)
        if state_col is None or county_col is None:
            raise ValueError("IPEDS needs county_fips or state_fips+county_code.")
        state = ipeds[state_col].astype(str).str.replace(r"\D", "", regex=True).str.zfill(2)
        county = ipeds[county_col].astype(str).str.replace(r"\D", "", regex=True).str.zfill(3)
        ipeds["county_fips"] = state + county

    ipeds["college_enrollment_total"] = to_numeric_clean(ipeds[enroll_col], nonnegative_only=True)
    ipeds = ipeds[ipeds["county_fips"].notna() & ipeds["college_enrollment_total"].notna()].copy()

    out = ipeds.groupby("county_fips", as_index=False)["college_enrollment_total"].sum()

    if unit_col is not None:
        institution_count = ipeds.groupby("county_fips")[unit_col].nunique().rename("institution_count")
        out = out.merge(institution_count.reset_index(), on="county_fips", how="left")

    return out


def load_metro_crosswalk(metro_path: Path) -> pd.DataFrame:
    metro = pd.read_csv(metro_path, dtype=str, low_memory=False)
    fips_col = pick_col(metro, METRO_FIPS_COLS, label="metro county FIPS")
    metro["county_fips"] = standardize_county_fips(metro[fips_col])

    metro_col = pick_col(metro, METRO_FLAG_COLS, required=False)
    rucc_col = pick_col(metro, METRO_RUCC_COLS, required=False)

    if metro_col is not None:
        metro_num = pd.to_numeric(metro[metro_col], errors="coerce")
        if metro_num.notna().sum() > 0:
            metro["metro"] = metro_num
        else:
            metro_text = metro[metro_col].astype(str).str.lower()
            metro["metro"] = np.where(
                metro_text.str.contains("non"),
                0,
                np.where(metro_text.str.contains("metro"), 1, np.nan),
            )
    elif rucc_col is not None:
        rucc = pd.to_numeric(metro[rucc_col], errors="coerce")
        metro["metro"] = np.where(rucc <= 3, 1, np.where(rucc.notna(), 0, np.nan))
    else:
        raise ValueError("Metro file needs either a metro flag column or RUCC code column.")

    return metro[["county_fips", "metro"]].drop_duplicates(subset=["county_fips"])


def build_dataset(
    year: int,
    qcew_path: Path,
    ipeds_path: Path,
    metro_path: Path,
    output_path: Path,
    acs_api_key: str = "",
    acs_out_path: Path | None = None,
    acs_only: bool = False,
) -> pd.DataFrame:
    acs = fetch_acs_county(year=year, api_key=acs_api_key)

    if acs_out_path is not None:
        save_csv(acs, acs_out_path, "ACS county extract")

    if acs_only:
        if acs_out_path is None or output_path.resolve() != acs_out_path.resolve():
            save_csv(acs, output_path, "ACS-only county dataset")
        return acs

    require_file(qcew_path, "QCEW county file")
    require_file(ipeds_path, "IPEDS institution file")
    require_file(metro_path, "metro crosswalk file")

    qcew = load_qcew_county(qcew_path, year=year)
    ipeds = load_ipeds_aggregated(ipeds_path)
    metro = load_metro_crosswalk(metro_path)

    df = acs.merge(qcew, on="county_fips", how="left")
    df = df.merge(ipeds, on="county_fips", how="left")
    df = df.merge(metro, on="county_fips", how="left")

    if "college_enrollment_total" not in df.columns:
        df["college_enrollment_total"] = 0.0
    df["college_enrollment_total"] = pd.to_numeric(df["college_enrollment_total"], errors="coerce").fillna(0.0)

    if "institution_count" in df.columns:
        df["institution_count"] = pd.to_numeric(df["institution_count"], errors="coerce").fillna(0).astype(int)

    for numeric_col in ["population", "median_gross_rent", "median_household_income", "avg_weekly_wage"]:
        if numeric_col in df.columns:
            df[numeric_col] = pd.to_numeric(df[numeric_col], errors="coerce")

    df["college_intensity"] = safe_divide(df["college_enrollment_total"], df["population"])
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
        "poverty_rate",
        "renter_share",
        "vacancy_rate",
        "vacancy_proxy",
        "ba_share",
    ]
    keep = [column for column in keep if column in df.columns]
    df = df[keep].copy()

    save_csv(df, output_path, "analysis dataset")
    return df


def main() -> None:
    load_env_file()

    parser = argparse.ArgumentParser(description="Build county-level analysis dataset.")
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--qcew", type=Path, default=Path("data/raw/qcew_county.csv"))
    parser.add_argument("--ipeds", type=Path, default=Path("data/raw/ipeds_institutions.csv"))
    parser.add_argument("--metro", type=Path, default=Path("data/raw/metro_crosswalk.csv"))
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--acs-out",
        type=Path,
        default=None,
        help="ACS extract path (default: data/raw/acs_county_<year>.csv)",
    )
    parser.add_argument("--acs-api-key", type=str, default=os.getenv("ACS_API_KEY", ""))
    parser.add_argument("--acs-only", action="store_true", help="Only pull and save ACS county variables.")
    args = parser.parse_args()

    if args.acs_out is None:
        if args.acs_only and args.output is not None:
            acs_out_path = args.output
        else:
            acs_out_path = Path(f"data/raw/acs_county_{args.year}.csv")
    else:
        acs_out_path = args.acs_out

    output_path = args.output
    if output_path is None:
        if args.acs_only:
            output_path = acs_out_path
        else:
            output_path = Path(f"data/processed/county_analysis_{args.year}.csv")

    if not args.acs_api_key:
        print("ACS API key not provided; using unauthenticated Census API request.")

    build_dataset(
        year=args.year,
        qcew_path=args.qcew,
        ipeds_path=args.ipeds,
        metro_path=args.metro,
        output_path=output_path,
        acs_api_key=args.acs_api_key,
        acs_out_path=acs_out_path,
        acs_only=args.acs_only,
    )


if __name__ == "__main__":
    main()
