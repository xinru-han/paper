# 微观食品需求：参与集合 MAIDADS、收入传导与预测

更新日期：2026-10-10。本文记录本项目采用的统计模型及其解释边界，不代表模型已经完成估计或通过所有诊断。实际样本数、收敛、检验、标准误和预测结果应以本项目生成的结果文件为准。

## 1. 研究对象和两阶段预算

本项目继续使用农村家庭食品消费调查。八类食品规格为主食及制品、肉类及制品、蛋类及制品、奶类、水产品及制品、油脂、蔬菜及制品、水果干果及制品。十类规格在八类基础上将猪肉从肉类中分出、将坚果干果从水果中分出。当前猪肉包括 `roulei_1` 猪肉和 `roulei_2` 排骨；品种不明的加工肉留在其他肉类。单列干果为 `shuiguo_6` 坚果；水果干、果脯仍留在水果及制品。细项映射必须互斥，并由实际的数据分类审计文件确认；不能把同一细项同时计入两个类别。豆类是否纳入主食以该规格的映射表为准。

数量使用总消费，包括购买后实际消费、自产消费和获赠消费；用独立社区价格估值。购买量、自产量和社区价格的异常标记保留供诊断，不通过弹性符号或显著性反向定义异常值。本项目不估计饲料压力指数。

设家庭 h 的共同用餐人口为 N_h，覆盖食品总月价值为 M_h。第一阶段的食品预算和收入分别为：

\[
m_h=M_h/N_h,\qquad
y_h=Y_h/(12N_h),
\]

其中 Y_h 为年度家庭收入，y_h 为月人均收入。若实现代码使用年人均预算与年人均收入，应同时乘以12，并保持单位记录一致。

食品价值包含实物消费的估值，未必等于现金购买支出，因此报告中应使用“覆盖食品消费预算/价值”。m_h 是所选八类或十类食品的合计，不能将全家庭总消费或收入直接当作该食品子系统的预算，也不能构造“收入减食品”的残差并称其为非食品消费。

第一阶段拟合 E[m_h | y_h,p_h,z_h]；第二阶段拟合覆盖食品预算条件下的食品构成。人均收入驱动食品预算和参与概率，第二阶段的预算变量仍为 m_h。完整系统的收入弹性不是第二阶段食品预算弹性的另一个名称。

## 2. 为什么原版 MAIDADS 不能直接生成真实零

标准 MAIDADS 的内点需求为：

\[
q_i=\gamma_i(u)+\frac{\phi_i(u)}{p_i}
\left[m-\sum_jp_j\gamma_j(u)\right].
\]

当最低消费参数非负、份额权重为正且自由预算为正时，所有 q_i 严格为正。把原始零替换为极小正数会改变参与和份额数据，不是删失估计。

Shonkwiler-Yen 的两步方程条件均值允许一般非线性函数，但逐方程的 \(\Phi_i f_i+c_i\varphi_i\) 一般不加总为1。对这些拟合值事后除以其总和会改变统计模型，不能自动继承 SY 的一致性或 MAIDADS 的效用解释。本项目采用一个直接定义零概率和正消费构成的两部扩展。

## 3. 离散参与集合

令 d_hi=1(q_hi>0)，R_h={i:d_hi=1}。对所选食品预算为正的家庭，R_h 非空。缺失、无效记录、负数量与真实零必须在数据阶段区分，不能统一编码为 d=0。

第一步在 Stata 中按食品拟合 probit：

\[
a_{hi}=x_h' b_i,\qquad
\pi_{hi}=\Phi(a_{hi}),
\]

x_h 包含人均收入的预先指定函数、相对社区价格、家庭人口和类型及有支撑的地区控制。某类在样本中没有零或全部为零时，普通 probit 不可识别；该情况应单独标记，不以任意概率截断掩盖。

各类 Stata probit 首先给出边际指数和独立 Bernoulli 工作规格。本轮主分析再估计一个高斯共同因子的相关参与模型；独立规格作为敏感性比较。非空条件下，独立规格的集合概率为：

\[
P_0=\prod_i(1-\pi_i),\quad Z=1-P_0,
\quad \Pr(R)=\frac{\prod_{i\in R}\pi_i\prod_{i\notin R}(1-\pi_i)}{Z},
\qquad R\ne\emptyset.
\]

主分析的相关参与潜变量为：

\[
d_i^*=a_i+\lambda_i f+\sqrt{1-\lambda_i^2}\varepsilon_i,
\quad f,\varepsilon_i\sim N(0,1),\qquad d_i=1(d_i^*>0).
\]

f 为家庭共同因子，类别误差在给定 f 时独立；因子 loadings 在工作模型中限制为非负且小于1。未条件化的边际概率仍为 \(\Phi(a_i)\)，类别潜误差相关为 \(\lambda_i\lambda_j\)。该模型只能表示一个因子解释的非负相关，不能处理一般多因子或负相关。Stata 边际指数作为固定 offset；这一步没有传播其估计误差。

