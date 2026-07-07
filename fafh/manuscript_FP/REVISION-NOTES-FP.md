# AE → Food Policy 改投说明（manuscript-FP.tex）

## 一、拒稿理由 → 修改对应

AE 主编（Ricker-Gilbert）的实质意见只有一条："**reads more as a technical note rather than quantifying what this measurement error means for nutrition and food security**"。本次修改围绕它做了三层手术：

| 层次 | 修改 | 位置 |
|---|---|---|
| **加**：量化政策含义 | 新增第 7 节 *What the measurement error means for food security and nutrition assessment*：7.1 膳食指南对照（表 9）；7.2 供给—消费对账 / missing meat 弥合率（表 10）；7.3 自给率变化 + 省级哑铃图 + 饲料粮折算（表 11、图 6）。全部结果位以 `\PH{}` 红色占位，配套计算规范见 `TODO-analysis-FP.md` | `sec:applications` |
| **改**：叙事重心从方法转向政策 | 标题、摘要（242 词，≤250 合规）、关键词（food security / nutrition / measurement error 前置，ML 后置）、引言整体重写（政策议程开篇 → missing meat 症状 → 双重缺口 → 四条发现含量化占位 → 三贡献首条即"政策量化"）；文献综述新增 2.3 小节"从测量误差到政策指标"，为第 7 节铺垫；讨论 8.1/8.2 与结论改写为围绕量化结果；第 5 节改名 *Adjustment-factor estimates* 以与第 7 节区分 | frontmatter、§1、§2.3、§8、§9 |
| **减**：去 technical note 感 | 原 2.3 方法综述压缩一半（现 2.4）；"Core estimators"六组公式整体移入新附录 B（正文留一段文字描述）；multiseed 表移入附录 A（正文留结论句）。方法在正文中的占比显著下降 | §2.4、§4.3、附录 A/B |

## 二、Food Policy 合规清单（已按 2026 年 Guide for Authors 核对）

- [x] 摘要 ≤250 词（现 242；**回填实数后需复核**）
- [x] Highlights：3–5 条、每条 ≤85 字符 → `highlights-FP.txt`（已程序验证 60–81 字符），投稿系统单独上传
- [x] 匿名稿（单盲）：作者/机构/致谢信息已移除（沿用原稿处理）
- [x] 参考文献：`elsarticle-harv`（作者—年份，Elsevier Harvard），已替换 apalike 并编译通过
- [x] 期刊定位："clear and explicit contribution to food policy debates of international interest"——引言、投稿信均落在营养监测、统计对账、自给率与全球饲料/进口预测基线三个国际议题上；且直接接续 Food Policy 2017 食物消费测量专辑（Zezza、Smith、Farfán、Fiedler & Yadav 均已在文中）
- [ ] Graphical abstract：期刊为"encouraged"非强制，可选；若做，建议用图 3（2024 各类 AF 点线图）改造
- [ ] CRediT、利益声明、数据可得性：占位已在文末，投稿系统内补作者信息

## 三、新增参考文献（9 条，全部已联网核实存在及卷期页码）

1. Bai, Zhang, Wahl & Seale (2016) *Applied Economics Letters* 23(15): 1084–1087 —— "Dining out, the missing food consumption in China"
2. Bai, Seale & Wahl (2020) *AJARE* 64(1): 150–170 —— FAFH 纳入与否对肉类需求估计的影响（与本文最直接的对话对象）
3. Ma, Huang & Rozelle (2004) *EDCC* 52(2): 445–473 —— 畜牧统计差异
4. Fukase & Martin (2016) *JAE* 67(1): 3–23 —— 需求→饲料/进口预测逻辑
5. Huang & Yang (2017) *Global Food Security* 12: 119–126 —— 中国粮食政策议程
6. Headey, Hirvonen & Hoddinott (2018) *AJAE* 100(5): 1302–1319 —— 动物源食物与营养
7. FAO (2001) *Food Balance Sheets: A Handbook* —— 平衡表口径
8. Chinese Nutrition Society (2022) 膳食指南 —— 表 9 推荐量来源
9. 中国疾控中心营养与健康所 (2019) 《中国食物成分表（标准版）》 —— 附录 A.7 系数来源

按您的既有流程，投稿前请再对 9 条做一次卷期页码复核（bib 条目在 `reference-FP.bib` 末尾集中排列，便于核对）。

## 四、遗留事项（按优先级）

1. **跑 `TODO-analysis-FP.md`**：回填 241 个 `\PH{}` 占位符（其中约 5/6 在新表格单元内）、生成 `fig6_ssr_dumbbell.png`（tex 已用 `\IfFileExists` 挂接，文件就位即自动替换占位框）。
2. 回填后把导言区 `\PH` 宏改为恒等（文件内已留注释），并复核摘要词数。
3. 投稿信 `cover-letter-FP.txt` 补作者信息；其中"前刊编辑建议量化营养与粮安含义"一句是对 desk reject 的坦诚化用，主编圈子小，如实提及利大于弊——若您不倾向提及，删除该句即可，其余自洽。
4. 建议审稿人（Editorial Manager 需填 3–5 位）：可考虑 FAFH/中国消费测量方向学者（如 Junfei Bai、Xiaohua Yu、David Abler、Kevin Chen 等），以及 2017 测量专辑作者群；注意回避合作者与同机构。
5. 篇幅：pandoc 全文（含表格与两个附录）约 12,000 词，正文散文体约 9,000+，在 Food Policy 常规区间内；若审稿要求压缩，首选把 §6 的 LOPO/temporal 两表移附录（各省一行的表体量最大）。

## 五、文件清单

```
manuscript-FP.tex      改投版主稿（编译通过，56 页，占位符红色显示）
manuscript-FP.pdf      当前编译稿（供快速通读结构）
reference-FP.bib       文献库（原 52 条 + 新增 9 条）
highlights-FP.txt      Highlights（单独上传）
cover-letter-FP.txt    投稿信草稿
TODO-analysis-FP.md    补充研究计划（Claude Code 用）
REVISION-NOTES-FP.md   本文件
fig*.png               原图 5 张 + 附录图 5 张（未改动；fig6 待生成）
```
