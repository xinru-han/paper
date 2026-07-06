# 猪肉/水产品拆分 MAIDADS/AIDADS 结果与异常检查

- 生成时间：2026-06-11T22:36:54
- 开始时间：2026-06-11T22:32:19
- 本轮不做 bootstrap。
- 分类：保留 `grain / oil / vegfruit / dairyegg / nonfood`；把 `meatsea` 拆为 `pork / aquatic / othermeat(牛羊禽)`。

## 模型品类

| group | label_cn | items |
| --- | --- | --- |
| grain | 粮食/主粮 | grain |
| oil | 食用油 | oil |
| vegfruit | 蔬菜水果 | vegetable+fruit |
| pork | 猪肉 | pork |
| aquatic | 水产品 | aquatic |
| othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry |
| dairyegg | 奶蛋类 | milk+egg |
| nonfood | 其他/未覆盖支出 |  |

## baseline_real_national_nonfood

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | -4903 | 17 | -9772 | -9710 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3861 |  |  |
| baseline_real_national_nonfood | MAIDADS_sat | -4970 | 26 | -9889 | -9794 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3735 |  |  |
| baseline_real_national_nonfood | LR_MAIDADS_vs_AIDADS |  | 9 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 134.9 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | aquatic | 水产品 | aquatic | 0.009545 | 0.007867 | 0.01209 | 0.7897 |
| baseline_real_national_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.04785 | 0.03719 | 0.1037 | 0.4615 |
| baseline_real_national_nonfood | AIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01307 | 0.01056 | 0.02834 | 0.4612 |
| baseline_real_national_nonfood | AIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.01056 | 0.008554 | 0.02962 | 0.3563 |
| baseline_real_national_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03151 | 0.0253 | 0.128 | 0.2461 |
| baseline_real_national_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01086 | 0.007972 | 0.05127 | 0.2118 |
| baseline_real_national_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07333 | 0.05069 | 0.4162 | 0.1762 |
| baseline_real_national_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.753 | 3.054 | 188.9 | 0.01987 |
| baseline_real_national_nonfood | MAIDADS_sat | aquatic | 水产品 | aquatic | 0.009194 | 0.007307 | 0.01209 | 0.7607 |
| baseline_real_national_nonfood | MAIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01305 | 0.01039 | 0.02834 | 0.4604 |
| baseline_real_national_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04523 | 0.03649 | 0.1037 | 0.4362 |
| baseline_real_national_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.01055 | 0.008741 | 0.02962 | 0.3562 |
| baseline_real_national_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03148 | 0.02499 | 0.128 | 0.2459 |
| baseline_real_national_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01043 | 0.007689 | 0.05127 | 0.2034 |
| baseline_real_national_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.06316 | 0.04774 | 0.4162 | 0.1518 |
| baseline_real_national_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.837 | 3.154 | 188.9 | 0.02031 |

### 异常检查

- 部分 MAIDADS 随机起点不可用或落入惩罚值，未被选为最终解：start_4(success=False, nll=-4.91e+03)。
- 选中解梯度范数偏大：max grad_norm=8.272e+09。
- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：aquatic。
- MAIDADS 部分食品相对 RMSE > 0.5：aquatic=0.76。
- 出现正的 Marshallian 自价格弹性：oil。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 1.10212e-08 |
| max_abs_price_adding_up_error | 7.56007e-10 |
| max_abs_marshallian_homogeneity_error | 7.30241e-08 |
| max_abs_hicksian_homogeneity_error | 7.30241e-08 |
| max_abs_slutsky_symmetry_error | 2.79787e-09 |

### 中位收入网格附近收入弹性：income=30000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.3042 | 0.01029 | in_support |
| oil | 食用油 | -0.01373 | 0.02151 | in_support |
| vegfruit | 蔬菜水果 | 0.04388 | 0.01516 | in_support |
| pork | 猪肉 | -0.1094 | 0.009658 | in_support |
| aquatic | 水产品 | -0.1329 | 0.003561 | in_support |
| othermeat | 其他肉类(牛羊禽) | -0.03285 | 0.009862 | in_support |
| dairyegg | 奶蛋类 | 0.03112 | 0.003274 | in_support |
| nonfood | 其他/未覆盖支出 | 1.084 | 0.9267 | in_support |

## robust_real_derived_cpi_nonfood

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | -4915 | 17 | -9797 | -9735 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3825 |  |  |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | -4917 | 26 | -9781 | -9687 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3829 |  |  |
| robust_real_derived_cpi_nonfood | LR_MAIDADS_vs_AIDADS |  | 9 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 2.035 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | aquatic | 水产品 | aquatic | 0.009383 | 0.007629 | 0.01209 | 0.7763 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01304 | 0.01043 | 0.02834 | 0.4602 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.04675 | 0.03667 | 0.1037 | 0.4508 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.01057 | 0.008577 | 0.02962 | 0.3569 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03151 | 0.0253 | 0.128 | 0.2462 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01086 | 0.007972 | 0.05127 | 0.2118 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07305 | 0.05032 | 0.4162 | 0.1755 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.716 | 3.037 | 187.4 | 0.01983 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | aquatic | 水产品 | aquatic | 0.0094 | 0.007686 | 0.01209 | 0.7777 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01304 | 0.01036 | 0.02834 | 0.4602 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04695 | 0.03662 | 0.1037 | 0.4528 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.01055 | 0.008536 | 0.02962 | 0.3562 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03154 | 0.02543 | 0.128 | 0.2464 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01088 | 0.007996 | 0.05127 | 0.2123 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.07269 | 0.05011 | 0.4162 | 0.1747 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.718 | 3.036 | 187.4 | 0.01984 |

### 异常检查

- 部分 MAIDADS 随机起点不可用或落入惩罚值，未被选为最终解：start_1(success=False, nll=-4.92e+03), start_3(success=False, nll=-4.92e+03)。
- 选中解梯度范数偏大：max grad_norm=2.928e+09。
- MAIDADS 部分食品相对 RMSE > 0.5：aquatic=0.78。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 1.56102e-08 |
| max_abs_price_adding_up_error | 1.7887e-09 |
| max_abs_marshallian_homogeneity_error | 1.14586e-07 |
| max_abs_hicksian_homogeneity_error | 1.14586e-07 |
| max_abs_slutsky_symmetry_error | 5.10466e-09 |

### 中位收入网格附近收入弹性：income=30000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.03853 | 0.01169 | in_support |
| oil | 食用油 | 0.005161 | 0.02207 | in_support |
| vegfruit | 蔬菜水果 | -0.002797 | 0.01449 | in_support |
| pork | 猪肉 | -0.1334 | 0.01023 | in_support |
| aquatic | 水产品 | -0.1561 | 0.003715 | in_support |
| othermeat | 其他肉类(牛羊禽) | 0.004639 | 0.01009 | in_support |
| dairyegg | 奶蛋类 | -0.08467 | 0.002976 | in_support |
| nonfood | 其他/未覆盖支出 | 1.084 | 0.9247 | in_support |

## 输出文件

- `*__split_panel.csv`：拆分品类估计面板。
- `*__parameter_estimates.csv`：AIDADS/MAIDADS 参数。
- `*__fit_by_group.csv`：分品类拟合误差。
- `*__model_comparison.csv`：AIC/BIC/LR 摘要；LR 不报告普通 chi-square p 值。
- `*__elasticity_income_grid.csv`：拆分品类收入弹性。
- `*__elasticity_price_marshallian_grid.csv`、`*__elasticity_price_hicksian_grid.csv`：价格弹性。
- `*__elasticity_consistency_tests.csv`：加总、齐次性和 Slutsky 对称性检查。