# Food Policy 改投版：补充研究计划（配套 Claude Code 执行）

> 目的：AE 主编 desk reject 的核心理由是"reads more as a technical note rather than quantifying what this measurement error means for nutrition and food security"。改投版新增第 7 节（`sec:applications`），把调整系数落到三类政策指标上：①膳食指南对照、②供给—消费对账（missing meat 缺口弥合）、③自给率与饲料粮含义。本文件是把正文中全部 `\PH{...}` 红色占位符替换为实数的完整计算规范。
>
> 约定：所有计算在既有 R 管线基础上新增脚本，输出统一写入 `numbers.json`，最后由 `fill_placeholders.R`（见 §8）自动回填 tex。**不要手工改 tex 数字。**

---

## 0. 前置输入（来自既有管线，不需重算）

| 对象 | 来源 | 说明 |
|---|---|---|
| `AF_national[k, t]` | 现有 FT-Transformer 管线输出 | 12 类 × 2015–2024 全国点估计（正文表 5 的底层数据） |
| `AF_boot[b, k, t]`，B=100 | 现有 bootstrap 输出 | 逐 replicate 全国 AF；第 7 节所有区间都由它传播 |
| `AF_prov[i, k, t]` 及其 bootstrap | 现有管线 | 31 省，用于 fig6 与省级 SSR |
| `AF_alt[model, k, 2024]` | 表 8（robustness）底层 | LightGBM 与 Random Forest 的全国 AF，用于附录表 `tab:app_sensitivity` |

若 bootstrap 只保存了汇总分位数而非逐 replicate 矩阵，先回溯管线补存 `B×K×T` 数组（第 7 节 CI 必需）。

## 1. 需要新采集的数据（建议目录 `data/applications/`）

**A. NBS 居民人均食品消费量（FAH 口径）**
- 来源：《中国统计年鉴 2025》"人民生活"篇 + 《中国住户调查年鉴》，全国居民人均主要食品消费量（kg/人·年），城乡分列与合计。
- 品类映射到论文 12 类：粮食（原粮/成品粮口径要记录）、蔬菜及食用菌、水果（鲜瓜果）、猪肉、牛肉、禽类、水产品、蛋类、奶类；豆类若年鉴无单列，用"豆类"或从粮食中拆分并在表注说明。
- 年份：目标 2024；若 2025 年鉴尚未给出 2024 全序列，用最新可得年份并全局替换正文 `\PH{2024}`（正文/表题共 7 处，见 §7 占位符清单）。
- 分省：同一年份 31 省人均消费量（住户调查年鉴分省表），用于 fig6 与省级 SSR。

**B. 生产量（万吨 → Mt）**
- 猪牛禽肉分品种产量、水产品产量、禽蛋产量、牛奶（奶类）产量、粮食分品种产量；全国 + 分省（猪肉分省用于 fig6）。来源：《中国统计年鉴》农业篇 / 国家统计局公报。

**C. 贸易量（用于供给侧可得量与饲料粮对比）**
- 海关口径进出口：猪肉 HS0203（+ 杂碎 0206 是否并入需在表注声明）、牛肉 0201/0202、禽肉 0207、水产品 HS03（+1604/1605 加工品是否并入声明）、乳品 0401–0406（折原奶系数声明）、蛋 0407/0408。
- 饲料对比基准：玉米 1005、高粱 1007、大麦 1003、木薯 0714、DDGS 2303 进口量与国内玉米产量（2024）。

**D. 人口**：全国与分省年中常住人口（若只有年末，用相邻两年均值；口径写入表注）。

**E. 营养系数（附录表 `tab:coefficients`）**
- 《中国食物成分表（标准版，第 6 版）》：每 100 g 可食部能量（kcal）与蛋白（g）、可食部比例。每一论文品类选 2–4 个代表食物按消费权重加权（权重可用 CHNS 样本内该类各细目消费份额，或成分表附录的常见食物；方法写入复现文件）。在表注给出成分表条目编号。

**F. 换算系数（需选定并给出引文，写入 `tab:coefficients` 注释与复现文件）**
- 胴体/毛重 → 零售重：猪、牛、禽分别给出（FAO 2001 技术转换系数或国内文献值；给出所用值与出处，敏感性 ±10% 备查）。
- 蛋：扣种蛋与损耗比例。奶类：液态奶当量折算。
- 料肉比 FCR（配合饲料口径）：猪、肉牛（谷物精料部分）、禽、水产（投喂养殖比例 × FCR）、蛋、奶（精料）。给出所选值 + 引文（行业年鉴/文献），并保存低/高两套用于文字表述"约 \PH{XX} Mt"的稳健区间。

> 数据核对纪律：每个外部数字在 `data/applications/sources.md` 登记"数值 | 单位 | 年份 | 出处（书名+表号/网址+访问日期）"。

## 2. 表 9 `tab:guidelines`（膳食指南对照）计算规范

