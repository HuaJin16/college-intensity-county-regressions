#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

MISSING_TEXT = {"", ".", "NA", "N/A", "NULL", "NONE", "NAN"}
UNITID_COLS = ["UNITID", "unitid"]

HD_NAME_COLS = ["INSTNM", "institution_name", "INST_NAME"]
HD_STATE_ABBR_COLS = ["STABBR", "state_abbr", "STATE"]
HD_COUNTY_CODE_COLS = ["COUNTYCD", "COUNTY_CODE", "county_code"]
HD_COUNTY_NAME_COLS = ["COUNTYNM", "COUNTYNAME", "county_name"]
HD_STATE_FIPS_COLS = ["FIPS", "STFIPS", "STATEFIPS", "state_fips"]

EFIA_ACTIVITY_COLS = ["CDACTUA", "CNACTUA", "CDACTGA"]
EFIA_DIRECT_12M_COLS = [
    "EFYTOTLT",
    "EFYTOTL",
    "ENR12M_TOTAL",
    "ENROLL12M",
    "TOTAL_12_MONTH_ENROLLMENT",
]
EFIA_FTE_COLS = ["EFTEUG", "EFTEGD", "FTEUG", "FTEGD", "FTEDPP"]
EFIA_FALL_COLS = ["EFTOTLT", "EFTOTL", "TOTAL_ENROLLMENT", "FALL_TOTAL"]


def require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")


def pick_col(df: pd.DataFrame, candidates: list[str], label: str, required: bool = True) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    if required:
        raise ValueError(f"Missing {label}. Tried: {candidates}")
    return None


def clean_text(values: pd.Series) -> pd.Series:
    out = values.astype(str).str.strip()
    upper = out.str.upper()
    return out.where(~upper.isin(MISSING_TEXT), np.nan)


def clean_digits(values: pd.Series) -> pd.Series:
    out = clean_text(values)
    out = out.str.replace(r"\.0$", "", regex=True)
    out = out.str.replace(r"\D", "", regex=True)
    return out.where(out.str.len() > 0, np.nan)


def to_numeric_nonnegative(values: pd.Series) -> pd.Series:
    out = pd.to_numeric(clean_text(values), errors="coerce")
    return out.where(out >= 0, np.nan)


def standardize_unitid(values: pd.Series) -> pd.Series:
    digits = clean_digits(values)
    return digits.str.zfill(6).where(digits.notna(), np.nan)


def count_duplicate_unitids(values: pd.Series) -> tuple[int, int]:
    valid = values.dropna()
    dup_mask = valid.duplicated(keep=False)
    return int(dup_mask.sum()), int(valid[dup_mask].nunique())


def first_available_numeric(df: pd.DataFrame, candidates: list[str]) -> tuple[pd.Series, list[str]]:
    used = [c for c in candidates if c in df.columns]
    out = pd.Series(np.nan, index=df.index, dtype=float)
    for col in used:
        out = out.fillna(to_numeric_nonnegative(df[col]))
    return out, used


def construct_county_fips(state_fips: pd.Series, county_code: pd.Series) -> tuple[pd.Series, dict[str, int]]:
    state_digits = clean_digits(state_fips)
    state_digits = state_digits.str.zfill(2).where(state_digits.notna(), np.nan)

    county_text = clean_text(county_code)
    county_negative = county_text.str.startswith("-").fillna(False)
    county_digits = clean_digits(county_code)

    direct = county_digits.where(county_digits.str.len().isin([4, 5]), np.nan)
    direct = direct.str.zfill(5).where(direct.notna(), np.nan)

    county_part = county_digits.where(county_digits.str.len().isin([1, 2, 3]), np.nan)
    county_part = county_part.str.zfill(3).where(county_part.notna(), np.nan)
    from_parts = (state_digits + county_part).where(state_digits.notna() & county_part.notna(), np.nan)

    county_fips = direct.combine_first(from_parts)
    county_fips = county_fips.where(county_fips.str.match(r"^\d{5}$"), np.nan)
    county_fips = county_fips.where(~county_negative, np.nan)
    county_fips = county_fips.where(county_fips != "00000", np.nan)

    method = pd.Series("missing", index=county_fips.index, dtype=object)
    method = method.where(~direct.notna(), "direct_county_code")
    method = method.where(~(direct.isna() & from_parts.notna()), "state_plus_county")
    method = method.where(county_fips.notna(), "missing")
    return county_fips, method.value_counts().to_dict()


