# 猪肉拆分 MAIDADS/AIDADS 结果与异常检查

- 生成时间：2026-06-11T23:05:38
- 开始时间：2026-06-11T23:01:25
- 本轮不做 bootstrap。
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

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | -3842 | 15 | -7654 | -7599 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3085 |  |  |
| baseline_real_national_nonfood | MAIDADS_sat | -3843 | 23 | -7639 | -7556 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3084 |  |  |
| baseline_real_national_nonfood | LR_MAIDADS_vs_AIDADS |  | 8 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 1.341 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.04505 | 0.03644 | 0.1037 | 0.4345 |
| baseline_real_national_nonfood | AIDADS_sat | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic | 0.01733 | 0.01377 | 0.04043 | 0.4287 |
| baseline_real_national_nonfood | AIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.01043 | 0.008475 | 0.02962 | 0.3519 |
| baseline_real_national_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03148 | 0.02552 | 0.128 | 0.246 |
| baseline_real_national_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01085 | 0.008016 | 0.05127 | 0.2116 |
| baseline_real_national_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07426 | 0.05169 | 0.4162 | 0.1784 |
| baseline_real_national_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.798 | 3.123 | 188.9 | 0.02011 |
| baseline_real_national_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04504 | 0.03641 | 0.1037 | 0.4343 |
| baseline_real_national_nonfood | MAIDADS_sat | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic | 0.01733 | 0.01378 | 0.04043 | 0.4287 |
| baseline_real_national_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.01042 | 0.008509 | 0.02962 | 0.3519 |
| baseline_real_national_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.0315 | 0.02546 | 0.128 | 0.2461 |
| baseline_real_national_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01084 | 0.008025 | 0.05127 | 0.2114 |
| baseline_real_national_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.07421 | 0.05185 | 0.4162 | 0.1783 |
| baseline_real_national_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.794 | 3.117 | 188.9 | 0.02008 |

### 异常检查

- 选中解梯度范数偏大：max grad_norm=219.3。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 1.0375e-08 |
| max_abs_price_adding_up_error | 1.11259e-09 |
| max_abs_marshallian_homogeneity_error | 8.02476e-08 |
| max_abs_hicksian_homogeneity_error | 8.02476e-08 |
| max_abs_slutsky_symmetry_error | 3.0936e-09 |

### 中位收入网格附近收入弹性：income=30000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.06693 | 0.01201 | in_support |
| oil | 食用油 | 0.0008386 | 0.02207 | in_support |
| vegfruit | 蔬菜水果 | 0.0008268 | 0.01434 | in_support |
| pork | 猪肉 | -0.1002 | 0.009426 | in_support |
| nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.0009678 | 0.01413 | in_support |
| dairyegg | 奶蛋类 | -0.05266 | 0.003049 | in_support |
| nonfood | 其他/未覆盖支出 | 1.083 | 0.925 | in_support |

## robust_real_derived_cpi_nonfood

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | -3851 | 15 | -7673 | -7618 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3089 |  |  |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | -3852 | 23 | -7659 | -7575 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3089 |  |  |
| robust_real_derived_cpi_nonfood | LR_MAIDADS_vs_AIDADS |  | 8 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 1.936 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.04502 | 0.03615 | 0.1037 | 0.4341 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic | 0.01733 | 0.01377 | 0.04043 | 0.4287 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.01049 | 0.008541 | 0.02962 | 0.3542 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03149 | 0.02538 | 0.128 | 0.246 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01086 | 0.007963 | 0.05127 | 0.2119 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07437 | 0.05294 | 0.4162 | 0.1787 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.798 | 3.13 | 187.4 | 0.02026 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04504 | 0.03614 | 0.1037 | 0.4343 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic | 0.01733 | 0.01378 | 0.04043 | 0.4286 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.0105 | 0.008574 | 0.02962 | 0.3543 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03151 | 0.02537 | 0.128 | 0.2461 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01084 | 0.007969 | 0.05127 | 0.2115 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.07421 | 0.05298 | 0.4162 | 0.1783 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.796 | 3.125 | 187.4 | 0.02026 |

### 异常检查

- 部分 MAIDADS 随机起点不可用或落入惩罚值，未被选为最终解：start_3(success=False, nll=-3.85e+03)。
- 选中解梯度范数偏大：max grad_norm=6.968e+09。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 1.09023e-08 |
| max_abs_price_adding_up_error | 1.03845e-09 |
| max_abs_marshallian_homogeneity_error | 6.97127e-08 |
| max_abs_hicksian_homogeneity_error | 6.97127e-08 |
| max_abs_slutsky_symmetry_error | 3.19512e-09 |

### 中位收入网格附近收入弹性：income=30000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.09115 | 0.01187 | in_support |
| oil | 食用油 | 0.0006136 | 0.02198 | in_support |
| vegfruit | 蔬菜水果 | -0.0002916 | 0.01449 | in_support |
| pork | 猪肉 | -0.1087 | 0.009587 | in_support |
| nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.0011 | 0.01414 | in_support |
| dairyegg | 奶蛋类 | -0.06357 | 0.003045 | in_support |
| nonfood | 其他/未覆盖支出 | 1.084 | 0.9249 | in_support |

## 输出文件

- `*__split_panel.csv`：拆分品类估计面板。
- `*__parameter_estimates.csv`：AIDADS/MAIDADS 参数。
- `*__fit_by_group.csv`：分品类拟合误差。
- `*__model_comparison.csv`：AIC/BIC/LR 摘要；LR 不报告普通 chi-square p 值。
- `*__elasticity_income_grid.csv`：拆分品类收入弹性。
- `*__elasticity_price_marshallian_grid.csv`、`*__elasticity_price_hicksian_grid.csv`：价格弹性。
- `*__elasticity_consistency_tests.csv`：加总、齐次性和 Slutsky 对称性检查。