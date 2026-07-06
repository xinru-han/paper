# 猪肉拆分 MAIDADS/AIDADS 结果与异常检查

- 生成时间：2026-07-06T00:05:33
- 开始时间：2026-07-05T23:53:30
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
| baseline_real_national_nonfood | AIDADS_sat | -4252 | 15 | -8473 | -8417 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3085 |  |  |
| baseline_real_national_nonfood | MAIDADS_sat | -4482 | 23 | -8917 | -8831 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2738 |  |  |
| baseline_real_national_nonfood | LR_MAIDADS_vs_AIDADS |  | 8 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 460.1 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.04579 | 0.03685 | 0.1059 | 0.4324 |
| baseline_real_national_nonfood | AIDADS_sat | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic | 0.01764 | 0.01404 | 0.04128 | 0.4274 |
| baseline_real_national_nonfood | AIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.01064 | 0.008664 | 0.03001 | 0.3545 |
| baseline_real_national_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03135 | 0.02524 | 0.1273 | 0.2462 |
| baseline_real_national_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01086 | 0.008014 | 0.05165 | 0.2103 |
| baseline_real_national_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.0744 | 0.05202 | 0.4123 | 0.1805 |
| baseline_real_national_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.756 | 3.089 | 191.7 | 0.01959 |
| baseline_real_national_nonfood | MAIDADS_sat | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic | 0.01707 | 0.01371 | 0.04128 | 0.4136 |
| baseline_real_national_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04233 | 0.0344 | 0.1059 | 0.3997 |
| baseline_real_national_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008251 | 0.006717 | 0.03001 | 0.2749 |
| baseline_real_national_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03065 | 0.02547 | 0.1273 | 0.2407 |
| baseline_real_national_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.008176 | 0.006542 | 0.05165 | 0.1583 |
| baseline_real_national_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.06425 | 0.04934 | 0.4123 | 0.1558 |
| baseline_real_national_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.638 | 2.944 | 191.7 | 0.01898 |

### 异常检查

- 选中解梯度范数偏大：max grad_norm=1.98e+08。
- 出现正的 Marshallian 自价格弹性：grain, oil。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 5.91048e-09 |
| max_abs_price_adding_up_error | 1.11313e-09 |
| max_abs_marshallian_homogeneity_error | 2.78694e-07 |
| max_abs_hicksian_homogeneity_error | 2.78694e-07 |
| max_abs_slutsky_symmetry_error | 2.5878e-09 |

### 中位收入网格附近收入弹性：income=30000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.3977 | 0.01002 | in_support |
| oil | 食用油 | -0.1989 | 0.0203 | in_support |
| vegfruit | 蔬菜水果 | 0.256 | 0.01727 | in_support |
| pork | 猪肉 | 0.1745 | 0.01116 | in_support |
| nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.1185 | 0.01543 | in_support |
| dairyegg | 奶蛋类 | 0.3318 | 0.003919 | in_support |
| nonfood | 其他/未覆盖支出 | 1.083 | 0.9219 | in_support |

## robust_real_derived_cpi_nonfood

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | -4394 | 15 | -8758 | -8702 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2816 |  |  |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | -4430 | 23 | -8814 | -8728 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2775 |  |  |
| robust_real_derived_cpi_nonfood | LR_MAIDADS_vs_AIDADS |  | 8 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 72.54 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.04329 | 0.03472 | 0.1059 | 0.4088 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic | 0.01651 | 0.01302 | 0.04128 | 0.3999 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.00842 | 0.006819 | 0.03001 | 0.2805 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03144 | 0.02498 | 0.1273 | 0.2469 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07771 | 0.0539 | 0.4123 | 0.1885 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.008539 | 0.006653 | 0.05165 | 0.1653 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.675 | 2.823 | 190.3 | 0.01931 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic | 0.01667 | 0.01354 | 0.04128 | 0.4039 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04233 | 0.03439 | 0.1059 | 0.3997 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008407 | 0.006776 | 0.03001 | 0.2801 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.0313 | 0.0256 | 0.1273 | 0.2458 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.07051 | 0.0509 | 0.4123 | 0.171 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.008503 | 0.006575 | 0.05165 | 0.1646 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.547 | 2.799 | 190.3 | 0.01864 |

### 异常检查

- 部分 MAIDADS 随机起点不可用或落入惩罚值，未被选为最终解：start_1(success=True, nll=1e+12), start_7(success=True, nll=1e+12), start_9(success=True, nll=1e+12), start_10(success=True, nll=1e+12)。
- 选中解梯度范数偏大：max grad_norm=357.2。
- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：grain。
- 出现正的 Marshallian 自价格弹性：grain, oil。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 2.69926e-09 |
| max_abs_price_adding_up_error | 2.52665e-10 |
| max_abs_marshallian_homogeneity_error | 7.74986e-08 |
| max_abs_hicksian_homogeneity_error | 7.74986e-08 |
| max_abs_slutsky_symmetry_error | 2.643e-09 |

### 中位收入网格附近收入弹性：income=30000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.08702 | 0.01127 | in_support |
| oil | 食用油 | -0.005917 | 0.02218 | in_support |
| vegfruit | 蔬菜水果 | 0.2275 | 0.01698 | in_support |
| pork | 猪肉 | 0.3963 | 0.0121 | in_support |
| nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.2601 | 0.01727 | in_support |
| dairyegg | 奶蛋类 | 0.4402 | 0.004009 | in_support |
| nonfood | 其他/未覆盖支出 | 1.076 | 0.9162 | in_support |

## 输出文件

- `*__split_panel.csv`：拆分品类估计面板。
- `*__parameter_estimates.csv`：AIDADS/MAIDADS 参数。
- `*__fit_by_group.csv`：分品类拟合误差。
- `*__model_comparison.csv`：AIC/BIC/LR 摘要；LR 不报告普通 chi-square p 值。
- `*__elasticity_income_grid.csv`：拆分品类收入弹性。
- `*__elasticity_price_marshallian_grid.csv`、`*__elasticity_price_hicksian_grid.csv`：价格弹性。
- `*__elasticity_consistency_tests.csv`：加总、齐次性和 Slutsky 对称性检查。