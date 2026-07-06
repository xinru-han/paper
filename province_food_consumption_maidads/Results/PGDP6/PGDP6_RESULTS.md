# 原始 6 类 MAIDADS/AIDADS：人均 GDP 预算口径敏感性结果

- 生成时间：2026-07-06T00:59:07
- 开始时间：2026-07-06T00:11:24
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
| pork | 猪肉 | pork |
| meatother | 非猪肉肉类及水产品 | beef+mutton+poultry+aquatic |
| dairyegg | 奶蛋类 | milk+egg |
| nonfood | 其他/未覆盖支出 |  |

## baseline_real_national_nonfood

### m 口径描述

| index | count | mean | std | min | 5% | 25% | 50% | 75% | 95% | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| m | 310 | 68076 | 30754.4 | 29310.6 | 37877.4 | 47585.4 | 58111.2 | 78846.2 | 138569 | 184841 |
| m_consumption_real | 310 | 20783.7 | 7227.42 | 9341.54 | 13675.1 | 16193 | 18427 | 22607 | 39547.7 | 45592.9 |
| pgdp_nominal | 310 | 64865.5 | 30158.3 | 25946 | 33853.7 | 44453.9 | 56007.7 | 76658.9 | 130231 | 185026 |
| covered_food_exp | 310 | 2384.22 | 395.434 | 1597.62 | 1827.6 | 2077.46 | 2372.28 | 2652.87 | 3061.65 | 3940.11 |
| nonfood_exp | 310 | 65691.8 | 30721.1 | 26870.4 | 35830.7 | 45037.2 | 55797.2 | 76556 | 136351 | 183003 |

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | -4341 | 15 | -8651 | -8595 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2902 |  |  |
| baseline_real_national_nonfood | MAIDADS_sat | -4428 | 23 | -8810 | -8724 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2801 |  |  |
| baseline_real_national_nonfood | LR_MAIDADS_vs_AIDADS |  | 8 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 174.8 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | meatother | 非猪肉肉类及水产品 | beef+mutton+poultry+aquatic | 0.01765 | 0.01406 | 0.04128 | 0.4275 |
| baseline_real_national_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.04407 | 0.03577 | 0.1059 | 0.4161 |
| baseline_real_national_nonfood | AIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008388 | 0.006997 | 0.03001 | 0.2795 |
| baseline_real_national_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03135 | 0.02553 | 0.1273 | 0.2462 |
| baseline_real_national_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07746 | 0.05393 | 0.4123 | 0.1879 |
| baseline_real_national_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.00951 | 0.007249 | 0.05165 | 0.1841 |
| baseline_real_national_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.595 | 2.914 | 683.8 | 0.005258 |
| baseline_real_national_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04334 | 0.0349 | 0.1059 | 0.4092 |
| baseline_real_national_nonfood | MAIDADS_sat | meatother | 非猪肉肉类及水产品 | beef+mutton+poultry+aquatic | 0.01623 | 0.01243 | 0.04128 | 0.3932 |
| baseline_real_national_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008487 | 0.007023 | 0.03001 | 0.2828 |
| baseline_real_national_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03104 | 0.02548 | 0.1273 | 0.2438 |
| baseline_real_national_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009461 | 0.007222 | 0.05165 | 0.1832 |
| baseline_real_national_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.06952 | 0.04871 | 0.4123 | 0.1686 |
| baseline_real_national_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.588 | 2.901 | 683.8 | 0.005246 |

### 异常检查

- 选中解梯度范数偏大：max grad_norm=1.573。
- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：dairyegg, meatother, oil。
- 出现正的 Marshallian 自价格弹性：oil。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 4.2977e-10 |
| max_abs_price_adding_up_error | 8.0356e-11 |
| max_abs_marshallian_homogeneity_error | 4.23855e-09 |
| max_abs_hicksian_homogeneity_error | 4.23855e-09 |
| max_abs_slutsky_symmetry_error | 8.43635e-11 |

### 收入弹性：income=30000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.2121 | 0.014 | in_support |
| oil | 食用油 | -0.1133 | 0.02417 | in_support |
| vegfruit | 蔬菜水果 | 0.2874 | 0.01235 | in_support |
| pork | 猪肉 | 0.3326 | 0.008034 | in_support |
| meatother | 非猪肉肉类及水产品 | 0.6761 | 0.009568 | in_support |
| dairyegg | 奶蛋类 | 0.7485 | 0.002064 | in_support |
| nonfood | 其他/未覆盖支出 | 1.066 | 0.9298 | in_support |

### Marshallian 自价格弹性：income=30000

