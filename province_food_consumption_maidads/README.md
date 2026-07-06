# Province Food Consumption: MAIDADS Demand System

完整复现中国省级食物消费的MAIDADS（Modified AIDS demand system）模型，对应论文《From_quantity_to_composition_2024update_final》。

## 项目结构

```
province_food_consumption_maidads/
├── README.md                                    (本文件)
├── scripts/                                     (所有Python脚本)
│   ├── run_maidads_pipeline.py                 (核心管线：面板+基础估计)
│   ├── run_pgdp6_models.py                     (GDP人均增长模型)
│   ├── run_original_item_models.py             (备选：食物品项模型)
│   ├── run_split_pork_*.py                     (备选：拆分猪肉)
│   ├── run_additional_checks.py                (稳健性+Bootstrap)
│   ├── run_formal_bootstrap.py                 (正式Bootstrap)
│   ├── build_gdp_food_nutrition_results.py     (GDP情景)
│   ├── prepare_paper_workflow_outputs.py       (论文包)
│   ├── compile_markdown_outputs.py             (结果整合)
│   └── build_2024update_docx.py                (生成论文docx)
├── Results/                                     (所有结果CSV/输出)
│   ├── parameter_estimates.csv                 (估计参数)
│   ├── elasticity_*.csv                        (需求弹性)
│   ├── projection_*.csv                        (GDP情景投影)
│   ├── 省级MAIDADS_全部结果整合.md             (结果汇总文档)
│   ├── 省级MAIDADS_全部代码整合.md             (代码汇总文档)
│   ├── FormalBootstrap_correct/                (Bootstrap置信区间)
│   ├── GDP_Food_Nutrition/                     (GDP增长情景)
│   ├── PGDP6/、SplitPork*/                     (备选模型结果)
│   └── ...
├── Data/
│   └── output/
│       └── maidads6_panel.csv                  (310 obs面板数据)
├── From_quantity_to_composition_2024update.docx (最终论文)
```

## 核心结果

| 指标 | 值 | 说明 |
|---|---|---|
| MAIDADS nll | −4481.554 | 负对数似然，模型拟合度 |
| AIDADS nll | −4247.48 | 7组AIDS嵌套模型 |
| LR | 466.5 | MAIDADS vs AIDADS似然比 |
| ω | 0.705 | 支出分配参数 |
| κ | 4.911 | 替代弹性参数 |
| 观测数 | 310 | 31省×10年(2014-2023) |
| 商品组 | 7 | grain,oil,vegfruit,pork,meatother,dairyegg,nonfood |
| 饲料粮(2030) | 378.3 Mt | 全国年需求量 |
| 饲料粮(2035) | 389.3 Mt | GDP增长情景 |
| 饲料粮(2050) | 393.4 Mt | 长期趋势 |
| 2050猪肉占比 | 41.9% | 2050年饲料粮中猪肉占比 |

## 运行说明

### 环境要求

```bash
pip install numpy pandas scipy matplotlib statsmodels python-docx openpyxl
```

### 执行顺序（从scripts/目录）

1. **核心估计**
   ```bash
   python3 run_maidads_pipeline.py
   ```
   生成 parameter_estimates.csv、elasticity_*.csv

2. **备选设定**（可选）
   ```bash
   python3 run_pgdp6_models.py
   python3 run_original_item_models.py
   python3 run_split_pork_models.py
   # ...其他备选脚本
   ```

3. **稳健性检验**
   ```bash
   python3 run_additional_checks.py
   python3 run_formal_bootstrap.py
   ```

4. **GDP增长情景**
   ```bash
   python3 build_gdp_food_nutrition_results.py
   ```

5. **论文输出整合**
   ```bash
   python3 prepare_paper_workflow_outputs.py
   python3 compile_markdown_outputs.py
   ```

6. **生成论文docx**
   ```bash
   python3 build_2024update_docx.py
   ```

## 重要修复

此版本包含4处关键修复，修复了旧的6组商品分类残留导致的KeyError：

1. **run_pgdp6_models.py** — GROUP_LABEL_CN更新为7组(含pork/meatother)
2. **build_gdp_food_nutrition_results.py** — GROUP_LABEL_CN + group_order 7组化
3. **prepare_paper_workflow_outputs.py** — 循环列表由meatsea改为pork+meatother
4. **build_2024update_docx.py** — 写死的macOS路径改为自动推导(PROVINCE_ROOT)

## 论文对应

- 论文文件：`From_quantity_to_composition_2024update.docx`
- 论文标题：《From quantity to composition: Demand-driven transitions in food consumption structure across Chinese provinces》
- 数据期间：2014-2023
- 地区范围：31个省级行政区

## 数据来源

- 面板数据：`Data/output/maidads6_panel.csv` (310观测)
- 来源：国家统计局、各省统计局

## 联系

- 作者：Xinru Han
- 邮箱：hanxinru888@gmail.com

---

*最后更新：2026-07-06*  
*所有结果已复现并与最终论文版本核对一致*
