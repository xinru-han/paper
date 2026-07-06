# 省级食物消费 MAIDADS — 2015–2024 更新说明 (README)

本文件记录将省级（31 省）MAIDADS 需求系统从 **2015–2023（279 省-年）** 延伸到
**2015–2024（310 省-年 = 31 省 × 10 年）** 的全部数据构建、口径、方法与结果变更。
更新采用 **7 组拆猪（split-pork）** 设定，全流程以 Python 复算。

---

## 1. 数据构建与更新

### 1.1 面板延伸（2024 新增年份）
- **消费数量**：`食物消费.xlsx`（宽表，EMIS/Wind 导出，401 列，省×指标序列；
  前 6 行为元数据，其后为年度值）。2024 值来自该表 2024 行。
- **收入 / 支出 / 人均 GDP**：2015–2023 沿用原始序列；2024 人均 GDP 用
  实际增速链式外推（chain-linked on real growth），并入面板 `pgdp`。
- **价格（主口径）**：见 §1.2。
- **人口（投影用）**：省级 SSP2 中间路径；2030=1,460,500,427，
  2035=1,453,583,009，2050=1,394,764,799 人。

### 1.2 价格口径
- **主口径（MAIN）**：城市食品价格监测（源2）。除粮食外全部食品项 2024 取
  Jan–May 5 个月均值；粮食单列（见下）。CRE（源1）在主口径中弃置（set aside）。
- **粮食价格**：成品粮零售监测（成品粮零售），2024 = Jan–May 5 个月均值；
  grain_growth 均值 +0.09%，区间 −2.6% ~ +5.4%，西藏 = 1.0000。
- **平减基年**：base_year = 2023（管线内部平减器归一化到 2023=100，正确链接到 2024）。
- **稳健性口径（Robustness）**：以 CPI 非食品分项（derived provincial non-food CPI）
  平减残差价格。

### 1.3 data.dta 重建
- Python 写出 `ProvinceData/workdata/data.dta`，schema 与原始一致：
  `year, provincechn, pgdp, monetary_deflator, q_*/p_*`（逐项数量/价格）。
- 观测数 310（31 省 × 10 年）。expenditure 中位数 ¥17,839；pgdp 中位数 ¥56,008。

---

## 2. 两项关键订正（相对旧 Results）

### 2.1 全局最优订正（OPTIMUM CORRECTION）
旧 Results 的 MAIDADS 停在一个**劣质局部最优** nll = −4344.23（ω≈局部值）。
以论文已发表参数化（ω=0.80, κ=6.27）为种子重新优化，找到**真正全局最优**：

  **nll = −4481.554（ω=0.705, κ=4.911）**，较旧解优约 137 nll 单位。

在该真优处 **猪肉收入弹性为正**（US$15k 处约 +0.11，随收入递减），与论文定性结论一致。
详见 `Results/OPTIMUM_CORRECTION_NOTE.md`。

### 2.2 预算变量尺度（m-SCALE）说明
估计实际使用 **人均实际消费支出（expenditure）** 作为 m（可复现已发表的
−14.33/obs 水平；本次 2015–2024 全样本重估 −4481.55/310 = −14.46/obs）。
论文正文将预算变量表述为“real per capita GDP”并以 K=0.137515 映射美元轴——
这是**文档层面的表述**。本次更新**按用户要求保留 GDP 表述与 K=0.137515 美元故事**，
仅更新周期、观测数与全部数值。详见 `Results/MSCALE_RESOLUTION_NOTE.md`。

---

## 3. 主口径结果（7 组，n=310，FINAL）

| 模型 | nll | k | AIC | BIC | per-obs |
|---|---|---|---|---|---|
| AIDADS_sat | −4248.285 | 14 | −8468.57 | −8416.26 | −13.70 |
| MAIDADS_sat | −4481.554 | 22 | −8919.11 | −8836.90 | −14.46 |

- 似然比 LR = 2×(4481.554−4248.285) = **466.5**（主口径），
  省块 bootstrap 尾概率 **0.270**；稳健口径 LR = 205.7，尾概率 0.566。