| demand_group | demand_group_label_cn | elasticity | support_flag |
| --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.03379 | in_support |
| oil | 食用油 | 0.002725 | in_support |
| vegfruit | 蔬菜水果 | -0.2 | in_support |
| pork | 猪肉 | -0.5278 | in_support |
| meatother | 非猪肉肉类及水产品 | -0.006503 | in_support |
| dairyegg | 奶蛋类 | -0.5938 | in_support |
| nonfood | 其他/未覆盖支出 | -1 | in_support |

### 收入弹性：income=50000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.2334 | 0.007492 | in_support |
| oil | 食用油 | -0.1177 | 0.01367 | in_support |
| vegfruit | 蔬菜水果 | 0.2432 | 0.00849 | in_support |
| pork | 猪肉 | 0.2724 | 0.005632 | in_support |
| meatother | 非猪肉肉类及水产品 | 0.4925 | 0.007717 | in_support |
| dairyegg | 奶蛋类 | 0.525 | 0.001709 | in_support |
| nonfood | 其他/未覆盖支出 | 1.042 | 0.9553 | in_support |

### Marshallian 自价格弹性：income=50000

| demand_group | demand_group_label_cn | elasticity | support_flag |
| --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.05602 | in_support |
| oil | 食用油 | 0.001589 | in_support |
| vegfruit | 蔬菜水果 | -0.2424 | in_support |
| pork | 猪肉 | -0.6322 | in_support |
| meatother | 非猪肉肉类及水产品 | -0.003835 | in_support |
| dairyegg | 奶蛋类 | -0.6027 | in_support |
| nonfood | 其他/未覆盖支出 | -1.002 | in_support |

### 收入弹性：income=80000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.2389 | 0.004188 | in_support |
| oil | 食用油 | -0.1129 | 0.00809 | in_support |
| vegfruit | 蔬菜水果 | 0.1931 | 0.00588 | in_support |
| pork | 猪肉 | 0.205 | 0.003938 | in_support |
| meatother | 非猪肉肉类及水产品 | 0.3662 | 0.005894 | in_support |
| dairyegg | 奶蛋类 | 0.3729 | 0.001317 | in_support |
| nonfood | 其他/未覆盖支出 | 1.027 | 0.9707 | in_support |

### Marshallian 自价格弹性：income=80000

| demand_group | demand_group_label_cn | elasticity | support_flag |
| --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.07902 | in_support |
| oil | 食用油 | 0.0008875 | in_support |
| vegfruit | 蔬菜水果 | -0.27 | in_support |
| pork | 猪肉 | -0.6998 | in_support |
| meatother | 非猪肉肉类及水产品 | -0.002194 | in_support |
| dairyegg | 奶蛋类 | -0.6053 | in_support |
| nonfood | 其他/未覆盖支出 | -1.003 | in_support |

## robust_real_derived_cpi_nonfood

### m 口径描述

| index | count | mean | std | min | 5% | 25% | 50% | 75% | 95% | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| m | 310 | 68076 | 30754.4 | 29310.6 | 37877.4 | 47585.4 | 58111.2 | 78846.2 | 138569 | 184841 |
| m_consumption_real | 310 | 20783.7 | 7227.42 | 9341.54 | 13675.1 | 16193 | 18427 | 22607 | 39547.7 | 45592.9 |
| pgdp_nominal | 310 | 64865.5 | 30158.3 | 25946 | 33853.7 | 44453.9 | 56007.7 | 76658.9 | 130231 | 185026 |
| covered_food_exp | 310 | 2384.22 | 395.434 | 1597.62 | 1827.6 | 2077.46 | 2372.28 | 2652.87 | 3061.65 | 3940.11 |
| nonfood_exp | 310 | 65691.8 | 30721.1 | 26870.4 | 35830.7 | 45037.2 | 55797.2 | 76556 | 136351 | 183003 |

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | -4370 | 15 | -8709 | -8653 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2877 |  |  |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | -4439 | 23 | -8832 | -8746 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2801 |  |  |
| robust_real_derived_cpi_nonfood | LR_MAIDADS_vs_AIDADS |  | 8 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 138 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.04422 | 0.03592 | 0.1059 | 0.4176 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | meatother | 非猪肉肉类及水产品 | beef+mutton+poultry+aquatic | 0.01659 | 0.01303 | 0.04128 | 0.4019 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008653 | 0.007199 | 0.03001 | 0.2883 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03134 | 0.02537 | 0.1273 | 0.2461 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07748 | 0.05384 | 0.4123 | 0.1879 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009515 | 0.00727 | 0.05165 | 0.1842 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.602 | 2.921 | 679 | 0.005306 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04322 | 0.03476 | 0.1059 | 0.4081 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | meatother | 非猪肉肉类及水产品 | beef+mutton+poultry+aquatic | 0.01624 | 0.01242 | 0.04128 | 0.3935 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008502 | 0.007039 | 0.03001 | 0.2833 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03104 | 0.02543 | 0.1273 | 0.2438 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009458 | 0.007222 | 0.05165 | 0.1831 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.06956 | 0.04858 | 0.4123 | 0.1687 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.555 | 2.88 | 679 | 0.005236 |

