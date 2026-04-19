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
    "rent_extensive_hc1": "Rent presence only (HC1)",
    "rent_intensive_positive_hc1": "Rent intensity among college counties",
    "rent_two_part_hc1": "Rent two-part decomposition",
    "rent_two_part_cluster_state": "Rent two-part (state-clustered SE)",
    "rent_two_part_winsorized_intensity": "Rent two-part winsorized intensity",
    "wage_extensive_hc1": "Wage presence only (HC1)",
    "wage_intensive_positive_hc1": "Wage intensity among college counties",
    "wage_two_part_hc1": "Wage two-part decomposition",
    "wage_two_part_cluster_state": "Wage two-part (state-clustered SE)",
    "wage_two_part_winsorized_intensity": "Wage two-part winsorized intensity",
}

OUTCOME_LABELS = {
    "ln_median_gross_rent": "Log median gross rent",
    "ln_avg_weekly_wage": "Log average weekly wage",
}

TERM_LABELS = {
    "college_intensity_pct": "College intensity (1 pp)",
    "college_intensity_pct_w": "College intensity, winsorized (1 pp)",
    "has_college": "College present (0/1)",
    "college_intensity_pct_positive_centered": "Conditional intensity (1 pp from positive-county mean)",
    "college_intensity_pct_positive_winsorized_centered": "Conditional intensity, winsorized (1 pp from positive-county mean)",
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
        ("Baseline pooled intensity", "baseline_rent_hc1", "college_intensity_pct"),
        ("Presence only", "rent_extensive_hc1", "has_college"),
        ("Intensive only", "rent_intensive_positive_hc1", "college_intensity_pct"),
        ("Two-part presence", "rent_two_part_hc1", "has_college"),
        (
            "Two-part intensity",
            "rent_two_part_hc1",
            "college_intensity_pct_positive_centered",
        ),
    ],
    "ln_avg_weekly_wage": [
        ("Baseline pooled intensity", "baseline_wage_hc1", "college_intensity_pct"),
        ("Presence only", "wage_extensive_hc1", "has_college"),
        ("Intensive only", "wage_intensive_positive_hc1", "college_intensity_pct"),
        ("Two-part presence", "wage_two_part_hc1", "has_college"),
        (
            "Two-part intensity",
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
    ] = "Intensity among college counties (1 pp)"

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
    presence = cells.get("Presence only")
    intensive_only = cells.get("Intensive only")
    two_part_presence = cells.get("Two-part presence")
    two_part_intensity = cells.get("Two-part intensity")

    if outcome == "ln_median_gross_rent":
        if two_part_intensity is not None and float(two_part_intensity["p_value"]) < 0.05:
            if two_part_presence is not None and float(two_part_presence["p_value"]) >= 0.10:
                return "Scale matters more than simple presence."
        if intensive_only is not None and float(intensive_only["p_value"]) < 0.05:
            return "Rent rises mainly with larger college footprints."
        return "Rent evidence is mixed across the margins."

    if intensive_only is not None and float(intensive_only["p_value"]) < 0.05:
        if two_part_intensity is not None and float(two_part_intensity["p_value"]) >= 0.10:
            return "Any wage signal is limited to college counties only."
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
                "Baseline pooled intensity": format_effect_cell(row_map.get("Baseline pooled intensity")),
                "Presence only (0/1)": format_effect_cell(row_map.get("Presence only")),
                "Intensive only (+1 pp)": format_effect_cell(row_map.get("Intensive only")),
                "Two-part presence (0/1)": format_effect_cell(row_map.get("Two-part presence")),
                "Two-part intensity (+1 pp)": format_effect_cell(row_map.get("Two-part intensity")),
                "Presentation takeaway": comparison_takeaway(outcome, row_map),
            }
        )

    return pd.DataFrame(comparison_rows), pd.DataFrame(plot_rows)


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
            "- Rent decomposition: once presence and size are separated, the extensive-margin indicator is near zero "
            f"(beta={fmt_num(rent_presence['coef'])}, {fmt_p_text(float(rent_presence['p_value']))}), while the conditional intensity term stays positive "
            f"(beta={fmt_num(rent_conditional['coef'])}, {fmt_p_text(float(rent_conditional['p_value']))})."
        )
    if wage_presence is not None and wage_conditional is not None and wage_intensive_only is not None:
        lines.append(
            "- Wage decomposition: the pooled two-part model shows little evidence for either college presence or conditional intensity, "
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
                "## Margin Decomposition",
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
        "Baseline pooled intensity": "#0f766e",
        "Presence only": "#1d4ed8",
        "Intensive only": "#b45309",
        "Two-part presence": "#7c3aed",
        "Two-part intensity": "#dc2626",
    }
    markers = {
        "Baseline pooled intensity": "D",
        "Presence only": "s",
        "Intensive only": "o",
        "Two-part presence": "^",
        "Two-part intensity": "o",
    }

    outcome_order = ["ln_median_gross_rent", "ln_avg_weekly_wage"]
    label_order = [
        "Baseline pooled intensity",
        "Presence only",
        "Intensive only",
        "Two-part presence",
        "Two-part intensity",
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

    fig.suptitle("Baseline vs presence vs intensity decomposition", y=0.98)
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
        "- We study 3,222 counties and ask a simple question: do counties with more college activity tend to have higher rents and higher wages?",
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
            "- The rent result is mostly an intensive-margin story: simple college presence is close to zero, but larger college footprints inside college counties are associated with higher rents."
        )
        lines.append(
            "- In other words, crossing from no college to an average college county does not move rent much after controls; moving from a smaller to a larger college county does."
        )
    if wage_presence is not None and wage_intensity is not None:
        lines.append(
            "- The wage result is much weaker: in the pooled two-part specification, neither the presence term nor the conditional intensity term is precise."
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
            "<li><strong>Rent two-part:</strong> the college-presence indicator is near zero once college size is separated out, while the conditional intensity term remains positive and precise.</li>"
        )
    if wage_presence is not None and wage_conditional is not None:
        takeaway_lines.append(
            "<li><strong>Wage two-part:</strong> neither the presence indicator nor the pooled conditional-intensity term is precise in the full-sample decomposition.</li>"
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
        <h2>Margin Decomposition</h2>
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


if __name__ == "__main__":
    main()
