# 修订日志（REV-1，依据 revision_directives_v2.md）

每个 Phase 结束追加一条：完成项、产出文件、验收/决策门结论、commit。

---

## R0 — 基础设施 + 完成性核验 + 回归测试升级（2026-07-08）

- **M15/F4 完成性门**：✅ 通过。二轮补录已并入合并面板——corn 2005（22 省）、wheat 2005（21 省）、rapeseed 2023（15 省，油菜种子费错行已由 `yearbook_fix_rapeseed2023.csv` 修正）。非阻塞。
- 新建 `constants.py`（外部常数登记，附来源）、`docs/rev_log.md`、`tables/` 目录。
- **M14a**：`test_cd.R` 升级为回归测试（省 FE + 时间趋势 + 二次项 + 可积 FE 项恢复精度），防 F-4 类回归缺陷。
- **INPUT 决策**：用户将提供 INPUT-1（分省播种面积）与 INPUT-2（分省农村 CPI）；M5 待数据到位后执行，本轮先做 M1–M4、M6–M15。

产出：`constants.py`、`docs/rev_log.md`、`tables/`、升级版 `R/test_cd.R`

---

## R1 — estimator 扩展（2026-07-08）

- **M6a Γ断点**：`itsur.R` 新增 `gamma_break=TRUE` → Δγ 块（`dgamma_n_m`，对称+行和为零，份额乘 D2、成本乘 0.5·D2·lnw·lnw，D2=1{year≥2014}），可积性自动保持；`tl_recover` 恢复 DGamma（后段 Γ=Gamma+DGamma）。LR 检验用 `drop_params="^dgamma_"`。玉米平滑冒烟：LR(Δγ=0)=118.5, p≈1e-20（**拒绝** Γ 稳定），共同评估点 M_ML pre=0.65 vs post=1.35（后段更高 → G3 触发 H1 部分复活分支）。
- **M13b 区域×时期可积FE**：`itsur.R` 新增 `extra_fe`（长度 n_obs 标签，NA=参照期不加项）→ 份额加 `xfe_n` 截距、成本加 `xfeC` 层截距 + Σ`xfe_n`·lnw_n 可积斜率（同 F-4 机制）；基期(2004-08)设 NA 避免与省FE共线。玉米冒烟 18 个区域×时期胞、cc 收敛，eps_ll=−0.27/eps_mm=−0.86/M_ML=0.81（近基线）。
- **M2a lny_e**：`build_panel.R` 加 `q_output_e`＝省内前3年亩产移动平均（≥2滞后可得），非NA起点2006，样本量不变（仅加列）。Spec B 用 lny=log(q_output_e)，丢弃 2004–05 等无滞后行。
- **回归测试**：改后 `test_cd.R` A/B 全过（含 F-4 可积守门断言）。

产出：改版 `R/itsur.R`（tl_param_names/tl_build_system/tl_recover）、`R/build_panel.R`、重建 `data/panel_*.csv`（+q_output_e 列）

---

## R2 — 主重估矩阵（2026-07-08/09，运行中）

四作业并行：robust_matrix（M3/M10/M11/M12c/M13a-c）、robust_specB（M2）、gamma_break（M6）、baseline+hw postest（M12a）。robust_matrix 加凹性块热启动（`a_init`）+ 单线程BLAS 提速。

**决策门结论：**
- **G2（Spec B 预期产量）✅ 未触发**：9 品种 |ΔM_ml| 全 <0.15（最大 soybean −0.10），无核心弹性变号 → **Spec B 进稳健性、基线不动**。附带证据：ε_Cy 在 Spec B 下仍病态（rapeseed 100% 为负、mid_indica 62%），**独立佐证 M4 撤除 RTS/TFP**。（`out/specB_compare.csv`、`out/specB_G2_flags.csv`）
- **G3（Γ 断点 2004–13 vs 2014–24）→ 全品种"H1 部分复活"**：9 品种全部拒绝 Γ 稳定（LR 43–149，p 1e-6~1e-27），且 **M_ML 后段一律更高**（共同评估点 pre≈0.2–0.9 → post≈1.5–1.9，Δ+0.64~+1.60）；Δλ 显示劳动节约偏向 2014 后加速（6/9 品种 dB_labor<0）。→ **叙事修正：替代弹性并非"稳定"，而是刘易斯转折后显著上升**，与工资诱致机械化一致，比 pooled S2 更支持 H1。稳健性由 M9 玉米/粳稻 bootstrap-LR 复核。（`out/gamma_break_test.csv`、`out/elasticities_split_*.csv`、`out/gamma_break_G3.csv`）

