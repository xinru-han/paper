# 猪肉拆分 MAIDADS/AIDADS 结果与异常检查：人均 GDP 预算口径

- 生成时间：2026-07-06T01:48:19
- 开始时间：2026-07-06T01:00:09
- 本轮不做 bootstrap。
- 本轮把模型预算变量 `m` 从实际人均消费支出改为实际人均 GDP：`m = pgdp / monetary_deflator`。
- 注意：此设定模仿 Gouel-Guimbard 原文的人均 GDP 预算尺度；但省级 household demand 解释应谨慎，因为 `nonfood` residual 变成 `人均 GDP - covered food expenditure`。
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

### m 口径描述

| index | count | mean | std | min | 5% | 25% | 50% | 75% | 95% | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| m | 310 | 68076 | 30754.4 | 29310.6 | 37877.4 | 47585.4 | 58111.2 | 78846.2 | 138569 | 184841 |
| m_consumption_real | 310 | 20783.7 | 7227.42 | 9341.54 | 13675.1 | 16193 | 18427 | 22607 | 39547.7 | 45592.9 |
| pgdp_nominal | 310 | 64865.5 | 30158.3 | 25946 | 33853.7 | 44453.9 | 56007.7 | 76658.9 | 130231 | 185026 |
| covered_food_exp_split | 310 | 2384.22 | 395.434 | 1597.62 | 1827.6 | 2077.46 | 2372.28 | 2652.87 | 3061.65 | 3940.11 |
| nonfood_exp_split | 310 | 65691.8 | 30721.1 | 26870.4 | 35830.7 | 45037.2 | 55797.2 | 76556 | 136351 | 183003 |

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | -4341 | 15 | -8651 | -8595 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2903 |  |  |
| baseline_real_national_nonfood | MAIDADS_sat | -4428 | 23 | -8810 | -8724 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2802 |  |  |
| baseline_real_national_nonfood | LR_MAIDADS_vs_AIDADS |  | 8 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 174.7 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_real_national_nonfood | AIDADS_sat | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic | 0.01765 | 0.01406 | 0.04128 | 0.4275 |
| baseline_real_national_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.04407 | 0.03578 | 0.1059 | 0.4161 |
| baseline_real_national_nonfood | AIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008394 | 0.007004 | 0.03001 | 0.2797 |
| baseline_real_national_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03135 | 0.02553 | 0.1273 | 0.2462 |
| baseline_real_national_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.07746 | 0.05394 | 0.4123 | 0.1879 |
| baseline_real_national_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009512 | 0.007254 | 0.05165 | 0.1842 |
| baseline_real_national_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.596 | 2.915 | 683.8 | 0.005259 |
| baseline_real_national_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04332 | 0.03489 | 0.1059 | 0.4091 |
| baseline_real_national_nonfood | MAIDADS_sat | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic | 0.01624 | 0.01246 | 0.04128 | 0.3933 |
| baseline_real_national_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008499 | 0.007043 | 0.03001 | 0.2832 |
| baseline_real_national_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03105 | 0.0255 | 0.1273 | 0.2438 |
| baseline_real_national_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009457 | 0.007225 | 0.05165 | 0.1831 |
| baseline_real_national_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.06951 | 0.04872 | 0.4123 | 0.1686 |
| baseline_real_national_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.586 | 2.899 | 683.8 | 0.005244 |

### 异常检查

- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：dairyegg, nonpork_meatsea, oil。
- 出现正的 Marshallian 自价格弹性：oil。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 7.32417e-10 |
| max_abs_price_adding_up_error | 1.27205e-10 |
| max_abs_marshallian_homogeneity_error | 1.7681e-08 |
| max_abs_hicksian_homogeneity_error | 1.7681e-08 |
| max_abs_slutsky_symmetry_error | 1.50968e-10 |

### 中位收入网格附近收入弹性：income=58111

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.237 | 0.00622 | in_support |
| oil | 食用油 | -0.1197 | 0.01156 | in_support |
| vegfruit | 蔬菜水果 | 0.2337 | 0.007568 | in_support |
| pork | 猪肉 | 0.2569 | 0.005038 | in_support |
| nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.4384 | 0.007147 | in_support |
| dairyegg | 奶蛋类 | 0.4855 | 0.001584 | in_support |
| nonfood | 其他/未覆盖支出 | 1.036 | 0.9609 | in_support |

## robust_real_derived_cpi_nonfood

### m 口径描述

| index | count | mean | std | min | 5% | 25% | 50% | 75% | 95% | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| m | 310 | 68076 | 30754.4 | 29310.6 | 37877.4 | 47585.4 | 58111.2 | 78846.2 | 138569 | 184841 |
| m_consumption_real | 310 | 20783.7 | 7227.42 | 9341.54 | 13675.1 | 16193 | 18427 | 22607 | 39547.7 | 45592.9 |
| pgdp_nominal | 310 | 64865.5 | 30158.3 | 25946 | 33853.7 | 44453.9 | 56007.7 | 76658.9 | 130231 | 185026 |
| covered_food_exp_split | 310 | 2384.22 | 395.434 | 1597.62 | 1827.6 | 2077.46 | 2372.28 | 2652.87 | 3061.65 | 3940.11 |
| nonfood_exp_split | 310 | 65691.8 | 30721.1 | 26870.4 | 35830.7 | 45037.2 | 55797.2 | 76556 | 136351 | 183003 |

