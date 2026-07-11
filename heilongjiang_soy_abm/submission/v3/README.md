# 黑龙江玉米—大豆种植决策：微观计量 + ABM 仿真（《中国农村经济》投稿）

## 结构
- `论文_中国农村经济.md / .docx` — 论文全文（docx 含 Word 原生公式）
- `abm.py` — 农户主体模型（修正版：参数不确定性/宏观冲击/份额残差/校准偏移/结构性零参与）
- `code/01_build_panel.py` — 固定观察点问卷 → 户×年面板（户键修复+去重）
- `code/02_build_deltapi.py` — 预期净收益差 Δπ（价格/成本/收缩单产/补贴标准）
- `code/03_estimate.py` — 动态logit/LPM/CRE/分解/分数logit + AME → behavior_params.json
- `code/04_simulate.py` — ABM 校准、留出验证、情景 S0–S5、目标反解、图
- `output/params|tables|scenarios|figures|logs` — 参数、回归表、情景结果、图、分阶段报告

## 复现
依次运行 code/01→02→03→04（Python3：pandas/numpy/statsmodels/matplotlib）。

## 数据说明
原始问卷（全国农村固定观察点黑龙江样本 2019–2024）与含身份证号的户级中间文件
（output/panel_*.csv, output/scenarios/agents.csv）不入库。
