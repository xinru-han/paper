# 猪肉/水产品/奶类/蛋类拆分 MAIDADS/AIDADS 结果与异常检查

- 生成时间：2026-06-11T21:45:31
- 开始时间：2026-06-11T21:39:47
- 本轮不做 bootstrap。
- 分类：保留 `grain / oil / vegfruit / nonfood`；把 `meatsea` 拆为 `pork / aquatic / othermeat(牛羊禽)`；把 `dairyegg` 拆为 `milk / egg`。

## 模型品类

| group | label_cn | items |
| --- | --- | --- |
| grain | 粮食/主粮 | grain |
| oil | 食用油 | oil |
| vegfruit | 蔬菜水果 | vegetable+fruit |
| pork | 猪肉 | pork |
| aquatic | 水产品 | aquatic |
| othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry |
| milk | 奶类 | milk |
| egg | 蛋类 | egg |
| nonfood | 其他/未覆盖支出 |  |

## baseline_real_national_nonfood

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | -6216 | 19 | -1.239e+04 | -1.232e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.398 |  |  |
| baseline_real_national_nonfood | MAIDADS_sat | -6338 | 29 | -1.262e+04 | -1.251e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.378 |  |  |
| baseline_real_national_nonfood | LR_MAIDADS_vs_AIDADS |  | 10 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 245.2 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | aquatic | 水产品 | aquatic | 0.009493 | 0.007283 | 0.01209 | 0.7854 |
| baseline_real_national_nonfood | AIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01354 | 0.01062 | 0.02834 | 0.4776 |
| baseline_real_national_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.04696 | 0.03753 | 0.1037 | 0.4528 |
| baseline_real_national_nonfood | AIDADS_sat | egg | 蛋类 | egg | 0.008216 | 0.006354 | 0.01962 | 0.4188 |
| baseline_real_national_nonfood | AIDADS_sat | milk | 奶类 | milk | 0.004077 | 0.003236 | 0.01 | 0.4075 |
| baseline_real_national_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03155 | 0.02515 | 0.128 | 0.2465 |
| baseline_real_national_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01086 | 0.008057 | 0.05127 | 0.2118 |
| baseline_real_national_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07636 | 0.05329 | 0.4162 | 0.1835 |
| baseline_real_national_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.812 | 3.17 | 188.9 | 0.02018 |
| baseline_real_national_nonfood | MAIDADS_sat | aquatic | 水产品 | aquatic | 0.009116 | 0.007264 | 0.01209 | 0.7542 |
| baseline_real_national_nonfood | MAIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01313 | 0.01066 | 0.02834 | 0.4632 |
| baseline_real_national_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04416 | 0.03587 | 0.1037 | 0.4259 |
| baseline_real_national_nonfood | MAIDADS_sat | egg | 蛋类 | egg | 0.00771 | 0.006012 | 0.01962 | 0.393 |
| baseline_real_national_nonfood | MAIDADS_sat | milk | 奶类 | milk | 0.003877 | 0.003116 | 0.01 | 0.3875 |
| baseline_real_national_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03163 | 0.02576 | 0.128 | 0.2471 |
| baseline_real_national_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01017 | 0.007581 | 0.05127 | 0.1984 |
| baseline_real_national_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.06453 | 0.04922 | 0.4162 | 0.155 |
| baseline_real_national_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.833 | 3.114 | 188.9 | 0.02029 |

### 异常检查

- 部分 MAIDADS 随机起点不可用或落入惩罚值，未被选为最终解：start_1(success=False, nll=-6.22e+03)。
- 选中解梯度范数偏大：max grad_norm=2.763e+10。
- MAIDADS 部分食品相对 RMSE > 0.5：aquatic=0.75。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 7.11029e-09 |
| max_abs_price_adding_up_error | 2.90446e-10 |
| max_abs_marshallian_homogeneity_error | 4.56154e-08 |
| max_abs_hicksian_homogeneity_error | 4.56154e-08 |
| max_abs_slutsky_symmetry_error | 1.3964e-09 |

