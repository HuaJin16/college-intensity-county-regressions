# County College Presence, College Scale, and County-Level Economic Outcomes: Cross-Sectional Evidence from 2024 U.S. County Data

## 1. Abstract

This paper studies whether U.S. counties with more college activity are associated with higher median gross rent and higher average weekly wage, and whether that relationship reflects simple college presence or the scale of local college activity. The analysis is cross-sectional, county-level (`county_fips`), and explicitly associational rather than causal. The final merged dataset contains 3,144 county-level observations from the 50 states and DC, built from ACS 2020-2024 5-year county data, 2024 QCEW county wage/employment data, IPEDS 2024 institution-level enrollment/location data aggregated to county, and a county metro crosswalk. College intensity is defined as county college enrollment divided by county population and reported as percentage points (`college_intensity_pct = 100 * college_intensity`).

Baseline rent and wage models are estimated with OLS, state fixed effects, and HC1 robust standard errors. Baseline rent results show a positive and statistically strong association between college intensity and log median gross rent (beta = 0.0016, SE = 0.0003, p < 0.001), which implies about 0.16% higher rent for a 1 percentage-point increase in college intensity. Baseline wage results show a near-zero association with log average weekly wage (beta = 0.0001, SE = 0.0003, p = 0.814). An added extensive/intensive decomposition shows that the rent relationship is concentrated on the intensive margin: simple college presence is near zero in the pooled sample, while higher college intensity among college counties remains positively associated with rent. For wages, the pooled two-part specification remains close to zero on both margins, and the only positive signal appears in the college-county-only intensive-margin specification. Robustness checks show that the rent estimate is sensitive to added controls (`renter_share`, `ba_share`) but remains positive under state-clustered inference and winsorized intensity.

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

This analysis combines four main data sources. First, I use ACS 5-year county data for 2020-2024, accessed through the 2024 ACS API, to measure population, median gross rent, median household income, and several housing and education characteristics. Second, I use 2024 BLS QCEW county data to measure average weekly wage and total county employment. Third, I use 2024 IPEDS files (HD and EFIA), which are aggregated from the institution level up to the county level to create county college enrollment totals. Fourth, I use the QCEW county-MSA-CSA crosswalk to create a county-level metro/nonmetro indicator.

I use ACS 5-year data instead of ACS 1-year data because this project is designed to cover as much of the county universe as possible, with one observation per county-level unit. The ACS 5-year files support that goal, while ACS 1-year data leave out many smaller counties. The 5-year estimates are also more stable for small-area variables like rent, income, housing shares, and education shares because they combine several years of survey responses. The tradeoff is that the ACS data reflect a 2020-2024 average, while the QCEW and IPEDS data are 2024 snapshots. Because of this, I treat the data as the closest available year match and interpret the results as cross-sectional associations rather than exact same-year comparisons.

### 4.2 Unit of analysis and geography scope

The unit of analysis is the county-level geographic unit identified by `county_fips`, and the final dataset includes one row per unit. The geographic scope is `us_50_dc`, which includes the 50 states and DC but excludes Puerto Rico. After applying this scope, the ACS master file contains 3,144 county-level observations, and that county list serves as the base for the merged dataset.

### 4.3 Variable construction

The main explanatory variable is `college_intensity`, defined as `college_enrollment_total / population`. For easier interpretation, I also report `college_intensity_pct`, which equals `100 * college_intensity`, so it can be read in percentage points. In addition, I create `has_college`, which equals 1 if `college_enrollment_total > 0` and 0 otherwise. This lets the analysis separate whether a county has any measured college presence at all from how large that presence is.

The two outcome variables are `median_gross_rent` and `avg_weekly_wage`. Median gross rent comes from ACS table `B25064_001E` and is modeled as `ln_median_gross_rent`. Average weekly wage comes from QCEW using `annual_avg_wkly_wage`, with a fallback of `avg_annual_pay / 52` when needed, and is modeled as `ln_avg_weekly_wage`. The main control variables are `ln_median_household_income` from ACS `B19013_001E`, `ln_population` from ACS `B01003_001E`, a `metro` indicator where metropolitan counties equal 1 and micropolitan or non-CBSA counties equal 0, and `C(state_fips)` state fixed effects. In some robustness checks, I also include `renter_share`, `vacancy_rate`, and `ba_share`.

### 4.4 Cleaning and merge design

