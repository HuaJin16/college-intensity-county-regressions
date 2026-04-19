#!/usr/bin/env python
from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import statsmodels.formula.api as smf

DEFAULT_INPUT = Path("data/processed/county_analysis_2024.csv")
DEFAULT_OUTDIR = Path("outputs")
INDUSTRY_CONTROL_CANDIDATES = ["manuf_emp_share", "leisure_emp_share"]


def winsorize(series: pd.Series, lower_q: float, upper_q: float) -> pd.Series:
    lower = series.quantile(lower_q)
    upper = series.quantile(upper_q)
    return series.clip(lower=lower, upper=upper)


def coerce_numeric(df: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")


def require_columns(df: pd.DataFrame, columns: list[str], context: str) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for {context}: {missing}")


def infer_single_year(df: pd.DataFrame) -> int | None:
    if "year" not in df.columns:
        return None

    years = pd.to_numeric(df["year"], errors="coerce").dropna().astype(int).unique().tolist()
    if len(years) != 1:
        return None
    return int(years[0])


def _parse_int_token(token: str) -> int | None:
    cleaned = token.replace(",", "").strip()
    if not cleaned:
        return None
    if not cleaned.isdigit():
        return None
    return int(cleaned)


def parse_merge_qc_report(path: Path) -> dict:
    if not path.exists():
        return {}

    text = path.read_text(encoding="utf-8")

    info: dict[str, object] = {}

    scope_match = re.search(r"- scope:\s*`([^`]+)`", text)
    if scope_match:
        info["scope"] = scope_match.group(1).strip()

    qcew_match = re.search(r"- QCEW out-of-scope counties:\s*([0-9,]+)", text)
    if qcew_match:
        qcew_val = _parse_int_token(qcew_match.group(1))
        if qcew_val is not None:
            info["qcew_out_of_scope"] = qcew_val

    ipeds_match = re.search(r"- IPEDS out-of-scope counties:\s*([0-9,]+)", text)
    if ipeds_match:
        ipeds_val = _parse_int_token(ipeds_match.group(1))
        if ipeds_val is not None:
            info["ipeds_out_of_scope"] = ipeds_val

    return info


def parse_ipeds_metadata(path: Path) -> dict:
    if not path.exists():
        return {}

    text = path.read_text(encoding="utf-8")
    info: dict[str, object] = {}

    step_match = re.search(r"priority rule step used:\s*`([^`]+)`", text)
    if step_match:
        info["enrollment_step"] = step_match.group(1).strip()

    excluded_match = re.search(r"institutions excluded from county aggregation:\s*([0-9,]+)", text)
    if excluded_match:
        excluded_val = _parse_int_token(excluded_match.group(1))
        if excluded_val is not None:
            info["excluded_total"] = excluded_val

    missing_enrollment_match = re.search(r"missing_enrollment:\s*([0-9,]+)", text)
    if missing_enrollment_match:
        missing_enrollment_val = _parse_int_token(missing_enrollment_match.group(1))
        if missing_enrollment_val is not None:
            info["excluded_missing_enrollment"] = missing_enrollment_val

    missing_geo_match = re.search(r"missing_or_unmappable_county_fips:\s*([0-9,]+)", text)
    if missing_geo_match:
        missing_geo_val = _parse_int_token(missing_geo_match.group(1))
        if missing_geo_val is not None:
            info["excluded_missing_geo"] = missing_geo_val

    return info


def geography_scope_label(scope: str) -> str:
    labels = {
        "us_50_dc": "50 states + DC",
        "us_50_dc_pr": "50 states + DC + Puerto Rico",
    }
    return labels.get(scope, scope)


def parse_qcew_industry_profile(path: Path) -> dict:
    if not path.exists():
        return {}

    try:
        qcew = pd.read_csv(path, usecols=["industry_code"], dtype=str, low_memory=False)
    except ValueError:
        qcew = pd.read_csv(path, dtype=str, low_memory=False)
        if "industry_code" not in qcew.columns:
            return {}

    codes = (
        qcew["industry_code"]
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )
    unique_codes = sorted({code for code in codes if code and code.lower() != "nan"})

    total_industry_codes = {"10", "000000", "0"}
    only_total = bool(unique_codes) and set(unique_codes).issubset(total_industry_codes)

    return {
        "unique_codes": unique_codes,
        "unique_code_count": len(unique_codes),
        "only_total_industry": only_total,
    }


def fit_ols(
    df: pd.DataFrame,
    formula: str,
    required_cols: list[str],
    cluster_state: bool,
) -> tuple:
    sample = df.dropna(subset=required_cols).copy()
    if sample.empty:
        raise ValueError(f"No observations left after complete-case filter for: {formula}")

    model = smf.ols(formula=formula, data=sample)
    if cluster_state:
        result = model.fit(cov_type="cluster", cov_kwds={"groups": sample["state_fips"]})
        se_type = "cluster_state"
    else:
        result = model.fit(cov_type="HC1")
        se_type = "HC1"

    return result, sample, se_type


def tidy_result(result, spec: str, outcome: str, se_type: str) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "term": result.params.index,
            "coef": result.params.values,
            "std_error": result.bse.values,
            "t_stat": result.tvalues.values,
            "p_value": result.pvalues.values,
        }
    )
    out["spec"] = spec
    out["outcome"] = outcome
    out["se_type"] = se_type
    out["nobs"] = int(result.nobs)
    out["r2"] = result.rsquared
    out["adj_r2"] = result.rsquared_adj
    return out


