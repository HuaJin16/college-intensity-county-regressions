# County College Presence, College Scale, and County-Level Economic Outcomes: Cross-Sectional Evidence from 2024 U.S. County Data

## 1. Abstract

This paper studies whether U.S. counties with more college activity are associated with higher median gross rent and higher average weekly wage, and whether that relationship reflects simple college presence or the scale of local college activity. The analysis is cross-sectional, county-level (`county_fips`), and explicitly associational rather than causal. The final merged dataset contains 3,222 counties (50 states + DC + Puerto Rico) built from ACS 2020-2024 5-year county data, 2024 QCEW county wage/employment data, IPEDS 2024 institution-level enrollment/location data aggregated to county, and a county metro crosswalk. College intensity is defined as county college enrollment divided by county population and reported as percentage points (`college_intensity_pct = 100 * college_intensity`).

Baseline rent and wage models are estimated with OLS, state fixed effects, and HC1 robust standard errors. Baseline rent results show a positive and statistically strong association between college intensity and log median gross rent (beta = 0.0015, SE = 0.0003, p < 0.001), which implies approximately 0.15% higher rent for a 1 percentage-point increase in college intensity. Baseline wage results show a near-zero association with log average weekly wage (beta = 0.0001, SE = 0.0003, p = 0.685). An added extensive/intensive decomposition shows that the rent relationship is concentrated on the intensive margin: simple college presence is near zero in the pooled sample, while higher college intensity among college counties remains positively associated with rent. For wages, the pooled two-part specification remains close to zero on both margins, although the positive-college sample shows a modest positive intensive-margin estimate. Robustness checks show that the rent estimate is sensitive to added controls (`renter_share`, `ba_share`) but remains positive under state-clustered inference and winsorized intensity.

The contribution of this paper is a transparent, reproducible county workflow that keeps no-college counties in sample, documents merge and missingness decisions, and separates baseline from robustness specifications for classroom interpretability.

## 2. Introduction

Colleges and universities are often treated as local economic anchors, but their county-level relationships with housing costs and labor outcomes vary substantially across places. Some counties host large student populations relative to permanent residents, while others have no local postsecondary institutions. Understanding this variation is useful for urban economics because it connects education geography to local housing demand and local labor-market conditions.

The core research question is: **Do counties with higher college intensity tend to have higher median gross rent and higher average weekly wage, conditional on a small set of economically motivated controls, and is any relationship driven by college presence or by college scale?** The paper answers this using a single cross section (year alignment centered on 2024), one observation per county, and separate regressions for rent and wage outcomes.

Methodologically, the project prioritizes transparency over complexity. The county dataset is built by starting from the ACS county universe and left-merging QCEW, county-aggregated IPEDS, and metro status. Baseline models use log outcomes, state fixed effects, and robust standard errors. Robustness checks test clustered inference, additional controls, and winsorized treatment scaling.

Main findings are asymmetric across outcomes. In rent models, the main empirical pattern is an **intensive-margin** relationship: larger college footprints in counties that already have colleges are associated with higher rents, while simple college presence is not. In wage models, the estimated relationship is small and statistically weak in pooled specifications. The key contribution is not a causal claim; instead, it is a clearly documented and replicable associational framework with explicit quality-control reporting (`data/intermediate/merge_qc_2024.md`) and limitations reporting (`outputs/memos/limitations.md`).

## 3. Institutional Background

Several urban-economic channels motivate a county-level relationship between college intensity and rents. Higher enrollment concentration can increase demand for nearby housing through students, faculty, staff, and institution-linked service employment. In constrained local housing markets, this demand pressure may correspond to higher observed gross rents. Counties with high enrollment intensity may also have different rental tenure composition and local amenity bundles that co-move with rents.

For wages, plausible channels are more mixed. Counties with strong postsecondary presence may have greater human-capital density, stronger matching for skilled occupations, and sectoral specialization in education, health, professional services, or technology. These factors can be associated with higher earnings. At the same time, college-intensive counties can also include institutional structures (for example, public-sector anchors, student-heavy labor markets, or lower-paid service ecosystems) that dampen average wage effects. This motivates estimating wage associations separately from rent associations.

