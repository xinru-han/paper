# 人均 GDP + 猪肉拆分 MAIDADS 完整结果整合

- 生成时间：2026-06-12T21:23:47.074842
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
| m | 279 | 66734.1 | 30063.9 | 29310.6 | 37641.7 | 46517 | 56761.9 | 77869.5 | 136989 | 175921 |
| m_consumption_real | 279 | 20418.1 | 7130.35 | 9341.54 | 13533.9 | 15906.5 | 17951.5 | 22009.8 | 39278 | 45408.3 |
| pgdp_nominal | 279 | 63149.8 | 29186.4 | 25946 | 33585.9 | 43814.4 | 53360.3 | 73339.7 | 127302 | 175921 |
| covered_food_exp_split | 279 | 2392.92 | 397.998 | 1597.62 | 1826.94 | 2088.72 | 2383.14 | 2658.33 | 3081.52 | 3940.11 |
| nonfood_exp_split | 279 | 64341.2 | 30026.4 | 26870.4 | 34927.8 | 44493.5 | 54414.1 | 74976.6 | 134817 | 173957 |

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | -3923 | 15 | -7816 | -7762 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2913 |  |  |
| baseline_real_national_nonfood | MAIDADS_sat | -3999 | 23 | -7953 | -7869 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2813 |  |  |
| baseline_real_national_nonfood | LR_MAIDADS_vs_AIDADS |  | 8 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 152.7 | invalid_not_reported_unidentified_nuisance_under_H0 |

### MAIDADS 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.0423 | 0.03403 | 0.1037 | 0.4079 |
| baseline_real_national_nonfood | MAIDADS_sat | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic | 0.01605 | 0.01229 | 0.04043 | 0.397 |
| baseline_real_national_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008409 | 0.006931 | 0.02962 | 0.2839 |
| baseline_real_national_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03123 | 0.02568 | 0.128 | 0.244 |
| baseline_real_national_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009494 | 0.007233 | 0.05127 | 0.1852 |
| baseline_real_national_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.07059 | 0.04898 | 0.4162 | 0.1696 |
| baseline_real_national_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.612 | 2.908 | 673.7 | 0.005361 |

### 理论一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 1.65058e-09 |
| max_abs_price_adding_up_error | 2.61239e-10 |
| max_abs_marshallian_homogeneity_error | 2.76529e-09 |
| max_abs_hicksian_homogeneity_error | 2.76529e-09 |
| max_abs_slutsky_symmetry_error | 3.66018e-10 |

## 二、点估计与诊断：robust_real_derived_cpi_nonfood

### m 口径描述

| index | count | mean | std | min | 5% | 25% | 50% | 75% | 95% | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| m | 279 | 66734.1 | 30063.9 | 29310.6 | 37641.7 | 46517 | 56761.9 | 77869.5 | 136989 | 175921 |
| m_consumption_real | 279 | 20418.1 | 7130.35 | 9341.54 | 13533.9 | 15906.5 | 17951.5 | 22009.8 | 39278 | 45408.3 |
| pgdp_nominal | 279 | 63149.8 | 29186.4 | 25946 | 33585.9 | 43814.4 | 53360.3 | 73339.7 | 127302 | 175921 |
| covered_food_exp_split | 279 | 2392.92 | 397.998 | 1597.62 | 1826.94 | 2088.72 | 2383.14 | 2658.33 | 3081.52 | 3940.11 |
| nonfood_exp_split | 279 | 64341.2 | 30026.4 | 26870.4 | 34927.8 | 44493.5 | 54414.1 | 74976.6 | 134817 | 173957 |

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | -3848 | 15 | -7666 | -7612 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3006 |  |  |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | -4013 | 23 | -7980 | -7896 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2805 |  |  |
| robust_real_derived_cpi_nonfood | LR_MAIDADS_vs_AIDADS |  | 8 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 329.6 | invalid_not_reported_unidentified_nuisance_under_H0 |

### MAIDADS 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04212 | 0.03387 | 0.1037 | 0.4061 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic | 0.01604 | 0.01225 | 0.04043 | 0.3967 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008342 | 0.006911 | 0.02962 | 0.2816 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03124 | 0.02558 | 0.128 | 0.2441 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009492 | 0.007239 | 0.05127 | 0.1851 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.07044 | 0.04836 | 0.4162 | 0.1692 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.577 | 2.885 | 668.5 | 0.005352 |

### 理论一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 1.69253e-09 |
| max_abs_price_adding_up_error | 2.62629e-10 |
| max_abs_marshallian_homogeneity_error | 1.5164e-08 |
| max_abs_hicksian_homogeneity_error | 1.5164e-08 |
| max_abs_slutsky_symmetry_error | 3.73614e-10 |

