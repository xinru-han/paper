# `fooddem` ado 文件参考手册

本目录的 `ado/` 是一个可复用的 Stata 食物需求系统包。它以任意数量
`K >= 3` 的食品组为输入，统一完成 AIDS、QUAIDS、EASI 和带预先承诺的
GEASI 需求系统估计，并提供零消费、单位价值、支出内生性、模型选择、
弹性、收入传导和理论正则性诊断。

本手册描述当前实现的实际接口、输出及限制。所有价格和支出变量在传给
估计器前均须为自然对数。

## 安装与最小工作流

在本项目内运行时，先将本地目录加入 Stata 的 ado 搜索路径：

```stata
adopath ++ "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/ado"
help fooddem
```

一个六品类、两步 GMM EASI 的典型工作流如下。变量名只是示例；`w1-w6`
必须是完整食品支出中的预算份额，`lp1-lp6` 和 `lnx` 分别是社区价格和
食品总支出的对数。

```stata
fooddem, model(easi) shares(w1-w6) prices(lp1-lp6) expenditure(lnx) ///
    order(1) demographics(urban hhsize year_2024) ///
    endogeneity(iv) instruments(iv_log iv_inverse) cluster(village_year) ///
    gmmsteps(2)

fooddem_firststage using "outputs/firststage.csv", replace
fooddem_tests      using "outputs/tests.csv", demographics(urban hhsize year_2024) replace
fooddem_elasticities using "outputs/elasticities.csv", replace
fooddem_regularity   using "outputs/regularity.csv", replace
fooddem_export       using "outputs/parameters.csv", replace
```

`using` 的文件名以 `.dta` 结尾时，导出 Stata 数据集；其他扩展名导出
CSV。所有写文件的命令均需要已有文件时显式使用 `replace`。

## 包的设计

### 可直接调用的命令

| 命令 | 用途 |
| --- | --- |
| `fooddem` | 主估计命令；估计 AIDS、QUAIDS、EASI 或 GEASI。 |
| `fooddem_p` | `predict` 后估计命令；产生各品类拟合预算份额。 |
| `fooddem_select` | 批量估计候选模型并进行函数形式和阶数选择。 |
| `fooddem_tests` | 输出模型阶数、人口项、内生性、过度识别等联合检验。 |
| `fooddem_firststage` | 输出排除工具变量的联合和条件一阶段诊断。 |
| `fooddem_endogtest` | 将已保存的一阶段、控制函数和过度识别结果返回至 `r()`。 |
| `fooddem_elasticities` | 数值计算 Marshallian、Hicksian 和支出弹性。 |
| `fooddem_regularity` | 检查加总、份额、单调性、Slutsky 对称性及曲率。 |
| `fooddem_demographics` | 计算人口特征对预测份额的局部或离散影响。 |
| `fooddem_income` | 二、三阶段预算下的收入、数量、价值和质量弹性。 |
| `fooddem_uvprice` | 按 Deaton 或市场中位数法恢复单位价值稳健性价格。 |
| `fooddem_precommitments` | 导出 GEASI 的预先承诺数量及 delta-method 标准误。 |
| `fooddem_export` | 将系数、标准误和检验统计量导出为整洁长表。 |

### 内部命令

下列文件由 `fooddem` 自动调用，通常不应单独执行：

| 文件 | 内部职责 |
| --- | --- |
| `fooddem_gmm.ado` | Stata `gmm` 的 AIDS/QUAIDS 矩条件求值器。 |
| `nlsurfooddem.ado` | Stata `nlsur` 的 AIDS/QUAIDS 非线性回归求值器。 |
| `fooddem_easi_linear.ado` | 普通 EASI GMM 的受约束线性初始值估计器。 |
| `fooddem_easi_gmm.ado` | 精确 EASI/GEASI 的 Mata 非线性 GMM 求解器。 |

这四个命令依赖主命令设置的内部上下文、全局宏和参数命名规则；跳过
`fooddem` 直接调用不会形成受支持的估计结果。

