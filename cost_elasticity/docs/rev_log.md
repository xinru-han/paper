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
