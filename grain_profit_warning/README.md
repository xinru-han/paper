# 种粮盈亏预测与预警体系 (grain_profit_warning)

省×作物×年面板（7 种粮食作物，2004–2024）上的种粮盈亏预测：
计量基准 + 树集成 + FT-Transformer + TabPFN + PySR 符号回归，
扩窗滚动时序验证（2015–2024），SHAP 关键因素识别，四级亏损预警体系。

## 目录

```
docs/research_design.md     研究设计总纲
code/
  01_build_grain_prices.py  发改委原粮收购价旬报 → 省×品种×年特征
  01b_build_retail_prices.py 央视成品粮零售旬报 → 全国品种×年信号
  02_build_panel.py         主面板构建(见 data/processed/data_dictionary.csv)
  common.py                 特征白名单 + 扩窗滚动验证框架
  03_baselines.py           FE-OLS/Logit + RF + XGBoost + LightGBM
  05_ft_transformer.py      FT-Transformer (rtdl)
  06_tabpfn.py              TabPFN v2
  07_pysr.py                符号回归(可解释预警公式)
  08_shap.py                SHAP 因素识别
  09_warning.py             预警分级体系 + 2023/2024 演示
data/processed/             主面板与中间数据
output/{tables,figures,preds}/ 结果
paper/                      论文稿
```

## 数据源

- 《全国农产品成本收益资料汇编》省级面板（经 cost_elasticity 项目清洗）
- 发改委农业生产资料价格、主产区原粮购销价格旬报（2020–2025）
- 央视成品粮零售价格旬报（2005–2024）
- 省级气温/降水及 1973–2002 基准距平

## 复现

按编号顺序运行 code/ 下脚本；Python 3.10，依赖见 requirements 注释。
仓库每 5 分钟自动同步（scripts/sync-grain-profit.sh）。
