# 原始品类 MAIDADS/AIDADS 重新估计与异常检查

- 生成时间：2026-07-05T23:53:29
- 开始时间：2026-07-05T23:37:04
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
| baseline_real_national_nonfood | AIDADS_sat | -1.121e+04 | 25 | -2.238e+04 | -2.228e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.5166 |  |  |
| baseline_real_national_nonfood | MAIDADS_sat | -1.136e+04 | 38 | -2.265e+04 | -2.251e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.5105 |  |  |
| baseline_real_national_nonfood | LR_MAIDADS_vs_AIDADS |  | 13 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 298.6 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | mutton | 羊肉 | 0.008032 | 0.004722 | 0.006078 | 1.321 |
| baseline_real_national_nonfood | AIDADS_sat | beef | 牛肉 | 0.006694 | 0.002984 | 0.005678 | 1.179 |
| baseline_real_national_nonfood | AIDADS_sat | poultry | 禽肉 | 0.01071 | 0.008347 | 0.01727 | 0.6204 |
| baseline_real_national_nonfood | AIDADS_sat | aquatic | 水产品 | 0.006997 | 0.005399 | 0.01225 | 0.571 |
| baseline_real_national_nonfood | AIDADS_sat | pork | 猪肉 | 0.04206 | 0.03433 | 0.1059 | 0.3972 |
| baseline_real_national_nonfood | AIDADS_sat | milk | 奶类 | 0.003927 | 0.003121 | 0.009988 | 0.3932 |
| baseline_real_national_nonfood | AIDADS_sat | egg | 蛋类 | 0.006631 | 0.005285 | 0.02003 | 0.3311 |
| baseline_real_national_nonfood | AIDADS_sat | fruit | 水果 | 0.005787 | 0.004775 | 0.02209 | 0.262 |
| baseline_real_national_nonfood | AIDADS_sat | oil | 食用油 | 0.03134 | 0.02532 | 0.1273 | 0.2461 |
| baseline_real_national_nonfood | AIDADS_sat | grain | 粮食/主粮 | 0.07751 | 0.05384 | 0.4123 | 0.188 |
| baseline_real_national_nonfood | AIDADS_sat | vegetable | 蔬菜 | 0.005109 | 0.0038 | 0.02956 | 0.1729 |
| baseline_real_national_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 | 3.545 | 2.673 | 191.7 | 0.01849 |
| baseline_real_national_nonfood | MAIDADS_sat | mutton | 羊肉 | 0.008017 | 0.004769 | 0.006078 | 1.319 |
| baseline_real_national_nonfood | MAIDADS_sat | beef | 牛肉 | 0.006719 | 0.00276 | 0.005678 | 1.183 |
| baseline_real_national_nonfood | MAIDADS_sat | poultry | 禽肉 | 0.01053 | 0.008247 | 0.01727 | 0.6097 |
| baseline_real_national_nonfood | MAIDADS_sat | aquatic | 水产品 | 0.007032 | 0.005498 | 0.01225 | 0.5738 |
| baseline_real_national_nonfood | MAIDADS_sat | pork | 猪肉 | 0.042 | 0.0346 | 0.1059 | 0.3966 |
| baseline_real_national_nonfood | MAIDADS_sat | milk | 奶类 | 0.00369 | 0.002938 | 0.009988 | 0.3695 |
| baseline_real_national_nonfood | MAIDADS_sat | egg | 蛋类 | 0.00673 | 0.00541 | 0.02003 | 0.336 |
| baseline_real_national_nonfood | MAIDADS_sat | fruit | 水果 | 0.00577 | 0.004803 | 0.02209 | 0.2612 |
| baseline_real_national_nonfood | MAIDADS_sat | oil | 食用油 | 0.03111 | 0.02491 | 0.1273 | 0.2443 |
| baseline_real_national_nonfood | MAIDADS_sat | vegetable | 蔬菜 | 0.004865 | 0.003695 | 0.02956 | 0.1646 |
| baseline_real_national_nonfood | MAIDADS_sat | grain | 粮食/主粮 | 0.06471 | 0.0496 | 0.4123 | 0.157 |
| baseline_real_national_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 | 3.399 | 2.631 | 191.7 | 0.01773 |

### 异常检查

- 部分 MAIDADS 随机起点不可用或落入惩罚值，未被选为最终解：start_4(success=False, nll=1e+12), start_5(success=True, nll=1e+12), start_6(success=True, nll=1e+12), start_7(success=True, nll=1e+12), start_8(success=True, nll=1e+12), start_9(success=True, nll=1e+12)。
- 选中解梯度范数偏大：max grad_norm=256.9。
- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：beef, grain, oil。
- MAIDADS 部分食品相对 RMSE > 0.5：beef=1.18, mutton=1.32, poultry=0.61, aquatic=0.57。
- 收入弹性绝对值 > 5 的点：beef@10000=12.94, aquatic@10000=13.95。
- 出现正的 Marshallian 自价格弹性：grain, oil。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 1.88035e-08 |
| max_abs_price_adding_up_error | 5.44285e-09 |
| max_abs_marshallian_homogeneity_error | 2.9681e-06 |
| max_abs_hicksian_homogeneity_error | 2.9681e-06 |
| max_abs_slutsky_symmetry_error | 5.60841e-09 |

