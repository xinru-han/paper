# 系统检视 · 报告二：计量方法与R实现审计（独立评审agent，2026-07-07）

审计范围：R/itsur.R、R/itsur_concave.R、R/estimate.R、R/bootstrap.R、R/postest_s2.R、
R/postest_decomp.R、R/test_cd.R、build_figs.R 及 out/*.csv 方向核对。只做代码追踪，未重估。

## 一、核实无误的部分

1. 份额方程与对称映射、交叉方程约束正确（itsur.R:59-88）。
2. 齐次性与加总：numeraire 内建 R1；tl_recover 恢复第N要素正确；不变性有单测+实证核验。
3. 弹性公式全部正确：eps_nn=(γ_nn+S²-S)/S、Allen 按列除 S_m、Morishima M[n,m]=eps_nm-eps_mm
   （Blackorby–Russell）；CD 极限单测核对无误。
4. **Morishima 方向标签正确**：M_ml=morishima[2,1]=M_{mach,labor}=工资变动下机械替代劳动，
   与摘要表述一致，无索引错误。
5. 凹性矩阵 G=Γ+SS'-diag(S) 正确；C1 参数化数学上成立。
6. ITSUR：迭代FGLS≈FIML，LR 自由度全部正确。
7. Bootstrap 种子处理可复现；draw 内完整复制流程（含重新中心化）。
8. OOS 无信息泄漏（中心化常数只用训练期、测试省限定训练期出现过的省）。

## 二、发现的问题

### F-1【FATAL→已修复】诱致性第二阶段符号解释与代码约定相反
sb:=-Δδ 为节约偏向，Hicks 预期 Σψ>0，实测 Σψ_labor=-0.236<0 = 劳动使用方向，
与摘要"方向符合Hicks"相反。→ **results_summary.md §4 已更正**（2026-07-07）。

### F-2【MAJOR】第二阶段推断失真
(a) 5品种共享同一劳动力市场，dlnrel_labor 跨品种高度相关，有效独立信息≈年份数，
HC1 假设独立→t=-5.2 严重高估；plan 承诺 Driscoll–Kraay 未实施。
(b) 因变量 Δδ̂ 为生成回归元，差分后 MA(1) 串行相关且同品种共享 γ̂。
(c) 结合 placebo 失败，本节证据力接近于无。
→ 修复：按年聚类/DK SE；bootstrap 传播第一阶段不确定性；或降级为描述性。

### F-3【MAJOR】S2(gindex) 系统内部不一致
份额方程换年哑变量后，成本方程仍保留 λ_t·t+0.5λ_tt·t² 且未加 Σδ_nτ·D_τ·lnw_n
——份额方程不再是成本方程的 Shephard 导数，错配经 GLS 交叉权重污染 γ 与 δ 路径。
→ 修复：S2 只估份额方程系统（general-index 文献常见做法）。

### F-4【MAJOR】省FE破坏系统可积性
份额方程含省截距 fe_np，则成本方程应含 Σ_n fe_np·lnw_n 交互；代码只有省截距 feC_p。
成本方程误差与回归元相关 → α_y、γ_yy、λ_t、λ_tt、λ_yt 有偏，波及规模弹性/TFP/分解。
test_cd.R 仿真无FE无时间项，单测测不出。
→ 修复：Xc 中填入 fe_np·lnw_n 列（参数已存在，不增自由度）。

### F-5【MAJOR】cc 基线三处方法论疑点
1. 惩罚施加在观测份额、验收在拟合份额，评估点错开。
2. "自价格全负"是约束产物，正文应并列 plain 弹性表以显示约束代价（Terrell 有偏-方差权衡）。
3. κ=1e6 近似硬约束下 percentile bootstrap 一致性不保证（Andrews 2000）；
   症状：cc 点估计 M_ML=0.90 vs bootstrap 中位数 0.966，中心错位未讨论。

### F-6【MAJOR】LR 检验 p 值忽略省内序列相关，统计量膨胀
→ block bootstrap 化 LR 分布，或表述降级为"iid 假设下拒绝"。

### F-7【MINOR】分解与 TFP 用 plain 参数（method 默认），与"基线=cc"矛盾。
### F-8【MINOR】OOS 实际为 ≤2021 训练 / 2022-24 测试；summary "留出2021-2024"表述错误；
   sys_tr 缺收敛断言。（代码无泄漏。）
### F-9【MINOR】聚合权重 q_output 是亩产非总产量——省际聚合系统性偏向高亩产省；
   NATIONAL 分解与品种级价格指数受影响。→ 改播种面积/总产量权重或明示口径。
### F-10【MINOR】bootstrap：method 传 "c1" 会静默跑 plain 并覆盖文件；
   prep_data 层报错的 draw 被 Filter 丢弃致 ok 率分母失真；建议省×时期双重 block 敏感性。
### F-11【NOTE】s2 滞后用位置 shift 无年份断档断言；内层 optim convergence 未检查；
   κ 无敏感性；test_cd.R 有无操作调试残留；plan 提及的 build_tables.R 不存在；
   decomp 注释"期中点"与实际全窗口均值不符。

## 三、总体判断

估计器核心经追踪均正确，单测覆盖了最易错的 numeraire 与方向问题。风险集中在下游推断
与叙述层：F-1（已修复表述）、F-2/F-3（S2 结构）、F-4（可积性）、F-5（cc 呈现方式）。
