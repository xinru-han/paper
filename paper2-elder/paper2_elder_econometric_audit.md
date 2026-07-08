# paper2-elder 计量经济学硬伤复核报告

> 检查依据：`paper2-elder.zip` 中的 `README.md`、`RESULTS.md`、`code/*.R` 与 `outputs/tables/*.csv`。压缩包未包含论文正文，因此以下判断主要针对实证设计、代码实现和结果表述口径。

## 一、总判断

当前版本已经修正了很多高风险表述，例如把 A-line 估计改为 selection-on-observables 下的调整后关联，把 `phi1` 改为 cross-sectional slope，把 leakage 改为描述性分解，并用 MNAR、generation ladder、wild bootstrap 等补充了重要敏感性检验。因此，**没有发现会导致整篇论文必须推倒重来的单一“致命硬伤”**。

但仍有若干审稿人很可能抓住的计量问题。建议把下面“必须处理”的项目先改完，否则即使结果稳健，也容易被认为识别和解释过度。

## 二、必须处理的问题

### 1. A-line 的核心结果仍存在“家庭规模/记录机会”机械性问题

A-line 用 household HDDS-12 作为家庭层面供食多样性指标，而三代同住本身意味着家庭成员更多、年龄结构更复杂、48 小时内记录到更多食物组的机会更高。因此，`threegen -> household HDDS` 的显著正相关可能部分来自“更多人在同一家庭内被观察”的机械效应，而不完全是供食质量或菜单结构改善。

代码中已经做了 household-size dummies，并显示家庭规模虚拟变量吸收 54.6% 的 three-generation 系数。但 household size 本身是 living arrangement 的构成部分，属于 post-treatment / definitional control，不能作为严格机制分解。建议正文把该结果解释为“家庭层面观察到的供食/餐桌多样性更高”，不要写成“三代同住提高饮食质量”。最好补充至少一个标准化结果：

- 以个人为单位的平均 FGDS 或 WDDS；
- 固定家庭成员数/用餐次数后的 rarefied HDDS；
- 人均或成人等价尺度下的食物组覆盖率；
- household HDDS excluding focal elder 或 excluding children 的稳健性。

### 2. living arrangement 由户籍/成员名册构造，未充分验证“实际同住/共同用餐”

`living_arrangement` 主要由 roster 年龄结构构造。若成年子女或孙辈登记在户内但长期外出，三代同住会被误判。A-line 尤其受影响，因为家庭消费和 48h 记录更接近实际在家吃饭的人，而不是名册成员。

建议用 `days_at_home`、`home_eating_days` 或 48h 有记录成员重构一个 “resident/eating-based living arrangement” 稳健性版本。至少需要报告：

- 以名册构造的 threegen 与以实际在家/用餐成员构造的 threegen 的一致率；
- 只保留主要成员均在家、或剔除长期外出成员后的 A-line 和 B-line 主结果。

### 3. B-line elder gap 不能作为“老人被家庭内部少分配”的强证据

主表中 elder 的 FGDS 差距显著，但已经有两个结果明显削弱该解释：

- 加入年龄后，elder 系数由 -0.294 变为 -0.166，且不显著；
- 剔除 <3 recorded meals 后，elder 系数变为 0.040，完全消失；
- generation ladder 中 child deficit 约为 elder deficit 的 4 倍；
- MNAR 情景下，如果低记录餐次的老人按共同居住成年人均值重估，elder gap 会翻转为正。

因此，B-line 应表述为“同一家庭内老年人的**记录到的**食物组多样性较低”，不能表述为“家庭内部对老人存在饮食分配不平等”或“老人真实摄入更差”。若论文想保留分配机制，必须把 age/health/meal-recording caveat 放在主文而不是附录。

### 4. B3 decomposition / leakage 只能作为描述性 reconciliation，不能作为正式机制估计

`phi1` 是 household HDDS 与 elder FGDS 的横截面斜率，且 elder 自己的 48h 饮食会机械进入 household HDDS，尤其在 elder-alone / elder-only households 中污染严重。当前已做排除 elder-alone/elder-only 的检验，但 decomposition 仍然不能解释为 causal pass-through。

此外，A-line 的 `dHDDS`、B2 的 `phi1`、B3 的 reduced-form elder effect 来自不同样本和不同控制变量集合，严格来说不是同一 estimand 的结构分解。建议：

- 将标题从 “pass-through / leakage” 改为 “descriptive reconciliation” 或 “accounting decomposition”；
- 删除“泄漏率”作为 headline；
- 只保留 allocation-specific leakage CI 跨零这一结论；
- 不再把 59% gap-to-household 放在摘要或主结论中。

### 5. Romano–Wolf p 值实现需要有限样本修正，不能报告 0.000