def choose_enrollment_variable(efia: pd.DataFrame) -> tuple[pd.Series, dict[str, object]]:
    direct_present = [c for c in EFIA_DIRECT_12M_COLS if c in efia.columns]
    activity_present = [c for c in EFIA_ACTIVITY_COLS if c in efia.columns]
    fte_present = [c for c in EFIA_FTE_COLS if c in efia.columns]
    fall_present = [c for c in EFIA_FALL_COLS if c in efia.columns]

    if direct_present:
        chosen = direct_present[0]
        return to_numeric_nonnegative(efia[chosen]), {
            "rule_step": "direct_12_month",
            "chosen_expression": chosen,
            "reason": "Direct 12-month enrollment field was present in EFIA.",
            "direct_12m_fields_present": direct_present,
            "activity_fields_present": activity_present,
            "fte_fields_present": fte_present,
            "fall_fields_present": fall_present,
        }

    ug, ug_used = first_available_numeric(efia, ["EFTEUG", "FTEUG"])
    gd, gd_used = first_available_numeric(efia, ["EFTEGD", "FTEGD"])
    dpp, dpp_used = first_available_numeric(efia, ["FTEDPP"])
    if ug_used or gd_used or dpp_used:
        has_any = pd.concat([ug.notna(), gd.notna(), dpp.notna()], axis=1).any(axis=1)
        enrollment = ug.fillna(0.0) + gd.fillna(0.0) + dpp.fillna(0.0)
        enrollment = enrollment.where(has_any, np.nan)
        return enrollment, {
            "rule_step": "fte_fallback",
            "chosen_expression": "EFTEUG/FTEUG + EFTEGD/FTEGD + FTEDPP",
            "reason": "No clear direct 12-month headcount field was present; used total FTE components.",
            "direct_12m_fields_present": direct_present,
            "activity_fields_present": activity_present,
            "fte_fields_present": fte_present,
            "fall_fields_present": fall_present,
            "ug_components_used": ug_used,
            "gd_components_used": gd_used,
            "dpp_components_used": dpp_used,
        }

    if fall_present:
        chosen = fall_present[0]
        return to_numeric_nonnegative(efia[chosen]), {
            "rule_step": "fall_fallback",
            "chosen_expression": chosen,
            "reason": "No direct 12-month or FTE measure found; used fall enrollment.",
            "direct_12m_fields_present": direct_present,
            "activity_fields_present": activity_present,
            "fte_fields_present": fte_present,
            "fall_fields_present": fall_present,
        }

    raise ValueError(
        "Could not identify an enrollment measure in EFIA. "
        f"Direct candidates tried: {EFIA_DIRECT_12M_COLS}; "
        f"FTE candidates tried: {EFIA_FTE_COLS}; "
        f"fall candidates tried: {EFIA_FALL_COLS}."
    )