def sample_row(
    spec: str,
    outcome: str,
    formula: str,
    n_total: int,
    n_sample: int,
    se_type: str,
    sample_filter: str = "all_counties",
) -> dict:
    return {
        "spec": spec,
        "outcome": outcome,
        "se_type": se_type,
        "formula": formula,
        "sample_filter": sample_filter,
        "n_total": int(n_total),
        "n_sample": int(n_sample),
        "n_dropped": int(n_total - n_sample),
    }


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


def choose_industry_controls(
    df: pd.DataFrame,
    wage_base_needed: list[str],
    min_coverage: float,
) -> tuple[list[str], dict[str, float]]:
    base_sample = df.dropna(subset=wage_base_needed).copy()
    coverage = {}
    selected = []

    for control in INDUSTRY_CONTROL_CANDIDATES:
        if control not in base_sample.columns:
            coverage[control] = 0.0
            continue

        control_coverage = float(base_sample[control].notna().mean())
        coverage[control] = control_coverage
        if control_coverage >= min_coverage:
            selected.append(control)

    return selected, coverage


def add_college_margin_variables(
    df: pd.DataFrame,
    winsor_lower: float,
    winsor_upper: float,
) -> dict[str, float]:
    if "college_enrollment_total" not in df.columns and "has_college" not in df.columns:
        raise ValueError("Need `college_enrollment_total` or `has_college` to build margin variables.")
    if "college_intensity_pct" not in df.columns:
        raise ValueError("Need `college_intensity_pct` to build margin variables.")

    if "has_college" in df.columns:
        has_college = pd.to_numeric(df["has_college"], errors="coerce").fillna(0)
        df["has_college"] = (has_college > 0).astype(int)
    else:
        college_enrollment = pd.to_numeric(df["college_enrollment_total"], errors="coerce").fillna(0.0)
        df["has_college"] = (college_enrollment > 0).astype(int)

    intensity = pd.to_numeric(df["college_intensity_pct"], errors="coerce")
    positive_mask = df["has_college"].eq(1)
    positive_intensity = intensity.loc[positive_mask].dropna()
    if positive_intensity.empty:
        raise ValueError("No positive-college counties available for margin decomposition.")

    positive_mean = float(positive_intensity.mean())
    centered = pd.Series(0.0, index=df.index, dtype=float)
    centered.loc[positive_mask] = intensity.loc[positive_mask] - positive_mean
    centered = centered.where(~positive_mask | intensity.notna(), float("nan"))
    df["college_intensity_pct_positive_centered"] = centered

    positive_winsorized = winsorize(
        series=positive_intensity,
        lower_q=winsor_lower,
        upper_q=winsor_upper,
    )
    positive_winsorized_mean = float(positive_winsorized.mean())
    winsorized_centered = pd.Series(0.0, index=df.index, dtype=float)
    winsorized_centered.loc[positive_mask] = positive_winsorized - positive_winsorized_mean
    winsorized_centered = winsorized_centered.where(~positive_mask | intensity.notna(), float("nan"))
    df["college_intensity_pct_positive_winsorized_centered"] = winsorized_centered

    return {
        "positive_college_counties": int(positive_mask.sum()),
        "positive_intensity_mean": positive_mean,
        "positive_intensity_winsorized_mean": positive_winsorized_mean,
    }


