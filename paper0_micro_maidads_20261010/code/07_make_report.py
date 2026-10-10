"""Public aggregate tables and figures; never export household identifiers."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
FAMILY = {"0": "未知形态", "1": "单人家庭", "2": "夫妻家庭", "3": "核心家庭", "4": "扩展家庭"}


def formatting(df):
    return df.to_string(index=False, float_format=lambda x: f"{x:.5f}", max_rows=None, max_cols=None)


def figures(k):
    folder = OUT / f"maidads_{k}"
    table = pd.read_csv(folder / "income_growth_scenarios.csv", dtype={"stratum": str})
    baseline = table.loc[table.dimension.eq("all")&table.specification.eq("main")&table.growth_multiplier.eq(1)].sort_values("group")
    fig, ax = plt.subplots(figsize=(11, 5), constrained_layout=True)
    x = np.arange(k)
    ax.bar(x-.18, baseline.food_expenditure_elasticity, width=.36, label="食物支出弹性", color="#347d58")
    ax.bar(x+.18, baseline.income_elasticity, width=.36, label="人均收入弹性（含参与变化）", color="#b54f59")
    ax.axhline(0, color="#777777", linewidth=.6)
    ax.set_xticks(x, baseline.group_name, rotation=25, ha="right")
    ax.set_ylabel("弹性：样本人口加权总量响应")
    ax.legend(frameon=False)
    fig.savefig(folder / "baseline_income_vs_food_expenditure_elasticity.png", dpi=180)
    plt.close(fig)
    for dimension, filename, ylabel, quantity in (
        ("province", "province_income_growth_quantity.png", "相对基期的预测消费量", True),
        ("family", "family_income_growth_elasticity.png", "人均收入弹性", False),
    ):
        subset = table.loc[table.dimension.eq(dimension)&table.specification.eq("main")]
        fig, axes = plt.subplots(int(np.ceil(k/2)), 2, figsize=(12, 2.5*int(np.ceil(k/2))), constrained_layout=True)
        handles = None
        for j, ax in enumerate(axes.flat):
            if j >= k:
                ax.axis("off")
                continue
            for name, d in subset.loc[subset.group.eq(j+1)].groupby("stratum", sort=True):
                d = d.sort_values("growth_multiplier")
                y = d.predicted_quantity_pc_month/d.predicted_quantity_pc_month.iloc[0] if quantity else d.income_elasticity
                label = FAMILY.get(str(name), str(name)) if dimension == "family" else str(name)
                ax.plot(d.growth_multiplier, y, marker="o", markersize=3, linewidth=1.2, label=label)
            ax.set_title(baseline.group_name.iloc[j], fontsize=10)
            ax.set_xlabel("收入倍数（价格和家庭构成固定）", fontsize=9)
            ax.set_ylabel(ylabel, fontsize=9)
            ax.axhline(1 if quantity else 0, color="#888888", linewidth=.5)
            ax.grid(axis="y", color="#dddddd", linewidth=.5)
            handles = ax.get_legend_handles_labels()
        fig.legend(*handles, loc="outside upper center", ncol=4, frameon=False, fontsize=9)
        fig.savefig(folder / filename, dpi=160)
        plt.close(fig)


def main():
    fonts = [p for p in font_manager.findSystemFonts() if any(x in p.lower() for x in ("noto", "wqy", "cjk"))]
    if fonts:
        prop = font_manager.FontProperties(fname=fonts[0])
        font_manager.fontManager.addfont(fonts[0])
        plt.rcParams["font.family"] = prop.get_name()
    plt.rcParams["axes.unicode_minus"] = False
    introduction = """微观 MAIDADS：8类与10类食品、零消费、收入增长及家庭形态
生成日期：2026-10-10

