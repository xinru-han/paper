# Paper 8 — Some Like It Hot: Temperature, the Daily Food Basket, and the Nutritional Cost of Climate Change in Urban China

研究方案：`../央视数据研究方案/paper8_气温冲击_气候饮食.md`（v2.1 组合的第 8 篇，目标 AJAE / JEEM）。
本文件夹是**可复现执行包**：code（R + 1 个 python 解析器）→ outputs（tables/figs）。

## 数据（不入库，本机路径）

| 输入 | 路径 |
|---|---|
| 家庭交易 2020-01–2022-12（1041 万笔，27,653 户） | `/root/data/数据/央视数据/Data_merged.csv` |
| 地级市日度气温/降水 1973–2024（长表 xlsx） | `/root/data/数据/央视数据/地级市天气数据/城市/` |
| 省×日×品类监测价（发改委，Paper1 已清洗） | `Paper1-EASI/processed/external_food_prices_category_province_monitor_date_cleaned_2020_2022.csv` |
| 城市层级映射 / 疫情 / 节假日 | `Paper1-EASI/processed/` |
| 中国食物成分表（新版营养成分表.zip） | `/root/data/数据/食物消费调查数据/食物编码和营养成分/` |

家庭仅识别到省×层级 → 气温暴露匹配：Tier A ↔ 省会精确；Tier B–E ↔ 省内非省会地级市均值（日温省内相关 ~0.9，衰减小；R1 给 Tier A 基准）。

## 脚本管线（code/，依次运行）

| 脚本 | 对应方案 | 内容 | 主要产出 |
|---|---|---|---|
| 00_setup.R | — | 路径、气温/降水分箱、日志、WCB 函数 | — |
| 01_weather_parse.py | 80a | 解析 104 个天气 xlsx → 年度 csv | `data/interim/weather_years/` |
| 02_weather_build.R | 80a | 1981–2010 常态、省×层级×日暴露、情景频数表 | lookups + interim |
| 03_lookups.R | 80b | 封控窗口、品类→组×易腐性、营养系数/kg | `data/lookups/` |
| 04_build_panel.R | 80b | 家庭×日网格（1747 万行）、交易聚合、单元×日×组 | `data/interim/` |
| 05_main_bins.R | 81 | 主回归：出行/日支出/分组条件结果；**三重推断**（聚类 SE + WCB + 置换） | t1, t2 |
| 06_channel.R | 82 | 价格方程（旬窗温度）+ **价格/需求渠道分解**（弹性 NSD 修复） | t3, t4 |
| 07_margins.R | 83 | **出行边际 vs 构成边际** + 老年/收入/层级异质性 | t5, t6 |
| 08_adaptation.R | 84 | 常态交互（横截面适应）+ 年内驯化曲线 | t7 |
| 09_displacement.R | 85 | 0–14 天分布滞后累积（**位移—放弃二分**） | t8 |
| 10_nutrition.R | 86 | 隐含数量×营养系数：热量/蛋白/铁响应、多样性、RIF 分位 | t9, t10 |
| 11_projection.R | 87 | +1.5/+3 °C 情景预测（三种适应）、福利、碳反馈、政策 | t11–t15 |
| 12_robustness.R | 88 | R1–R6 | t16 |
| 13_figures.R | — | 图 1–5 | `outputs/figs/` |

调试：`P8_DEBUG=TRUE Rscript code/04_build_panel.R` 抽 5% 家庭。R 库位于 `/root/Rlib_p8`（fixest 0.14.2，R 4.1.2）。

## 识别设计（摘要）

- 主 FE：家庭 + 暴露单元×年月 + 星期几 → 识别变异 = **同单元同月内的日温异常**；协变量：降水箱、节假日/春节窗、封控指示（8 事件表）、log(1+新增病例)。
- 参照组 (18,24]；7 个 tavg 分箱；推断 24 省聚类三报（cluster / WCB-Rademacher / 单元内年标签置换）。
- 渠道分解：监测价（旬窗温度）价格方程 γ_g^b；需求渠道 = 总效应 − [γ_g + Σ_k E_gk γ_k]，E 为 Paper1 弹性经最近负半定投影修复（失败则文献对角后备，log 会注明）。

## 产出

`outputs/tables/t1–t16*.csv`（回归系数与后估计量）、`outputs/figs/fig1–fig5*.png`、`logs/run_log.md`（每步样本量/关键系数）。结果汇总见 `outputs/RESULTS.md`。

## 同步

本文件夹（除 `data/interim/`）每 5 分钟由 cron `sync-paper8-hot.sh` rsync 到 `github.com:xinru-han/paper` 仓库的 `paper8_hot/` 子目录并自动 push。