## `fooddem`：主估计器

### 语法

```stata
fooddem [if] [in], model(aids|quaids|easi) ///
    shares(varlist) prices(varlist) expenditure(varname) ///
    [ estimator(gmm|nlsur) order(#) demographics(varlist) ///
      quantities(varlist) selection(none|sy) selectvars(varlist) ///
      endogeneity(none|iv|cf) instruments(varlist) cluster(varname) ///
      precommitment from(matrix) gmmsteps(1|2) iterate(#) tolerance(#) ]
```

`shares()`、`prices()` 的变量数必须相同，记为 `K`，且 `K >= 3`。每一行
的份额必须均在 `[0,1]` 内并加总为 1（容差 `1e-8`）。`prices()` 与
`expenditure()` 必须已经取对数。命令在所有结构变量上作共同样本标记，
因此结果不混入不同方程的样本。

默认值是 `estimator(gmm)`、`selection(none)`、`endogeneity(none)` 和两
步 GMM。系统实际估计前 `K-1` 个方程，并依据加总约束重构第 `K` 个方程。

### 模型

| `model()` | Engel 曲线和价格结构 |
| --- | --- |
| `aids` | 线性 AIDS。 |
| `quaids` | AIDS 加入二次对数实际支出项。 |
| `easi` | 多项式 EASI；`order()` 是最高 Engel 阶数。 |
| `easi, precommitment` | GEASI；在 EASI 的可支配支出中估计品类预先承诺。 |

所有模型都在参数化中施加加总、价格齐次性和 Slutsky 对称性。AIDS/QUAIDS
的价格指数中同时纳入人口项和控制函数残差，避免这些平移项破坏条件可积
性。EASI 使用精确隐式效用

```text
y = x - w' p + 0.5 p' A p
```

而不是将 `w'p` 机械替换为观测值的线性近似。EASI 的 `order()` 必须至少为
1 且小于 `K`；更高阶模型并非自动更优，应由 `fooddem_select` 和诊断检验
决定。

### 主要选项

| 选项 | 含义与约束 |
| --- | --- |
| `estimator(gmm)` | 默认。允许普通、IV 和控制函数设定；EASI/GEASI 使用内部精确 GMM。 |
| `estimator(nlsur)` | 非线性 SUR；不支持 `endogeneity(iv)`，内生性只能使用 `cf`。 |
| `order(#)` | EASI 的最高 Engel 阶；QUAIDS 固定为二阶；AIDS 固定为一阶。 |
| `demographics(varlist)` | 人口、地区或时间控制变量。其效应进入各方程，并在 AIDS/QUAIDS 的价格指数中一致处理。 |
| `quantities(varlist)` | 与品类一一对应的消费数量；仅 `selection(sy)` 必需。 |
| `selection(sy)` | Shonkwiler-Yen 两步零消费修正。先估计各品类参与 Probit，再把参与概率和逆 Mills 项纳入系统。 |
| `selectvars(varlist)` | 参与方程额外解释变量；也进入后续预测所需的数据上下文。 |
| `endogeneity(iv)` | 将 `instruments()` 作为排除工具变量，采用 IV-GMM。 |
| `endogeneity(cf)` | 先对总食品支出建一阶段，令其残差进入需求方程。 |
| `instruments(varlist)` | IV 或控制函数的一阶段排除变量；选 IV/CF 时必填。 |
| `cluster(varname)` | GMM、结构方程、一阶段和参与方程的聚类变量。 |
| `gmmsteps(1|2)` | 一步为模型筛选的恒等权重 GMM；两步使用有效权重和聚类稳健协方差。 |
| `precommitment` | 仅 EASI；改为 GEASI。 |
| `from(matrix)` | 以兼容参数向量作为初值，适合用已收敛 EASI 结果 warm start GEASI。 |
| `iterate(#)` / `tolerance(#)` | EASI/GEASI 非线性求解器的迭代上限和收敛容差。 |

