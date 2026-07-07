"""
02_build_deltapi.py — 构建预期净收益差 Δπ = E[π_soy] − E[π_corn]（元/亩，/100 标度）

口径（朴素预期，播种决策于 t 年春，信息集为 t−1 年实现值 + t 年已公布补贴政策）：
  E[π_c,it] = p̂_c,ct−1 × ŷ_c,i − ĉ_c,ct−1 + sub_c,ct
  - p̂：县×年销售价格中位数（t−1 年），县内样本<5 时回退省中位数
  - ŷ：户潜在单产 = 经验贝叶斯收缩（户 t−1 前历史均值向县均值收缩，k=2）；
       无历史（如从未种大豆）→ 县×(≤t−1) 年中位数
  - ĉ：县×年×作物 亩均现金成本中位数（t−1 年），同样回退省级
  - sub：分县分年补贴标准（元/亩），由户报补贴反推：
       2024 有分作物户报 → 中位数(户报补贴/该作物面积)
       2021–2023 仅合并生产者补贴 → 对 (area_corn, area_soy) 无截距稳健回归
输出：output/panel_analysis.csv, output/params/price_cost_sub_tables.csv, output/logs/phase2_report.md
"""
import pandas as pd
import numpy as np
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "output")
os.makedirs(f"{OUT}/params", exist_ok=True)

panel = pd.read_csv(f"{OUT}/panel_hh.csv")
crop = pd.read_csv(f"{OUT}/panel_crop_long.csv")
cs = crop[crop["crop"].isin(["corn", "soy"])].copy()

# ---------- 1. 县×年 价格/成本 中位数（含省级回退） ----------
def county_year_median(df, val, min_n=5):
    g = df.groupby(["county_name", "year", "crop"])[val].agg(["median", "count"]).reset_index()
    prov = df.groupby(["year", "crop"])[val].median().rename("prov").reset_index()
    g = g.merge(prov, on=["year", "crop"], how="left")
    g[val] = np.where(g["count"] >= min_n, g["median"], g["prov"])
    g[val] = g[val].fillna(g["prov"])
    return g[["county_name", "year", "crop", val]]

# 补齐所有 县×年×作物 组合（双城无大豆行 → 直接省级）
counties = sorted(cs["county_name"].unique())
years = sorted(cs["year"].unique())
full = pd.MultiIndex.from_product([counties, years, ["corn", "soy"]],
                                  names=["county_name", "year", "crop"]).to_frame(index=False)
ptab = full.merge(county_year_median(cs, "price"), on=["county_name", "year", "crop"], how="left")
ctab = full.merge(county_year_median(cs, "cost_mu"), on=["county_name", "year", "crop"], how="left")
prov_p = cs.groupby(["year", "crop"])["price"].median().rename("pv").reset_index()
prov_c = cs.groupby(["year", "crop"])["cost_mu"].median().rename("cv").reset_index()
ptab = ptab.merge(prov_p, on=["year", "crop"]).assign(price=lambda d: d["price"].fillna(d["pv"])).drop(columns="pv")
ctab = ctab.merge(prov_c, on=["year", "crop"]).assign(cost_mu=lambda d: d["cost_mu"].fillna(d["cv"])).drop(columns="cv")

# ---------- 2. 户潜在单产（收缩估计，只用 t−1 前信息） ----------
K = 2.0
cs_y = cs.dropna(subset=["yield"])[["hh_id", "county_name", "year", "crop", "yield"]]

def shrunk_yield(hh_id, county, crop_c, t):
    hist = cs_y[(cs_y["hh_id"] == hh_id) & (cs_y["crop"] == crop_c) & (cs_y["year"] < t)]
    cty = cs_y[(cs_y["county_name"] == county) & (cs_y["crop"] == crop_c) & (cs_y["year"] < t)]["yield"]
    if len(cty) < 5:
        cty = cs_y[(cs_y["crop"] == crop_c) & (cs_y["year"] < t)]["yield"]
    prior = cty.median() if len(cty) else np.nan
    if len(hist) == 0:
        return prior
    return (hist["yield"].sum() + K * prior) / (len(hist) + K)

# ---------- 3. 补贴标准反推 ----------
sub_rows = []
for (cty, yr), g in panel.groupby(["county_name", "year"]):
    if yr == 2024:
        gc = g[(g["area_corn"] > 0) & (g["sub_corn_rep"] > 0)]
        gs = g[(g["area_soy"] > 0) & (g["sub_soy_rep"] > 0)]
        rc = (gc["sub_corn_rep"] / gc["area_corn"]).median() if len(gc) >= 3 else np.nan
        rs = (gs["sub_soy_rep"] / gs["area_soy"]).median() if len(gs) >= 3 else np.nan
        n_c, n_s = len(gc), len(gs)
    else:
        gg = g[(g["sub_prod_rep"] > 0) & (g["B"] > 0)].copy()
        n_c = int((gg["area_corn"] > 0).sum()); n_s = int((gg["area_soy"] > 0).sum())
        # 纯玉米户/纯大豆户直接给率；混合户信息并入回归
        rc = rs = np.nan
        if len(gg) >= 5:
            X = gg[["area_corn", "area_soy"]].values
            y = gg["sub_prod_rep"].values
            # 稳健：先用纯种户中位数，再最小二乘兜底
            pure_c = gg[(gg["area_soy"] == 0) & (gg["area_corn"] > 0)]
            pure_s = gg[(gg["area_corn"] == 0) & (gg["area_soy"] > 0)]
            rc = (pure_c["sub_prod_rep"] / pure_c["area_corn"]).median() if len(pure_c) >= 3 else np.nan
            rs = (pure_s["sub_prod_rep"] / pure_s["area_soy"]).median() if len(pure_s) >= 3 else np.nan
            if np.isnan(rc) or np.isnan(rs):
                try:
                    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
                    if np.isnan(rc):
                        rc = beta[0]
                    if np.isnan(rs):
                        rs = beta[1]
                except Exception:
                    pass
    sub_rows.append({"county_name": cty, "year": yr, "sub_corn": rc, "sub_soy": rs,
                     "n_corn": n_c, "n_soy": n_s})
