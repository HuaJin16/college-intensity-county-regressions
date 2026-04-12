#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

MISSING_TEXT = {"", "NA", "N/A", "NULL", "NONE", "NAN"}

FIPS_COLS = [
    "county_fips",
    "countyfips",
    "fips",
    "area_fips",
    "county_fips_raw",
    "County FIPS",
    "Area FIPS",
]

COUNTY_NAME_COLS = [
    "county_name",
    "county",
    "county_title",
    "county_name_raw",
    "County",
    "County Name",
]

CBSA_CODE_COLS = [
    "cbsa_code",
    "cbsa",
    "msa_code",
    "metro_code",
    "cbsa_code_raw",
    "CBSA Code",
    "MSA Code",
]

CBSA_TITLE_COLS = [
    "cbsa_title",
    "cbsa_name",
    "msa_title",
    "msa_name",
    "metro_title",
    "cbsa_title_raw",
    "CBSA Title",
    "MSA Title",
]

CSA_CODE_COLS = [
    "csa_code",
    "csa",
    "csa_code_raw",
    "CSA Code",
]

CSA_TITLE_COLS = [
    "csa_title",
    "csa_name",
    "csa_title_raw",
    "CSA Title",
]

UNIVERSE_FIPS_COLS = [
    "county_fips",
    "fips",
    "FIPS",
    "GEOID",
    "area_fips",
    "County Code",
]

UNIVERSE_NAME_COLS = [
    "county_name",
    "county",
    "county_title",
    "NAME",
    "County Name",
]


def pick_col(
    df: pd.DataFrame,
    candidates: Iterable[str],
    label: str,
    required: bool = True,
) -> str | None:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    if required:
        raise ValueError(f"Missing {label}. Tried: {list(candidates)}")
    return None


def clean_text(values: pd.Series) -> pd.Series:
    out = values.astype(str).str.strip()
    upper = out.str.upper()
    return out.where(~upper.isin(MISSING_TEXT), np.nan)


def standardize_county_fips(values: pd.Series) -> pd.Series:
    out = clean_text(values)
    out = out.str.replace(r"\.0$", "", regex=True)
    out = out.str.replace(r"\D", "", regex=True)
    out = out.str[-5:].str.zfill(5)
    return out.where(out.str.match(r"^\d{5}$"), np.nan)


def first_nonmissing(values: pd.Series):
    valid = values.dropna()
    if valid.empty:
        return np.nan
    return valid.iloc[0]


def read_delimited(path: Path, sep: str | None, header="infer") -> pd.DataFrame:
    kwargs = {"dtype": str, "header": header}
    if sep is None:
        kwargs["sep"] = None
        kwargs["engine"] = "python"
    else:
        kwargs["sep"] = sep
    return pd.read_csv(path, **kwargs)


def read_crosswalk(path: Path) -> pd.DataFrame:
    frame = None
    sep_used = None
    for sep in ["\t", ",", None]:
        try:
            candidate = read_delimited(path, sep=sep, header="infer")
        except Exception:
            continue
        if candidate.shape[1] > 1:
            frame = candidate
            sep_used = sep
            break
        if frame is None:
            frame = candidate
            sep_used = sep

    if frame is None:
        raise ValueError(f"Could not parse metro crosswalk file: {path}")

    if not frame.empty:
        first_col_name = str(frame.columns[0]).strip()
        first_col_digits = "".join(ch for ch in first_col_name if ch.isdigit())
        looks_like_data_row = len(first_col_digits) == 5
        if looks_like_data_row:
            frame = read_delimited(path, sep=sep_used, header=None)
            if frame.shape[1] < 4:
                raise ValueError(
                    "Metro crosswalk with no header needs at least 4 columns: "
                    "county_fips, county_name, cbsa_code, cbsa_title."
                )

            rename_map = {
                0: "county_fips_raw",
                1: "county_name_raw",
                2: "cbsa_code_raw",
                3: "cbsa_title_raw",
            }
            if frame.shape[1] >= 5:
                rename_map[4] = "csa_code_raw"
            if frame.shape[1] >= 6:
                rename_map[5] = "csa_title_raw"

            frame = frame.rename(columns=rename_map)

    return frame


def classify_cbsa(cbsa_title: pd.Series) -> tuple[pd.Series, pd.Series]:
    title = clean_text(cbsa_title)
    lower = title.fillna("").str.lower()

    is_micro = lower.str.contains("micro")
    is_metro = (~is_micro) & lower.str.contains(r"\bmsa\b|metropolitan")
    is_none = title.isna()

    cbsa_type = pd.Series(
        np.select(
            [is_metro, is_micro, is_none],
            ["metro", "micro", "none"],
            default="unknown",
        ),
        index=title.index,
    )

    # Exact mapping for baseline control:
    # metro = 1 for MSA (metropolitan), metro = 0 for MicroSA or no CBSA assignment.
    metro = pd.Series(
        np.select(
            [is_metro, is_micro | is_none],
            [1.0, 0.0],
            default=np.nan,
        ),
        index=title.index,
        dtype=float,
    )
    return cbsa_type, metro


