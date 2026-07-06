# 原始品类 MAIDADS/AIDADS 重新估计与异常检查

- 生成时间：2026-06-11T21:28:28
- 开始时间：2026-06-11T20:20:55
- 本轮不做 bootstrap。
- 食品品类使用原始 11 类，不再合并肉类水产品或奶蛋；另外保留 `nonfood` 残差作为第 12 类。
- 饱和设定仍为：所有食品 `beta=0`，`nonfood beta=1`。

## 原始品类与模型品类

| group | label_cn |
| --- | --- |
| grain | 粮食/主粮 |
| oil | 食用油 |
| vegetable | 蔬菜 |
| fruit | 水果 |
| pork | 猪肉 |
| beef | 牛肉 |
| mutton | 羊肉 |
| poultry | 禽肉 |
| aquatic | 水产品 |
| egg | 蛋类 |
| milk | 奶类 |
| nonfood | 其他/未覆盖支出 |

## baseline_real_national_nonfood

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | -1.017e+04 | 25 | -2.028e+04 | -2.019e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.5236 |  |  |
| baseline_real_national_nonfood | MAIDADS_sat | -1.022e+04 | 38 | -2.036e+04 | -2.022e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.5204 |  |  |
| baseline_real_national_nonfood | LR_MAIDADS_vs_AIDADS |  | 13 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 99.49 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | mutton | 羊肉 | 0.007818 | 0.00498 | 0.00596 | 1.312 |
| baseline_real_national_nonfood | AIDADS_sat | beef | 牛肉 | 0.006726 | 0.002912 | 0.005376 | 1.251 |
| baseline_real_national_nonfood | AIDADS_sat | poultry | 禽肉 | 0.01063 | 0.008199 | 0.01701 | 0.625 |
| baseline_real_national_nonfood | AIDADS_sat | aquatic | 水产品 | 0.006481 | 0.004818 | 0.01209 | 0.5362 |
| baseline_real_national_nonfood | AIDADS_sat | pork | 猪肉 | 0.04263 | 0.03566 | 0.1037 | 0.4111 |
| baseline_real_national_nonfood | AIDADS_sat | milk | 奶类 | 0.003752 | 0.003068 | 0.01 | 0.375 |
| baseline_real_national_nonfood | AIDADS_sat | egg | 蛋类 | 0.007001 | 0.00559 | 0.01962 | 0.3569 |
| baseline_real_national_nonfood | AIDADS_sat | fruit | 水果 | 0.006108 | 0.004988 | 0.02182 | 0.28 |
| baseline_real_national_nonfood | AIDADS_sat | oil | 食用油 | 0.03151 | 0.02537 | 0.128 | 0.2462 |
| baseline_real_national_nonfood | AIDADS_sat | grain | 粮食/主粮 | 0.07853 | 0.05399 | 0.4162 | 0.1887 |
| baseline_real_national_nonfood | AIDADS_sat | vegetable | 蔬菜 | 0.005227 | 0.003836 | 0.02945 | 0.1775 |
| baseline_real_national_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 | 3.664 | 2.812 | 188.9 | 0.0194 |
| baseline_real_national_nonfood | MAIDADS_sat | mutton | 羊肉 | 0.007801 | 0.00506 | 0.00596 | 1.309 |
| baseline_real_national_nonfood | MAIDADS_sat | beef | 牛肉 | 0.006666 | 0.002646 | 0.005376 | 1.24 |
| baseline_real_national_nonfood | MAIDADS_sat | poultry | 禽肉 | 0.01061 | 0.007988 | 0.01701 | 0.624 |
| baseline_real_national_nonfood | MAIDADS_sat | aquatic | 水产品 | 0.006625 | 0.004963 | 0.01209 | 0.5481 |
| baseline_real_national_nonfood | MAIDADS_sat | pork | 猪肉 | 0.04198 | 0.03442 | 0.1037 | 0.4048 |
| baseline_real_national_nonfood | MAIDADS_sat | milk | 奶类 | 0.003782 | 0.003084 | 0.01 | 0.378 |
| baseline_real_national_nonfood | MAIDADS_sat | egg | 蛋类 | 0.007137 | 0.005831 | 0.01962 | 0.3638 |
| baseline_real_national_nonfood | MAIDADS_sat | fruit | 水果 | 0.005995 | 0.004951 | 0.02182 | 0.2748 |
| baseline_real_national_nonfood | MAIDADS_sat | oil | 食用油 | 0.03194 | 0.02513 | 0.128 | 0.2495 |
| baseline_real_national_nonfood | MAIDADS_sat | vegetable | 蔬菜 | 0.004999 | 0.003759 | 0.02945 | 0.1697 |
| baseline_real_national_nonfood | MAIDADS_sat | grain | 粮食/主粮 | 0.06795 | 0.04925 | 0.4162 | 0.1633 |
| baseline_real_national_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 | 3.57 | 2.694 | 188.9 | 0.0189 |

### 异常检查

