# 猪肉/水产品拆分 MAIDADS/AIDADS 结果与异常检查：人均 GDP 口径

- 生成时间：2026-07-06T03:15:07
- 开始时间：2026-07-06T01:48:20
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
| baseline_real_national_nonfood | AIDADS_sat | -5542 | 17 | -1.105e+04 | -1.099e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3444 |  |  |
| baseline_real_national_nonfood | MAIDADS_sat | -5654 | 26 | -1.126e+04 | -1.116e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3355 |  |  |
| baseline_real_national_nonfood | LR_MAIDADS_vs_AIDADS |  | 9 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 224.6 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | aquatic | 水产品 | aquatic | 0.007278 | 0.005615 | 0.01225 | 0.5939 |
| baseline_real_national_nonfood | AIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01322 | 0.01065 | 0.02902 | 0.4555 |
| baseline_real_national_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.04442 | 0.03618 | 0.1059 | 0.4194 |
| baseline_real_national_nonfood | AIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008932 | 0.007228 | 0.03001 | 0.2976 |
| baseline_real_national_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03134 | 0.02532 | 0.1273 | 0.2461 |
| baseline_real_national_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01086 | 0.008025 | 0.05165 | 0.2103 |
| baseline_real_national_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07746 | 0.05386 | 0.4123 | 0.1879 |
| baseline_real_national_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.552 | 2.873 | 683.8 | 0.005194 |
| baseline_real_national_nonfood | MAIDADS_sat | aquatic | 水产品 | aquatic | 0.007126 | 0.005574 | 0.01225 | 0.5815 |
| baseline_real_national_nonfood | MAIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01313 | 0.0105 | 0.02902 | 0.4523 |
| baseline_real_national_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04352 | 0.03501 | 0.1059 | 0.411 |
| baseline_real_national_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008866 | 0.007264 | 0.03001 | 0.2954 |
| baseline_real_national_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03108 | 0.02547 | 0.1273 | 0.2441 |
| baseline_real_national_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01003 | 0.00767 | 0.05165 | 0.1942 |
| baseline_real_national_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.07001 | 0.04927 | 0.4123 | 0.1698 |
| baseline_real_national_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.556 | 2.88 | 683.8 | 0.0052 |

### 异常检查

- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：aquatic, grain, oil, othermeat, vegfruit。
- MAIDADS 部分食品相对 RMSE > 0.5：aquatic=0.58。
- 出现正的 Marshallian 自价格弹性：grain, oil。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 1.77258e-09 |
| max_abs_price_adding_up_error | 2.38308e-10 |
| max_abs_marshallian_homogeneity_error | 1.41084e-08 |
| max_abs_hicksian_homogeneity_error | 1.41084e-08 |
| max_abs_slutsky_symmetry_error | 3.61686e-10 |

### 中位收入网格附近收入弹性：income=58111

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.2536 | 0.006186 | in_support |
| oil | 食用油 | -0.1323 | 0.01154 | in_support |
| vegfruit | 蔬菜水果 | 0.2417 | 0.007273 | in_support |
| pork | 猪肉 | 0.2358 | 0.005095 | in_support |
| aquatic | 水产品 | 1.384 | 0.001694 | in_support |
| othermeat | 其他肉类(牛羊禽) | 0.1074 | 0.005378 | in_support |
| dairyegg | 奶蛋类 | 0.5126 | 0.00153 | in_support |
| nonfood | 其他/未覆盖支出 | 1.037 | 0.9613 | in_support |

## robust_real_derived_cpi_nonfood

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | -5552 | 17 | -1.107e+04 | -1.101e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3442 |  |  |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | -5677 | 26 | -1.13e+04 | -1.121e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3333 |  |  |
| robust_real_derived_cpi_nonfood | LR_MAIDADS_vs_AIDADS |  | 9 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 251.5 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | aquatic | 水产品 | aquatic | 0.007273 | 0.005612 | 0.01225 | 0.5935 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01322 | 0.01063 | 0.02902 | 0.4554 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.04438 | 0.0361 | 0.1059 | 0.419 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008921 | 0.007219 | 0.03001 | 0.2972 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03135 | 0.02522 | 0.1273 | 0.2462 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01086 | 0.008031 | 0.05165 | 0.2103 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07748 | 0.05383 | 0.4123 | 0.1879 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.519 | 2.848 | 679 | 0.005182 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | aquatic | 水产品 | aquatic | 0.007235 | 0.005661 | 0.01225 | 0.5904 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01312 | 0.01042 | 0.02902 | 0.4521 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04349 | 0.03487 | 0.1059 | 0.4106 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008506 | 0.007014 | 0.03001 | 0.2834 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03103 | 0.0254 | 0.1273 | 0.2437 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009463 | 0.007227 | 0.05165 | 0.1832 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.06985 | 0.04881 | 0.4123 | 0.1694 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.551 | 2.878 | 679 | 0.00523 |

### 异常检查

- 选中解梯度范数偏大：max grad_norm=2.554。
- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：aquatic, grain, oil, othermeat, pork。
- MAIDADS 部分食品相对 RMSE > 0.5：aquatic=0.59。
- 出现正的 Marshallian 自价格弹性：grain, oil。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 1.69384e-09 |
| max_abs_price_adding_up_error | 2.42499e-10 |
| max_abs_marshallian_homogeneity_error | 9.37904e-09 |
| max_abs_hicksian_homogeneity_error | 9.37904e-09 |
| max_abs_slutsky_symmetry_error | 3.56588e-10 |

### 中位收入网格附近收入弹性：income=58111

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.2293 | 0.006173 | in_support |
| oil | 食用油 | -0.1278 | 0.01153 | in_support |
| vegfruit | 蔬菜水果 | 0.228 | 0.007591 | in_support |
| pork | 猪肉 | 0.2254 | 0.005224 | in_support |
| aquatic | 水产品 | 1.202 | 0.001727 | in_support |
| othermeat | 其他肉类(牛羊禽) | 0.1044 | 0.005311 | in_support |
| dairyegg | 奶蛋类 | 0.4978 | 0.001563 | in_support |
| nonfood | 其他/未覆盖支出 | 1.037 | 0.9609 | in_support |

## 输出文件

- `*__split_panel.csv`：拆分品类估计面板。
- `*__parameter_estimates.csv`：AIDADS/MAIDADS 参数。
- `*__fit_by_group.csv`：分品类拟合误差。
- `*__model_comparison.csv`：AIC/BIC/LR 摘要；LR 不报告普通 chi-square p 值。
- `*__elasticity_income_grid.csv`：拆分品类收入弹性。
- `*__elasticity_price_marshallian_grid.csv`、`*__elasticity_price_hicksian_grid.csv`：价格弹性。
- `*__elasticity_consistency_tests.csv`：加总、齐次性和 Slutsky 对称性检查。