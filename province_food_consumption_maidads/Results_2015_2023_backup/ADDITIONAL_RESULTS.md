# 追加处理与稳健性估计结果

## 一、已补充内容

- 主结果采用全国非食品 CPI；稳健性用食物支出份额近似反推出省级非食品 CPI。
- 构造 `cpi_nonfood` 省级近似非食品价格口径并重新估计 AIDADS/MAIDADS。
- 对每个 `variant × model` 分别用 2015-2020 年训练、2021-2023 年测试，以及 2015-2022 年训练、2023 年测试做样本外验证。
- 做 1000 次省份簇 bootstrap（正式规模），其中 998 次完全收敛；关键区间仅用完全收敛 draw 汇总。
- LR cluster bootstrap 已完成 500 次（正式规模），其中 462 次成功；普通 χ² p 值不作为有效推断。

## 二、CPI 非食品稳健性估计
| model | nll | success | message |
| --- | --- | --- | --- |
| AIDADS_sat | -3013.916 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH |
| MAIDADS_sat | -3232.579 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH |

## 三、样本外验证
| variant | model | train_years | test_years | group | rmse_x | mae_x | mean_x | n_test | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | dairyegg | 0.012 | 0.010 | 0.034 | 93.000 | 0.371 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | grain | 0.067 | 0.055 | 0.420 | 93.000 | 0.160 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | meatsea | 0.075 | 0.060 | 0.171 | 93.000 | 0.437 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | nonfood | 4.651 | 3.708 | 198.051 | 93.000 | 0.023 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | oil | 0.031 | 0.025 | 0.129 | 93.000 | 0.243 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | vegfruit | 0.012 | 0.010 | 0.055 | 93.000 | 0.215 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | dairyegg | 0.012 | 0.010 | 0.034 | 93.000 | 0.345 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | grain | 0.065 | 0.053 | 0.420 | 93.000 | 0.154 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | meatsea | 0.073 | 0.058 | 0.171 | 93.000 | 0.425 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | nonfood | 4.405 | 3.509 | 198.051 | 93.000 | 0.022 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | oil | 0.032 | 0.025 | 0.129 | 93.000 | 0.251 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | vegfruit | 0.010 | 0.008 | 0.055 | 93.000 | 0.176 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2022 | 2023 | dairyegg | 0.013 | 0.011 | 0.035 | 31.000 | 0.373 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2022 | 2023 | grain | 0.068 | 0.055 | 0.405 | 31.000 | 0.167 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2022 | 2023 | meatsea | 0.073 | 0.057 | 0.184 | 31.000 | 0.397 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2022 | 2023 | nonfood | 4.193 | 3.505 | 205.931 | 31.000 | 0.020 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2022 | 2023 | oil | 0.032 | 0.026 | 0.126 | 31.000 | 0.253 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2022 | 2023 | vegfruit | 0.012 | 0.009 | 0.056 | 31.000 | 0.209 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2022 | 2023 | dairyegg | 0.012 | 0.010 | 0.035 | 31.000 | 0.354 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2022 | 2023 | grain | 0.064 | 0.054 | 0.405 | 31.000 | 0.158 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2022 | 2023 | meatsea | 0.067 | 0.052 | 0.184 | 31.000 | 0.366 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2022 | 2023 | nonfood | 4.246 | 3.540 | 205.931 | 31.000 | 0.021 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2022 | 2023 | oil | 0.031 | 0.025 | 0.126 | 31.000 | 0.242 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2022 | 2023 | vegfruit | 0.010 | 0.008 | 0.056 | 31.000 | 0.179 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | dairyegg | 0.013 | 0.010 | 0.034 | 93.000 | 0.377 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | grain | 0.067 | 0.055 | 0.420 | 93.000 | 0.160 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | meatsea | 0.073 | 0.058 | 0.171 | 93.000 | 0.426 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | nonfood | 4.617 | 3.678 | 198.042 | 93.000 | 0.023 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | oil | 0.031 | 0.025 | 0.129 | 93.000 | 0.244 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | vegfruit | 0.012 | 0.010 | 0.055 | 93.000 | 0.217 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | dairyegg | 0.012 | 0.010 | 0.034 | 93.000 | 0.355 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | grain | 0.065 | 0.053 | 0.420 | 93.000 | 0.154 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | meatsea | 0.068 | 0.054 | 0.171 | 93.000 | 0.397 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | nonfood | 4.530 | 3.627 | 198.042 | 93.000 | 0.023 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | oil | 0.031 | 0.025 | 0.129 | 93.000 | 0.241 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | vegfruit | 0.010 | 0.008 | 0.055 | 93.000 | 0.186 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2022 | 2023 | dairyegg | 0.013 | 0.011 | 0.035 | 31.000 | 0.375 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2022 | 2023 | grain | 0.067 | 0.055 | 0.405 | 31.000 | 0.167 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2022 | 2023 | meatsea | 0.074 | 0.058 | 0.184 | 31.000 | 0.402 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2022 | 2023 | nonfood | 4.262 | 3.556 | 205.931 | 31.000 | 0.021 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2022 | 2023 | oil | 0.032 | 0.026 | 0.126 | 31.000 | 0.253 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2022 | 2023 | vegfruit | 0.012 | 0.009 | 0.056 | 31.000 | 0.209 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2022 | 2023 | dairyegg | 0.012 | 0.010 | 0.035 | 31.000 | 0.356 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2022 | 2023 | grain | 0.064 | 0.054 | 0.405 | 31.000 | 0.157 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2022 | 2023 | meatsea | 0.068 | 0.053 | 0.184 | 31.000 | 0.371 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2022 | 2023 | nonfood | 4.291 | 3.579 | 205.931 | 31.000 | 0.021 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2022 | 2023 | oil | 0.031 | 0.025 | 0.126 | 31.000 | 0.244 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2022 | 2023 | vegfruit | 0.010 | 0.008 | 0.056 | 31.000 | 0.180 |

