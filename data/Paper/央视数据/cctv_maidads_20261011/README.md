# 央视购买数据 MAIDADS 实证包

本目录从央视 2020–2022 年交易记录重建需求系统。不是农户调查，不计算饲料压力指数，不进行 bootstrap。统计估计和弹性计算使用 Stata 17 / Mata；Python 仅用于任务调度、独立公式核对、图表与报告汇编。

## 结果入口

- `outputs/RESULTS_CN.md`：结果解释、质量门槛及局限。
- `outputs/ALL_MAIN_RESULTS.txt`：全部主要汇总表，含失败与未通过诊断的估计。
- `outputs/estimation/`：原生 AIDADS、MAIDADS 的参数、完整价格矩阵、支出弹性分布及数值检查。
- `outputs/comparators/`：同一 share-QML 尺度的 AIDS、QUAIDS 对照。
- `outputs/validation/`：2022 时间留出及五折整省留出，所有折次保留。
- `outputs/income/`：收入区间模型、食品预算曲线、线性与收入档/人口代理敏感性。
- `outputs/scenarios/`：逐户收入增长预测、按省/家庭类型的汇总。
- `outputs/corner/`：严格零购买角点扩展的真实数据试估与结构测试。
- `outputs/corner_scenarios/`：受限角点试估在全部2022年度家庭的收入情景诊断，不能当完整自由 MAIDADS。
- `docs/RESEARCH_LOG.md`：本次科研日志，注明外部同步状态。

`converged=0`、数值边界、低秩或不完整预测覆盖不是合格主估计，不能根据负自价格符号将其自动转为主结果。当前实际原生自由参数估计未通过资格检查，情景只能作为参数诊断；正式预测列在 `qualified_forecast=0` 时留空。强识别模拟资料恢复检验与实际数据结果分开保存。

## 食品与价格

八类为主食、油脂、蔬菜、水果、猪肉、其他肉类、水产品、奶类。九类将其他肉分为禽类及其他肉和牛羊肉。坚果有购买金额，但当前没有合格独立价格，不能用食用油代理增加十类价格系统。

原始数量缺失不等于零购买。参与状态以金额判断；数量为外部类别价格指数下的数量等价值，不是公斤，也不等于包含外食的完整膳食摄入量。价格使用固定训练期篮子和外部监测价格，整省验证会重新构造训练省权重和归一化。

## 原生 Ado

将本目录 `ado` 加入 Stata 的 `adopath` 后，可按任意 `K>=2` 调用：

```stata
adopath ++ "/root/data/Paper/央视数据/cctv_maidads_20261011/ado"
maidadsfit, expenditure(m) prices(p1 p2 p3) shares(w1 w2 w3) ///
    model(maidads) outdir("result_directory") starts(3) iterate(400)
```

`model(aidads)` 为常数承诺量规格。主 ado 不提供不存在的联合标准误、p 值或置信区间。`converged` 包含严格数值/支持域诊断；各检查详见 `audit.csv`，参数边界与候选解详见 `candidates.csv`。它不是已经解决任何数据集的零值、内生性和完整家庭预算系统的一键估计器。AIDS/QUAIDS 对照、区间收入第一阶段和角点扩展分别由本包中的独立脚本实现。

## 复现顺序

每个并发 Stata 进程必须使用独立且已存在的 `STATATMP`。不要使用当前许可证不支持的 `stata-mp`。

```bash
python3 code/run_pipeline.py --rebuild-data --validation --corner
```

原始输入路径及类别映射在 `code/01_build_data.do` 中。需要当地原始数据和外部价格文件；公开仓库不包含真实户级数据。完整重跑可能较久，所有阶段记录日志和执行状态，不以 Stata 的零退出码代替结果检查。

此次诊断情景显式使用已完成但不合格的 `maidads_8_warm` 参数目录，不对失败主模型静默回退：

```stata
do code/06_scenarios.do "/root/data/Paper/央视数据/cctv_maidads_20261011/outputs/estimation/maidads_8_warm"
```

调度器也接受 `--diagnostic-modeldir`。端到端主调度未作为一次独立全量集成运行执行；本次各阶段分别实际运行、核对并保留执行日志。

## 解释边界

MAIDADS 低/高承诺端点在原生估计中均自由估计，允许自然的非负边界；不会固定低端点为零，也不会用 Cholesky 修改 Slutsky 矩阵。alpha/beta 以正 softmax 参数化，尚未完整搜索自然 simplex 的精确零边界。触及 logit guard 的解不能称无边界主解；也不能据此断言模型不成立或边界解不存在。理论上的 Hicksian 符号及非负交叉替代来自原始效用/支出函数，并不独立证明原始数据正确。

角点扩展采用平移对数效用和随机偏好积分，以 KKT 决定消费集合；为确保全局规则性，其真实试估施加 `alpha=beta` 等限制，必须与完整自由端点 MAIDADS 分开报告。模拟偏好积分不是 bootstrap。

收入只有五个金额档，调查中的报告周期尚未得到元数据确认；家庭人口也是区间代理。连续收入曲线是条件分布与预算投影假设下的情景，不是观察到的准确人均年收入，更不是已识别的因果收入效应。

价格弹性是覆盖食品集合内、固定食品预算或食品子效用的弹性，不是完整家庭预算的补偿价格弹性。收入弹性由食品预算收入响应与条件食品支出弹性链式计算。按省汇总是一户一年等权的样本均值，没有人口代表性权重，不应称为省级人口预测。

GitHub 仅同步代码、文档和无户标识的汇总结果；`data/`、真实交易缓存、个体预测、支撑样本及含真实户信息的日志均留在本地。
