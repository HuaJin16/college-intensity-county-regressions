#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DEFAULT_TABLES_DIR = Path("outputs/tables")
DEFAULT_OUTDIR = Path("outputs/presentation")
DEFAULT_DATA_PATH = Path("data/processed/county_analysis_2024.csv")

INTENSITY_SPEC_ORDER = [
    "baseline_rent_hc1",
    "rent_cluster_state",
    "rent_plus_renter_share",
    "rent_plus_ba_share",
    "rent_winsorized_intensity",
    "baseline_wage_hc1",
    "wage_cluster_state",
    "wage_winsorized_intensity",
]

MARGIN_SPEC_ORDER = [
    "rent_extensive_hc1",
    "rent_intensive_positive_hc1",
    "rent_two_part_hc1",
    "rent_two_part_cluster_state",
    "rent_two_part_winsorized_intensity",
    "wage_extensive_hc1",
    "wage_intensive_positive_hc1",
    "wage_two_part_hc1",
    "wage_two_part_cluster_state",
    "wage_two_part_winsorized_intensity",
]

SPEC_ORDER = INTENSITY_SPEC_ORDER + MARGIN_SPEC_ORDER

SPEC_LABELS = {
    "baseline_rent_hc1": "Rent baseline (HC1)",
    "rent_cluster_state": "Rent baseline (state-clustered SE)",
    "rent_plus_renter_share": "Rent + renter share",
    "rent_plus_ba_share": "Rent + BA share",
    "rent_winsorized_intensity": "Rent winsorized intensity",
    "baseline_wage_hc1": "Wage baseline (HC1)",
    "wage_cluster_state": "Wage baseline (state-clustered SE)",
    "wage_winsorized_intensity": "Wage winsorized intensity",
    "rent_extensive_hc1": "Rent extensive margin (HC1)",
    "rent_intensive_positive_hc1": "Rent intensive margin among college counties",
    "rent_two_part_hc1": "Rent joint extensive/intensive model",
    "rent_two_part_cluster_state": "Rent joint model (state-clustered SE)",
    "rent_two_part_winsorized_intensity": "Rent joint model, winsorized intensity",
    "wage_extensive_hc1": "Wage extensive margin (HC1)",
    "wage_intensive_positive_hc1": "Wage intensive margin among college counties",
    "wage_two_part_hc1": "Wage joint extensive/intensive model",
    "wage_two_part_cluster_state": "Wage joint model (state-clustered SE)",
    "wage_two_part_winsorized_intensity": "Wage joint model, winsorized intensity",
}

OUTCOME_LABELS = {
    "ln_median_gross_rent": "Log median gross rent",
    "ln_avg_weekly_wage": "Log average weekly wage",
}

TERM_LABELS = {
    "college_intensity_pct": "College intensity (1 pp)",
    "college_intensity_pct_w": "College intensity, winsorized (1 pp)",
    "has_college": "Extensive margin (0/1)",
    "college_intensity_pct_positive_centered": "Intensive margin (1 pp from positive-county mean)",
    "college_intensity_pct_positive_winsorized_centered": "Intensive margin, winsorized (1 pp from positive-county mean)",
}

TERM_ORDER = {
    "has_college": 1,
    "college_intensity_pct": 2,
    "college_intensity_pct_w": 3,
    "college_intensity_pct_positive_centered": 4,
    "college_intensity_pct_positive_winsorized_centered": 5,
}

COMPARISON_PLAN = {
    "ln_median_gross_rent": [
        ("Pooled comparison", "baseline_rent_hc1", "college_intensity_pct"),
        ("Extensive only", "rent_extensive_hc1", "has_college"),
        ("Intensive only", "rent_intensive_positive_hc1", "college_intensity_pct"),
        ("Joint extensive", "rent_two_part_hc1", "has_college"),
        (
            "Joint intensive",
            "rent_two_part_hc1",
            "college_intensity_pct_positive_centered",
        ),
    ],
    "ln_avg_weekly_wage": [
        ("Pooled comparison", "baseline_wage_hc1", "college_intensity_pct"),
        ("Extensive only", "wage_extensive_hc1", "has_college"),
        ("Intensive only", "wage_intensive_positive_hc1", "college_intensity_pct"),
        ("Joint extensive", "wage_two_part_hc1", "has_college"),
        (
            "Joint intensive",
            "wage_two_part_hc1",
            "college_intensity_pct_positive_centered",
        ),
    ],
}


def require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")


def significance_stars(p_value: float) -> str:
    if p_value < 0.01:
        return "***"
    if p_value < 0.05:
        return "**"
    if p_value < 0.1:
        return "*"
    return ""