The county is an appropriate unit because major data sources (ACS, QCEW, IPEDS geography fields/crosswalks) can be harmonized by county FIPS and because county-level policy, labor markets, and housing markets remain salient for comparative analysis.

## 4. Data

### 4.1 Sources and year alignment

The analysis uses:

- **ACS 5-year county data (2020-2024, accessed via 2024 ACS API endpoint)** for population, rent, income, and housing/education shares.
- **BLS QCEW county annual data (2024)** for average weekly wage and total county employment.
- **IPEDS 2024 files (HD + EFIA)** aggregated from institution level to county enrollment totals.
- **QCEW county-MSA-CSA crosswalk** transformed into a metro/nonmetro county indicator.

Why ACS 5-year estimates are used instead of ACS 1-year 2024:

- The project targets near-universe county coverage with one row per county. ACS 5-year supports this county scope, while ACS 1-year excludes many small counties.
- ACS 5-year estimates are more stable for small-area variables (rent, income, housing shares, education shares) because they pool multiple years of survey responses.
- Using ACS 1-year would shift the sample toward larger counties and metros, reducing comparability across places and changing the interpretation of county-level associations.
- Tradeoff: ACS 5-year is a 2020-2024 average while QCEW/IPEDS are 2024 snapshots. We therefore treat alignment as nearest-year and interpret results as cross-sectional associations under mixed-year timing.

### 4.2 Unit of analysis and geography scope

- Unit: U.S. county (`county_fips`), one row per county.
- Scope: `us_50_dc_pr` (50 states + DC + Puerto Rico).
- ACS master counties retained: **3,222**.

### 4.3 Variable construction

Main regressor:

- `college_intensity = college_enrollment_total / population`
- `college_intensity_pct = 100 * college_intensity`
- `has_college = 1[college_enrollment_total > 0]`

Outcomes:

- `median_gross_rent` (ACS `B25064_001E`), modeled as `ln_median_gross_rent`.
- `avg_weekly_wage` (QCEW `annual_avg_wkly_wage`, with `avg_annual_pay/52` fallback if needed), modeled as `ln_avg_weekly_wage`.

Key controls:

- `ln_median_household_income` from ACS `B19013_001E`.
- `ln_population` from ACS `B01003_001E`.
- `metro` (MSA = 1; MicroSA or unassigned CBSA = 0).
- `C(state_fips)` fixed effects.

Robustness-only controls include `renter_share`, `vacancy_rate`, and `ba_share`.

### 4.4 Cleaning and merge design

FIPS cleaning follows a common rule across files: cast to string, trim, strip non-digits, zero-pad to 5 digits, keep valid county FIPS. Merge order is ACS master -> QCEW -> county-aggregated IPEDS -> metro crosswalk using left joins.

Coverage and filtering diagnostics:

- QCEW unique counties before ACS-universe filter: **3,275**; retained after filter: **3,221**.
- IPEDS unique counties before filter: **1,429**; retained after filter: **1,425**.
- Out-of-scope dropped prior to merge: QCEW **54** (including **51** pseudo-FIPS ending in `999`), IPEDS **4**.

### 4.5 IPEDS-specific decisions

IPEDS county aggregation metadata reports:

- Cleaned institution rows: **6,072**.
- Included in county aggregation: **5,858**.
- Excluded: **214** institutions (211 missing enrollment, 3 missing/unmappable county FIPS).
- Enrollment measure used: **FTE fallback** (`EFTEUG/FTEUG + EFTEGD/FTEGD + FTEDPP`) because a direct 12-month headcount field was not available in this release.

County aggregation output includes **1,429** counties with positive/nonmissing enrollment totals.

### 4.6 Final analytic sample and missingness

