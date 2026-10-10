# 九类食物需求系统结果（未Bootstrap）

本轮按九类字面定义估计。鲜果、畜禽肉制品、调料和烟酒糖茶不进入份额分母，因此是九类内部的条件需求弹性。

- 完整模型样本：3,131户年。
- NLSUR-CF同估计器比较的BIC/族内顺序选择：EASI order 3。
- AIDS、QUAIDS和EASI都使用Shonkwiler-Yen零消费修正、收入工具变量控制函数和村年聚类标准误。
- 省份固定效应与调查年份完全共线；最终设计保留省份固定效应、删除年份指标，设计矩阵满秩。
- AIDS/QUAIDS使用1%--99%修剪后的数量加权聚合弹性，避免近零预测份额支配简单均值。
- EASI报告样本参考点解析弹性及delta-method p值；本轮未运行bootstrap。
- EASI GMM-IV虽数值收敛，但两种权重矩阵均未通过事后诊断，已从主弹性结果剔除。
- 所有模型均未施加Slutsky负半定曲率参数化。

## 模型选择（NLSUR-CF）

|模型|阶数|收敛|参数数|BIC|Engel高阶项p值|族内推荐|最终推荐|
|---|---:|---:|---:|---:|---:|---:|---:|
|AIDS|1|1|193|-106717.5|NA|0|0|
|EASI|1|1|193|-106683.8|NA|0|0|
|EASI|2|1|201|-106715.2|0.0000|0|0|
|EASI|3|1|209|-106962.9|0.0000|1|1|
|QUAIDS|2|1|201|-106749.8|0.0000|1|0|

## 样本统计

|类别|消费参与率|平均预算份额|消费户月数量中位数|社区价格中位数|
|---|---:|---:|---:|---:|
|主食及加工品|100.0%|24.2%|14.262|2.700|
|豆类及加工品|93.5%|4.5%|1.371|4.000|
|畜禽肉|97.4%|29.4%|4.470|12.865|
|蛋类及制品|96.6%|3.8%|0.743|5.380|
|奶类|67.5%|5.1%|1.500|5.000|
|水产品及制品|69.2%|6.2%|1.000|11.000|
|油脂|98.1%|8.4%|1.249|7.990|
|蔬菜及制品|99.9%|14.3%|9.066|2.000|
|干果及制品|68.3%|4.2%|0.750|9.800|

## AIDS NLSUR-CF主要弹性

|类别|支出弹性(p值)|Marshallian自价格(p值)|Hicksian自价格(p值)|
|---|---:|---:|---:|
|主食及加工品|0.818 (NA)|-0.267 (NA)|-0.091 (NA)|
|豆类及加工品|0.247 (NA)|0.438 (NA)|0.451 (NA)|
|畜禽肉|1.163 (NA)|-0.475 (NA)|-0.111 (NA)|
|蛋类及制品|0.851 (NA)|-0.291 (NA)|-0.252 (NA)|
|奶类|0.956 (NA)|0.113 (NA)|0.169 (NA)|
|水产品及制品|2.037 (NA)|0.809 (NA)|0.960 (NA)|
|油脂|0.467 (NA)|0.146 (NA)|0.188 (NA)|
|蔬菜及制品|0.785 (NA)|-0.384 (NA)|-0.250 (NA)|
|干果及制品|1.598 (NA)|-0.647 (NA)|-0.583 (NA)|

## QUAIDS NLSUR-CF主要弹性

|类别|支出弹性(p值)|Marshallian自价格(p值)|Hicksian自价格(p值)|
|---|---:|---:|---:|
|主食及加工品|0.909 (NA)|-0.290 (NA)|-0.094 (NA)|
|豆类及加工品|0.325 (NA)|0.370 (NA)|0.386 (NA)|
|畜禽肉|1.087 (NA)|-0.433 (NA)|-0.094 (NA)|
|蛋类及制品|1.010 (NA)|-0.356 (NA)|-0.306 (NA)|
|奶类|0.883 (NA)|0.170 (NA)|0.219 (NA)|
|水产品及制品|1.913 (NA)|0.746 (NA)|0.890 (NA)|
|油脂|0.424 (NA)|0.164 (NA)|0.202 (NA)|
|蔬菜及制品|0.902 (NA)|-0.421 (NA)|-0.266 (NA)|
|干果及制品|1.517 (NA)|-0.550 (NA)|-0.497 (NA)|

## EASI NLSUR-CF主要弹性