`06_bline_gap.R` 中 Romano–Wolf p 值用 `mean(maxnull >= abs(t_obs))`，因此出现了 p=0。有限次 bootstrap 下 p 值不应为 0，应改为 `(1 + #extreme)/(1 + B)`，并将 B 提高到至少 999 或 1999。当前所有 `p_rw=0.000` 建议改为 `<0.003` 或按新 bootstrap 输出。

同时，cluster bootstrap 中重复抽中的 village 没有 relabel，建议检查是否会影响 bootstrap 的聚类方差计算。更稳妥的做法是使用成熟的 wild cluster bootstrap / randomization inference 实现，或至少把该检验定位为辅助。

### 6. county policy text 的县名匹配存在潜在 merge bug

`11_county_policy_text.R` 中部分 merge 使用 `countyn` 单独匹配，而不是 `provn + countyn` 或 county code。中国县名存在跨省重名，单用县名可能导致错误合并或重复匹配。该部分虽然只是 descriptive context，但代码层面需要修正：

- `first_mention`、`county_panel`、`intensity` 均使用 `provn + countyn` 或统一县级行政代码；
- `eld <- merge(..., by = c("provn", "countyn"))`；
- 聚类也使用唯一 county_id，而不是单独 `countyn`。

### 7. table25 健康分层没有形成有效分组

`table25_elder_health_strata.csv` 只输出了 “elder appears less healthy” 一个 stratum，没有健康组结果。因此不能在正文中引用“健康分层”作为证据。要么修复分层变量，要么删除该表和相关表述。

### 8. B-line threshold sensitivity 与主模型 estimand 不一致

`table21` 中 B-line elder gap 使用了更广的 mixed-household 样本和不含 `elder:threegen` 的模型，因此 elder>=60 的结果为 -0.200，而主表 two-generation baseline elder gap 为 -0.294。该敏感性不是主模型的直接复现。建议将 threshold sensitivity 改成与主模型完全一致的样本和模型，或者在表注中明确其是 pooled mixed-household gap。

### 9. GRF 部分仍不宜使用 ATT/CATE 语言

`12_grf_heterogeneity.R` 虽然已说明 treatment non-random，但输出仍写 “causal forest”、“ATT”、“CATE”。审稿人可能认为口径冲突。建议改为：

- “honest forest heterogeneity of adjusted association”；
- “conditional contrast” 而不是 CATE；
- “targeted subgroup pattern” 而不是 treatment-effect heterogeneity。

若保留 causal_forest 工具，正文中也应明确它只是机器学习异质性诊断，不提供因果识别。

## 三、建议作为次要修改的问题

1. A-line 的 IPW/entropy balancing/AIPW 表中估计器名称仍写 ATT，建议改成 adjusted contrast 或 weighted contrast。
2. Oster `delta_for_beta0 = -44.08` 不应解释为强识别证据，只能说在当前可观测控制下，未观测选择需要呈反向且很强才会推翻结果。
3. share family 的 BH-FDR 已经显示 0/30 survive，正文不要讲 share composition 作为稳健发现。
4. negative control（salt + condiment share）不是完美 placebo，因为做饭方式、家庭规模、共同用餐也可能影响调味品份额，只能作为辅助诊断。
5. nutrient unit audit 已经判定 FAIL。presence/absence 指标虽然比克重稳健，但仍需确认其来自原始食物组是否出现，而不是来自已经错误合并后的克重字段。
6. 若数据有抽样权重或分层设计，应补充说明为什么不用 survey weights；至少报告 province/county 固定效应下的稳健性。

## 四、建议修改后的主结论口径

建议论文最终把核心结论压缩为三层：

1. **家庭层面**：三代同住家庭在 48 小时窗口内观察到的 household HDDS 更高，这一关联在县年固定效应、村年固定效应、权重调整和置换检验下较稳定；但它主要反映家庭规模和共同用餐带来的餐桌多样性，不应解释为严格因果效应。
2. **个体层面**：在同一家庭内，老年人记录到的食物组多样性低于共同居住的非老年成年人，但该差距对年龄控制、餐次记录和潜在代理记录误差敏感，因此不能直接解释为家庭内部对老人的分配不平等。
3. **政策模拟层面**：人口老龄化和小型化可能通过家庭供食组织弱化老年人饮食多样性，但当前估计支持的是方向性、数量级较小的会计推演，不是强因果预测。

## 五、结论

目前版本的最大风险已经不再是“模型完全错了”，而是**结果解释可能比识别能力走得更远**。如果按上面建议把 A-line 解释为 household provisioning association，把 B-line 解释为 measured elder dietary diversity gap，把 B3 和 2035 projection 定位为 accounting exercise，并修复 RW p 值、county merge、健康分层和 threshold sensitivity 的代码问题，计量经济学层面的硬伤基本可以控制住。
