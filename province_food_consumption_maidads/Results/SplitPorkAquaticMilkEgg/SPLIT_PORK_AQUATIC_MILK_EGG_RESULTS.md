# 猪肉/水产品/奶类/蛋类拆分 MAIDADS/AIDADS 结果与异常检查

- 生成时间：2026-07-06T01:00:08
- 开始时间：2026-07-06T00:26:52
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
| baseline_real_national_nonfood | AIDADS_sat | -6913 | 19 | -1.379e+04 | -1.372e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3917 |  |  |
| baseline_real_national_nonfood | MAIDADS_sat | -6954 | 29 | -1.385e+04 | -1.374e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3883 |  |  |
| baseline_real_national_nonfood | LR_MAIDADS_vs_AIDADS |  | 10 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 82.11 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | aquatic | 水产品 | aquatic | 0.009454 | 0.007312 | 0.01225 | 0.7715 |
| baseline_real_national_nonfood | AIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01356 | 0.01065 | 0.02902 | 0.4673 |
| baseline_real_national_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.04708 | 0.0376 | 0.1059 | 0.4446 |
| baseline_real_national_nonfood | AIDADS_sat | egg | 蛋类 | egg | 0.008253 | 0.006412 | 0.02003 | 0.4121 |
| baseline_real_national_nonfood | AIDADS_sat | milk | 奶类 | milk | 0.004035 | 0.003189 | 0.009988 | 0.4039 |
| baseline_real_national_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03133 | 0.02511 | 0.1273 | 0.246 |
| baseline_real_national_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01087 | 0.008024 | 0.05165 | 0.2104 |
| baseline_real_national_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07341 | 0.05137 | 0.4123 | 0.1781 |
| baseline_real_national_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.739 | 3.098 | 191.7 | 0.0195 |
| baseline_real_national_nonfood | MAIDADS_sat | aquatic | 水产品 | aquatic | 0.009594 | 0.007896 | 0.01225 | 0.7829 |
| baseline_real_national_nonfood | MAIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01346 | 0.01097 | 0.02902 | 0.4637 |
| baseline_real_national_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04639 | 0.03713 | 0.1059 | 0.438 |
| baseline_real_national_nonfood | MAIDADS_sat | egg | 蛋类 | egg | 0.008251 | 0.006427 | 0.02003 | 0.412 |
| baseline_real_national_nonfood | MAIDADS_sat | milk | 奶类 | milk | 0.003947 | 0.003138 | 0.009988 | 0.3951 |
| baseline_real_national_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03154 | 0.02489 | 0.1273 | 0.2477 |
| baseline_real_national_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01049 | 0.007741 | 0.05165 | 0.2032 |
| baseline_real_national_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.06766 | 0.04846 | 0.4123 | 0.1641 |
| baseline_real_national_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.721 | 3.034 | 191.7 | 0.01941 |

### 异常检查

- 部分 MAIDADS 随机起点不可用或落入惩罚值，未被选为最终解：start_1(success=False, nll=-6.91e+03), start_4(success=False, nll=-6.94e+03), start_5(success=False, nll=-6.91e+03), start_6(success=False, nll=-6.93e+03)。
- 选中解梯度范数偏大：max grad_norm=2.399e+09。
- MAIDADS 部分食品相对 RMSE > 0.5：aquatic=0.78。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 1.91787e-08 |
| max_abs_price_adding_up_error | 2.67422e-09 |
| max_abs_marshallian_homogeneity_error | 1.7154e-07 |
| max_abs_hicksian_homogeneity_error | 1.7154e-07 |
| max_abs_slutsky_symmetry_error | 5.37449e-09 |

### 中位收入网格附近收入弹性：income=30000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.1051 | 0.01129 | in_support |
| oil | 食用油 | 0.006981 | 0.02158 | in_support |
| vegfruit | 蔬菜水果 | 0.03507 | 0.01491 | in_support |
| pork | 猪肉 | -0.08117 | 0.009496 | in_support |
| aquatic | 水产品 | -0.1549 | 0.003947 | in_support |
| othermeat | 其他肉类(牛羊禽) | -0.02327 | 0.01073 | in_support |
| milk | 奶类 | 0.01827 | 0.001277 | in_support |
| egg | 蛋类 | -0.1423 | 0.001776 | in_support |
| nonfood | 其他/未覆盖支出 | 1.084 | 0.925 | in_support |