令 \(b_i(f)=[a_i+\lambda_i f]/\sqrt{1-\lambda_i^2}\)，原始集合质量为：

\[
v_R=\int\prod_{i\in R}\Phi[b_i(f)]
\prod_{i\notin R}\Phi[-b_i(f)]\varphi(f)df,
\qquad \pi_R=\frac{v_R}{1-v_\emptyset}.
\]

对收入或价格变量 v，相关集合概率导数包含非空归一化：

\[
\pi_{R,v}=\frac{v_{R,v}}{1-v_\emptyset}
+\frac{v_R v_{\emptyset,v}}{(1-v_\emptyset)^2}.
\]

实现采用32节点 Gauss-Hermite 积分，且检查固定拟合参数下64节点的差异。对全样本参与集合应枚举所有非空集合，而非仅保留观测频率高的集合。需要报告各类参与率、常见集合频率、成对共同消费率、probit 校准、loadings 边界、相关模型与独立模型差异和积分精度。估计条件连续部分并不能修复错误的集合概率。

本轮相关模型校准显示：八类集合总变差距离从独立模型约0.09688降至0.01658；十类从0.16334降至0.04027。十类全参与观测比例约34.34%，相关模型预测约34.35%；最大 loading 约0.6673，没有激活人工上界。十类固定参数64与32节点总对数似然差约-2.06e-8。上述均是样本内校准或数值精度指标，不能替代样本外验证；以 `correlated_hurdle_fit.json` 和相应验证表为准。由于独立零相关假设涉及边界和因子未识别，似然改善不能直接用普通卡方 LR p 值解释。

若某食品被设为必然参与，必须由其全样本参与记录支持，不能仅因其“应当是必需品”强制参与。模型是条件于覆盖食品预算为正的系统；全食品预算为零的家庭需要额外的顶层食品参与模型。

## 4. 连续部分：集合条件 MAIDADS

设总类别数为 K，人口特征为 z。原始端点权重分别为：

\[
\alpha_i(z)\ge0,\quad\beta_i(z)\ge0,
\quad\sum_i\alpha_i(z)=\sum_i\beta_i(z)=1.
\]

食品子系统自由估计两个 simplex，不使用省级代码中“最后一类高收入份额为1”的非食品饱和限制。可用 softmax 和一个参考类别识别参数。为控制参数规模，家庭类型可对 alpha 和 beta 的 logit 使用同一组平移；这仍需由代码和参数表明确记录。

\[
s(u)=\operatorname{logit}^{-1}(u),\qquad
\phi_i(u,z)=\alpha_i(z)[1-s(u)]+\beta_i(z)s(u).
\]

在非空集合 R 内定义：

\[
\Phi_R=\sum_{j\in R}\phi_j,\qquad
c_{Ri}=\phi_i/\Phi_R\ (i\in R),\qquad
\sum_{i\in R}c_{Ri}=1.
\]

这个归一化是在条件效用/支出函数定义中完成的，不是将 SY 拟合份额事后归一化。

### 4.1 本轮最低消费端点限制

完整 MAIDADS 可写作 \(\gamma_i(u)=\delta_i[1-t(u)]+\tau_i t(u)\)，其中 \(t(u)=\operatorname{logit}^{-1}(\omega u)\)。本轮主规格采用低端点为零的限制：

\[
\delta_i=0,\qquad\gamma_i(u)=\tau_i t(u),
\quad\tau_i\ge0,\quad\omega>0.
\]

该限制使 u 趋于负无穷时的最低消费成本趋于零，从而避免固定正最低预算把低消费家庭排除出可行域。不能采用逐户裁切最低消费或强制保留某个自由预算比例来替代可行域估计。

报告名称应为“低端点为零的参与集合 MAIDADS”，不能称为完全无约束的 MAIDADS。它不允许正的低收入最低消费端点，也不允许最低消费量随效用下降。完整双端点模型可作为后续扩展，但需重新检查可行性和识别。

AIDADS 比较规格的 gamma 固定为零，因此应明确称为“零最低消费 AIDADS”。tau=0 时 omega 在零假设下不可识别，而且 tau 位于非负边界；普通卡方分布 LR p 值不适用于这个比较。可报告拟合和样本外预测比较，或在后续以合适的重抽样比较。

### 4.2 条件支出函数和需求

\[
Q_R(u,p,z)=\exp\left[u+\kappa-
\sum_{i\in R}c_{Ri}(u,z)\ln\frac{c_{Ri}(u,z)}{p_i}\right],
\]

\[
E_R(u,p,z)=\sum_{i\in R}p_i\gamma_i(u,z)+Q_R(u,p,z).
\]

解 \(E_R(u,p,z)=m\)，并预测：

\[
q_{Ri}=\gamma_i+\frac{c_{Ri}Q_R}{p_i}\quad(i\in R),
\qquad q_{Ri}=0\quad(i\notin R).
\]

