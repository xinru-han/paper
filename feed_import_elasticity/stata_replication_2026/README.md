# Stata AIDS/QUAIDS/EASI replication (2026)

本目录使用 Stata 17 SE 和 `fooddem` ado，重新估计中国五类饲料原料进口需求系统，
并与 2026-06-14 的旧 R/FIML 结果比较。数值结论见
[`RESULTS_SUMMARY.md`](RESULTS_SUMMARY.md)。

## 数据与口径

- 原始宽表：`../revision_2026/checkpoints/panel_wide.parquet`
- 质量调整价格：`../revision_2026/checkpoints/price_variants.parquet` 中的
  `completed` 价格
- 样本：2017Q1-2023Q4，634 个正五类进口预算的省份-季度观测
- 商品顺序：玉米、高粱、木薯干、燕麦、大麦；大麦方程由加总约束恢复
- 控制变量：猪肉、牛肉、羊肉、肉类、禽蛋、牛奶产量（样本内标准化）
- 内生支出：Bartik 工具变量第一阶段残差作为控制函数；第一阶段含省份和季度
  双向固定效应
- 推断：省级聚类 VCE（30 个有正预算观测的省份）

`input/feed_import_panel.csv` 是从上述 parquet 检查点生成的审计快照。
`code/00_export_input.py` 只做格式转换和合并，不执行估计。

## 模型

1. 基准：AIDS、QUAIDS、EASI(1-3) 的 NLSUR、Shonkwiler-Yen 校正、控制函数。
2. 稳健性：相同模型去掉 SY 校正；这是对 SY 项联合不显著的响应。
3. 所有模型均由 `fooddem` 参数化强制满足 adding-up、价格齐次和 Slutsky 对称。
4. `fooddem_select` 用嵌套 Engel 项检验确定家族内阶数，再用 BIC 比较 AIDS 家族
   与 EASI 家族。

本次尝试的两步 IV-GMM 在 AIDS 初始规格上超过 7 分钟仍未返回，因而中止；正式
结果不包含未收敛或中止的数值。NLSUR+控制函数与旧 R/FIML 的识别口径更接近。

## 目录

- `ado/`：本次实际使用的 `fooddem` ado 快照（主程序版本 1.3.0，2026-07-14）
- `code/`：数据准备、估计、后估计、R/Stata 比较与一键运行脚本
- `input/`：Stata 输入 CSV 和人工核对的旧 R 核心结果
- `data/`：Stata 估计数据集
- `output/`：模型选择、系数、检验、弹性、正则性、`.ster` 估计对象和比较表
- `logs/`：本机运行日志；因含 Stata 许可证头而不提交 Git

## 运行

```bash
cd /root/data/Paper/饲料进口弹性/stata_replication_2026
./code/run_all.sh
```

默认使用：

- Python：`/root/.claude-science/conda/envs/python/bin/python`（需 pandas/pyarrow）
- Stata：`/usr/local/stata17/stata-se`
- ado：本目录 `ado/`

可通过 `PYTHON`、`STATA` 环境变量或 `run_all.sh` 的第二个参数覆盖。

## 关键输出

- `output/model_selection_nlsur_cf.csv`：SY 基准的 AIDS/QUAIDS/EASI 选择
- `output/model_selection_nlsur_cf_no_sy.csv`：无 SY 稳健性模型选择
- `output/reference_nlsur_cf_quaids.csv`：与旧 R 均值参考点最可比的 Stata QUAIDS
  条件弹性
- `output/preferred_elasticities_nlsur_cf_unconditional.csv`：含广延边际的无条件弹性
- `output/reference_nlsur_cf_no_sy_easi3.csv`：无 SY EASI(3) 参考点弹性
- `output/r_vs_stata_core_comparison.csv`：旧 R 与 Stata 核心弹性逐项比较
- `output/stata_model_comparison_all.csv`：全部收敛/失败状态、BIC 和嵌套检验

## 解释限制

基准 QUAIDS 在样本均值处满足局部曲率，但全样本五类潜在预测份额同时为正的比例
只有 24.4%。因此主文只能声称局部正则；逐观测弹性必须限制在
`minshare(.001)` 的共同内部支持，并报告 `support_rate`。无条件弹性不能解释为
潜在条件弹性，反之亦然。
