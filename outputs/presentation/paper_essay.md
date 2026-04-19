# County College Presence, College Scale, and County-Level Economic Outcomes: Cross-Sectional Evidence from 2024 U.S. County-Level Data

## 1. Abstract

This paper studies whether U.S. county-level units with more college activity are associated with higher median gross rent and higher average weekly wage, and whether that relationship reflects simple college presence or the scale of local college activity. The analysis is cross-sectional, county-level (`county_fips`), and explicitly associational rather than causal. The final merged dataset contains 3,144 county-level observations from the 50 states and DC, built from ACS 2020-2024 5-year county data, 2024 QCEW county wage/employment data, IPEDS 2024 institution-level enrollment/location data aggregated to county, and a county metro crosswalk. College intensity is defined as county college enrollment divided by county population and reported as percentage points (`college_intensity_pct = 100 * college_intensity`), and `has_college` is an indicator for counties with positive aggregated college enrollment.

The empirical strategy uses pooled comparison models as reference points and then estimates three extensive-margin and intensive-margin models that separately study (i) whether counties with any college presence differ from counties with none and (ii) whether counties with larger college footprints differ from counties with smaller ones. The pooled rent comparison shows a positive and statistically strong association between college intensity and log median gross rent (beta = 0.0016, SE = 0.0003, p < 0.001), which implies about 0.16% higher rent for a 1 percentage-point increase in college intensity. The pooled wage comparison shows a near-zero association with log average weekly wage (beta = 0.0001, SE = 0.0003, p = 0.814). The extensive-margin and intensive-margin models show that the rent relationship is concentrated on the intensive margin: `has_college` is near zero in both the extensive-only and joint models, while higher college intensity among college counties remains positively associated with rent. For wages, counties with and without college presence do not differ systematically after controls, and the only positive signal appears in the intensive-only model estimated on college counties. Robustness checks show that the rent estimate is sensitive to added controls (`renter_share`, `ba_share`) but remains positive under clustered inference and when an outlier-adjusted college-intensity measure is used.

The contribution of this paper is a transparent, reproducible county workflow that keeps no-college counties in sample, documents merge and missingness decisions, and separates pooled comparison models, extensive-margin and intensive-margin models, and robustness checks for classroom interpretability.

## 2. Introduction

Colleges and universities are often treated as local economic anchors, but their county-level relationships with housing costs and labor outcomes vary substantially across places. Some counties host large student populations relative to permanent residents, while others have no local postsecondary institutions. Understanding this variation is useful for urban economics because it connects education geography to local housing demand and local labor-market conditions.

The core research question is: **Do counties with higher college intensity tend to have higher median gross rent and higher average weekly wage, conditional on a small set of economically motivated controls, and is any relationship driven by college presence or by college scale?** More specifically, the paper asks two linked questions: first, do counties with any measured college presence differ from counties with none; second, among counties with colleges, do larger college footprints correspond to different outcomes than smaller ones? The paper answers these questions using a single cross section (year alignment centered on 2024), one observation per county-level unit, and separate regressions for rent and wage outcomes.

Methodologically, the project prioritizes transparency over complexity. The county dataset is built by starting from the ACS county universe and left-merging QCEW, county-aggregated IPEDS, and metro status. The empirical design reports pooled comparison models for reference and then separates college presence into extensive-margin and intensive-margin components using three additional models. This makes it possible to distinguish counties with no college presence from counties with some college presence, and also to distinguish counties with smaller college footprints from counties with larger ones. All main specifications use log outcomes, state fixed effects, and robust standard errors.

Main findings are asymmetric across outcomes. In rent models, the main empirical pattern is an **intensive-margin** relationship: larger college footprints in counties that already have colleges are associated with higher rents, while simple college presence is not. In wage models, the estimated relationship is small and statistically weak in pooled specifications. The key contribution is not a causal claim; instead, it is a clearly documented and replicable associational framework with explicit quality-control reporting (`data/intermediate/merge_qc_2024.md`) and limitations reporting (`outputs/memos/limitations.md`).

## 3. Institutional Background

Several urban-economic channels motivate a county-level relationship between college intensity and rents. Higher enrollment concentration can increase demand for nearby housing through students, faculty, staff, and institution-linked service employment. In constrained local housing markets, this demand pressure may correspond to higher observed gross rents. Counties with high enrollment intensity may also have different rental tenure composition and local amenity bundles that co-move with rents.