def load_regression_tables(tables_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    baseline_rent_path = tables_dir / "baseline_rent.csv"
    baseline_wage_path = tables_dir / "baseline_wage.csv"
    robustness_path = tables_dir / "robustness.csv"
    margin_path = tables_dir / "margin_decomposition.csv"
    samples_path = tables_dir / "model_samples.csv"

    require_file(baseline_rent_path, "baseline rent table")
    require_file(baseline_wage_path, "baseline wage table")
    require_file(robustness_path, "robustness table")
    require_file(margin_path, "margin decomposition table")
    require_file(samples_path, "model sample table")

    baseline_rent = pd.read_csv(baseline_rent_path)
    baseline_wage = pd.read_csv(baseline_wage_path)
    robustness = pd.read_csv(robustness_path)
    margin = pd.read_csv(margin_path)
    samples = pd.read_csv(samples_path)

    coeffs = pd.concat([baseline_rent, baseline_wage, robustness, margin], ignore_index=True)
    return coeffs, samples


def build_key_coefficients(
    coeffs: pd.DataFrame,
    samples: pd.DataFrame,
    key_terms: set[str],
    key_specs: list[str] | None = None,
) -> pd.DataFrame:
    key = coeffs[coeffs["term"].isin(key_terms)].copy()
    if key_specs is not None:
        key = key[key["spec"].isin(key_specs)].copy()
    if key.empty:
        raise ValueError("No college-intensity coefficients found in regression tables.")

    key["measure_note"] = np.select(
        [
            key["term"].eq("college_intensity_pct_w"),
            key["term"].eq("college_intensity_pct_positive_centered"),
            key["term"].eq("college_intensity_pct_positive_winsorized_centered"),
            key["term"].eq("has_college"),
        ],
        [
            "winsorized (1st/99th pct)",
            "positive-county centered",
            "winsorized positive-county centered",
            "indicator",
        ],
        default="raw",
    )
    key["ci_low"] = key["coef"] - 1.96 * key["std_error"]
    key["ci_high"] = key["coef"] + 1.96 * key["std_error"]
    key["implied_pct_change"] = 100.0 * (np.exp(key["coef"]) - 1.0)
    key["stars"] = key["p_value"].apply(significance_stars)
    key["spec_label"] = key["spec"].map(SPEC_LABELS).fillna(key["spec"])
    key["outcome_label"] = key["outcome"].map(OUTCOME_LABELS).fillna(key["outcome"])
    key["term_label"] = key["term"].map(TERM_LABELS).fillna(key["term"])
    key.loc[
        key["spec"].isin(MARGIN_SPEC_ORDER) & key["term"].eq("college_intensity_pct"),
        "term_label",
    ] = "Intensive margin among college counties (1 pp)"

    sample_cols = [
        col
        for col in ["spec", "n_sample", "n_dropped", "se_type", "sample_filter"]
        if col in samples.columns
    ]
    if sample_cols:
        sample_info = samples[sample_cols].drop_duplicates(subset=["spec"])
        key = key.merge(sample_info, on="spec", how="left", suffixes=("", "_sample"))

    key["spec_order"] = key["spec"].apply(
        lambda spec: SPEC_ORDER.index(spec) if spec in SPEC_ORDER else 999
    )
    key["term_order"] = key["term"].map(TERM_ORDER).fillna(999)
    key = key.sort_values(["spec_order", "outcome", "term_order"]).reset_index(drop=True)
    return key


def load_data_summary(data_path: Path) -> dict[str, object]:
    require_file(data_path, "processed county dataset")
    df = pd.read_csv(data_path, dtype={"county_fips": str, "state_fips": str}, low_memory=False)
    if "has_college" in df.columns:
        has_college = pd.to_numeric(df["has_college"], errors="coerce").fillna(0)
    else:
        college_enrollment = pd.to_numeric(df["college_enrollment_total"], errors="coerce").fillna(0.0)
        has_college = (college_enrollment > 0).astype(int)

    institution_total = 0
    if "institution_count" in df.columns:
        institution_total = int(pd.to_numeric(df["institution_count"], errors="coerce").fillna(0).sum())

    has_college_count = int((has_college > 0).sum())
    county_total = int(len(df))
    no_college_count = county_total - has_college_count
    college_share = 100.0 * has_college_count / county_total if county_total else 0.0
    includes_puerto_rico = bool(df["state_fips"].eq("72").any()) if "state_fips" in df.columns else False
    scope_label = "50 states + DC + Puerto Rico" if includes_puerto_rico else "50 states + DC"

    return {
        "county_total": county_total,
        "has_college_count": has_college_count,
        "no_college_count": no_college_count,
        "institution_total": institution_total,
        "college_share": college_share,
        "scope_label": scope_label,
    }


def fmt_num(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}"


def fmt_p(value: float) -> str:
    if value < 0.001:
        return "<0.001"
    return f"{value:.3f}"


def fmt_p_text(value: float) -> str:
    p_value = fmt_p(value)
    return f"p{p_value}" if p_value.startswith("<") else f"p={p_value}"


def format_sample_filter(value: str) -> str:
    mapping = {
        "all_counties": "All counties",
        "has_college == 1": "College counties only",
    }
    return mapping.get(value, value)


def lookup_row(df: pd.DataFrame, spec: str, term: str | None = None) -> pd.Series | None:
    subset = df.loc[df["spec"] == spec]
    if term is not None:
        subset = subset.loc[subset["term"] == term]
    if subset.empty:
        return None
    return subset.iloc[0]


def format_effect_cell(row: pd.Series | None) -> str:
    if row is None:
        return "NA"

    implied = float(row["implied_pct_change"])
    stars = row.get("stars", "") or ""
    if row["term"] == "has_college":
        return f"{implied:+.2f}%{stars}"
    return f"{implied:+.2f}% per +1 pp{stars}"


def comparison_takeaway(outcome: str, cells: dict[str, pd.Series | None]) -> str:
    presence = cells.get("Extensive only")
    intensive_only = cells.get("Intensive only")
    two_part_presence = cells.get("Joint extensive")
    two_part_intensity = cells.get("Joint intensive")

    if outcome == "ln_median_gross_rent":
        if two_part_intensity is not None and float(two_part_intensity["p_value"]) < 0.05:
            if two_part_presence is not None and float(two_part_presence["p_value"]) >= 0.10:
                return "The intensive margin matters more than the extensive margin."
        if intensive_only is not None and float(intensive_only["p_value"]) < 0.05:
            return "Rent rises mainly on the intensive margin."
        return "Rent evidence is mixed across the margins."

    if intensive_only is not None and float(intensive_only["p_value"]) < 0.05:
        if two_part_intensity is not None and float(two_part_intensity["p_value"]) >= 0.10:
            return "Any wage signal is limited to the intensive margin within college counties."
    if presence is not None and float(presence["p_value"]) >= 0.10:
        return "No robust countywide wage premium shows up."
    return "Wage evidence stays weak in pooled models."


def build_margin_comparison(intensity_key: pd.DataFrame, margin_key: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    comparison_rows: list[dict[str, object]] = []
    plot_rows: list[dict[str, object]] = []

    combined = pd.concat([intensity_key, margin_key], ignore_index=True)
    for outcome, plan in COMPARISON_PLAN.items():
        row_map: dict[str, pd.Series | None] = {}
        for label, spec, term in plan:
            row = lookup_row(combined, spec, term)
            row_map[label] = row
            if row is None:
                continue

            ci_low_pct = 100.0 * (np.exp(float(row["ci_low"])) - 1.0)
            ci_high_pct = 100.0 * (np.exp(float(row["ci_high"])) - 1.0)
            plot_rows.append(
                {
                    "outcome": outcome,
                    "outcome_label": OUTCOME_LABELS.get(outcome, outcome),
                    "comparison": label,
                    "coef_pct": float(row["implied_pct_change"]),
                    "ci_low_pct": ci_low_pct,
                    "ci_high_pct": ci_high_pct,
                    "term": row["term"],
                    "stars": row.get("stars", "") or "",
                }
            )

        comparison_rows.append(
                {
                    "Outcome": OUTCOME_LABELS.get(outcome, outcome),
                    "Pooled comparison": format_effect_cell(row_map.get("Pooled comparison")),
                    "Extensive only (0/1)": format_effect_cell(row_map.get("Extensive only")),
                    "Intensive only (+1 pp)": format_effect_cell(row_map.get("Intensive only")),
                    "Joint extensive (0/1)": format_effect_cell(row_map.get("Joint extensive")),
                    "Joint intensive (+1 pp)": format_effect_cell(row_map.get("Joint intensive")),
                    "Presentation takeaway": comparison_takeaway(outcome, row_map),
                }
            )

    return pd.DataFrame(comparison_rows), pd.DataFrame(plot_rows)


def format_effect_with_p(row: pd.Series | None, include_per_pp: bool = True) -> str:
    if row is None:
        return "NA"

    implied = float(row["implied_pct_change"])
    p_text = fmt_p(float(row["p_value"]))
    p_label = f"p {p_text}" if p_text.startswith("<") else f"p={p_text}"
    if row["term"] == "has_college" or not include_per_pp:
        return f"{implied:+.2f}% ({p_label})"
    return f"{implied:+.2f}% per +1 pp ({p_label})"


def format_coef_se(row: pd.Series | None) -> str:
    if row is None:
        return "NA"

    stars = row.get("stars", "") or ""
    return f"{fmt_num(float(row['coef']))}{stars} ({fmt_num(float(row['std_error']))})"


def build_paper_baseline_table(intensity_key: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for spec, outcome_label in [
        ("baseline_rent_hc1", "Median gross rent"),
        ("baseline_wage_hc1", "Average weekly wage"),
    ]:
        row = lookup_row(intensity_key, spec, "college_intensity_pct")
        if row is None:
            continue
        rows.append(
            {
                "Outcome": outcome_label,
                "Coefficient on college intensity": f"{fmt_num(float(row['coef']))} ({fmt_num(float(row['std_error']))})",
                "p-value": fmt_p(float(row["p_value"])),
                "Approx. % change": f"{float(row['implied_pct_change']):+.2f}% per +1 pp",
                "N": int(row["n_sample"]),
            }
        )
    return pd.DataFrame(rows)


def build_paper_presence_size_table(margin_key: pd.DataFrame) -> pd.DataFrame:
    rows = []
    plans = [
        ("Median gross rent", "rent_extensive_hc1", "rent_intensive_positive_hc1", "rent_two_part_hc1"),
        ("Average weekly wage", "wage_extensive_hc1", "wage_intensive_positive_hc1", "wage_two_part_hc1"),
    ]
    for outcome_label, extensive_spec, intensive_spec, joint_spec in plans:
        presence_only = lookup_row(margin_key, extensive_spec, "has_college")
        size_only = lookup_row(margin_key, intensive_spec, "college_intensity_pct")
        joint_presence = lookup_row(margin_key, joint_spec, "has_college")
        joint_size = lookup_row(margin_key, joint_spec, "college_intensity_pct_positive_centered")
        takeaway = ""
        if outcome_label == "Median gross rent":
            takeaway = "The intensive margin matters more than the extensive margin for rent."
        else:
            takeaway = "Neither the extensive nor the intensive margin shows a strong pooled wage relationship."

        rows.append(
            {
                "Outcome": outcome_label,
                "Extensive margin only": format_coef_se(presence_only),
                "Intensive margin only": format_coef_se(size_only),
                "Extensive margin in joint model": format_coef_se(joint_presence),
                "Intensive margin in joint model": format_coef_se(joint_size),
                "Main takeaway": takeaway,
            }
        )
    return pd.DataFrame(rows)


def build_paper_robustness_table(intensity_key: pd.DataFrame, margin_key: pd.DataFrame) -> pd.DataFrame:
    rows = []

    def add_single(outcome: str, check: str, row: pd.Series | None) -> None:
        if row is None:
            return
        rows.append(
            {
                "Outcome": outcome,
                "Robustness check": check,
                "Result": format_coef_se(row),
            }
        )

    def add_joint(outcome: str, check: str, presence_row: pd.Series | None, size_row: pd.Series | None) -> None:
        if presence_row is None or size_row is None:
            return
        rows.append(
            {
                "Outcome": outcome,
                "Robustness check": check,
                "Result": (
                    f"extensive {format_coef_se(presence_row)}; "
                    f"intensive {format_coef_se(size_row)}"
                ),
            }
        )

    add_single("Median gross rent", "State-clustered standard errors", lookup_row(intensity_key, "rent_cluster_state", "college_intensity_pct"))
    add_single("Median gross rent", "Add renter share", lookup_row(intensity_key, "rent_plus_renter_share", "college_intensity_pct"))
    add_single("Median gross rent", "Add bachelor's degree share", lookup_row(intensity_key, "rent_plus_ba_share", "college_intensity_pct"))
    add_single("Median gross rent", "Outlier-adjusted college intensity", lookup_row(intensity_key, "rent_winsorized_intensity", "college_intensity_pct_w"))
    add_joint(
        "Median gross rent",
        "Joint model with state-clustered standard errors",
        lookup_row(margin_key, "rent_two_part_cluster_state", "has_college"),
        lookup_row(margin_key, "rent_two_part_cluster_state", "college_intensity_pct_positive_centered"),
    )
    add_joint(
        "Median gross rent",
        "Joint model with outlier-adjusted intensive term",
        lookup_row(margin_key, "rent_two_part_winsorized_intensity", "has_college"),
        lookup_row(margin_key, "rent_two_part_winsorized_intensity", "college_intensity_pct_positive_winsorized_centered"),
    )

    add_single("Average weekly wage", "State-clustered standard errors", lookup_row(intensity_key, "wage_cluster_state", "college_intensity_pct"))
    add_single("Average weekly wage", "Outlier-adjusted college intensity", lookup_row(intensity_key, "wage_winsorized_intensity", "college_intensity_pct_w"))
    add_joint(
        "Average weekly wage",
        "Joint model with state-clustered standard errors",
        lookup_row(margin_key, "wage_two_part_cluster_state", "has_college"),
        lookup_row(margin_key, "wage_two_part_cluster_state", "college_intensity_pct_positive_centered"),
    )
    add_joint(
        "Average weekly wage",
        "Joint model with outlier-adjusted intensive term",
        lookup_row(margin_key, "wage_two_part_winsorized_intensity", "has_college"),
        lookup_row(margin_key, "wage_two_part_winsorized_intensity", "college_intensity_pct_positive_winsorized_centered"),
    )

    return pd.DataFrame(rows)


def write_results_brief(
    path: Path,
    intensity_key: pd.DataFrame,
    margin_key: pd.DataFrame,
    comparison_table: pd.DataFrame,
) -> None:
    lines = [
        "# Presentation Results Brief",
        "",
        "Key coefficient shown below is the estimated association for a 1 percentage-point increase in county college intensity.",
        "",
        "| Specification | Outcome | Coef (SE) | 95% CI | p-value | N |",
        "|---|---|---:|---:|---:|---:|",
    ]

    for row in intensity_key.itertuples(index=False):
        coef_cell = f"{fmt_num(row.coef)}{row.stars} ({fmt_num(row.std_error)})"
        ci_cell = f"[{fmt_num(row.ci_low)}, {fmt_num(row.ci_high)}]"
        n_sample = int(row.n_sample) if pd.notna(row.n_sample) else ""
        lines.append(
            f"| {row.spec_label} | {row.outcome_label} | {coef_cell} | {ci_cell} | {fmt_p(row.p_value)} | {n_sample} |"
        )

    rent_base = lookup_row(intensity_key, "baseline_rent_hc1")
    wage_base = lookup_row(intensity_key, "baseline_wage_hc1")
    rent_presence = lookup_row(margin_key, "rent_two_part_hc1", "has_college")
    rent_conditional = lookup_row(
        margin_key,
        "rent_two_part_hc1",
        "college_intensity_pct_positive_centered",
    )
    wage_presence = lookup_row(margin_key, "wage_two_part_hc1", "has_college")
    wage_conditional = lookup_row(
        margin_key,
        "wage_two_part_hc1",
        "college_intensity_pct_positive_centered",
    )
    wage_intensive_only = lookup_row(margin_key, "wage_intensive_positive_hc1", "college_intensity_pct")

    lines.extend(["", "## Slide-ready takeaway"])
    if rent_base is not None:
        rent_pct = float(rent_base["implied_pct_change"])
        lines.append(
            "- Baseline rent model: college intensity is positively associated with rent "
            f"(beta={fmt_num(rent_base['coef'])}, {fmt_p_text(float(rent_base['p_value']))}), "
            f"about {fmt_num(rent_pct, 2)}% higher rent per +1 pp college intensity."
        )
    if wage_base is not None:
        wage_pct = float(wage_base["implied_pct_change"])
        lines.append(
            "- Baseline wage model: association with wage is near zero and statistically weak "
            f"(beta={fmt_num(wage_base['coef'])}, {fmt_p_text(float(wage_base['p_value']))}, "
            f"~{fmt_num(wage_pct, 2)}% per +1 pp)."
        )
    if rent_presence is not None and rent_conditional is not None:
        lines.append(
            "- Rent extensive/intensive results: once the two margins are separated, the extensive-margin indicator is near zero "
            f"(beta={fmt_num(rent_presence['coef'])}, {fmt_p_text(float(rent_presence['p_value']))}), while the intensive-margin term stays positive "
            f"(beta={fmt_num(rent_conditional['coef'])}, {fmt_p_text(float(rent_conditional['p_value']))})."
        )
    if wage_presence is not None and wage_conditional is not None and wage_intensive_only is not None:
        lines.append(
            "- Wage extensive/intensive results: the joint model shows little evidence for either the extensive or intensive margin, "
            f"but the college-only intensive spec is modestly positive (beta={fmt_num(wage_intensive_only['coef'])}, {fmt_p_text(float(wage_intensive_only['p_value']))})."
        )

    if not comparison_table.empty:
        comparison_columns = list(comparison_table.columns)
        lines.extend(
            [
                "",
                "## One-Slide Comparison",
                "",
                "| " + " | ".join(comparison_columns) + " |",
                "|" + "|".join(["---"] * len(comparison_columns)) + "|",
            ]
        )
        for _, row in comparison_table.iterrows():
            lines.append("| " + " | ".join(str(row[col]) for col in comparison_columns) + " |")

    if not margin_key.empty:
        lines.extend(
            [
                "",
                "## Extensive And Intensive Margins",
                "",
                "| Specification | Outcome | Term | Coef (SE) | 95% CI | p-value | N | Sample |",
                "|---|---|---|---:|---:|---:|---:|---|",
            ]
        )
        for row in margin_key.itertuples(index=False):
            coef_cell = f"{fmt_num(row.coef)}{row.stars} ({fmt_num(row.std_error)})"
            ci_cell = f"[{fmt_num(row.ci_low)}, {fmt_num(row.ci_high)}]"
            n_sample = int(row.n_sample) if pd.notna(row.n_sample) else ""
            sample_filter = row.sample_filter if pd.notna(row.sample_filter) else "all_counties"
            sample_filter = format_sample_filter(sample_filter)
            lines.append(
                f"| {row.spec_label} | {row.outcome_label} | {row.term_label} | {coef_cell} | {ci_cell} | {fmt_p(row.p_value)} | {n_sample} | {sample_filter} |"
            )

    lines.extend(
        [
            "- Interpretation remains associational (cross-sectional; not causal).",
            "",
            "Notes: * p<0.10, ** p<0.05, *** p<0.01",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_coefficient_plot(path: Path, key: pd.DataFrame) -> None:
    outcome_order = ["ln_median_gross_rent", "ln_avg_weekly_wage"]
    colors = {
        "ln_median_gross_rent": "#1f77b4",
        "ln_avg_weekly_wage": "#ff7f0e",
    }

    fig, axes = plt.subplots(1, 2, figsize=(14, 8), sharex=False)

    for idx, outcome in enumerate(outcome_order):
        ax = axes[idx]
        subset = key[key["outcome"] == outcome].copy()
        subset = subset.sort_values("spec_order")

        if subset.empty:
            ax.text(0.5, 0.5, "No estimates", ha="center", va="center", transform=ax.transAxes)
            ax.axis("off")
            continue

        y_pos = np.arange(len(subset))
        x = subset["coef"].to_numpy()
        x_err = 1.96 * subset["std_error"].to_numpy()

        ax.errorbar(
            x,
            y_pos,
            xerr=x_err,
            fmt="o",
            color=colors.get(outcome, "#333333"),
            ecolor="#666666",
            elinewidth=1.4,
            capsize=3,
            markersize=6,
        )
        ax.axvline(0.0, color="black", linewidth=1)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(subset["spec_label"])
        ax.invert_yaxis()
        ax.set_xlabel("Coefficient on college intensity")
        ax.set_title(OUTCOME_LABELS.get(outcome, outcome))

    fig.suptitle("College intensity coefficient across baseline and robustness specs", y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def make_margin_comparison_plot(path: Path, plot_df: pd.DataFrame) -> None:
    colors = {
        "Pooled comparison": "#0f766e",
        "Extensive only": "#1d4ed8",
        "Intensive only": "#b45309",
        "Joint extensive": "#7c3aed",
        "Joint intensive": "#dc2626",
    }
    markers = {
        "Pooled comparison": "D",
        "Extensive only": "s",
        "Intensive only": "o",
        "Joint extensive": "^",
        "Joint intensive": "o",
    }

    outcome_order = ["ln_median_gross_rent", "ln_avg_weekly_wage"]
    label_order = [
        "Pooled comparison",
        "Extensive only",
        "Intensive only",
        "Joint extensive",
        "Joint intensive",
    ]

    fig, axes = plt.subplots(1, 2, figsize=(15, 8), sharex=True)
    if len(outcome_order) == 1:
        axes = [axes]

    for idx, outcome in enumerate(outcome_order):
        ax = axes[idx]
        subset = plot_df[plot_df["outcome"] == outcome].copy()
        subset["label_order"] = subset["comparison"].map({label: i for i, label in enumerate(label_order)})
        subset = subset.sort_values("label_order")

        if subset.empty:
            ax.text(0.5, 0.5, "No estimates", ha="center", va="center", transform=ax.transAxes)
            ax.axis("off")
            continue

        y_pos = np.arange(len(subset))
        lower_err = subset["coef_pct"] - subset["ci_low_pct"]
        upper_err = subset["ci_high_pct"] - subset["coef_pct"]

        for pos, row, low, high in zip(y_pos, subset.itertuples(index=False), lower_err, upper_err):
            ax.errorbar(
                x=row.coef_pct,
                y=pos,
                xerr=np.array([[low], [high]]),
                fmt=markers.get(row.comparison, "o"),
                color=colors.get(row.comparison, "#333333"),
                ecolor="#5f6773",
                elinewidth=1.5,
                capsize=3,
                markersize=8,
            )

        ax.axvline(0.0, color="black", linewidth=1)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(subset["comparison"])
        ax.invert_yaxis()
        ax.set_xlabel("Implied % change in outcome")
        ax.set_title(OUTCOME_LABELS.get(outcome, outcome))
        ax.grid(axis="x", color="#d6dde6", linewidth=0.8, alpha=0.7)

    fig.suptitle("Pooled comparison versus extensive and intensive margins", y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def build_display_table(df: pd.DataFrame) -> pd.DataFrame:
    display = df.copy()
    display["stars"] = display["stars"].fillna("")
    display["Coefficient (SE)"] = display.apply(
        lambda row: f"{fmt_num(row['coef'])}{row['stars']} ({fmt_num(row['std_error'])})",
        axis=1,
    )
    display["95% CI"] = display.apply(
        lambda row: f"[{fmt_num(row['ci_low'])}, {fmt_num(row['ci_high'])}]",
        axis=1,
    )
    display["p-value"] = display["p_value"].apply(fmt_p)
    display["N"] = display["n_sample"].fillna(display["nobs"]).astype(int)
    display["Implied % change"] = display["implied_pct_change"].map(
        lambda value: f"{value:.2f}%"
    )
    if "sample_filter" in display.columns:
        display["sample_filter"] = display["sample_filter"].fillna("all_counties")
        display["sample_filter"] = display["sample_filter"].map(format_sample_filter)

    keep_cols = [
        "spec_label",
        "outcome_label",
        "term_label",
        "measure_note",
        "Coefficient (SE)",
        "95% CI",
        "p-value",
        "Implied % change",
        "N",
        "sample_filter",
        "se_type",
    ]
    keep_cols = [col for col in keep_cols if col in display.columns]
    display = display[keep_cols].copy()
    display = display.rename(
        columns={
            "spec_label": "Specification",
            "outcome_label": "Outcome",
            "term_label": "Term",
            "measure_note": "Measure",
            "sample_filter": "Sample",
            "se_type": "SE type",
        }
    )
    return display


def write_talk_track(
    path: Path,
    baseline: pd.DataFrame,
    margin: pd.DataFrame,
    data_summary: dict[str, object],
) -> None:
    rent_base = lookup_row(baseline, "baseline_rent_hc1", "college_intensity_pct")
    wage_base = lookup_row(baseline, "baseline_wage_hc1", "college_intensity_pct")
    rent_presence = lookup_row(margin, "rent_two_part_hc1", "has_college")
    rent_intensity = lookup_row(margin, "rent_two_part_hc1", "college_intensity_pct_positive_centered")
    wage_presence = lookup_row(margin, "wage_two_part_hc1", "has_college")
    wage_intensity = lookup_row(margin, "wage_two_part_hc1", "college_intensity_pct_positive_centered")
    wage_intensive_only = lookup_row(margin, "wage_intensive_positive_hc1", "college_intensity_pct")

    lines = [
        "# Presentation Talk Track",
        "",
        "## Open",
        f"- We study {int(data_summary['county_total']):,} counties and ask a simple question: do counties with more college activity tend to have higher rents and higher wages?",
        f"- About {data_summary['college_share']:.1f}% of counties have measured college enrollment, so separating presence from size matters empirically.",
        "",
        "## Baseline story",
    ]

    if rent_base is not None:
        lines.append(
            "- In the pooled baseline rent model, a 1 percentage-point increase in college intensity is associated with "
            f"about {float(rent_base['implied_pct_change']):.2f}% higher rent ({fmt_p_text(float(rent_base['p_value']))})."
        )
    if wage_base is not None:
        lines.append(
            "- In the pooled baseline wage model, the estimate is only "
            f"about {float(wage_base['implied_pct_change']):.2f}% per +1 pp and is statistically weak ({fmt_p_text(float(wage_base['p_value']))})."
        )

    lines.extend([
        "",
        "## Main interpretation",
    ])

    if rent_presence is not None and rent_intensity is not None:
        lines.append(
            "- The rent result is mostly an intensive-margin story: the extensive margin is close to zero, but larger college footprints inside college counties are associated with higher rents."
        )
        lines.append(
            "- In other words, the extensive-margin shift from no college presence to average positive college presence does not move rent much after controls; the intensive margin from a smaller to a larger college county does."
        )
    if wage_presence is not None and wage_intensity is not None:
        lines.append(
            "- The wage result is much weaker: in the joint extensive/intensive specification, neither the extensive-margin term nor the intensive-margin term is precise."
        )
    if wage_intensive_only is not None:
        lines.append(
            "- The only wage signal is inside the college-county subsample, where the intensive-margin estimate is modestly positive, so I would describe the wage evidence as suggestive but not robust."
        )

    lines.extend(
        [
            "",
            "## Close",
            "- My presentation takeaway is: colleges look more connected to local housing-market pressure than to broad county wage premiums.",
            "- This remains a cross-sectional associational exercise, so the results should be framed as conditional correlations rather than causal effects.",
            "- The next upgrade with the highest payoff is adding county industry-mix controls from a richer QCEW extract to strengthen the wage side.",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def add_html_table_caption(table_html: str, caption: str) -> str:
    table_open_end = table_html.find(">")
    if table_open_end == -1:
        raise ValueError("Expected opening table tag in HTML output.")
    return f"{table_html[:table_open_end + 1]}\n  <caption>{caption}</caption>{table_html[table_open_end + 1:]}"


def write_paper_results_html(
    path: Path,
    baseline_table: pd.DataFrame,
    presence_size_table: pd.DataFrame,
    robustness_table: pd.DataFrame,
    data_summary: dict[str, object],
) -> None:
    generated_on = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    scope_label = str(data_summary["scope_label"])

    baseline_html = add_html_table_caption(
        baseline_table.to_html(index=False, border=0, classes="results-table"),
        "Table 5.1. Pooled Associations of College Intensity with County Rent and Wage Outcomes",
    )
    presence_size_html = add_html_table_caption(
        presence_size_table.to_html(index=False, border=0, classes="results-table"),
        "Table 5.2. Extensive- and Intensive-Margin Associations of College Presence and College Size with County Rent and Wage Outcomes",
    )
    robustness_html = add_html_table_caption(
        robustness_table.to_html(index=False, border=0, classes="results-table"),
        "Table 5.3. Robustness Checks for College-Intensity Associations with County Rent and Wage Outcomes",
    )

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>County College Extensive And Intensive Margin Results</title>
  <style>
    :root {{
      --bg: #f7f4ef;
      --panel: #ffffff;
      --ink: #20242a;
      --muted: #66717d;
      --accent: #8a3b12;
      --border: #d8dedf;
      --header: #f3f7f7;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Georgia", "Times New Roman", serif;
      color: var(--ink);
      background: linear-gradient(180deg, #fcfaf7 0%, var(--bg) 100%);
      line-height: 1.5;
    }}
    .wrap {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 28px 18px 40px;
    }}
    .hero {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-top: 6px solid var(--accent);
      border-radius: 14px;
      padding: 22px 24px;
      box-shadow: 0 6px 18px rgba(40, 45, 50, 0.06);
    }}
    h1, h2 {{
      margin: 0 0 10px;
      font-weight: 700;
      letter-spacing: 0.2px;
    }}
    h1 {{ font-size: 30px; }}
    h2 {{ font-size: 22px; }}
    p {{ margin: 8px 0; }}
    .grid {{
      display: grid;
      gap: 18px;
      margin-top: 18px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 18px;
      box-shadow: 0 4px 12px rgba(40, 45, 50, 0.05);
    }}
    .results-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    .results-table caption {{
      caption-side: top;
      text-align: left;
      font-weight: 700;
      font-size: 15px;
      margin-bottom: 10px;
      color: var(--ink);
    }}
    .results-table th,
    .results-table td {{
      padding: 10px 8px;
      border-bottom: 1px solid var(--border);
      text-align: left;
      vertical-align: top;
    }}
    .results-table th {{
      background: var(--header);
      color: #24323a;
      font-weight: 700;
    }}
    .note {{
      margin-top: 10px;
      color: var(--muted);
      font-size: 13px;
    }}
    @media (max-width: 820px) {{
      .wrap {{ padding: 14px; }}
      h1 {{ font-size: 24px; }}
      h2 {{ font-size: 20px; }}
      .results-table {{ font-size: 13px; }}
    }}
  </style>
</head>
<body>
  <main class="wrap">
    <section class="hero">
      <h1>County College Extensive And Intensive Margin Results</h1>
      <p>Condensed results tables aligned with the paper's results section.</p>
      <p>Cross-sectional county-level regressions for rent and wage outcomes ({scope_label}). Generated: {generated_on}</p>
    </section>

    <section class="grid">
      <article class="card">
        <h2>Pooled Comparison Estimates</h2>
        {baseline_html}
        <p class="note">These full-sample models provide a compact reference point, but they combine extensive-margin and intensive-margin variation into one coefficient.</p>
      </article>

      <article class="card">
        <h2>Extensive And Intensive Margin Results</h2>
        {presence_size_html}
        <p class="note">Coefficients are shown with standard errors in parentheses. The first two columns show the extensive-only and intensive-only results, while the joint-model columns show the extensive and intensive margins estimated together in the same regression. * p&lt;0.10, ** p&lt;0.05, *** p&lt;0.01.</p>
      </article>

      <article class="card">
        <h2>Robustness Checks</h2>
        {robustness_html}
        <p class="note">Coefficients are shown with standard errors in parentheses. State-clustered rows change the standard errors, and outlier-adjusted rows reduce the influence of unusually large college-intensity values. * p&lt;0.10, ** p&lt;0.05, *** p&lt;0.01. All estimates remain associational, not causal.</p>
      </article>
    </section>
  </main>
</body>
</html>
"""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def write_presentation_html(
    path: Path,
    intensity_key: pd.DataFrame,
    baseline: pd.DataFrame,
    margin: pd.DataFrame,
    comparison_table: pd.DataFrame,
    data_summary: dict[str, object],
) -> None:
    baseline_table = build_display_table(baseline)
    all_specs_table = build_display_table(intensity_key)
    margin_table = build_display_table(margin)
    comparison_html = comparison_table.to_html(index=False, escape=False, border=0, classes="results-table")

    baseline_html = baseline_table.to_html(index=False, escape=False, border=0, classes="results-table")
    all_specs_html = all_specs_table.to_html(index=False, escape=False, border=0, classes="results-table")
    margin_html = margin_table.to_html(index=False, escape=False, border=0, classes="results-table")

    rent_row = lookup_row(baseline, "baseline_rent_hc1")
    wage_row = lookup_row(baseline, "baseline_wage_hc1")
    rent_presence = lookup_row(margin, "rent_two_part_hc1", "has_college")
    rent_conditional = lookup_row(margin, "rent_two_part_hc1", "college_intensity_pct_positive_centered")
    wage_presence = lookup_row(margin, "wage_two_part_hc1", "has_college")
    wage_conditional = lookup_row(margin, "wage_two_part_hc1", "college_intensity_pct_positive_centered")

    takeaway_lines = []
    if rent_row is not None:
        rent_pct = float(rent_row["implied_pct_change"])
        takeaway_lines.append(
            "<li><strong>Rent baseline:</strong> college intensity is positively associated with rent "
            f"(beta={fmt_num(rent_row['coef'])}, {fmt_p_text(float(rent_row['p_value']))}), "
            f"about {fmt_num(rent_pct, 2)}% higher rent per +1 pp college intensity.</li>"
        )
    if wage_row is not None:
        wage_pct = float(wage_row["implied_pct_change"])
        takeaway_lines.append(
            "<li><strong>Wage baseline:</strong> association with wage is near zero and statistically weak "
            f"(beta={fmt_num(wage_row['coef'])}, {fmt_p_text(float(wage_row['p_value']))}, ~{fmt_num(wage_pct, 2)}% per +1 pp).</li>"
        )
    if rent_presence is not None and rent_conditional is not None:
        takeaway_lines.append(
            "<li><strong>Rent extensive/intensive results:</strong> the extensive-margin indicator is near zero once the two margins are separated, while the intensive-margin term remains positive and precise.</li>"
        )
    if wage_presence is not None and wage_conditional is not None:
        takeaway_lines.append(
            "<li><strong>Wage extensive/intensive results:</strong> neither the extensive-margin indicator nor the pooled intensive-margin term is precise in the full-sample joint model.</li>"
        )
    takeaway_lines.append(
        "<li><strong>Interpretation:</strong> estimates are associational (cross-sectional), not causal.</li>"
    )

    generated_on = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    county_total = int(data_summary["county_total"])
    has_college_count = int(data_summary["has_college_count"])
    no_college_count = int(data_summary["no_college_count"])
    institution_total = int(data_summary["institution_total"])
    college_share = float(data_summary["college_share"])
    scope_label = str(data_summary["scope_label"])

    html = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>County College Intensity - Presentation Summary</title>
  <style>
    :root {{
      --bg: #f4f2ee;
      --panel: #ffffff;
      --ink: #1f2328;
      --muted: #5f6773;
      --accent: #0e7490;
      --accent-soft: #dff3f8;
      --border: #d6dde6;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Source Sans Pro", "Trebuchet MS", "Segoe UI", sans-serif;
      color: var(--ink);
      background: radial-gradient(circle at 20% 10%, #eef7fb 0%, var(--bg) 50%, #ebe7df 100%);
      line-height: 1.5;
    }}
    .wrap {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 28px 18px 40px;
    }}
    .hero {{
      background: linear-gradient(135deg, #0e7490, #155e75);
      color: #fff;
      border-radius: 16px;
      padding: 24px 26px;
      box-shadow: 0 10px 24px rgba(13, 40, 60, 0.18);
    }}
    h1, h2 {{
      font-family: "Merriweather", Georgia, serif;
      margin: 0 0 12px;
      letter-spacing: 0.2px;
    }}
    h1 {{ font-size: 30px; }}
    h2 {{ font-size: 22px; margin-top: 0; }}
    .hero p {{ margin: 6px 0; opacity: 0.96; }}
    .grid {{
      display: grid;
      gap: 18px;
      margin-top: 18px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 18px;
      box-shadow: 0 4px 14px rgba(24, 36, 48, 0.07);
    }}
    .takeaways {{
      background: var(--accent-soft);
      border-left: 5px solid var(--accent);
      padding: 12px 14px;
      border-radius: 8px;
    }}
    .takeaways ul {{ margin: 8px 0 0 18px; padding: 0; }}
    .takeaways li {{ margin: 7px 0; }}
    .results-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    .results-table th,
    .results-table td {{
      border-bottom: 1px solid var(--border);
      text-align: left;
      padding: 9px 8px;
      vertical-align: top;
    }}
    .results-table th {{
      background: #f5f9fc;
      color: #1b3240;
      font-weight: 700;
    }}
    .figure-box img {{
      width: 100%;
      height: auto;
      border: 1px solid var(--border);
      border-radius: 10px;
      background: #fff;
    }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }}
    .kpi {{
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 10px 12px;
      background: #fbfdff;
    }}
    .kpi .label {{
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 3px;
    }}
    .kpi .value {{
      font-size: 24px;
      font-weight: 700;
      color: #123247;
      line-height: 1.1;
    }}
    .foot {{
      margin-top: 14px;
      color: var(--muted);
      font-size: 13px;
    }}
    @media (max-width: 820px) {{
      h1 {{ font-size: 24px; }}
      h2 {{ font-size: 20px; }}
      .wrap {{ padding: 14px; }}
      .hero {{ padding: 18px; }}
      .card {{ padding: 14px; }}
      .results-table {{ font-size: 13px; }}
      .kpi-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
  </style>
</head>
<body>
  <main class=\"wrap\">
    <section class=\"hero\">
      <h1>County College Intensity - Presentation Summary</h1>
      <p>Cross-sectional county regressions for rent and wage outcomes ({scope_label}).</p>
      <p>Generated: {generated_on}</p>
    </section>

    <section class=\"grid\">
      <article class=\"card\">
        <h2>Executive Takeaways</h2>
        <div class=\"takeaways\">
          <ul>
            {''.join(takeaway_lines)}
          </ul>
        </div>
      </article>

      <article class=\"card figure-box\">
        <h2>Coefficient Plot (College Intensity Term)</h2>
        <img src=\"college_intensity_coef_plot.png\" alt=\"Coefficient plot across model specifications\" />
      </article>

      <article class=\"card figure-box\">
        <h2>One-Slide Comparison Plot</h2>
        <img src=\"margin_comparison_plot.png\" alt=\"Baseline versus extensive and intensive margin comparison plot\" />
      </article>

      <article class=\"card\">
        <h2>Data Snapshot</h2>
        <div class=\"kpi-grid\">
          <div class=\"kpi\">
            <div class=\"label\">Final county rows</div>
            <div class=\"value\">{county_total:,}</div>
          </div>
          <div class=\"kpi\">
            <div class=\"label\">Counties with colleges</div>
            <div class=\"value\">{has_college_count:,}</div>
          </div>
          <div class=\"kpi\">
            <div class=\"label\">Counties without colleges</div>
            <div class=\"value\">{no_college_count:,}</div>
          </div>
          <div class=\"kpi\">
            <div class=\"label\">IPEDS institutions in scope</div>
            <div class=\"value\">{institution_total:,}</div>
          </div>
        </div>
        <p class=\"foot\">College-presence share in the final county file: {college_share:.1f}%.</p>
      </article>

      <article class=\"card\">
        <h2>Baseline Results (Slide Table)</h2>
        {baseline_html}
      </article>

      <article class=\"card\">
        <h2>One-Slide Comparison Table</h2>
        {comparison_html}
      </article>

      <article class=\"card\">
        <h2>All Key Coefficients (Baseline + Robustness)</h2>
        {all_specs_html}
      </article>

      <article class=\"card\">
        <h2>Extensive And Intensive Margins</h2>
        {margin_html}
      </article>
    </section>

    <p class=\"foot\">Notes: * p&lt;0.10, ** p&lt;0.05, *** p&lt;0.01. Coefficients are conditional associations, not causal effects.</p>
  </main>
</body>
</html>
"""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build presentation-ready regression outputs.")
    parser.add_argument("--tables-dir", type=Path, default=DEFAULT_TABLES_DIR)
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH)
    args = parser.parse_args()

    coeffs, samples = load_regression_tables(args.tables_dir)
    intensity_key = build_key_coefficients(
        coeffs,
        samples,
        key_terms={"college_intensity_pct", "college_intensity_pct_w"},
        key_specs=INTENSITY_SPEC_ORDER,
    )
    margin_key = build_key_coefficients(
        coeffs,
        samples,
        key_terms={
            "has_college",
            "college_intensity_pct",
            "college_intensity_pct_positive_centered",
            "college_intensity_pct_positive_winsorized_centered",
        },
        key_specs=MARGIN_SPEC_ORDER,
    )
    comparison_table, comparison_plot_df = build_margin_comparison(intensity_key, margin_key)
    paper_baseline_table = build_paper_baseline_table(intensity_key)
    paper_presence_size_table = build_paper_presence_size_table(margin_key)
    paper_robustness_table = build_paper_robustness_table(intensity_key, margin_key)
    data_summary = load_data_summary(args.data)

    args.outdir.mkdir(parents=True, exist_ok=True)

    key_cols = [
        "spec",
        "spec_label",
        "outcome",
        "outcome_label",
        "term",
        "term_label",
        "measure_note",
        "coef",
        "std_error",
        "ci_low",
        "ci_high",
        "p_value",
        "stars",
        "nobs",
        "n_sample",
        "sample_filter",
        "r2",
        "se_type",
        "implied_pct_change",
    ]
    key_cols = [col for col in key_cols if col in intensity_key.columns]
    intensity_out = intensity_key[key_cols].copy()
    intensity_out.to_csv(args.outdir / "college_intensity_key_coefficients.csv", index=False)

    margin_cols = [col for col in key_cols if col in margin_key.columns]
    margin_out = margin_key[margin_cols].copy()
    margin_out.to_csv(args.outdir / "margin_decomposition_key_coefficients.csv", index=False)
    comparison_table.to_csv(args.outdir / "margin_comparison_table.csv", index=False)

    baseline_specs = ["baseline_rent_hc1", "baseline_wage_hc1"]
    baseline_out = intensity_out[intensity_out["spec"].isin(baseline_specs)].copy()
    baseline_out.to_csv(args.outdir / "baseline_key_results.csv", index=False)

    write_results_brief(
        args.outdir / "results_brief.md",
        intensity_key,
        margin_key,
        comparison_table,
    )
    make_coefficient_plot(args.outdir / "college_intensity_coef_plot.png", intensity_key)
    make_margin_comparison_plot(args.outdir / "margin_comparison_plot.png", comparison_plot_df)
    write_talk_track(
        args.outdir / "presentation_talk_track.md",
        baseline_out,
        margin_out,
        data_summary,
    )
    write_presentation_html(
        args.outdir / "presentation_summary.html",
        intensity_out,
        baseline_out,
        margin_out,
        comparison_table,
        data_summary,
    )
    write_paper_results_html(
        args.outdir / "paper_results_tables.html",
        paper_baseline_table,
        paper_presence_size_table,
        paper_robustness_table,
        data_summary,
    )

    print(f"Saved presentation pack in: {args.outdir}")
    print(f"- {args.outdir / 'college_intensity_key_coefficients.csv'}")
    print(f"- {args.outdir / 'margin_decomposition_key_coefficients.csv'}")
    print(f"- {args.outdir / 'margin_comparison_table.csv'}")
    print(f"- {args.outdir / 'baseline_key_results.csv'}")
    print(f"- {args.outdir / 'results_brief.md'}")
    print(f"- {args.outdir / 'college_intensity_coef_plot.png'}")
    print(f"- {args.outdir / 'margin_comparison_plot.png'}")
    print(f"- {args.outdir / 'presentation_talk_track.md'}")
    print(f"- {args.outdir / 'presentation_summary.html'}")
    print(f"- {args.outdir / 'paper_results_tables.html'}")


if __name__ == "__main__":
    main()