To make the files compatible, I clean county FIPS codes the same way across all sources. I convert them to strings, trim spaces, remove non-digit characters, zero-pad them to five digits, and keep only valid county FIPS codes. The merge begins with the ACS county file as the master dataset, then adds QCEW county data, county-aggregated IPEDS data, and finally the metro crosswalk using left joins.

Before restricting to the ACS-based scope, the QCEW file contained 3,275 unique counties and the IPEDS county aggregate contained 1,429. After applying the `us_50_dc` scope, 3,143 QCEW counties and 1,398 IPEDS counties remained. This means 132 QCEW county codes were dropped as out of scope, including 51 pseudo-FIPS codes ending in `999`, and 31 IPEDS county codes were also dropped before the final merge.

### 4.5 IPEDS-specific decisions

The IPEDS county aggregation required a few extra decisions. After cleaning, the IPEDS institutional file contained 6,072 institution rows. Of these, 5,858 were included in the county aggregation, while 214 were excluded. Most exclusions came from missing enrollment values (211 institutions), and 3 more were excluded because their county FIPS were missing or could not be mapped. Because this release did not provide a direct 12-month enrollment headcount in a usable form, I used an FTE fallback measure based on undergraduate, graduate, and professional FTE counts. Before geography filtering, the county-level IPEDS aggregate includes 1,429 counties with positive or nonmissing enrollment totals.

### 4.6 Final analytic sample and missingness

The final merged dataset contains 3,144 rows, with one unique row for each county-level unit in scope. Missing data are limited but still important. Median gross rent is missing for 7 counties, median household income is missing for 1 county, and average weekly wage is missing for 1 county. There are 1,746 counties with `college_enrollment_total = 0`, meaning more than half of the counties in the sample have no measured college enrollment in this construction.

The missing counties are identified in the merge quality-control report. Rent is missing for Alpine and Sierra in California, and Borden, Kenedy, King, Loving, and Terrell in Texas. Median household income is missing for De Baca, New Mexico. Average weekly wage is missing for Kalawao, Hawaii. After applying complete-case rules for each model, the baseline rent regression uses 3,136 counties, meaning 8 are dropped from the merged dataset, while the baseline wage regression uses 3,143 counties, meaning only 1 county is dropped.

### 4.7 Descriptive patterns

The distribution of `college_intensity_pct` is highly right-skewed. The median is 0.00, the 75th percentile is 3.28, the 90th percentile is 7.95, the 99th percentile is 31.65, and the maximum is 118.71 in Lynchburg city, Virginia. A value above 100% is possible because the numerator is institution-reported enrollment tied to the county where the school is located, while the denominator is the county's resident population. In counties with very large student populations relative to permanent residents, this ratio can therefore exceed 100%.

The final sample includes 1,185 metro counties and 1,959 nonmetro counties. There are 1,398 counties with positive college intensity, which is about 44.5% of the sample. This means most counties in the dataset have zero measured local college enrollment, which is one reason it is useful to separate the extensive margin of college presence from the intensive margin of college size.

## 5. Methodology

The paper estimates two baseline OLS models with log outcomes and state fixed effects.

Reproducibility capsule (exact workflow and outputs):

1. Build harmonized county inputs as needed:
   - `python src/data/02_build_ipeds_county.py` -> `data/intermediate/ipeds_county_aggregate_2024.csv` and audit metadata.
   - `python src/data/02_build_metro_crosswalk.py --county-universe data/raw/acs_county_2024.csv` -> `data/raw/metro_crosswalk.csv`.
2. Build analytical county dataset:
   - `python src/data/02_build_county_dataset.py --year 2024 --geography-scope us_50_dc` -> `data/processed/county_analysis_2024.csv` and `data/intermediate/merge_qc_2024.md`.
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
| Rent baseline (HC1) |                          0.0016 | 0.0003 |  <0.001 |  [0.0009, 0.0022] |                        +0.16% rent | 3136 | 0.813 |
| Wage reduced baseline (HC1; no industry shares) |                          0.0001 | 0.0003 |   0.814 | [-0.0006, 0.0008] |                        +0.01% wage | 3143 | 0.437 |

For interpretation, outcomes are in logs while `college_intensity_pct` is in level percentage points, so the implied percent association for a +1 pp change is computed as `100 * (exp(beta) - 1)` (approximately `100 * beta` when beta is small).

Interpretation:

- **Rent:** Counties with higher college intensity are associated with higher rents in the baseline model, holding income, population, metro status, and state fixed effects constant.
- **Wage (reduced baseline):** The wage association is close to zero and statistically indistinguishable from zero; this is a reduced baseline because county industry-share controls were unavailable in the current QCEW county extract.

