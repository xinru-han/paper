#!/usr/bin/env python3
import csv
import math
import os
import sys


PROJECT = sys.argv[1] if len(sys.argv) > 1 else "/root/data/Paper/饲料进口弹性/stata_aids_baseline_2026"
OUT = os.path.join(PROJECT, "output")
GOODS = ["corn", "sorghum", "cassava", "oats", "barley"]
CN = {"corn": "玉米", "sorghum": "高粱", "cassava": "木薯干", "oats": "燕麦", "barley": "大麦"}
MODELS = ["quaids", "sy_aids", "sy_quaids"]
MNAME = {"aids": "AIDS", "quaids": "QUAIDS", "sy_aids": "SY-AIDS", "sy_quaids": "SY-QUAIDS"}


def read(name):
    with open(os.path.join(OUT, name), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def number(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return math.nan


def fmt(x, digits=3):
    x = number(x)
    if math.isnan(x):
        return ""
    if abs(x) < 1e-16:
        return "0"
    if abs(x) < 0.001:
        return f"{x:.2e}"
    return f"{x:.{digits}f}"


def pformat(x):
    x = number(x)
    if math.isnan(x):
        return ""
    if x < 1e-16:
        return "<1e-16"
    return fmt(x)


extended = read("extended_elasticities_complete.csv")
base = read("basic_aids_elasticities_complete.csv")
diagnostics = read("extended_model_diagnostics.csv")
tests = read("extended_model_joint_tests.csv")
selection = read("sy_selection_reference.csv")
base_diagnostic = read("basic_aids_model_diagnostics.csv")[0]
base_tests = read("basic_aids_joint_tests.csv")

all_rows = []
for r in base:
    item = dict(r)
    item["model"] = "aids"
    item["margin"] = "latent"
    all_rows.append(item)
all_rows.extend(extended)

fields = ["model", "margin", "elasticity_type", "demand_product", "price_product",
          "reference_share", "estimate", "std_error", "z_value", "p_value",
          "ci_low", "ci_high", "significance", "p_value_vs_one", "significance_vs_one"]
with open(os.path.join(OUT, "all_models_elasticities_complete.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(all_rows)

emap = {(r["model"], r["elasticity_type"], r["demand_product"], r["price_product"]): r for r in all_rows}
tmap = {(r["model"], r["test"]): r for r in tests}
dmap = {r["model"]: r for r in diagnostics}
base_n = number(base_diagnostic["N"])
base_ll = number(base_diagnostic["ll"])
dmap["aids"] = {
    "model": "aids", "N": base_diagnostic["N"], "n_clusters": base_diagnostic["n_clusters"],
    "n_parameters": "18", "converged": base_diagnostic["converged"], "ll": base_diagnostic["ll"],
    "aic": str(-2*base_ll + 2*18), "bic": str(-2*base_ll + math.log(base_n)*18),
}
tmap[("aids", "all_price_terms_zero")] = {
    "p_value": next(r["p_value"] for r in base_tests if r["test"] == "all_price_terms_zero")
}


def cell(r):
    stars = r.get("significance", "")
    return f"{fmt(r['estimate'])}{stars}<br>({fmt(r['std_error'])}; p={pformat(r['p_value'])})"


def matrix(model, kind):
    ans = ["| 需求\\价格 | " + " | ".join(CN[g] for g in GOODS) + " |",
           "|---|" + "---:|" * 5]
    for g in GOODS:
        ans.append("| " + CN[g] + " | " + " | ".join(cell(emap[(model, kind, g, p)]) for p in GOODS) + " |")
    return "\n".join(ans)


def valid_shares(model):
    vals = [number(emap[(model, "expenditure", g, "")]["reference_share"]) for g in GOODS]
    return all(0 < x < 1 for x in vals)


with open(os.path.join(OUT, "model_reference_regularity.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["model", "product", "reference_share", "share_in_unit_interval"])
    for model in ["aids"] + MODELS:
        for g in GOODS:
            share = number(emap[(model, "expenditure", g, "")]["reference_share"])
            w.writerow([model, g, share, int(0 < share < 1)])

with open(os.path.join(OUT, "extended_elasticity_identity_audit.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["model", "weighted_expenditure_gap", "max_marshallian_homogeneity_gap", "max_hicksian_adding_up_gap"])
    for model in ["aids"] + MODELS:
        shares = {g: number(emap[(model, "expenditure", g, "")]["reference_share"]) for g in GOODS}
        eta = {g: number(emap[(model, "expenditure", g, "")]["estimate"]) for g in GOODS}
        weighted_gap = abs(sum(shares[g]*eta[g] for g in GOODS) - 1)
        mgap = max(abs(sum(number(emap[(model, "marshallian", g, p)]["estimate"]) for p in GOODS) + eta[g]) for g in GOODS)
        hgap = max(abs(sum(number(emap[(model, "hicksian", g, p)]["estimate"]) for p in GOODS)) for g in GOODS)
        w.writerow([model, weighted_gap, mgap, hgap])


lines = []
lines.append("# Stata SY-AIDS、QUAIDS 与 SY-QUAIDS 完整弹性\n")
lines.append("样本、价格填补和异常值处理与基础 AIDS 完全一致。SY 参与方程使用总支出和五类价格，五个观测份额方程同时估计，每类均有独立的 SY 密度修正项。")
lines.append("弹性是在中心化样本均值处的潜在条件弹性。星号检验 H0:弹性=0：*** p<0.01，** p<0.05，* p<0.10；括号内为省级聚类 SE 和 p 值。SY 第二阶段的推断条件于第一阶段估计值。\n")

lines.append("## 参与率与模型检验\n")
lines.append("| 产品 | 样本参与率 | 均值点预测参与率 |")
lines.append("|---|---:|---:|")
for r in selection:
    lines.append(f"| {CN[r['product']]} | {100*number(r['participation_rate']):.1f}% | {100*number(r['phi_ref']):.1f}% |")

lines.append("\n| 模型 | 方程数 | 参考份额有效 | 价格项 p | 二次项 p | SY项 p | BIC |")
lines.append("|---|---:|---:|---:|---:|---:|---:|")
for model in ["aids"] + MODELS:
    pricep = tmap[(model, "all_price_terms_zero")]["p_value"]
    quad = tmap.get((model, "all_quadratic_terms_zero"), {}).get("p_value", "")
    sy = tmap.get((model, "all_SY_density_terms_zero"), {}).get("p_value", "")
    neq = 5 if model.startswith("sy_") else 4
    lines.append(f"| {MNAME[model]} | {neq} | {'是' if valid_shares(model) else '否'} | {pformat(pricep)} | {pformat(quad)} | {pformat(sy)} | {fmt(dmap[model]['bic'])} |")
lines.append("\n注：BIC 只可在相同方程数内比较，即 AIDS vs QUAIDS、SY-AIDS vs SY-QUAIDS，不应将四方程和五方程 BIC 直接比较。\n")

lines.append("## 跨模型核心比较\n")
lines.append("| 模型 | 产品 | 参考份额 | 支出弹性 | Marshallian自价格 | Hicksian自价格 |")
lines.append("|---|---|---:|---:|---:|---:|")
for model in ["aids"] + MODELS:
    for g in GOODS:
        ex = emap[(model, "expenditure", g, "")]
        ma = emap[(model, "marshallian", g, g)]
        hi = emap[(model, "hicksian", g, g)]
        lines.append(f"| {MNAME[model]} | {CN[g]} | {fmt(ex['reference_share'])} | {fmt(ex['estimate'])}{ex.get('significance','')} | {fmt(ma['estimate'])}{ma.get('significance','')} | {fmt(hi['estimate'])}{hi.get('significance','')} |")

for model in MODELS:
    lines.append(f"\n## {MNAME[model]}\n")
    lines.append("### 支出弹性\n")
    lines.append("| 产品 | 参考份额 | 弹性 | SE | p(弹性=0) | p(弹性=1) | 95% CI |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for g in GOODS:
        r = emap[(model, "expenditure", g, "")]
        unitstar = r.get("significance_vs_one", "")
        lines.append(f"| {CN[g]} | {fmt(r['reference_share'])} | {fmt(r['estimate'])}{r.get('significance','')} | {fmt(r['std_error'])} | {pformat(r['p_value'])} | {pformat(r['p_value_vs_one'])}{unitstar} | [{fmt(r['ci_low'])}, {fmt(r['ci_high'])}] |")
    lines.append("\n### Marshallian 非补偿价格弹性\n")
    lines.append(matrix(model, "marshallian"))
    lines.append("\n### Hicksian 补偿价格弹性\n")
    lines.append(matrix(model, "hicksian"))

lines.append("\n## 结果判断\n")
lines.append("- QUAIDS 的五个参考份额均有效，但二次项联合 p=0.116，相比 AIDS 的非线性证据较弱；BIC 仅小幅降低。")
lines.append("- SY-AIDS 的 SY 项联合显著，但大麦潜在参考份额为负，木薯弹性方差很大；该规格不满足参考点正则性，不应作为主结果。")
lines.append("- SY-QUAIDS 的参考份额全部为正，二次项和 SY 项均高度显著，五个 Marshallian 自价格弹性均为负且显著；在要求同时处理零份额和 Engel 非线性时，它是三个扩展模型中唯一通过这些基本检查的规格。")
lines.append("- 所有结果仍是保留种用产品、极小贸易单元和极端单价的未清洗基线。")

with open(os.path.join(PROJECT, "EXTENDED_MODELS_RESULTS.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(os.path.join(PROJECT, "EXTENDED_MODELS_RESULTS.md"))