|类别|支出弹性(p值)|Marshallian自价格(p值)|Hicksian自价格(p值)|
|---|---:|---:|---:|
|主食及加工品|1.000 (0.0000)|-0.392 (0.0000)|-0.157 (0.0170)|
|豆类及加工品|0.414 (0.1859)|-0.121 (0.4200)|-0.102 (0.4794)|
|畜禽肉|1.181 (0.0000)|-0.501 (0.0003)|-0.143 (0.2273)|
|蛋类及制品|1.162 (0.0000)|-0.238 (0.0952)|-0.193 (0.1693)|
|奶类|0.244 (0.5417)|-0.018 (0.9556)|-0.004 (0.9895)|
|水产品及制品|1.293 (0.0001)|0.403 (0.4850)|0.488 (0.3881)|
|油脂|0.483 (0.0034)|0.025 (0.8434)|0.066 (0.5594)|
|蔬菜及制品|1.035 (0.0000)|-0.359 (0.0000)|-0.214 (0.0004)|
|干果及制品|2.159 (0.1028)|-0.517 (0.2887)|-0.460 (0.3243)|

## EASI GMM-IV失败诊断（不用于经济解释）

|规格|过度识别统计量|自由度|p值|正预测份额率|负Hicksian自价格率|Slutsky最大特征值|采用|
|---|---:|---:|---:|---:|---:|---:|---:|
|EASI GMM-IV two-step|114.906|55|0.000004|0.0073|0.5217|0.1990|0|
|EASI GMM-IV one-step|0.771|55|NA|0.0006|0.6667|0.2998|0|

## 估计与识别诊断

|模型|估计器|GMM步数|收敛|返回码|Hansen p值|首阶段F|首阶段p值|首阶段R²|
|---|---|---:|---:|---:|---:|---:|---:|---:|
|AIDS|nlsur_cf|0|1|0|NA|10.93|0.0000|0.377|
|QUAIDS|nlsur_cf|0|1|0|NA|10.93|0.0000|0.377|
|EASI_NLSUR|nlsur_cf|0|1|0|NA|10.93|0.0000|0.377|
|EASI_GMM|gmm_iv|2|1|0|0.0000|10.93|0.0000|0.377|

## 联合检验

|模型|检验|统计量|自由度|p值|
|---|---|---:|---:|---:|
|AIDS NLSUR-CF|demographics_joint_zero|157.271|72|0.0000|
|AIDS NLSUR-CF|all_share_shifters_joint_zero|867.309|128|0.0000|
|AIDS NLSUR-CF|expenditure_exogeneity|35.487|8|0.0000|
|AIDS NLSUR-CF|Shonkwiler_Yen_terms_joint_zero|22.764|5|0.0004|
|AIDS NLSUR-CF|excluded_instruments_first_stage|10.930|NA|0.0000|
|AIDS NLSUR-CF|theory_restrictions_imposed|1.000|NA|NA|
|QUAIDS NLSUR-CF|highest_Engel_order_joint_zero|86.638|8|0.0000|
|QUAIDS NLSUR-CF|demographics_joint_zero|161.032|72|0.0000|
|QUAIDS NLSUR-CF|all_share_shifters_joint_zero|899.718|128|0.0000|
|QUAIDS NLSUR-CF|expenditure_exogeneity|34.859|8|0.0000|
|QUAIDS NLSUR-CF|Shonkwiler_Yen_terms_joint_zero|10.844|5|0.0546|
|QUAIDS NLSUR-CF|excluded_instruments_first_stage|10.930|NA|0.0000|
|QUAIDS NLSUR-CF|theory_restrictions_imposed|1.000|NA|NA|
|EASI NLSUR-CF|highest_Engel_order_joint_zero|40.348|8|0.0000|
|EASI NLSUR-CF|demographics_joint_zero|171.874|72|0.0000|
|EASI NLSUR-CF|all_share_shifters_joint_zero|929.008|128|0.0000|
|EASI NLSUR-CF|expenditure_exogeneity|25.589|8|0.0012|
|EASI NLSUR-CF|Shonkwiler_Yen_terms_joint_zero|7.168|5|0.2084|
|EASI NLSUR-CF|excluded_instruments_first_stage|10.930|NA|0.0000|
|EASI NLSUR-CF|theory_restrictions_imposed|1.000|NA|NA|
|EASI GMM-IV two-step (rejected)|highest_Engel_order_joint_zero|6.691|8|0.5703|
|EASI GMM-IV two-step (rejected)|demographics_joint_zero|268.298|72|0.0000|
|EASI GMM-IV two-step (rejected)|all_share_shifters_joint_zero|1017.514|128|0.0000|
|EASI GMM-IV two-step (rejected)|Shonkwiler_Yen_terms_joint_zero|99.544|5|0.0000|
|EASI GMM-IV two-step (rejected)|Hansen_overidentification|114.906|55|0.0000|
|EASI GMM-IV two-step (rejected)|excluded_instruments_first_stage|10.930|NA|0.0000|
|EASI GMM-IV two-step (rejected)|theory_restrictions_imposed|1.000|NA|NA|
|EASI GMM-IV one-step (rejected)|highest_Engel_order_joint_zero|5.735|8|0.6769|
|EASI GMM-IV one-step (rejected)|demographics_joint_zero|244.388|72|0.0000|
|EASI GMM-IV one-step (rejected)|all_share_shifters_joint_zero|611.759|128|0.0000|
|EASI GMM-IV one-step (rejected)|Shonkwiler_Yen_terms_joint_zero|16.577|5|0.0054|
|EASI GMM-IV one-step (rejected)|GMM_overidentification_identity_weight|0.771|55|NA|
|EASI GMM-IV one-step (rejected)|excluded_instruments_first_stage|10.930|NA|0.0000|
|EASI GMM-IV one-step (rejected)|theory_restrictions_imposed|1.000|NA|NA|