### 零消费：`selection(sy)`

对每个食品组，包先以数量是否大于零定义参与变量，并以价格、支出、人口
项和 `selectvars()` 估计 Probit。结构方程使用相应的预测参与概率和逆
Mills 项修正零消费选择。若某组参与率不低于 98%，该 Probit 被视为近乎
完全参与而自动旁路，参与概率设为 1，避免不可识别的 Probit 造成伪修正；
参与率不高于 2% 时命令停止并要求重新定义品类或样本。

预测和所有数值反事实会重新计算活跃参与方程的概率与修正项。因此价格、
支出或人口特征变化不会错误地固定零消费修正。解析结构方程协方差条件于
第一步 Probit；若实际存在显著审查，应按抽样聚类对完整两步流程 bootstrap。

### 支出内生性与工具变量

`iv` 用工具变量直接构建 GMM 矩条件；`cf` 则将总支出一阶段残差纳入份额方
程。非线性 EASI 的工具矩条件自动包含支出及其多项式项的工具化信息。工具
变量只解决在给定排除限制成立时的支出内生性，不能自动解决价格测量误差、
共同冲击或弱工具变量问题。

一步 GMM 的 J 统计量是恒等权重下的拟合指标，不能解释为 Hansen 过度识别
检验；仅两步 GMM 的相应 p 值可作为 Hansen 检验。应同时调用
`fooddem_firststage` 报告联合 F、逐个工具条件 F 和部分 `R^2`，并在弱工具
情形做工具集合敏感性分析或弱识别稳健推断。

### GEASI 预先承诺

GEASI 以有界变换 `c = scale * tanh(theta)` 表示预先承诺数量，保证搜索过程
处于可行区域，并把总承诺限制在总食品支出的 50% 以下。`c` 可以为正或负；
负值不自动具有“承诺”的经济含义。当前实现估计常数承诺，不支持承诺数量
随人口特征变化，因为该扩展在一般样本中容易引起矩条件与参数的秩不足。

### 估计结果

除标准 `e(b)`、`e(V)`、`e(N)` 外，主命令保存：

| 保存内容 | 说明 |
| --- | --- |
| `e(fooddem_model)` / `e(fooddem_estimator)` | 模型与估计器名称。 |
| `e(fooddem_shares)` / `e(fooddem_prices)` | 原始预算份额和对数价格变量列表。 |
| `e(fooddem_expenditure)` | 原始对数支出变量。 |
| `e(fooddem_demographics)` | 人口特征变量列表。 |
| `e(fooddem_selection)` / `e(fooddem_syactive)` | 零消费设定及活跃的 SY 方程。 |
| `e(fooddem_endogeneity)` / `e(fooddem_instruments)` | 内生性设定和排除工具变量。 |
| `e(fooddem_cluster)` | 聚类变量。 |
| `e(fooddem_precommitment)` / `e(fooddem_cscales)` | GEASI 设定及承诺变换尺度。 |
| `e(fooddem_goods)` / `e(fooddem_order)` / `e(fooddem_npar)` | 食品组数、Engel 阶数和参数数。 |
| `e(J)`、`e(J_df)` | GMM J 统计量和自由度；两步才可作 Hansen 检验。 |
| `e(firststage_F)`、`e(firststage_p)`、`e(firststage_r2)` | 有工具变量时保存的一阶段概览。 |
| `e(predict)` | 后估计预测程序 `fooddem_p`。 |

还可使用 `ereturn list` 查看完整内容。

## 预测与反事实：`fooddem_p`

### 语法

```stata
predict neww1 neww2 ... newwK
```

该命令只能在最近一次 `fooddem` 之后使用，且必须给出恰好 `K` 个新的数值
变量。它重新建立估计时的中心化数据、控制函数与 SY 修正，并产生完整 `K`
个预测份额。

