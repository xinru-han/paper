# 逐条回应：paper2_elder_econometric_audit.md（2026-07-08 修订轮）

依据 `paper2_elder_econometric_audit.md` 的"必须处理"9 项与"次要"6 项，全部落实。
代码改动分布：新增 `17_measurement_robustness.R`；修改 05/06/08/11/12/13/15/18/99 与 README。

## 必须处理项

### #1 A-line 家庭规模/记录机会机械性 → 新增 table26（17_measurement_robustness.R）
规模标准化结果（三代 vs 有非老年成年人，county-year FE，村聚类）：
- household HDDS-12（原 headline）：+0.547***
- **HDDS-12 固定记录成员数+记录餐次（rarefaction 式）：+0.142（不显著）**
- **成员个人 FGDS-10 均值：+0.068（不显著）**
- 成员并集 FGDS-10（全体）：+0.561***；**剔除老人后并集：+0.677*****；剔除儿童后并集：+0.323***
结论采纳审计建议：A-line 只解释为"三代同住家庭 48h 观察到的**餐桌/供食多样性**更高"，
明确**不支持**"提高个体饮食质量"的读法（个人层面均值为零效应）；size-dummy 分解（T4）
在正文中降格为 accounting split（household size 是 living arrangement 的定义性组成部分）。

### #2 名册构造 vs 实际同住 → 新增 table27/27b
- 用 `days_at_home`（截尾至 365）重构 resident 口径（≥180 天在家）：与名册分类一致率
  **98.9%**（全部老年户）/ 98.9%（cohabit/threegen 估计样本）；48h 有记录成员口径一致率 71.0%/62.8%。
- A-line：名册 +0.547*** / resident +0.543*** / 48h-observed +0.871***。
- B-line 两代基线老人缺口：名册 −0.294*** / resident −0.300*** / 仅保留≥180 天在家成员 −0.298***。
  登记未实住成员不驱动结果。

### #3 B-line 不作"家庭内部少分配"解释
RESULTS.md B 线标题与首句改为"**recorded** food-group diversity 更低"；
年龄控制（−0.29→−0.17 失显著）、≥3 餐次样本（+0.04 消失）、MNAR 翻转三条 caveat
从附录移入主文首段，明示"不能读作分配不平等或真实摄入更差"。

### #4 B3 改为 descriptive reconciliation
08 脚本头注、headline 文本、fig8 标题、报告标题全部重标签为
"descriptive reconciliation (accounting decomposition)"；
RESULTS.md 中"59% gap-to-household"退出 headline（仅表内保留 continuity 项并加禁引说明）；
唯一可引用结论 = allocation-specific leakage CI 跨零。摘要层不再出现漏损率。

### #5 Romano–Wolf p 值
06 脚本：p = (1+#extreme)/(1+B)，B 从 300 → 999，p 不再可能为 0（下限 0.001）；
bootstrap 抽中的村庄**重标签**（每次抽取 = 独立 cluster），避免重复村共享标签低估
bootstrap 聚类方差；正文定位为 wild cluster bootstrap（脚本 14）之外的辅助多重性控制。

### #6 县名 merge
11 脚本所有县级键改为 (provn, countyn)：`first_mention`、`county_panel` 合并、
`intensity` 选列、eld 合并 `by=c("provn","countyn")`；聚类改 `county_id=paste(provn,countyn)`；
句子抽样 by 加 provn。

### #7 table25 健康分层
退化原因：原切点 median(health) 取自全样本=1（老人自评健康众数为 1）→ 全部落入单层。
修复为老人本人健康的两个非退化切分：
- 慢性病登记（disease_raw 非空）：有病老人户缺口 −0.229**，无病 −0.188*；
- 自评健康劣于最优码（health≥2）：−0.243** vs 最优码 −0.167*。
**两层都存在相近缺口** → 不支持纯生理解释，但健康是 post-treatment，仅作描述性引用。

### #8 table21 B-line 阈值敏感性与主 estimand 对齐
重构后：与主模型完全一致（cohabit/threegen 混合户 + elder + elder×threegen + female | hh_id），
elder≥60 复现主表 **−0.294***（精确一致），elder≥65 → −0.426***；
原 pooled 全混合户无交互版本保留但明确标注"different estimand"。

### #9 GRF 口径
12 脚本：ATT → "adjusted average contrast (treated)"；CATE → "conditional contrast"；
表列名 mean_cate → mean_cond_contrast；图题改
"Honest-forest heterogeneity of the adjusted association … NOT causal"；
报告首行明示 grf 仅为 ML 异质性诊断，不提供因果识别。

## 次要项

1. 05 估计量重命名：IPW_ATT/EntropyBal_ATT/AIPW_ATT → *_adj_contrast（ATT 权重、estimand 为
   selection-on-observables 下的加权对比）。
2. Oster：robustness summary 增加 caution——δ=−44 不是识别证据，只说明在当前可观测控制下
   反向未观测选择需极强才能归零系数。
3. share 族 BH-FDR 0/30 存活：RESULTS.md 已明示 share 结果降格为 secondary（维持）。
4. 负控制改称 imperfect placebo（烹饪方式/规模/共餐也可能影响调味品份额），定位辅助诊断。
5. presence 指标溯源：06 新增 MDD-W 克重族 vs DBI-16 克重族的 any-animal 一致性检查
   （`presence_provenance_check.md`）——单位错误缩放克重但不翻转零/非零，两套独立编码
   族一致排除"错误合并继承 presence"。
6. 无抽样权重：RESULTS.md 增加 design note（调查未提供设计权重，估计不加权；
   province/county/village×year FE 序列覆盖区域构成主要担忧）。

## 主结论三层口径（RESULTS.md "Headline framing"）
1. 家庭层面：三代同住 → 观察到的 household HDDS 更高；餐桌多样性/共餐规模现象，
   adjusted association，非因果、非个体饮食质量。
2. 个体层面：户内老人**记录到的**食物组多样性更低；对年龄、餐次、代理记录敏感，
   儿童缺口更大（4 倍），不能读作对老人的分配不平等。
3. 2035 投影：方向性、小量级的 accounting 推演，非强因果预测。