## 常规性诊断

|模型|诊断|数值|阈值|通过|
|---|---|---:|---:|---:|
|AIDS NLSUR-CF|adding_up_max_abs_error|0.00000|0.00000|1|
|AIDS NLSUR-CF|positive_fitted_share_rate|0.79208|1.00000|0|
|AIDS NLSUR-CF|positive_expenditure_elasticities|0.97352|1.00000|0|
|AIDS NLSUR-CF|negative_hicksian_own_elasticities|0.64220|1.00000|0|
|AIDS NLSUR-CF|slutsky_symmetry_max_abs_error|0.00000|0.00010|1|
|AIDS NLSUR-CF|slutsky_max_eigenvalue|0.07785|0.00000|0|
|AIDS NLSUR-CF|adding_up_homogeneity_symmetry_imposed|1.00000|1.00000|1|
|QUAIDS NLSUR-CF|adding_up_max_abs_error|0.00000|0.00000|1|
|QUAIDS NLSUR-CF|positive_fitted_share_rate|0.77866|1.00000|0|
|QUAIDS NLSUR-CF|positive_expenditure_elasticities|0.97585|1.00000|0|
|QUAIDS NLSUR-CF|negative_hicksian_own_elasticities|0.62984|1.00000|0|
|QUAIDS NLSUR-CF|slutsky_symmetry_max_abs_error|0.00000|0.00010|1|
|QUAIDS NLSUR-CF|slutsky_max_eigenvalue|0.07250|0.00000|0|
|QUAIDS NLSUR-CF|adding_up_homogeneity_symmetry_imposed|1.00000|1.00000|1|
|EASI NLSUR-CF|adding_up_max_abs_error|0.00000|0.00000|1|
|EASI NLSUR-CF|positive_fitted_share_rate|0.72245|1.00000|0|
|EASI NLSUR-CF|positive_expenditure_elasticities|0.94474|1.00000|0|
|EASI NLSUR-CF|negative_hicksian_own_elasticities|0.64107|1.00000|0|
|EASI NLSUR-CF|slutsky_symmetry_max_abs_error|0.00000|0.00010|1|
|EASI NLSUR-CF|slutsky_max_eigenvalue|0.04943|0.00000|0|
|EASI NLSUR-CF|adding_up_homogeneity_symmetry_imposed|1.00000|1.00000|1|
|EASI GMM-IV two-step (rejected)|adding_up_max_abs_error|0.00000|0.00000|1|
|EASI GMM-IV two-step (rejected)|positive_fitted_share_rate|0.00735|1.00000|0|
|EASI GMM-IV two-step (rejected)|positive_expenditure_elasticities|0.86957|1.00000|0|
|EASI GMM-IV two-step (rejected)|negative_hicksian_own_elasticities|0.52174|1.00000|0|
|EASI GMM-IV two-step (rejected)|slutsky_symmetry_max_abs_error|0.00000|0.00010|1|
|EASI GMM-IV two-step (rejected)|slutsky_max_eigenvalue|0.19897|0.00000|0|
|EASI GMM-IV two-step (rejected)|adding_up_homogeneity_symmetry_imposed|1.00000|1.00000|1|
|EASI GMM-IV one-step (rejected)|adding_up_max_abs_error|0.00000|0.00000|1|
|EASI GMM-IV one-step (rejected)|positive_fitted_share_rate|0.00064|1.00000|0|
|EASI GMM-IV one-step (rejected)|positive_expenditure_elasticities|0.72222|1.00000|0|
|EASI GMM-IV one-step (rejected)|negative_hicksian_own_elasticities|0.66667|1.00000|0|
|EASI GMM-IV one-step (rejected)|slutsky_symmetry_max_abs_error|0.00000|0.00010|1|
|EASI GMM-IV one-step (rejected)|slutsky_max_eigenvalue|0.29979|0.00000|0|
|EASI GMM-IV one-step (rejected)|adding_up_homogeneity_symmetry_imposed|1.00000|1.00000|1|

## 解释限制

九类不是全部食品，特别是鲜果被排除，因此支出弹性是给定九类总支出的条件支出弹性。水产品只有42个村年直接报价，且需要较多省年/年份中位数填补，该类价格弹性的识别明显弱于其他类别。三种NLSUR-CF模型都不能在全样本满足曲率，正的Hicksian自价格点估计不能解释为可靠需求反应。正式结果需在最终分类确定后重新bootstrap，并重新设计水产品等低覆盖类别；高维GMM还需要更强工具变量和解析雅可比。