- Merged rows: **3,222** (unique county FIPS = 3,222).
- Missing in merged data: `median_gross_rent` = 7 counties; `median_household_income` = 1 county; `avg_weekly_wage` = 1 county.
- Counties with `college_enrollment_total = 0`: **1,797**.
- Named missing-outcome/control counties from merge QC: rent is missing in Alpine (CA), Sierra (CA), Borden (TX), Kenedy (TX), King (TX), Loving (TX), and Terrell (TX); median household income is missing in De Baca (NM); average weekly wage is missing in Kalawao (HI).

Model complete-case sample sizes:

- Rent baseline N = **3,214** (8 dropped from merged frame).
- Wage baseline N = **3,221** (1 dropped from merged frame).

### 4.7 Descriptive patterns

- `college_intensity_pct` is highly right-skewed: median = 0.00, 75th percentile = 3.26, 90th = 7.95, 99th = 31.58, max = 118.71 (Lynchburg city, VA).
- A value above 100% can occur because the numerator is institution-reported enrollment headcount (location-based) while the denominator is resident county population; high student-concentration counties can therefore exceed 100 in this ratio.
- Metro distribution in final data: 1,251 metro counties and 1,971 nonmetro counties.
- Positive-intensity counties: 1,425 (44.2% of counties), implying most counties have zero measured local college enrollment in this construction.

## 5. Methodology

The paper estimates two baseline OLS models with log outcomes and state fixed effects.

Reproducibility capsule (exact workflow and outputs):

1. Build harmonized county inputs as needed:
   - `python src/data/02_build_ipeds_county.py` -> `data/intermediate/ipeds_county_aggregate_2024.csv` and audit metadata.
   - `python src/data/02_build_metro_crosswalk.py` -> `data/raw/metro_crosswalk.csv`.
2. Build analytical county dataset:
   - `python src/data/02_build_county_dataset.py --year 2024` -> `data/processed/county_analysis_2024.csv` and `data/intermediate/merge_qc_2024.md`.
3. Estimate baseline and robustness regressions:
   - `python src/models/03_run_models.py --input data/processed/county_analysis_2024.csv --outdir outputs` -> `outputs/tables/*.csv` and `outputs/memos/limitations.md`.
4. Build presentation-ready outputs:
   - `python src/models/04_build_presentation_pack.py --tables-dir outputs/tables --outdir outputs/presentation` -> key coefficient tables, plot, and summary memo.

> **Methods explainer box (plain language)**
>
> - **Cross-sectional** means we study differences **across counties at one aligned period**, not changes over time.
> - **County-level** means each observation is one county (`county_fips`), so all variables are harmonized to county geography.
> - **OLS (ordinary least squares)** is the estimation method that chooses coefficients to minimize squared prediction errors.
> - Put together, this project runs **cross-sectional, county-level OLS regressions**.
> - We then use **HC1 robust standard errors** (and state-clustered SE in robustness) to quantify statistical uncertainty around coefficient estimates.
> - Interpretation is **associational**: estimates describe conditional correlations, not causal effects.

Baseline rent model:

`ln_median_gross_rent ~ college_intensity_pct + ln_median_household_income + ln_population + metro + C(state_fips)`

Baseline wage model:

`ln_avg_weekly_wage ~ college_intensity_pct + ln_population + metro + C(state_fips)`

To separate the presence of a college from the size of college activity, the updated workflow also estimates an extensive/intensive decomposition:

- Extensive-only: replace `college_intensity_pct` with `has_college`.
- Intensive-only: rerun the baseline model on the positive-college sample (`has_college = 1`).
- Combined two-part model: include `has_college` and a centered positive-county intensity term, `college_intensity_pct_positive_centered`, in the same pooled specification.

Centering the positive-county intensity term means the `has_college` coefficient compares no-college counties to counties with an average positive college presence rather than to a hypothetical county with a college and zero enrollment.

The intended wage baseline includes industry mix controls if feasible. In this run, those controls were not included because the county QCEW extract (`data/raw/qcew_county.csv`) contains only total industry (`industry_code = 10`), yielding 0% usable coverage for county industry-share controls.

Control-variable definitions used in baseline and robustness models:

