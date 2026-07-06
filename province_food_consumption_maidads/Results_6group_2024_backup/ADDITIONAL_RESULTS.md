# 追加处理与稳健性估计结果

## 一、已补充内容

- 主结果采用全国非食品 CPI；稳健性用食物支出份额近似反推出省级非食品 CPI。
- 构造 `cpi_nonfood` 省级近似非食品价格口径并重新估计 AIDADS/MAIDADS。
- 对每个 `variant × model` 分别用 2015-2020 年训练、2021-2023 年测试，以及 2015-2022 年训练、2023 年测试做样本外验证。
- 做 30 次省份簇 bootstrap，其中 26 次完全收敛；关键区间仅用完全收敛 draw 汇总。

## 二、CPI 非食品稳健性估计
- AIDADS_sat: nll=-3328.578, success=True, message=CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH
- MAIDADS_sat: nll=-3414.548, success=True, message=CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH

## 三、样本外验证
| variant | model | train_years | test_years | group | rmse_x | mae_x | mean_x | n_test | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | dairyegg | 0.0124989 | 0.0102278 | 0.0336588 | 93 | 0.371343 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | grain | 0.0672176 | 0.0546952 | 0.420289 | 93 | 0.159932 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | meatsea | 0.0746015 | 0.0601062 | 0.170545 | 93 | 0.437429 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | nonfood | 4.65074 | 3.70774 | 198.051 | 93 | 0.0234825 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | oil | 0.0313052 | 0.0249081 | 0.128885 | 93 | 0.242893 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | vegfruit | 0.0118541 | 0.00974136 | 0.0550384 | 93 | 0.21538 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | dairyegg | 0.011623 | 0.00954878 | 0.0336588 | 93 | 0.345318 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | grain | 0.0645467 | 0.0532897 | 0.420289 | 93 | 0.153577 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | meatsea | 0.0725186 | 0.0578101 | 0.170545 | 93 | 0.425216 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | nonfood | 4.40309 | 3.50709 | 198.051 | 93 | 0.0222321 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | oil | 0.0323449 | 0.0252763 | 0.128885 | 93 | 0.25096 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | vegfruit | 0.00968924 | 0.00784399 | 0.0550384 | 93 | 0.176045 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2022 | 2023 | dairyegg | 0.0129973 | 0.0106364 | 0.0348762 | 31 | 0.37267 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2022 | 2023 | grain | 0.0677645 | 0.0549458 | 0.404668 | 31 | 0.167457 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2022 | 2023 | meatsea | 0.0729456 | 0.0568945 | 0.18365 | 31 | 0.397199 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2022 | 2023 | nonfood | 4.19415 | 3.50592 | 205.931 | 31 | 0.0203668 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2022 | 2023 | oil | 0.0319637 | 0.0259932 | 0.126385 | 31 | 0.252906 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2022 | 2023 | vegfruit | 0.0117516 | 0.00938812 | 0.0563143 | 31 | 0.208679 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2022 | 2023 | dairyegg | 0.0123396 | 0.0100264 | 0.0348762 | 31 | 0.353811 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2022 | 2023 | grain | 0.0639744 | 0.0535359 | 0.404668 | 31 | 0.158091 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2022 | 2023 | meatsea | 0.0673276 | 0.0520197 | 0.18365 | 31 | 0.366608 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2022 | 2023 | nonfood | 4.24691 | 3.54024 | 205.931 | 31 | 0.020623 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2022 | 2023 | oil | 0.030635 | 0.0246241 | 0.126385 | 31 | 0.242394 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2022 | 2023 | vegfruit | 0.0100959 | 0.00801841 | 0.0563143 | 31 | 0.179277 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | dairyegg | 0.012677 | 0.0103448 | 0.0336588 | 93 | 0.376633 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | grain | 0.0673028 | 0.0550198 | 0.420289 | 93 | 0.160134 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | meatsea | 0.0726963 | 0.0583694 | 0.170545 | 93 | 0.426258 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | nonfood | 4.61776 | 3.67863 | 198.042 | 93 | 0.023317 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | oil | 0.031494 | 0.0248755 | 0.128885 | 93 | 0.244358 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | vegfruit | 0.0119487 | 0.00984727 | 0.0550384 | 93 | 0.217097 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | dairyegg | 0.0119496 | 0.00978706 | 0.0336588 | 93 | 0.355021 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | grain | 0.0648817 | 0.0534854 | 0.420289 | 93 | 0.154374 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | meatsea | 0.0676674 | 0.0536427 | 0.170545 | 93 | 0.396771 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | nonfood | 4.52837 | 3.62571 | 198.042 | 93 | 0.0228657 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | oil | 0.0310994 | 0.0247073 | 0.128885 | 93 | 0.241296 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | vegfruit | 0.010216 | 0.00828069 | 0.0550384 | 93 | 0.185616 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2022 | 2023 | dairyegg | 0.013083 | 0.0106936 | 0.0348762 | 31 | 0.375125 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2022 | 2023 | grain | 0.0674201 | 0.055006 | 0.404668 | 31 | 0.166606 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2022 | 2023 | meatsea | 0.0738846 | 0.057773 | 0.18365 | 31 | 0.402312 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2022 | 2023 | nonfood | 4.26139 | 3.55486 | 205.931 | 31 | 0.0206933 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2022 | 2023 | oil | 0.0319625 | 0.0258517 | 0.126385 | 31 | 0.252897 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2022 | 2023 | vegfruit | 0.0117868 | 0.00943 | 0.0563143 | 31 | 0.209305 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2022 | 2023 | dairyegg | 0.0124047 | 0.0100783 | 0.0348762 | 31 | 0.355677 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2022 | 2023 | grain | 0.0637344 | 0.053532 | 0.404668 | 31 | 0.157498 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2022 | 2023 | meatsea | 0.0680316 | 0.0525224 | 0.18365 | 31 | 0.370442 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2022 | 2023 | nonfood | 4.29166 | 3.5799 | 205.931 | 31 | 0.0208403 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2022 | 2023 | oil | 0.0307841 | 0.0245879 | 0.126385 | 31 | 0.243573 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2022 | 2023 | vegfruit | 0.0101571 | 0.00805397 | 0.0563143 | 31 | 0.180365 |

