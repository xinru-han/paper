# Paper 9：Trading Up, Trading Down — EASI-Q 质量弹性（执行库）

方案：`央视数据研究方案/paper9_质量弹性_EASI-Q_v2.md`。数据 2020-01–2022-12，27,653 户交易级面板；
13 个可计价品类（奶类5种/黄油/成人奶粉/方便面/挂面/食用油/大米/面粉/坚果）+ 8 生鲜品类合并为复合品。

## 数据路径

- 原始交易：`/root/data/数据/央视数据/Data_merged.csv`
- 监测价：`Paper1-EASI/processed/external_food_prices_*.csv`（OBS7 有真实观测价：大米/面粉/食用油/方便面/常温牛奶/新鲜牛奶/成人奶粉；
  其余 6 个可计价品类的 proxy 填充直接抄常温牛奶序列不可用 → 基准价改用**省×月中位 unit value**，`src` 列标注）
- 复用 paper8-hot：hh_info（tier_a）、lockdown_windows、省×层级×日气温（月度热天数）、营养系数

## 管线（`nohup bash code/run_pipeline.sh &`，内存门槛+自动重试；日志 logs/pipeline.log）

| 脚本 | 内容 | 产出 |
|---|---|---|
| 90a_uv_build.R | uv 清洗（单位双峰诊断、品类×省 1%/99% 截尾、中位数 [1/5,5] 窗口）、户月预算面板 | t1, interim |
| 90b_price_panel.R | 混合基准价（监测价/中位uv/Stone复合品）、冲击变量、主面板+质量面板（r_prem） | interim |
| 90c_ladder.R | 质量阶梯字典 + 奶类组内/组间面板 | lookups |
| 90d_income_link.R | LLI 收入-支出链接方程（within/between 双版） | t2a |
| 91_stageA_easi.R | 截断 EASI 14 商品：SY 两步 + y 迭代 + 控制函数；齐次性=价格正规化，对称性=事后最小距离（附成对 z 诊断） | t2, t2b |
| 92_stageB_quality.R | 13 条质量方程：FE 版 θ_g(y)（三次多项式）+ 价格版 Ψ^M + 齐次性检验 Σψ+θ=0；大米/面粉/坚果计量层 IPW | t3, t3a, t3b, t6b |
| 93_elasticities.R | χ/θ/η_dir/收入质量弹性、两边际表、诊断、价格弹性 e^M、质量地板分位、奶类组内组间 | t4, t4b, t5, t11* |
| 94_psi_matrix.R | Ψ^M→Ψ^H、质量校正价格弹性 ε^q=e^M−Ψ^M、热力图 | t6*, fig2, fig3 |
| 95_mckelvey.R | Deaton 价盲法三种 cluster 分辨率 vs 观测价真值、偏误~价格变异比、uv 价格弹性 vs 观测价 | t7*, fig5 |
| 96_shocks.R | 跳档 pecking order 事件研究（持续≥3月过滤）、封控/猪价×暴露/春节/热天 r-lnQ 成对 | t8*, fig6 |
| 97_qcpi.R | 分位有效通胀（实付 vs 市场基准指数）、质量楔子 | t9*, fig7 |
| 98_welfare_voucher.R | 质量缓冲（包络二阶）、乳品券 25% 泄漏率模拟（分收入档，券 vs 现金）、阶梯营养梯度 | t10*, t13 |
| 99_robustness.R | R1 TierA / R2 去封控 / R3 季度 / R4 紧截尾 / R8 阶数 / R9 中位uv | t12 |
| 9f_figures.R | θ(y) 曲线族、两边际收入梯度、奶类阶梯转移热图 | fig1/4/8 |
| 9x_bootstrap.R | 户级 cluster bootstrap θ（B=200；λ_sel 与 y 迭代不逐次重估，见脚本头注释） | t3c |

调试：`P9_DEBUG=TRUE` 抽 3,000 户；`P9_RPOLY` 改 Engel 阶数。R 库 `/root/Rlib_p8`（fixest 0.14.2 + quantreg，R 4.1.2）。

## 与 md 方案的已文档化偏差

1. Stage A 逐方程 fixest 估计（非 systemfit SUR）；对称性以事后最小距离 (A+A')/2 施加并报成对 z 诊断——一致性不受影响，牺牲跨方程效率。
2. ln x 内生性：控制函数已放弃——收入档与记录食物支出几乎无关（90d within ς2≈0.002，弱一阶段），vhat 无信息且与 y 近共线；主规格 = OLS+户FE（方案 §12 预设退路），t2a 保留弱一阶段证据。
3. Yu–Abler 精确校正公式离线不可复现 → t7 报"回收率诊断"θ_true/γ_naive 并在脚本注释声明。
4. bootstrap 不逐 draw 重估 probit 层与 y 迭代（λ_sel 固定、y 用一次性 Stone 近似）。
5. 6 个无观测监测价品类（挂面/黄油/奶酪/常温酸奶/新鲜酸奶/坚果）基准价 = 省×月中位 uv：其 ψ_gg 有向 −1 方向的机械衰减风险（r 含 −ln p_base 且 p_base 与本品 uv 同源），解读时以 OBS7 品类为准。

结果汇总见 `outputs/RESULTS.md`（管线完成后生成）。GitHub：paper repo 子文件夹 `paper9_easiq`，
`/root/paper/scripts/sync-paper9-easiq.sh` 每 5 分钟 cron 自动同步（排除 data/interim/）。