对 EASI/GEASI，预测时求解隐式效用方程的全部实根，并选择最接近观测隐式
效用的稳定根。若不存在稳定根，命令以返回码 430 停止，而不是悄悄输出错误
反事实。进行价格、收入或人口反事实时，可临时修改原始 `prices()`、
`expenditure()` 或 `demographics()` 变量后再 `predict`；应在每次扰动后恢复
原数据。

## 模型选择：`fooddem_select`

### 语法

```stata
fooddem_select using filename [if] [in], ///
    shares(varlist) prices(varlist) expenditure(varname) ///
    [ estimator(gmm|nlsur) maxorder(3) demographics(varlist) ///
      quantities(varlist) selection(none|sy) selectvars(varlist) ///
      endogeneity(none|iv|cf) instruments(varlist) cluster(varname) ///
      gmmsteps(1|2) iterate(#) tolerance(#) geasi replace ]
```

该命令依次估计 AIDS、QUAIDS 和 EASI(1) 至 EASI(`maxorder`)，并把
`maxorder` 自动限制为 `K-1`。指定 `geasi` 时，还以已收敛 EASI 为初值估计
GEASI。输出中的每行包括模型、阶数、GMM 步数、返回码、样本数、参数数、
收敛状态、J/RSS、AIC/BIC、最高 Engel 阶联合检验和预先承诺联合检验。

选择规则先在同一家族内进行嵌套检验：QUAIDS 的二次项、EASI 的最高多项式
阶数；再用 BIC 比较胜出的 AIDS/QUAIDS 与 EASI 家族。BIC 是非嵌套比较的
辅助准则，不替代经济理论、识别诊断和样本外稳健性。命令返回
`r(preferred_model)`、`r(preferred_order)`、`r(preferred_bic)` 和
`r(preferred_estimate)`；EASI 成为优选时也返回对应 EASI 结果。

## 估计后检验

### `fooddem_tests`

```stata
fooddem_tests using filename, [demographics(varlist) replace]
```

在现有 `fooddem` 结果上导出可用的联合 Wald 检验：QUAIDS/EASI 的最高 Engel
阶、指定人口项、所有平移项、控制函数残差、活跃 SY 项和 GEASI 承诺项。它还
报告 GMM 过度识别标签、工具变量一阶段 F 以及理论约束状态。传入的
`demographics()` 必须是估计时已包含的变量的子集。

对于一步 GMM，过度识别行会明确标为恒等权重 J，p 值留空；两步时才标为
Hansen J。该命令不把不适用于当前模型的检验伪装为零或显著。

### `fooddem_firststage`

```stata
fooddem_firststage using filename, [replace]
```

要求最近的模型包含排除工具变量。它以原始对数食品支出为因变量，在结构
模型的价格、人口项、选择方程变量基础上加入工具变量，输出：

```text
test, instrument, F, df_num, df_den, p_value, partial_R2, firststage_R2, N
```

输出有一行联合排除工具检验，并对每个工具变量给出在其余工具条件下的 F
检验。F 的协方差使用模型的稳健或聚类设定；部分 `R^2` 来自受限与非受限
OLS 残差平方和，故它本身不是聚类稳健统计量。该诊断不提供弱 IV 稳健的
结构推断。

### `fooddem_endogtest`

```stata
fooddem_endogtest
return list
```

不写文件，直接将当前估计中保存的一阶段 F/p/`R^2`、控制函数联合检验（如
适用）、GMM J、J 自由度和 Hansen p 值返回至 `r()`。`r(overid_is_Hansen)`
用于区分两步 Hansen 与一步恒等权重 J。

## 弹性与人口效应

### `fooddem_elasticities`

```stata
fooddem_elasticities using filename, [step(.001) replace]
```

使用比例扰动 `h = ln(1 + step)` 的中心差分，计算每户的：

- 支出弹性（每个品类一行）；
- Marshallian 价格弹性（全部 `K x K` 组合）；
- Hicksian 价格弹性（全部 `K x K` 组合）。