1. `FAH_gday[g] = Σ_k∈g NBS_kgyr[k] × 1000/365`；分组映射：谷类 = 稻谷+小麦+粗粮+豆类（豆类并入谷类的做法在表注已声明，与 DGCR"全谷物和杂豆"一致）；畜禽肉 = 猪+牛+禽（羊肉不在 12 类，表注已声明）；其余一一对应。
2. `ADJ_gday[g] = Σ_k∈g NBS_kgyr[k] × AF_national[k,2024] × 1000/365`（先逐品类乘 AF 再聚合）。
3. `Understate%[g] = (ADJ−FAH)/FAH × 100`。
4. 能量/蛋白：`kcal = Σ_k gday_k × EP_k × E_k/100`（EP=可食部，E=能量系数）；蛋白同理；动物蛋白 share = 动物源蛋白/总蛋白（动物源 = 猪牛禽+水产+蛋+奶）。
5. Assessment change 判定：比较 FAH 与 ADJ 分别落在指南区间的位置（below/within/above），生成如 `within → above` 的字符串，回填正文与表格；**同时**回填正文句式选择占位符（如 `\PH{within/near}`、`\PH{entirely above}`——若 bootstrap 2.5 分位仍 > 75 g/d 则用 entirely above，否则改写为 "with the interval largely above"）。
6. CI：对每个 b 重复 2–4，取 2.5/97.5 分位；表 9 主体只放点估计，区间写入复现文件（表注已如此声明），但正文引用的畜禽肉区间 `\PH{(XX, XX)}` 必填。

## 3. 表 10 `tab:reconciliation`（供给—消费对账）计算规范

1. 供给侧人均可得量（零售重，kg/人·年）：
   `SUP_k = (PROD_k + IM_k − EX_k − NONFOOD_k) × conv_k / POP`
   - NONFOOD：猪牛禽=0（产量已是胴体口径，损耗并入 conv 或单列）；蛋=种蛋+损耗（给比例出处）；水产=非食用（鱼粉等）扣减（渔业统计年鉴口径）；在表注/复现文件写明。
2. `GAP_k = SUP_k − FAH_k`；`CLOSED%_k = FAH_k × (AF_k − 1) / GAP_k × 100`。
3. CI：仅让 AF 随 b 变动（表注已声明 accounting components fixed）。
4. 摘要与引言用的"总体 missing meat 弥合率" `\PH{XX} percent`：对猪牛禽（可含水产，选定后全篇一致）以 GAP 为权重加权 CLOSED%。
5. 防御性检查：若某类 GAP≤0 或 CLOSED%>100，说明口径冲突（多为零售折算或非食用扣减），回到 conv/NONFOOD 排查，不允许直接截断；必要时该行加表注。

## 4. 表 11 `tab:ssr` + 图 6 + 饲料粮计算规范

1. 全国：`DEM_k = NBS_kgyr[k] × (1 或 AF_k) × POP / 1e9`（Mt）；`SSR = PROD/DEM × 100`；`Δpp = SSR_adj − SSR_unadj`。表注已声明"non-household components held fixed"，故居民口径即可；若你想更保守，把加工/损耗常数项 C 同加到两列分母（Δpp 结论不变），在复现文件记录选择。
2. 正文句 `\PH{describe which commodities cross...}`：程序判定哪些品类 unadj≥100 且 adj<100（或跨越其他政策参考线），生成一句话回填；若无跨线品类，改写为 "no commodity crosses the 100-percent line, but the margins narrow materially for ..."。
3. **图 6（fig6_ssr_dumbbell.png）**：省级猪肉 SSR（unadj vs adj，2024）。
   - `SSR_prov = PROD_pork_prov / (NBSprov_pork × AF_prov_pork × POP_prov)`；两列。
   - ggplot2 哑铃图：`geom_segment` + 两组点（空心=unadj，实心=adj），按降幅排序，x 轴 %；`geom_vline(xintercept=100, linetype="dashed")`；主产区（川豫湘鄂等）与主销区（京沪浙粤）会自然分层——若个别牧区/直辖市 SSR 极端（>300% 或 <20%），x 轴用 `scale_x_continuous(trans="log10")` 或截断+注记。
   - 输出 300 dpi PNG 至 tex 同目录，配色沿用 fig4 系列（现图为蓝—红渐变地图，本图建议中性灰段+终点用现有主色）；宽高比约 0.95\linewidth × 高 5–6 in。tex 已用 `\IfFileExists` 挂接，文件生成后重编译即自动替换占位框。
4. 饲料粮：`FEED = Σ_k∈ASF NBS_kgyr[k] × (AF_k − 1) × POP × liveconv_k × FCR_k / 1e9`（Mt）；`liveconv` 为零售/产品重→活重（或精料对应口径）系数。对比基准：占 2024 国内玉米产量 %、占 2024 玉米+高粱+大麦进口 %。低/高 FCR 两套结果存复现文件，正文取中间值。