## 四、模型比较
| variant | model | nll | k_effective | aic | bic | success | lr_stat | p_value_chi2 | chi2_p_value_status | cluster_bootstrap_tail_probability | lr_bootstrap_successful_reps | oos_food_rmse_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | -3321.36 | 12 | -6618.73 | -6573.89 | True |  |  |  |  |  | 0.03949 |
| baseline_real_national_nonfood | MAIDADS_sat | -3552.32 | 19 | -7066.63 | -6995.64 | True |  |  |  |  |  | 0.0375095 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | -3328.58 | 12 | -6633.16 | -6588.32 | True |  |  |  |  |  | 0.0394256 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | -3414.55 | 19 | -6791.1 | -6720.1 | True |  |  |  |  |  | 0.0370926 |
| baseline_real_national_nonfood | LR_MAIDADS_vs_AIDADS |  | 7 |  |  | True | 461.904 |  | invalid_not_reported_unidentified_nuisance_under_H0 | 0.454545 | 11 |  |

## 五、LR bootstrap（pilot）

普通 χ² p 值因 MAIDADS 在 AIDADS 原假设下存在不可识别 nuisance parameter，本轮不作为有效推断报告。
| test | observed_lr | bootstrap_reps | successful_reps | cluster_bootstrap_tail_probability | lr_bootstrap_median | lr_bootstrap_q95 | chi2_p_value_status | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MAIDADS_vs_AIDADS | 461.904 | 12 | 11 | 0.454545 | 175.491 | 674.354 | invalid_not_reported | Cluster bootstrap pilot; chi-square reference not used. |

## 六、bootstrap 关键区间
| metric | group_or_item | year | ci_2_5 | median | ci_97_5 |
| --- | --- | --- | --- | --- | --- |
| daily_kcal_per_cap_weighted | dairyegg | 2050 | 72.3032 | 93.1023 | 122.923 |
| daily_kcal_per_cap_weighted | grain | 2050 | 348.491 | 547.881 | 736.492 |
| daily_kcal_per_cap_weighted | meatsea | 2050 | 364.063 | 507.259 | 718.809 |
| daily_kcal_per_cap_weighted | oil | 2050 | 141.363 | 200.036 | 282.333 |
| daily_kcal_per_cap_weighted | vegfruit | 2050 | 121.161 | 141.804 | 178.257 |
| feed_grain_million_ton | aquatic | 2050 | 23.6617 | 33.0853 | 47.3358 |
| feed_grain_million_ton | beef | 2050 | 38.7358 | 53.9332 | 76.1496 |
| feed_grain_million_ton | egg | 2050 | 48.9736 | 63.0938 | 83.2948 |
| feed_grain_million_ton | milk | 2050 | 11.3244 | 14.5618 | 19.231 |
| feed_grain_million_ton | mutton | 2050 | 25.6376 | 35.5755 | 49.1879 |
| feed_grain_million_ton | pork | 2050 | 149.886 | 208.888 | 295.81 |
| feed_grain_million_ton | poultry | 2050 | 46.5987 | 64.9454 | 92.1647 |

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
- 当前 bootstrap 或 LR bootstrap 仍低于正式规模；正式论文版请把对应 reps 提高到 500-1000。