输出字段为 `elasticity_type`、`demand_good`、`shock_good`、`elasticity`、
`std_dev`、`p10`、`p50`、`p90`、`n_valid`。其中 `std_dev` 是户间弹性异质性
的标准差，**不是** 参数估计标准误。数值扰动时会重新求 EASI 根和 SY 参与
修正；`0 < step <= .1`。

### `fooddem_regularity`

```stata
fooddem_regularity using filename, [step(.001) replace]
```

该命令以同样的数值导数检查并导出：加总最大误差、预测份额为正的比例、
正支出弹性比例、负 Hicksian 自价格弹性比例、Slutsky 对称性最大误差，以及
对称化 Slutsky 矩阵最大特征值。它也返回 `r(hicksian)` 和 `r(slutsky)`。

加总、齐次性和对称性已在潜在需求系统中施加；曲率/负半定性没有施加，
因而是实证诊断而非保证。SY 修正后的无条件需求也可能不完全继承潜在系统
的有限样本正则性。

### `fooddem_demographics`

```stata
fooddem_demographics using filename, [step(.001) replace]
```

需要估计中存在 `demographics()`。二元人口变量（样本取值严格为 0/1）采用
从 0 到 1 的离散预测差；连续变量采用 1% 乘法扰动的局部份额效应。输出
`demographic`、`effect_type`、`good`、`effect`、`n_valid`。这些是预测效应，
目前不含参数不确定性。

## 收入、数量和质量：`fooddem_income`

### 语法

```stata
fooddem_income using filename, income(varname) ///
    [ values(varlist) controls(varlist) id(varname) step(.001) ///
      valuemethod(ppml|logols) cluster(varname) replace ]
```

命令在当前需求系统基础上构建二、三阶段预算分解：

1. 对数总食品支出回归于对数收入、收入倒数和可选控制变量，得到总食品支出
   对收入的弹性；
2. 用 `fooddem_p` 的支出反事实计算条件食品组数量/支出弹性，并与第一步
   相乘，得到无条件数量收入弹性；
3. 若给出各食品组 `values()`，逐组估计商品价值收入弹性，再以“价值弹性
   减数量弹性”得到质量/来源弹性。

默认 `valuemethod(ppml)`，保留零商品价值；`logols` 只适合零值已被合理处理
的样本。`id()` 在该命令的工作样本中必须唯一。输出是**户级长表**，包含
收入、控制变量、总支出弹性、每组支出/数量/价值/质量收入弹性及估计方法；
它通常含微观信息，应在公开版本控制前先聚合或脱敏。

## 单位价值价格恢复：`fooddem_uvprice`

### 语法

```stata
fooddem_uvprice [if] [in], quantities(varlist) market(varlist) ///
    generate(prefix) [ unitvalues(varlist) | values(varlist) ] ///
    [ demographics(varlist) method(deaton|median) mincell(3) trim(1) ///
      fallback1(varlist) fallback2(varlist) fallback3(varlist) ///
      allowoverall complete source(prefix) audit(filename) replace ]
```

`unitvalues()` 与 `values()` 二选一；后者自动计算 `values()/quantities()`。
两者与 `quantities()` 必须均有 `K` 列。`market()` 为第一层共同市场标识，
可以是一个或多个变量。

- `method(deaton)`：在市场内对数单位价值回归中控制消费数量和人口特征，
  再由市场均值净化质量和数量效应，恢复相对共同市场价格；
- `method(median)`：取市场内单位价值中位数，适合作为透明的稳健性比较。

小于 `mincell()` 的市场不生成“精确市场价格”。可依次用
`fallback1()`、`fallback2()`、`fallback3()` 在**仅由精确市场价格**构成的
上级市场中取中位数，避免递归插补充当捐赠者。`allowoverall` 最后以总体中位
数填补；`complete` 要求所有价格均被解决，否则报错。`source(prefix)` 记录
来源代码，`audit()` 输出逐品类审计表。