For wages, plausible channels are more mixed. Counties with strong postsecondary presence may have greater human-capital density, stronger matching for skilled occupations, and sectoral specialization in education, health, professional services, or technology. These factors can be associated with higher earnings. At the same time, college-intensive counties can also include institutional structures (for example, public-sector anchors, student-heavy labor markets, or lower-paid service ecosystems) that dampen average wage effects. This motivates estimating wage associations separately from rent associations.

The county-level geographic unit is appropriate because major data sources (ACS, QCEW, IPEDS geography fields/crosswalks) can be harmonized by county FIPS and because county-level policy, labor markets, and housing markets remain salient for comparative analysis.

## 4. Data

### 4.1 Sources and year alignment

This analysis combines four main data sources. First, I use ACS 5-year county data for 2020-2024, accessed through the 2024 ACS API, to measure population, median gross rent, median household income, renter share, vacancy rate, and bachelor's degree share. Second, I use 2024 BLS QCEW county data to measure average weekly wage; total county employment is merged into the dataset but is not a reported regression outcome. Third, I use 2024 IPEDS files (HD and EFIA), which are aggregated from the institution level to the county level to create county college enrollment totals and the `has_college` indicator used in the extensive-margin and intensive-margin models. Fourth, I use the QCEW county-MSA-CSA crosswalk to create a county-level metro/nonmetro indicator.

I use ACS 5-year data instead of ACS 1-year data because this project is designed to cover as much of the county universe as possible, with one observation per county-level unit. The ACS 5-year files support that goal, while ACS 1-year data leave out many smaller counties. The 5-year estimates are also more stable for small-area variables like rent, income, housing shares, and education shares because they combine several years of survey responses. The tradeoff is that the ACS data reflect a 2020-2024 average, while the QCEW and IPEDS data are 2024 snapshots. Because of this, I treat the data as the closest available year match and interpret the results as cross-sectional associations rather than exact same-year comparisons.

### 4.2 Unit of analysis and geography scope

The unit of analysis is the county-level geographic unit identified by `county_fips`, and the final dataset includes one row per unit. The geographic scope is `us_50_dc`, which includes the 50 states and DC but excludes Puerto Rico. After applying this scope, the ACS master file contains 3,144 county-level observations, and that county list serves as the base for the merged dataset.

### 4.3 Variable construction

The main explanatory variable is `college_intensity`, defined as `college_enrollment_total / population`. For easier interpretation, I also report `college_intensity_pct`, which equals `100 * college_intensity`, so it can be read in percentage points. In addition, I create `has_college`, which equals 1 if `college_enrollment_total > 0` and 0 otherwise. This lets the analysis distinguish counties with no measured college presence from counties with some college presence, and then distinguish smaller college footprints from larger ones among counties that already have colleges, which correspond to the extensive and intensive margins.

The two outcome variables are `median_gross_rent` and `avg_weekly_wage`. Median gross rent comes from ACS table `B25064_001E` and is modeled as `ln_median_gross_rent`. Average weekly wage comes from QCEW using `annual_avg_wkly_wage`, with a fallback of `avg_annual_pay / 52` when needed, and is modeled as `ln_avg_weekly_wage`. The main control variables are `ln_median_household_income` from ACS `B19013_001E`, `ln_population` from ACS `B01003_001E`, a `metro` indicator where metropolitan counties equal 1 and micropolitan or non-CBSA counties equal 0, and `C(state_fips)` state fixed effects. In robustness work, I also construct renter share, vacancy rate, and `ba_share`, although the current reported robustness tables use renter share and `ba_share` rather than vacancy rate.

### 4.4 Cleaning and merge design

To make the files compatible, I clean county FIPS codes the same way across all sources. I convert them to strings, trim spaces, remove non-digit characters, zero-pad them to five digits, and keep only valid county FIPS codes. The merge begins with the ACS county file as the master dataset, then adds QCEW county data, county-aggregated IPEDS data, and finally the metro crosswalk using left joins.

Before restricting to the ACS-based scope, the QCEW file contained 3,275 unique counties and the IPEDS county aggregate contained 1,429. After applying the `us_50_dc` scope, 3,143 QCEW counties and 1,398 IPEDS counties remained. This means 132 QCEW county codes were dropped as out of scope, including 51 pseudo-FIPS codes ending in `999`, and 31 IPEDS county codes were also dropped before the final merge.

