# 农业机械化对粮食综合生产能力的影响：Meta分析 + CASM情景模拟

## ★★ ms版：manuscript对齐主线（最终采用，2026-07-08）

按作者要求，以论文初稿（20260701）为基准复刻：v2 check后数据、
一文一主效应量56条、轨道一PCC沿用manuscript数值、v1路径分类
（MCI/AMS/AML）、DL随机效应+WLS Meta回归+FAT-PET-PEESE原框架，
只修根本性错误并更新数字，结论结构不变。

- `code/10-ms-meta.py` → `results/meta_ms/`：表1与manuscript**逐数一致**
  （单产0.133***/面积0.060**/效率0.172***，I²、Q完全相同）；表2-5为
  同口径重算更新；`audit_findings.txt` 为根本性错误检查报告
- `code/11-ms-scenarios.py` → `results/casm_ms/simulation_plan_ms.csv`：
  与论文表7同构，按式(25)用重算弹性中位数统一（修复表6/表7内部不一致），
  Shifter与论文高度接近（S2: 0.458+0.066 vs 论文0.438+0.072）
- `code/12-ms-casm.py` → `results/casm_ms/`：Python版CASM基线+9情景

**ms版模拟结果（2030）**：基准粮食73377万吨/自给率85.35%（模型为
CASM20260514 Python版，与manuscript所用20260410版基准72530万吨略有差异，
情景排序与结论一致）。**S2-Medium +2.63% > S1-Medium +1.95% >
S3-Medium +1.12%**；S2-High +3.58%（自给率88.15%）为全情景最高；
除S1-Low、S3-Medium/Low边缘情形外，各情景谷物自给率均超100%，
口粮除S3-Low(99.19%)外全部超100%——manuscript"农机社会化服务路径
政策潜力最大（提单产+稳面积）"的核心结论在更新数据下继续成立。

**错误检查主要发现**（详见`results/meta_ms/audit_findings.txt`）：
① v1代码GPR模块使用虚构数据（已删）；② v1代码Meta回归缺LogN与表3不符
（已补)；③ 论文表6弹性与表7 Shifter隐含弹性不一致（已按式25统一）；
④ check版修订的β/SE与轨道一PCC存在36条不一致，建议附录说明提取基准；
⑤ 分路径计数与表2略有出入；⑥ P_13缺号；⑦ DF=N近似（附KH参考CI）。

---

## v3 全文多效应量版（方法升级备选，2026-07-08）

针对v2中"面积不显著、单产仅5%边缘显著"的功效不足问题，参照
IFPRI DP02361（Roche等2025：215篇13000+条弹性，两层随机截距，1/√N精度项）与
Tan等(2026, JAE)（34篇87条，逆方差RE+WLS+Egger/Begg）的范式，
放弃"一文一主效应量"，对77篇原始文献（文献筛选-中文38篇+英文39篇）
用MinerU API全文OCR后提取**全部合格效应量**：

- `code/5-mineru-ocr.py` 全文OCR（77/77成功；全文md不入库，版权原因）
- `docs/extraction_protocol.md` 多效应量提取协议（14个提取批次，来源可回溯至表号）
- `data/extracted_parts/*.csv` 分批提取件 → `data/meta_effects_expanded.csv`
  （540条原始提取 → 419条可算PCC，48篇文献；无效率方程反号、
  非粮镜像/空间溢出/净收益口径剔除）
- `code/meta_stats.py` + `code/7-multilevel-meta.py`：相关效应RVE
  （Hedges-Tipton-Johnson 2010，rho=0.8，文献层面聚类稳健SE，t(m-1)推断），
  IFPRI式[Q1−3IQR,Q3+3IQR]异常值规则，RVE Meta回归（含1/√N精度项），
  Egger/Begg + FAT-PET-PEESE → `results/meta_v3/`
- `code/8-scenario-design-v3.py`：单锚点PCC校准（λ=单产合并弹性/单产合并PCC
  =0.0705/0.106=0.665；各单元弹性=λ×单元RVE合并PCC，10%不显著记0）
  → `results/casm_v3/simulation_plan_v3.csv`
- `code/9-run-casm-v3.py`：CASM基线+9情景 → `results/casm_v3/`

**v3 主要结果（RVE合并PCC，主分析）**：

| 维度 | k条/m篇 | 合并PCC | p值 | 发表偏倚 |
|---|---|---|---|---|
| 粮食单产 | 152/24 | **+0.106***\* | <0.0001 | FAT不显著；PET +0.078***、PEESE +0.096***稳健 |
| 播种面积 | 73/9 | **+0.164***\* | 0.0013 | FAT/Egger/Begg均不显著；PET +0.142* |
| 生产效率 | 170/18 | **+0.146***\* | 0.0001 | FAT不显著 |

分路径：单产 MCI +0.084***、AMS +0.091***；面积 MCI +0.203**、AML +0.248***、
AMS +0.071(不显著)；效率 AMS +0.160***。三维度合并效应全部1%显著——
扩充样本+RVE后，面积维度显著性问题在不动任何数据的前提下由检验功效解决。

**v3 CASM模拟结果（2030年）**：基准粮食73377万吨/自给率85.35%。
S1-Medium +2.31%（自给率87.14%）> S3-Medium +1.32% > S2-Medium +0.84%；
S1-High +3.28%为全情景最高，除S2与S3-Low外各情景谷物自给率均破100%。
与论文初稿的重要叙事差异：新证据下面积效应集中于MCI与AML路径
（AMS面积合并PCC不显著→S2无面积冲击），"农机资本投入路径"因兼具单产与
最大面积效应成为增产潜力最大路径，原稿"AMS复合优势"结论需改写；
AMS的比较优势转移至生产效率维度（+0.160***，效率不进入CASM冲击）。