## 三、平均人均 GDP 水平弹性

| variant | group | group_label_cn | gdp_elasticity | marshallian_own_price | hicksian_own_price | budget_share |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | grain | 粮食/主粮 | -0.2388 | 0.001234 | -2.17e-05 | 0.005261 |
| baseline_real_national_nonfood | oil | 食用油 | -0.1092 | 0.001079 | -1.129e-05 | 0.009984 |
| baseline_real_national_nonfood | vegfruit | 蔬菜水果 | 0.2162 | -0.2649 | -0.2635 | 0.006775 |
| baseline_real_national_nonfood | pork | 猪肉 | 0.2506 | -0.735 | -0.7339 | 0.004672 |
| baseline_real_national_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.3842 | -0.002511 | -2.237e-05 | 0.006478 |
| baseline_real_national_nonfood | dairyegg | 奶蛋类 | 0.4405 | -0.5799 | -0.5793 | 0.001461 |
| baseline_real_national_nonfood | nonfood | 其他/未覆盖支出 | 1.032 | -1.003 | -0.006255 | 0.9654 |
| robust_real_derived_cpi_nonfood | grain | 粮食/主粮 | -0.2209 | -0.1285 | -0.1297 | 0.005305 |
| robust_real_derived_cpi_nonfood | oil | 食用油 | -0.1096 | 0.000953 | -0.0001329 | 0.009911 |
| robust_real_derived_cpi_nonfood | vegfruit | 蔬菜水果 | 0.2191 | -0.2601 | -0.2586 | 0.006772 |
| robust_real_derived_cpi_nonfood | pork | 猪肉 | 0.2499 | -0.7332 | -0.732 | 0.004656 |
| robust_real_derived_cpi_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.3747 | -0.00263 | -0.0002035 | 0.006476 |
| robust_real_derived_cpi_nonfood | dairyegg | 奶蛋类 | 0.4505 | -0.6351 | -0.6345 | 0.00147 |
| robust_real_derived_cpi_nonfood | nonfood | 其他/未覆盖支出 | 1.032 | -1.004 | -0.006993 | 0.9654 |

## 四、平均人均 GDP 水平弹性 bootstrap 区间

### gdp_elasticity

| variant | group | group_label_cn | median | ci_2_5 | ci_97_5 | n_success_draws |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | dairyegg | 奶蛋类 | 0.4445 | 0.3282 | 0.5675 | 1000 |
| baseline_real_national_nonfood | grain | 粮食/主粮 | -0.2273 | -0.3403 | -0.06467 | 1000 |
| baseline_real_national_nonfood | nonfood | 其他/未覆盖支出 | 1.032 | 1.028 | 1.036 | 1000 |
| baseline_real_national_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.4104 | 0.2525 | 0.7003 | 1000 |
| baseline_real_national_nonfood | oil | 食用油 | -0.1137 | -0.2705 | 0.1192 | 1000 |
| baseline_real_national_nonfood | pork | 猪肉 | 0.2341 | 0.09037 | 0.3979 | 1000 |
| baseline_real_national_nonfood | vegfruit | 蔬菜水果 | 0.2132 | 0.1081 | 0.3494 | 1000 |
| robust_real_derived_cpi_nonfood | dairyegg | 奶蛋类 | 0.4695 | 0.3514 | 0.6339 | 999 |
| robust_real_derived_cpi_nonfood | grain | 粮食/主粮 | -0.2173 | -0.3442 | -0.06171 | 999 |
| robust_real_derived_cpi_nonfood | nonfood | 其他/未覆盖支出 | 1.032 | 1.028 | 1.036 | 999 |
| robust_real_derived_cpi_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.3743 | 0.1055 | 0.6901 | 999 |
| robust_real_derived_cpi_nonfood | oil | 食用油 | -0.1192 | -0.2853 | 0.106 | 999 |
| robust_real_derived_cpi_nonfood | pork | 猪肉 | 0.2337 | 0.08524 | 0.4137 | 999 |
| robust_real_derived_cpi_nonfood | vegfruit | 蔬菜水果 | 0.2227 | 0.1112 | 0.377 | 999 |

### marshallian_own_price