## robust_real_derived_cpi_nonfood

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | -6930 | 19 | -1.382e+04 | -1.375e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3905 |  |  |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | -7193 | 29 | -1.433e+04 | -1.422e+04 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.3399 |  |  |
| robust_real_derived_cpi_nonfood | LR_MAIDADS_vs_AIDADS |  | 10 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 525.9 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | aquatic | 水产品 | aquatic | 0.009419 | 0.00733 | 0.01225 | 0.7686 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.0135 | 0.01071 | 0.02902 | 0.4652 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.04667 | 0.0374 | 0.1059 | 0.4407 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | egg | 蛋类 | egg | 0.008267 | 0.006439 | 0.02003 | 0.4128 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | milk | 奶类 | milk | 0.004018 | 0.003181 | 0.009988 | 0.4023 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03145 | 0.02486 | 0.1273 | 0.2469 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.01086 | 0.008009 | 0.05165 | 0.2104 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07294 | 0.05094 | 0.4123 | 0.1769 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.711 | 3.076 | 190.3 | 0.0195 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | aquatic | 水产品 | aquatic | 0.007193 | 0.005575 | 0.01225 | 0.587 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | othermeat | 其他肉类(牛羊禽) | beef+mutton+poultry | 0.01366 | 0.0112 | 0.02902 | 0.4706 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04278 | 0.0344 | 0.1059 | 0.404 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | milk | 奶类 | milk | 0.003663 | 0.002935 | 0.009988 | 0.3667 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | egg | 蛋类 | egg | 0.00627 | 0.004851 | 0.02003 | 0.3131 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03144 | 0.02641 | 0.1273 | 0.2469 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009009 | 0.00731 | 0.05165 | 0.1744 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.06448 | 0.04868 | 0.4123 | 0.1564 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.474 | 2.807 | 190.3 | 0.01826 |

### 异常检查

- 部分 MAIDADS 随机起点不可用或落入惩罚值，未被选为最终解：start_2(success=False, nll=-6.93e+03), start_3(success=False, nll=-6.93e+03), start_5(success=False, nll=-6.96e+03)。
- 选中解梯度范数偏大：max grad_norm=268.2。
- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：milk, vegfruit。
- MAIDADS 部分食品相对 RMSE > 0.5：aquatic=0.59。
- 收入弹性绝对值 > 5 的点：aquatic@10000=5.15。
- 出现正的 Marshallian 自价格弹性：grain, oil, othermeat。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 1.4189e-08 |
| max_abs_price_adding_up_error | 2.78234e-09 |
| max_abs_marshallian_homogeneity_error | 5.96393e-07 |
| max_abs_hicksian_homogeneity_error | 5.96393e-07 |
| max_abs_slutsky_symmetry_error | 4.06205e-09 |

### 中位收入网格附近收入弹性：income=30000

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.3475 | 0.0101 | in_support |
| oil | 食用油 | -0.3456 | 0.01905 | in_support |
| vegfruit | 蔬菜水果 | 0.3175 | 0.01695 | in_support |
| pork | 猪肉 | 0.4075 | 0.01208 | in_support |
| aquatic | 水产品 | 0.4686 | 0.005266 | in_support |
| othermeat | 其他肉类(牛羊禽) | -0.2539 | 0.009844 | in_support |
| milk | 奶类 | 0.3127 | 0.001452 | in_support |
| egg | 蛋类 | 0.4499 | 0.002409 | in_support |
| nonfood | 其他/未覆盖支出 | 1.082 | 0.9228 | in_support |

## 输出文件

- `*__split_panel.csv`：拆分品类估计面板。
- `*__parameter_estimates.csv`：AIDADS/MAIDADS 参数。
- `*__fit_by_group.csv`：分品类拟合误差。
- `*__model_comparison.csv`：AIC/BIC/LR 摘要；LR 不报告普通 chi-square p 值。
- `*__elasticity_income_grid.csv`：拆分品类收入弹性。
- `*__elasticity_price_marshallian_grid.csv`、`*__elasticity_price_hicksian_grid.csv`：价格弹性。
- `*__elasticity_consistency_tests.csv`：加总、齐次性和 Slutsky 对称性检查。