## 四、模型比较
| variant | model | nll | k_effective | aic | bic | success | lr_stat | p_value_chi2 | chi2_p_value_status | cluster_bootstrap_tail_probability | lr_bootstrap_successful_reps | oos_food_rmse_mean | lr_bootstrap_completed_reps | lr_bootstrap_reps | lr_bootstrap_inference_scale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | -3008.279 | 12.000 | -5992.558 | -5948.984 | True |  |  |  |  |  | 0.039 |  |  |  |
| baseline_real_national_nonfood | MAIDADS_sat | -3228.932 | 19.000 | -6419.865 | -6350.872 | True |  |  |  |  |  | 0.038 |  |  |  |
| robust_real_derived_cpi_nonfood | AIDADS_sat | -3013.916 | 12.000 | -6003.832 | -5960.257 | True |  |  |  |  |  | 0.039 |  |  |  |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | -3232.579 | 19.000 | -6427.158 | -6358.165 | True |  |  |  |  |  | 0.037 |  |  |  |
| baseline_real_national_nonfood | LR_MAIDADS_vs_AIDADS |  | 7.000 |  |  | True | 441.306 |  | invalid_not_reported_unidentified_nuisance_under_H0 | 0.297 | 462.000 |  | 500.000 | 500.000 | formal |

## 五、LR cluster bootstrap

普通 χ² p 值因 MAIDADS 在 AIDADS 原假设下存在不可识别 nuisance parameter，本轮不作为有效推断报告。
| test | observed_lr | bootstrap_reps | completed_reps | successful_reps | convergence_rate | cluster_bootstrap_tail_probability | lr_bootstrap_median | lr_bootstrap_q95 | lr_bootstrap_q99 | chi2_p_value_status | note | inference_scale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MAIDADS_vs_AIDADS | 441.306 | 500.000 | 500.000 | 462.000 | 0.924 | 0.297 | 298.557 | 672.592 | 730.011 | invalid_not_reported | Cluster bootstrap with province-block resampling; chi-square p-value not used. | formal |

## 六、bootstrap 关键区间
| metric | group_or_item | year | ci_2_5 | median | ci_97_5 | n_success_draws | target_reps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| daily_kcal_per_cap_weighted | dairyegg | 2050.000 | 62.566 | 73.268 | 103.948 | 998.000 | 1000.000 |
| daily_kcal_per_cap_weighted | grain | 2050.000 | 560.273 | 724.481 | 851.645 | 998.000 | 1000.000 |
| daily_kcal_per_cap_weighted | meatsea | 2050.000 | 322.940 | 379.439 | 615.096 | 998.000 | 1000.000 |
| daily_kcal_per_cap_weighted | oil | 2050.000 | 191.374 | 238.744 | 293.047 | 998.000 | 1000.000 |
| daily_kcal_per_cap_weighted | vegfruit | 2050.000 | 104.573 | 120.937 | 149.166 | 998.000 | 1000.000 |
| feed_grain_million_ton | aquatic | 2050.000 | 21.073 | 24.756 | 40.335 | 998.000 | 1000.000 |
| feed_grain_million_ton | beef | 2050.000 | 35.045 | 40.791 | 65.266 | 998.000 | 1000.000 |
| feed_grain_million_ton | egg | 2050.000 | 42.412 | 49.589 | 70.475 | 998.000 | 1000.000 |
| feed_grain_million_ton | milk | 2050.000 | 9.787 | 11.488 | 16.235 | 998.000 | 1000.000 |
| feed_grain_million_ton | mutton | 2050.000 | 23.317 | 27.247 | 42.584 | 998.000 | 1000.000 |
| feed_grain_million_ton | pork | 2050.000 | 132.797 | 155.950 | 253.277 | 998.000 | 1000.000 |
| feed_grain_million_ton | poultry | 2050.000 | 41.373 | 48.619 | 78.798 | 998.000 | 1000.000 |

## 七、输出文件

- `province_cpi_indices.csv`：省级总/食品/近似非食品 CPI 与 2023=100 指数。
- `robustness_cpi_nonfood_parameter_estimates.csv`：CPI 非食品价格口径参数。
- `robustness_cpi_nonfood_fit_by_group.csv`：CPI 非食品价格口径拟合误差。
- `robustness_cpi_nonfood_projection_group_2030_2035_2050.csv`：CPI 稳健预测。
- `oos_fit_by_group.csv`、`oos_predictions.csv` 与 `Results/OOS/oos_predictions__*.csv`：按口径、模型、样本切分独立保存的样本外验证。
- `bootstrap_key_ci.csv`、`bootstrap_parameter_ci.csv`、`bootstrap_draw_metrics.csv`：bootstrap 区间和抽样明细。
- `lr_test_chi2_and_bootstrap.csv`、`lr_bootstrap_draws.csv`：LR 检验的 cluster bootstrap 摘要和抽样明细。

## 八、仍需人工确认

- 食品 CPI 三个文件是分段表，本脚本按年份拼接；请后续核对 2015 年以前文件是否确为同一食品分类口径。
- 省级非食品 CPI 由总 CPI、食品 CPI、食物支出份额反推，是近似值；更理想的是直接拿到省级非食品 CPI。
- 正式规模 bootstrap 与 LR cluster bootstrap 已完成；若模型选择推断成为论文核心，可追加 parametric-null LR bootstrap 稳健性。
- 预测人口路径已改用 Chen et al. (2020) SSP2 省级人口预测；收入、城镇化和年龄结构路径仍需更正式的数据来源。