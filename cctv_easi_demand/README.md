# CCTV High-Frequency Food Demand — EASI (Paper1-EASI)

Claude-science 修改的高频家庭食品需求系统代码与结果（2026-07-05）。

## 目录

| 路径 | 内容 |
|------|------|
| `final_demand_model_R/` | R 脚本 23、CODE.md、RESULTS.md、最终弹性诊断输出 |
| `repro_run/src/` | R 流水线脚本 20–22 |
| `repro_run/outputs/` | 价格审计、潜在价格、需求估计、正则性检验结果 |
| `repro_run/config/` | 价格规则与组权重 YAML |
| `repro_run/*.png` | 复现对比图表 |
| `scripts/` | Python 数据匹配与外部价格构建 |
| `AJAE评审与优化升级方案_v4.md` | AJAE 审改方案 |

## 运行

```bash
# R 复现流水线（在 repro_run 目录下）
cd repro_run && Rscript src/20_build_high_frequency_price_and_panel.R
Rscript src/21_estimate_high_frequency_demand_R.R
Rscript src/22_estimate_high_frequency_demand_fast_R.R

# 最终诊断
Rscript final_demand_model_R/23_finalize_demand_diagnostics.R
```

## 未纳入 git 的大文件

- `processed/`（原始 enriched 交易数据，~16 GB）
- `repro_run/data_derived/`（月度面板 CSV，~2 GB）
- `selection_cre_probit_predictions_r.csv`（~208 MB，超过 GitHub 单文件限制）

## 自动同步

工作目录 `/root/data/Paper/央视数据/Paper1-EASI` 的变更由 `paper-sync-all.timer` 每 5 分钟同步并推送到 GitHub。
