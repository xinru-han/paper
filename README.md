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
├── covid_wugong/                          (新冠对务工的影响)
│   ├── scripts/                           (Python 流水线)
│   ├── repro/                               (R 复现与输出)
│   └── repro_deliverables/                  (最终交付结果)
├── feed_import_elasticity/                (饲料进口弹性 QU AIDS)
│   ├── revision_2026/                       (审改复现代码与结果)
│   ├── restricted_demand/                   (弹性矩阵结果)
│   └── data/                                (*-feed.csv 输入)
├── cctv_easi_demand/                      (央视高频食品需求 EASI)
│   ├── final_demand_model_R/                (脚本 23 + 诊断输出)
│   ├── repro_run/                           (R 流水线 20–22 + 结果)
│   └── scripts/                             (Python 数据工程)
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

### 2. COVID Impact on Migrant Work (新冠对务工的影响)
- **文件夹**: `covid_wugong/`
- **内容**: Python 数据流水线 + R 复现脚本 + 表格/图表结果
- **自动同步**: `/root/data/Paper/covid` → git，每 5 分钟推送

详见 `covid_wugong/README.md`

### 3. Feed-Grain Import Elasticity (饲料进口弹性)
- **文件夹**: `feed_import_elasticity/`
- **内容**: QUAIDS 审改 Python 流水线 + bootstrap + 政策识别 + 弹性结果
- **自动同步**: `/root/data/Paper/饲料进口弹性` → git，每 5 分钟推送

详见 `feed_import_elasticity/README.md`

### 4. CCTV High-Frequency Food Demand — EASI (Paper1-EASI)
- **文件夹**: `cctv_easi_demand/`
- **内容**: SY-EASI/QUAIDS 需求系统 R 流水线 + Python 数据工程 + 弹性诊断
- **自动同步**: `/root/data/Paper/央视数据/Paper1-EASI` → git，每 5 分钟推送

详见 `cctv_easi_demand/README.md`

### 5. Food Self-Provisioning & Separability (可分离性/家庭食物自给)
- **文件夹**: `separability_selfprovisioning/`
- **论文**: Farming for the Family Table: Household Composition and Food Self-Provisioning in Rural China
- **内容**: R 复现流水线（Benjamin 式联合排除检验 + 两部模型 + 村内固定效应 + FDR + 后估计 A0–A5）
- **数据**: 3,565 户 × 8 类食物 = 28,520 户-类观测（2023–2024 八省农户调查）
- **关键结果**: 可分离性被拒绝——主参与检验 Wald=16.73 (p=0.002, N=27,568)；村内数量边际 Wald=16.06/15.77 (p=0.003)；失效集中于蛋、油、菜、果
- **自动同步**: `/root/data/Paper/食物消费数据/Paper1-Seperability` → git，每 5 分钟推送

详见 `separability_selfprovisioning/README.md`

### 6. Soybean Second-Best Equilibrium (大豆全产业链第二优均衡)
- **文件夹**: `soybean_second_best/`
- **论文**: 中国大豆全产业链第二优均衡理论（soybean_theory_paper_revised.tex）
- **内容**: Python 定量模拟 M1–M7（校准规划模型/进口组合蒙特卡洛/生产网络放大/万户农户 ABM/政策矩阵 P0–P6/命题检验 T1–T6/Sobol 敏感性）+ 交互式仿真网站（Flask, 175.27.226.92:7070）
- **数据**: 2023 年全国投入产出表（211 部门）、《全国农产品成本收益资料汇编 2024》、海关 2024 分国别进口、NBS 产量
- **关键结果**: Y\*=2085 万吨复现观测（揭示性安全权重 β≈886）；6/6 理论命题通过；政策排序 P6(定向+韧性组合) ≻ P2 定向补贴 ≻ P1 统一补贴 ≻ 单项包 ≻ P0
- **自动同步**: `/root/soybean_sim` → git，每 5 分钟推送

详见 `soybean_second_best/README.md`

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