### 4.5 IPEDS-specific decisions

The IPEDS county aggregation required a few extra decisions. After cleaning, the IPEDS institutional file contained 6,072 institution rows. Of these, 5,858 were included in the county aggregation, while 214 were excluded. Most exclusions came from missing enrollment values (211 institutions), and 3 more were excluded because their county FIPS were missing or could not be mapped. Because this release did not provide a direct 12-month enrollment headcount in a usable form, I used an FTE fallback measure based on undergraduate, graduate, and professional FTE counts. Before geography filtering, the county-level IPEDS aggregate includes 1,429 counties with positive or nonmissing enrollment totals.

### 4.6 Final analytic sample and missingness

The final merged dataset contains 3,144 rows, with one unique row for each county-level unit in scope. Missing data are limited but still important. Median gross rent is missing for 7 counties, median household income is missing for 1 county, and average weekly wage is missing for 1 county. There are 1,746 counties with `college_enrollment_total = 0`, meaning more than half of the counties in the sample have no measured college enrollment in this construction.

The missing counties are identified in the merge quality-control report. Rent is missing for Alpine and Sierra in California, and Borden, Kenedy, King, Loving, and Terrell in Texas. Median household income is missing for De Baca, New Mexico. Average weekly wage is missing for Kalawao, Hawaii. After applying complete-case rules for each model, the pooled rent comparison regression uses 3,136 counties, meaning 8 are dropped from the merged dataset, while the pooled wage comparison regression uses 3,143 counties, meaning only 1 county is dropped.

### 4.7 Descriptive patterns

The distribution of `college_intensity_pct` is highly right-skewed. The median is 0.00, the 75th percentile is 3.28, the 90th percentile is 7.95, the 99th percentile is 31.65, and the maximum is 118.71 in Lynchburg city, Virginia. A value above 100% is possible because the numerator is institution-reported enrollment tied to the county where the school is located, while the denominator is the county's resident population. In counties with very large student populations relative to permanent residents, this ratio can therefore exceed 100%.

The final sample includes 1,185 metro counties and 1,959 nonmetro counties. There are 1,398 counties with positive college intensity, which is about 44.5% of the sample. This means most counties in the dataset have zero measured local college enrollment, which is one reason it is useful to separate the extensive margin of college presence from the intensive margin of college size.

## 5. Methodology

The main empirical design uses three models to separate the extensive margin from the intensive margin. Rather than relying only on a single pooled college-intensity coefficient, I estimate separate models for whether counties with any measured college presence differ from counties with none, whether larger college footprints matter among counties that already have colleges, and whether those two channels remain distinct when both are included in the same regression. For comparison, I also report pooled one-coefficient regressions of outcomes on county college intensity for the full sample. All specifications are estimated by OLS with log outcomes, county controls, state fixed effects, and HC1 robust standard errors.

Reproducibility capsule (exact workflow and outputs):

1. Build harmonized county inputs as needed:
   - `python src/data/02_build_ipeds_county.py` -> `data/intermediate/ipeds_county_aggregate_2024.csv` and audit metadata.
   - `python src/data/02_build_metro_crosswalk.py --county-universe data/raw/acs_county_2024.csv` -> `data/raw/metro_crosswalk.csv`.
2. Build analytical county dataset:
   - `python src/data/02_build_county_dataset.py --year 2024 --geography-scope us_50_dc` -> `data/processed/county_analysis_2024.csv` and `data/intermediate/merge_qc_2024.md`.
3. Estimate comparison, extensive-margin, intensive-margin, and robustness regressions:
    - `python src/models/03_run_models.py --input data/processed/county_analysis_2024.csv --outdir outputs` -> `outputs/tables/*.csv` and `outputs/memos/limitations.md`.
4. Build presentation-ready outputs:
   - `python src/models/04_build_presentation_pack.py --tables-dir outputs/tables --outdir outputs/presentation` -> key coefficient tables, plot, and summary memo.