sub_derived = pd.DataFrame(sub_rows)  # 户报反推费率，仅作交叉验证
sub_derived.loc[sub_derived["n_soy"] < 3, "sub_soy"] = np.nan

# 主口径：官方省级统一标准（元/亩）。来源：黑龙江省玉米大豆生产者补贴实施方案
# 2021 玉米68/大豆248；2022 玉米28/大豆248；2023 玉米约15/大豆350；2024 玉米约20/大豆350
SUB_OFFICIAL = {2021: (68, 248), 2022: (28, 248), 2023: (15, 350), 2024: (20, 350)}
sub = pd.MultiIndex.from_product([counties, list(SUB_OFFICIAL)],
                                 names=["county_name", "year"]).to_frame(index=False)
sub["sub_corn"] = sub["year"].map(lambda y: SUB_OFFICIAL[y][0])
sub["sub_soy"] = sub["year"].map(lambda y: SUB_OFFICIAL[y][1])

# ---------- 4. 组装 Δπ ----------
def get(tab, val, cty, yr, cr):
    r = tab[(tab["county_name"] == cty) & (tab["year"] == yr) & (tab["crop"] == cr)]
    return r[val].iloc[0] if len(r) else np.nan

rows = []
for _, r in panel.iterrows():
    cty, yr, hh = r["county_name"], int(r["year"]), r["hh_id"]
    tm1 = yr - 1
    if tm1 not in years:
        rows.append({}); continue
    p_c = get(ptab, "price", cty, tm1, "corn"); p_s = get(ptab, "price", cty, tm1, "soy")
    c_c = get(ctab, "cost_mu", cty, tm1, "corn"); c_s = get(ctab, "cost_mu", cty, tm1, "soy")
    y_c = shrunk_yield(hh, cty, "corn", yr); y_s = shrunk_yield(hh, cty, "soy", yr)
    srow = sub[(sub["county_name"] == cty) & (sub["year"] == yr)]
    s_c = srow["sub_corn"].iloc[0] if len(srow) else np.nan
    s_s = srow["sub_soy"].iloc[0] if len(srow) else np.nan
    pi_c_mkt = p_c * y_c - c_c
    pi_s_mkt = p_s * y_s - c_s
    rows.append({"pi_corn_mkt": pi_c_mkt, "pi_soy_mkt": pi_s_mkt,
                 "dpi_mkt": pi_s_mkt - pi_c_mkt, "dpi_sub": s_s - s_c,
                 "sub_corn_std": s_c, "sub_soy_std": s_s,
                 "dpi": (pi_s_mkt - pi_c_mkt) + (s_s - s_c)})
dp = pd.DataFrame(rows, index=panel.index)
panel = pd.concat([panel, dp], axis=1)
panel["dpi100"] = panel["dpi"] / 100.0
panel["dpi_mkt100"] = panel["dpi_mkt"] / 100.0
panel["dpi_sub100"] = panel["dpi_sub"] / 100.0

panel.to_csv(f"{OUT}/panel_analysis.csv", index=False)
ptab.to_csv(f"{OUT}/params/price_table.csv", index=False)
ctab.to_csv(f"{OUT}/params/cost_table.csv", index=False)
sub.to_csv(f"{OUT}/params/subsidy_table.csv", index=False)
sub_derived.to_csv(f"{OUT}/params/subsidy_derived_check.csv", index=False)

# ---------- 报告 ----------
rep = ["# Phase 2 Δπ 构建报告\n"]
rep.append("## 补贴标准（官方省级统一口径，元/亩）\n")
rep.append(sub.drop_duplicates(["year"])[["year", "sub_corn", "sub_soy"]].to_string(index=False))
rep.append("\n\n## 户报补贴反推费率（交叉验证）\n")
rep.append(sub_derived.round(1).to_string(index=False))
rep.append("\n\n## Δπ 分布（估计样本 2022–2024，有滞后项）\n")
est = panel[panel["plant_soy_lag"].notna()]
d = est[["dpi", "dpi_mkt", "dpi_sub"]].describe().round(1)
rep.append(d.to_string())
rep.append("\n\n## 分县分年 Δπ 中位数\n")
g = est.groupby(["county_name", "year"])[["dpi", "dpi_mkt", "dpi_sub"]].median().round(0)
rep.append(g.to_string())
with open(f"{OUT}/logs/phase2_report.md", "w") as f:
    f.write("\n".join(rep))
print(sub.round(1).to_string(index=False))
print(g.to_string())
print("est sample:", len(est), "dpi missing:", est["dpi"].isna().sum())
