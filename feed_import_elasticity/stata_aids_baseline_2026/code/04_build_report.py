#!/usr/bin/env python3
import csv
import math
import os
import sys


PROJECT = sys.argv[1] if len(sys.argv) > 1 else "/root/data/Paper/饲料进口弹性/stata_aids_baseline_2026"
OUT = os.path.join(PROJECT, "output")
GOODS = ["corn", "sorghum", "cassava", "oats", "barley"]
CN = {"corn": "玉米", "sorghum": "高粱", "cassava": "木薯干", "oats": "燕麦", "barley": "大麦"}


def rows(name):
    with open(os.path.join(OUT, name), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return math.nan


def fmt(x, digits=3):
    x = num(x)
    if math.isnan(x):
        return ""
    if x == 0:
        return "0"
    if abs(x) < 0.001:
        return f"{x:.2e}"
    return f"{x:.{digits}f}"


def integer(x):
    x = num(x)
    return 0 if math.isnan(x) else int(x)


def sort_number(x):
    x = num(x)
    return -math.inf if math.isnan(x) else x


def pformat(x):
    x = num(x)
    if math.isnan(x):
        return ""
    if x < 1e-16:
        return "<1e-16"
    return fmt(x)


raw = rows("raw_transaction_descriptive_by_product.csv")
hs = rows("raw_hs_code_descriptive.csv")
cells = rows("product_cell_descriptive.csv")
expdiag = rows("province_quarter_expenditure_diagnostics.csv")
raw_anom = rows("raw_transaction_anomalies.csv")
cell_anom = rows("province_quarter_product_anomalies.csv")
model = rows("basic_aids_model_diagnostics.csv")[0]
tests = rows("basic_aids_joint_tests.csv")
params = rows("basic_aids_parameters.csv")
elastic = rows("basic_aids_elasticities_complete.csv")

total_transactions = sum(integer(r["n_transactions"]) for r in raw)
invalid_qty = sum(integer(r["n_invalid_qty"]) for r in raw)
mild_raw = sum(integer(r["n_mild_price_outlier"]) for r in raw)
severe_raw = sum(integer(r["n_severe_price_outlier"]) for r in raw)
seed_rows = sum(integer(r["n_seed_records"]) for r in hs)
seed_value = sum(num(r["total_value_usd"]) for r in hs if integer(r["n_seed_records"]) > 0)
total_value = sum(num(r["total_value_usd"]) for r in raw)
mild_cells = sum(integer(r["cell_price_outlier_mild"]) for r in cell_anom)
severe_cells = sum(integer(r["cell_price_outlier_severe"]) for r in cell_anom)
mild_exp = sum(integer(r["expenditure_outlier_mild"]) for r in expdiag)
severe_exp = sum(integer(r["expenditure_outlier_severe"]) for r in expdiag)

emap = {(r["elasticity_type"], r["demand_product"], r["price_product"]): r for r in elastic}
eta = {g: num(emap[("expenditure", g, "")]["estimate"]) for g in GOODS}
shares = {g: num(emap[("expenditure", g, "")]["reference_share"]) for g in GOODS}

weighted_eta = sum(shares[g] * eta[g] for g in GOODS)
marshallian_gap = 0.0
hicksian_gap = 0.0
for g in GOODS:
    sm = sum(num(emap[("marshallian", g, p)]["estimate"]) for p in GOODS)
    sh = sum(num(emap[("hicksian", g, p)]["estimate"]) for p in GOODS)
    marshallian_gap = max(marshallian_gap, abs(sm + eta[g]))
    hicksian_gap = max(hicksian_gap, abs(sh))

with open(os.path.join(OUT, "elasticity_identity_audit.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["identity", "value", "target", "absolute_gap"])
    w.writerow(["share_weighted_expenditure_elasticity", weighted_eta, 1, abs(weighted_eta - 1)])
    w.writerow(["max_abs_marshallian_row_sum_plus_expenditure", marshallian_gap, 0, marshallian_gap])
    w.writerow(["max_abs_hicksian_row_sum", hicksian_gap, 0, hicksian_gap])


def matrix_table(kind):
    lines = ["| 需求\\价格 | " + " | ".join(CN[g] for g in GOODS) + " |",
             "|---|" + "---:|" * len(GOODS)]
    for g in GOODS:
        vals = []
        for p in GOODS:
            r = emap[(kind, g, p)]
            vals.append(f"{fmt(r['estimate'])}{r['significance']}<br>({fmt(r['std_error'])}; p={pformat(r['p_value'])})")
        lines.append(f"| {CN[g]} | " + " | ".join(vals) + " |")
    return "\n".join(lines)


lines = []
lines.append("# 原始数据诊断与 Stata 基础 AIDS 结果\n")
lines.append("本报告是一个全新基线，不读取旧的 panel、SY、控制函数、质量调整价格或弹性结果。")
lines.append("星号检验 H0:弹性=0：*** p<0.01，** p<0.05，* p<0.10。括号内为省级聚类标准误与 p 值。\n")

lines.append("## 1. 原始数据与样本\n")
lines.append(f"- 原始期间：2017–2023；精确 HS8 匹配后 {total_transactions:,} 条进口记录。")
lines.append(f"- 五类合计金额 {total_value/1e9:.3f} 十亿美元；省份×季度正总支出样本 {int(num(model['N']))} 个，{int(num(model['n_clusters']))} 个省级聚类。")
lines.append("- 份额为 0 的产品价格无法由当地交易识别，仅使用同产品同季度正贸易单元的中位数填补；没有缩尾。\n")

lines.append("| 产品 | 原始记录 | 金额(十亿美元) | 中位单价 | p99单价 | 数量无效 | 温和IQR异常 | 严重IQR异常 |")
lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
for r in raw:
    g = r["product"]
    lines.append(f"| {CN[g]} | {integer(r['n_transactions'])} | {num(r['total_value_usd'])/1e9:.3f} | {fmt(r['median_unit_value'])} | {fmt(r['p99_unit_value'])} | {integer(r['n_invalid_qty'])} | {integer(r['n_mild_price_outlier'])} | {integer(r['n_severe_price_outlier'])} |")

lines.append("\n| 产品 | 零份额率 | 平均份额 | 份额中位数 | 正贸易单元 | 价格填补单元 |")
lines.append("|---|---:|---:|---:|---:|---:|")
for r in cells:
    g = r["product"]
    lines.append(f"| {CN[g]} | {fmt(100*num(r['zero_share_rate']),1)}% | {fmt(r['mean_share'])} | {fmt(r['median_share'])} | {integer(r['n_positive_share'])} | {integer(r['n_price_imputed'])} |")

lines.append("\n## 2. 潜在异常值\n")
lines.append(f"- 原始交易层：{invalid_qty} 条数量缺失/非正；对数单价 1.5×IQR 标记 {mild_raw} 条，3×IQR 严重标记 {severe_raw} 条。")
lines.append(f"- HS 口径：{seed_rows} 条“种用”记录，金额 {seed_value/1e6:.3f} 百万美元，占五类总金额 {100*seed_value/total_value:.3f}%。其经济用途与饲料不一致，是后续清洗的首要候选。")
lines.append(f"- 省季度产品层：1.5×IQR 价格异常 {mild_cells} 个，3×IQR 严重异常 {severe_cells} 个。")
lines.append(f"- 省季度总支出层：对数总支出 1.5×IQR 异常 {mild_exp} 个，3×IQR 严重异常 {severe_exp} 个。\n")

lines.append("最高的原始单价记录：\n")
lines.append("| 日期 | 省份 | 产品 | HS8 | 商品 | 金额 | 数量kg | 美元/kg | 种用 |")
lines.append("|---|---|---|---|---|---:|---:|---:|---:|")
for r in sorted(raw_anom, key=lambda x: sort_number(x["unit_value"]), reverse=True)[:12]:
    lines.append(f"| {r['date']} | {r['province']} | {CN[r['product']]} | {r['hs8']} | {r['product_name']} | {fmt(r['value_usd'],0)} | {fmt(r['qty_kg'],0)} | {fmt(r['unit_value'])} | {integer(r['seed_code'])} |")

lines.append("\n最低的省季度总支出单元：\n")
lines.append("| 省份 | 年 | 季度 | 总支出(美元) | 温和异常 | 严重异常 |")
lines.append("|---|---:|---:|---:|---:|---:|")
for r in sorted(expdiag, key=lambda x: num(x["total_expenditure_usd"]))[:10]:
    lines.append(f"| {r['province']} | {r['year']} | {r['quarter']} | {fmt(r['total_expenditure_usd'],0)} | {integer(r['expenditure_outlier_mild'])} | {integer(r['expenditure_outlier_severe'])} |")

lines.append("\n## 3. 基础 AIDS 估计\n")
lines.append("模型是 exact nonlinear AIDS：固定 translog 价格指数截距为 0，对数价格和对数总支出在样本均值中心化，并在估计中直接施加加总、一次齐次与对称约束。不包含省/季度固定效应或其他控制项。")
lines.append(f"模型收敛={model['converged']}，log likelihood={fmt(model['ll'])}。联合检验：支出项全为 0，p={fmt(tests[0]['p_value'])}；价格项全为 0，p={fmt(tests[1]['p_value'])}。\n")

lines.append("### 支出弹性\n")
lines.append("| 产品 | 参考份额 | 弹性 | SE | p(弹性=0) | p(弹性=1) | 95% CI |")
lines.append("|---|---:|---:|---:|---:|---:|---:|")
for g in GOODS:
    r = emap[("expenditure", g, "")]
    lines.append(f"| {CN[g]} | {fmt(r['reference_share'])} | {fmt(r['estimate'])}{r['significance']} | {fmt(r['std_error'])} | {pformat(r['p_value'])} | {pformat(r['p_value_vs_one'])}{r['significance_vs_one']} | [{fmt(r['ci_low'])}, {fmt(r['ci_high'])}] |")

lines.append("\n### Marshallian 非补偿价格弹性\n")
lines.append(matrix_table("marshallian"))
lines.append("\n### Hicksian 补偿价格弹性\n")
lines.append(matrix_table("hicksian"))

lines.append("\n## 4. 约束与解读核验\n")
lines.append(f"- 份额加权支出弹性={weighted_eta:.9f}（目标 1）。")
lines.append(f"- max|Marshallian 行和+支出弹性|={marshallian_gap:.2e}。")
lines.append(f"- max|Hicksian 行和|={hicksian_gap:.2e}。")
lines.append("- 这些是五类进口总支出内的条件需求弹性，不是中国总进口的无条件弹性。")
lines.append("- 当前结果刻意保留“种用”、极小贸易单元和极端单价，因此只应视为未清洗基线，不宜直接作为论文主结果。")

with open(os.path.join(PROJECT, "BASELINE_AIDS_RESULTS.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(os.path.join(PROJECT, "BASELINE_AIDS_RESULTS.md"))