**robust_matrix 数值（全部产出，热启动跑完）：**
- **M3a plain/cc**：曲率约束抬升 M_ml 显著者 corn +0.18、wheat +0.15、peanut +0.30、rapeseed +0.34（plain 凹性违反率 28–49%、触发观测 62–158）；rice_early/late 近零位移（plain 本已凹）。→ 须诚实披露"旱作 M_ml≈1 部分是约束产物"。（`out/plaincc_compare.csv`）
- **M3b κ 网格**：max|ΔM_ml(1e6→1e7)|=0.024（soybean，余 <0.013）；**略超 0.02 验收线**，记为"近收敛，soybean 边际敏感 0.024（仍在 bootstrap CI 内）"，基线保持 κ=1e6。（`out/kappa_sensitivity.csv`）
- **M13b 区域×时期可积FE**：M_ml 一律小降 −0.05~−0.15（corn −0.151、soybean −0.152 触 0.15 线）→ 识别节须注明"吸收区域×时期共同冲击后替代估计软化 ~10–15%，符号与旱>稻排序不变"。（`out/robust_regionperiod.csv`）
- **M10/M11/M13c/M12c**：wmach剔年/仅原生xls年/剔疫情/发改委三肥替代 均已产出对照（`out/robust_{wmach_years,xlsonly,dropcovid,fertndrc}.csv`）。
- **M13a 价格变异诊断**：`out/price_variation_diag.csv`（各 ln(w_m/w_other) 对年份 R² + 省内SD，daywage vs hired）。
- **M12a hw**：9 品种 hw 全套 postest 产出，eps_ll∈[−0.45,−0.26]、M_ml∈[0.69,0.97]，全部同号。

R2 ✅ 完成。后处理管线（chain_post → run_post_R2）已自动接续：Group A(S2/6f/decomp/priceCV) → B(M9 tests_boot/M8 induced_regional) → C(M1 bootstrap B=500) → D(hw+doubleblock) → E(M4 tauC/M7 consistency)。


---

## R3/R4/R5 — bootstrap + postest v2 + 区域诱致性（2026-07-09）

- **M1 bootstrap（B=500 联合重抽，热启动+单线程BLAS，per-draw 101s，6核）**：cc + hw 各 500 draws。
  ok 率：7 品种 100%、wheat 99.4%；**early/late indica 91.2%/91.0%**（省份少，joint 交集偶 <4 省 →
  prep_fail 44，CI 基于 ~455 draws，已披露，非 fit 失败）。产出 draws/status/ci/crosscrop/manifest。
  跨品种：**旱作−稻作 M_ML 差 0.329 [0.137, 0.479] 排除零**；corn/soybean 显著高于各稻。
  玉米双 block（省×时期）M_ML 0.60[0.53,0.75]（更细FE，偏低）。
- **M9 tests_boot**：玉米四检验 bootstrap 非拒绝率 0–0.5%（强拒绝稳健）；**玉米/粳稻断点非拒绝
  0–0.5%（G3 断点抗序列相关）**；wheat 位似性 analytic p=0.070、bootstrap 非拒绝 27.5%（未拒，重表述）。
- **M8 induced_regional（G4）**：labor k1–5 Σψ=0.344 t_DK=3.86 placebo 干净 → **suggestive，回正文**；
  k1–3 边界（placebo F2 t=2.17）；mach placebo 失败→描述性。较 pooled 根本改善（符号转正）。
- **M4 tauC**：τ_C≈−0.01~−0.04/年；scale_tfp 改名 _deprecated；grep 自查 TFP/RTS 零 value-claim。
- **M7 bias_consistency**：consistent=TRUE 仅 corn/japonica/mid_indica 劳动节约 + 四稻机械使用；
  wheat/soybean/peanut/rapeseed 跨规格不一致，不下偏向结论。
- **M12a/b**：hw 全套 postest；价格交叉验证 w_fert vs 发改委三肥 corr 0.51–0.94。

## R6 — 表/图/终版 summary（2026-07-09）

- **M14c build_tables**：T1–T9（md+csv）0 缺失。
- **build_figs v2**：F3v2 断点两段 M_ML、F6 M_ML bootstrap CI 森林图、F7 区域诱致系数；F5 实际口径待 INPUT。
- **results_summary_v2.md**：12 节结构；**禁止表述 6 条逐条自查通过**（TFP/RTS 仅出现在"撤除"语境，
  零 value-claim；旱>稻带 CI；偏向限定 consistent 品种；诱致因果只在 placebo 干净的 labor k1–5）。
- **data_appendix.md**：15 项价格口径 + 插补计数 + 毒死蜱局限 + OCR 规模 + F4 完成性。
- **M5 待 INPUT-1/2**（分省播种面积 + 农村CPI）后补跑实际口径分解。