- 部分 MAIDADS 随机起点不可用或落入惩罚值，未被选为最终解：start_5(success=True, nll=1e+12)。
- 选中解梯度范数偏大：max grad_norm=225.2。
- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：beef, grain, oil。
- MAIDADS 部分食品相对 RMSE > 0.5：beef=1.24, mutton=1.31, poultry=0.62, aquatic=0.55。
- 收入弹性绝对值 > 5 的点：beef@10000=16.81, aquatic@10000=15.49。
- 出现正的 Marshallian 自价格弹性：grain。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 2.37668e-08 |
| max_abs_price_adding_up_error | 9.04743e-09 |
| max_abs_marshallian_homogeneity_error | 6.26261e-06 |
| max_abs_hicksian_homogeneity_error | 6.26261e-06 |
| max_abs_slutsky_symmetry_error | 1.16803e-08 |

## robust_real_derived_cpi_nonfood

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | -1.017e+04 | 25 | -2.029e+04 | -2.02e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.5228 |  |  |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | -1.018e+04 | 38 | -2.028e+04 | -2.015e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.52 |  |  |
| robust_real_derived_cpi_nonfood | LR_MAIDADS_vs_AIDADS |  | 13 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 22.93 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | mutton | 羊肉 | 0.007994 | 0.004693 | 0.00596 | 1.341 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | beef | 牛肉 | 0.006614 | 0.002749 | 0.005376 | 1.23 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | poultry | 禽肉 | 0.01066 | 0.008264 | 0.01701 | 0.6269 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | aquatic | 水产品 | 0.006636 | 0.005024 | 0.01209 | 0.549 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | pork | 猪肉 | 0.04185 | 0.03456 | 0.1037 | 0.4036 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | milk | 奶类 | 0.003827 | 0.003117 | 0.01 | 0.3825 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | egg | 蛋类 | 0.006691 | 0.005349 | 0.01962 | 0.341 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | fruit | 水果 | 0.005836 | 0.004825 | 0.02182 | 0.2675 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | oil | 食用油 | 0.03154 | 0.02534 | 0.128 | 0.2464 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | grain | 粮食/主粮 | 0.07854 | 0.05398 | 0.4162 | 0.1887 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | vegetable | 蔬菜 | 0.0051 | 0.003798 | 0.02945 | 0.1731 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 | 3.616 | 2.717 | 187.4 | 0.01929 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | mutton | 羊肉 | 0.007807 | 0.005105 | 0.00596 | 1.31 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | beef | 牛肉 | 0.006623 | 0.00284 | 0.005376 | 1.232 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | poultry | 禽肉 | 0.01066 | 0.008216 | 0.01701 | 0.6266 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | aquatic | 水产品 | 0.00665 | 0.005017 | 0.01209 | 0.5502 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | pork | 猪肉 | 0.04196 | 0.03445 | 0.1037 | 0.4046 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | milk | 奶类 | 0.003809 | 0.003109 | 0.01 | 0.3807 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | egg | 蛋类 | 0.006681 | 0.005318 | 0.01962 | 0.3406 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | fruit | 水果 | 0.00584 | 0.004829 | 0.02182 | 0.2677 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | oil | 食用油 | 0.03153 | 0.02536 | 0.128 | 0.2464 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | grain | 粮食/主粮 | 0.07846 | 0.05407 | 0.4162 | 0.1885 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | vegetable | 蔬菜 | 0.005093 | 0.003793 | 0.02945 | 0.1729 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 | 3.598 | 2.719 | 187.4 | 0.0192 |

### 异常检查

- 部分 MAIDADS 随机起点不可用或落入惩罚值，未被选为最终解：start_2(success=True, nll=1e+12), start_3(success=False, nll=1e+12), start_5(success=True, nll=1e+12)。
- 选中解梯度范数偏大：max grad_norm=28.16。
- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：beef, grain。
- MAIDADS 部分食品相对 RMSE > 0.5：beef=1.23, mutton=1.31, poultry=0.63, aquatic=0.55。
- 收入弹性绝对值 > 5 的点：beef@10000=12.13, aquatic@10000=12.16。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 1.58881e-08 |
| max_abs_price_adding_up_error | 6.93133e-09 |
| max_abs_marshallian_homogeneity_error | 3.58289e-06 |
| max_abs_hicksian_homogeneity_error | 3.58289e-06 |
| max_abs_slutsky_symmetry_error | 2.95678e-09 |

## 输出文件

- `*__original_item_panel.csv`：原始品类估计面板。
- `*__parameter_estimates.csv`：AIDADS/MAIDADS 参数。
- `*__fit_by_group.csv`：分品类拟合误差。
- `*__model_comparison.csv`：AIC/BIC/LR 摘要；LR 不报告普通 chi-square p 值。
- `*__elasticity_income_grid.csv`：原始品类收入弹性。
- `*__elasticity_price_marshallian_grid.csv`、`*__elasticity_price_hicksian_grid.csv`：价格弹性。
- `*__elasticity_consistency_tests.csv`：加总、齐次性和 Slutsky 对称性检查。
- `*__parameter_boundary_report.csv`、`*__multistart_diagnostics.csv`：边界与优化诊断。