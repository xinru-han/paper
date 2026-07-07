# 成本弹性论文 — Translog 成本函数与刘易斯转折（2004–2024 省级面板）

要素替代弹性、技术偏向与诱致性创新：中国 9 种主要作物
（玉米/小麦/大豆/粳稻/中籼/早籼/晚籼/花生/油菜）。
研究方案见 `docs/plan_refined.md`，**结果汇总见 `docs/results_summary.md`**。

## 目录

```
docs/     方案、数据审计（汇编/发改委）、OCR补录记录、结果汇总
python/   数据抽取（extract_yearbook.py、build_prices_ndrc.py、patch_ocr_gaps.py）
data/     yearbook_long.csv、prices_ndrc_annual.csv、panel_{crop}.csv 等
R/        itsur.R(核心估计器) itsur_concave.R(曲率惩罚) build_panel.R
          estimate.R bootstrap.R postest_s2.R postest_decomp.R build_figs.R test_cd.R
out/      估计输出 CSV（*_cc 为曲率约束基线）
figs/     论文图 F1–F5（300dpi）
scripts/  run_pipeline.sh（一键复现全流程）
```

## 复现

```bash
Rscript R/build_panel.R          # 面板（自动合入OCR修正与补录）
bash scripts/run_pipeline.sh     # 估计→S2→分解/OOS→bootstrap→图（约1.5h）
```

方法要点：translog 成本函数 + Shephard 份额方程 ITSUR（迭代 FGLS 至 1e-10），
省份 FE，齐次性经 numeraire(other) 构造、对称性内建；基线为 Terrell (1996)
逐观测曲率惩罚（κ=1e6，凹性 96–100%）；LR 检验与 numeraire 不变性用无约束版。
推断用省级 block bootstrap（B=200）。
