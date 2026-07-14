# EASI 自价格弹性曲率约束修正

## 结论

正的 Hicksian 自价格弹性不能通过事后改号解决。当前项目采用两步修正：

1. 按 Hovhannisyan et al. (2025) 在价格、支出和人口特征的样本均值处报告
   主弹性；
2. 在 EASI-GMM 估计中用 Cholesky 重参数化直接施加局部 Slutsky 负半定，
   并用 delta method 计算弹性标准误、p 值和置信区间。

局部曲率模型收敛，Hansen `p=0.0688`，六类参考点 Hicksian 自价格弹性均为
负。强制所有家庭都满足曲率的全局版本虽然消除了全部正号，但没有收敛且
Hansen `p<0.001`，因此不能作为主模型。

## 理论依据与实现

对本项目的 EASI 份额方程，记对数价格系数矩阵为 `Gamma`、潜在预算份额为
`w`。补偿价格反应的份额形式为

```text
S(w) = Gamma + w*w' - diag(w),
e_H,ij = S_ij / w_i.
```

支出函数对价格凹要求 `S(w)` 负半定；因此其对角元非正，内部解的 Hicksian
自价格弹性也必须非正。加总、齐次和对称并不会自动保证这一条件。

局部模型在样本均值的拟合份额 `w0` 处使用

```text
Gamma = diag(w0) - w0*w0' - Q*L*L'*Q',
```

其中 `Q'1=0`，`L` 为下三角矩阵。于是
`S(w0)=-Q*L*L'*Q'`，在保留加总和对称的同时保证负半定。参数在 GMM 中
联合重估，协方差矩阵通过重参数化 Jacobian 转换回原始 `Gamma` 参数。

## 局部曲率主结果

| 食品 | Hicksian 自价格 | 标准误 | p 值 | 95% CI |
| --- | ---: | ---: | ---: | ---: |
| 粮食 | -0.241 | 0.060 | <0.001 | [-0.359, -0.124] |
| 豆类 | -0.341 | 0.167 | 0.041 | [-0.668, -0.014] |
| 肉类 | -0.255 | 0.061 | <0.001 | [-0.374, -0.135] |
| 食用油 | -0.180 | 0.087 | 0.037 | [-0.350, -0.011] |
| 蔬菜 | -0.211 | 0.062 | <0.001 | [-0.334, -0.089] |
| 水果 | -0.074 | 0.087 | 0.393 | [-0.244, 0.096] |

水果点估计符合理论，但不能拒绝弹性为零。不能将它写成“显著负价格反应”。

约束前参考点最大特征值为 `0.00262`；约束后为数值零
(`4.40e-18`)。两步 GMM 的 Hansen 统计量只从 `28.732` 变为 `28.825`，
Hansen p 值从 `0.0703` 变为 `0.0688`，说明局部修正没有造成明显拟合损失。

## 为什么原总体加权值仍可能为正

旧主表把不同价格、支出和人口点的户级弹性按预测数量加权。局部曲率只在
一个共同参考点施加，因此它不会保证每个异质家庭都满足曲率。约束后该旧口径
的粮食和食用油总体值仍分别为 `0.102` 和 `0.104`，但户级中位数为
`-0.243` 和 `-0.171`。这些值保留为异质性和模型外推诊断，不再作为主价格
弹性。

这一报告口径与 Hovhannisyan et al. (2025) 将弹性评价在样本平均值的做法
一致。它同时避免了极小拟合份额导致的比率异常值控制总体结论。

## 价格测量证据

不加曲率约束时，只保留六类价格均来自本村/当年直接报价的样本，六类总体
Hicksian 自价格弹性已经全部为负：

```text
-0.128, -0.051, -0.244, -0.263, -0.209, -0.055
```

而完整插补价格样本的粮食和食用油总体值为正。数量 p99 修剪只能使粮食转负，
不能使食用油转负。因此正号不只是消费异常值，也与乡镇、县、省价格插补压缩
村际价格变异，以及价格和本地生产条件/商品质量共同变化有关。曲率约束不能
代替价格识别，直接村价结果必须与主表并列报告。

直接价格未约束模型的 Hansen `p=0.457`。在这个较小样本上再施加局部曲率后，
Hansen `p<0.001`，且豆类参考点弹性变为不稳定的 `-3.50`。所以直接价格证据
采用未约束结果，不用被过度约束且规格检验拒绝的版本。这个对比也说明，不能
为了得到负号而忽略模型拟合和识别检验。

## 全局约束为何不采用

全局充分条件令 `Gamma=-Q*L*L'*Q'`。因为
`diag(w)-w*w'` 对任何内部份额均为正半定，所以每个家庭的
`S(w)=Gamma-[diag(w)-w*w']` 都负半定。实际结果确实使六类户级负值率均为
100%，总体自价格弹性为：

```text
-0.824, -0.937, -0.518, -0.934, -0.892, -0.770
```

但该模型没有收敛，Hansen `J=236.77`、`df=19`、`p<0.001`。这说明以当前
EASI(1) 和价格数据强制全样本全局曲率会严重牺牲矩条件拟合。该结果只证明
“机械强约束可以消除正号”，不能作为可信需求弹性。

## 正式报告规则

- 主表使用局部曲率 EASI-GMM 的样本均值弹性及 p 值；
- 水果写为负但不显著；其余五类为显著负；
- 本村直接价格样本作为价格测量关键稳健性；
- 户级数量加权弹性只报告为异质性诊断；
- 全局模型明确列为被 Hansen 检验拒绝且未收敛的反例，不用于政策模拟；
- 自产需求系统仍不作结构解释，主福利系统继续使用社区零售价计值的总消费。

## 可复现文件

- 约束估计：[code/12_curvature_constrained.do](code/12_curvature_constrained.do)
- 通用估计器：[ado/fooddem.ado](ado/fooddem.ado)
- EASI-GMM 参数化：[ado/fooddem_easi_gmm.ado](ado/fooddem_easi_gmm.ado)
- 参考点推断：[ado/fooddem_reference.ado](ado/fooddem_reference.ado)
- 局部曲率完整弹性：[outputs/source_total_curvature_constrained_reference.csv](outputs/source_total_curvature_constrained_reference.csv)
- 估计比较：[outputs/source_total_curvature_estimation_comparison.csv](outputs/source_total_curvature_estimation_comparison.csv)
- 全局规则性诊断：[outputs/source_total_curvature_global_regularity_latent.csv](outputs/source_total_curvature_global_regularity_latent.csv)

## 参考文献

- Diewert, W. E. and Wales, T. J. (1987). Flexible Functional Forms and Global
  Curvature Conditions. *Econometrica*, 55(1), 43-68.
  https://doi.org/10.2307/1911156
- Moschini, G. (1999). Imposing Local Curvature Conditions in Flexible Demand
  Systems. *Journal of Business & Economic Statistics*, 17(4), 487-490.
- Lewbel, A. and Pendakur, K. (2009). Tricks with Hicks: The EASI Demand System.
  *American Economic Review*, 99(3), 827-863.
  https://doi.org/10.1257/aer.99.3.827
- Hovhannisyan, V., Khachatryan, A. and Asci, S. (2025). A Comprehensive
  Analysis of Urban-Rural Differences: The Case of Food Consumption in China.
  *European Review of Agricultural Economics*, 52(4), 778-817.
  https://doi.org/10.1093/erae/jbaf023
