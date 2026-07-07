# 细化执行方案：工资上涨、要素替代与诱致性技术变迁——中国农业省级成本函数系统（2004–2024）

**版本**：v1（2026-07-07）。基于 `plan_original.md`（作者原始规范）细化，结合本机数据实际可得性落地。
**实现语言**：R（作者指定）。估计器为自写受约束 ITSUR（`R/itsur.R`），已通过 Cobb–Douglas 单元测试与 numeraire 不变性检验。
**代码与结果**：`paper` repo 子文件夹 `cost_elasticity/`，5 分钟 cron 自动 commit+push。

---

## 1. 相对原方案的落地决策（对应原 DP1–DP4）

在自治执行模式下，按数据实际情况采用如下默认决策（均可逆，作者可随时改）：

- **DP1（价格来源）**：无 NBS 分类指数提取件；改用**发改委价格监测**（旬度、分省、绝对价格水平）作为汇编单位值之外的价格来源。这比指数拼接更好——直接是绝对价，无需锚定。
  - 优先级1（单位值，汇编内部）：labor = 劳动日工价（汇编直接给出）；fert = 化肥费 ÷ 化肥折纯量；land（稳健性）= 流转地租金。
  - 优先级2（发改委监测价）：mach 价格代理 = 柴油/农用机油省级年均价（机械作业的核心可变投入；机械服务市场价无全国分省序列，正文如实说明代理性质）；seed = 对应作物种子省级年均价；other = 农药、农膜等监测价的 Törnqvist 合成。
  - 兜底（个别省年缺失）：区域中位数插补 + 全国序列比例外推，逐条记录 `price_construction_log.csv`。
- **DP2（科目归属）**：机械作业费 + 排灌费 + 畜力费 + 燃料动力费 → mach；农药 + 农膜 + 其他直接费用（工具材料、修理维护、技术服务等）→ other。与原方案默认一致。
- **DP3（土地）**：基线 = 5 要素可变成本系统（排除土地成本与保险税金等间接费用）；6 要素含地系统进稳健性。E2（省级加总影子地租）列为可选扩展，不阻塞主线。
- **DP4（外部 IV 数据）**：基线 Spec A（实际 lny）+ 稳健性 Spec B（前 3 年亩产移动平均的预期产量）。气象 IV（Spec C）暂不取数。

## 2. 数据源与样本

### 2.1 成本收益汇编（因变量 + 份额 + 单位值价格）
来源 `/root/data/数据/成本收益数据/`：
- 卷 2007–2019、2025：原始 xls 表（分省分品种成本收益表）→ 数据年 2006–2018、2024。
- 卷 2005、2006、2020–2024：MinerU OCR 长表数据库 `provincial_cost_benefit_long.csv` → 数据年 2004、2005、2019–2023。OCR 数值须过 QC（份额加总、量纲、与相邻 xls 年份连续性检验），异常值按 `value_anomalies.csv` 复核。
- 覆盖矩阵（品种×省×数据年）在 Phase 0 产出 `out/coverage_matrix.csv`。

### 2.2 品种
主分析：玉米（pilot）、小麦、稻谷（汇编"稻谷平均"口径优先，籼粳分列稳健性）、大豆。样本许可则加：油菜籽、花生、棉花（经济作物）。生猪系统（feed/piglet/labor/energy/other，分规模）列 Phase 2 之后。

### 2.3 发改委价格监测（w_mach、w_seed、w_other）
来源 `/root/data/数据/发改委价格数据/`（清洗规则详见 `docs/price_cleaning.md`，Phase 0 审计后定稿）：
- 农业生产资料价格 2003.04–2023.11（两个衔接 xls）+ 2023.11–2024 旬报 → 省×年：柴油、种子（分作物）、化肥各品种（交叉校验汇编单位值）、农药、农膜。
- 农机用油/饲料/仔猪 2006–2010（生猪系统备用）。
- 聚合规则：旬度监测值 → 省内中位数 → 年度平均；相似规格变量按"同类取中位数、跨年拼接时用重叠期比率校准"处理；全流程写 `price_construction_log.csv`。

