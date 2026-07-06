# 5. Estimation, Fit, and Diagnostics

Table 1 summarizes the fit of AIDADS and MAIDADS under the main and robustness price specifications.

| variant | model | nll | aic | bic | oos_food_rmse_mean |
| --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | -3008.279 | -5992.558 | -5948.984 | 0.039 |
| baseline_real_national_nonfood | MAIDADS_sat | -3228.932 | -6419.865 | -6350.872 | 0.038 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | -3013.916 | -6003.832 | -5960.257 | 0.039 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | -3232.579 | -6427.158 | -6358.165 | 0.037 |

In the main specification, MAIDADS lowers the concentrated negative log likelihood relative to AIDADS. Out-of-sample validation is now computed separately for each model and specification, avoiding the earlier error in which a single OOS statistic could be broadcast across rows. The main-specification mean food RMSE is lower for MAIDADS than AIDADS, but the improvement is modest and should be interpreted together with the split-specific group errors.

The LR statistic comparing MAIDADS and AIDADS is 441.306. However, the standard chi-square reference distribution is not used for inference because nuisance parameters are not identified under the restricted model. The current LR bootstrap is formal-scale: 462 successful draws out of 500, with a cluster-bootstrap tail probability of 0.297. This result cautions against interpreting the large in-sample LR statistic as decisive model-selection evidence.

The theoretical consistency checks are numerically tight. The maximum absolute consistency error across the recorded adding-up, homogeneity, and Slutsky checks is 9.25e-08. Parameter boundary reports distinguish restrictions imposed by saturation from parameters estimated near a boundary.

Unsupported or weak claims to resolve:
- Clarify the null-resampling interpretation of the LR bootstrap and consider a parametric-null bootstrap robustness check.
- Add a table of split-specific OOS results in the appendix.