> **Methods explainer box (plain language)**
>
> - **Cross-sectional** means we study differences **across counties at one aligned period**, not changes over time.
> - **County-level** means each observation is one county-level geographic unit identified by `county_fips`, so all variables are harmonized to county geography.
> - **OLS (ordinary least squares)** is the estimation method that chooses coefficients to minimize squared prediction errors.
> - Put together, this project runs **cross-sectional, county-level OLS regressions**.
> - We then use **HC1 robust standard errors** (and state-clustered SE in robustness) to quantify statistical uncertainty around coefficient estimates.
> - Interpretation is **associational**: estimates describe conditional correlations, not causal effects.

Outcome-specific controls used throughout the regressions:

- **Rent models:** `ln_median_household_income`, `ln_population`, `metro`, and `C(state_fips)`
- **Wage models:** `ln_population`, `metro`, and `C(state_fips)`; industry-mix controls are intended when available, but they are not available in the current county QCEW extract

Main extensive-margin and intensive-margin models:

1. **College-presence-only model:**

   `y_i ~ has_college_i + controls_i + C(state_fips)`

   The coefficient on `has_college` compares counties with no measured college enrollment to counties with some measured college enrollment.

2. **College-size-only model on the positive-college sample:**

   `y_i ~ college_intensity_pct_i + controls_i + C(state_fips)`, estimated only for `has_college_i = 1`

   This model uses the same intensity regressor name as the pooled comparison model, but it is not the same specification because all zero-college counties are excluded. The coefficient therefore captures whether, among counties that already have colleges, larger college presence is associated with different outcomes than smaller college presence; this is the intensive margin.

3. **Joint extensive/intensive model:**

   `y_i ~ has_college_i + college_intensity_pct_positive_centered_i + controls_i + C(state_fips)`

   In this model, the coefficient on `has_college` captures the no-college-versus-some-college difference, while the coefficient on the centered intensity term captures the small-versus-large college difference among counties with colleges.

The centered positive-county intensity term is used so that the `has_college` coefficient in the joint model compares no-college counties to counties with an average positive college presence rather than to a hypothetical county with a college and zero enrollment. This makes the joint specification easier to interpret because the extensive-margin coefficient and the intensive-margin coefficient refer to distinct channels.

For comparison, I also report pooled one-coefficient regressions for the full county sample:

Pooled comparison rent model:

`ln_median_gross_rent ~ college_intensity_pct + ln_median_household_income + ln_population + metro + C(state_fips)`

Pooled comparison wage model:

`ln_avg_weekly_wage ~ college_intensity_pct + ln_population + metro + C(state_fips)`

These pooled comparison models are useful summaries, but each coefficient mixes two sources of variation: the jump from no college presence to some college presence, and the difference between smaller and larger college footprints among counties that already have colleges. The extensive-margin and intensive-margin models are therefore the main strategy for interpretation, while the pooled comparison models are reported only as compact reference points.

The intended wage specification includes industry mix controls if feasible. In this run, those controls were not included because the county QCEW extract (`data/raw/qcew_county.csv`) contains only total industry (`industry_code = 10`), yielding 0% usable coverage for county industry-share controls.

Control-variable definitions used in the comparison, extensive-margin, intensive-margin, and robustness models:

- `ln_median_household_income`: natural log of ACS county median household income; proxies local purchasing power and broad demand conditions in the rent model.
- `ln_population`: natural log of county population; controls for county scale and agglomeration-related differences in both rent and wage outcomes.
- `metro`: binary county indicator from the CBSA crosswalk (1 = metropolitan statistical area county, 0 = micropolitan or non-CBSA county); captures urban-rural market structure differences.
- `C(state_fips)`: state fixed effects; absorb time-invariant state-level factors such as policy, regulation, tax structure, and persistent regional cost/wage differences.
- `renter_share` (robustness): renter-occupied housing units divided by occupied housing units; captures tenure composition relevant for rent determination.
- `vacancy_rate` (constructed robustness control): vacant housing units divided by total housing units; captures local housing slack/tightness. This variable is constructed in the dataset but not used in the current reported robustness table.
- `ba_share` (robustness): share of adults with bachelor's degree or higher (ACS education tabulations); proxies county human-capital composition.
- `manuf_emp_share`, `leisure_emp_share`, `prof_emp_share` (intended wage controls): county employment shares by major industry group from QCEW; designed to account for sectoral composition of local labor demand, but unavailable in this run because the county QCEW file only includes total industry.

How to read `C(state_fips)` in output tables:

