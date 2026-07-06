# 人均 GDP + 猪肉拆分 MAIDADS 完整结果整合

- 生成时间：2026-07-06T04:28:44.017972
- 主模型设定：预算变量使用实际人均 GDP，`m = pgdp / monetary_deflator`。
- 分类：`grain / oil / vegfruit / pork / nonpork_meatsea / dairyegg / nonfood`。
- `nonpork_meatsea = beef + mutton + poultry + aquatic`。
- Bootstrap：省份簇重抽样，整省 2015-2023 年作为一个 block。

## 一、模型品类

| group | label_cn | items |
| --- | --- | --- |
| grain | 粮食/主粮 | grain |
| oil | 食用油 | oil |
| vegfruit | 蔬菜水果 | vegetable+fruit |
| pork | 猪肉 | pork |
| nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic |
| dairyegg | 奶蛋类 | milk+egg |
| nonfood | 其他/未覆盖支出 |  |

## 二、点估计与诊断：baseline_real_national_nonfood

### m 口径描述

| index | count | mean | std | min | 5% | 25% | 50% | 75% | 95% | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| m | 310 | 68076 | 30754.4 | 29310.6 | 37877.4 | 47585.4 | 58111.2 | 78846.2 | 138569 | 184841 |
| m_consumption_real | 310 | 20783.7 | 7227.42 | 9341.54 | 13675.1 | 16193 | 18427 | 22607 | 39547.7 | 45592.9 |
| pgdp_nominal | 310 | 64865.5 | 30158.3 | 25946 | 33853.7 | 44453.9 | 56007.7 | 76658.9 | 130231 | 185026 |
| covered_food_exp_split | 310 | 2384.22 | 395.434 | 1597.62 | 1827.6 | 2077.46 | 2372.28 | 2652.87 | 3061.65 | 3940.11 |
| nonfood_exp_split | 310 | 65691.8 | 30721.1 | 26870.4 | 35830.7 | 45037.2 | 55797.2 | 76556 | 136351 | 183003 |

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | -4341 | 15 | -8651 | -8595 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2903 |  |  |
| baseline_real_national_nonfood | MAIDADS_sat | -4428 | 23 | -8810 | -8724 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2802 |  |  |
| baseline_real_national_nonfood | LR_MAIDADS_vs_AIDADS |  | 8 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 174.7 | invalid_not_reported_unidentified_nuisance_under_H0 |

### MAIDADS 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04332 | 0.03489 | 0.1059 | 0.4091 |
| baseline_real_national_nonfood | MAIDADS_sat | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic | 0.01624 | 0.01246 | 0.04128 | 0.3933 |
| baseline_real_national_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008499 | 0.007043 | 0.03001 | 0.2832 |
| baseline_real_national_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03105 | 0.0255 | 0.1273 | 0.2438 |
| baseline_real_national_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009457 | 0.007225 | 0.05165 | 0.1831 |
| baseline_real_national_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.06951 | 0.04872 | 0.4123 | 0.1686 |
| baseline_real_national_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.586 | 2.899 | 683.8 | 0.005244 |

### 理论一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 7.32417e-10 |
| max_abs_price_adding_up_error | 1.27205e-10 |
| max_abs_marshallian_homogeneity_error | 1.7681e-08 |
| max_abs_hicksian_homogeneity_error | 1.7681e-08 |
| max_abs_slutsky_symmetry_error | 1.50968e-10 |

## 二、点估计与诊断：robust_real_derived_cpi_nonfood

### m 口径描述

| index | count | mean | std | min | 5% | 25% | 50% | 75% | 95% | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| m | 310 | 68076 | 30754.4 | 29310.6 | 37877.4 | 47585.4 | 58111.2 | 78846.2 | 138569 | 184841 |
| m_consumption_real | 310 | 20783.7 | 7227.42 | 9341.54 | 13675.1 | 16193 | 18427 | 22607 | 39547.7 | 45592.9 |
| pgdp_nominal | 310 | 64865.5 | 30158.3 | 25946 | 33853.7 | 44453.9 | 56007.7 | 76658.9 | 130231 | 185026 |
| covered_food_exp_split | 310 | 2384.22 | 395.434 | 1597.62 | 1827.6 | 2077.46 | 2372.28 | 2652.87 | 3061.65 | 3940.11 |
| nonfood_exp_split | 310 | 65691.8 | 30721.1 | 26870.4 | 35830.7 | 45037.2 | 55797.2 | 76556 | 136351 | 183003 |

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | -4370 | 15 | -8709 | -8653 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2877 |  |  |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | -4439 | 23 | -8832 | -8746 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2801 |  |  |
| robust_real_derived_cpi_nonfood | LR_MAIDADS_vs_AIDADS |  | 8 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 138.7 | invalid_not_reported_unidentified_nuisance_under_H0 |