def build_ipeds_county_files(
    hd_path: Path,
    efia_path: Path,
    institution_out: Path,
    county_out: Path,
    metadata_out: Path,
    excluded_out: Path,
) -> None:
    require_file(hd_path, "IPEDS HD file")
    require_file(efia_path, "IPEDS EFIA file")

    hd = pd.read_csv(hd_path, compression="zip", dtype=str, low_memory=False)
    efia = pd.read_csv(efia_path, compression="zip", dtype=str, low_memory=False)

    hd_unit_col = pick_col(hd, UNITID_COLS, "HD UNITID")
    hd_name_col = pick_col(hd, HD_NAME_COLS, "HD institution name")
    hd_state_abbr_col = pick_col(hd, HD_STATE_ABBR_COLS, "HD state abbreviation")
    hd_county_code_col = pick_col(hd, HD_COUNTY_CODE_COLS, "HD county code")
    hd_county_name_col = pick_col(hd, HD_COUNTY_NAME_COLS, "HD county name", required=False)
    hd_state_fips_col = pick_col(hd, HD_STATE_FIPS_COLS, "HD state FIPS", required=False)
    if hd_state_fips_col is None:
        raise ValueError(
            "Missing state identifier needed for county FIPS fallback. "
            f"Tried HD columns: {HD_STATE_FIPS_COLS}"
        )

    efia_unit_col = pick_col(efia, UNITID_COLS, "EFIA UNITID")

    hd_std = pd.DataFrame(
        {
            "UNITID": standardize_unitid(hd[hd_unit_col]),
            "institution_name": clean_text(hd[hd_name_col]),
            "state_abbr": clean_text(hd[hd_state_abbr_col]).str.upper(),
            "county_code": clean_text(hd[hd_county_code_col]),
            "county_name": clean_text(hd[hd_county_name_col]) 
            if hd_county_name_col
            else np.nan,
            "state_fips_hd": clean_digits(hd[hd_state_fips_col]).str.zfill(2),
        }
    )
    hd_std["county_fips"], county_method_counts = construct_county_fips(
        hd_std["state_fips_hd"], hd_std["county_code"]
    )

    efia_std = pd.DataFrame({"UNITID": standardize_unitid(efia[efia_unit_col])})
    chosen_enrollment, enrollment_decision = choose_enrollment_variable(efia)
    efia_std["college_enrollment_total"] = chosen_enrollment

    hd_dup_rows, hd_dup_unitids = count_duplicate_unitids(hd_std["UNITID"])
    efia_dup_rows, efia_dup_unitids = count_duplicate_unitids(efia_std["UNITID"])
    if hd_dup_rows > 0:
        raise ValueError(
            f"HD has duplicate UNITIDs before merge: {hd_dup_rows} duplicate rows across "
            f"{hd_dup_unitids} UNITIDs."
        )
    if efia_dup_rows > 0:
        raise ValueError(
            f"EFIA has duplicate UNITIDs before merge: {efia_dup_rows} duplicate rows across "
            f"{efia_dup_unitids} UNITIDs."
        )

    merge_audit = hd_std[["UNITID"]].merge(efia_std[["UNITID"]], on="UNITID", how="outer", indicator=True)
    merge_counts = merge_audit["_merge"].value_counts().to_dict()

    merged = hd_std.merge(efia_std, on="UNITID", how="left", validate="one_to_one")
    merged_dup_rows, merged_dup_unitids = count_duplicate_unitids(merged["UNITID"])
    if merged_dup_rows > 0:
        raise ValueError(
            f"Merged file has duplicate UNITIDs: {merged_dup_rows} duplicate rows across "
            f"{merged_dup_unitids} UNITIDs."
        )

    institution_out_df = merged[
        [
            "UNITID",
            "institution_name",
            "state_abbr",
            "county_code",
            "county_name",
            "county_fips",
            "college_enrollment_total",
        ]
    ].copy()

    missing_geo = institution_out_df["county_fips"].isna()
    missing_enrollment = institution_out_df["college_enrollment_total"].isna()
    excluded_mask = missing_geo | missing_enrollment

    excluded = institution_out_df.loc[excluded_mask].copy()
    excluded["exclusion_reason"] = np.select(
        [
            missing_geo.loc[excluded.index] & missing_enrollment.loc[excluded.index],
            missing_geo.loc[excluded.index],
            missing_enrollment.loc[excluded.index],
        ],
        [
            "missing_county_fips_and_enrollment",
            "missing_or_unmappable_county_fips",
            "missing_enrollment",
        ],
        default="other",
    )

    aggregation_base = institution_out_df.loc[~excluded_mask].copy()
    county_out_df = (
        aggregation_base.groupby("county_fips", as_index=False)
        .agg(
            college_enrollment_total=("college_enrollment_total", "sum"),
            institution_count=("UNITID", "nunique"),
        )
        .sort_values("county_fips")
    )

    institution_out.parent.mkdir(parents=True, exist_ok=True)
    county_out.parent.mkdir(parents=True, exist_ok=True)
    metadata_out.parent.mkdir(parents=True, exist_ok=True)
    excluded_out.parent.mkdir(parents=True, exist_ok=True)

    institution_out_df.to_csv(institution_out, index=False)
    county_out_df.to_csv(county_out, index=False)
    excluded.to_csv(excluded_out, index=False)

    excluded_geo_names = (
        excluded.loc[excluded["exclusion_reason"].str.contains("county_fips"), ["UNITID", "institution_name"]]
        .sort_values(["UNITID", "institution_name"])
        .drop_duplicates()
    )
    metadata_lines = [
        "# IPEDS 2024 County Aggregation Metadata",
        "",
        "## Raw files used",
        f"- `{hd_path.as_posix()}`",
        f"- `{efia_path.as_posix()}`",
        "",
        "## Schema inspection",
        "### HD fields selected",
        f"- `UNITID`: `{hd_unit_col}`",
        f"- institution name: `{hd_name_col}`",
        f"- state abbreviation: `{hd_state_abbr_col}`",
        f"- county code: `{hd_county_code_col}`",
        f"- county name: `{hd_county_name_col}`",
        f"- state identifier for county FIPS construction: `{hd_state_fips_col}`",
        "",
        "### EFIA candidate enrollment fields present",
        f"- activity fields present: {enrollment_decision['activity_fields_present']}",
        f"- direct 12-month fields present: {enrollment_decision['direct_12m_fields_present']}",
        f"- FTE fields present: {enrollment_decision['fte_fields_present']}",
        f"- fall fields present: {enrollment_decision['fall_fields_present']}",
        "",
        "## Enrollment variable decision",
        f"- priority rule step used: `{enrollment_decision['rule_step']}`",
        f"- chosen enrollment variable: `{enrollment_decision['chosen_expression']}`",
        f"- reason: {enrollment_decision['reason']}",
    ]

    if "ug_components_used" in enrollment_decision:
        metadata_lines.extend(
            [
                f"- UG component fields used in order: {enrollment_decision['ug_components_used']}",
                f"- graduate component fields used in order: {enrollment_decision['gd_components_used']}",
                f"- doctoral/professional component fields used: {enrollment_decision['dpp_components_used']}",
            ]
        )

    metadata_lines.extend(
        [
            "",
            "## County FIPS construction",
            "- county FIPS built from HD county code directly when available; fallback is state FIPS + county code.",
            f"- construction method counts: {county_method_counts}",
            "",
            "## Duplicate UNITID checks",
            f"- HD before merge: {hd_dup_rows} duplicate rows across {hd_dup_unitids} UNITIDs",
            f"- EFIA before merge: {efia_dup_rows} duplicate rows across {efia_dup_unitids} UNITIDs",
            f"- merged after merge: {merged_dup_rows} duplicate rows across {merged_dup_unitids} UNITIDs",
            f"- UNITID merge audit counts: {merge_counts}",
            "",
            "## Exclusions from county aggregation",
            f"- institutions in cleaned institution file: {len(institution_out_df):,}",
            f"- institutions included in county aggregation: {len(aggregation_base):,}",
            f"- institutions excluded from county aggregation: {len(excluded):,}",
            "- exclusion reasons (counts):",
        ]
    )

    for reason, count in excluded["exclusion_reason"].value_counts().to_dict().items():
        metadata_lines.append(f"  - {reason}: {count}")

    metadata_lines.extend(
        [
            f"- full excluded institution list: `{excluded_out.as_posix()}`",
            "",
            "### Institutions with missing or unmappable county geography",
        ]
    )

    if excluded_geo_names.empty:
        metadata_lines.append("- none")
    else:
        for row in excluded_geo_names.itertuples(index=False):
            metadata_lines.append(f"- {row.UNITID}: {row.institution_name}")

    metadata_lines.extend(
        [
            "",
            "## Output files",
            f"- institution-level cleaned file: `{institution_out.as_posix()}`",
            f"- county-level aggregate file: `{county_out.as_posix()}`",
        ]
    )

    metadata_out.write_text("\n".join(metadata_lines) + "\n", encoding="utf-8")

    print(f"Saved institution-level IPEDS file: {institution_out} ({len(institution_out_df):,} rows)")
    print(f"Saved county-level IPEDS aggregate: {county_out} ({len(county_out_df):,} rows)")
    print(f"Saved excluded-institution audit file: {excluded_out} ({len(excluded):,} rows)")
    print(f"Saved metadata note: {metadata_out}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build county-level IPEDS enrollment aggregates from HD and EFIA.")
    parser.add_argument("--hd", type=Path, default=Path("data/raw/ipeds_hd_2024.zip"))
    parser.add_argument("--efia", type=Path, default=Path("data/raw/ipeds_efia_2024.zip"))
    parser.add_argument(
        "--institution-out",
        type=Path,
        default=Path("data/intermediate/ipeds_institutions_clean_2024.csv"),
    )
    parser.add_argument(
        "--county-out",
        type=Path,
        default=Path("data/intermediate/ipeds_county_aggregate_2024.csv"),
    )
    parser.add_argument(
        "--metadata-out",
        type=Path,
        default=Path("data/intermediate/ipeds_2024_metadata.md"),
    )
    parser.add_argument(
        "--excluded-out",
        type=Path,
        default=Path("data/intermediate/ipeds_excluded_from_county_aggregation_2024.csv"),
    )
    args = parser.parse_args()

    build_ipeds_county_files(
        hd_path=args.hd,
        efia_path=args.efia,
        institution_out=args.institution_out,
        county_out=args.county_out,
        metadata_out=args.metadata_out,
        excluded_out=args.excluded_out,
    )


if __name__ == "__main__":
    main()
