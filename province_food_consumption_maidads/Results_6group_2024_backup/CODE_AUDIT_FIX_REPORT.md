# CODE_AUDIT_FIX_REPORT

| 审查项 | 本轮处理 | 输出文件 | 剩余限制 |
| --- | --- | --- | --- |
| A1/OOS 指标广播 | 已改为按 variant/model/split/group 输出；追加脚本会重跑 AIDADS 与 MAIDADS | `oos_fit_by_group.csv`, `oos_predictions.csv` | 朴素基线、留一省/留一区域仍待增强 |
| A2/bootstrap 过少 | 追加正式规模 `run_formal_bootstrap.py`，记录省份簇 bootstrap 成功率与区间 | `bootstrap_*`, `FormalBootstrap/*` | 若模型或数据变更，需重新跑正式规模 bootstrap |
| A3/LR χ² 不合法 | 删除把 χ² p 作为最终证据的表述，追加 cluster bootstrap LR；普通 χ² p 不报告 | `lr_test_chi2_and_bootstrap.csv` | 严格 parametric-null bootstrap 仍可增强 |
| A4/价格口径 | 主估计改为 2023 实际价；食品价格和总支出分别用食品/总 CPI 平减 | `maidads6_panel.csv` | 缺分项食品 CPI |
| A5/省级预测路径 | 人口路径改用 Chen et al. (2020) Sci Data 的 SSP2 省级人口预测；收入仍用全国增长率加省份收敛情景 | `projection_growth_path.csv`, `Data/output/provincial_population_projection_ssp2.csv` | 需补正式分省收入、城镇化和年龄结构预测 |
| A6/价格弹性与一致性 | 新增 Marshallian/Hicksian 价格弹性和理论一致性误差表 | `elasticity_price_*`, `elasticity_consistency_tests.csv` | 解析式(7)(8)单元测试仍可进一步补强 |
| B3/饲料粮 | 只输出动物产品，并保留 feed_cereal_share 字段 | `feed_demand_method.md` | 若系数为总饲料而非饲料粮，需补谷物占比 |
| B4/未覆盖食品 | 把展示标签改为其他/未覆盖支出，并写入口径说明 | `data_quality_report.md` | 需外部总热量/FAOSTAT 对账 |
| B5/grain kcal | 马铃薯 /5 只保留为粮食当量权重，热量按实际 kcal/kg 加权 | `grain_weights_processed.csv` | 仍缺分省主粮细类结构 |