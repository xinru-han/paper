修订版本：2026-11-08

建议先阅读
  manuscript_en.docx / manuscript_en.pdf
    完整英文修订稿，不只是英文标题或摘要。
  猪肉降价_食品篮子成本_中文修订稿.docx / 同名PDF
    与英文稿对应的中文修订稿，末尾保留英文摘要供核对。
  supplementary_material_en.docx / supplementary_material_en.pdf
    与正文引用对应的英文补充材料，补充表S1—S16。

采用标题
  猪肉降价，食品篮子仍变贵：中国家庭购买响应与品类价格抵消的微观证据
  Cheaper Pork, Costlier Food Baskets:
  Price Offsets and Household Purchases in China

原稿与本次修改
  以 welfare_revision_2026-10-13/家庭食品购买的价格响应与成本暴露_英文期刊导向修订稿.docx
  为基础；原文件未覆盖，副本保存在 sources/input_manuscript.docx。
  引言按研究动机、相关研究、交易资料中的具体问题、研究问题与设计、
  两项经验贡献、主要结果与文章结构重写。
  成本分解结果前置为第四节；购买响应及频率置于第五节；全文表图重编号。
  摘要、引言、结果解释、讨论和结论围绕同一问题调整。
  识别条件与理论诊断集中于方法、诊断和一段讨论，不在引言及摘要反复设防。
  新增品类抵消图；重画价格路径，修复原图纵轴标签重叠。
  英文稿页眉、表头、图注、参考文献与交叉引用同步整理。

贡献及其证据位置
  1. 实际价格组合中的品类抵消及家庭间分布。
     正文表2、表3、图2及补充表S16：猪肉贡献约-4.60个百分点，其他肉类
     约+0.60个百分点，非肉类约+6.97个百分点；净成本仍增加2.97%。
     收入档的成本排序随涨价品类改变。这里没有宣称发明新指数或识别因果冲击。
  2. 食品子预算内的非等比例购买响应及其采购频率背景。
     正文表4、表5：其他肉类和食用油的预算响应高于1，蔬菜和水果低于1；
     食用油和主食的月度低购买覆盖与年度高覆盖并存。
     函数形式、食品聚合和规格比较是支撑检查，没有另包装成方法创新。

本次实际运行
  code/06_price_offset_check.do 已用本机 Stata/SE 17 运行成功。
  运行日志：logs/06_price_offset_check.log，末尾标记 PRICE_OFFSET_CHECK_SUCCESS。
  从现有 Stata 月度面板重新计算价格年均值和2020年基准篮子成本，核对原稿
  2.973402578372977%和4.427046612142189元，并导出八类完整成本贡献及两张图。
  code/build_revision.py 已运行并将原八张表的222个数值与已有Stata CSV逐项核对。
  输出正文仍保留这八张表的数值和56个可编辑公式对象；公式下标作显示兼容修复。
  本次没有重新估计主需求模型，也没有运行本目录早先的曲率约束福利模拟。
  不能把新增成本核对描述成全套需求系统重估。

复现与来源
  python3 code/build_revision.py
    使用已复制的 sources/ 文档和汇总CSV重建中英文Word与补充材料。
    依赖 python-docx、lxml、Pillow；不需要R，不重新估计统计模型。
  stata-se -b do code/06_price_offset_check.do
    重新计算成本分解需要原有本地数据与配置：
    welfare_revision_2026-10-13/code/00_config.do
    meat_merge_trial_2026-10-11/data/analysis_monthly.dta
    该Stata脚本沿用现有Stata口径，不用历史R模型。
  sources/welfare_stata/ 保存指定目录中的既有Stata代码；
  sources/upstream/ 保存正文实际使用的八分类Stata代码、ado及汇总结果。
  sources/basket_weights_2021.csv 保存组内价格权重。
  outputs/source_manifest.json 记录复制来源文件的SHA-256；
  outputs/document_validation.json 记录表格核对、成本数值和Word检查。
  没有复制或上传原始交易或家庭微观数据；本文件夹不是含原始数据的全流程复制包。

文件用途
  outputs/：新增Stata成本分解CSV、DTA及可编辑图源所对应的PNG/PDF图。
  code/：本次新增的Stata核对、正文文本及Word生成程序。
  logs/：实际运行日志。
  submission_materials/highlights.txt：四条英文研究要点。
  submission_materials/literature_checks.txt：本次写作核对的主要文献来源。

投稿前作者仍需补齐
  作者与单位、通讯作者、基金、利益冲突与数据可得性说明；确认交易数据使用授权。
  再按选定期刊的字数、匿名审稿及格式要求整理。本文不把固定篮子成本表述为
  结构福利、营养变化、全国代表性通胀或所需补助标准。