### MAIDADS 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04322 | 0.03475 | 0.1059 | 0.4081 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic | 0.01626 | 0.01248 | 0.04128 | 0.3938 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008499 | 0.007045 | 0.03001 | 0.2832 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03105 | 0.02544 | 0.1273 | 0.2438 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009456 | 0.007234 | 0.05165 | 0.1831 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.06956 | 0.04857 | 0.4123 | 0.1687 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.555 | 2.879 | 679 | 0.005236 |

### 理论一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 7.745e-10 |
| max_abs_price_adding_up_error | 1.25435e-10 |
| max_abs_marshallian_homogeneity_error | 1.96888e-08 |
| max_abs_hicksian_homogeneity_error | 1.96888e-08 |
| max_abs_slutsky_symmetry_error | 1.63744e-10 |

## 三、平均人均 GDP 水平弹性

| variant | group | group_label_cn | gdp_elasticity | marshallian_own_price | hicksian_own_price | budget_share |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | grain | 粮食/主粮 | -0.2373 | -0.07254 | -0.07375 | 0.005114 |
| baseline_real_national_nonfood | oil | 食用油 | -0.1171 | 0.001105 | -2.865e-05 | 0.009681 |
| baseline_real_national_nonfood | vegfruit | 蔬菜水果 | 0.214 | -0.2616 | -0.2602 | 0.006693 |
| baseline_real_national_nonfood | pork | 猪肉 | 0.2303 | -0.6766 | -0.6756 | 0.00447 |
| baseline_real_national_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.3944 | -0.002612 | -4.257e-05 | 0.006516 |
| baseline_real_national_nonfood | dairyegg | 奶蛋类 | 0.4276 | -0.6016 | -0.601 | 0.001453 |
| baseline_real_national_nonfood | nonfood | 其他/未覆盖支出 | 1.032 | -1.003 | -0.006197 | 0.9661 |
| robust_real_derived_cpi_nonfood | grain | 粮食/主粮 | -0.2299 | -0.08636 | -0.08753 | 0.005104 |
| robust_real_derived_cpi_nonfood | oil | 食用油 | -0.1193 | 0.0004013 | -0.0007483 | 0.009634 |
| robust_real_derived_cpi_nonfood | vegfruit | 蔬菜水果 | 0.2189 | -0.2695 | -0.268 | 0.006691 |
| robust_real_derived_cpi_nonfood | pork | 猪肉 | 0.2298 | -0.703 | -0.702 | 0.004478 |
| robust_real_derived_cpi_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.369 | -0.003505 | -0.001111 | 0.006489 |
| robust_real_derived_cpi_nonfood | dairyegg | 奶蛋类 | 0.4439 | -0.6064 | -0.6057 | 0.001451 |
| robust_real_derived_cpi_nonfood | nonfood | 其他/未覆盖支出 | 1.032 | -1.003 | -0.006468 | 0.9662 |

## 四、平均人均 GDP 水平弹性 bootstrap 区间

### gdp_elasticity

_无记录。_

### marshallian_own_price

_无记录。_

### hicksian_own_price

_无记录。_

### budget_share

_无记录。_

## 五、Bootstrap 收敛状态

| variant | target_reps | completed_reps | successful_reps | convergence_rate |
| --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | 1000 | 1000 | 1000 | 1 |
| robust_real_derived_cpi_nonfood | 1000 | 1000 | 999 | 0.999 |

## 六、LR Cluster Bootstrap

| variant | test | observed_lr | bootstrap_reps | completed_reps | successful_reps | convergence_rate | cluster_bootstrap_tail_probability | lr_bootstrap_median | lr_bootstrap_q95 | lr_bootstrap_q99 | chi2_p_value_status | note | inference_scale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | MAIDADS_vs_AIDADS | 174.7 | 500 | 500 | 498 | 0.996 | 0.5201 | 181.5 | 434.3 | 544 | invalid_not_reported | Province-block cluster bootstrap; ordinary chi-square p-value not used. | formal |
| robust_real_derived_cpi_nonfood | MAIDADS_vs_AIDADS | 138.7 | 500 | 500 | 498 | 0.996 | 0.7129 | 190.8 | 425.7 | 519.4 | invalid_not_reported | Province-block cluster bootstrap; ordinary chi-square p-value not used. | formal |