| variant | group | group_label_cn | median | ci_2_5 | ci_97_5 | n_success_draws |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | dairyegg | 奶蛋类 | -0.5951 | -0.8677 | -0.3229 | 1000 |
| baseline_real_national_nonfood | grain | 粮食/主粮 | -0.1037 | -0.2485 | 0.001593 | 1000 |
| baseline_real_national_nonfood | nonfood | 其他/未覆盖支出 | -1.003 | -1.008 | -0.9995 | 1000 |
| baseline_real_national_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | -0.01745 | -0.5454 | -0.001926 | 1000 |
| baseline_real_national_nonfood | oil | 食用油 | -0.00792 | -0.145 | 0.002206 | 1000 |
| baseline_real_national_nonfood | pork | 猪肉 | -0.7498 | -0.9358 | -0.5763 | 1000 |
| baseline_real_national_nonfood | vegfruit | 蔬菜水果 | -0.2372 | -0.3725 | -0.09904 | 1000 |
| robust_real_derived_cpi_nonfood | dairyegg | 奶蛋类 | -0.5923 | -0.8779 | -0.3042 | 999 |
| robust_real_derived_cpi_nonfood | grain | 粮食/主粮 | -0.1282 | -0.2912 | 0.001322 | 999 |
| robust_real_derived_cpi_nonfood | nonfood | 其他/未覆盖支出 | -1.004 | -1.008 | -0.9998 | 999 |
| robust_real_derived_cpi_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | -0.01082 | -0.5439 | -0.001515 | 999 |
| robust_real_derived_cpi_nonfood | oil | 食用油 | -0.004054 | -0.1645 | 0.002276 | 999 |
| robust_real_derived_cpi_nonfood | pork | 猪肉 | -0.7409 | -0.9504 | -0.5473 | 999 |
| robust_real_derived_cpi_nonfood | vegfruit | 蔬菜水果 | -0.2363 | -0.3706 | -0.08864 | 999 |

### hicksian_own_price

| variant | group | group_label_cn | median | ci_2_5 | ci_97_5 | n_success_draws |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | dairyegg | 奶蛋类 | -0.5944 | -0.8672 | -0.3222 | 1000 |
| baseline_real_national_nonfood | grain | 粮食/主粮 | -0.1046 | -0.2496 | -1.181e-05 | 1000 |
| baseline_real_national_nonfood | nonfood | 其他/未覆盖支出 | -0.007036 | -0.01114 | -0.004438 | 1000 |
| baseline_real_national_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | -0.01481 | -0.5424 | -6.792e-06 | 1000 |
| baseline_real_national_nonfood | oil | 食用油 | -0.00885 | -0.1463 | -4.484e-06 | 1000 |
| baseline_real_national_nonfood | pork | 猪肉 | -0.7488 | -0.9343 | -0.5754 | 1000 |
| baseline_real_national_nonfood | vegfruit | 蔬菜水果 | -0.2356 | -0.3709 | -0.09767 | 1000 |
| robust_real_derived_cpi_nonfood | dairyegg | 奶蛋类 | -0.5915 | -0.8772 | -0.3035 | 999 |
| robust_real_derived_cpi_nonfood | grain | 粮食/主粮 | -0.1289 | -0.2925 | -7.505e-05 | 999 |
| robust_real_derived_cpi_nonfood | nonfood | 其他/未覆盖支出 | -0.007075 | -0.01097 | -0.004355 | 999 |
| robust_real_derived_cpi_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | -0.00846 | -0.541 | -1.392e-05 | 999 |
| robust_real_derived_cpi_nonfood | oil | 食用油 | -0.005029 | -0.1656 | -8.887e-06 | 999 |
| robust_real_derived_cpi_nonfood | pork | 猪肉 | -0.7401 | -0.9488 | -0.5466 | 999 |
| robust_real_derived_cpi_nonfood | vegfruit | 蔬菜水果 | -0.2348 | -0.3694 | -0.08677 | 999 |

### budget_share