对于每个集合，\(\sum_i p_i q_{Ri}=m\) 精确成立。它是“给定参与集合的消费构成模型”。把 R 解释为物理不可得、购买固定成本或纯偏好限制，需要额外信息；仅观察到年度零消费不能识别这些原因。

数值检查至少包括正价格、正预算、集合内正预测、预算误差、隐式方程残差、\(E_{R,u}>0\)、根的唯一性诊断、边界状态和多起点优化。有限网格根检查不是全域唯一性的证明。参数人工上界或优化边界若激活，必须报告并进行扩边界复估。优化器失败或驻点检验失败时，即使末次迭代可行、预算闭合，也不能标为已收敛的估计。

**本轮数值 guard 的历史与最终状态。** 最初较窄的 guard，以及随后标准 guard 下的候选解曾有活跃人工边界；这些是历史拟合，不应当作最终主结果。标准 guard 的八类解有主食 log(tau) 上界活跃，十类解有主食 beta logit 边界活跃。`code/09_guard_sensitivity.py` 扩大数值 guard 后取得通过优化成功、驻点和结构可行性验收的解；`code/11_finalize_fits.py` 将这些解提升为主拟合，并保留 `standardguard` 历史文件。当前主拟合的 `expanded_guards=true` 且活跃边界列表为空。扩大后的端点权重 logits 范围为 [-12,12]、log(tau) 为 [-18,8]、log(omega) 为 [-3.5,3]、kappa 为 [-8,8]；其余 bounds 以核心代码与拟合 JSON 为准。这些仍是数值保护范围，并非经济学参数限制，也不证明全局最优。

八类主食 tau 从标准 guard 约149提高至扩大 guard 约193个等价斤/人/月。tau 表示 u 趋于正无穷时的最低消费上端点，不能当作样本实际承诺消费；后者是 gamma=tau*logit_inverse(omega*u)。扩界后不再碰边界，不能消除远端 tau 的弱识别风险。需要共同比较样本实际 gamma、条件需求、弹性以及各收入增长情景的稳定性；本轮因八类变化超过敏感性阈值，已用最终解重算主预测。十类弹性变化约0.0005量级，也使用最终解重算。收入增长情景仍是固定价格和制度条件下的横截面情景，不应外推为任意长期收入增长的可靠结构预测。

每次提升或更换主参数后，必须重新运行 `08_audit_working_domain.py`，让输出 `fit_sha256` 对应当前主拟合。旧 SHA 的证书只对旧拟合有效，不能作为当前结果的最终证书。全效用域唯一根证书与参数 guard 敏感性是两个不同的验收事项，必须分别保留。

### 4.3 全效用域单调的充分条件与非唯一根风险

delta=0 不自动保证 E_R 随 u 单调。给定集合和人口特征，令 \(A_R=\sum_R\alpha_i\)、\(B_R=\sum_R\beta_i\)，并把两个端点在集合内标准化为 \(a_i=\alpha_i/A_R\)、\(b_i=\beta_i/B_R\)。条件权重也可写为：

\[
c_{Ri}=a_i(1-v_R)+b_i v_R,\qquad
v_R=\operatorname{logit}^{-1}[u+\ln(B_R/A_R)].
\]