def add_county_universe(out: pd.DataFrame, county_universe_path: Path) -> pd.DataFrame:
    universe = pd.read_csv(county_universe_path, dtype=str, low_memory=False)
    universe_fips_col = pick_col(universe, UNIVERSE_FIPS_COLS, "county-universe FIPS")
    universe_name_col = pick_col(universe, UNIVERSE_NAME_COLS, "county-universe county name", required=False)

    universe_df = pd.DataFrame()
    universe_df["county_fips"] = standardize_county_fips(universe[universe_fips_col])
    if universe_name_col is not None:
        universe_df["county_name_universe"] = clean_text(universe[universe_name_col])

    universe_df = universe_df[universe_df["county_fips"].notna()].drop_duplicates(subset=["county_fips"])

    merged = universe_df.merge(out, on="county_fips", how="left")
    if "county_name_universe" in merged.columns:
        merged["county_name"] = merged.get("county_name", pd.Series(np.nan, index=merged.index)).fillna(
            merged["county_name_universe"]
        )
        merged = merged.drop(columns=["county_name_universe"])

    merged["cbsa_type"] = merged.get("cbsa_type", pd.Series(np.nan, index=merged.index)).fillna("none")
    merged["metro"] = pd.to_numeric(merged.get("metro", np.nan), errors="coerce").fillna(0.0)
    return merged


def build_metro_crosswalk(
    input_path: Path,
    output_path: Path,
    county_universe_path: Path | None = None,
) -> pd.DataFrame:
    raw = read_crosswalk(input_path)

    county_col = pick_col(raw, FIPS_COLS, "county FIPS")
    cbsa_title_col = pick_col(raw, CBSA_TITLE_COLS, "CBSA title (MSA/MicroSA)")

    county_name_col = pick_col(raw, COUNTY_NAME_COLS, "county name", required=False)
    cbsa_code_col = pick_col(raw, CBSA_CODE_COLS, "CBSA code", required=False)
    csa_code_col = pick_col(raw, CSA_CODE_COLS, "CSA code", required=False)
    csa_title_col = pick_col(raw, CSA_TITLE_COLS, "CSA title", required=False)

    out = pd.DataFrame()
    out["county_fips"] = standardize_county_fips(raw[county_col])
    out["cbsa_title"] = clean_text(raw[cbsa_title_col])

    if county_name_col is not None:
        out["county_name"] = clean_text(raw[county_name_col])
    if cbsa_code_col is not None:
        out["cbsa_code"] = clean_text(raw[cbsa_code_col])
    if csa_code_col is not None:
        out["csa_code"] = clean_text(raw[csa_code_col])
    if csa_title_col is not None:
        out["csa_title"] = clean_text(raw[csa_title_col])

    out = out[out["county_fips"].notna()].copy()

    out["cbsa_type"], out["metro"] = classify_cbsa(out["cbsa_title"])

    conflict_counts = out.groupby("county_fips")["metro"].nunique(dropna=True)
    conflicting = conflict_counts[conflict_counts > 1]
    if not conflicting.empty:
        sample_conflicts = ", ".join(conflicting.index[:10].tolist())
        raise ValueError(
            "Conflicting metro assignment found for county_fips values. "
            f"Examples: {sample_conflicts}"
        )

    agg_map = {col: first_nonmissing for col in out.columns if col != "county_fips"}
    out = out.groupby("county_fips", as_index=False).agg(agg_map)

    if county_universe_path is not None:
        out = add_county_universe(out, county_universe_path)

    ordered_cols = [
        "county_fips",
        "metro",
        "cbsa_type",
        "county_name",
        "cbsa_code",
        "cbsa_title",
        "csa_code",
        "csa_title",
    ]
    ordered_cols = [col for col in ordered_cols if col in out.columns]
    out = out[ordered_cols].sort_values("county_fips").reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_path, index=False)

    print(f"Saved metro crosswalk: {output_path} ({len(out):,} counties)")
    print(f"CBSA type counts: {out['cbsa_type'].value_counts(dropna=False).to_dict()}")
    print(f"metro missing count: {int(out['metro'].isna().sum())}")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build county metro indicator from QCEW County-MSA-CSA crosswalk."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw/qcew_county_msa_csa_crosswalk.txt"),
        help="Raw QCEW county-MSA-CSA crosswalk (CSV/TSV; with or without header).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/metro_crosswalk.csv"),
        help="Canonical metro crosswalk used by the county build script.",
    )
    parser.add_argument(
        "--county-universe",
        type=Path,
        default=None,
        help=(
            "Optional county-universe file (for example ACS county extract) used to "
            "force one row for every county_fips; counties not in the QCEW crosswalk "
            "are set to metro=0 and cbsa_type=none."
        ),
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"Missing metro source file: {args.input}")

    if args.county_universe is not None and not args.county_universe.exists():
        raise FileNotFoundError(f"Missing county universe file: {args.county_universe}")

    build_metro_crosswalk(
        input_path=args.input,
        output_path=args.output,
        county_universe_path=args.county_universe,
    )


if __name__ == "__main__":
    main()