| variant | group | group_label_cn | median | ci_2_5 | ci_97_5 | n_success_draws |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | dairyegg | 奶蛋类 | 0.001467 | 0.001312 | 0.001616 | 1000 |
| baseline_real_national_nonfood | grain | 粮食/主粮 | 0.005292 | 0.005048 | 0.005545 | 1000 |
| baseline_real_national_nonfood | nonfood | 其他/未覆盖支出 | 0.9653 | 0.9637 | 0.967 | 1000 |
| baseline_real_national_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.006459 | 0.005732 | 0.007341 | 1000 |
| baseline_real_national_nonfood | oil | 食用油 | 0.009949 | 0.009161 | 0.01079 | 1000 |
| baseline_real_national_nonfood | pork | 猪肉 | 0.004675 | 0.004026 | 0.005393 | 1000 |
| baseline_real_national_nonfood | vegfruit | 蔬菜水果 | 0.006775 | 0.0063 | 0.007201 | 1000 |
| robust_real_derived_cpi_nonfood | dairyegg | 奶蛋类 | 0.001471 | 0.001312 | 0.001623 | 999 |
| robust_real_derived_cpi_nonfood | grain | 粮食/主粮 | 0.005278 | 0.005048 | 0.005534 | 999 |
| robust_real_derived_cpi_nonfood | nonfood | 其他/未覆盖支出 | 0.9654 | 0.9638 | 0.9671 | 999 |
| robust_real_derived_cpi_nonfood | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.006472 | 0.005747 | 0.00734 | 999 |
| robust_real_derived_cpi_nonfood | oil | 食用油 | 0.009902 | 0.009158 | 0.01074 | 999 |
| robust_real_derived_cpi_nonfood | pork | 猪肉 | 0.004645 | 0.004003 | 0.005406 | 999 |
| robust_real_derived_cpi_nonfood | vegfruit | 蔬菜水果 | 0.006782 | 0.006308 | 0.00721 | 999 |

## 五、Bootstrap 收敛状态

| variant | target_reps | completed_reps | successful_reps | convergence_rate |
| --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | 1000 | 1000 | 1000 | 1 |
| robust_real_derived_cpi_nonfood | 1000 | 1000 | 999 | 0.999 |

## 六、LR Cluster Bootstrap

| variant | test | observed_lr | bootstrap_reps | completed_reps | successful_reps | convergence_rate | cluster_bootstrap_tail_probability | lr_bootstrap_median | lr_bootstrap_q95 | lr_bootstrap_q99 | chi2_p_value_status | note | inference_scale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | MAIDADS_vs_AIDADS | 152.7 | 500 | 500 | 498 | 0.996 | 0.6265 | 181.5 | 434.3 | 544 | invalid_not_reported | Province-block cluster bootstrap; ordinary chi-square p-value not used. | formal |
| robust_real_derived_cpi_nonfood | MAIDADS_vs_AIDADS | 329.6 | 500 | 500 | 498 | 0.996 | 0.1546 | 190.8 | 425.7 | 519.4 | invalid_not_reported | Province-block cluster bootstrap; ordinary chi-square p-value not used. | formal |

## 七、样本外验证

| variant | model | train_years | test_years | oos_food_rmse_mean | oos_food_relative_rmse_mean | oos_food_mae_mean |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | 0.03349 | 0.3077 | 0.02721 |
| baseline_real_national_nonfood | AIDADS_sat | 2015-2022 | 2023 | 0.03294 | 0.2961 | 0.02682 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | 0.02977 | 0.2758 | 0.02436 |
| baseline_real_national_nonfood | MAIDADS_sat | 2015-2022 | 2023 | 0.03092 | 0.2743 | 0.02526 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2020 | 2021-2023 | 0.03349 | 0.3125 | 0.02724 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | 2015-2022 | 2023 | 0.03253 | 0.2846 | 0.02663 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2020 | 2021-2023 | 0.03143 | 0.3007 | 0.02595 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | 2015-2022 | 2023 | 0.03075 | 0.2745 | 0.02494 |

## 八、OOS 配对 Bootstrap：AIDADS vs MAIDADS

| variant | train_years | test_years | comparison | observed_mean_diff | ci_2_5 | median | ci_97_5 | p_share_diff_le_0 | bootstrap_reps | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | 2015-2020 | 2021-2023 | AIDADS_MSE_minus_MAIDADS_MSE | 0.0003687 | 9.236e-05 | 0.0003582 | 0.0007205 | 0.004 | 1000 | Positive observed_mean_diff means MAIDADS has lower food MSE than AIDADS. |
| baseline_real_national_nonfood | 2015-2022 | 2023 | AIDADS_MSE_minus_MAIDADS_MSE | 0.0001645 | -0.0001019 | 0.0001529 | 0.0005304 | 0.138 | 1000 | Positive observed_mean_diff means MAIDADS has lower food MSE than AIDADS. |
| robust_real_derived_cpi_nonfood | 2015-2020 | 2021-2023 | AIDADS_MSE_minus_MAIDADS_MSE | 0.0002355 | -3.943e-05 | 0.0002234 | 0.0005871 | 0.056 | 1000 | Positive observed_mean_diff means MAIDADS has lower food MSE than AIDADS. |
| robust_real_derived_cpi_nonfood | 2015-2022 | 2023 | AIDADS_MSE_minus_MAIDADS_MSE | 0.0001963 | -6.189e-05 | 0.0001864 | 0.0005439 | 0.107 | 1000 | Positive observed_mean_diff means MAIDADS has lower food MSE than AIDADS. |

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