因 \(\sum_Rc'_{Ri}=0\)，对固定价格向量有全 u 域上界：

\[
\left|\sum_Rc'_{Ri}\ln(c_{Ri}/p_i)\right|
\le B_{mono}=
\frac{\lVert b-a\rVert_1}{8}
\left[\max_{i\in R}\ln\frac{\max(a_i,b_i)}{p_i}
-\min_{i\in R}\ln\frac{\min(a_i,b_i)}{p_i}\right].
\]

在严格正的端点权重下，\(B_{mono}<1\) 保证所有 u 上的 \(Q'_R>0\)。配合 tau>=0、omega>0，便保证所有 u 上 \(E'_R>0\)。delta=0 时两端分别趋于0和正无穷，因此每个正预算恰有一个效用根。该界不受所有价格的共同货币缩放影响。

\(B_{mono}\ge1\) 只是该充分条件没有认证单调，并不证明模型无效。粗界在某个端点份额很小时尤其保守。本项目另外使用以下更紧的严格区间证书，而不是将有限效用网格误称为证明。令 \(d_i=b_i-a_i\)、\(t=v_R\)，则

\[
h(t)=\sum_Rc'_{Ri}\ln(c_{Ri}/p_i)
=t(1-t)L(t),\quad
L(t)=\sum_Rd_i\ln\frac{a_i+d_i t}{p_i},
\quad
L'(t)=\sum_R\frac{d_i^2}{a_i+d_i t}\ge0.
\]

对覆盖整个 [0,1] 的任意分区，在区间 \([t_l,t_h]\) 上令
\(P_{lh}=\max_{t\in[t_l,t_h]}t(1-t)\)。其精确值在区间包含1/2时为1/4，否则是两端抛物线值的最大值。因为 L 单调，区间上的严格上界为

\[
h(t)\le P_{lh}\max\{L(t_h),0\},\qquad
B_{interval}=\max_{[t_l,t_h]}P_{lh}\max\{L(t_h),0\}.
\]

若 \(B_{interval}<1\)，便在每个实数效用上有 \(Q'_R=Q_R[1-h(t)]>0\)，从而有唯一支出根。L 的右端值不是对未知极值的抽样替代，而是利用其单调性得到覆盖整个闭区间的上界。实现采用128等长区间并加入靠近0、1的二进制端点；未获证书的病例再细化到512等长区间。两个严格界的较小值仍是有效上界。所有端点权重严格为正，证书保留数值安全余量1e-10。该余量是浮点实现的保护，并非形式化区间算术误差证明。

若每个价格都有 \(|\Delta\ln p_i|\le r\)，则价格盒内还满足
\(h_{new}(t)\le h_{base}(t)+r\lVert b-a\rVert_1/4\)。因此只要
\(\min(B_{mono},B_{interval})+r\lVert b-a\rVert_1/4<1\)，便同时认证该价格扰动盒内的所有效用与正预算。本轮另报告 r=0.02 的价格盒；它不代表任意大幅价格变化均有效。

如果两种充分证书都失败，才在所有实际样本及报告情景的价格/参与集合上检查 E_u、根数，并对导数变号或接近零的区间细化驻点。仅检查返回根处 E_u>0 无法发现其他根。极端反例为无最低消费 K=2 模型，alpha 的 logit 为5、beta 的 logit 为-5、kappa=0，价格=(10,0.00001)、预算0.01：支出方程有三个根，尽管一个返回根的局部 E_u 为正且预算正确。

本项目的 `code/test_maidads_hurdle.py` 提供粗充分界函数和有限网格根诊断，并保留这个反例。`code/08_audit_working_domain.py --goods 8/10` 逐一认证样本中每个独特价格/家庭特征组合的全部非空参与集合，补充严格区间证书；只有未获得证书的病例才进行 [-40,40]、初始步长0.1的细化数值诊断。输出保留拟合参数、原始分析文件、核心代码的 SHA256，避免将旧拟合证书沿用于新拟合。有限区间、有限网格、没有覆盖全部驻点的检测都只能称为工作域诊断；必须注明区间、步长、情景覆盖和未认证病例，不能把有限网格全通过写为全参数空间的唯一性证明。样本价格与所有参与集合的全效用证书也不等于所有可能价格及任意参数值的全局证明。

## 5. 条件 Dirichlet hurdle 分布

观察到的集合内预算份额为 w_Ri=p_i q_i/m，且 w_Ri>0、\(\sum_Rw_{Ri}=1\)。模型条件均值为 \(\mu_{Ri}=p_iq_{Ri}^{model}/m\)。工作分布为：

\[
\Pr(R\mid y,p,z)\times
\operatorname{Dirichlet}(w_R;\rho\mu_R),\qquad\rho>0.
\]

这种分布直接在 active simplex 上定义正消费份额，并以集合的离散质量生成其他类别的零。它避免把预算闭合的 K 个份额当成 K 个独立高斯方程。只有一个 active 食品的集合，其份额为1，连续分布退化，不提供连续构成参数的识别信息，但保留在参与和预算样本中。

Dirichlet 的条件均值为 mu，协方差为 \([\operatorname{diag}(\mu)-\mu\mu']/(\rho+1)\)，这是一项较强的工作分布限制。需要检查残差、离散集合与连续构成拟合，不能因为条件需求满足曲率就声称随机分布正确。

若条件份额严格小于1但极小，应原样保留，诊断记录精度或异常值。不得为优化方便将真实正份额替换成任意最小份额，也不得增加伪消费。输出 p 值时需说明完整的推断方法和生成变量修正。

## 6. 可用于估计及弹性的解析导数

下式固定集合 R、人口特征 z 和模型参数。令 \(L_i=\ln(c_{Ri}/p_i)\)，集合内各向量维度为 |R|。

\[
\phi'_i=(\beta_i-\alpha_i)s(1-s),\qquad
\Phi'_R=\sum_R\phi'_i,
\]

\[
c'_{Ri}=\frac{\phi'_i\Phi_R-\phi_i\Phi'_R}{\Phi_R^2},
\qquad\sum_Rc'_{Ri}=0.
\]

在本轮 delta=0 的规格中：

\[
\gamma'_i=\tau_i\omega t(1-t),\qquad
Q'_R=Q_R\left[1-\sum_Rc'_{Ri}L_i\right],
\]

\[
E'_R=\sum_Rp_i\gamma'_i+Q'_R,\quad
q'_{Ri}=\gamma'_i+(c'_{Ri}Q_R+c_{Ri}Q'_R)/p_i.
\]

采用 \(E'_R>0\) 的可行分支：

\[
\frac{\partial u}{\partial m}=1/E'_R,
\quad\frac{\partial q_{Ri}}{\partial m}=q'_{Ri}/E'_R,
\quad\eta^R_{i,m}=\frac m{q_{Ri}}\frac{q'_{Ri}}{E'_R}.
\]

\[
H^R_{ij}=\frac{\partial^2E_R}{\partial p_i\partial p_j}
=Q_R\left[\frac{c_{Ri}c_{Rj}}{p_ip_j}
-\mathbf1(i=j)\frac{c_{Ri}}{p_i^2}\right],
\]

\[
\epsilon^{H,R}_{ij}=H^R_{ij}\frac{p_j}{q_{Ri}},\qquad
\epsilon^{M,R}_{ij}=\epsilon^{H,R}_{ij}-\eta^R_{i,m}w^R_j.
\]

H 是固定效用、固定参与集合的条件 Slutsky 矩阵。它由支出函数直接导出，自动对称负半定；这种经济模型的结构性质不属于事后为改变符号施加局部 Cholesky 修正。类内数量为零的 inactive 食品不能定义 log 弹性，应记录为不适用；其集合条件数量导数为零。单一 active 食品的条件 Hicksian 自价格导数为零，不能强求其显著小于零。

理论检查为：预算闭合、\(\sum_iw_i^R\eta^R_{i,m}=1\)、\(\eta^R_{i,m}+\sum_j\epsilon^{M,R}_{ij}=0\)、H 对称及最大特征值不超过数值容差。结构符合理论不等于样本估计显著，也不保证每一食品为正常品。

### 6.1 固定 u 的参数导数与隐式估计梯度

对任意参数 theta，下标 theta 表示固定 u,p,m 的偏导数：

\[
c_{Ri,\theta}=
\frac{\phi_{i,\theta}\Phi_R-\phi_i\Phi_{R,\theta}}{\Phi_R^2},
\qquad
Q_{R,\theta}=Q_R\left[\kappa_\theta-
\sum_Rc_{Ri,\theta}L_i\right].
\]

\[
E_{R,\theta}=\sum_Rp_i\gamma_{i,\theta}+Q_{R,\theta},
\quad u_\theta=-E_{R,\theta}/E'_R,
\]

\[
\frac{d q_{Ri}}{d\theta}=\gamma_{i,\theta}
+\frac{c_{Ri,\theta}Q_R+c_{Ri}Q_{R,\theta}}{p_i}
+q'_{Ri}u_\theta.
\]

softmax 的 Jacobian 为 \(\operatorname{diag}(\alpha)-\alpha\alpha'\)，beta 同理；共享家庭类型平移分别作用于两个端点。对本轮最低消费函数，固定 u 时 \(\partial\gamma_i/\partial\tau_i=t\)、\(\partial\gamma_i/\partial\omega=\tau_i u t(1-t)\)。若使用 tau 的对数坐标，按链式法则再乘 tau。

给定观测预算，\(\mu_{Ri,\theta}=p_iq_{Ri,\theta}/m\)。Dirichlet 对数似然及导数为：

\[
\ell_R=\ln\Gamma(\rho)-\sum_R\ln\Gamma(\rho\mu_i)
+\sum_R(\rho\mu_i-1)\ln w_i,
\]

\[
\ell_{R,\theta}=\rho\sum_R
[\ln w_i-\psi(\rho\mu_i)]\mu_{i,\theta},
\]

\[
\frac{\partial\ell_R}{\partial\rho}
=\psi(\rho)-\sum_R\mu_i\psi(\rho\mu_i)+\sum_R\mu_i\ln w_i.
\]

psi 为 digamma。上述导数需以中央差分在可行的内部点、接近经济边界点和不同集合维度上核对；差分必须保持同一可行根。

## 7. 第一阶段食品预算、收入传导和价格口径

Stata 中的预算主规格采用 Gamma 家族、log 链接的均值模型：

\[
\widehat m_h=\exp\{f(\ln y_h)+g(p_h)+z_h'b\}.
\]

采用 Gamma/log GLM 时，条件均值直接为 exp(index)，不需要将 log-OLS 的 smearing 因子机械套用。Gamma 分布不是收入/预算的因果识别条件；应报告均值拟合、异方差、收入支撑和影响点，并可将其他合理均值模型作为敏感性比较。

如果 \(f(l)=b_1l+b_2l^2\)，则 \(\epsilon_{m,y}=b_1+2b_2\ln y\)；如包含家庭类型交互，应加上相应类型系数。使用样条时，应对实际基函数求导。预算价格弹性 \(\epsilon_{m,p_j}=\partial\ln\widehat m/\partial\ln p_j\) 同理由 g 的导数获得。

仅报告第二阶段条件价格弹性时，预算 m 固定。报告完整的收入条件价格响应时，需允许预算阶段随价格变化：

\[
\frac{\partial q_{Ri}}{\partial\ln p_j}\Big|_y
=q_{Ri}\left[\epsilon^{M,R}_{ij}
+\eta^R_{i,m}\epsilon_{m,p_j}\right].
\]

如果预算模型采用仅相对价格，宏观所有价格同比例上升时的响应需要同收入实际购买力的定义一致。收入、价格和预算的系数只能解释为条件相关和情景响应，除非另有有效工具变量或明确识别设计。第一阶段预测预算不会自动消除预算或收入的内生性；本轮不据此宣称因果弹性。

## 8. 参与边际与全样本总响应

给定家庭的收入、价格和人口特征，食品无条件均值为：

\[
\bar q_i(y,p,z)=\sum_{R\ne\emptyset}\pi_R(y,p,z)
q_{Ri}(\widehat m(y,p,z),p,z).
\]

收入变化的分解为：

\[
\frac{\partial\bar q_i}{\partial\ln y}
=\underbrace{\sum_R\pi_Rq_{Ri}\eta^R_{i,m}\epsilon_{m,y}}
_{\text{集合内预算传导}}
+\underbrace{\sum_Rq_{Ri}\frac{\partial\pi_R}{\partial\ln y}}
_{\text{参与集合变化}}.
\]

两项之和除以 \(\bar q_i>0\)，得到全样本收入响应弹性。不能把第二项省略后称为已经解决零消费的收入弹性。

相应的收入固定价格总响应为：

\[
\frac{\partial\bar q_i}{\partial\ln p_j}
=\sum_R\pi_Rq_{Ri}
[\epsilon^{M,R}_{ij}+\eta^R_{i,m}\epsilon_{m,p_j}]
+\sum_Rq_{Ri}\frac{\partial\pi_R}{\partial\ln p_j}.
\]

也可单独报告固定食品预算的 hurdle 价格响应，此时删去预算价格传导项，并使用该口径的参与函数。两种口径必须分别命名。

对于任一对数情景变量 v，Stata probit 边际参与概率导数为：

\[
\pi_{i,v}=\varphi(a_i)a_{i,v}.
\]

在独立敏感性规格中，对非空集合，归一化集合概率的导数为：

\[
\pi_{R,v}=\pi_R\left\{
\sum_{i\in R}\frac{\pi_{i,v}}{\pi_i}
-\sum_{i\notin R}\frac{\pi_{i,v}}{1-\pi_i}
-\frac{Z_v}{Z}\right\},
\]

\[
P_{0,v}=-P_0\sum_i\frac{\pi_{i,v}}{1-\pi_i},\qquad
Z_v=-P_{0,v}.
\]

相关主规格则使用第3节的积分质量和非空归一化导数。计算时应使用稳定概率/对数算法，并处理由样本实际支持的必然参与类别。集合概率应加总为1，集合概率导数应加总为0。loadings 在收入/价格情景中固定；如果将其设为随收入变化，需要另加该参数路径导数。

参与集合随价格改变的总响应一般没有单一家庭效用的直接福利解释。因此“条件集合 Hicksian 弹性”和“全样本 hurdle 价格总响应”分别报告。不能把后一项与收入弹性套入 Slutsky 公式，便称为全人口结构 Hicksian 弹性。

## 9. 金额、数量与价格规范化

月人均预算、月人均收入和社区价格必须使用同一货币基准。年度收入先转为月收入；数量也采用同一消费期间。使用实际金额时，应对收入和预算应用同一明确平减方法，并处理地区/调查年份差异；若使用当年金额与地区控制，应如实标明当年价格情景。

每类食品合并指数不能使用家庭自己的消费构成作为自身价格权重，因为这会引入构成/质量与需求的机械相关。固定商品权重、社区报价和推算层级均需保留来源审计。可使用固定篮子价格 p_i 及与其匹配的等价数量 q_i=value_i/p_i，保持 \(m=\sum_i p_iq_i\)。这种 q_i 是类别篮子等价量，不能直接称为包含不同商品的物理公斤；如要输出物理公斤预测，应另行给出固定商品构成与转换规则。

本轮保持实际类别篮子等价斤的数量单位，不对各食品再进行不同的数量/价格单位变换。第二阶段仅把所有 p 和 m 共同除以100，以100元为数值货币单位；q 不变。第一阶段收入与预算在元/人/月中拟合，传入第二阶段时再转换预算。共同货币单位转换应保持需求、效用、弹性和份额似然不变，并进行独立验证。

一般情况下，若 \(\widetilde q_i=q_i/s_i\)、\(\widetilde p_i=p_i s_i/c\)、\(\widetilde m=m/c\)，虽然预算恒等式仍成立，但这不足以证明同一 MAIDADS 参数化等价。由于条件权重依效用变化，逐商品数量单位转换需要从隐式效用定义一致调整规范化，不能只保持 kappa 不变就假定模型相同。本轮避免这种逐商品转换；参数坐标缩放也必须在预测前恢复原经济参数。

## 10. 家庭形态与省份平均预测

本轮家庭形态来自共同用餐人口名册的亲属关系码推导，名称为“名册推导家庭类型”，并非问卷直接回答的原始家庭形态变量。人口数使用 HA0 的共同用餐人口定义；年龄以该条记录的调查年度减出生年度计算。不能把行政登记人口与共同用餐人口混用。

关系名册完整要求：名册人数与用餐人口数一致、成员关系码有效、且恰有一位户主。关系码1为户主、2为配偶、4为子女；不能把其他亲属码当作子女。完整关系名册下，单人归type1；两人且仅户主/配偶归type2；仅出现户主、配偶、子女且至少有子女归type3；其余完整名册归type4。不完整或有冲突的关系信息保留为type0。共同模型样本中的实际分类为：

| type | 定义 | 户年数 |
| --- | --- | ---: |
| 0 | 关系不完整或有冲突 | 375 |
| 1 | 单人家庭 | 169 |
| 2 | 夫妻家庭 | 1104 |
| 3 | 核心家庭 | 434 |
| 4 | 扩展及其他家庭 | 1063 |
| 合计 | 八类/十类共同样本 | 3145 |

关系完整子样本为2770户年；全样本可以保留未知类型独立类别，二者应作为预先记录的不同口径比较。另有按年龄划分的“无儿童无老人、含儿童、含老人、两者都有”指标，儿童为15岁以下、老人为65岁及以上；年龄名册不完整单列未知，不能自动归为无儿童无老人。原始关系/年龄、成员缺失、年龄不合理和名册覆盖不足标记均应保留。最新 `family_morphology_counts.csv`、`age_family_counts.csv` 与本节计数/规则应一致。

家庭类型影响可进入参与、食品预算以及第二阶段端点权重。为了区别人口构成与收入分布，比较类型的实际分布均值和共同收入/价格情景的标准化均值；不要用类型间收入水平不同造成的曲线差异替代类型参数效应。

情景预测对每户增长人均收入：\(y_h(g)=y_h(0)g\)，保持该家庭的实际社区价格、人口和类型不变，再依次计算预算、集合概率和期望食品需求。g 是收入倍数，例如1、1.1、1.25、1.5、2；若换为年度增长路径，应明确基年与增长率是假设，不能把省级 GDP 增长预测当作农户收入预测。

省份人均平均为：

\[
\bar q_{pi}(g)=\frac{\sum_{h\in p}a_hN_h\bar q_{hi}(g)}
{\sum_{h\in p}a_hN_h},
\]

其中 a_h 为有效调查权重；没有调查权重时取1，输出应命名“样本省份人均平均”，不宣称省总体代表性。先预测各户再聚合，不能只预测一个具有平均收入、平均家庭规模和平均价格的虚拟家庭。

省份或家庭类型的平均弹性应由总数量响应求得：

\[
\eta_{pi}(g)=\frac{\sum_{h\in p}a_hN_h\bar q_{hi}(g)
\eta_{hi}(g)}{\sum_{h\in p}a_hN_h\bar q_{hi}(g)}.
\]

这不是个体弹性的算术平均。均值、分位数和数量加权总体弹性是不同统计量，应分别标名。收入超出训练支撑的家庭/省份应标记外推；固定家庭类型构成、价格和人口的增长情景不能解释为真实人口老龄化或家庭结构转变预测。

## 11. 估计检验、标准误与后续创新验证

本轮完整保留所有预先指定的八类/十类模型尝试、样本流、数值失败、边界和诊断。不按所有自价格负且显著来选择分类、删样本或起点。Hicksian 非正是结构需求的曲率性质；显著性是数据和推断的结果，不能在研究设计中保证。

probit 和预算 GLM 可输出各自的 Stata 聚类稳健标准误与 p 值；它们不等于第二阶段弹性或全阶段情景预测的标准误。第二阶段的工作 Dirichlet Hessian 也不自动修正社区内相关、第一阶段生成变量及模型误设。

若本轮未完成完整联合 sandwich 或社区层 bootstrap，应仅报告 MAIDADS 和情景的点估计与诊断。空白/未估计 p 值不能填写为0、1或“显著”。不得将优化器返回的收敛指标当作统计 p 值。

后续推断可在村/社区层重抽样，每次重新构造训练样本内固定篮子/价格填补规则、参与 probit、食品预算、条件 MAIDADS 和预测聚合；若重用固定已估价格，应明确 CI 条件于价格构造。按预先规定记录失败率和完整估计状态，不能只保留成功抽样而忽略失败造成的选择。

原创性目前应表述为“针对中国农村食品调查的参与集合、社区价格、家庭形态和收入路径的联合扩展”。MAIDADS 的人口特征扩展和食品零需求处理都有既有研究。要提出新的理论贡献，需进一步完成针对该联合模型的识别/一致性推导、与普通 SY 和其他两部模型的模拟比较、集合概率误设敏感性及样本外预测。未检索到同名应用不等于已证明首次。

## 12. 未来的结构性角点替代

一个更接近经济角点机制的替代是负平移隐式直接加总效用：

\[
F(q,u)=\sum_i\phi_i(u)\ln[q_i+a_i(u)]-u-\kappa,
\quad a_i(u)>0,\quad q_i\ge0.
\]

其固定 u 的补偿需求满足 Kuhn-Tucker 条件：

\[
q_i=\max\{\phi_i/(\lambda p_i)-a_i,0\}.
\]

给定 active 集合 A，可解：

\[
\ln\lambda=
\frac{\sum_A\phi_i\ln(\phi_i/p_i)+
\sum_{\bar A}\phi_i\ln a_i-u-\kappa}{\sum_A\phi_i},
\quad E=\sum_A\phi_i/\lambda-\sum_Ap_i a_i.
\]

平移令零处边际效用有限，因此能产生真正经济角点，但它改变了原版非负最低消费参数的含义。效用嵌套、随机偏好/删失似然、跨集合导数和识别都需要单独推导。将一个确定性带零预测模型放入 Gaussian QML 本身不足以证明解决了删失偏误。本轮主估计没有将该替代冒充原 MAIDADS 已完成的方法。

## 13. 本地来源与主要文献

原始/整理数据来源：

- `/root/data/数据/食物消费调查数据/`。
- `/root/data/数据/食物消费调查数据/处理后的data/户表数据_已清洗.dta` 及其变量标签 CSV。
- `/root/data/数据/食物消费调查数据/处理后的data/村表数据_已清洗.dta` 及其变量标签 CSV。
- `/root/data/Paper/食物消费数据/paper0-EASI/item_level_food_descriptives/outputs/household_item_long.dta` 为此前建立的细项长表，须与原始记录核对消费期间、来源和缺失码。
- `/root/data/Paper/食物消费数据/paper0-EASI/easi_reclassification_screen/code/01_build_nine_group_data.py` 为此前分类/社区价格构建参考，不能将其遗留模型结果当成本轮新估计。

省级方法来源：

- `/root/data/Paper/省级食物消费/ProvinceMAIDADS/scripts/run_maidads_pipeline.py`。
- `/root/data/Paper/省级食物消费/paper-AE/submission_0921/replication/code/estimate_demand.py`，含隐式预算根、解析导数、优化和理论诊断。
- `/root/data/Paper/省级食物消费/paper-AE/submission_0921/replication/documentation/ESTIMATION_PROTOCOL.md`，说明 GDP 代理预算、饱和限制与无 bootstrap 的推断边界。

本轮使用真实家庭人均收入，经食品预算阶段传导；省级 GDP 预算残差不是本轮的非食品数据。省级代码中固定 beta 的饱和非食品限制、七类固定维度、宏观预测和饲料账户均不直接移植。

主要原始文献：

1. Rimmer, M. T. and Powell, A. A. (1996). An implicitly additive demand system. [原论文 DOI](https://doi.org/10.1080/000368496327589)。
2. Preckel, P. V., Cranfield, J. A. L. and Hertel, T. W. (2010). A modified, implicit, directly additive demand system. [原论文](https://www.tandfonline.com/doi/full/10.1080/00036840701591361)。它将固定最低消费参数改为效用函数，标准参数限制不能解释微观真实零。
3. Shonkwiler, J. S. and Yen, S. T. (1999). Two-step estimation of a censored system of equations. [原论文 DOI](https://doi.org/10.2307/1244339)。用于说明一般非线性删失方程的两步估计，不是本项目集合模型已证明一致性的依据。
4. Yen, S. T., Fang, C. and Su, S.-J. (2004). Household food demand in urban China: a censored system approach. [原论文](https://www.sciencedirect.com/science/article/abs/pii/S0147596704000459)。中国微观食品零消费处理已有研究。
5. Britz, W. (2022; vol. 10 no. 3 标2021). Estimating a global MAIDADS demand system considering demography, climate and norms. [期刊原文页面](https://oaj.fupress.net/index.php/bae/article/view/10488)。已把人口特征与其他因素加入 MAIDADS，因此单独加入人口特征不能直接称首次。
6. Bhat, C. R. (2008). The multiple discrete-continuous extreme value model: role of utility function parameters, identification considerations, and model extensions. [作者原稿](https://www.caee.utexas.edu/prof/bhat/abstracts/mdcev_bhat_may2006.pdf)，[作者文献及代码页](https://caee.webhost.utexas.edu/prof/bhat/MDCEV.html)。用于平移效用和KT角点的已有理论基础，不替代本项目未来角点 MAIDADS 的专门推导。
