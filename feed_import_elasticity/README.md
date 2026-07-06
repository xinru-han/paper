# Feed-Grain Import Elasticity (饲料进口弹性)

Claude-science 修改的 QUAIDS 审改复现代码与结果（2026-07-05/06）。

## 目录

| 路径 | 内容 |
|------|------|
| `revision_2026/code/` | Python 流水线（面板构建、Bartik IV、FIML AIDS/QUAIDS、bootstrap、政策识别） |
| `revision_2026/output/` | 估计结果 CSV、诊断报告 |
| `revision_2026/figures/` | 图表 |
| `revision_2026/checkpoints/` | 中间 parquet 检查点 |
| `revision_2026/*.md` | 审改备忘录与修订文档 |
| `restricted_demand/` | 受约束需求弹性矩阵结果 |
| `data/*-feed.csv` | 五品类饲料粮海关逐笔聚合输入 |
| `data/acc.xls` | 地区代码对照 |
| `cf_aids_quaids_*.md` | R 代码与结果整合总览 |
| `paper_full*.txt` | 论文正文 |

## 运行

```bash
cd revision_2026/code
python3 01_build_panel.py
python3 02_build_bartik_instrument.py
# ... 依次运行至 08_policy_event_identification.py
```

## 未纳入 git 的大文件

- `进口数据/`（完整海关逐笔，~4.7 GB）
- `data/*-food.csv`（全 HS 食品章节）
- `主产区原粮购销价格监测旬报/`、`全国邮政编码数据库/`
- `*.docx`

## 自动同步

工作目录 `/root/data/Paper/饲料进口弹性` 的变更由 `paper-sync-all.timer` 每 5 分钟同步并推送到 GitHub。
