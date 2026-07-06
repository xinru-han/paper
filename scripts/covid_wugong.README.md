# COVID Impact on Migrant Work (新冠对务工的影响)

Claude-science 修改的复现代码与结果（2026-07-05/06）。

## 目录

| 路径 | 内容 |
|------|------|
| `scripts/` | Python 数据提取与合并流水线 |
| `repro/scripts/` | R 复现脚本（基线、事件研究、IV、工资子样本等） |
| `repro/output/` | 复现中间输出 |
| `repro/figures/` | 图表 |
| `repro/data/` | 分析用小数据（不含原始 .dta） |
| `repro_deliverables/` | 最终交付表格、诊断与报告 |
| `*.R` | 根目录 R 脚本（与 repro 同步版本） |

## 运行

```bash
# Python 流水线
cd scripts && python3 01_extract_micro.py  # 依次运行 01–08

# R 复现
cd repro/scripts && Rscript 01_baseline_and_dynamics_2023.R
```

## 数据来源

原始 `.dta` 与大型中间文件未纳入 git（见仓库 `.gitignore`），需从本地数据目录获取。

## 自动同步

工作目录 `/root/data/Paper/covid` 的变更由 `paper-sync-covid.timer` 每 5 分钟同步到此目录并推送到 GitHub。
