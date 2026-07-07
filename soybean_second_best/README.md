# 中国大豆全产业链第二优均衡：定量模拟与政策仿真

理论: `soybean_theory_paper_revised.tex`；执行方案: `soybean_simulation_plan.md`（见论文目录）。

## 快速开始

```bash
pip install -r requirements.txt
python run_all.py --fast   # 全流程 <15 分钟
python run_all.py --full   # 完整抽样
pytest -q                  # 理论命题单元测试
python webapp/app.py       # 交互式仿真网站(:7070)
```

## 模块

| 模块 | 内容 | 主要输出 |
|---|---|---|
| M1 | 校准规划模型与比较静态 | T1/T2, F1/F2 |
| M2 | 进口组合与蒙特卡洛风险 | T3, F3/F4 |
| M3 | 生产网络放大 (2023年211部门IO表) | T_M3, F5 |
| M4 | 合成代表性农户 ABM 2026–2035 | T_M4, F6 |
| M5 | 政策矩阵 P0–P6 | T4, F7/F8 |
| M6 | 命题检验 T1–T6 | T_M6 |
| M7 | Sobol/LHS 敏感性 | T5, F9 |

结果汇总见 `results/REPORT.md`。

最近更新: 2026-07-07