恢复的 Deaton 价格在截距归一化下是相对共同市场价格。它适合验证或稳健性
分析，不能在没有外部归一化时被解释为绝对市场价格。主分析若有村表报价，
应优先使用经完整填补审计的社区价格，而非家庭单位价值。

## GEASI 与结果导出

### `fooddem_precommitments`

```stata
fooddem_precommitments using filename, [replace]
```

仅适用于最近一次 GEASI 估计。输出 `good`、`scale`、潜在参数及其标准误、
变换后的预先承诺数量和 delta-method 标准误、z 统计量和 p 值。结果应结合
尺度、总支出占比、识别强度及经济含义判断，不能仅根据符号下结论。

### `fooddem_export`

```stata
fooddem_export using filename, [label(string) replace]
```

将当前 `e(b)` 和 `e(V)` 展开为 `parameter`、`coefficient`、`std_error`、
`z`、`p_value`、`model` 的长表。`label()` 可为导出的模型行赋予便于汇总的
名称；缺省时使用当前模型标签。它仅导出结构参数，不替代弹性和正则性输出。

## 推荐的实证顺序

1. 用原始消费、村表报价和地理信息构造品类支出、份额、社区价格、人口变量
   与分析样本；保留每种价格来源和每一步合并的审计表。
2. 在主样本上运行描述统计、零消费率、价格变异与购买覆盖率。首先确认份额
   加总、价格单位、社区-年份标识和缺失模式。
3. 使用 `fooddem_select` 的一步 GMM 对 AIDS、QUAIDS 和多个 EASI 阶数做
   透明筛选；以嵌套 Engel 检验及 BIC 共同判断，不只比较单一拟合指标。
4. 对选择的模型运行聚类两步 GMM，输出 `fooddem_tests`、
   `fooddem_firststage`、`fooddem_elasticities` 和 `fooddem_regularity`。
5. 对支出内生性报告 IV/CF 设定、一阶段强度、两步 Hansen（如可用）和工具
   集合敏感性。弱工具变量时，应降低因果解释强度。
6. 将 GEASI、NLSUR/控制函数、单位价值价格及替代品类定义作为稳健性分析，
   而非在没有识别支持时机械挑选“最好看”的结果。
7. 最后运行收入和质量分解，并明确区分条件支出弹性、无条件收入弹性、数量
   弹性与质量/来源弹性。

## 关键限制与解释边界

- 本包要求调用者先处理调查设计、价格单位、异常原始记录和样本权重。若
  调查没有可核验的权重，不应声称结果是总体加权代表性估计。
- 社区价格填补应只从已直接观测的捐赠者取值，并记录同乡镇、邻村、县、
  省等层级；不能让低层插补值递归传递。
- `fooddem` 的需求系统约束不等同于对所有户的曲率保证，必须报告
  `fooddem_regularity` 的经验结果。
- SY 是对零消费选择的结构近似，不把零值自动解释为“没有偏好”；极低或极高
  参与率需要单独的识别判断。
- 参数、弹性与收入分解的模型不确定性并不会因同一套 ado 自动消失。函数
  形式、工具变量、价格构造和品类聚合均应在论文中可复现地说明。

## 与本项目脚本的对应关系

本项目中 `code/04_estimate_easi.do` 调用主估计、模型选择及全部后估计命令；
`code/06_instrument_sensitivity.do` 记录工具变量集合敏感性；
`tests/test_fooddem.do` 用合成数据测试任意 `K`、约束、EASI/GEASI、SY、
IV/CF 和导出接口。社区价格构造和单位价值审计分别在
`code/01_build_village_prices.do` 与 `code/00_build_household_unit_values.do`
中完成。

方法细节、数据审计和当前实证结果另见
[`METHODS_AND_AUDIT.md`](METHODS_AND_AUDIT.md) 与
[`RESULTS_SUMMARY.md`](RESULTS_SUMMARY.md)。