- **组顺序/标签**：Staples(grain), Oils and fats(oil), Vegetables and fruits(vegfruit),
  Pork(pork), Non-pork meat/aquatic(meatother=[beef,mutton,poultry,aquatic]),
  Dairy and eggs(dairyegg=[egg,milk]), Other/non-covered residual(nonfood)。
- ω = 0.705，κ = 4.911。

### 均值-GDP 组收入弹性（Table 3）
grain −0.423 (p=0.009)，oil −0.223 (p=0.351)，vegfruit +0.365 (p<0.002)，
pork **+0.214 (p=0.036，正)**，meatother +0.151 (p=0.004)，dairyegg +0.534 (p<0.002)，
nonfood +1.127 (p<0.002)。

### 饲料粮当量（Table 9，百万吨 Mt）
- 合计：**378.3 (2030) → 389.3 (2035) → 393.4 (2050)** Mt（2050 CI [367.3, 529.9]）。
- 2050 分项：猪肉 165.0（≈42%）、蛋 62.6、禽 54.1、牛 43.8、羊 26.6、水产 26.9、奶 14.4。
- 稳健口径饲料粮：384.5 / 396.6 / 401.4 Mt。

---

## 4. 稳健性口径（CPI 非食品平减）
- AIDADS nll = −4374.256；MAIDADS nll = −4477.105。
- 模型排序与主口径一致（MAIDADS 降低 AIC/BIC，均值食品相对 RMSE 0.2848→0.2716）。
- 对比见 `compare_main_robustness.csv`、`robustness_*` 系列文件、`robustness_compare.png`。

---

## 5. 新旧对比（2015–2023 vs 2015–2024）
- 模型选择：`compare_old_new_model_selection.csv`（旧 MAIDADS −3999/−7953/BIC−7869 →
  新 −4482/−8919/−8837）。
- 收入弹性：`compare_old_new_income_elasticity.csv`。
- 饲料粮分项：`compare_old_new_feedgrain_item.csv`（旧 2050 合计 ~349.8 → 新 393.4 Mt）。
- 图：`fig_old_new_compare.png`、`delta_old_vs_new.png`、`fig_bootstrap_forest.png`。

---

## 6. Bootstrap（权威来源）
- **`Results/FormalBootstrap_correct/bootstrap/`**：700 draws，646 收敛，
  **450 有效**（success==True 且 −6000<nll<−1000）。
- 参数/弹性/饲料粮 CI：`bootstrap_parameter_ci_filtered.csv`、
  `bootstrap_income_elasticity_ci_filtered.csv`、`bootstrap_feedgrain_item_ci_filtered.csv`。
- **作废**：`FormalBootstrap/`（僵尸）、`FormalBootstrap_STALE_2015_2023/`、
  `robustness_model_comparison.csv`、`model_comparison.csv` 的 baseline 行（−4344）。

---

## 7. 论文更新
- `From_quantity_to_composition_2024update.docx`：由 `build_2024update_docx.py`
  以程序化“复制源文档 + 逐单元格/逐 run 替换”方式生成。
- 保留 real-per-capita-GDP 表述与 K=0.137515 美元轴故事；更新周期 2015–2023→2015–2024、
  观测 279→310、全部 11 张表与叙述数值。
- 已核验：**全文零残留旧周期 token**。

---

## 8. 关键文件索引
- 面板：`ProvinceData/workdata/data.dta`
- 管线：`ProvinceMAIDADS/scripts/run_maidads_pipeline.py`
- 主表 JSON：`ProvinceMAIDADS/scripts/docx_master_all_tables.json`
- docx 构建脚本：`ProvinceMAIDADS/scripts/build_2024update_docx.py`
- 参数：`Results/parameter_estimates.csv`（nll 以此为准，勿用 stale model_comparison.csv）
- 说明：`Results/OPTIMUM_CORRECTION_NOTE.md`、`Results/MSCALE_RESOLUTION_NOTE.md`