### 异常检查

- 部分 MAIDADS 随机起点不可用或落入惩罚值，未被选为最终解：start_10(success=True, nll=1e+12)。
- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：meatother, oil。
- 出现正的 Marshallian 自价格弹性：oil。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 4.45828e-10 |
| max_abs_price_adding_up_error | 7.90243e-11 |
| max_abs_marshallian_homogeneity_error | 5.92384e-09 |
| max_abs_hicksian_homogeneity_error | 5.92384e-09 |
| max_abs_slutsky_symmetry_error | 8.93623e-11 |

### 收入弹性：income=30000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.2225 | 0.01392 | in_support |
| oil | 食用油 | -0.1233 | 0.02414 | in_support |
| vegfruit | 蔬菜水果 | 0.3004 | 0.01228 | in_support |
| pork | 猪肉 | 0.3278 | 0.008012 | in_support |
| meatother | 非猪肉肉类及水产品 | 0.6763 | 0.00971 | in_support |
| dairyegg | 奶蛋类 | 0.7997 | 0.002019 | in_support |
| nonfood | 其他/未覆盖支出 | 1.066 | 0.9299 | in_support |

### Marshallian 自价格弹性：income=30000

| demand_group | demand_group_label_cn | elasticity | support_flag |
| --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.03347 | in_support |
| oil | 食用油 | 0.001451 | in_support |
| vegfruit | 蔬菜水果 | -0.1862 | in_support |
| pork | 猪肉 | -0.488 | in_support |
| meatother | 非猪肉肉类及水产品 | -0.01036 | in_support |
| dairyegg | 奶蛋类 | -0.5411 | in_support |
| nonfood | 其他/未覆盖支出 | -0.9999 | in_support |

### 收入弹性：income=50000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.2264 | 0.007452 | in_support |
| oil | 食用油 | -0.1202 | 0.01361 | in_support |
| vegfruit | 蔬菜水果 | 0.2481 | 0.008479 | in_support |
| pork | 猪肉 | 0.2797 | 0.005625 | in_support |
| meatother | 非猪肉肉类及水产品 | 0.4661 | 0.007752 | in_support |
| dairyegg | 奶蛋类 | 0.5441 | 0.001698 | in_support |
| nonfood | 其他/未覆盖支出 | 1.042 | 0.9554 | in_support |

### Marshallian 自价格弹性：income=50000

| demand_group | demand_group_label_cn | elasticity | support_flag |
| --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.06091 | in_support |
| oil | 食用油 | -0.0008433 | in_support |
| vegfruit | 蔬菜水果 | -0.2445 | in_support |
| pork | 猪肉 | -0.6357 | in_support |
| meatother | 非猪肉肉类及水产品 | -0.007967 | in_support |
| dairyegg | 奶蛋类 | -0.5887 | in_support |
| nonfood | 其他/未覆盖支出 | -1.003 | in_support |

### 收入弹性：income=80000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.2324 | 0.004181 | in_support |
| oil | 食用油 | -0.1162 | 0.008046 | in_support |
| vegfruit | 蔬菜水果 | 0.1979 | 0.005885 | in_support |
| pork | 猪肉 | 0.2115 | 0.003947 | in_support |
| meatother | 非猪肉肉类及水产品 | 0.3519 | 0.005862 | in_support |
| dairyegg | 奶蛋类 | 0.3869 | 0.001318 | in_support |
| nonfood | 其他/未覆盖支出 | 1.027 | 0.9708 | in_support |

### Marshallian 自价格弹性：income=80000

| demand_group | demand_group_label_cn | elasticity | support_flag |
| --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.0891 | in_support |
| oil | 食用油 | -0.002451 | in_support |
| vegfruit | 蔬菜水果 | -0.2832 | in_support |
| pork | 猪肉 | -0.731 | in_support |
| meatother | 非猪肉肉类及水产品 | -0.00671 | in_support |
| dairyegg | 奶蛋类 | -0.6118 | in_support |
| nonfood | 其他/未覆盖支出 | -1.003 | in_support |

## 输出文件

- `*__pgdp6_panel.csv`：人均 GDP 预算口径估计面板。
- `*__parameter_estimates.csv`：AIDADS/MAIDADS 参数。
- `*__fit_by_group.csv`：分品类拟合误差。
- `*__model_comparison.csv`：AIC/BIC/LR 摘要；LR 不报告普通 chi-square p 值。
- `*__elasticity_income_grid.csv`：人均 GDP 网格下的收入/GDP 弹性。
- `*__elasticity_price_marshallian_grid.csv`、`*__elasticity_price_hicksian_grid.csv`：价格弹性。
- `*__elasticity_consistency_tests.csv`：加总、齐次性和 Slutsky 对称性检查。