## robust_real_derived_cpi_nonfood

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | -1.126e+04 | 25 | -2.248e+04 | -2.238e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.5139 |  |  |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | -1.131e+04 | 38 | -2.254e+04 | -2.239e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.5123 |  |  |
| robust_real_derived_cpi_nonfood | LR_MAIDADS_vs_AIDADS |  | 13 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 87.32 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | mutton | 羊肉 | 0.00789 | 0.005167 | 0.006078 | 1.298 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | beef | 牛肉 | 0.006753 | 0.002955 | 0.005678 | 1.189 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | poultry | 禽肉 | 0.01071 | 0.008276 | 0.01727 | 0.62 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | aquatic | 水产品 | 0.00677 | 0.005168 | 0.01225 | 0.5525 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | pork | 猪肉 | 0.04267 | 0.03508 | 0.1059 | 0.403 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | milk | 奶类 | 0.003819 | 0.00309 | 0.009988 | 0.3823 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | egg | 蛋类 | 0.006727 | 0.005328 | 0.02003 | 0.3359 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | fruit | 水果 | 0.005839 | 0.004837 | 0.02209 | 0.2643 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | oil | 食用油 | 0.03136 | 0.02521 | 0.1273 | 0.2463 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | grain | 粮食/主粮 | 0.07755 | 0.05384 | 0.4123 | 0.1881 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | vegetable | 蔬菜 | 0.005133 | 0.003813 | 0.02956 | 0.1737 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 | 3.541 | 2.702 | 190.3 | 0.01861 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | mutton | 羊肉 | 0.007904 | 0.005007 | 0.006078 | 1.3 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | beef | 牛肉 | 0.006749 | 0.002846 | 0.005678 | 1.188 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | poultry | 禽肉 | 0.01053 | 0.008079 | 0.01727 | 0.6098 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | aquatic | 水产品 | 0.006818 | 0.005241 | 0.01225 | 0.5564 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | pork | 猪肉 | 0.04246 | 0.03446 | 0.1059 | 0.4009 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | milk | 奶类 | 0.003864 | 0.00312 | 0.009988 | 0.3869 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | egg | 蛋类 | 0.006665 | 0.005321 | 0.02003 | 0.3328 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | fruit | 水果 | 0.005947 | 0.004875 | 0.02209 | 0.2692 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | oil | 食用油 | 0.0323 | 0.02581 | 0.1273 | 0.2537 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | grain | 粮食/主粮 | 0.06945 | 0.05021 | 0.4123 | 0.1685 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | vegetable | 蔬菜 | 0.004963 | 0.003755 | 0.02956 | 0.1679 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 | 3.549 | 2.674 | 190.3 | 0.01865 |

### 异常检查

- 部分 MAIDADS 随机起点不可用或落入惩罚值，未被选为最终解：start_5(success=True, nll=1e+12), start_7(success=True, nll=1e+12), start_8(success=True, nll=1e+12), start_9(success=True, nll=1e+12)。
- 选中解梯度范数偏大：max grad_norm=140.8。
- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：beef, grain, oil。
- MAIDADS 部分食品相对 RMSE > 0.5：beef=1.19, mutton=1.30, poultry=0.61, aquatic=0.56。
- 收入弹性绝对值 > 5 的点：beef@10000=14.99, aquatic@10000=13.56。
- 出现正的 Marshallian 自价格弹性：grain。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 1.9002e-08 |
| max_abs_price_adding_up_error | 9.07168e-09 |
| max_abs_marshallian_homogeneity_error | 4.50099e-06 |
| max_abs_hicksian_homogeneity_error | 4.50099e-06 |
| max_abs_slutsky_symmetry_error | 8.41256e-09 |

## 输出文件

- `*__original_item_panel.csv`：原始品类估计面板。
- `*__parameter_estimates.csv`：AIDADS/MAIDADS 参数。
- `*__fit_by_group.csv`：分品类拟合误差。
- `*__model_comparison.csv`：AIC/BIC/LR 摘要；LR 不报告普通 chi-square p 值。
- `*__elasticity_income_grid.csv`：原始品类收入弹性。
- `*__elasticity_price_marshallian_grid.csv`、`*__elasticity_price_hicksian_grid.csv`：价格弹性。
- `*__elasticity_consistency_tests.csv`：加总、齐次性和 Slutsky 对称性检查。
- `*__parameter_boundary_report.csv`、`*__multistart_diagnostics.csv`：边界与优化诊断。