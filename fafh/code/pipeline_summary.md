# 户外消费系数研究流程摘要（步骤 2～5）

## 已执行步骤
2. 12 个模型主流程预测
3. 后处理与模型比较
3.5. 预测精度对比（交叉验证 RMSE/MAE/R²/MAPE）
4. 稳健性检验
5. Bootstrap 预测区间（未执行）

## 主要输出文件
- 各模型预测: `predictions_<model>.csv`
- 各模型稳健结果: `predictions_<model>_robust.csv`
- 各模型 Bootstrap: `predictions_<model>_bootstrap.csv`
- 模型比较（全国）: `model_comparison_national.csv`
- 预测精度明细: `model_accuracy_detail.csv`（各模型×品类 MAE/RMSE/R²/MAPE）
- 预测精度汇总: `model_accuracy_summary.csv`（按模型平均及排名）
- 省级/全国户内外消费量: `results_province_<model>.csv`, `results_national_<model>.csv`
