# 修订日志（REV-1，依据 revision_directives_v2.md）

每个 Phase 结束追加一条：完成项、产出文件、验收/决策门结论、commit。

---

## R0 — 基础设施 + 完成性核验 + 回归测试升级（2026-07-08）

- **M15/F4 完成性门**：✅ 通过。二轮补录已并入合并面板——corn 2005（22 省）、wheat 2005（21 省）、rapeseed 2023（15 省，油菜种子费错行已由 `yearbook_fix_rapeseed2023.csv` 修正）。非阻塞。
- 新建 `constants.py`（外部常数登记，附来源）、`docs/rev_log.md`、`tables/` 目录。
- **M14a**：`test_cd.R` 升级为回归测试（省 FE + 时间趋势 + 二次项 + 可积 FE 项恢复精度），防 F-4 类回归缺陷。
- **INPUT 决策**：用户将提供 INPUT-1（分省播种面积）与 INPUT-2（分省农村 CPI）；M5 待数据到位后执行，本轮先做 M1–M4、M6–M15。

产出：`constants.py`、`docs/rev_log.md`、`tables/`、升级版 `R/test_cd.R`
