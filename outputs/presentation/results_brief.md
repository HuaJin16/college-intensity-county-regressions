# Presentation Results Brief

Key coefficient shown below is the estimated association for a 1 percentage-point increase in county college intensity.

| Specification | Outcome | Coef (SE) | 95% CI | p-value | N |
|---|---|---:|---:|---:|---:|
| Rent baseline (HC1) | Log median gross rent | 0.0016*** (0.0003) | [0.0009, 0.0022] | <0.001 | 3136 |
| Rent baseline (state-clustered SE) | Log median gross rent | 0.0016*** (0.0003) | [0.0010, 0.0022] | <0.001 | 3136 |
| Rent + renter share | Log median gross rent | -0.0001 (0.0003) | [-0.0007, 0.0005] | 0.717 | 3136 |
| Rent + BA share | Log median gross rent | -0.0005* (0.0003) | [-0.0010, 0.0001] | 0.095 | 3136 |
| Rent winsorized intensity | Log median gross rent | 0.0021*** (0.0004) | [0.0014, 0.0028] | <0.001 | 3136 |
| Wage baseline (HC1) | Log average weekly wage | 0.0001 (0.0003) | [-0.0006, 0.0008] | 0.814 | 3143 |
| Wage baseline (state-clustered SE) | Log average weekly wage | 0.0001 (0.0003) | [-0.0005, 0.0007] | 0.784 | 3143 |
| Wage winsorized intensity | Log average weekly wage | 0.0001 (0.0004) | [-0.0008, 0.0010] | 0.799 | 3143 |

## Slide-ready takeaway
- Baseline rent model: college intensity is positively associated with rent (beta=0.0016, p<0.001), about 0.16% higher rent per +1 pp college intensity.
- Baseline wage model: association with wage is near zero and statistically weak (beta=0.0001, p=0.814, ~0.01% per +1 pp).
- Rent decomposition: once presence and size are separated, the extensive-margin indicator is near zero (beta=-0.0020, p=0.731), while the conditional intensity term stays positive (beta=0.0019, p<0.001).
- Wage decomposition: the pooled two-part model shows little evidence for either college presence or conditional intensity, but the college-only intensive spec is modestly positive (beta=0.0007, p=0.050).

## One-Slide Comparison

| Outcome | Baseline pooled intensity | Presence only (0/1) | Intensive only (+1 pp) | Two-part presence (0/1) | Two-part intensity (+1 pp) | Presentation takeaway |
|---|---|---|---|---|---|---|
| Log median gross rent | +0.16% per +1 pp*** | +0.02% | +0.20% per +1 pp*** | -0.20% | +0.19% per +1 pp*** | Scale matters more than simple presence. |
| Log average weekly wage | +0.01% per +1 pp | -0.59% | +0.07% per +1 pp* | -0.63% | +0.03% per +1 pp | No robust countywide wage premium shows up. |

## Margin Decomposition

| Specification | Outcome | Term | Coef (SE) | 95% CI | p-value | N | Sample |
|---|---|---|---:|---:|---:|---:|---|
| Rent presence only (HC1) | Log median gross rent | College present (0/1) | 0.0002 (0.0057) | [-0.0110, 0.0114] | 0.971 | 3136 | All counties |
| Rent intensity among college counties | Log median gross rent | Intensity among college counties (1 pp) | 0.0020*** (0.0004) | [0.0012, 0.0029] | <0.001 | 1398 | College counties only |
| Rent two-part decomposition | Log median gross rent | College present (0/1) | -0.0020 (0.0057) | [-0.0132, 0.0092] | 0.731 | 3136 | All counties |
| Rent two-part decomposition | Log median gross rent | Conditional intensity (1 pp from positive-county mean) | 0.0019*** (0.0004) | [0.0012, 0.0027] | <0.001 | 3136 | All counties |
| Rent two-part (state-clustered SE) | Log median gross rent | College present (0/1) | -0.0020 (0.0063) | [-0.0143, 0.0104] | 0.754 | 3136 | All counties |
| Rent two-part (state-clustered SE) | Log median gross rent | Conditional intensity (1 pp from positive-county mean) | 0.0019*** (0.0004) | [0.0012, 0.0026] | <0.001 | 3136 | All counties |
| Rent two-part winsorized intensity | Log median gross rent | College present (0/1) | -0.0025 (0.0057) | [-0.0137, 0.0087] | 0.665 | 3136 | All counties |
| Rent two-part winsorized intensity | Log median gross rent | Conditional intensity, winsorized (1 pp from positive-county mean) | 0.0025*** (0.0004) | [0.0018, 0.0033] | <0.001 | 3136 | All counties |
| Wage presence only (HC1) | Log average weekly wage | College present (0/1) | -0.0060 (0.0070) | [-0.0196, 0.0077] | 0.392 | 3143 | All counties |
| Wage intensity among college counties | Log average weekly wage | Intensity among college counties (1 pp) | 0.0007* (0.0004) | [-0.0000, 0.0015] | 0.050 | 1398 | College counties only |
| Wage two-part decomposition | Log average weekly wage | College present (0/1) | -0.0063 (0.0070) | [-0.0201, 0.0074] | 0.367 | 3143 | All counties |
| Wage two-part decomposition | Log average weekly wage | Conditional intensity (1 pp from positive-county mean) | 0.0003 (0.0004) | [-0.0005, 0.0010] | 0.454 | 3143 | All counties |
| Wage two-part (state-clustered SE) | Log average weekly wage | College present (0/1) | -0.0063 (0.0091) | [-0.0242, 0.0116] | 0.489 | 3143 | All counties |
| Wage two-part (state-clustered SE) | Log average weekly wage | Conditional intensity (1 pp from positive-county mean) | 0.0003 (0.0004) | [-0.0005, 0.0011] | 0.492 | 3143 | All counties |
| Wage two-part winsorized intensity | Log average weekly wage | College present (0/1) | -0.0064 (0.0070) | [-0.0202, 0.0074] | 0.362 | 3143 | All counties |
| Wage two-part winsorized intensity | Log average weekly wage | Conditional intensity, winsorized (1 pp from positive-county mean) | 0.0004 (0.0005) | [-0.0005, 0.0013] | 0.409 | 3143 | All counties |
- Interpretation remains associational (cross-sectional; not causal).

Notes: * p<0.10, ** p<0.05, *** p<0.01
