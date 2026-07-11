# 食物需求预测2050 / China's Diet Transition to 2050

Global Food Security / Journal of Environmental Management 方向的工作稿
《China's dietary transition to 2050: implications for agricultural markets, trade
and model-covered environmental pressures》的代码、数据与稿件。原稿经全面升级：
GAMS→Python复现、接入CASM-World世界模型、国际权威足迹系数库、边界隔离账户、
模型覆盖商品的全球净效应核算。

## 目录

| 目录 | 内容 |
|---|---|
| `scenarios/` | 模拟方案（整理自原Excel）：情景定义A1–C6、宏观假设、收入弹性、人均路径、健康膳食基准、营养系数 |
| `model/` | Python版CASM（v2.2.7论文版）：19情景复现runner + 验证脚本 |
| `model/world/` | CASM-World世界模型情景runner（4情景×13区域×2050）和本地 `cw/` 核心包 |
| `modules/coefficients/` | 国际足迹系数库（FAOSTAT/Poore&Nemecek 2018/Mekonnen&Hoekstra/IPCC 2019/Ludemann 2022，全部溯源） |
| `modules/` | 足迹核算模块（碳双边界/蓝绿灰水/活性氮/土地）+ 事后分析 |
| `results/` | 中国19情景长表、世界4情景长表、足迹结果、事后分析（SSR/行星边界/MTS效率/健康代理）、验证报告 |
| `figures/` | 4主图+4扩展图（png 300dpi + pdf）与作图脚本 |
| `manuscript/` | manuscript_v2.md、SI、response_to_reviewers.md、cover_letter.md |
| `docs/` | 审稿意见整理、原论文表格提取、Nature故事线设计 |

## 核心结果（2050，HDS相对BS）

- 中国境内：能量摄入-26%、红肉-72%、碳排放-31%（含技术）/-1%（固定系数，因需求经贸易外传）
- 世界价格：猪肉-56%、大豆-35%、玉米-33%、奶粉+20%（唯一逆势）
- 供给地理：巴西大豆-11.7%、阿根廷-14%、美国猪肉-46%；中国境外收获耕地减少21.7 Mha
- 全球净效应：模型覆盖商品农场端碳-495 Mt CO₂e，91%发生在中国境外；水、氮和土地占用已移至边界敏感性/诊断账户，不再作为完整全球总量
- MTS温和转型：当前增长率插值设定下实现约65%的PTS-HDS变化（21指标中位）；替代插值和弹性敏感性仍需扩展

## 复现

```bash
cd model && python3 run_scenarios.py && python3 validate.py   # 中国19情景（~6分钟）
cd world && python3 run_scenarios.py && python3 validate_china_demand_alignment.py && python3 analyze.py
cd ../../modules && python3 footprints.py                     # 足迹核算
cd ../figures && python3 make_figures.py                      # 全部图表
```

验证：与GAMS真值逐格中位偏差0（机器精度），论文表2–6全部复现至舍入精度
（见 `results/validation_report.md`，含原GAMS产物两处已知问题的说明）。

原始材料位于 `/root/data/Paper/食物预测2050/`。模型重跑请先复制本目录到独立工作区，避免运行输出污染原始仓库。