def write_limitations_memo(
    path: Path,
    df: pd.DataFrame,
    samples: pd.DataFrame,
    industry_controls: list[str],
    industry_coverage: dict[str, float],
    min_industry_coverage: float,
    skipped_specs: list[str],
    merge_qc_info: dict,
    ipeds_metadata_info: dict,
    qcew_industry_info: dict,
) -> None:
    merged_n = len(df)

    def get_n(spec_name: str) -> int:
        match = samples.loc[samples["spec"] == spec_name, "n_sample"]
        if match.empty:
            return 0
        return int(match.iloc[0])

    rent_n = get_n("baseline_rent_hc1")
    wage_n = get_n("baseline_wage_hc1")

    missing_rent = int(df["median_gross_rent"].isna().sum()) if "median_gross_rent" in df.columns else 0
    missing_income = (
        int(df["median_household_income"].isna().sum())
        if "median_household_income" in df.columns
        else 0
    )
    missing_wage = int(df["avg_weekly_wage"].isna().sum()) if "avg_weekly_wage" in df.columns else 0
    zero_college = (
        int((df["college_enrollment_total"] == 0).sum())
        if "college_enrollment_total" in df.columns
        else 0
    )

    lines = [
        "# Limitations",
        "",
        "- This is a cross-sectional associational analysis; coefficients represent conditional correlations, not causal effects.",
    ]

    scope = str(merge_qc_info.get("scope", "")).strip()
    qcew_out_of_scope = merge_qc_info.get("qcew_out_of_scope")
    ipeds_out_of_scope = merge_qc_info.get("ipeds_out_of_scope")
    scope_label = geography_scope_label(scope)
    if scope and isinstance(qcew_out_of_scope, int) and isinstance(ipeds_out_of_scope, int):
        lines.append(
            f"- Geography scope is fixed to the ACS county universe for {scope_label} "
            f"(`{scope}`), so non-ACS-source county FIPS are excluded before merge "
            f"(QCEW dropped {qcew_out_of_scope:,} out-of-scope county FIPS; "
            f"IPEDS dropped {ipeds_out_of_scope:,})."
        )
    elif scope:
        lines.append(
            f"- Geography scope is fixed to the ACS county universe for {scope_label} "
            f"(`{scope}`), which may exclude counties/territories present in non-ACS sources."
        )

    lines.extend(
        [
            f"- Baseline model samples are complete-case subsets of the merged county data (merged N = {merged_n:,}; rent N = {rent_n:,}; wage N = {wage_n:,}).",
            f"- Missingness in merged data before model filtering: `median_gross_rent` = {missing_rent:,} counties, `median_household_income` = {missing_income:,} county, and `avg_weekly_wage` = {missing_wage:,} county.",
            f"- Counties with no colleges are retained with `college_enrollment_total = 0` (count = {zero_college:,}), so identification includes many zero-intensity counties.",
        ]
    )

    excluded_missing_enrollment = ipeds_metadata_info.get("excluded_missing_enrollment")
    if isinstance(excluded_missing_enrollment, int) and excluded_missing_enrollment > 0:
        lines.append(
            "- Extensive-margin models define `has_college = 1[college_enrollment_total > 0]`; because "
            f"{excluded_missing_enrollment:,} IPEDS institutions were excluded for missing enrollment, "
            "some counties with institution records may still be coded as `has_college = 0`."
        )

    if industry_controls:
        lines.append(
            f"- Baseline wage model includes industry controls that met coverage threshold ({min_industry_coverage:.0%}): {', '.join(industry_controls)}."
        )
    else:
        parts = []
        for control in INDUSTRY_CONTROL_CANDIDATES:
            control_cov = industry_coverage.get(control, 0.0)
            parts.append(f"{control}={control_cov:.1%}")
        if bool(qcew_industry_info.get("only_total_industry", False)):
            lines.append(
                "- Baseline wage model omits industry-mix controls because the current QCEW county file "
                "only contains total industry (`industry_code = 10`), yielding 0.0% non-missing "
                f"coverage for `manuf_emp_share` and `leisure_emp_share` ({', '.join(parts)})."
            )
        else:
            lines.append(
                "- Baseline wage model omits industry controls because non-missing coverage is below "
                f"threshold ({min_industry_coverage:.0%}; {', '.join(parts)})."
            )

    enrollment_step = str(ipeds_metadata_info.get("enrollment_step", "")).strip()
    excluded_total = ipeds_metadata_info.get("excluded_total")
    excluded_missing_geo = ipeds_metadata_info.get("excluded_missing_geo")
    if (
        enrollment_step == "fte_fallback"
        and isinstance(excluded_total, int)
        and isinstance(excluded_missing_enrollment, int)
        and isinstance(excluded_missing_geo, int)
    ):
        lines.append(
            "- IPEDS enrollment for this build uses an FTE fallback (not direct 12-month headcount), "
            f"and {excluded_total:,} institutions are excluded from county aggregation "
            f"({excluded_missing_enrollment:,} missing enrollment, {excluded_missing_geo:,} "
            "missing/unmappable county FIPS)."
        )
    else:
        lines.append(
            "- IPEDS enrollment definitions and institution county assignments are source-release "
            "dependent and should be interpreted with the documented data-construction assumptions."
        )

    if "college_intensity_pct" in df.columns:
        intensity = pd.to_numeric(df["college_intensity_pct"], errors="coerce")
        over_100 = int((intensity > 100).sum())
        if over_100 > 0:
            max_val = float(intensity.max())
            top_idx = intensity.idxmax()
            location_hint = ""
            if "county_fips" in df.columns and "county_name" in df.columns:
                top_fips = str(df.loc[top_idx, "county_fips"])
                top_name = str(df.loc[top_idx, "county_name"])
                location_hint = f" ({top_fips}: {top_name})"
            lines.append(
                "- College intensity has an extreme outlier "
                f"({over_100:,} county above 100%; max = {max_val:.2f}%{location_hint}), so "
                "winsorized-intensity robustness estimates should be reviewed alongside baseline estimates."
            )

    if skipped_specs:
        lines.append(
            f"- Optional robustness specs skipped due unavailable columns/data coverage: {', '.join(skipped_specs)}."
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run baseline and robustness county regressions.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    parser.add_argument(
        "--merge-qc",
        type=Path,
        default=None,
        help="Path to merge QC markdown report (default: data/intermediate/merge_qc_<year>.md).",
    )
    parser.add_argument(
        "--ipeds-metadata",
        type=Path,
        default=None,
        help="Path to IPEDS metadata markdown (default: data/intermediate/ipeds_<year>_metadata.md).",
    )
    parser.add_argument(
        "--qcew-raw",
        type=Path,
        default=Path("data/raw/qcew_county.csv"),
        help="Path to raw QCEW county file used for industry-code diagnostics.",
    )
    parser.add_argument("--min-industry-coverage", type=float, default=0.80)
    parser.add_argument("--winsor-lower", type=float, default=0.01)
    parser.add_argument("--winsor-upper", type=float, default=0.99)
    args = parser.parse_args()

    if not (0.0 <= args.winsor_lower < args.winsor_upper <= 1.0):
        raise ValueError("Winsor quantiles must satisfy 0 <= lower < upper <= 1.")

    df = pd.read_csv(args.input, dtype={"county_fips": str, "state_fips": str}, low_memory=False)

    inferred_year = infer_single_year(df)
    default_merge_qc = (
        Path(f"data/intermediate/merge_qc_{inferred_year}.md")
        if inferred_year is not None
        else Path("data/intermediate/merge_qc_2024.md")
    )
    default_ipeds_metadata = (
        Path(f"data/intermediate/ipeds_{inferred_year}_metadata.md")
        if inferred_year is not None
        else Path("data/intermediate/ipeds_2024_metadata.md")
    )
    merge_qc_path = args.merge_qc if args.merge_qc is not None else default_merge_qc
    ipeds_metadata_path = (
        args.ipeds_metadata if args.ipeds_metadata is not None else default_ipeds_metadata
    )
    qcew_raw_path = args.qcew_raw

    merge_qc_info = parse_merge_qc_report(merge_qc_path)
    ipeds_metadata_info = parse_ipeds_metadata(ipeds_metadata_path)
    qcew_industry_info = parse_qcew_industry_profile(qcew_raw_path)

    numeric_cols = [
        "ln_median_gross_rent",
        "ln_avg_weekly_wage",
        "college_intensity_pct",
        "has_college",
        "ln_median_household_income",
        "ln_population",
        "metro",
        "manuf_emp_share",
        "leisure_emp_share",
        "prof_emp_share",
        "renter_share",
        "vacancy_rate",
        "ba_share",
        "median_gross_rent",
        "median_household_income",
        "avg_weekly_wage",
        "college_enrollment_total",
    ]
    coerce_numeric(df, numeric_cols)

    tables_dir = args.outdir / "tables"
    figures_dir = args.outdir / "figures"
    memos_dir = args.outdir / "memos"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    memos_dir.mkdir(parents=True, exist_ok=True)

    margin_info = add_college_margin_variables(
        df=df,
        winsor_lower=args.winsor_lower,
        winsor_upper=args.winsor_upper,
    )

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
    require_columns(df, rent_needed, "baseline rent model")

    wage_base_needed = [
        "ln_avg_weekly_wage",
        "college_intensity_pct",
        "ln_population",
        "metro",
        "state_fips",
    ]
    require_columns(df, wage_base_needed, "baseline wage model")

    industry_controls, industry_coverage = choose_industry_controls(
        df, wage_base_needed, args.min_industry_coverage
    )
    wage_terms = ["college_intensity_pct", "ln_population", "metro"] + industry_controls + [
        "C(state_fips)"
    ]
    wage_formula = "ln_avg_weekly_wage ~ " + " + ".join(wage_terms)
    wage_needed = wage_base_needed + industry_controls

    n_total = len(df)
    sample_rows: list[dict] = []
    summary_rows: list[dict] = []
    skipped_specs: list[str] = []

    rent_base, rent_sample, rent_se_type = fit_ols(
        df=df,
        formula=rent_formula,
        required_cols=rent_needed,
        cluster_state=False,
    )
    baseline_rent = tidy_result(
        result=rent_base,
        spec="baseline_rent_hc1",
        outcome="ln_median_gross_rent",
        se_type=rent_se_type,
    )
    baseline_rent.to_csv(tables_dir / "baseline_rent.csv", index=False)
    summary_rows.append(
        {
            "spec": "baseline_rent_hc1",
            "formula": rent_formula,
            "nobs": int(rent_base.nobs),
            "r2": rent_base.rsquared,
            "adj_r2": rent_base.rsquared_adj,
        }
    )
    sample_rows.append(
        sample_row(
            spec="baseline_rent_hc1",
            outcome="ln_median_gross_rent",
            formula=rent_formula,
            n_total=n_total,
            n_sample=len(rent_sample),
            se_type=rent_se_type,
        )
    )

    wage_base, wage_sample, wage_se_type = fit_ols(
        df=df,
        formula=wage_formula,
        required_cols=wage_needed,
        cluster_state=False,
    )
    baseline_wage = tidy_result(
        result=wage_base,
        spec="baseline_wage_hc1",
        outcome="ln_avg_weekly_wage",
        se_type=wage_se_type,
    )
    baseline_wage.to_csv(tables_dir / "baseline_wage.csv", index=False)
    summary_rows.append(
        {
            "spec": "baseline_wage_hc1",
            "formula": wage_formula,
            "nobs": int(wage_base.nobs),
            "r2": wage_base.rsquared,
            "adj_r2": wage_base.rsquared_adj,
        }
    )
    sample_rows.append(
        sample_row(
            spec="baseline_wage_hc1",
            outcome="ln_avg_weekly_wage",
            formula=wage_formula,
            n_total=n_total,
            n_sample=len(wage_sample),
            se_type=wage_se_type,
        )
    )

    robustness_tables = []

    rent_cluster, rent_cluster_sample, rent_cluster_se = fit_ols(
        df=df,
        formula=rent_formula,
        required_cols=rent_needed,
        cluster_state=True,
    )
    robustness_tables.append(
        tidy_result(
            result=rent_cluster,
            spec="rent_cluster_state",
            outcome="ln_median_gross_rent",
            se_type=rent_cluster_se,
        )
    )
    sample_rows.append(
        sample_row(
            spec="rent_cluster_state",
            outcome="ln_median_gross_rent",
            formula=rent_formula,
            n_total=n_total,
            n_sample=len(rent_cluster_sample),
            se_type=rent_cluster_se,
        )
    )

    wage_cluster, wage_cluster_sample, wage_cluster_se = fit_ols(
        df=df,
        formula=wage_formula,
        required_cols=wage_needed,
        cluster_state=True,
    )
    robustness_tables.append(
        tidy_result(
            result=wage_cluster,
            spec="wage_cluster_state",
            outcome="ln_avg_weekly_wage",
            se_type=wage_cluster_se,
        )
    )
    sample_rows.append(
        sample_row(
            spec="wage_cluster_state",
            outcome="ln_avg_weekly_wage",
            formula=wage_formula,
            n_total=n_total,
            n_sample=len(wage_cluster_sample),
            se_type=wage_cluster_se,
        )
    )

    if "renter_share" in df.columns and df["renter_share"].notna().any():
        rent_renter_formula = (
            "ln_median_gross_rent ~ college_intensity_pct + ln_median_household_income + "
            "ln_population + metro + renter_share + C(state_fips)"
        )
        rent_renter_needed = rent_needed + ["renter_share"]
        rent_renter, rent_renter_sample, rent_renter_se = fit_ols(
            df=df,
            formula=rent_renter_formula,
            required_cols=rent_renter_needed,
            cluster_state=False,
        )
        robustness_tables.append(
            tidy_result(
                result=rent_renter,
                spec="rent_plus_renter_share",
                outcome="ln_median_gross_rent",
                se_type=rent_renter_se,
            )
        )
        sample_rows.append(
            sample_row(
                spec="rent_plus_renter_share",
                outcome="ln_median_gross_rent",
                formula=rent_renter_formula,
                n_total=n_total,
                n_sample=len(rent_renter_sample),
                se_type=rent_renter_se,
            )
        )
    else:
        skipped_specs.append("rent_plus_renter_share")

    if "ba_share" in df.columns and df["ba_share"].notna().any():
        rent_ba_formula = (
            "ln_median_gross_rent ~ college_intensity_pct + ln_median_household_income + "
            "ln_population + metro + ba_share + C(state_fips)"
        )
        rent_ba_needed = rent_needed + ["ba_share"]
        rent_ba, rent_ba_sample, rent_ba_se = fit_ols(
            df=df,
            formula=rent_ba_formula,
            required_cols=rent_ba_needed,
            cluster_state=False,
        )
        robustness_tables.append(
            tidy_result(
                result=rent_ba,
                spec="rent_plus_ba_share",
                outcome="ln_median_gross_rent",
                se_type=rent_ba_se,
            )
        )
        sample_rows.append(
            sample_row(
                spec="rent_plus_ba_share",
                outcome="ln_median_gross_rent",
                formula=rent_ba_formula,
                n_total=n_total,
                n_sample=len(rent_ba_sample),
                se_type=rent_ba_se,
            )
        )
    else:
        skipped_specs.append("rent_plus_ba_share")

    df["college_intensity_pct_w"] = winsorize(
        series=df["college_intensity_pct"],
        lower_q=args.winsor_lower,
        upper_q=args.winsor_upper,
    )

    rent_w_formula = (
        "ln_median_gross_rent ~ college_intensity_pct_w + ln_median_household_income + "
        "ln_population + metro + C(state_fips)"
    )
    rent_w_needed = [
        "ln_median_gross_rent",
        "college_intensity_pct_w",
        "ln_median_household_income",
        "ln_population",
        "metro",
        "state_fips",
    ]
    rent_w, rent_w_sample, rent_w_se = fit_ols(
        df=df,
        formula=rent_w_formula,
        required_cols=rent_w_needed,
        cluster_state=False,
    )
    robustness_tables.append(
        tidy_result(
            result=rent_w,
            spec="rent_winsorized_intensity",
            outcome="ln_median_gross_rent",
            se_type=rent_w_se,
        )
    )
    sample_rows.append(
        sample_row(
            spec="rent_winsorized_intensity",
            outcome="ln_median_gross_rent",
            formula=rent_w_formula,
            n_total=n_total,
            n_sample=len(rent_w_sample),
            se_type=rent_w_se,
        )
    )

    wage_w_terms = ["college_intensity_pct_w", "ln_population", "metro"] + industry_controls + [
        "C(state_fips)"
    ]
    wage_w_formula = "ln_avg_weekly_wage ~ " + " + ".join(wage_w_terms)
    wage_w_needed = [
        "ln_avg_weekly_wage",
        "college_intensity_pct_w",
        "ln_population",
        "metro",
        "state_fips",
    ] + industry_controls
    wage_w, wage_w_sample, wage_w_se = fit_ols(
        df=df,
        formula=wage_w_formula,
        required_cols=wage_w_needed,
        cluster_state=False,
    )
    robustness_tables.append(
        tidy_result(
            result=wage_w,
            spec="wage_winsorized_intensity",
            outcome="ln_avg_weekly_wage",
            se_type=wage_w_se,
        )
    )
    sample_rows.append(
        sample_row(
            spec="wage_winsorized_intensity",
            outcome="ln_avg_weekly_wage",
            formula=wage_w_formula,
            n_total=n_total,
            n_sample=len(wage_w_sample),
            se_type=wage_w_se,
        )
    )

    margin_tables = []

    rent_extensive_formula = (
        "ln_median_gross_rent ~ has_college + ln_median_household_income + "
        "ln_population + metro + C(state_fips)"
    )
    rent_extensive_needed = [
        "ln_median_gross_rent",
        "has_college",
        "ln_median_household_income",
        "ln_population",
        "metro",
        "state_fips",
    ]
    rent_extensive, rent_extensive_sample, rent_extensive_se = fit_ols(
        df=df,
        formula=rent_extensive_formula,
        required_cols=rent_extensive_needed,
        cluster_state=False,
    )
    margin_tables.append(
        tidy_result(
            result=rent_extensive,
            spec="rent_extensive_hc1",
            outcome="ln_median_gross_rent",
            se_type=rent_extensive_se,
        )
    )
    summary_rows.append(
        {
            "spec": "rent_extensive_hc1",
            "formula": rent_extensive_formula,
            "nobs": int(rent_extensive.nobs),
            "r2": rent_extensive.rsquared,
            "adj_r2": rent_extensive.rsquared_adj,
        }
    )
    sample_rows.append(
        sample_row(
            spec="rent_extensive_hc1",
            outcome="ln_median_gross_rent",
            formula=rent_extensive_formula,
            n_total=n_total,
            n_sample=len(rent_extensive_sample),
            se_type=rent_extensive_se,
        )
    )

    rent_intensive_positive, rent_intensive_positive_sample, rent_intensive_positive_se = fit_ols(
        df=df[df["has_college"] == 1].copy(),
        formula=rent_formula,
        required_cols=rent_needed,
        cluster_state=False,
    )
    margin_tables.append(
        tidy_result(
            result=rent_intensive_positive,
            spec="rent_intensive_positive_hc1",
            outcome="ln_median_gross_rent",
            se_type=rent_intensive_positive_se,
        )
    )
    summary_rows.append(
        {
            "spec": "rent_intensive_positive_hc1",
            "formula": rent_formula,
            "nobs": int(rent_intensive_positive.nobs),
            "r2": rent_intensive_positive.rsquared,
            "adj_r2": rent_intensive_positive.rsquared_adj,
        }
    )
    sample_rows.append(
        sample_row(
            spec="rent_intensive_positive_hc1",
            outcome="ln_median_gross_rent",
            formula=rent_formula,
            n_total=n_total,
            n_sample=len(rent_intensive_positive_sample),
            se_type=rent_intensive_positive_se,
            sample_filter="has_college == 1",
        )
    )

    rent_two_part_formula = (
        "ln_median_gross_rent ~ has_college + college_intensity_pct_positive_centered + "
        "ln_median_household_income + ln_population + metro + C(state_fips)"
    )
    rent_two_part_needed = [
        "ln_median_gross_rent",
        "has_college",
        "college_intensity_pct_positive_centered",
        "ln_median_household_income",
        "ln_population",
        "metro",
        "state_fips",
    ]
    rent_two_part, rent_two_part_sample, rent_two_part_se = fit_ols(
        df=df,
        formula=rent_two_part_formula,
        required_cols=rent_two_part_needed,
        cluster_state=False,
    )
    margin_tables.append(
        tidy_result(
            result=rent_two_part,
            spec="rent_two_part_hc1",
            outcome="ln_median_gross_rent",
            se_type=rent_two_part_se,
        )
    )
    summary_rows.append(
        {
            "spec": "rent_two_part_hc1",
            "formula": rent_two_part_formula,
            "nobs": int(rent_two_part.nobs),
            "r2": rent_two_part.rsquared,
            "adj_r2": rent_two_part.rsquared_adj,
        }
    )
    sample_rows.append(
        sample_row(
            spec="rent_two_part_hc1",
            outcome="ln_median_gross_rent",
            formula=rent_two_part_formula,
            n_total=n_total,
            n_sample=len(rent_two_part_sample),
            se_type=rent_two_part_se,
        )
    )

    rent_two_part_cluster, rent_two_part_cluster_sample, rent_two_part_cluster_se = fit_ols(
        df=df,
        formula=rent_two_part_formula,
        required_cols=rent_two_part_needed,
        cluster_state=True,
    )
    margin_tables.append(
        tidy_result(
            result=rent_two_part_cluster,
            spec="rent_two_part_cluster_state",
            outcome="ln_median_gross_rent",
            se_type=rent_two_part_cluster_se,
        )
    )
    summary_rows.append(
        {
            "spec": "rent_two_part_cluster_state",
            "formula": rent_two_part_formula,
            "nobs": int(rent_two_part_cluster.nobs),
            "r2": rent_two_part_cluster.rsquared,
            "adj_r2": rent_two_part_cluster.rsquared_adj,
        }
    )
    sample_rows.append(
        sample_row(
            spec="rent_two_part_cluster_state",
            outcome="ln_median_gross_rent",
            formula=rent_two_part_formula,
            n_total=n_total,
            n_sample=len(rent_two_part_cluster_sample),
            se_type=rent_two_part_cluster_se,
        )
    )

    rent_two_part_w_formula = (
        "ln_median_gross_rent ~ has_college + college_intensity_pct_positive_winsorized_centered + "
        "ln_median_household_income + ln_population + metro + C(state_fips)"
    )
    rent_two_part_w_needed = [
        "ln_median_gross_rent",
        "has_college",
        "college_intensity_pct_positive_winsorized_centered",
        "ln_median_household_income",
        "ln_population",
        "metro",
        "state_fips",
    ]
    rent_two_part_w, rent_two_part_w_sample, rent_two_part_w_se = fit_ols(
        df=df,
        formula=rent_two_part_w_formula,
        required_cols=rent_two_part_w_needed,
        cluster_state=False,
    )
    margin_tables.append(
        tidy_result(
            result=rent_two_part_w,
            spec="rent_two_part_winsorized_intensity",
            outcome="ln_median_gross_rent",
            se_type=rent_two_part_w_se,
        )
    )
    summary_rows.append(
        {
            "spec": "rent_two_part_winsorized_intensity",
            "formula": rent_two_part_w_formula,
            "nobs": int(rent_two_part_w.nobs),
            "r2": rent_two_part_w.rsquared,
            "adj_r2": rent_two_part_w.rsquared_adj,
        }
    )
    sample_rows.append(
        sample_row(
            spec="rent_two_part_winsorized_intensity",
            outcome="ln_median_gross_rent",
            formula=rent_two_part_w_formula,
            n_total=n_total,
            n_sample=len(rent_two_part_w_sample),
            se_type=rent_two_part_w_se,
        )
    )

    wage_extensive_terms = ["has_college", "ln_population", "metro"] + industry_controls + [
        "C(state_fips)"
    ]
    wage_extensive_formula = "ln_avg_weekly_wage ~ " + " + ".join(wage_extensive_terms)
    wage_extensive_needed = [
        "ln_avg_weekly_wage",
        "has_college",
        "ln_population",
        "metro",
        "state_fips",
    ] + industry_controls
    wage_extensive, wage_extensive_sample, wage_extensive_se = fit_ols(
        df=df,
        formula=wage_extensive_formula,
        required_cols=wage_extensive_needed,
        cluster_state=False,
    )
    margin_tables.append(
        tidy_result(
            result=wage_extensive,
            spec="wage_extensive_hc1",
            outcome="ln_avg_weekly_wage",
            se_type=wage_extensive_se,
        )
    )
    summary_rows.append(
        {
            "spec": "wage_extensive_hc1",
            "formula": wage_extensive_formula,
            "nobs": int(wage_extensive.nobs),
            "r2": wage_extensive.rsquared,
            "adj_r2": wage_extensive.rsquared_adj,
        }
    )
    sample_rows.append(
        sample_row(
            spec="wage_extensive_hc1",
            outcome="ln_avg_weekly_wage",
            formula=wage_extensive_formula,
            n_total=n_total,
            n_sample=len(wage_extensive_sample),
            se_type=wage_extensive_se,
        )
    )

    wage_intensive_positive, wage_intensive_positive_sample, wage_intensive_positive_se = fit_ols(
        df=df[df["has_college"] == 1].copy(),
        formula=wage_formula,
        required_cols=wage_needed,
        cluster_state=False,
    )
    margin_tables.append(
        tidy_result(
            result=wage_intensive_positive,
            spec="wage_intensive_positive_hc1",
            outcome="ln_avg_weekly_wage",
            se_type=wage_intensive_positive_se,
        )
    )
    summary_rows.append(
        {
            "spec": "wage_intensive_positive_hc1",
            "formula": wage_formula,
            "nobs": int(wage_intensive_positive.nobs),
            "r2": wage_intensive_positive.rsquared,
            "adj_r2": wage_intensive_positive.rsquared_adj,
        }
    )
    sample_rows.append(
        sample_row(
            spec="wage_intensive_positive_hc1",
            outcome="ln_avg_weekly_wage",
            formula=wage_formula,
            n_total=n_total,
            n_sample=len(wage_intensive_positive_sample),
            se_type=wage_intensive_positive_se,
            sample_filter="has_college == 1",
        )
    )

    wage_two_part_terms = [
        "has_college",
        "college_intensity_pct_positive_centered",
        "ln_population",
        "metro",
    ] + industry_controls + ["C(state_fips)"]
    wage_two_part_formula = "ln_avg_weekly_wage ~ " + " + ".join(wage_two_part_terms)
    wage_two_part_needed = [
        "ln_avg_weekly_wage",
        "has_college",
        "college_intensity_pct_positive_centered",
        "ln_population",
        "metro",
        "state_fips",
    ] + industry_controls
    wage_two_part, wage_two_part_sample, wage_two_part_se = fit_ols(
        df=df,
        formula=wage_two_part_formula,
        required_cols=wage_two_part_needed,
        cluster_state=False,
    )
    margin_tables.append(
        tidy_result(
            result=wage_two_part,
            spec="wage_two_part_hc1",
            outcome="ln_avg_weekly_wage",
            se_type=wage_two_part_se,
        )
    )
    summary_rows.append(
        {
            "spec": "wage_two_part_hc1",
            "formula": wage_two_part_formula,
            "nobs": int(wage_two_part.nobs),
            "r2": wage_two_part.rsquared,
            "adj_r2": wage_two_part.rsquared_adj,
        }
    )
    sample_rows.append(
        sample_row(
            spec="wage_two_part_hc1",
            outcome="ln_avg_weekly_wage",
            formula=wage_two_part_formula,
            n_total=n_total,
            n_sample=len(wage_two_part_sample),
            se_type=wage_two_part_se,
        )
    )

    wage_two_part_cluster, wage_two_part_cluster_sample, wage_two_part_cluster_se = fit_ols(
        df=df,
        formula=wage_two_part_formula,
        required_cols=wage_two_part_needed,
        cluster_state=True,
    )
    margin_tables.append(
        tidy_result(
            result=wage_two_part_cluster,
            spec="wage_two_part_cluster_state",
            outcome="ln_avg_weekly_wage",
            se_type=wage_two_part_cluster_se,
        )
    )
    summary_rows.append(
        {
            "spec": "wage_two_part_cluster_state",
            "formula": wage_two_part_formula,
            "nobs": int(wage_two_part_cluster.nobs),
            "r2": wage_two_part_cluster.rsquared,
            "adj_r2": wage_two_part_cluster.rsquared_adj,
        }
    )
    sample_rows.append(
        sample_row(
            spec="wage_two_part_cluster_state",
            outcome="ln_avg_weekly_wage",
            formula=wage_two_part_formula,
            n_total=n_total,
            n_sample=len(wage_two_part_cluster_sample),
            se_type=wage_two_part_cluster_se,
        )
    )

    wage_two_part_w_terms = [
        "has_college",
        "college_intensity_pct_positive_winsorized_centered",
        "ln_population",
        "metro",
    ] + industry_controls + ["C(state_fips)"]
    wage_two_part_w_formula = "ln_avg_weekly_wage ~ " + " + ".join(wage_two_part_w_terms)
    wage_two_part_w_needed = [
        "ln_avg_weekly_wage",
        "has_college",
        "college_intensity_pct_positive_winsorized_centered",
        "ln_population",
        "metro",
        "state_fips",
    ] + industry_controls
    wage_two_part_w, wage_two_part_w_sample, wage_two_part_w_se = fit_ols(
        df=df,
        formula=wage_two_part_w_formula,
        required_cols=wage_two_part_w_needed,
        cluster_state=False,
    )
    margin_tables.append(
        tidy_result(
            result=wage_two_part_w,
            spec="wage_two_part_winsorized_intensity",
            outcome="ln_avg_weekly_wage",
            se_type=wage_two_part_w_se,
        )
    )
    summary_rows.append(
        {
            "spec": "wage_two_part_winsorized_intensity",
            "formula": wage_two_part_w_formula,
            "nobs": int(wage_two_part_w.nobs),
            "r2": wage_two_part_w.rsquared,
            "adj_r2": wage_two_part_w.rsquared_adj,
        }
    )
    sample_rows.append(
        sample_row(
            spec="wage_two_part_winsorized_intensity",
            outcome="ln_avg_weekly_wage",
            formula=wage_two_part_w_formula,
            n_total=n_total,
            n_sample=len(wage_two_part_w_sample),
            se_type=wage_two_part_w_se,
        )
    )

    robustness = pd.concat(robustness_tables, ignore_index=True)
    robustness.to_csv(tables_dir / "robustness.csv", index=False)

    margin_decomposition = pd.concat(margin_tables, ignore_index=True)
    margin_decomposition.to_csv(tables_dir / "margin_decomposition.csv", index=False)

    samples_df = pd.DataFrame(sample_rows)
    samples_df.to_csv(tables_dir / "model_samples.csv", index=False)

    summary_stats = pd.DataFrame(summary_rows)
    summary_stats.to_csv(tables_dir / "model_summary_stats.csv", index=False)

    residual_plot(
        result=rent_base,
        path=figures_dir / "rent_residuals_vs_fitted.png",
        title="Rent model residuals vs fitted",
    )
    residual_plot(
        result=wage_base,
        path=figures_dir / "wage_residuals_vs_fitted.png",
        title="Wage model residuals vs fitted",
    )

    write_limitations_memo(
        path=memos_dir / "limitations.md",
        df=df,
        samples=samples_df,
        industry_controls=industry_controls,
        industry_coverage=industry_coverage,
        min_industry_coverage=args.min_industry_coverage,
        skipped_specs=skipped_specs,
        merge_qc_info=merge_qc_info,
        ipeds_metadata_info=ipeds_metadata_info,
        qcew_industry_info=qcew_industry_info,
    )

    print(f"Baseline rent sample: {len(rent_sample):,} of {n_total:,} counties")
    print(f"Baseline wage sample: {len(wage_sample):,} of {n_total:,} counties")
    print(
        "Margin decomposition uses "
        f"{margin_info['positive_college_counties']:,} counties with `has_college = 1` "
        f"(mean positive-county intensity = {margin_info['positive_intensity_mean']:.2f} pp)."
    )
    if industry_controls:
        print(f"Included wage industry controls: {industry_controls}")
    else:
        coverage_text = ", ".join(
            f"{control}={industry_coverage.get(control, 0.0):.1%}"
            for control in INDUSTRY_CONTROL_CANDIDATES
        )
        print(
            "No wage industry controls met the minimum coverage threshold "
            f"({args.min_industry_coverage:.0%}; {coverage_text})."
        )

    print(f"Saved tables: {tables_dir}")
    print(f"Saved margin table: {tables_dir / 'margin_decomposition.csv'}")
    print(f"Saved figures: {figures_dir}")
    print(f"Saved memo: {memos_dir / 'limitations.md'}")


if __name__ == "__main__":
    main()