## 七、样本外验证

| variant | model | train_years | test_years | oos_food_rmse_mean | oos_food_relative_rmse_mean | oos_food_mae_mean |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | 0.03353 | 0.3095 | 0.02718 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2022 | 2023 | 0.03258 | 0.2849 | 0.02669 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | 0.02984 | 0.2766 | 0.02447 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2022 | 2023 | 0.0309 | 0.2742 | 0.0252 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | 0.03358 | 0.3133 | 0.02731 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2022 | 2023 | 0.03445 | 0.3094 | 0.02808 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | 0.02984 | 0.2764 | 0.02441 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2022 | 2023 | 0.03088 | 0.2743 | 0.02519 |

## 八、OOS 配对 Bootstrap：AIDADS vs MAIDADS

| variant | train_years | test_years | comparison | observed_mean_diff | ci_2_5 | median | ci_97_5 | p_share_diff_le_0 | bootstrap_reps | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | 2015-2020 | 2021-2023 | AIDADS_MSE_minus_MAIDADS_MSE | 0.0003605 | 9.002e-05 | 0.0003485 | 0.0007301 | 0.005 | 1000 | Positive observed_mean_diff means MAIDADS has lower food MSE than AIDADS. |
| baseline_real_national_nonfood | 2015-2022 | 2023 | AIDADS_MSE_minus_MAIDADS_MSE | 0.0001829 | -7.861e-05 | 0.0001766 | 0.0005269 | 0.105 | 1000 | Positive observed_mean_diff means MAIDADS has lower food MSE than AIDADS. |
| robust_real_derived_cpi_nonfood | 2015-2020 | 2021-2023 | AIDADS_MSE_minus_MAIDADS_MSE | 0.0003514 | 0.0001043 | 0.0003419 | 0.0006772 | 0.003 | 1000 | Positive observed_mean_diff means MAIDADS has lower food MSE than AIDADS. |
| robust_real_derived_cpi_nonfood | 2015-2022 | 2023 | AIDADS_MSE_minus_MAIDADS_MSE | 0.0003387 | 0.0001006 | 0.0003332 | 0.0006606 | 0.002 | 1000 | Positive observed_mean_diff means MAIDADS has lower food MSE than AIDADS. |

## 九、参数 Bootstrap 区间

### alpha

| variant | group | group_label_cn | median | ci_2_5 | ci_97_5 | n_success_draws |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | dairyegg | 奶蛋类 | 0.001887 | 0.0008766 | 0.003542 | 1000 |
| baseline_real_national_nonfood | grain | 粮食/主粮 | 0.00121 | 1.155e-07 | 0.003471 | 1000 |
| baseline_real_national_nonfood | nonfood | 其他/未覆盖支出 | 0.9847 | 0.9736 | 0.9927 | 1000 |
| baseline_real_national_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.0002049 | 1.107e-07 | 0.007723 | 1000 |
| baseline_real_national_nonfood | oil | 食用油 | 0.0001832 | 1.106e-07 | 0.003261 | 1000 |
| baseline_real_national_nonfood | pork | 猪肉 | 0.0077 | 0.004012 | 0.01352 | 1000 |
| baseline_real_national_nonfood | vegfruit | 蔬菜水果 | 0.003451 | 0.001209 | 0.006622 | 1000 |
| robust_real_derived_cpi_nonfood | dairyegg | 奶蛋类 | 0.002025 | 0.000842 | 0.004455 | 999 |
| robust_real_derived_cpi_nonfood | grain | 粮食/主粮 | 0.001573 | 8.437e-07 | 0.004512 | 999 |
| robust_real_derived_cpi_nonfood | nonfood | 其他/未覆盖支出 | 0.9834 | 0.9663 | 0.9925 | 999 |
| robust_real_derived_cpi_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.0001327 | 2.23e-07 | 0.007195 | 999 |
| robust_real_derived_cpi_nonfood | oil | 食用油 | 0.0001178 | 2.041e-07 | 0.003551 | 999 |
| robust_real_derived_cpi_nonfood | pork | 猪肉 | 0.008139 | 0.004076 | 0.01568 | 999 |
| robust_real_derived_cpi_nonfood | vegfruit | 蔬菜水果 | 0.003769 | 0.001182 | 0.008352 | 999 |

### delta