- `C(state_fips)` creates one indicator per state and omits one reference state (in this run, Alabama `01`), so each displayed state coefficient is interpreted relative to that omitted state after conditioning on other regressors.
- Example: a positive coefficient like `C(state_fips)[T.06]` in a log-outcome model means counties in state `06` have a higher average outcome level than otherwise comparable counties in Alabama, holding included controls fixed.
- These state fixed-effect coefficients are nuisance controls, not the main estimands. Their role is to absorb broad state-level differences so identification comes from within-state county variation in college presence and college intensity.

Inference and sample handling:

- Main reported inference: HC1 robust standard errors.
- Robustness inference: state-clustered standard errors (`state_fips`).
- Estimation samples: model-specific complete-case subsets.
- Log transforms applied only to strictly positive values.

Robustness specifications:

1. Rent model with state-clustered SE.
2. Wage model with state-clustered SE.
3. Rent model + `renter_share`.
4. Rent model + `ba_share`.
5. Rent and wage pooled comparison models using an outlier-adjusted `college_intensity_pct` measure (1st/99th percentiles; cutoffs 0.00 and 31.65).
6. Rent and wage joint extensive/intensive models with state-clustered SE.
7. Rent and wage joint extensive/intensive models using outlier-adjusted intensive terms.

Interpretation rule: coefficients are conditional correlations in a cross section; they are not interpreted as causal effects.

## 6. Results

### 6.1 Pooled comparison estimates

| Outcome model       | Coef on `college_intensity_pct` |     SE | p-value |            95% CI | Implied change per +1 pp intensity |    N |    R2 |
| ------------------- | ------------------------------: | -----: | ------: | ----------------: | ---------------------------------: | ---: | ----: |
| Rent pooled comparison (HC1) |                          0.0016 | 0.0003 |  <0.001 |  [0.0009, 0.0022] |                        +0.16% rent | 3136 | 0.813 |
| Wage pooled comparison (HC1; no industry shares) |                          0.0001 | 0.0003 |   0.814 | [-0.0006, 0.0008] |                        +0.01% wage | 3143 | 0.437 |

For interpretation, outcomes are in logs while `college_intensity_pct` is in level percentage points, so the implied percent association for a +1 pp change is computed as `100 * (exp(beta) - 1)` (approximately `100 * beta` when beta is small).

Interpretation:

- **Rent:** Counties with higher college intensity are associated with higher rents in the pooled comparison model, holding income, population, metro status, and state fixed effects constant.
- **Wage (pooled comparison):** The wage association is close to zero and statistically indistinguishable from zero; this is a reduced comparison model because county industry-share controls were unavailable in the current QCEW county extract.

These pooled comparison estimates are informative, but by themselves they do not show whether the rent pattern reflects counties crossing from no college presence to some college presence, or whether it reflects differences between smaller and larger college counties. The next three subsections address those questions directly.

### 6.2 College presence results

The extensive-margin model replaces `college_intensity_pct` with `has_college`, so the key coefficient measures whether counties with any measured college enrollment differ from counties with none after conditioning on the same controls and state fixed effects.

- **Rent, extensive-only:** `has_college` = 0.0002 (SE = 0.0057, p = 0.971).
- **Wage, extensive-only:** `has_college` = -0.0060 (SE = 0.0070, p = 0.392).

Interpretation:

- For **rent**, counties with any measured college presence do not differ meaningfully from counties with none once controls are included.
- For **wage**, counties with and without measured college presence also do not differ systematically after controls.

### 6.3 College size results

The intensive-margin model drops the zero-college counties and estimates the pooled comparison specification only on the 1,398 counties with `has_college = 1`. This coefficient therefore captures whether, among counties that already have colleges, larger college presence is associated with different outcomes than smaller college presence.

- **Rent, intensive-only positive-college sample:** `college_intensity_pct` = 0.0020 (SE = 0.0004, p < 0.001).
- **Wage, intensive-only positive-college sample:** `college_intensity_pct` = 0.0007 (SE = 0.0004, p = 0.050).

Interpretation:

- For **rent**, the positive and precise intensive-margin estimate shows that larger college footprints are associated with higher rents among counties that already have colleges.
- For **wage**, the positive-college sample shows only a modest intensive-margin relationship, and that estimate is much weaker than the comparable rent result.

