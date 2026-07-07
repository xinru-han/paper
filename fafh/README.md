# FAFH 论文项目（Food Policy 改投版）

中国食物消费统计的户外消费（FAFH）调整系数：机器学习估计 + 粮食安全/营养政策含义量化。
AE desk reject 后改投 **Food Policy**，核心增补第 7 节（膳食指南对照、供给—消费对账、自给率与饲料粮）。

## 目录导航

| 目录 | 内容 |
|---|---|
| `manuscript_FP/` | **当前投稿版**：manuscript-FP.tex/pdf、reference-FP.bib、全部图（fig2–fig6、figA1–A6）、numbers.json（第7节数字唯一来源）、sources.md（外部数据出处）、cover-letter-FP.txt、highlights-FP.txt、REVISION-NOTES-FP.md（改投说明）、TODO-analysis-FP.md（计算规范） |
| `code/` | 全部 pipeline 代码：predict_*.py（14个模型）、run_*.py（主流程）、postprocess、sensitivity、绘图；config/、models_custom/、checkpoints/（TabPFN ckpt）；RUN_ORDER.md、执行流程说明.md |
| `data/` | 输入数据：data.csv（CHNS 微观 2004–2011）、data2012.csv（宏观协变量）、imputed_ratios_best.csv、applications/（第7节 NBS/海关/营养系数数据）、geo/（地图 geojson） |
| `results/` | 输出结果：predictions/、national/、province/、grain_structure/、ratio_samples/、accuracy/（模型对比）、logs/、shap_plots/ |
| `archive/` | AE 投稿归档（manuscript-0529.tex、AE/、journal_submission/ 复现包、Cover Letter/Title Page.docx）、旧 FP 草稿（FP-package 占位符版、修改意见-claude、food_policy_revised.tex）、models_legacy |
| `docs/` | 方法说明（Copula）、论文初稿.md、paper_draft/（早期稿+审稿意见） |
| `lit/` | 参考文献 PDF（含 chns/ 子目录） |

## 运行方式

**必须在本目录（项目根）运行**（代码用 `os.getcwd()` 定位数据）：

```bash
python code/run_step1_imputation.py      # 步骤1：缺失插补
python code/run_step2_to_end.py          # 步骤2至结束：全模型预测+汇总
python code/predict_xgboost.py           # 或单模型
```

新生成的输出会写到项目根目录，请手动归入 `results/` 对应子目录。

## 编译论文

```bash
cd manuscript_FP && tectonic manuscript-FP.tex   # tectonic 已装于 /usr/local/bin
```

## GitHub

代码与结果同步至 `git@github.com:xinru-han/paper.git` 的 `fafh/` 子目录（cron 每 5 分钟自动同步；不含 CHNS 微观数据、文献 PDF、40MB ckpt）。