| variant | group | group_label_cn | median | ci_2_5 | ci_97_5 | n_success_draws |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | dairyegg | 奶蛋类 | 2.859e-05 | 2.008e-05 | 5.218e-05 | 1000 |
| baseline_real_national_nonfood | grain | 粮食/主粮 | 0.6512 | 0.4333 | 0.8788 | 1000 |
| baseline_real_national_nonfood | nonfood | 其他/未覆盖支出 | 0.002567 | 0.002322 | 0.002843 | 1000 |
| baseline_real_national_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 6.237e-06 | 6.144e-06 | 7.021e-06 | 1000 |
| baseline_real_national_nonfood | oil | 食用油 | 0.1607 | 0.09465 | 0.246 | 1000 |
| baseline_real_national_nonfood | pork | 猪肉 | 0.06805 | 0.02227 | 0.09885 | 1000 |
| baseline_real_national_nonfood | vegfruit | 蔬菜水果 | 0.02782 | 0.002652 | 0.04153 | 1000 |
| robust_real_derived_cpi_nonfood | dairyegg | 奶蛋类 | 8.502e-06 | 7.674e-06 | 1.045e-05 | 999 |
| robust_real_derived_cpi_nonfood | grain | 粮食/主粮 | 0.6347 | 0.4244 | 0.8567 | 999 |
| robust_real_derived_cpi_nonfood | nonfood | 其他/未覆盖支出 | 28.25 | 5.451e-05 | 349.5 | 999 |
| robust_real_derived_cpi_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.001068 | 6.144e-06 | 0.03473 | 999 |
| robust_real_derived_cpi_nonfood | oil | 食用油 | 0.1605 | 0.09778 | 0.2431 | 999 |
| robust_real_derived_cpi_nonfood | pork | 猪肉 | 0.07273 | 0.03292 | 0.1073 | 999 |
| robust_real_derived_cpi_nonfood | vegfruit | 蔬菜水果 | 0.02789 | 0.002572 | 0.04128 | 999 |

### tau

| variant | group | group_label_cn | median | ci_2_5 | ci_97_5 | n_success_draws |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | dairyegg | 奶蛋类 | 0.02447 | 0.006221 | 0.04287 | 1000 |
| baseline_real_national_nonfood | grain | 粮食/主粮 | 0.1152 | 6.144e-06 | 0.3254 | 1000 |
| baseline_real_national_nonfood | nonfood | 其他/未覆盖支出 | 0.1356 | 0.1221 | 0.1504 | 1000 |
| baseline_real_national_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.07664 | 0.03441 | 0.1045 | 1000 |
| baseline_real_national_nonfood | oil | 食用油 | 0.09188 | 0.003846 | 0.1434 | 1000 |
| baseline_real_national_nonfood | pork | 猪肉 | 0.00053 | 0.00036 | 0.03561 | 1000 |
| baseline_real_national_nonfood | vegfruit | 蔬菜水果 | 0.05236 | 0.03535 | 0.08212 | 1000 |
| robust_real_derived_cpi_nonfood | dairyegg | 奶蛋类 | 0.02521 | 0.005947 | 0.04685 | 999 |
| robust_real_derived_cpi_nonfood | grain | 粮食/主粮 | 0.09873 | 6.97e-06 | 0.3131 | 999 |
| robust_real_derived_cpi_nonfood | nonfood | 其他/未覆盖支出 | 11.99 | 2.189 | 31.13 | 999 |
| robust_real_derived_cpi_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.07188 | 0.03022 | 0.09695 | 999 |
| robust_real_derived_cpi_nonfood | oil | 食用油 | 0.09009 | 0.005121 | 0.1442 | 999 |
| robust_real_derived_cpi_nonfood | pork | 猪肉 | 9.873e-06 | 8.938e-06 | 1.098e-05 | 999 |
| robust_real_derived_cpi_nonfood | vegfruit | 蔬菜水果 | 0.0527 | 0.03513 | 0.08233 | 999 |

### omega

