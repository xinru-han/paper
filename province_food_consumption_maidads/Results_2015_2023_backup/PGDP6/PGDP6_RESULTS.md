# 原始 6 类 MAIDADS/AIDADS：人均 GDP 预算口径敏感性结果

- 生成时间：2026-06-11T23:22:55
- 开始时间：2026-06-11T23:15:38
- 本轮不做 bootstrap。
- 分类：`grain / oil / vegfruit / meatsea / dairyegg / nonfood`，与最早 6 类主模型一致。
- 本轮把模型预算变量 `m` 从实际人均消费支出改为实际人均 GDP：`m = pgdp / monetary_deflator`。
- 注意：此设定模仿 Gouel-Guimbard 原文的人均 GDP 预算尺度；但省级 household demand 解释应谨慎，因为 `nonfood` residual 变成 `人均 GDP - covered food expenditure`。

## 模型品类

| group | label_cn | items |
| --- | --- | --- |
| grain | 粮食/主粮 | grain |
| oil | 食用油 | oil |
| vegfruit | 蔬菜水果 | vegetable+fruit |
| meatsea | 肉类及水产品 | pork+beef+mutton+poultry+aquatic |
| dairyegg | 奶蛋类 | milk+egg |
| nonfood | 其他/未覆盖支出 |  |

## baseline_real_national_nonfood

### m 口径描述

| index | count | mean | std | min | 5% | 25% | 50% | 75% | 95% | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| m | 279 | 66734.1 | 30063.9 | 29310.6 | 37641.7 | 46517 | 56761.9 | 77869.5 | 136989 | 175921 |
| m_consumption_real | 279 | 20418.1 | 7130.35 | 9341.54 | 13533.9 | 15906.5 | 17951.5 | 22009.8 | 39278 | 45408.3 |
| pgdp_nominal | 279 | 63149.8 | 29186.4 | 25946 | 33585.9 | 43814.4 | 53360.3 | 73339.7 | 127302 | 175921 |
| covered_food_exp | 279 | 2392.92 | 397.998 | 1597.62 | 1826.94 | 2088.72 | 2383.14 | 2658.33 | 3081.52 | 3940.11 |
| nonfood_exp | 279 | 64341.2 | 30026.4 | 26870.4 | 34927.8 | 44493.5 | 54414.1 | 74976.6 | 134817 | 173957 |

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | -3119 | 13 | -6212 | -6165 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2425 |  |  |
| baseline_real_national_nonfood | MAIDADS_sat | -3172 | 20 | -6304 | -6231 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2388 |  |  |
| baseline_real_national_nonfood | LR_MAIDADS_vs_AIDADS |  | 7 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 105.5 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | meatsea | 肉类及水产品 | pork+beef+mutton+poultry+aquatic | 0.04503 | 0.03512 | 0.1441 | 0.3124 |
| baseline_real_national_nonfood | AIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008262 | 0.006823 | 0.02962 | 0.2789 |
| baseline_real_national_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.0315 | 0.02574 | 0.128 | 0.2461 |
| baseline_real_national_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07844 | 0.05473 | 0.4162 | 0.1885 |
| baseline_real_national_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009566 | 0.007168 | 0.05127 | 0.1866 |
| baseline_real_national_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.64 | 2.927 | 673.7 | 0.005403 |
| baseline_real_national_nonfood | MAIDADS_sat | meatsea | 肉类及水产品 | pork+beef+mutton+poultry+aquatic | 0.04429 | 0.03461 | 0.1441 | 0.3073 |
| baseline_real_national_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008507 | 0.006998 | 0.02962 | 0.2872 |
| baseline_real_national_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03121 | 0.02566 | 0.128 | 0.2438 |
| baseline_real_national_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009538 | 0.007305 | 0.05127 | 0.186 |
| baseline_real_national_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.07052 | 0.04911 | 0.4162 | 0.1694 |
| baseline_real_national_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.489 | 2.791 | 673.7 | 0.005179 |

### 异常检查

- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：grain, oil。
- 出现正的 Marshallian 自价格弹性：grain, oil。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 4.59701e-10 |
| max_abs_price_adding_up_error | 8.01472e-11 |
| max_abs_marshallian_homogeneity_error | 1.32448e-09 |
| max_abs_hicksian_homogeneity_error | 1.32448e-09 |
| max_abs_slutsky_symmetry_error | 8.33759e-11 |

### 收入弹性：income=30000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.1797 | 0.0139 | in_support |
| oil | 食用油 | -0.09523 | 0.02416 | in_support |
| vegfruit | 蔬菜水果 | 0.2424 | 0.01236 | in_support |
| meatsea | 肉类及水产品 | 0.3659 | 0.01894 | in_support |
| dairyegg | 奶蛋类 | 0.6313 | 0.00209 | in_support |
| nonfood | 其他/未覆盖支出 | 1.07 | 0.9286 | in_support |