### 模型比较

| variant | model | nll | k_effective | aic | bic | success | message | mean_food_relative_rmse | lr_stat | chi2_p_value_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | -4370 | 15 | -8709 | -8653 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2877 |  |  |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | -4439 | 23 | -8832 | -8746 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.2801 |  |  |
| robust_real_derived_cpi_nonfood | LR_MAIDADS_vs_AIDADS |  | 8 |  |  | True | Naive chi-square p-value not reported; nuisance parameters unidentified under AIDADS. |  | 138.7 | invalid_not_reported_unidentified_nuisance_under_H0 |

### 分品类拟合误差

| variant | model | group | group_label_cn | items | rmse_x | mae_x | mean_x | relative_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_real_derived_cpi_nonfood | AIDADS_sat | pork | 猪肉 | pork | 0.04422 | 0.03591 | 0.1059 | 0.4175 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic | 0.01659 | 0.01304 | 0.04128 | 0.4019 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008651 | 0.007199 | 0.03001 | 0.2882 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | oil | 食用油 | oil | 0.03134 | 0.02537 | 0.1273 | 0.2461 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | grain | 粮食/主粮 | grain | 0.0775 | 0.05385 | 0.4123 | 0.188 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009514 | 0.00727 | 0.05165 | 0.1842 |
| robust_real_derived_cpi_nonfood | AIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.602 | 2.921 | 679 | 0.005305 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | pork | 猪肉 | pork | 0.04322 | 0.03475 | 0.1059 | 0.4081 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | beef+mutton+poultry+aquatic | 0.01626 | 0.01248 | 0.04128 | 0.3938 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | dairyegg | 奶蛋类 | milk+egg | 0.008499 | 0.007045 | 0.03001 | 0.2832 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | oil | 食用油 | oil | 0.03105 | 0.02544 | 0.1273 | 0.2438 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | vegfruit | 蔬菜水果 | vegetable+fruit | 0.009456 | 0.007234 | 0.05165 | 0.1831 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | grain | 粮食/主粮 | grain | 0.06956 | 0.04857 | 0.4123 | 0.1687 |
| robust_real_derived_cpi_nonfood | MAIDADS_sat | nonfood | 其他/未覆盖支出 |  | 3.555 | 2.879 | 679 | 0.005236 |

### 异常检查

- 部分 MAIDADS 随机起点不可用或落入惩罚值，未被选为最终解：start_9(success=True, nll=1e+12), start_10(success=True, nll=1e+12)。
- 选中解梯度范数偏大：max grad_norm=7.294。
- MAIDADS 存在贴近下边界的 alpha/delta/tau 参数：dairyegg, nonpork_meatsea, oil。
- 出现正的 Marshallian 自价格弹性：oil。

### 弹性一致性最大误差

| check | max_abs_error |
| --- | --- |
| adding_up_income_error | 7.745e-10 |
| max_abs_price_adding_up_error | 1.25435e-10 |
| max_abs_marshallian_homogeneity_error | 1.96888e-08 |
| max_abs_hicksian_homogeneity_error | 1.96888e-08 |
| max_abs_slutsky_symmetry_error | 1.63744e-10 |

### 中位收入网格附近收入弹性：income=58111

| group | group_label_cn | quantity_2000kcal_elasticity | budget_share | support_flag |
| --- | --- | --- | --- | --- |
| grain | 粮食/主粮 | -0.2282 | 0.0062 | in_support |
| oil | 食用油 | -0.1209 | 0.0115 | in_support |
| vegfruit | 蔬菜水果 | 0.2373 | 0.007561 | in_support |
| pork | 猪肉 | 0.2541 | 0.005049 | in_support |
| nonpork_meatsea | 非猪肉肉类及水产品(牛羊禽水产) | 0.4052 | 0.007151 | in_support |
| dairyegg | 奶蛋类 | 0.5007 | 0.001578 | in_support |
| nonfood | 其他/未覆盖支出 | 1.037 | 0.961 | in_support |

## 输出文件

- `*__split_panel.csv`：拆分品类估计面板。
- `*__parameter_estimates.csv`：AIDADS/MAIDADS 参数。
- `*__fit_by_group.csv`：分品类拟合误差。
- `*__model_comparison.csv`：AIC/BIC/LR 摘要；LR 不报告普通 chi-square p 值。
- `*__elasticity_income_grid.csv`：拆分品类收入弹性。
- `*__elasticity_price_marshallian_grid.csv`、`*__elasticity_price_hicksian_grid.csv`：价格弹性。
- `*__elasticity_consistency_tests.csv`：加总、齐次性和 Slutsky 对称性检查。