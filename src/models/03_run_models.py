#!/usr/bin/env python
from __future__ import annotations

import argparse
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
) -> dict:
    return {
        "spec": spec,
        "outcome": outcome,
        "se_type": se_type,
        "formula": formula,
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


def write_limitations_memo(
    path: Path,
    df: pd.DataFrame,
    samples: pd.DataFrame,
    industry_controls: list[str],
    industry_coverage: dict[str, float],
    min_industry_coverage: float,
    skipped_specs: list[str],
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
        f"- Baseline model samples are complete-case subsets of the merged county data (merged N = {merged_n:,}; rent N = {rent_n:,}; wage N = {wage_n:,}).",
        f"- Missingness in merged data before model filtering: median_gross_rent = {missing_rent:,}, median_household_income = {missing_income:,}, avg_weekly_wage = {missing_wage:,}.",
        f"- Counties with no college enrollment are retained with college_enrollment_total = 0 (count = {zero_college:,}).",
    ]

    if industry_controls:
        lines.append(
            f"- Baseline wage model includes industry controls that met coverage threshold ({min_industry_coverage:.0%}): {', '.join(industry_controls)}."
        )
    else:
        parts = []
        for control in INDUSTRY_CONTROL_CANDIDATES:
            control_cov = industry_coverage.get(control, 0.0)
            parts.append(f"{control}={control_cov:.1%}")
        lines.append(
            f"- Baseline wage model omits industry controls because non-missing coverage is below threshold ({min_industry_coverage:.0%}; {', '.join(parts)})."
        )

    lines.append(
        "- IPEDS enrollment definitions and institution county assignments are source-release dependent and should be interpreted with the documented data-construction assumptions."
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
    parser.add_argument("--min-industry-coverage", type=float, default=0.80)
    parser.add_argument("--winsor-lower", type=float, default=0.01)
    parser.add_argument("--winsor-upper", type=float, default=0.99)
    args = parser.parse_args()

    if not (0.0 <= args.winsor_lower < args.winsor_upper <= 1.0):
        raise ValueError("Winsor quantiles must satisfy 0 <= lower < upper <= 1.")

    df = pd.read_csv(args.input, dtype={"county_fips": str, "state_fips": str}, low_memory=False)

    numeric_cols = [
        "ln_median_gross_rent",
        "ln_avg_weekly_wage",
        "college_intensity_pct",
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

    robustness = pd.concat(robustness_tables, ignore_index=True)
    robustness.to_csv(tables_dir / "robustness.csv", index=False)

    samples_df = pd.DataFrame(sample_rows)
    samples_df.to_csv(tables_dir / "model_samples.csv", index=False)

    summary_stats = pd.DataFrame(
        [
            {
                "spec": "baseline_rent_hc1",
                "formula": rent_formula,
                "nobs": int(rent_base.nobs),
                "r2": rent_base.rsquared,
                "adj_r2": rent_base.rsquared_adj,
            },
            {
                "spec": "baseline_wage_hc1",
                "formula": wage_formula,
                "nobs": int(wage_base.nobs),
                "r2": wage_base.rsquared,
                "adj_r2": wage_base.rsquared_adj,
            },
        ]
    )
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
    )

    print(f"Baseline rent sample: {len(rent_sample):,} of {n_total:,} counties")
    print(f"Baseline wage sample: {len(wage_sample):,} of {n_total:,} counties")
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
    print(f"Saved figures: {figures_dir}")
    print(f"Saved memo: {memos_dir / 'limitations.md'}")


if __name__ == "__main__":
    main()
