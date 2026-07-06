# Research Papers Repository

论文代码与结果汇总库。每篇论文对应一个子目录，包含完整的code、data、results。

## 目录结构

```
paper/
├── province_food_consumption_maidads/     (省级食物消费MAIDADS模型)
│   ├── README.md                          (详细说明)
│   ├── scripts/                           (所有Python脚本)
│   ├── Results/                           (完整结果)
│   ├── Data/                              (输入数据)
│   └── From_quantity_to_composition_2024update.docx (论文)
└── ...                                     (其他论文项目)
```

## 已发布论文

### 1. Province Food Consumption: MAIDADS Demand System
- **文件夹**: `province_food_consumption_maidads/`
- **论文**: From_quantity_to_composition_2024update_final
- **模型**: Modified AIDS Demand System (MAIDADS)
- **数据**: 31省×10年面板数据 (2014-2023)
- **关键结果**: 
  - MAIDADS nll = −4481.554
  - 支出分配ω = 0.705，替代弹性κ = 4.911
  - 2050年饲料粮需求393.4 Mt

详见 `province_food_consumption_maidads/README.md`

## 使用说明

### 克隆仓库
```bash
git clone git@github.com:xinru-han/paper.git
cd paper
```

### 运行某篇论文的代码
```bash
cd province_food_consumption_maidads/scripts
python3 run_maidads_pipeline.py
```

### 提交更新
```bash
git add .
git commit -m "Update: description"
git push
```

## 维护

- 所有code更新需提交到git
- 大文件使用 `.gitignore` 排除（如>100MB的中间数据）
- 每个子项目需包含完整README说明

---

*最后更新：2026-07-06*