## 5. 附录表回填

- `tab:coefficients`：填 §1E/§1F 全部系数；注释末尾的 `\PH{Fill coefficients...}` 整句删除，替换为具体来源句。
- `tab:app_sensitivity`：用 `AF_alt`（LightGBM、RF，2024 全国）重跑 §2–§4 的 6 个指标；同时把正文第 7 节末段 `\PH{hold}` 按结果改为 hold / broadly hold（若某指标方向翻转必须如实改写并在讨论 limitations 补一句）。

## 6. 摘要/引言/讨论/结论散句占位符 ↔ 数据源对照

| 位置 | 占位符 | 取值来源 |
|---|---|---|
| 摘要 | 畜禽+水产低估 `XX–XX%` | 表 9 Understate% 的两类区间端点 |
| 摘要/引言/8.1/8.2/结论 | 缺口弥合 `XX%` | §3.4 加权 CLOSED% |
| 摘要/引言/8.1/8.2/结论 | SSR 降幅 `X–X pp` | 表 11 ASF 各类 Δpp 的 min–max |
| 引言/8.2/结论 | 饲料粮 `XX Mt` | §4.4 |
| 引言/7.1/结论 | 畜禽肉 FAH、ADJ g/d、超上限 % | 表 9 畜禽行；超限% = (ADJ−75)/75×100 |
| 7.1 | 水产 below→within 两值 | 表 9 水产行（若判定不同，据实改写句子） |
| 7.1/8.2 | 奶类两值及占下限 % | 表 9 奶类行；占比 = ADJ/300×100 |
| 7.1 | 能量 +X%、蛋白 +X%、动物蛋白 share 两值 | §2.4 |
| 7.3 | 省级最大降幅 `XX pp` | fig6 底层数据 max Δ |
| 全文 | `\PH{2024}` ×7 | 实际数据年份，全局统一替换 |

回填后全局校验：`grep -c 'PH{' manuscript-FP.tex` 必须为 0；然后把导言区 `\newcommand{\PH}[1]{{\color{red}[#1]}}` 改为 `\newcommand{\PH}[1]{#1}` 留作保险。

## 7. 实现骨架（R，接入现有 tidyverse 流程）

```
analysis/applications/
├── 01_read_inputs.R        # 读 NBS/生产/贸易/人口 xlsx → tidy；单位统一 kg、Mt、person
├── 02_coefficients.R       # 成分表加权系数 + conv/FCR 表 → coefficients.csv（同步填 tab:coefficients）
├── 03_guidelines.R         # §2；输出 tbl9 + 判定字符串
├── 04_reconciliation.R     # §3；输出 tbl10 + 加权closed
├── 05_ssr_feed.R           # §4；输出 tbl11 + fig6_ssr_dumbbell.png + feed
├── 06_sensitivity.R        # §5 app_sensitivity
├── 07_bootstrap_propagate.R# 读 AF_boot，对 03–05 逐 b 重算 → CI
├── 08_export_numbers.R     # 汇总 → numbers.json（键名 = 占位符语义名）
└── fill_placeholders.R     # 读 numbers.json + placeholder_map.csv，按“出现顺序+上下文锚点”双校验替换 tex
```
`fill_placeholders.R` 的替换策略：不要按顺序盲替。为每个 `\PH` 建 `placeholder_map.csv`（锚点前 30 字符、语义键、格式化规则 sprintf），逐条 `str_replace(fixed(...))`，替换后 assert 剩余计数递减 1。

## 8. 交付验收清单

- [ ] `numbers.json` 全键有值，单位/小数位符合各表注（AF 3 位、g/d 1 位、%取整或 1 位、Mt 1 位、pp 1 位）
- [ ] 表 9/10/11、附录 A.7/A.8、fig6 全部落位；`grep -c 'PH{'` = 0
- [ ] 三遍编译无 undefined citation/reference；摘要重数词后 ≤250（回填实数后复核，当前 242 留了余量）
- [ ] 逻辑一致性：摘要—引言—7 节—8 节—结论五处同一指标数值一致（由 numbers.json 单一来源保证）
- [ ] 反向核对 3 个抽查：畜禽 g/d 用计算器手核；猪肉 CLOSED% 手核；SSR_unadj 与公开报道量级对照（猪肉应≈100 上下）
- [ ] 敏感性叙述与 A.8 结果一致（hold 措辞核对）

## 9. 可选加分项（时间允许再做）

1. FAO FBS 对照段：将调整后人均供给与 FAOSTAT FBS per-capita supply 对比一段（+1 小段文字，无新表），进一步外部验证。
2. 城乡分列指南对照：城镇畜禽超限更严重、农村奶类缺口更大——一句话+复现文件即可，防审稿人问。
3. 2020 疫情年注记：AF 时间序列在 2020 的形态一句话说明（现图 2 已含）。
