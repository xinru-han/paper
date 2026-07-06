# 猪肉/水产品拆分 MAIDADS/AIDADS 结果与异常检查：人均 GDP 口径

- 生成时间：2026-06-11T22:59:45
- 开始时间：2026-06-11T22:41:03
- 本轮不做 bootstrap。
- 本轮把模型预算变量 `m` 从实际人均消费支出改为实际人均 GDP：`m = pgdp / monetary_deflator`。
- 注意：MAIDADS 理论中的 `m` 是预算/总支出变量；本轮是把人均 GDP 作为尺度变量的敏感性试验。
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
| baseline_real_national_nonfood | AIDADS_sat | -5010 | 17 | -9986 | -9924 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3445 |  |  |
| baseline_real_national_nonfood | MAIDADS_sat | -5095 | 26 | -1.014e+04 | -1.004e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3355 |  |  |
| baseline_real_national_nonfood | LR_MAIDADS_vs_AIDADS |  | 9 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 169.5 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | aquatic | 水产品 | aquatic | 0.007156 | 0.005478 | 0.01209 | 0.5921 |
| baseline_real_national_nonfood | AIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01301 | 0.01048 | 0.02834 | 0.4591 |
| baseline_real_national_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.04349 | 0.03559 | 0.1037 | 0.4194 |
| baseline_real_national_nonfood | AIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008743 | 0.007061 | 0.02962 | 0.2952 |
| baseline_real_national_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03149 | 0.02556 | 0.128 | 0.246 |
| baseline_real_national_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01084 | 0.008019 | 0.05127 | 0.2114 |
| baseline_real_national_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07836 | 0.05428 | 0.4162 | 0.1883 |
| baseline_real_national_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.586 | 2.886 | 673.7 | 0.005323 |
| baseline_real_national_nonfood | MAIDADS_sat | aquatic | 水产品 | aquatic | 0.006963 | 0.005292 | 0.01209 | 0.5761 |
| baseline_real_national_nonfood | MAIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01303 | 0.0105 | 0.02834 | 0.4597 |
| baseline_real_national_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04301 | 0.03533 | 0.1037 | 0.4148 |
| baseline_real_national_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008681 | 0.007105 | 0.02962 | 0.293 |
| baseline_real_national_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03144 | 0.02596 | 0.128 | 0.2456 |
| baseline_real_national_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009667 | 0.007411 | 0.05127 | 0.1885 |
| baseline_real_national_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.07093 | 0.05005 | 0.4162 | 0.1704 |
| baseline_real_national_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.605 | 2.905 | 673.7 | 0.005351 |

### 异常检查

- 部分 MAIDADS 随机起点不可用或落入惩罚值，未被选为最终解：start_2(success=False, nll=-5.12e+03), start_4(success=False, nll=-5.12e+03)。
- 选中解梯度范数偏大：max grad_norm=4.158。
- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：aquatic, grain, oil, othermeat, pork。
- MAIDADS 部分食品相对 RMSE > 0.5：aquatic=0.58。
- 出现正的 Marshallian 自价格弹性：grain, oil。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 7.142e-10 |
| max_abs_price_adding_up_error | 8.48225e-11 |
| max_abs_marshallian_homogeneity_error | 8.76917e-08 |
| max_abs_hicksian_homogeneity_error | 8.76917e-08 |
| max_abs_slutsky_symmetry_error | 1.92984e-10 |

### 中位收入网格附近收入弹性：income=56762

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.2523 | 0.006386 | in_support |
| oil | 食用油 | -0.1308 | 0.01195 | in_support |
| vegfruit | 蔬菜水果 | 0.2682 | 0.007544 | in_support |
| pork | 猪肉 | 0.4041 | 0.004684 | in_support |
| aquatic | 水产品 | 1.165 | 0.001856 | in_support |
| othermeat | 其他肉类(牛羊禽) | -0.01225 | 0.005504 | in_support |
| dairyegg | 奶蛋类 | 0.5361 | 0.001556 | in_support |
| nonfood | 其他/未覆盖支出 | 1.037 | 0.9605 | in_support |

## robust_real_derived_cpi_nonfood

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | -5054 | 17 | -1.007e+04 | -1.001e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3391 |  |  |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | -5129 | 26 | -1.021e+04 | -1.011e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3336 |  |  |
| robust_real_derived_cpi_nonfood | LR_MAIDADS_vs_AIDADS |  | 9 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 149.7 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | aquatic | 水产品 | aquatic | 0.007145 | 0.005472 | 0.01209 | 0.5911 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.013 | 0.01042 | 0.02834 | 0.4587 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.04344 | 0.03557 | 0.1037 | 0.4189 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008383 | 0.006942 | 0.02962 | 0.283 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03149 | 0.02562 | 0.128 | 0.246 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07836 | 0.05419 | 0.4162 | 0.1883 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009608 | 0.007306 | 0.05127 | 0.1874 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.616 | 2.918 | 668.5 | 0.00541 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | aquatic | 水产品 | aquatic | 0.007111 | 0.005556 | 0.01209 | 0.5884 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01294 | 0.01028 | 0.02834 | 0.4567 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04229 | 0.03396 | 0.1037 | 0.4078 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008381 | 0.006911 | 0.02962 | 0.2829 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03124 | 0.02561 | 0.128 | 0.2441 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009482 | 0.007227 | 0.05127 | 0.1849 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.07086 | 0.04896 | 0.4162 | 0.1703 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.568 | 2.877 | 668.5 | 0.005338 |

### 异常检查

- 部分 MAIDADS 随机起点不可用或落入惩罚值，未被选为最终解：start_3(success=False, nll=-5.13e+03)。
- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：aquatic, grain, oil, othermeat, pork。
- MAIDADS 部分食品相对 RMSE > 0.5：aquatic=0.59。
- 出现正的 Marshallian 自价格弹性：grain, oil。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 1.69136e-09 |
| max_abs_price_adding_up_error | 2.45167e-10 |
| max_abs_marshallian_homogeneity_error | 9.17031e-09 |
| max_abs_hicksian_homogeneity_error | 9.17031e-09 |
| max_abs_slutsky_symmetry_error | 3.59448e-10 |

### 中位收入网格附近收入弹性：income=56762

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.2239 | 0.006401 | in_support |
| oil | 食用油 | -0.1178 | 0.0119 | in_support |
| vegfruit | 蔬菜水果 | 0.2321 | 0.007713 | in_support |
| pork | 猪肉 | 0.2545 | 0.005394 | in_support |
| aquatic | 水产品 | 1.216 | 0.001725 | in_support |
| othermeat | 其他肉类(牛羊禽) | 0.07254 | 0.005351 | in_support |
| dairyegg | 奶蛋类 | 0.5102 | 0.001584 | in_support |
| nonfood | 其他/未覆盖支出 | 1.038 | 0.9599 | in_support |

## 输出文件

- `*__split_panel.csv`：拆分品类估计面板。
- `*__parameter_estimates.csv`：AIDADS/MAIDADS 参数。
- `*__fit_by_group.csv`：分品类拟合误差。
- `*__model_comparison.csv`：AIC/BIC/LR 摘要；LR 不报告普通 chi-square p 值。
- `*__elasticity_income_grid.csv`：拆分品类收入弹性。
- `*__elasticity_price_marshallian_grid.csv`、`*__elasticity_price_hicksian_grid.csv`：价格弹性。
- `*__elasticity_consistency_tests.csv`：加总、齐次性和 Slutsky 对称性检查。