---

## v2 check后数据版（历史版本，2026-07-08）

对应论文：《农业机械化提升粮食综合生产能力的作用路径与政策潜力——基于Meta分析与CASM情景模拟》
（初稿 20260701）。本目录是对 `code_data_v1` 的全面更新：使用人工check后的中英文
文献参数重建基础数据、按现行Meta分析规范重新估计、重新设计并用Python版CASM重跑情景。

## 目录

```
data/    文献参数提取与汇总.csv      中文文献check版（P_01–P_31）
         En_文献参数提取与汇总.xlsx  英文文献check版（E_01–E_26）
         meta_base_dataset.csv      ★ 整合后的基础数据（56条×47列）
code/    0-build-dataset.py   整合+解析+PCC重算核验
         1-meta-analysis.py   随机效应Meta（REML+Knapp-Hartung）
         2-meta-regression.py WLS Meta回归 + FAT-PET-PEESE
         3-scenario-design.py CASM情景方案生成
         4-run-casm.py        CASM基线+9情景批量求解
casm_model/  Python版CASM副本（casm/ 代码 + inputs/ 输入数据，
             源自 /root/data/CASM/casm_py/base 与 CASM20260514，原模型未动）
results/meta/  Meta分析全部表(csv)、图(png)、日志(txt)
results/casm/  simulation_plan.csv（★模拟方案）、table7/8、明细长表
```

按 `code/0→1→2→3→4` 顺序运行即可完整复现（4号脚本约10分钟）。

## check后数据的关键发现（与v1/论文初稿的差异）

1. **PCC须重算**：check版修订了β/SE/t/N等原始统计量，但表中PCC列仍是修订前旧值。
   本版统一按 PCC=t/√(t²+df) 用check后统计量重算（53/56条可重算，36条与旧值差异>0.05）。
2. **15条文献核心自变量并非机械化**（如耕地块数、数字技术、金融素养、户主年龄、
   高标准农田等），主分析剔除，机械化样本 k=41（单产17、面积6、效率18）。
3. **路径构成变化**：check后 AML(综合机械化水平) 仅4条、AMS 25条、MCI 12条；
   E_24/25/26的自变量实为农机总动力（划入MCI）。
4. **主要结论的变化**：
   - 生产效率维度依旧最稳健（PCC=+0.140***，PET/PEESE校正后仍显著为正）；
   - 单产维度合并PCC=+0.083**，其中AMS路径显著(+0.095***)、MCI经KH校正后不显著；
   - **播种面积维度证据明显弱化**：合并PCC=+0.286*仅10%显著（I²=99.7%，由单篇宏观
     极端值E_24驱动，IQR剔除后降至+0.169）；AMS面积合并PCC不再显著，且唯一面积
     弹性(P_31)是服务价格弹性(-0.221)，不能映射为正向数量冲击；
   - 播种面积维度FAT显著（存在正向发表偏倚），PET校正后为负。
5. **方法升级**：τ²由DL→REML、Knapp-Hartung置信区间、95%预测区间、留一法、
   Meta回归加入τ²加权与最小样本量守卫（面积k=6不跑回归）；删除v1中使用
   虚构数据的GPR模块与41观测上过拟合的XGBoost+SHAP模块。

## CASM情景（results/casm/simulation_plan.csv）

沿用论文 3路径×3速度 设计，Shifter=新弹性中位数×代理指标年均增速，
叠加于基准AYGR0/AAGR0（CGRN粮食作物，2026–2030）：

| 情景 | 单产Shifter/年 | 面积Shifter/年 | 依据 |
|---|---|---|---|
| S1 农机资本投入 M/H/L | 0.427/0.605/0.249% | 0 | 弹性0.178(k=6)；面积单篇极端值不采信 |
| S2 农机社会化服务 M/H/L | 0.458/0.621/0.294% | 0 | 半弹性近似0.164(k=6)；check后面积证据不支持正向冲击 |
| S3 综合机械化水平 M/H/L | 0.204/0.441/0.024% | 0.017/0.036/0.002% | 单产弹性k=1、面积弹性k=1，均高不确定性 |

## 模拟主要结果（2030年，Python版CASM，基期2023）

- 基准：粮食产量 73377万吨、净进口 12595万吨、自给率 85.35%；
  谷物自给率 98.79%、口粮自给率 99.08%（与论文基准一致）。
- S2-High 增产最大（+3.12%，自给率87.79%）；S2-Medium +2.29%略高于S1-Medium +2.14%
  （但因面积冲击归零，S1与S2差距较论文初稿明显收窄，S2优势主要来自略高的推进速度）；
- S3对推进速度高度敏感（Low仅+0.13%，High +2.39%）；
- 除S1-Low、S3-Medium/Low外，各情景2030年谷物自给率均超100%，口粮全部超100%
  （S3-Low口粮99.19%）。

注意：因面积冲击设定收紧，"AMS提单产+稳面积复合优势"这一论文初稿论断在check后
数据下不再成立，正文第五、六部分与表6–9需要相应改写。

## 复现环境

Python 3 + numpy/pandas/scipy/statsmodels/matplotlib/openpyxl。
CASM模型说明见 `/root/data/CASM/casm_py`（github: xinru-han/casm_py）。