| variant | group | group_label_cn | median | ci_2_5 | ci_97_5 | n_success_draws |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | dairyegg | 奶蛋类 | 0.8009 | 0.4696 | 3.245 | 1000 |
| baseline_real_national_nonfood | grain | 粮食/主粮 | 0.8009 | 0.4696 | 3.245 | 1000 |
| baseline_real_national_nonfood | nonfood | 其他/未覆盖支出 | 0.8009 | 0.4696 | 3.245 | 1000 |
| baseline_real_national_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.8009 | 0.4696 | 3.245 | 1000 |
| baseline_real_national_nonfood | oil | 食用油 | 0.8009 | 0.4696 | 3.245 | 1000 |
| baseline_real_national_nonfood | pork | 猪肉 | 0.8009 | 0.4696 | 3.245 | 1000 |
| baseline_real_national_nonfood | vegfruit | 蔬菜水果 | 0.8009 | 0.4696 | 3.245 | 1000 |
| robust_real_derived_cpi_nonfood | dairyegg | 奶蛋类 | 0.7751 | 0.3699 | 2.918 | 999 |
| robust_real_derived_cpi_nonfood | grain | 粮食/主粮 | 0.7751 | 0.3699 | 2.918 | 999 |
| robust_real_derived_cpi_nonfood | nonfood | 其他/未覆盖支出 | 0.7751 | 0.3699 | 2.918 | 999 |
| robust_real_derived_cpi_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.7751 | 0.3699 | 2.918 | 999 |
| robust_real_derived_cpi_nonfood | oil | 食用油 | 0.7751 | 0.3699 | 2.918 | 999 |
| robust_real_derived_cpi_nonfood | pork | 猪肉 | 0.7751 | 0.3699 | 2.918 | 999 |
| robust_real_derived_cpi_nonfood | vegfruit | 蔬菜水果 | 0.7751 | 0.3699 | 2.918 | 999 |

### kappa

| variant | group | group_label_cn | median | ci_2_5 | ci_97_5 | n_success_draws |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | dairyegg | 奶蛋类 | 6.274 | 5.73 | 6.995 | 1000 |
| baseline_real_national_nonfood | grain | 粮食/主粮 | 6.274 | 5.73 | 6.995 | 1000 |
| baseline_real_national_nonfood | nonfood | 其他/未覆盖支出 | 6.274 | 5.73 | 6.995 | 1000 |
| baseline_real_national_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 6.274 | 5.73 | 6.995 | 1000 |
| baseline_real_national_nonfood | oil | 食用油 | 6.274 | 5.73 | 6.995 | 1000 |
| baseline_real_national_nonfood | pork | 猪肉 | 6.274 | 5.73 | 6.995 | 1000 |
| baseline_real_national_nonfood | vegfruit | 蔬菜水果 | 6.274 | 5.73 | 6.995 | 1000 |
| robust_real_derived_cpi_nonfood | dairyegg | 奶蛋类 | 6.21 | 5.432 | 6.931 | 999 |
| robust_real_derived_cpi_nonfood | grain | 粮食/主粮 | 6.21 | 5.432 | 6.931 | 999 |
| robust_real_derived_cpi_nonfood | nonfood | 其他/未覆盖支出 | 6.21 | 5.432 | 6.931 | 999 |
| robust_real_derived_cpi_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 6.21 | 5.432 | 6.931 | 999 |
| robust_real_derived_cpi_nonfood | oil | 食用油 | 6.21 | 5.432 | 6.931 | 999 |
| robust_real_derived_cpi_nonfood | pork | 猪肉 | 6.21 | 5.432 | 6.931 | 999 |
| robust_real_derived_cpi_nonfood | vegfruit | 蔬菜水果 | 6.21 | 5.432 | 6.931 | 999 |

## 十、输出文件索引

- `bootstrap_draw_status.csv`：bootstrap 每个 draw 的收敛状态。
- `bootstrap_metric_draws.csv` / `bootstrap_metric_ci.csv`：弹性、预算份额和预测数量的 bootstrap 明细与区间。
- `bootstrap_parameter_draws.csv` / `bootstrap_parameter_ci.csv`：参数 bootstrap 明细与区间。
- `lr_bootstrap_draws.csv` / `lr_test_chi2_and_bootstrap.csv`：LR cluster bootstrap 明细与摘要。
- `oos_fit_by_group.csv` / `oos_summary_by_model.csv` / `oos_paired_bootstrap_model_comparison.csv`：样本外验证。
- `elasticity_at_mean_pgdp_summary.csv`：平均人均 GDP 点估计弹性。

## 十一、解释提醒

- 本设定模仿 Gouel-Guimbard 原文的人均 GDP 预算尺度。
- 在省级 household demand 解释中，`nonfood` residual 是 `人均 GDP - 已覆盖食品支出`，不是严格居民非食品消费。
- LR 普通 chi-square p 值不使用；表中仅报告 province-block cluster bootstrap tail probability。