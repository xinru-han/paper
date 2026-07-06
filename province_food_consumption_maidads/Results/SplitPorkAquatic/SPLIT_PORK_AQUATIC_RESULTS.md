# 猪肉/水产品拆分 MAIDADS/AIDADS 结果与异常检查

- 生成时间：2026-07-06T00:26:51
- 开始时间：2026-07-06T00:05:33
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
| baseline_real_national_nonfood | AIDADS_sat | -5544 | 17 | -1.105e+04 | -1.099e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3393 |  |  |
| baseline_real_national_nonfood | MAIDADS_sat | -5689 | 26 | -1.133e+04 | -1.123e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3328 |  |  |
| baseline_real_national_nonfood | LR_MAIDADS_vs_AIDADS |  | 9 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 290.6 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | aquatic | 水产品 | aquatic | 0.006964 | 0.005398 | 0.01225 | 0.5683 |
| baseline_real_national_nonfood | AIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01322 | 0.01067 | 0.02902 | 0.4556 |
| baseline_real_national_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.04355 | 0.03587 | 0.1059 | 0.4112 |
| baseline_real_national_nonfood | AIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008867 | 0.00711 | 0.03001 | 0.2954 |
| baseline_real_national_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03134 | 0.0253 | 0.1273 | 0.2461 |
| baseline_real_national_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01086 | 0.008031 | 0.05165 | 0.2103 |
| baseline_real_national_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07748 | 0.05385 | 0.4123 | 0.1879 |
| baseline_real_national_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.543 | 2.842 | 191.7 | 0.01848 |
| baseline_real_national_nonfood | MAIDADS_sat | aquatic | 水产品 | aquatic | 0.007094 | 0.005511 | 0.01225 | 0.5789 |
| baseline_real_national_nonfood | MAIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01376 | 0.01126 | 0.02902 | 0.4742 |
| baseline_real_national_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04247 | 0.03472 | 0.1059 | 0.401 |
| baseline_real_national_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.00878 | 0.007086 | 0.03001 | 0.2925 |
| baseline_real_national_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03151 | 0.02657 | 0.1273 | 0.2474 |
| baseline_real_national_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009304 | 0.007664 | 0.05165 | 0.1801 |
| baseline_real_national_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.06409 | 0.04884 | 0.4123 | 0.1555 |
| baseline_real_national_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.569 | 2.891 | 191.7 | 0.01862 |

### 异常检查

- 选中解梯度范数偏大：max grad_norm=298。
- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：aquatic, dairyegg, grain, oil, othermeat, vegfruit。
- MAIDADS 部分食品相对 RMSE > 0.5：aquatic=0.58。
- 出现正的 Marshallian 自价格弹性：grain, oil, othermeat。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 1.16752e-08 |
| max_abs_price_adding_up_error | 1.7997e-09 |
| max_abs_marshallian_homogeneity_error | 5.16613e-07 |
| max_abs_hicksian_homogeneity_error | 5.16613e-07 |
| max_abs_slutsky_symmetry_error | 3.92846e-09 |

### 中位收入网格附近收入弹性：income=30000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.3886 | 0.01008 | in_support |
| oil | 食用油 | -0.3747 | 0.01892 | in_support |
| vegfruit | 蔬菜水果 | 0.3811 | 0.0172 | in_support |
| pork | 猪肉 | 0.2819 | 0.01108 | in_support |
| aquatic | 水产品 | 0.5657 | 0.005441 | in_support |
| othermeat | 其他肉类(牛羊禽) | -0.3679 | 0.009318 | in_support |
| dairyegg | 奶蛋类 | 0.4639 | 0.003953 | in_support |
| nonfood | 其他/未覆盖支出 | 1.082 | 0.924 | in_support |

## robust_real_derived_cpi_nonfood

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | -5562 | 17 | -1.109e+04 | -1.103e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.335 |  |  |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | -5604 | 26 | -1.116e+04 | -1.106e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.333 |  |  |
| robust_real_derived_cpi_nonfood | LR_MAIDADS_vs_AIDADS |  | 9 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 84.6 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | aquatic | 水产品 | aquatic | 0.006693 | 0.005105 | 0.01225 | 0.5462 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01321 | 0.01059 | 0.02902 | 0.4552 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.04304 | 0.03534 | 0.1059 | 0.4064 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008782 | 0.007075 | 0.03001 | 0.2926 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03135 | 0.02525 | 0.1273 | 0.2462 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01086 | 0.008028 | 0.05165 | 0.2103 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07747 | 0.05384 | 0.4123 | 0.1879 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.49 | 2.782 | 190.3 | 0.01834 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | aquatic | 水产品 | aquatic | 0.006529 | 0.004892 | 0.01225 | 0.5328 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01325 | 0.01059 | 0.02902 | 0.4564 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04434 | 0.0356 | 0.1059 | 0.4187 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.009165 | 0.007375 | 0.03001 | 0.3054 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03152 | 0.02479 | 0.1273 | 0.2475 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01038 | 0.007734 | 0.05165 | 0.2009 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.06988 | 0.05013 | 0.4123 | 0.1695 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.495 | 2.781 | 190.3 | 0.01836 |

### 异常检查

- 部分 MAIDADS 随机起点不可用或落入惩罚值，未被选为最终解：start_5(success=True, nll=1e+12), start_6(success=True, nll=1e+12), start_9(success=True, nll=1e+12)。
- 选中解梯度范数偏大：max grad_norm=483.7。
- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：aquatic, grain, oil, othermeat, vegfruit。
- MAIDADS 部分食品相对 RMSE > 0.5：aquatic=0.53。
- 收入弹性绝对值 > 5 的点：aquatic@10000=6.36。
- 出现正的 Marshallian 自价格弹性：grain, oil, othermeat。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 2.57021e-09 |
| max_abs_price_adding_up_error | 2.09701e-10 |
| max_abs_marshallian_homogeneity_error | 1.62225e-07 |
| max_abs_hicksian_homogeneity_error | 1.62225e-07 |
| max_abs_slutsky_symmetry_error | 3.99758e-10 |

### 中位收入网格附近收入弹性：income=30000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.1116 | 0.01097 | in_support |
| oil | 食用油 | -0.002011 | 0.02141 | in_support |
| vegfruit | 蔬菜水果 | 0.04694 | 0.01467 | in_support |
| pork | 猪肉 | 0.6257 | 0.01254 | in_support |
| aquatic | 水产品 | 0.8816 | 0.006364 | in_support |
| othermeat | 其他肉类(牛羊禽) | -0.04824 | 0.01011 | in_support |
| dairyegg | 奶蛋类 | 0.3627 | 0.003555 | in_support |
| nonfood | 其他/未覆盖支出 | 1.072 | 0.9204 | in_support |

## 输出文件

- `*__split_panel.csv`：拆分品类估计面板。
- `*__parameter_estimates.csv`：AIDADS/MAIDADS 参数。
- `*__fit_by_group.csv`：分品类拟合误差。
- `*__model_comparison.csv`：AIC/BIC/LR 摘要；LR 不报告普通 chi-square p 值。
- `*__elasticity_income_grid.csv`：拆分品类收入弹性。
- `*__elasticity_price_marshallian_grid.csv`、`*__elasticity_price_hicksian_grid.csv`：价格弹性。
- `*__elasticity_consistency_tests.csv`：加总、齐次性和 Slutsky 对称性检查。