### 中位收入网格附近收入弹性：income=30000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.3836 | 0.009936 | in_support |
| oil | 食用油 | 0.01268 | 0.02242 | in_support |
| vegfruit | 蔬菜水果 | 0.06015 | 0.01486 | in_support |
| pork | 猪肉 | -0.0328 | 0.009624 | in_support |
| aquatic | 水产品 | -0.1164 | 0.003656 | in_support |
| othermeat | 其他肉类(牛羊禽) | -0.02581 | 0.01042 | in_support |
| milk | 奶类 | 0.05761 | 0.001237 | in_support |
| egg | 蛋类 | -0.09965 | 0.001735 | in_support |
| nonfood | 其他/未覆盖支出 | 1.084 | 0.9261 | in_support |

## robust_real_derived_cpi_nonfood

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | -6233 | 19 | -1.243e+04 | -1.236e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3948 |  |  |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | -6236 | 29 | -1.241e+04 | -1.231e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3947 |  |  |
| robust_real_derived_cpi_nonfood | LR_MAIDADS_vs_AIDADS |  | 10 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 6.973 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | aquatic | 水产品 | aquatic | 0.009331 | 0.007338 | 0.01209 | 0.772 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01334 | 0.01072 | 0.02834 | 0.4705 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.0464 | 0.03718 | 0.1037 | 0.4474 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | egg | 蛋类 | egg | 0.008231 | 0.006368 | 0.01962 | 0.4196 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | milk | 奶类 | milk | 0.00409 | 0.003247 | 0.01 | 0.4088 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03168 | 0.02492 | 0.128 | 0.2475 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01087 | 0.008099 | 0.05127 | 0.212 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07514 | 0.05171 | 0.4162 | 0.1805 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.757 | 3.113 | 187.4 | 0.02005 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | aquatic | 水产品 | aquatic | 0.009333 | 0.007389 | 0.01209 | 0.7721 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01328 | 0.01059 | 0.02834 | 0.4686 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04645 | 0.03701 | 0.1037 | 0.4479 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | egg | 蛋类 | egg | 0.008232 | 0.006362 | 0.01962 | 0.4196 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | milk | 奶类 | milk | 0.00412 | 0.003266 | 0.01 | 0.4118 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03163 | 0.02482 | 0.128 | 0.2471 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01087 | 0.008083 | 0.05127 | 0.2121 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.07414 | 0.05119 | 0.4162 | 0.1781 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.766 | 3.118 | 187.4 | 0.02009 |

### 异常检查

- 部分 MAIDADS 随机起点不可用或落入惩罚值，未被选为最终解：start_1(success=False, nll=-6.23e+03), start_3(success=False, nll=-6.23e+03), start_4(success=False, nll=-6.22e+03)。
- 选中解梯度范数偏大：max grad_norm=1.798e+09。
- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：aquatic。
- MAIDADS 部分食品相对 RMSE > 0.5：aquatic=0.77。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 1.81055e-08 |
| max_abs_price_adding_up_error | 2.30938e-09 |
| max_abs_marshallian_homogeneity_error | 1.37661e-07 |
| max_abs_hicksian_homogeneity_error | 1.37661e-07 |
| max_abs_slutsky_symmetry_error | 5.87347e-09 |

### 中位收入网格附近收入弹性：income=30000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.02622 | 0.01167 | in_support |
| oil | 食用油 | -0.01386 | 0.02129 | in_support |
| vegfruit | 蔬菜水果 | -0.001438 | 0.01425 | in_support |
| pork | 猪肉 | -0.139 | 0.009528 | in_support |
| aquatic | 水产品 | -0.1597 | 0.003361 | in_support |
| othermeat | 其他肉类(牛羊禽) | -0.02441 | 0.009842 | in_support |
| milk | 奶类 | -0.04452 | 0.001167 | in_support |
| egg | 蛋类 | -0.1494 | 0.001635 | in_support |
| nonfood | 其他/未覆盖支出 | 1.082 | 0.9273 | in_support |

## 输出文件

- `*__split_panel.csv`：拆分品类估计面板。
- `*__parameter_estimates.csv`：AIDADS/MAIDADS 参数。
- `*__fit_by_group.csv`：分品类拟合误差。
- `*__model_comparison.csv`：AIC/BIC/LR 摘要；LR 不报告普通 chi-square p 值。
- `*__elasticity_income_grid.csv`：拆分品类收入弹性。
- `*__elasticity_price_marshallian_grid.csv`、`*__elasticity_price_hicksian_grid.csv`：价格弹性。
- `*__elasticity_consistency_tests.csv`：加总、齐次性和 Slutsky 对称性检查。