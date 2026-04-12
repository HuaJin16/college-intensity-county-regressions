#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DEFAULT_TABLES_DIR = Path("outputs/tables")
DEFAULT_OUTDIR = Path("outputs/presentation")

SPEC_ORDER = [
    "baseline_rent_hc1",
    "rent_cluster_state",
    "rent_plus_renter_share",
    "rent_plus_ba_share",
    "rent_winsorized_intensity",
    "baseline_wage_hc1",
    "wage_cluster_state",
    "wage_winsorized_intensity",
]

SPEC_LABELS = {
    "baseline_rent_hc1": "Rent baseline (HC1)",
    "rent_cluster_state": "Rent baseline (state-clustered SE)",
    "rent_plus_renter_share": "Rent + renter share",
    "rent_plus_ba_share": "Rent + BA share",
    "rent_winsorized_intensity": "Rent winsorized intensity",
    "baseline_wage_hc1": "Wage baseline (HC1)",
    "wage_cluster_state": "Wage baseline (state-clustered SE)",
    "wage_winsorized_intensity": "Wage winsorized intensity",
}

OUTCOME_LABELS = {
    "ln_median_gross_rent": "Log median gross rent",
    "ln_avg_weekly_wage": "Log average weekly wage",
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
    samples_path = tables_dir / "model_samples.csv"

    require_file(baseline_rent_path, "baseline rent table")
    require_file(baseline_wage_path, "baseline wage table")
    require_file(robustness_path, "robustness table")
    require_file(samples_path, "model sample table")

    baseline_rent = pd.read_csv(baseline_rent_path)
    baseline_wage = pd.read_csv(baseline_wage_path)
    robustness = pd.read_csv(robustness_path)
    samples = pd.read_csv(samples_path)

    coeffs = pd.concat([baseline_rent, baseline_wage, robustness], ignore_index=True)
    return coeffs, samples


def build_key_coefficients(coeffs: pd.DataFrame, samples: pd.DataFrame) -> pd.DataFrame:
    key_terms = {"college_intensity_pct", "college_intensity_pct_w"}
    key = coeffs[coeffs["term"].isin(key_terms)].copy()
    if key.empty:
        raise ValueError("No college-intensity coefficients found in regression tables.")

    key["intensity_measure"] = np.where(
        key["term"].eq("college_intensity_pct_w"),
        "winsorized (1st/99th pct)",
        "raw",
    )
    key["ci_low"] = key["coef"] - 1.96 * key["std_error"]
    key["ci_high"] = key["coef"] + 1.96 * key["std_error"]
    key["implied_pct_change_per_1pp"] = 100.0 * (np.exp(key["coef"]) - 1.0)
    key["stars"] = key["p_value"].apply(significance_stars)
    key["spec_label"] = key["spec"].map(SPEC_LABELS).fillna(key["spec"])
    key["outcome_label"] = key["outcome"].map(OUTCOME_LABELS).fillna(key["outcome"])

    sample_cols = [col for col in ["spec", "n_sample", "n_dropped", "se_type"] if col in samples.columns]
    if sample_cols:
        sample_info = samples[sample_cols].drop_duplicates(subset=["spec"])
        key = key.merge(sample_info, on="spec", how="left", suffixes=("", "_sample"))

    key["spec_order"] = key["spec"].apply(
        lambda spec: SPEC_ORDER.index(spec) if spec in SPEC_ORDER else 999
    )
    key = key.sort_values(["spec_order", "outcome"]).reset_index(drop=True)
    return key


def fmt_num(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}"


def fmt_p(value: float) -> str:
    if value < 0.001:
        return "<0.001"
    return f"{value:.3f}"


def write_results_brief(path: Path, key: pd.DataFrame) -> None:
    lines = [
        "# Presentation Results Brief",
        "",
        "Key coefficient shown below is the estimated association for a 1 percentage-point increase in county college intensity.",
        "",
        "| Specification | Outcome | Coef (SE) | 95% CI | p-value | N |",
        "|---|---|---:|---:|---:|---:|",
    ]

    for row in key.itertuples(index=False):
        coef_cell = f"{fmt_num(row.coef)}{row.stars} ({fmt_num(row.std_error)})"
        ci_cell = f"[{fmt_num(row.ci_low)}, {fmt_num(row.ci_high)}]"
        n_sample = int(row.n_sample) if pd.notna(row.n_sample) else ""
        lines.append(
            f"| {row.spec_label} | {row.outcome_label} | {coef_cell} | {ci_cell} | {fmt_p(row.p_value)} | {n_sample} |"
        )

    def row_for(spec: str) -> pd.Series | None:
        subset = key.loc[key["spec"] == spec]
        if subset.empty:
            return None
        return subset.iloc[0]

    rent_base = row_for("baseline_rent_hc1")
    wage_base = row_for("baseline_wage_hc1")

    lines.extend(["", "## Slide-ready takeaway"])
    if rent_base is not None:
        rent_pct = 100.0 * (np.exp(rent_base["coef"]) - 1.0)
        rent_p = fmt_p(float(rent_base["p_value"]))
        rent_p_text = f"p{rent_p}" if rent_p.startswith("<") else f"p={rent_p}"
        lines.append(
            "- Baseline rent model: college intensity is positively associated with rent "
            f"(beta={fmt_num(rent_base['coef'])}, {rent_p_text}), "
            f"about {fmt_num(rent_pct, 2)}% higher rent per +1 pp college intensity."
        )
    if wage_base is not None:
        wage_pct = 100.0 * (np.exp(wage_base["coef"]) - 1.0)
        wage_p = fmt_p(float(wage_base["p_value"]))
        wage_p_text = f"p{wage_p}" if wage_p.startswith("<") else f"p={wage_p}"
        lines.append(
            "- Baseline wage model: association with wage is near zero and statistically weak "
            f"(beta={fmt_num(wage_base['coef'])}, {wage_p_text}, "
            f"~{fmt_num(wage_pct, 2)}% per +1 pp)."
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
    display["Implied % change per +1pp"] = display["implied_pct_change_per_1pp"].map(
        lambda value: f"{value:.2f}%"
    )

    keep_cols = [
        "spec_label",
        "outcome_label",
        "intensity_measure",
        "Coefficient (SE)",
        "95% CI",
        "p-value",
        "Implied % change per +1pp",
        "N",
        "se_type",
    ]
    keep_cols = [col for col in keep_cols if col in display.columns]
    display = display[keep_cols].copy()
    display = display.rename(
        columns={
            "spec_label": "Specification",
            "outcome_label": "Outcome",
            "intensity_measure": "Intensity measure",
            "se_type": "SE type",
        }
    )
    return display


def write_presentation_html(path: Path, key: pd.DataFrame, baseline: pd.DataFrame) -> None:
    baseline_table = build_display_table(baseline)
    all_specs_table = build_display_table(key)

    baseline_html = baseline_table.to_html(index=False, escape=False, border=0, classes="results-table")
    all_specs_html = all_specs_table.to_html(index=False, escape=False, border=0, classes="results-table")

    def get_row(spec: str) -> pd.Series | None:
        subset = baseline.loc[baseline["spec"] == spec]
        if subset.empty:
            return None
        return subset.iloc[0]

    rent_row = get_row("baseline_rent_hc1")
    wage_row = get_row("baseline_wage_hc1")

    takeaway_lines = []
    if rent_row is not None:
        rent_pct = 100.0 * (np.exp(rent_row["coef"]) - 1.0)
        rent_p = fmt_p(float(rent_row["p_value"]))
        rent_p_text = f"p{rent_p}" if rent_p.startswith("<") else f"p={rent_p}"
        takeaway_lines.append(
            "<li><strong>Rent baseline:</strong> college intensity is positively associated with rent "
            f"(beta={fmt_num(rent_row['coef'])}, {rent_p_text}), "
            f"about {fmt_num(rent_pct, 2)}% higher rent per +1 pp college intensity.</li>"
        )
    if wage_row is not None:
        wage_pct = 100.0 * (np.exp(wage_row["coef"]) - 1.0)
        wage_p = fmt_p(float(wage_row["p_value"]))
        wage_p_text = f"p{wage_p}" if wage_p.startswith("<") else f"p={wage_p}"
        takeaway_lines.append(
            "<li><strong>Wage baseline:</strong> association with wage is near zero and statistically weak "
            f"(beta={fmt_num(wage_row['coef'])}, {wage_p_text}, ~{fmt_num(wage_pct, 2)}% per +1 pp).</li>"
        )
    takeaway_lines.append(
        "<li><strong>Interpretation:</strong> estimates are associational (cross-sectional), not causal.</li>"
    )

    generated_on = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")

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
    }}
  </style>