### 6.4 Joint extensive/intensive model

The joint extensive/intensive model includes both `has_college` and `college_intensity_pct_positive_centered` in the same regression. In this specification, the `has_college` coefficient captures the extensive-margin difference between no-college counties and counties with an average positive college presence, while the centered intensity term captures the intensive-margin relationship among counties that already have colleges.

- **Rent, joint model:** `has_college` = -0.0020 (SE = 0.0057, p = 0.731); `college_intensity_pct_positive_centered` = 0.0019 (SE = 0.0004, p < 0.001).
- **Wage, joint model:** `has_college` = -0.0063 (SE = 0.0070, p = 0.367); `college_intensity_pct_positive_centered` = 0.0003 (SE = 0.0004, p = 0.454).

Interpretation:

- For **rent**, the joint model shows that the relationship is driven by the intensive margin rather than the extensive margin. The `has_college` coefficient is near zero, while the centered intensive term remains positive and statistically strong.
- For **wage**, neither the no-college-versus-some-college distinction nor the small-versus-large-college distinction is statistically strong in the joint specification.

The rent-side joint result is also robust to state-clustered inference and to using an outlier-adjusted intensive term: the intensive-margin coefficient rises to about 0.0025 (SE = 0.0004, p < 0.001), while the extensive-margin coefficient remains near zero.

### 6.5 Robustness Checks

- Rent, state-clustered SE: beta = 0.0016, SE = 0.0003, p < 0.001 (very similar to the HC1 pooled comparison estimate).
- Rent + renter share: beta = -0.0001, SE = 0.0003, p = 0.717.
- Rent + BA share: beta = -0.0005, SE = 0.0003, p = 0.095.
- Rent, outlier-adjusted college intensity: beta = 0.0021, SE = 0.0004, p < 0.001.
- Wage, state-clustered SE: beta = 0.0001, SE = 0.0003, p = 0.784.
- Wage, outlier-adjusted college intensity: beta = 0.0001, SE = 0.0004, p = 0.799.

The pooled rent coefficient remains positive under clustered inference and when using an outlier-adjusted college-intensity measure, but it becomes smaller when renter share and educational attainment are added. This sensitivity suggests that part of the pooled rent relationship overlaps with differences in housing composition and local demographics. Even so, the joint extensive/intensive results remain stable: the extensive-margin effect stays near zero, while the intensive-margin effect remains positive. For wages, the estimated effects remain small and statistically weak across the robustness checks.

### 6.6 Control-pattern context

In the pooled rent comparison model, `ln_median_household_income` (0.5914), `ln_population` (0.0741), and `metro` (0.0236, about +2.38%) are positive and statistically strong. In the pooled wage comparison model, `ln_population` (0.0548) and `metro` (0.0501, about +5.13%) are also positive and significant. These control estimates align with expected scale and urbanicity gradients in county outcomes.

### 6.7 Practical reading of magnitudes

- A +10 percentage-point increase in college intensity corresponds to roughly +1.6% higher rent in the pooled rent comparison specification.
- The analogous wage implication is about +0.08% in the pooled wage comparison specification and is not statistically precise.

## 7. Conclusions

This county-level cross-sectional analysis finds that college intensity is positively associated with median gross rent in pooled comparison models but not robustly associated with average weekly wage. Once the paper explicitly separates the extensive margin from the intensive margin, the main rent pattern becomes clear: the extensive margin is not associated with materially different rents, but the intensive margin among college counties is. For wage, neither the extensive-margin distinction nor the intensive-margin distinction is robust in pooled specifications, even though the positive-college sample alone shows a modest intensive-margin relationship.

The project adds value through reproducible construction and explicit diagnostics rather than causal identification. It preserves all ACS counties in scope, keeps no-college counties in sample, documents out-of-scope county handling, and reports model-specific sample drops.

The main limitations are important for interpretation: cross-sectional omitted-variable risk, potential reverse directionality, unavailable county industry controls in the current QCEW extract, FTE-based IPEDS enrollment fallback, and treatment sensitivity to extreme college-intensity observations. As a result, findings should be presented as conditional associations only.

For next iteration, the highest-return upgrade is replacing `data/raw/qcew_county.csv` with a county-by-industry extract from the annual singlefile so wage models can include explicit industry-mix controls consistent with the original PRD design.
