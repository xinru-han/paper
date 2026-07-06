# 猪肉拆分 MAIDADS/AIDADS 结果与异常检查：人均 GDP 预算口径

- 生成时间：2026-06-12T00:28:17
- 开始时间：2026-06-12T00:16:53
- 本轮不做 bootstrap。
- 本轮把模型预算变量 `m` 从实际人均消费支出改为实际人均 GDP：`m = pgdp / monetary_deflator`。
- 注意：此设定模仿 Gouel-Guimbard 原文的人均 GDP 预算尺度；但省级 household demand 解释应谨慎，因为 `nonfood` residual 变成 `人均 GDP - covered food expenditure`。
- 分类：保留 `grain / oil / vegfruit / dairyegg / nonfood`；把原 `meatsea` 拆为 `pork / nonpork_meatsea(牛羊禽+水产品)`。

## 模型品类

| group | label_cn | items |
| --- | --- | --- |
| grain | 粮食/主粮 | grain |
| oil | 食用油 | oil |
| vegfruit | 蔬菜水果 | vegetable+fruit |
| pork | 猪肉 | pork |
| nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic |
| dairyegg | 奶蛋类 | milk+egg |
| nonfood | 其他/未覆盖支出 |  |

## baseline_real_national_nonfood

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

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic | 0.01735 | 0.01382 | 0.04043 | 0.429 |
| baseline_real_national_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.04312 | 0.03506 | 0.1037 | 0.4158 |
| baseline_real_national_nonfood | AIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008393 | 0.007027 | 0.02962 | 0.2833 |
| baseline_real_national_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.0315 | 0.02579 | 0.128 | 0.2461 |
| baseline_real_national_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07837 | 0.0544 | 0.4162 | 0.1883 |
| baseline_real_national_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009487 | 0.00726 | 0.05127 | 0.185 |
| baseline_real_national_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.597 | 2.906 | 673.7 | 0.005339 |
| baseline_real_national_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.0423 | 0.03403 | 0.1037 | 0.4079 |
| baseline_real_national_nonfood | MAIDADS_sat | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic | 0.01605 | 0.01229 | 0.04043 | 0.397 |
| baseline_real_national_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008409 | 0.006931 | 0.02962 | 0.2839 |
| baseline_real_national_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03123 | 0.02568 | 0.128 | 0.244 |
| baseline_real_national_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009494 | 0.007233 | 0.05127 | 0.1852 |
| baseline_real_national_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.07059 | 0.04898 | 0.4162 | 0.1696 |
| baseline_real_national_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.612 | 2.908 | 673.7 | 0.005361 |

### 异常检查

- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：dairyegg, grain, nonpork_meatsea, oil。
- 出现正的 Marshallian 自价格弹性：grain, oil。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 1.65058e-09 |
| max_abs_price_adding_up_error | 2.61239e-10 |
| max_abs_marshallian_homogeneity_error | 2.76529e-09 |
| max_abs_hicksian_homogeneity_error | 2.76529e-09 |
| max_abs_slutsky_symmetry_error | 3.66018e-10 |

### 中位收入网格附近收入弹性：income=56762

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.2307 | 0.006425 | in_support |
| oil | 食用油 | -0.1076 | 0.01195 | in_support |
| vegfruit | 蔬菜水果 | 0.2263 | 0.007684 | in_support |
| pork | 猪肉 | 0.2661 | 0.005268 | in_support |
| nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.4111 | 0.007142 | in_support |
| dairyegg | 奶蛋类 | 0.4794 | 0.001594 | in_support |
| nonfood | 其他/未覆盖支出 | 1.037 | 0.9599 | in_support |

## robust_real_derived_cpi_nonfood

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

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic | 0.01732 | 0.01373 | 0.04043 | 0.4285 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.04272 | 0.03418 | 0.1037 | 0.412 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.009554 | 0.007746 | 0.02962 | 0.3225 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03158 | 0.02511 | 0.128 | 0.2467 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01035 | 0.007535 | 0.05127 | 0.2018 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07992 | 0.05324 | 0.4162 | 0.192 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.665 | 2.97 | 668.5 | 0.005483 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04212 | 0.03387 | 0.1037 | 0.4061 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic | 0.01604 | 0.01225 | 0.04043 | 0.3967 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008342 | 0.006911 | 0.02962 | 0.2816 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03124 | 0.02558 | 0.128 | 0.2441 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009492 | 0.007239 | 0.05127 | 0.1851 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.07044 | 0.04836 | 0.4162 | 0.1692 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.577 | 2.885 | 668.5 | 0.005352 |

### 异常检查

- 选中解梯度范数偏大：max grad_norm=162.1。
- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：dairyegg, nonpork_meatsea, oil, pork。
- 出现正的 Marshallian 自价格弹性：oil。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 1.69253e-09 |
| max_abs_price_adding_up_error | 2.62629e-10 |
| max_abs_marshallian_homogeneity_error | 1.5164e-08 |
| max_abs_hicksian_homogeneity_error | 1.5164e-08 |
| max_abs_slutsky_symmetry_error | 3.73614e-10 |

### 中位收入网格附近收入弹性：income=56762

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.2152 | 0.006461 | in_support |
| oil | 食用油 | -0.1091 | 0.01186 | in_support |
| vegfruit | 蔬菜水果 | 0.2322 | 0.007676 | in_support |
| pork | 猪肉 | 0.2695 | 0.005248 | in_support |
| nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.4043 | 0.007148 | in_support |
| dairyegg | 奶蛋类 | 0.4977 | 0.001601 | in_support |
| nonfood | 其他/未覆盖支出 | 1.037 | 0.96 | in_support |

## 输出文件

- `*__split_panel.csv`：拆分品类估计面板。
- `*__parameter_estimates.csv`：AIDADS/MAIDADS 参数。
- `*__fit_by_group.csv`：分品类拟合误差。
- `*__model_comparison.csv`：AIC/BIC/LR 摘要；LR 不报告普通 chi-square p 值。
- `*__elasticity_income_grid.csv`：拆分品类收入弹性。
- `*__elasticity_price_marshallian_grid.csv`、`*__elasticity_price_hicksian_grid.csv`：价格弹性。
- `*__elasticity_consistency_tests.csv`：加总、齐次性和 Slutsky 对称性检查。