一、解释口径
本轮采用所选八/十类食品的总消费，购买、自用生产和赠送统一按社区价格估值，不另作购买/自用弹性比较。
食物预算为该食品集合的消费总估值，不是纯现金购买支出，也不是所有未纳入食品（如豆类）的全口径金额。
8类和10类使用相同食品明细和相同3145户共同样本；10类从肉类拆出猪肉（含排骨），从水果类拆出干果（坚果）。
第二阶段为原省级项目隐式效用 MAIDADS 的食物条件系统，而非 EASI 或 GEASI；没有饲料压力指数。
收入采用调查上一年家庭总收入/吃饭人口/12，省份数值为样本人口加权平均，不是有抽样权重的省级总体估计。
价格保持固定，收入分别乘以1、1.1、1.25、1.5、2；是比较静态情景，不是时间或因果预测。
q是固定参考篮子的等价人均月斤数，不等于所有实际细项未来物理斤数。
所有省份结果先对每户预测再按吃饭人口加权，未用省均收入替代个体收入。

二、零消费处理
Stata估计Gamma-log食物预算模型与逐食品probit边际参与率。
独立参与检验不通过，因此主结果为单公共因子相关probit；非截断因子分布保留这些边际，条件非空后有明确normalizer。
采用Gauss-Hermite积分32节点并检查64节点。
在每个非空参与集合内，按集合归一化边际预算参数求解原MAIDADS隐式效用；集合外数量严格为0。
正份额采用Dirichlet条件似然，保证每户、每个参与集合的预算闭合；无加小常数、删除零消费户或事后比例修补。
预测对8类255个、10类1023个非空集合精确求和；没有随机蒙特卡洛误差，随机因子积分仍有可审计数值误差。
低效用承诺量端点delta固定为0，保证任意小正预算可行；这是明确的受限MAIDADS，不冒充完整自由delta模型。
此hurdle为可检验的经验扩展，不是已推导完整Kuhn-Tucker角点随机效用系统；参与误差与正份额误差条件独立仍是维护假设。
共同因子只允许非负的一因子相关结构，不能声称已消除所有联合参与错设。
不宣称首次零消费需求系统或首次人口特征MAIDADS；可能创新须限定并进一步查重和推导。

三、弹性及推断
食物支出弹性：对食物总预算的响应，不是收入弹性。
人均收入弹性 = 食物预算收入响应传导 + 食品参与率收入响应；表中分别列intensive/extensive。
Hicksian/Marshallian结构矩阵仅针对固定参与集合、固定食物预算的条件系统。
包含参与及预算变化的全样本价格响应称total price response，不能冒称结构Hicksian。
负Hicksian来自MAIDADS原效用结构的解析导数，没有Cholesky修正，也没有为符号/显著性筛选模型。
Stata第一阶段p值确实由村年聚类sandwich获得，但尚未传播到第二阶段和完整预测；完整系统未做cluster bootstrap。
因此最终食品弹性和预测的p值/区间留空，不把第一阶段p值或条件delta method当成完整两阶段推断。
AIDADS(gamma=0)对照报告AIC/BIC；因零承诺量边界且omega在原假设下不识别，不报告常规卡方LR p值。
8类与10类似然定义/维度不同，不能用它们的AIC高低跨分类选模。

四、数据与模型局限
其他肉的独立代表报价不足，使用细项社区价格区间校准代理，质量构成误差仍可能存在；10类仅是可估计的探索拆分。
水产直接报价和独立价格较少；价格来源和补全层级见数据审计。
上一年收入与本月消费存在时间窗差异；极低收入户食品/收入比异常已标记，未为显著性改金额。
收入尾部训练敏感性、食物价格折算购买力敏感性和独立参与敏感性均列出。
增加线性收入函数敏感性：二次项村聚类联合Wald p为10类.040858、8类.042723；AIC弱支持二次而BIC支持线性。
扩展家庭在线性预算模型中收入弹性仍近零/略负且不显著（10类p=.586281），不能声称最终负值显著或只由二次尾部造成。
原数值guard存在活跃边界，已保留历史fit并采用真正收敛的扩大guard解重新计算全部结果。最终8/10主参数没有活跃数值边界。
8类扩界前后支出弹性最大变化.01619，10类约.000547；tau/kappa长期端点仍弱识别，不推断无限收入下最低消费量。
没有识别完整CPI实际收入、食物预算内生性、参与-数量联合内生性或因果价格效应；收入第一阶段本身不等于有效IV识别。
家庭形态来自完整吃饭人口关系名册：0未知375，1单人169，2夫妻1104，3核心434，4扩展1063。
收入翻倍中超出原样本P1/P99收入区间的比例单独报告；不可把高收入外推当验证成功。