- `ln_median_household_income`: natural log of ACS county median household income; proxies local purchasing power and broad demand conditions in the rent model.
- `ln_population`: natural log of county population; controls for county scale and agglomeration-related differences in both rent and wage outcomes.
- `metro`: binary county indicator from the CBSA crosswalk (1 = metropolitan statistical area county, 0 = micropolitan or non-CBSA county); captures urban-rural market structure differences.
- `C(state_fips)`: state fixed effects; absorb time-invariant state-level factors such as policy, regulation, tax structure, and persistent regional cost/wage differences.
- `renter_share` (robustness): renter-occupied housing units divided by occupied housing units; captures tenure composition relevant for rent determination.
- `vacancy_rate` (constructed robustness control): vacant housing units divided by total housing units; captures local housing slack/tightness. This variable is constructed in the dataset but not used in the current reported robustness table.
- `ba_share` (robustness): share of population with bachelor's degree or higher (ACS education tabulations); proxies county human-capital composition.
- `manuf_emp_share`, `leisure_emp_share`, `prof_emp_share` (intended wage controls): county employment shares by major industry group from QCEW; designed to account for sectoral composition of local labor demand, but unavailable in this run because the county QCEW file only includes total industry.

How to read `C(state_fips)` in output tables:

- `C(state_fips)` creates one indicator per state and omits one reference state (in this run, Alabama `01`), so each displayed state coefficient is interpreted relative to that omitted state after conditioning on other regressors.
- Example: a positive coefficient like `C(state_fips)[T.06]` in a log-outcome model means counties in state `06` have a higher average outcome level than otherwise comparable counties in Alabama, holding included controls fixed.
- These state fixed-effect coefficients are nuisance controls, not the main estimands. Their role is to absorb broad state-level differences so the `college_intensity_pct` coefficient is identified primarily from within-state county variation.

Inference and sample handling:

- Baseline inference: HC1 robust standard errors.
- Robustness inference: state-clustered standard errors (`state_fips`).
- Estimation samples: model-specific complete-case subsets.
- Log transforms applied only to strictly positive values.

Robustness specifications:

1. Rent model with state-clustered SE.
2. Wage model with state-clustered SE.
3. Rent model + `renter_share`.
4. Rent model + `ba_share`.
5. Rent and wage models with winsorized `college_intensity_pct` (1st/99th percentiles; cutoffs 0.00 and 31.58).

Interpretation rule: coefficients are conditional correlations in a cross section; they are not interpreted as causal effects.

## 6. Results

### 6.1 Baseline estimates

| Outcome model       | Coef on `college_intensity_pct` |     SE | p-value |            95% CI | Implied change per +1 pp intensity |    N |    R2 |
| ------------------- | ------------------------------: | -----: | ------: | ----------------: | ---------------------------------: | ---: | ----: |
| Rent baseline (HC1) |                          0.0015 | 0.0003 |  <0.001 |  [0.0009, 0.0021] |                        +0.15% rent | 3214 | 0.826 |
| Wage reduced baseline (HC1; no industry shares) |                          0.0001 | 0.0003 |   0.685 | [-0.0005, 0.0008] |                        +0.01% wage | 3221 | 0.536 |

For interpretation, outcomes are in logs while `college_intensity_pct` is in level percentage points, so the implied percent association for a +1 pp change is computed as `100 * (exp(beta) - 1)` (approximately `100 * beta` when beta is small).

Interpretation:

- **Rent:** Counties with higher college intensity are associated with higher rents in the baseline model, holding income, population, metro status, and state fixed effects constant.
- **Wage (reduced baseline):** The wage association is close to zero and statistically indistinguishable from zero; this is a reduced baseline because county industry-share controls were unavailable in the current QCEW county extract.

### 6.2 Extensive and intensive margin decomposition

The decomposition results clarify what is driving the baseline single-coefficient model.

