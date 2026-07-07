# 执行方案：工资上涨、要素替代与诱致性技术变迁——中国农业省级成本函数系统（2004–2024）

**用途**：本文件是交给 Claude Code 的完整执行规范，覆盖理论推导、数据构建、估计、post-estimation、表图与工程规范。执行顺序见第 8 节的阶段门（Phase gates）——**Phase 0 完成后必须停下等作者确认三个决策点，再进入估计**。

**语言约定**：管线代码与日志用英文变量名 + 中文注释；表图标题与最终稿件用英文。

**内部代号**：项目内部称 `TLCF-Lewis`（translog cost function, Lewis narrative）。与需求论文的惯例一致：**内部代号不得出现在任何稿件文本、表注、图注中**。

**铁律（沿用需求论文管线规范）**：
1. 稿件中每一个数字必须可追溯到 `out/` 目录下的管线输出 CSV，禁止手输、禁止估算。
2. 少数外部常数（平减指数基期、政策日期、情景假设）必须登记在 `constants.py`，逐条附来源。
3. 每一步都写 QC assert 与 manifest（复制需求论文 `build_figs.py` 的风格）。

---

## 0. 定位、研究问题与假设

**故事锚**：2004 年是三重起点——农村工资进入加速上涨期（刘易斯拐点文献：Zhang–Yang–Wang 2011, CER；蔡昉系列）、农机购置补贴元年、《全国农产品成本收益资料汇编》核算口径改革（新增土地成本、家庭用工折价改按当地雇工工价）。样本 2004–2024 恰好覆盖"劳动由丰裕转向稀缺"的完整二十年。

**研究问题**：
- RQ1：中国农业中劳动与机械（及其他要素对）的替代弹性有多大？是否随工资水平上升而变化？
- RQ2：技术进步是否存在方向性偏向（节约劳动、使用机械/化肥）？偏向的时间路径如何？
- RQ3：偏向是否响应滞后的相对要素价格变动（Hayami–Ruttan / Binswanger 诱致性创新假说）？
- RQ4（政策落点）：2004–2024 亩均实际成本上涨可分解为要素价格、单产、技术进步三部分各占多少？工资推动的"成本地板"有多厚，技术进步对冲了多少？

**可检验假设**：
- H1：劳动–机械的 Morishima 替代弹性显著为正（互为替代），且在样本期后段（高工资区间）更大。
- H2：技术进步为劳动节约型（$B_{labor}<0$）、机械使用型（$B_{mach}>0$），2010 年后加速。
- H3：劳动节约偏向对滞后 1–3 年的相对工资上涨有显著正响应；对未来价格（placebo）无响应。
- H4：分解中要素价格贡献（尤以工资）占亩均成本上涨的主导份额；技术进步项为负（对冲）。

**期刊定位**：主投 AJAE；备选 *Agricultural Economics*（与需求论文形成姊妹篇——需求端投影 2050 猪肉与饲料粮，供给端给成本与要素响应）、*China Economic Review*、*Food Policy*。

---

## 1. 理论模型与完整推导

### 1.1 生产者问题与成本函数性质

设省 $i$、年 $\tau$、品种 $c$（各品种分别估计独立系统，下文省略脚标）的代表性生产者以要素价格 $w=(w_1,\dots,w_N)$、既定产出 $y$、技术状态 $t$ 最小化成本，得成本函数

