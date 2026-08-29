# 中国膳食转型2050：CASM-World全球溢出研究

本目录是论文的可审计工作区。当前主稿为
`manuscript/manuscript_v3_casm_world.md`，使用重建的CASM-World V2评估中国膳食结构变化对中国、世界、UN区域、收入组以及个别经济体-产品的影响。

## 当前状态

**诊断性条件情景稿，尚不是可直接投稿的发表基线。**

CASM-World V2通过18/20个预先冻结的发表门槛；未通过的是两个2050价格区间门槛。共享作物资源/土地分配模块也尚未实现。主稿、SI和cover letter已同步标注该状态，不把诊断结果包装为无条件预测。

## 研究设计

- 193个求解经济体账户，31种产品，2023共同基准年。
- 中国CASM提供BASELINE、PTS、MTS和CGS四条路径。
- 19种世界模型产品接收中国食物偏好冲击；非食物用途保持SSP路径。
- SSP2逐年求解2023-2050；SSP1/3/4/5求解2023与2050端点。
- SSP2 2050追加低/中/高反应参数和五嵌套需求形式敏感性。
- 主运160个均衡全部收敛，最大市场残差`7.253e-15`。

## 新核心结果（SSP2 2050，CGS相对同SSP基线）

- 世界价格：猪肉-46.2%、稻米-14.6%、牛肉-12.1%；禽肉+8.4%、液体奶+18.6%、全脂奶粉+22.6%。
- 中国：猪肉食物需求-51.6 Mt，液体奶+53.9 Mt；对应净进口平衡变化-32.3 Mt和+48.7 Mt。
- 世界：非重叠13初级产品篮子生产-71.0 Mt，其中亚洲-59.4 Mt。
- 农场端GHG：全球-254.5 Mt CO2e (-4.04%)；中国外-207.2 Mt，占81.4%。PTS则增加+23.1 Mt CO2e。
- 不确定性：五条SSP下配对效应较稳定；嵌套需求下猪肉价格效应收窄到-21.2%，禽肉由+8.4%变为-10.8%。

## 边界

世界模型不包括薯类、蔬菜、水果、蛋、水产品和羊肉，因此CGS是“模型覆盖商品中的部分综合指南转型”，不是完整健康膳食。贸易是净进口恒等式，没有双边流量。GHG是冻结2023年归属的生物性农场端生产排放，不是全生命周期或土地利用变化排放。

## 目录

| 路径 | 内容 |
|---|---|
| `manuscript/manuscript_v3_casm_world.md` | 当前主稿 |
| `manuscript/supplementary_information_v3_casm_world.md` | 新SI |
| `manuscript/revision_notes_casm_world_rebuild_20260829.md` | 旧结论替换和修订说明 |
| `manuscript/cover_letter_nature_communications_draft.md` | Nature Communications方向cover letter（内部HOLD） |
| `model/casm_world_rebuild_core/` | 本次运行对应的模型核心源码、配置、测试与数据哈希清单 |
| `model/casm_world_rebuild_study/` | 路径映射、跑模型、分析、作图和测试代码 |
| `results/casm_world_rebuild/` | 原始压缩结果、对比结果、审计报告和论文表 |
| `figures/casm_world_rebuild/` | 4张主图，PNG和PDF |
| `manuscript/manuscript_v2.md` | 保留的旧版稿，不再是默认稿 |

## 复现

完整独立模型副本和本次所有输出位于：

`/root/data/Paper/食物预测2050/casm_world_rebuild_diet_study_20260829/model_run/`

在该目录下执行：

```bash
export PYTHONPATH="$PWD/src"
/root/data/CASM/casm_world_rebuild_2050/.venv/bin/python study/china_diet/prepare_diet_paths.py
/root/data/CASM/casm_world_rebuild_2050/.venv/bin/python study/china_diet/run_counterfactuals.py
/root/data/CASM/casm_world_rebuild_2050/.venv/bin/python study/china_diet/analyze_counterfactuals.py
/root/data/CASM/casm_world_rebuild_2050/.venv/bin/python study/china_diet/make_figures.py
/root/data/CASM/casm_world_rebuild_2050/.venv/bin/python -m pytest -q study/china_diet/tests
```

论文-结果一致性审计：

```bash
cd /root/data/Paper/食物预测2050/casm_world_rebuild_diet_study_20260829/paper_worktree/food_demand_2050
python3 audit_manuscript_repository_consistency.py
```

原始模型`/root/data/CASM/casm_world_rebuild_2050/`没有被本研究运行改写。
