# Presentation Results Brief

Key coefficient shown below is the estimated association for a 1 percentage-point increase in county college intensity.

| Specification | Outcome | Coef (SE) | 95% CI | p-value | N |
|---|---|---:|---:|---:|---:|
| Rent baseline (HC1) | Log median gross rent | 0.0015*** (0.0003) | [0.0009, 0.0021] | <0.001 | 3214 |
| Rent baseline (state-clustered SE) | Log median gross rent | 0.0015*** (0.0003) | [0.0009, 0.0021] | <0.001 | 3214 |
| Rent + renter share | Log median gross rent | -0.0001 (0.0003) | [-0.0007, 0.0004] | 0.644 | 3214 |
| Rent + BA share | Log median gross rent | -0.0005* (0.0003) | [-0.0011, 0.0000] | 0.066 | 3214 |
| Rent winsorized intensity | Log median gross rent | 0.0020*** (0.0004) | [0.0013, 0.0027] | <0.001 | 3214 |
| Wage baseline (HC1) | Log average weekly wage | 0.0001 (0.0003) | [-0.0005, 0.0008] | 0.685 | 3221 |
| Wage baseline (state-clustered SE) | Log average weekly wage | 0.0001 (0.0003) | [-0.0005, 0.0007] | 0.642 | 3221 |
| Wage winsorized intensity | Log average weekly wage | 0.0002 (0.0004) | [-0.0007, 0.0011] | 0.644 | 3221 |

## Slide-ready takeaway
- Baseline rent model: college intensity is positively associated with rent (beta=0.0015, p<0.001), about 0.15% higher rent per +1 pp college intensity.
- Baseline wage model: association with wage is near zero and statistically weak (beta=0.0001, p=0.685, ~0.01% per +1 pp).
- Rent decomposition: once presence and size are separated, the extensive-margin indicator is near zero (beta=-0.0026, p=0.647), while the conditional intensity term stays positive (beta=0.0019, p<0.001).
- Wage decomposition: the pooled two-part model shows little evidence for either college presence or conditional intensity, but the college-only intensive spec is modestly positive (beta=0.0008, p=0.044).

## One-Slide Comparison

| Outcome | Baseline pooled intensity | Presence only (0/1) | Intensive only (+1 pp) | Two-part presence (0/1) | Two-part intensity (+1 pp) | Presentation takeaway |
|---|---|---|---|---|---|---|
| Log median gross rent | +0.15% per +1 pp*** | -0.06% | +0.20% per +1 pp*** | -0.26% | +0.19% per +1 pp*** | Scale matters more than simple presence. |
| Log average weekly wage | +0.01% per +1 pp | -0.43% | +0.08% per +1 pp** | -0.47% | +0.03% per +1 pp | Any wage signal is limited to college counties only. |

## Margin Decomposition

| Specification | Outcome | Term | Coef (SE) | 95% CI | p-value | N | Sample |
|---|---|---|---:|---:|---:|---:|---|
| Rent presence only (HC1) | Log median gross rent | College present (0/1) | -0.0006 (0.0056) | [-0.0116, 0.0104] | 0.920 | 3214 | All counties |
| Rent intensity among college counties | Log median gross rent | Intensity among college counties (1 pp) | 0.0020*** (0.0004) | [0.0012, 0.0028] | <0.001 | 1425 | College counties only |
| Rent two-part decomposition | Log median gross rent | College present (0/1) | -0.0026 (0.0056) | [-0.0135, 0.0084] | 0.647 | 3214 | All counties |
| Rent two-part decomposition | Log median gross rent | Conditional intensity (1 pp from positive-county mean) | 0.0019*** (0.0004) | [0.0011, 0.0026] | <0.001 | 3214 | All counties |
| Rent two-part (state-clustered SE) | Log median gross rent | College present (0/1) | -0.0026 (0.0061) | [-0.0146, 0.0095] | 0.676 | 3214 | All counties |
| Rent two-part (state-clustered SE) | Log median gross rent | Conditional intensity (1 pp from positive-county mean) | 0.0019*** (0.0004) | [0.0012, 0.0026] | <0.001 | 3214 | All counties |
| Rent two-part winsorized intensity | Log median gross rent | College present (0/1) | -0.0030 (0.0056) | [-0.0140, 0.0080] | 0.589 | 3214 | All counties |
| Rent two-part winsorized intensity | Log median gross rent | Conditional intensity, winsorized (1 pp from positive-county mean) | 0.0025*** (0.0004) | [0.0017, 0.0032] | <0.001 | 3214 | All counties |
| Wage presence only (HC1) | Log average weekly wage | College present (0/1) | -0.0043 (0.0069) | [-0.0178, 0.0092] | 0.530 | 3221 | All counties |
| Wage intensity among college counties | Log average weekly wage | Intensity among college counties (1 pp) | 0.0008** (0.0004) | [0.0000, 0.0015] | 0.044 | 1425 | College counties only |
| Wage two-part decomposition | Log average weekly wage | College present (0/1) | -0.0047 (0.0069) | [-0.0183, 0.0089] | 0.498 | 3221 | All counties |
| Wage two-part decomposition | Log average weekly wage | Conditional intensity (1 pp from positive-county mean) | 0.0003 (0.0004) | [-0.0004, 0.0011] | 0.418 | 3221 | All counties |
| Wage two-part (state-clustered SE) | Log average weekly wage | College present (0/1) | -0.0047 (0.0090) | [-0.0223, 0.0129] | 0.602 | 3221 | All counties |
| Wage two-part (state-clustered SE) | Log average weekly wage | Conditional intensity (1 pp from positive-county mean) | 0.0003 (0.0004) | [-0.0005, 0.0011] | 0.454 | 3221 | All counties |
| Wage two-part winsorized intensity | Log average weekly wage | College present (0/1) | -0.0048 (0.0069) | [-0.0184, 0.0088] | 0.491 | 3221 | All counties |
| Wage two-part winsorized intensity | Log average weekly wage | Conditional intensity, winsorized (1 pp from positive-county mean) | 0.0004 (0.0005) | [-0.0005, 0.0013] | 0.366 | 3221 | All counties |
- Interpretation remains associational (cross-sectional; not causal).

Notes: * p<0.10, ** p<0.05, *** p<0.01