$$C(w,y,t)=\min_x\{w'x:\ f(x,t)\ge y\}. \tag{1}$$

微观理论性质：$C$ 对 $w$ 非负、非降、**一次齐次**、**凹**；对 $y$ 非降。这些性质中齐次与对称在估计中直接施加，凹性与单调性事后逐点检验（第 1.7 节）——这是需求论文"理论一致性检验"的生产端对应物。

**产出量纲说明（重要）**：汇编成本为每亩（生猪为每头），故 $C$ 为单位土地（单位头）成本，$y$ 为亩产（每头主产品产量）。由此估出的"规模弹性"是**单产集约化弹性**，不是农场规模报酬；后者在扩展 E2（省级加总）中处理，正文必须如实表述。

### 1.2 Translog 二阶近似

$$\ln C=\alpha_0+\sum_n\alpha_n\ln w_n+\alpha_y\ln y+\tfrac12\sum_n\sum_m\gamma_{nm}\ln w_n\ln w_m+\sum_n\gamma_{ny}\ln w_n\ln y+\tfrac12\gamma_{yy}(\ln y)^2$$
$$\qquad+\lambda_t t+\tfrac12\lambda_{tt}t^2+\sum_n\lambda_{nt}\,t\ln w_n+\lambda_{yt}\,t\ln y+\mu_i+u. \tag{2}$$

$t=$ 年份 $-2014$（居中），$\mu_i$ 为省份固定效应。所有 $\ln w$、$\ln y$ 围绕样本均值中心化（几何均值归一化），使一阶系数在样本均值点可解释为份额/弹性。

### 1.3 Shephard 引理与份额方程

Shephard：$x_n=\partial C/\partial w_n$。定义成本份额 $S_n\equiv w_nx_n/C$，则

$$S_n=\frac{w_n}{C}\frac{\partial C}{\partial w_n}=\frac{\partial\ln C}{\partial\ln w_n}=\alpha_n+\sum_m\gamma_{nm}\ln w_m+\gamma_{ny}\ln y+\lambda_{nt}t+\mu_{ni}+\varepsilon_n. \tag{3}$$

估计系统 = 式 (2) 的水平方程 + $N-1$ 个份额方程（删去第 $N$ 个，"其他"要素；参数由约束恢复；迭代 SUR 至收敛后结果对删哪个方程不变——需 assert 验证）。

### 1.4 参数约束

$$\text{(R1) }\sum_n\alpha_n=1;\quad\text{(R2) }\gamma_{nm}=\gamma_{mn};\quad\text{(R3) }\sum_n\gamma_{nm}=0\ \forall m;\quad\text{(R4) }\sum_n\gamma_{ny}=0;\quad\text{(R5) }\sum_n\lambda_{nt}=0. \tag{4}$$

(R1)–(R5) 联合保证对 $w$ 一次齐次且份额加总恒为 1。实现上以第 $N$ 种要素价格作 numeraire：所有方程中用 $\ln(w_m/w_N)$、$\ln(C/w_N)$，齐次性由构造满足。

### 1.5 弹性公式（完整推导）

由 $x_n=S_nC/w_n\Rightarrow\ln x_n=\ln S_n+\ln C-\ln w_n$，对 $\ln w_m$ 求导（产出与技术固定，即**产出不变的条件要素需求弹性**）：

$$\varepsilon_{nm}\equiv\frac{\partial\ln x_n}{\partial\ln w_m}\bigg|_{y,t}=\frac{1}{S_n}\frac{\partial S_n}{\partial\ln w_m}+\frac{\partial\ln C}{\partial\ln w_m}-\delta_{nm}=\frac{\gamma_{nm}}{S_n}+S_m-\delta_{nm},$$

即

$$\boxed{\ \varepsilon_{nn}=\frac{\gamma_{nn}+S_n^2-S_n}{S_n},\qquad \varepsilon_{nm}=\frac{\gamma_{nm}+S_nS_m}{S_n}\ (n\ne m).\ } \tag{5}$$

**Allen–Uzawa 偏替代弹性**：$\sigma_{nm}\equiv CC_{nm}/(C_nC_m)$。由 $C_n=CS_n/w_n$，交叉求导：

$$C_{nm}=\frac{\partial}{\partial w_m}\Big(\frac{CS_n}{w_n}\Big)=\frac{C_mS_n+C\,\partial S_n/\partial w_m}{w_n}=\frac{C}{w_nw_m}(S_nS_m+\gamma_{nm})\quad(n\ne m),$$
$$C_{nn}=\frac{C}{w_n^2}(S_n^2+\gamma_{nn}-S_n),$$

故

$$\sigma_{nm}=\frac{\gamma_{nm}+S_nS_m}{S_nS_m}=\frac{\varepsilon_{nm}}{S_m},\qquad \sigma_{nn}=\frac{\gamma_{nn}+S_n^2-S_n}{S_n^2}. \tag{6}$$

**Morishima 替代弹性（正文首选，Blackorby–Russell 1989 AER）**：

$$M_{nm}\equiv\frac{\partial\ln(x_n/x_m)}{\partial\ln w_m}=\varepsilon_{nm}-\varepsilon_{mm}. \tag{7}$$

$M_{nm}>0$ 为替代。注意 **不对称**（$M_{nm}\ne M_{mn}$）：$M_{LM}$ 度量机械价格变动下劳动/机械比的响应，$M_{ML}$ 度量工资变动下的响应——刘易斯故事的核心参数是 $M_{ML}$（工资涨→机械替代劳动的幅度），两向都报。

**Cobb–Douglas 校验**（写进单元测试）：$\gamma=0$ 时 $\varepsilon_{nn}=S_n-1$、$\varepsilon_{nm}=S_m$、$\sigma_{nm}=1$、$M_{nm}=1$，全部符合理论值。

**评估点约定**：一律在**拟合份额** $\hat S$ 处评估（与曲率检验内部一致）；观测份额版本入附录稳健性。

### 1.6 规模弹性与技术变迁

$$\epsilon_{Cy}\equiv\frac{\partial\ln C}{\partial\ln y}=\alpha_y+\gamma_{yy}\ln y+\sum_n\gamma_{ny}\ln w_n+\lambda_{yt}t,\qquad RTS=1/\epsilon_{Cy}\ \text{（单产集约化口径）}. \tag{8}$$

对偶技术变迁率（成本下降率取负号）：

$$\dot\tau_C\equiv\frac{\partial\ln C}{\partial t}=\lambda_t+\lambda_{tt}t+\sum_n\lambda_{nt}\ln w_n+\lambda_{yt}\ln y. \tag{9}$$

原始（primal）TFP 增长率（Ohta 1974）：$\;\dot{TFP}=-\dot\tau_C/\epsilon_{Cy}$。

**技术偏向**：$\partial S_n/\partial t=\lambda_{nt}$（绝对偏向）；相对偏向

$$B_n=\lambda_{nt}/S_n,\qquad B_n<0\Rightarrow n\text{-节约},\ B_n>0\Rightarrow n\text{-使用}. \tag{10}$$

Hicks 中性 $\iff\lambda_{nt}=0\ \forall n$（LR 检验，第 4.3 节）。

### 1.7 曲率与单调性（理论一致性检验）

凹性要求 $\nabla^2_{ww}C$ 半负定。对 translog，Hessian 元素为 $C_{nm}=\frac{C}{w_nw_m}(\gamma_{nm}+S_nS_m-\delta_{nm}S_n)$，因 $C,w>0$，凹性等价于矩阵

$$G(S)\equiv\Gamma+SS'-\mathrm{diag}(S)\ \text{半负定}. \tag{11}$$

由齐次性可证 $G\iota=\Gamma\iota+S(S'\iota)-S=0$（用 R3 与 $\sum S=1$），即 $G$ 恒有一个结构性零特征值。**操作规则**：逐观测点计算 $G(\hat S)$ 特征值，判定 $\lambda_{\max}(G)\le 10^{-7}$ 为满足；报告满足率（总体、分品种、分时期）。单调性：$\hat S_n>0$ 逐点检验。

**应急预案**（若核心观测区凹性满足率 < 80%）：
- C1（局部施加，Ryan–Wales 2000, *Econ. Letters*）：在归一化点（中心化后 $\ln w=0,\ln y=0,t=0$，此处 $S^*=\alpha$）令 $G^*=-AA'$（$A$ 下三角），即重参数化 $\Gamma=\mathrm{diag}(\alpha)-\alpha\alpha'-AA'$，系统变为参数非线性，改用非线性 GMM/MLE。
- C2（全局曲率）：换 Symmetric Generalized McFadden（Diewert–Wales 1987, *Econometrica*）。

### 1.8 诱致性创新：两阶段检验（Binswanger–Ruttan 传统）

**第一阶段（general-index 规格 S2，参照 Baltagi–Griffin 1988, JPE）**：把式 (3) 中 $\lambda_{nt}t$ 换成年份哑变量交互 $\sum_\tau\delta_{n\tau}D_\tau$，标准化 $\delta_{n,2004}=0$、$\sum_n\delta_{n\tau}=0\ \forall\tau$。$\delta_{n\tau}$ = 价格与产出不变条件下要素 $n$ 份额的**累计技术性移动**（累计绝对偏向）。年度偏向 $b_{n\tau}=\delta_{n\tau}-\delta_{n,\tau-1}$；定义**节约偏向** $sb_{n\tau}\equiv-b_{n\tau}$（正 = 该年技术朝节约 $n$ 移动）。

**第二阶段**：对 $n\in\{labor, mach\}$ 分别做跨品种面板回归（品种 $c$ × 年 $\tau$，约 4–6 品种 × 20 年）：

$$sb^c_{n\tau}=\theta^c+\sum_{k=1}^{3}\psi_k\,\Delta\ln\!\big(w_{n}/\bar w\big)^c_{\tau-k}+e^c_{n\tau}, \tag{12}$$

$\bar w$ 为该品种全要素 Törnqvist 价格指数（分省按产量加权到品种层面）。H3：劳动方程 $\sum_k\psi_k>0$。推断用 Driscoll–Kraay。**Placebo**：加入 $k=-1,-2$ 的未来价格变动，系数应≈0。**诚实定位**：国家层面价格与技术存在联立性，此检验以品种间暴露差异 + 滞后结构 + placebo 缓解，正文表述为"与诱致性创新假说一致的证据"，不宣称严格因果——审稿人友好。

### 1.9 扩展 E2：省级加总的受限可变成本函数与影子地租

每亩数据下土地量恒为 1，无法直接对土地求导。加总到省：$TVC_{prov}=$ 亩均可变成本 × 播种面积，$Y=$ 总产量，$L=$ 播种面积（年内准固定）。估 translog $VC(w_v,Y,L,t)$（对 $w_v$ 一次齐次），影子地租

$$r^*=-\frac{\partial VC}{\partial L}=-\frac{VC}{L}\cdot\frac{\partial\ln VC}{\partial\ln L}, \tag{13}$$

与汇编"流转地租金"逐省逐年对表（一张好图 + 一段好讨论：要素市场扭曲/流转市场发育）。识别告诫：面积本身是选择变量，此模块定位为描述性扩展，非主结果。

---

## 2. 数据构建

### 2.1 来源

- 《全国农产品成本收益资料汇编》2005–2025 卷（生产年 2004–2024），省级、分品种、每亩/每头分项成本与实物量。**作者提供原始提取件**（Excel/CSV/扫描表均可，Phase 0 先做 inventory）。
- NBS 省级农业生产资料（及服务）价格分类指数：化肥、农药、机械化农具、种子、饲料、农用机油等；农村 CPI（平减用）。
- 可选外部数据（决策点 DP4）：气象（生长季降水/温度距平，作产量 IV）；农民工月均工资（替代工资序列稳健性）。

### 2.2 品种与样本

主分析（分别独立系统）：**玉米**（pilot）、小麦、稻谷（先用汇编稻谷平均口径，籼粳分列入稳健性）、大豆；**生猪**单独系统（并按散养/小/中/大规模分别估计——机械化与规模故事的畜牧版，且与需求论文的猪肉主线呼应）。每品种取主产省，预期 N ≈ 15–20 省 × 21 年 ≈ 300–420 省年观测，5 要素系统足够。进入/退出省份记录在 coverage matrix。

### 2.3 成本科目 → 要素映射（默认方案，DP2 待确认）

种植业 5 要素基线：

| 要素 | 汇编科目 | 价格来源 |
|---|---|---|
| labor 劳动 | 家庭用工折价 + 雇工费用 | 劳动日工价（汇编直接给出）|
| mach 机械动力与服务 | 机械作业费 + 排灌费 + 畜力费(+燃料动力费若列示) | NBS 机械化农具/农用机油/服务指数拼接 + 锚定 |
| fert 化肥 | 化肥费 | **单位值**：化肥费 ÷ 折纯量（汇编两项都有，直接得元/公斤纯养分）|
| seed 种子 | 种子费 | NBS 种子分类指数拼接锚定（若汇编有用种量则用单位值优先）|
| other 其他材料 | 农药 + 农膜 + 其他直接费用 + 技术服务费等 | 子指数按份额 Törnqvist 合成 |

**土地（DP3）**：基线 = 可变成本系统（排除土地成本，视为准固定）；稳健性 = 6 要素总成本（土地价格用汇编流转地租金）；扩展 = E2。

生猪 5 要素基线：feed（精饲料+青粗，价格用单位值 = 精饲料费÷精饲料量）、piglet（仔猪费，价格 = 仔猪进价）、labor、energy（燃料动力+水费）、other（医疗防疫+死亡损失+其他）。

### 2.4 价格构建规则（优先级）

1. **单位值优先**：科目同时有金额与实物量 → 直接除（化肥、精饲料、仔猪、劳动）。质量混杂（Deaton 问题）由折纯口径/日工价口径缓解，正文注明。
2. **指数拼接锚定**：只有分类指数 → 选一个锚定年（有单位值或权威绝对价的年份）把指数链式还原成绝对价格水平。份额系统其实只需相对价格，锚定主要服务于图表可读性。
3. 每条价格序列写入 `price_construction_log.csv`：来源、口径、拼接点、锚定值与出处。
4. 平减：份额估计**不需要**平减（齐次性下只用相对价格）；实际工资叙事图与成本分解用省农村 CPI，登记 `constants.py`。

### 2.5 数据 schema（`data/panel_{crop}.csv`）

`crop, province, region, year, C_total, q_output`（亩产 kg/亩或每头 kg）`, S_labor, S_mach, S_fert, S_seed, S_other, w_labor, w_mach, w_fert, w_seed, w_other` + 审计用原始分项列（labor_days, fert_kg, cost_* 各科目）。QC assert：份额加总 = 1（容差 1e-8）、无负值、价格 > 0、单位值与指数交叉校验相关系数报告。

### 2.6 识别与内生性阶梯

- 价格变异结构诊断（Phase 0 必做）：各 $\ln(w_m/w_N)$ 对年份哑变量回归的 $R^2$、省内标准差——若相对价格几乎全是全国性时间变异，省 FE + 年 FE 会抽干识别。**基线**：省 FE + 品种内区域×时期段（4 区域 × 4 时期）效应，不放全套年 FE（年 FE 只在 S2 偏向路径规格里以份额方程年哑变量形式出现）。
- 产量内生性三档：Spec A 基线用实际 $\ln y$；Spec B 用预期产量（省内该品种前 3 年亩产移动平均）；Spec C 气象 IV + 3SLS（需外部数据，DP4）。主表 A，稳健性 B，若取数则加 C。
- 工资内生性（技术反哺工资）：以滞后工资规格作稳健性；shift-share 非农需求 IV 留作后续升级，不进本文基线。

---

## 3. 估计程序（Claude Code 实现规范）

### 3.1 系统与归一化

每品种一个系统：$\ln(C/w_N)$ 方程 + $S_1..S_{N-1}$（删 other）。回归元为中心化的 $\ln(w_m/w_N)$、$\ln y$、$t$。省份哑变量进每个方程。

### 3.2 受约束 ITSUR（自写实现，纯 numpy/scipy）

1. 构造自由参数向量 $\theta$（对称与齐次由参数映射矩阵内建：只估 $\gamma_{nm}, n\le m<N$，其余由 R1–R5 恢复），拼大设计矩阵使跨方程共享参数。
2. 逐方程 OLS → 残差 → $\hat\Sigma$（J×J）。
3. FGLS：$\hat\theta=[X'(\hat\Sigma^{-1}\!\otimes\!I)X]^{-1}X'(\hat\Sigma^{-1}\!\otimes\!I)y$；更新 $\hat\Sigma$；迭代至 $\|\Delta\theta\|_\infty<10^{-10}$（等价 FIML）。
4. **不变性 assert**：改删另一份额方程重估，$\max|\Delta\theta|<10^{-6}$。
5. **CD 单元测试**：仿真 Cobb–Douglas 数据，回收 $\gamma\approx0$ 且弹性命中理论值（式 5–7 校验）。

### 3.3 推断

主推断 = **省份 block bootstrap**（整省重抽，B=500，pilot 200，seed=20260703）：每次重跑完整 ITSUR，存参数抽取 `bootstrap_parameter_draws_{crop}.csv`；所有弹性/偏向/分解统计量给 percentile 95% CI；记录每 draw 收敛与凹性满足率（沿用需求论文 bootstrap 追踪惯例）。附录给均值点 delta 法标准误作交叉核对。局限如实注明：省 block bootstrap 不处理跨省共同冲击——由区域×时期效应部分吸收。

### 3.4 两套主规格

- **S1（参数化趋势）**：式 (2)–(3) 原样，出主表（参数、弹性、偏向、检验、分解）。
- **S2（general index）**：份额方程年哑变量版，出偏向路径 $\delta_{n\tau}$ 与诱致性第二阶段（式 12）。

---

## 4. Post-estimation（全部从 `out/*.csv` 生成）

1. **弹性表**：$\varepsilon$、$\sigma$、$M$ 全矩阵，按四个时期（2004–08 / 09–14 / 15–19 / 20–24）在时期均值点评估，bootstrap CI。
2. **弹性演化曲线**：逐观测点 $M_{ML}$（工资变动方向的劳动–机械 Morishima）对实际工资作图 + bootstrap 带——需求论文 Figure 3 的生产端同构图，是本文招牌图。
3. **假设检验表**（LR/Wald，ITSUR 下用似然比）：位似性（$\gamma_{ny}=0\,\forall n$）、齐次技术（追加 $\gamma_{yy}=0$）、Hicks 中性（$\lambda_{nt}=0\,\forall n$）、无技术变迁（$\lambda_t=\lambda_{tt}=\lambda_{nt}=\lambda_{yt}=0$）、Cobb–Douglas（$\gamma_{nm}=0$）。
4. **偏向表**：$\lambda_{nt}$、$B_n=\lambda_{nt}/\bar S_n$、分类（节约/使用）、CI；S2 的累计偏向路径图。
5. **诱致性创新**：式 (12) 回归表（劳动、机械各一栏；累计响应 $\sum\psi_k$；placebo 列；分时期）。
6. **成本增长分解**（Törnqvist 离散化）：对每品种每省 2004→2024 及分段，
$$\Delta\ln C^{real}\approx\sum_n\bar S_n\Delta\ln w_n^{real}+\bar\epsilon_{Cy}\Delta\ln y+\widehat{\dot\tau}_C\cdot\Delta t+\text{residual},$$
省份按产量加权到全国，残差如实报告。堆叠柱图 + 表（直接回应"成本地板"与中外成本差距讨论）。
7. **规模（集约化）弹性路径**与 primal TFP 率路径（Ohta 公式）。
8. **理论一致性表**：凹性逐点满足率、单调性满足率（总体/分品种/分时期/bootstrap draws）。
9. **OOS**：2004–2021 训练 → 预测 2022–24 份额；RMSE 对比基准 =（i）受约束 Cobb–Douglas 系统（ii）随机游走份额。需求论文 Figure 7 的翻版。
10. **情景（克制版）**：在 2024 评估点，登记假设"实际工资至 2035 年累计 +50%（≈3.8%/年）"，其余不变，由系统推机械份额与亩均成本变化；明确标注 partial-equilibrium、产出条件不变。
11. **E2 影子地租 vs 流转租金**对比图（若 DP3 选做）。

---

## 5. 表图清单（文件名预分配）

**Tables**（`tables/`，均由 `build_tables.py` 从 CSV 生成）：
T1 描述统计（分时期份额与实际价格）；T2 参数估计（玉米主表，其余品种附录）；T3 假设检验；T4 自价格弹性 + Morishima 矩阵（分时期，CI）；T5 技术偏向；T6 诱致性创新回归；T7 成本增长分解；T8 OOS RMSE；T9 稳健性摘要。附录：凹性满足率、不变性检验、价格构建日志摘要、覆盖矩阵。

**Figures**（`figs/`，`build_figs.py`，300 dpi，serif，与需求论文 rcParams 一致）：
F1 动机图：实际日工价、机械服务价、亩用工天数、机械费份额四联时序（2004–2024，分品种）——"刘易斯一图"；F2 拟合优度（fitted vs observed 份额散点，需求论文 Fig 2 同构）；F3 $M_{ML}$ 对实际工资的演化曲线 + bootstrap 带；F4 累计偏向路径 $\delta_{n\tau}$ + CI；F5 成本分解堆叠柱；F6 OOS 对比；F7 情景图（可选）；F8 影子地租 vs 流转租金（E2，可选）。

---

## 6. 稳健性矩阵

要素聚合（4 要素合并 seed+other；6 要素含地）× 价格来源（单位值 vs 指数拼接）× 产量处理（A/B/C）× 时期（剔除 2020–22 疫情年；前后半段分估）× 函数形式（凹性不达标则 C1/C2）× 稻谷籼粳分列 × 生猪分规模 × 观测份额 vs 拟合份额评估点。结果汇总进 T9，一表打尽。

---

## 7. 工程规范与 QC

```
prod/
  data_raw/            # 汇编提取件 + NBS 指数（作者提供）
  build_data.py        # → data/panel_{crop}.csv, price_construction_log.csv, data_audit.md
  constants.py         # 外部常数登记（逐条来源）
  estimate.py          # → out/params_{crop}.csv, fitted_shares_{crop}.csv
  bootstrap.py         # → out/bootstrap_parameter_draws_{crop}.csv, draw_metrics.csv
  postest.py           # → out/elasticities_*.csv, tests_*.csv, bias_*.csv, decomp_*.csv, oos_*.csv
  build_tables.py / build_figs.py  # → tables/, figs/, manifest.json
```

**必备 asserts**：份额加总=1；对称性数值成立；ITSUR 不变性 <1e-6；CD 单元测试通过；弹性可从存档参数精确复现（<1e-10，同需求论文 `eta replication` 惯例）；每张表每张图的数字均产自 `out/` CSV；manifest 记录版本、seed、B、凹性满足率、收敛率。

---

## 8. 阶段与决策门

**Phase 0 — 数据审计（先做，做完停）**：inventory 全部提取件；生成覆盖矩阵（品种×省×年）；价格序列清单（哪些能走单位值、哪些只有指数、指数起讫年）；价格变异结构诊断（2.6）；核实 2004 卷口径改革细节（土地成本、家庭用工折价基准）。产出 `data_audit.md`，**停下等作者确认**：
- **DP1**：生产资料/服务价格数据是分类指数还是绝对水平？锚定方案选择。
- **DP2**：排灌费、燃料动力、畜力费的要素归属确认（默认并入 mach）。
- **DP3**：土地处理（基线可变成本 / 6 要素 / E2）；生猪是否分规模估计。
- **DP4**：是否取气象数据做 IV、是否取农民工工资做替代序列。

**Phase 1 — 玉米 pilot**：端到端跑通（估计+postest+F1–F3），验收标准：不变性通过、凹性满足率 ≥80%（否则触发 C1/C2 并再确认）、bootstrap 收敛率报告。
**Phase 2 — 全品种 + 生猪。**
**Phase 3 — 稳健性 + 诱致性创新 + E2。**
**Phase 4 — 全套表图 + 英文稿件骨架。**

---

## 9. 论文骨架（英文稿）

1 Introduction（刘易斯锚 + 三重 2004 起点 + 贡献三点：省级面板系统弹性、偏向路径与诱致性检验、成本分解）；2 Policy background（工资、农机补贴、社会化服务）；3 Model（第 1 节压缩版）；4 Data（汇编 + 价格构建，附录放日志）；5 Results（弹性 → 偏向 → 诱致性 → 分解）；6 Robustness & validation（凹性、OOS、稳健性矩阵）；7 Conclusion & policy（成本地板、机械/服务政策、与需求论文 2050 投影的供需对接一段）。

---

## 10. 参考文献（**投稿前逐条核验**，此处仅为工作清单）

Binswanger 1974 AER（多要素技术偏向度量）; Binswanger 1974 AJAE（成本函数法估要素需求与替代弹性）; Christensen–Jorgenson–Lau 1973 REStat; Berndt–Wood 1975 REStat; Blackorby–Russell 1989 AER; Diewert–Wales 1987 Econometrica; Ryan–Wales 2000 Economics Letters; Ohta 1974; Baltagi–Griffin 1988 JPE; Driscoll–Kraay 1998 REStat; Hayami–Ruttan 1985; Zhang–Yang–Wang 2011 China Economic Review（刘易斯拐点）; 蔡昉相关; Zhang–Yang–Reardon 2017 CER（机械外包服务集群）; 中国农业机械化/要素替代实证（Wang/Yamauchi 等，具体出处待核）; Jin–Huang–Rozelle 农业 TFP 系列（待核）。
