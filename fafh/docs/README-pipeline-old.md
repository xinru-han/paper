# 户外消费系数预测研究项目

## 项目概述

本项目旨在预测中国各省份和全国层面的户外食物消费系数，采用**预测任务**（Predictive Task）范式，重点关注预测准确性和模型稳健性。

## 项目结构

```
/usr/fafh/
├── README.md                          # 项目主README（本文件）
├── requirements.txt                   # Python依赖
├── run_complete_analysis.py          # 主控制脚本（完整分析流程）
│
├── data/                              # 数据文件目录
│   ├── data.csv                      # 微观数据（2004-2011年）
│   ├── data2012.csv                  # 宏观预测数据（2012年及以后）
│   ├── data_q.csv                    # 消费量数据
│   ├── national_avg.csv              # 全国平均户内消费
│   └── procince_pop.csv              # 省份人口数据
│
├── config/                            # 配置文件目录
│   ├── requirements.txt              # 依赖配置
│   └── requirements_models.txt       # 模型依赖配置
│
├── checkpoints/                       # 模型检查点目录
│   └── tabpfn-*.ckpt                 # TabPFN预训练模型
│
├── output/                            # 输出结果目录
│   ├── predictions/                  # 预测结果
│   ├── evaluations/                  # 评估结果
│   └── figures/                      # 图表
│
├── src/                               # 源代码目录
│   ├── data_preparation.py           # 基础数据准备模块
│   ├── data_preparation_advanced.py  # 高级数据准备（Copula、Kriging）
│   │
│   ├── models/                       # 模型实现目录
│   │   └── custom_models.py         # 自定义模型（TabM、Trompt等）
│   │
│   ├── predictors/                   # 预测脚本目录
│   │   ├── predict_fttransformer_advanced.py # FT-Transformer（高级版）
│   │   ├── predict_fttransformer.py  # FT-Transformer（基础版）
│   │   ├── predict_xgboost.py       # XGBoost
│   │   ├── predict_catboost.py      # CatBoost
│   │   ├── predict_lightgbm.py      # LightGBM
│   │   ├── predict_randomforest.py  # Random Forest
│   │   ├── predict_linear.py        # Ridge Regression
│   │   ├── predict_lasso.py         # Lasso Regression
│   │   ├── predict_mlp.py           # MLP
│   │   ├── predict_resnet_tabular.py # ResNet
│   │   ├── predict_tabnet.py        # TabNet
│   │   ├── predict_tabm.py          # TabM
│   │   ├── predict_tabpfn.py        # TabPFN
│   │   ├── predict_excelformer.py   # ExcelFormer
│   │   ├── predict_trompt.py        # Trompt
│   │   └── predict_xrfm.py         # XRFM
│   │
│   ├── analysis/                    # 分析脚本目录
│   │   ├── evaluate_models.py      # 模型评估
│   │   └── robustness_analysis.py   # 稳健性检验
│   │
│   └── utils/                        # 工具函数目录
│       └── (待添加)
│
├── scripts/                           # 脚本目录
│   ├── calculate_national_average.py  # 计算全国平均
│   ├── calculate_final_results.py    # 计算最终结果
│   └── run_all_models.py            # 运行所有模型
│
├── docs/                              # 文档目录
│   ├── COMPLETE_RESEARCH_METHODOLOGY.md # 完整研究方法
│   ├── MODEL_TECHNICAL_REVIEW.md     # 模型技术审查
│   ├── MODEL_COMPARISON_EVALUATION.md # 模型对比评估
│   └── ...                           # 其他文档
│
└── legacy/                            # 旧版本备份目录
    └── ...                            # 旧文件备份
```

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行完整分析

```bash
python run_complete_analysis.py
```

这将运行：
1. FT-Transformer理论完美实现
2. 稳健性检验
3. 模型对比（12个模型）
4. 稻谷预测和全国消费系数计算

### 3. 运行单个模型

```bash
# FT-Transformer高级版
python src/predictors/predict_fttransformer_advanced.py

# 其他模型
python src/predictors/predict_xgboost.py
python src/predictors/predict_catboost.py
# ... 等等
```

### 4. 运行所有模型对比

```bash
python scripts/run_all_models.py
```

## 主要功能

### 1. 数据准备

- **Copula收入分布匹配**：使用Copula方法匹配微观和宏观收入分布
- **Kriging空间插值**：使用Kriging方法进行空间插值
- **统一随机种子**：确保结果可重现

### 2. 主要模型：FT-Transformer + Hurdle

- **FT-Transformer**：专门为表格数据设计的Transformer架构
- **Hurdle模型**：两阶段模型（参与决策 + 强度决策）
- **Bootstrap预测区间**：提供不确定性量化
- **早停机制**：防止过拟合
- **超参数优化**：使用Optuna进行50次试验

### 3. 对比模型（12个）

- **Transformer-based**：FT-Transformer, TabNet, TabM
- **Tree-based GBDT**：XGBoost, CatBoost, LightGBM
- **Bagging**：Random Forest
- **Linear**：Ridge, Lasso
- **Deep Learning**：MLP, ResNet
- **特殊方法**：TabPFN

### 4. 稳健性检验

- **Monte Carlo方法**：估计预测区间
- **贝叶斯方法**：提供不确定性量化

## 输出结果

### 预测结果

- `output/predictions/predictions_fttransformer_advanced.csv`：FT-Transformer预测结果
- `output/predictions/predictions_fttransformer_bootstrap.csv`：Bootstrap预测区间
- `output/predictions/predictions_*.csv`：其他模型预测结果

### 评估结果

- `output/evaluations/model_comparison.csv`：模型对比结果
- `output/evaluations/robustness_results.csv`：稳健性检验结果

### 最终结果

- `grain_structure_predictions.csv`：粮食结构预测
- `national_outdoor_coefficient_final.csv`：全国户外消费系数

## 文档

详细文档请参考 `docs/` 目录：

- `COMPLETE_RESEARCH_METHODOLOGY.md`：完整研究方法（用于论文）
- `MODEL_TECHNICAL_REVIEW.md`：模型技术审查
- `MODEL_COMPARISON_EVALUATION.md`：模型对比评估
- `HURDLE_MODEL_EVALUATION.md`：Hurdle模型评估

## 注意事项

1. **数据路径**：确保数据文件在 `data/` 目录中
2. **GPU支持**：推荐使用GPU加速训练
3. **运行时间**：完整分析可能需要数小时（取决于硬件）
4. **内存要求**：建议16GB+内存

## 许可证

[待添加]

## 联系方式

[待添加]