### Marshallian 自价格弹性：income=30000

| demand_group | demand_group_label_cn | elasticity | support_flag |
| --- | --- | --- | --- |
| grain | 粮食/主粮 | 0.00249 | in_support |
| oil | 食用油 | 0.002295 | in_support |
| vegfruit | 蔬菜水果 | -0.1721 | in_support |
| meatsea | 肉类及水产品 | -0.588 | in_support |
| dairyegg | 奶蛋类 | -0.4707 | in_support |
| nonfood | 其他/未覆盖支出 | -1.009 | in_support |

### 收入弹性：income=50000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.2163 | 0.007536 | in_support |
| oil | 食用油 | -0.1092 | 0.01376 | in_support |
| vegfruit | 蔬菜水果 | 0.2409 | 0.008402 | in_support |
| meatsea | 肉类及水产品 | 0.3565 | 0.0137 | in_support |
| dairyegg | 奶蛋类 | 0.5292 | 0.001687 | in_support |
| nonfood | 其他/未覆盖支出 | 1.042 | 0.9549 | in_support |

### Marshallian 自价格弹性：income=50000

| demand_group | demand_group_label_cn | elasticity | support_flag |
| --- | --- | --- | --- |
| grain | 粮食/主粮 | 0.001619 | in_support |
| oil | 食用油 | 0.001494 | in_support |
| vegfruit | 蔬菜水果 | -0.2174 | in_support |
| meatsea | 肉类及水产品 | -0.7014 | in_support |
| dairyegg | 奶蛋类 | -0.5041 | in_support |
| nonfood | 其他/未覆盖支出 | -1.008 | in_support |

### 收入弹性：income=80000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.2461 | 0.004224 | in_support |
| oil | 食用油 | -0.1175 | 0.00815 | in_support |
| vegfruit | 蔬菜水果 | 0.2185 | 0.005854 | in_support |
| meatsea | 肉类及水产品 | 0.3048 | 0.01001 | in_support |
| dairyegg | 奶蛋类 | 0.427 | 0.00132 | in_support |
| nonfood | 其他/未覆盖支出 | 1.027 | 0.9704 | in_support |

### Marshallian 自价格弹性：income=80000

| demand_group | demand_group_label_cn | elasticity | support_flag |
| --- | --- | --- | --- |
| grain | 粮食/主粮 | 0.001023 | in_support |
| oil | 食用油 | 0.0009466 | in_support |
| vegfruit | 蔬菜水果 | -0.2533 | in_support |
| meatsea | 肉类及水产品 | -0.7809 | in_support |
| dairyegg | 奶蛋类 | -0.5244 | in_support |
| nonfood | 其他/未覆盖支出 | -1.007 | in_support |

## robust_real_derived_cpi_nonfood

### m 口径描述

| index | count | mean | std | min | 5% | 25% | 50% | 75% | 95% | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| m | 279 | 66734.1 | 30063.9 | 29310.6 | 37641.7 | 46517 | 56761.9 | 77869.5 | 136989 | 175921 |
| m_consumption_real | 279 | 20418.1 | 7130.35 | 9341.54 | 13533.9 | 15906.5 | 17951.5 | 22009.8 | 39278 | 45408.3 |
| pgdp_nominal | 279 | 63149.8 | 29186.4 | 25946 | 33585.9 | 43814.4 | 53360.3 | 73339.7 | 127302 | 175921 |
| covered_food_exp | 279 | 2392.92 | 397.998 | 1597.62 | 1826.94 | 2088.72 | 2383.14 | 2658.33 | 3081.52 | 3940.11 |
| nonfood_exp | 279 | 64341.2 | 30026.4 | 26870.4 | 34927.8 | 44493.5 | 54414.1 | 74976.6 | 134817 | 173957 |

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | -3128 | 13 | -6230 | -6183 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2423 |  |  |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | -3184 | 20 | -6328 | -6255 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2378 |  |  |
| robust_real_derived_cpi_nonfood | LR_MAIDADS_vs_AIDADS |  | 7 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 111.2 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | meatsea | 肉类及水产品 | pork+beef+mutton+poultry+aquatic | 0.04491 | 0.03493 | 0.1441 | 0.3116 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008265 | 0.006832 | 0.02962 | 0.279 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03152 | 0.02569 | 0.128 | 0.2462 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07846 | 0.05468 | 0.4162 | 0.1885 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009548 | 0.007171 | 0.05127 | 0.1862 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.606 | 2.899 | 668.5 | 0.005394 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | meatsea | 肉类及水产品 | pork+beef+mutton+poultry+aquatic | 0.04415 | 0.03452 | 0.1441 | 0.3063 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008409 | 0.006937 | 0.02962 | 0.2839 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03121 | 0.02558 | 0.128 | 0.2438 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009537 | 0.007309 | 0.05127 | 0.186 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.07032 | 0.04842 | 0.4162 | 0.169 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.46 | 2.776 | 668.5 | 0.005176 |