### 6.2 Extensive and intensive margin decomposition

The decomposition results clarify what is driving the baseline single-coefficient model.

- **Rent, extensive-only:** `has_college` = 0.0002 (SE = 0.0057, p = 0.971).
- **Rent, intensive-only positive-college sample:** `college_intensity_pct` = 0.0020 (SE = 0.0004, p < 0.001).
- **Rent, pooled two-part model:** `has_college` = -0.0020 (SE = 0.0057, p = 0.731); `college_intensity_pct_positive_centered` = 0.0019 (SE = 0.0004, p < 0.001).
- **Wage, extensive-only:** `has_college` = -0.0060 (SE = 0.0070, p = 0.392).
- **Wage, intensive-only positive-college sample:** `college_intensity_pct` = 0.0007 (SE = 0.0004, p = 0.050).
- **Wage, pooled two-part model:** `has_college` = -0.0063 (SE = 0.0070, p = 0.367); `college_intensity_pct_positive_centered` = 0.0003 (SE = 0.0004, p = 0.454).

Interpretation:

- For **rent**, the baseline association appears to come from the **intensive margin** rather than the extensive margin. Counties that simply cross from no college presence to an average positive college presence do not show a distinct rent difference after controls, but counties with larger college footprints among the positive-college group do have higher rents.
- For **wage**, the decomposition weakens the already-limited baseline story. The positive-college sample shows a modest intensive-margin association, but once the no-college counties are returned to the pooled two-part specification, neither margin remains statistically strong.

The rent-side two-part result is also robust to state-clustered inference and to winsorizing the positive-county intensity term: the conditional intensity coefficient rises to about 0.0025 (SE = 0.0004, p < 0.001), while the extensive-margin coefficient remains near zero.

### 6.3 Robustness results for the key regressor

- Rent, state-clustered SE: beta = 0.0016, SE = 0.0003, p < 0.001 (very similar to HC1 baseline).
- Rent + renter share: beta = -0.0001, SE = 0.0003, p = 0.717.
- Rent + BA share: beta = -0.0005, SE = 0.0003, p = 0.095.
- Rent, winsorized intensity: beta = 0.0021, SE = 0.0004, p < 0.001.
- Wage, state-clustered SE: beta = 0.0001, SE = 0.0003, p = 0.784.
- Wage, winsorized intensity: beta = 0.0001, SE = 0.0004, p = 0.799.

The rent coefficient remains positive under clustered inference and winsorization but attenuates and changes sign when adding `renter_share` or `ba_share`. This sensitivity indicates that baseline rent associations partly overlap with local housing tenure structure and educational composition. Wage associations remain near zero across all tested variants.

### 6.4 Control-pattern context

In baseline rent, `ln_median_household_income` (0.5914), `ln_population` (0.0741), and `metro` (0.0236, about +2.38%) are positive and statistically strong. In baseline wage, `ln_population` (0.0548) and `metro` (0.0501, about +5.13%) are also positive and significant. These control estimates align with expected scale and urbanicity gradients in county outcomes.

### 6.5 Practical reading of magnitudes

- A +10 percentage-point increase in college intensity corresponds to roughly +1.6% higher rent in the baseline rent specification.
- The analogous wage implication is about +0.08% in baseline and is not statistically precise.

## 7. Conclusions

This county-level cross-sectional analysis finds that college intensity is positively associated with median gross rent in baseline models but not robustly associated with average weekly wage. The new decomposition sharpens that conclusion: for rent, the main pattern is an intensive-margin relationship among counties that already have colleges, while the extensive-margin indicator is close to zero after controls. For wage, pooled extensive- and intensive-margin estimates remain weak, even though the positive-college sample alone shows a modest intensive-margin relationship.

The project adds value through reproducible construction and explicit diagnostics rather than causal identification. It preserves all ACS counties in scope, keeps no-college counties in sample, documents out-of-scope county handling, and reports model-specific sample drops.

The main limitations are important for interpretation: cross-sectional omitted-variable risk, potential reverse directionality, unavailable county industry controls in the current QCEW extract, FTE-based IPEDS enrollment fallback, and treatment sensitivity to extreme college-intensity observations. As a result, findings should be presented as conditional associations only.

For next iteration, the highest-return upgrade is replacing `data/raw/qcew_county.csv` with a county-by-industry extract from the annual singlefile so wage models can include explicit industry-mix controls consistent with the original PRD design.
