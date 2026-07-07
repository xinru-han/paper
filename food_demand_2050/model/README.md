# Python CASM — 食物需求预测2050 复现

论文《Alternative pathways for China's diet transition: Implications for food security,
nutrition and greenhouse gas emissions to 2050》全部GAMS模拟的Python复现。
无需GAMS：模型为逐年递归动态MCP，用Fischer–Burmeister半光滑牛顿法求解。

## 结构

- `casm/` — CASM v2.2.7 Python移植（复制自 `/root/data/CASM/casm_python` 并适配论文版：
  基期2024、预测2025–2050、读取论文文件夹的 `0data.xlsx / 1parameter.xlsx / 2simulation.xlsm`）。
- `run_scenarios.py` — 跑全部19个情景（BS + A1–A6 + B1–B6 + C1–C6）：
  3个GAMS文件夹（CASM20251118=PTS、…diet=HDS、…median=MTS）×（BASE+SIM1–6），
  BASE三处相同只跑一次。每情景~12秒，全套约6分钟。
  结果写 `../results/results_long.csv`（scenario, group, sim, variable, commodity, year, value）
  与 `../results/scenario_summary.csv`。
- `validate.py` — 与GAMS真值（预测结果整理/3RESULTCOM-*.XLSX）及论文表2/4/6逐格核对，
  写 `../results/validation_report.md`。

## 情景编码

| 论文代码 | GAMS方案 | 含义 |
|---|---|---|
| BS | BASE | 偏好不变（afhgr0=0），中人口中城镇化 |
| X1 | SIM1 | 代表性：中人口中城镇化 |
| X2/X3 | SIM4/SIM5 | 高/低城镇化 |
| X4/X5 | SIM2/SIM3 | 高/低人口 |
| X6 | SIM6 | 老龄化（标准人当量人口） |

X∈{A=PTS动态弹性, B=HDS健康膳食, C=MTS温和转型（增长率=A、B算术平均）}。
膳食路径通过 `afhgr0`（人均食用需求年增长率，2025–2050恒定）注入需求方程偏好项
`AFH_t = AFH_{t-1}(1+afhgr0)`。

## 运行

```bash
cd model
python3 run_scenarios.py   # → ../results/
python3 validate.py        # → ../results/validation_report.md
```

## 验证结论

19情景全部收敛（|F|≲1e-12）；与GAMS逐格对比中位偏差0（机器精度），
论文表2/4/6全部数字在舍入精度内复现。两处与原GAMS产物的已知差异
（normal工作簿营养系数陈旧、SIM6排放系数缺失）见 `../results/validation_report.md`，
均为原始文件问题而非Python误差。
