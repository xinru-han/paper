"""
02_build_deltapi.py — 预期净收益差 Δπ（审阅修订版）

三个版本（P2）：
  dpi_roll  滚动更新 ŷ（原版，行为口径：含干中学信息，预定但非严格外生）
  dpi_base  基期锁定 ŷ（主规格：ŷ 只用2021年信息构造并全程冻结，时间变异
            纯来自县×年价格/成本/补贴 → shift-share 结构）
  dpi_loo   leave-one-out ŷ（县×(<t)年中位数剔除本户，切断户级不可观测渠道）
另构造（P1/P8/P10）：
  Suit 三口径（仅用2021信息）；豆粮价格比；CPI平减（2024=100）；
  sub_lag 预期口径；村报玉米补贴的村级补贴差 dpi_sub_vill；价格单元底层n表
输出：output/panel_analysis.csv, output/params/*, output/logs/phase2_report.md
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
counties = sorted(cs["county_name"].unique())
years = sorted(cs["year"].unique())

# CPI 平减因子（国家统计局CPI同比：2022 +2.0%, 2023 +0.2%, 2024 +0.2%；2024=1）
DEFL = {2021: 1.020 * 1.002 * 1.002, 2022: 1.002 * 1.002, 2023: 1.002, 2024: 1.0}

# ---------- 1. 县×年 价格/成本 中位数（含底层n与省级回退） ----------
def county_year_median(df, val, min_n=5):
    g = df.groupby(["county_name", "year", "crop"])[val].agg(["median", "count"]).reset_index()
    prov = df.groupby(["year", "crop"])[val].median().rename("prov").reset_index()
    g = g.merge(prov, on=["year", "crop"], how="left")
    g["pooled"] = (g["count"] < min_n).astype(int)
    g[val] = np.where(g["count"] >= min_n, g["median"], g["prov"])
    g[val] = g[val].fillna(g["prov"])
    return g[["county_name", "year", "crop", val, "count", "pooled"]]

full = pd.MultiIndex.from_product([counties, years, ["corn", "soy"]],
                                  names=["county_name", "year", "crop"]).to_frame(index=False)
ptab = full.merge(county_year_median(cs, "price"), on=["county_name", "year", "crop"], how="left")
ctab = full.merge(county_year_median(cs, "cost_mu"), on=["county_name", "year", "crop"], how="left")
for tab, val in [(ptab, "price"), (ctab, "cost_mu")]:
    prov = cs.groupby(["year", "crop"])[val].median().rename("pv").reset_index()
    tab_m = tab.merge(prov, on=["year", "crop"], how="left")
    tab[val] = tab_m[val].fillna(tab_m["pv"])
    tab["count"] = tab["count"].fillna(0)
    tab["pooled"] = tab["pooled"].fillna(1)
ptab.to_csv(f"{OUT}/params/price_table.csv", index=False)
ctab.to_csv(f"{OUT}/params/cost_table.csv", index=False)
# 附录：价格单元底层观测数（P8）
ptab.pivot_table(index=["county_name", "crop"], columns="year", values="count")\
    .to_csv(f"{OUT}/tables/price_cell_n.csv")

# ---------- 2. 补贴标准 ----------
SUB_OFFICIAL = {2021: (68, 248), 2022: (28, 248), 2023: (15, 350), 2024: (20, 350)}
sub = pd.DataFrame([{"year": y, "sub_corn": v[0], "sub_soy": v[1]} for y, v in SUB_OFFICIAL.items()])
sub.to_csv(f"{OUT}/params/subsidy_table.csv", index=False)

# ---------- 3. 三版潜在单产 ----------
K = 2.0
cs_y = cs.dropna(subset=["yield"])[["hh_id", "county_name", "year", "crop", "yield"]]
cty_yr_med = cs_y.groupby(["county_name", "year", "crop"])["yield"].median()
prov_yr_med = cs_y.groupby(["year", "crop"])["yield"].median()

def cty_prior(cty, crop_c, upto):
    sel = cs_y[(cs_y["county_name"] == cty) & (cs_y["crop"] == crop_c) & (cs_y["year"] <= upto)]
    if len(sel) >= 5:
        return sel["yield"].median()
    sel = cs_y[(cs_y["crop"] == crop_c) & (cs_y["year"] <= upto)]
    return sel["yield"].median() if len(sel) else np.nan

def ey_roll(hh, cty, crop_c, t):
    hist = cs_y[(cs_y["hh_id"] == hh) & (cs_y["crop"] == crop_c) & (cs_y["year"] < t)]
    prior = cty_prior(cty, crop_c, t - 1)
    if len(hist) == 0:
        return prior
    return (hist["yield"].sum() + K * prior) / (len(hist) + K)

BASE_YR = 2021
base_hh = cs_y[cs_y["year"] == BASE_YR].groupby(["hh_id", "crop"])["yield"].mean()

def ey_base(hh, cty, crop_c):
    prior = cty_prior(cty, crop_c, BASE_YR)
    v = base_hh.get((hh, crop_c), np.nan)
    if pd.isna(v):
        return prior
    return (v + K * prior) / (1 + K)

def ey_loo(hh, cty, crop_c, t):
    sel = cs_y[(cs_y["county_name"] == cty) & (cs_y["crop"] == crop_c)
               & (cs_y["year"] < t) & (cs_y["hh_id"] != hh)]
    if len(sel) >= 5:
        return sel["yield"].median()
    sel = cs_y[(cs_y["crop"] == crop_c) & (cs_y["year"] < t) & (cs_y["hh_id"] != hh)]
    return sel["yield"].median() if len(sel) else np.nan

# ---------- 4. Suit 三口径（只用2021信息，P1-1） ----------
# (a) 村2021大豆面积份额
v21 = panel[panel["year"] == 2021].groupby("village").apply(
    lambda d: d["area_soy"].sum() / d["B"].sum() if d["B"].sum() > 0 else np.nan).rename("suit_vill")
# (b) 户基期相对单产 ȳs/ȳm（缺豆单产者用县2021中位数）
def suit_hh_yield(hh, cty):
    ys = base_hh.get((hh, "soy"), np.nan)
    ym = base_hh.get((hh, "corn"), np.nan)
    if pd.isna(ys):
        ys = cty_prior(cty, "soy", BASE_YR)
    if pd.isna(ym):
        ym = cty_prior(cty, "corn", BASE_YR)
    return ys / ym if (ym and not pd.isna(ym) and not pd.isna(ys)) else np.nan
# (c) 县序数（大豆适宜度：双城0 桦南1 甘南2）
CTY_ORD = {"双城区": 0, "桦南县": 1, "甘南县": 2}

# ---------- 5. 豆粮价格比（省级，t-1信息集） ----------
prov_p = cs.groupby(["year", "crop"])["price"].median().unstack()
price_ratio = (prov_p["soy"] / prov_p["corn"]).rename("pr_ratio")  # 按实现年份索引

# ---------- 6. 组装 ----------
def get(tab, val, cty, yr, cr):
    r = tab[(tab["county_name"] == cty) & (tab["year"] == yr) & (tab["crop"] == cr)]
    return r[val].iloc[0] if len(r) else np.nan

rows = []
for _, r in panel.iterrows():
    cty, yr, hh, vill = r["county_name"], int(r["year"]), r["hh_id"], r["village"]
    tm1 = yr - 1
    rec = {"suit_vill": v21.get(vill, np.nan), "suit_hhy": suit_hh_yield(hh, cty),
           "suit_cty": CTY_ORD.get(cty, np.nan),
           "pr_ratio_lag": price_ratio.get(tm1, np.nan)}
    if tm1 in years:
        p_c, p_s = get(ptab, "price", cty, tm1, "corn"), get(ptab, "price", cty, tm1, "soy")
        c_c, c_s = get(ctab, "cost_mu", cty, tm1, "corn"), get(ctab, "cost_mu", cty, tm1, "soy")
        s_c, s_s = SUB_OFFICIAL[yr]
        s_c_l, s_s_l = SUB_OFFICIAL.get(tm1, (np.nan, np.nan))
        d = DEFL[yr]
        for ver, ey_f in [("roll", lambda cr_: ey_roll(hh, cty, cr_, yr)),
                          ("base", lambda cr_: ey_base(hh, cty, cr_)),
                          ("loo", lambda cr_: ey_loo(hh, cty, cr_, yr))]:
            y_c, y_s = ey_f("corn"), ey_f("soy")
            mkt = (p_s * y_s - c_s) - (p_c * y_c - c_c)
            rec[f"dpi_mkt_{ver}"] = mkt * d
            rec[f"dpi_{ver}"] = (mkt + (s_s - s_c)) * d
        rec["dpi_sub"] = (s_s - s_c) * d
        rec["dpi_sub_lag"] = (s_s_l - s_c_l) * DEFL.get(tm1, np.nan) if tm1 in DEFL else np.nan
        # 村级补贴差（村报玉米标准，P1辅助识别）
        vs = r.get("v_sub_corn", np.nan)
        rec["dpi_sub_vill"] = (s_s - vs) * d if pd.notna(vs) else np.nan
    rows.append(rec)

dp = pd.DataFrame(rows, index=panel.index)
panel = pd.concat([panel, dp], axis=1)
for ver in ["roll", "base", "loo"]:
    panel[f"dpi100_{ver}"] = panel[f"dpi_{ver}"] / 100.0
    panel[f"dpi_mkt100_{ver}"] = panel[f"dpi_mkt_{ver}"] / 100.0
panel["dpi_sub100"] = panel["dpi_sub"] / 100.0
# 兼容旧接口（滚动版）
panel["dpi100"] = panel["dpi100_roll"]
panel["dpi"] = panel["dpi_roll"]
panel["dpi_mkt"] = panel["dpi_mkt_roll"]
panel["dpi_mkt100"] = panel["dpi_mkt100_roll"]
# Suit 标准化（估计样本上）
for sv in ["suit_vill", "suit_hhy"]:
    m, sd = panel[sv].mean(), panel[sv].std()
    panel[sv + "_z"] = (panel[sv] - m) / sd if sd and sd > 0 else np.nan
panel["suit_cty_z"] = (panel["suit_cty"] - panel["suit_cty"].mean()) / panel["suit_cty"].std()

panel.to_csv(f"{OUT}/panel_analysis.csv", index=False)

# ---------- 报告 ----------
est = panel[panel["plant_soy_lag"].notna()]
rep = ["# Phase 2 Δπ 构建报告（修订版）\n",
       "## 三版 Δπ 相关性与分布（估计样本，2024不变价）\n",
       est[["dpi_roll", "dpi_base", "dpi_loo"]].describe().round(1).to_string(),
       "\n\n相关系数：\n" + est[["dpi_roll", "dpi_base", "dpi_loo"]].corr().round(3).to_string(),
       "\n\n## Suit 覆盖率\n" + panel[["suit_vill", "suit_hhy", "suit_cty"]].notna().mean().round(3).to_string(),
       "\n\n## 村级补贴差覆盖\n" + f"dpi_sub_vill 非缺失 {panel['dpi_sub_vill'].notna().sum()} 行",
       "\n\n## 豆粮价格比（省级中位数）\n" + prov_p.round(2).to_string()]
with open(f"{OUT}/logs/phase2_report.md", "w") as f:
    f.write("\n".join(rep))
print(est[["dpi_roll", "dpi_base", "dpi_loo"]].describe().round(1).to_string())
print(est[["dpi_roll", "dpi_base", "dpi_loo"]].corr().round(3).to_string())
print("suit覆盖:", panel[["suit_vill", "suit_hhy"]].notna().mean().round(3).to_dict(),
      "v_sub行:", int(panel["dpi_sub_vill"].notna().sum()))