"""
    txt = [introduction]
    md = ["# 微观 MAIDADS 结果\n", introduction]
    for k in (8, 10):
        folder = OUT / f"maidads_{k}"
        base = pd.read_csv(folder / "baseline_elasticities.csv")
        whole = base.loc[base.dimension.eq("all")].sort_values("group")
        cols = ["group_name", "food_expenditure_elasticity", "income_elasticity", "income_intensive", "income_extensive", "hicksian_own_fixed_set_average", "total_own_price_response"]
        txt += [f"\n===== {k}类：全样本弹性（相关参与主结果） =====\n", formatting(whole[cols]), "\n"]
        md += [f"\n## {k}类主结果\n", whole[cols].round(4).to_markdown(index=False), "\n"]
        sections = [
            ("第二阶段模型比较：只可在同一分类内比较", folder / "model_comparison.csv"),
            ("第一阶段收入弹性及真实p值", OUT / f"stata_stage1_{k}" / "income_elasticity_tests.csv"),
            ("收入函数形状与家庭预算响应检验p值", OUT / f"budget_shape_{k}" / "tests.csv"),
            ("二次/线性预算函数工作似然比较", OUT / f"budget_shape_{k}" / "modelcomparison.csv"),
            ("原标准guard到最终扩大guard的敏感性", folder / "maidads_expanded_guard_comparison.csv"),
            ("固定参与集合结构弹性", folder / "conditional_fixed_set_elasticities.csv"),
            ("固定参与集合Marshallian全矩阵", folder / "conditional_marshallian_matrix.csv"),
            ("固定参与集合Hicksian全矩阵", folder / "conditional_hicksian_matrix.csv"),
            ("含参与和预算变化的total price response全矩阵", folder / "unconditional_total_price_response_matrix.csv"),
            ("省份收入增长预测及弹性", folder / "province_income_growth_predictions.csv"),
            ("家庭形态收入增长预测及弹性", folder / "family_income_growth_elasticities.csv"),
            ("个体弹性分布（非总体抽样分布）", folder / "household_elasticity_distribution.csv"),
            ("相关参与参数", OUT / f"stata_stage1_{k}" / "correlated_hurdle_loadings.csv"),
        ]
        for heading, path in sections:
            txt += [f"\n--- {k}类：{heading} ---\n", formatting(pd.read_csv(path)), "\n"]
        sensitivities = pd.read_csv(folder / "income_growth_scenarios.csv")
        sensitivities = sensitivities.loc[sensitivities.dimension.eq("all")&sensitivities.growth_multiplier.eq(1)]
        txt += [f"\n--- {k}类：敏感性比较 ---\n", formatting(sensitivities[["specification"]+cols]), "\n"]
        md += [f"\n### {k}类敏感性\n", sensitivities[["specification"]+cols].round(4).to_markdown(index=False), "\n"]
        for filename in ("maidads_fit.json", "maidads_working_domain_audit.json", "hurdle_integration_audit.json", "forecast_derivative_validation.json"):
            txt += [f"\n--- {k}类：{filename} ---\n", (folder / filename).read_text(), "\n"]
        figures(k)
    for filename in ("data_validation.csv", "sample_flow.csv", "income_outlier_audit.csv", "participation_independence_summary.csv"):
        txt += [f"\n===== {filename} =====\n", formatting(pd.read_csv(OUT / filename)), "\n"]
    txt += ["\n===== 原始 MAIDADS 与既有研究 =====\n",
            "Preckel, Cranfield, Hertel (2010): https://doi.org/10.1080/00036840701591361\n",
            "Britz (2022) 已有含人口特征的 MAIDADS，不能将人口特征泛称首次创新: https://oaj.fupress.net/index.php/bae/article/view/10488\n",
            "方法推导、零消费工作假设、完整核验和文献见 documentation/METHOD_ZERO_AND_INCOME.md。\n"]
    (OUT / "完整主要结果.txt").write_text("\n".join(txt), encoding="utf-8")
    (ROOT / "documentation" / "RESULTS_SUMMARY.md").write_text("\n".join(md).rstrip()+"\n", encoding="utf-8")
    print("Report and figures created", flush=True)


if __name__ == "__main__":
    main()