</head>
<body>
  <main class=\"wrap\">
    <section class=\"hero\">
      <h1>County College Intensity - Presentation Summary</h1>
      <p>Cross-sectional county regressions for rent and wage outcomes (50 states + DC + Puerto Rico).</p>
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

      <article class=\"card\">
        <h2>Baseline Results (Slide Table)</h2>
        {baseline_html}
      </article>

      <article class=\"card\">
        <h2>All Key Coefficients (Baseline + Robustness)</h2>
        {all_specs_html}
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
    args = parser.parse_args()

    coeffs, samples = load_regression_tables(args.tables_dir)
    key = build_key_coefficients(coeffs, samples)

    args.outdir.mkdir(parents=True, exist_ok=True)

    key_cols = [
        "spec",
        "spec_label",
        "outcome",
        "outcome_label",
        "intensity_measure",
        "coef",
        "std_error",
        "ci_low",
        "ci_high",
        "p_value",
        "stars",
        "nobs",
        "n_sample",
        "r2",
        "se_type",
        "implied_pct_change_per_1pp",
    ]
    key_cols = [col for col in key_cols if col in key.columns]
    key_out = key[key_cols].copy()
    key_out.to_csv(args.outdir / "college_intensity_key_coefficients.csv", index=False)

    baseline_specs = ["baseline_rent_hc1", "baseline_wage_hc1"]
    baseline_out = key_out[key_out["spec"].isin(baseline_specs)].copy()
    baseline_out.to_csv(args.outdir / "baseline_key_results.csv", index=False)

    write_results_brief(args.outdir / "results_brief.md", key)
    make_coefficient_plot(args.outdir / "college_intensity_coef_plot.png", key)
    write_presentation_html(args.outdir / "presentation_summary.html", key_out, baseline_out)

    print(f"Saved presentation pack in: {args.outdir}")
    print(f"- {args.outdir / 'college_intensity_key_coefficients.csv'}")
    print(f"- {args.outdir / 'baseline_key_results.csv'}")
    print(f"- {args.outdir / 'results_brief.md'}")
    print(f"- {args.outdir / 'college_intensity_coef_plot.png'}")
    print(f"- {args.outdir / 'presentation_summary.html'}")


if __name__ == "__main__":
    main()