- **Rent, extensive-only:** `has_college` = -0.0006 (SE = 0.0056, p = 0.920).
- **Rent, intensive-only positive-college sample:** `college_intensity_pct` = 0.0020 (SE = 0.0004, p < 0.001).
- **Rent, pooled two-part model:** `has_college` = -0.0026 (SE = 0.0056, p = 0.647); `college_intensity_pct_positive_centered` = 0.0019 (SE = 0.0004, p < 0.001).
- **Wage, extensive-only:** `has_college` = -0.0043 (SE = 0.0069, p = 0.530).
- **Wage, intensive-only positive-college sample:** `college_intensity_pct` = 0.0008 (SE = 0.0004, p = 0.044).
- **Wage, pooled two-part model:** `has_college` = -0.0047 (SE = 0.0069, p = 0.498); `college_intensity_pct_positive_centered` = 0.0003 (SE = 0.0004, p = 0.418).

Interpretation:

- For **rent**, the baseline association appears to come from the **intensive margin** rather than the extensive margin. Counties that simply cross from no college presence to an average positive college presence do not show a distinct rent difference after controls, but counties with larger college footprints among the positive-college group do have higher rents.
- For **wage**, the decomposition weakens the already-limited baseline story. The positive-college sample shows a modest intensive-margin association, but once the no-college counties are returned to the pooled two-part specification, neither margin remains statistically strong.

The rent-side two-part result is also robust to state-clustered inference and to winsorizing the positive-county intensity term: the conditional intensity coefficient rises to about 0.0025 (SE = 0.0004, p < 0.001), while the extensive-margin coefficient remains near zero.

### 6.3 Robustness results for the key regressor

- Rent, state-clustered SE: beta = 0.0015, SE = 0.0003, p < 0.001 (very similar to HC1 baseline).
- Rent + renter share: beta = -0.0001, SE = 0.0003, p = 0.644.
- Rent + BA share: beta = -0.0005, SE = 0.0003, p = 0.066.
- Rent, winsorized intensity: beta = 0.0020, SE = 0.0004, p < 0.001.
- Wage, state-clustered SE: beta = 0.0001, SE = 0.0003, p = 0.642.
- Wage, winsorized intensity: beta = 0.0002, SE = 0.0004, p = 0.644.

The rent coefficient remains positive under clustered inference and winsorization but attenuates and changes sign when adding `renter_share` or `ba_share`. This sensitivity indicates that baseline rent associations partly overlap with local housing tenure structure and educational composition. Wage associations remain near zero across all tested variants.

### 6.4 Control-pattern context

In baseline rent, `ln_median_household_income` (0.5883), `ln_population` (0.0738), and `metro` (0.0246, about +2.49%) are positive and statistically strong. In baseline wage, `ln_population` (0.0548) and `metro` (0.0506, about +5.19%) are also positive and significant. These control estimates align with expected scale and urbanicity gradients in county outcomes.

### 6.5 Practical reading of magnitudes

- A +10 percentage-point increase in college intensity corresponds to roughly +1.5% higher rent in the baseline rent specification (10 x 0.15%).
- The analogous wage implication is about +0.14% in baseline and not statistically precise.

## 7. Conclusions

This county-level cross-sectional analysis finds that college intensity is positively associated with median gross rent in baseline models but not robustly associated with average weekly wage. The new decomposition sharpens that conclusion: for rent, the main pattern is an intensive-margin relationship among counties that already have colleges, while the extensive-margin indicator is close to zero after controls. For wage, pooled extensive- and intensive-margin estimates remain weak, even though the positive-college sample alone shows a modest intensive-margin relationship.

The project adds value through reproducible construction and explicit diagnostics rather than causal identification. It preserves all ACS counties in scope, keeps no-college counties in sample, documents out-of-scope county handling, and reports model-specific sample drops.

The main limitations are important for interpretation: cross-sectional omitted-variable risk, potential reverse directionality, unavailable county industry controls in the current QCEW extract, FTE-based IPEDS enrollment fallback, and treatment sensitivity to extreme college-intensity observations. As a result, findings should be presented as conditional associations only.

For next iteration, the highest-return upgrade is replacing `data/raw/qcew_county.csv` with a county-by-industry extract from the annual singlefile so wage models can include explicit industry-mix controls consistent with the original PRD design.