### 异常检查

- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：dairyegg, meatsea, oil。
- 出现正的 Marshallian 自价格弹性：oil。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 4.52935e-10 |
| max_abs_price_adding_up_error | 7.93378e-11 |
| max_abs_marshallian_homogeneity_error | 1.27784e-09 |
| max_abs_hicksian_homogeneity_error | 1.27784e-09 |
| max_abs_slutsky_symmetry_error | 8.27727e-11 |

### 收入弹性：income=30000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.1699 | 0.01387 | in_support |
| oil | 食用油 | -0.09503 | 0.02401 | in_support |
| vegfruit | 蔬菜水果 | 0.2451 | 0.01235 | in_support |
| meatsea | 肉类及水产品 | 0.3603 | 0.01893 | in_support |
| dairyegg | 奶蛋类 | 0.6518 | 0.002077 | in_support |
| nonfood | 其他/未覆盖支出 | 1.07 | 0.9288 | in_support |

### Marshallian 自价格弹性：income=30000

| demand_group | demand_group_label_cn | elasticity | support_flag |
| --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.06869 | in_support |
| oil | 食用油 | 0.002166 | in_support |
| vegfruit | 蔬菜水果 | -0.1739 | in_support |
| meatsea | 肉类及水产品 | -0.5879 | in_support |
| dairyegg | 奶蛋类 | -0.54 | in_support |
| nonfood | 其他/未覆盖支出 | -1.01 | in_support |

### 收入弹性：income=50000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.1978 | 0.007577 | in_support |
| oil | 食用油 | -0.1084 | 0.01368 | in_support |
| vegfruit | 蔬菜水果 | 0.2423 | 0.008398 | in_support |
| meatsea | 肉类及水产品 | 0.3514 | 0.01366 | in_support |
| dairyegg | 奶蛋类 | 0.5418 | 0.001691 | in_support |
| nonfood | 其他/未覆盖支出 | 1.042 | 0.955 | in_support |

### Marshallian 自价格弹性：income=50000

| demand_group | demand_group_label_cn | elasticity | support_flag |
| --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.1105 | in_support |
| oil | 食用油 | 0.001306 | in_support |
| vegfruit | 蔬菜水果 | -0.2184 | in_support |
| meatsea | 肉类及水产品 | -0.6997 | in_support |
| dairyegg | 奶蛋类 | -0.5706 | in_support |
| nonfood | 其他/未覆盖支出 | -1.009 | in_support |

### 收入弹性：income=80000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.224 | 0.004288 | in_support |
| oil | 食用油 | -0.1165 | 0.008107 | in_support |
| vegfruit | 蔬菜水果 | 0.2191 | 0.005854 | in_support |
| meatsea | 肉类及水产品 | 0.2996 | 0.00996 | in_support |
| dairyegg | 奶蛋类 | 0.4335 | 0.001329 | in_support |
| nonfood | 其他/未覆盖支出 | 1.027 | 0.9705 | in_support |

### Marshallian 自价格弹性：income=80000

| demand_group | demand_group_label_cn | elasticity | support_flag |
| --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.1597 | in_support |
| oil | 食用油 | 0.000703 | in_support |
| vegfruit | 蔬菜水果 | -0.2534 | in_support |
| meatsea | 肉类及水产品 | -0.7781 | in_support |
| dairyegg | 奶蛋类 | -0.5891 | in_support |
| nonfood | 其他/未覆盖支出 | -1.008 | in_support |

## 输出文件

- `*__pgdp6_panel.csv`：人均 GDP 预算口径估计面板。
- `*__parameter_estimates.csv`：AIDADS/MAIDADS 参数。
- `*__fit_by_group.csv`：分品类拟合误差。
- `*__model_comparison.csv`：AIC/BIC/LR 摘要；LR 不报告普通 chi-square p 值。
- `*__elasticity_income_grid.csv`：人均 GDP 网格下的收入/GDP 弹性。
- `*__elasticity_price_marshallian_grid.csv`、`*__elasticity_price_hicksian_grid.csv`：价格弹性。
- `*__elasticity_consistency_tests.csv`：加总、齐次性和 Slutsky 对称性检查。