### 2.4 面板 schema（`data/panel_{crop}.csv`）
`crop, province, region, year, C_var, q_output, S_labor, S_mach, S_fert, S_seed, S_other, w_labor, w_mach, w_fert, w_seed, w_other` + 审计原始列（labor_days, fert_kg, cost_* 分项）。QC assert：份额加总=1（1e-8）、价格>0、单位值 vs 发改委价相关性报告。

## 3. 模型与估计（同原方案第 1、3 节，R 实现）

- 理论：translog 成本函数 + Shephard 份额方程系统，约束 R1–R5 由 numeraire（other）+ 对称参数映射内建（`R/itsur.R`）。
- 估计：ITSUR 迭代至 ‖Δθ‖∞<1e-10（FIML 等价）；省份 FE 进每个方程；变量中心化（几何均值归一化），t = year − 2014。
- 规格：S1 参数化趋势（主表）；S2 general index（份额方程年哑变量，`share_time="gindex"`）出偏向路径与诱致性第二阶段。
- 识别诊断（Phase 0）：ln(w_m/w_N) 对年份哑变量 R²、省内标准差 → 决定是否用区域×时期段效应替代全套年 FE（基线：省 FE，不放年 FE；S2 中年哑变量只进份额方程）。
- 推断：省份 block bootstrap（B=500，pilot 200，seed=20260703），percentile CI；delta 法交叉核对。
- 已完成的估计器验收：CD 仿真回收 γ≈0、CD 弹性公式命中理论值（<1e-12）、换 numeraire 后完整 Γ 不变（<1e-12）。

## 4. Post-estimation（同原方案第 4 节）

弹性表（ε、Allen σ、Morishima M；四时期均值点 + bootstrap CI）→ M_ML 对实际工资演化曲线（招牌图）→ 假设检验（位似性/Hicks中性/无技术变迁/CD，LR）→ 技术偏向 B_n 与 S2 累计路径 → 诱致性创新两阶段（式 12，Driscoll–Kraay，placebo）→ 成本增长 Törnqvist 分解 → 凹性/单调性满足率 → OOS（2004–21 训练 → 2022–24 份额预测）。

## 5. 目录结构

```
cost_elasticity/
  R/itsur.R          # 核心估计器（含受限估计 drop_params → LR 检验）
  R/test_cd.R        # CD 单元测试（必须通过才允许跑真数据）
  R/build_prices.R   # 发改委价格清洗 → data/prices_ndrc_annual.csv
  R/build_panel.R    # 汇编提取+合并 → data/panel_{crop}.csv
  R/estimate.R       # → out/params_{crop}.csv, fitted_shares
  R/bootstrap.R      # → out/bootstrap_draws_{crop}.csv
  R/postest.R        # → out/elasticities_* tests_* bias_* decomp_* oos_*
  R/build_tables.R / build_figs.R
  data/  out/  tables/  figs/  docs/
```

## 6. 阶段门

- **Phase 0** 数据审计（进行中）→ `docs/data_audit.md`，价格清洗规则定稿。
- **Phase 1** 玉米 pilot 端到端（估计+弹性+F1–F3）；验收：ITSUR 收敛、凹性满足率≥80%（否则触发 Ryan–Wales 局部凹性 C1）、bootstrap 收敛率报告。
- **Phase 2** 小麦、稻谷、大豆（+样本足够的经济作物）。
- **Phase 3** 稳健性矩阵 + 诱致性创新 + S2。
- **Phase 4** 全套表图 + 结果 md 摘要。

其余理论推导、弹性公式、凹性检验、表图清单与工程铁律全部沿用 `plan_original.md`（第 1、4–7 节），不再重复。
