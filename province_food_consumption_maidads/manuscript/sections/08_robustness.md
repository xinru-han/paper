# 8. Robustness and Audit Findings

The main robustness exercise replaces the national non-food CPI residual price with a derived provincial non-food CPI. The resulting MAIDADS fit remains better than AIDADS within that specification. Cross-specification AIC and BIC comparisons should not be over-interpreted because the residual-price construction differs across specifications.

The code audit also changed several data and reporting conventions. The residual category is described as other/non-covered expenditure rather than strict non-food consumption. The grain-calorie calculation uses actual calorie weights rather than the potato grain-equivalent conversion. OOS files are stored separately by variant, model, and split. The projection module now uses Chen et al. (2020) SSP2 provincial population paths rather than population-share trend extrapolation. The paper workflow records a YELLOW gate status because the income side of projections remains a conditional scenario, not because bootstrap inference is still pilot-scale.

Unsupported or weak claims to resolve:
- Add official non-food CPI or CPI category weights.
- Add leave-one-province and leave-one-region validation.
