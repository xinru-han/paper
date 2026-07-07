# -*- coding: utf-8 -*-
"""构建主面板: 省×作物×年 (2004-2024), 7种粮食作物
目标: net_profit(元/亩), loss(0/1), cash_income(现金口径)
特征: L1滞后层 + L2年内信号层(投入品价/收购价/气象) + L3结构层
输出: data/processed/master_panel.csv, data_dictionary.csv
"""
import os
import numpy as np
import pandas as pd

OUT = "/root/grain_profit_warning/data/processed"
os.makedirs(OUT, exist_ok=True)

GRAIN = ["corn", "wheat", "soybean", "rice_early_indica",
         "rice_mid_indica", "rice_late_indica", "rice_japonica"]

PROV_CODE = {"北京": 11, "天津": 12, "河北": 13, "山西": 14, "内蒙古": 15,
             "辽宁": 21, "吉林": 22, "黑龙江": 23, "上海": 31, "江苏": 32,
             "浙江": 33, "安徽": 34, "福建": 35, "江西": 36, "山东": 37,
             "河南": 41, "湖北": 42, "湖南": 43, "广东": 44, "广西": 45,
             "海南": 46, "重庆": 50, "四川": 51, "贵州": 52, "云南": 53,
             "西藏": 54, "陕西": 61, "甘肃": 62, "青海": 63, "宁夏": 64, "新疆": 65}

# ---------- 1. 成本收益面板 ----------
yb = pd.read_csv("/root/paper/cost_elasticity/data/yearbook_long.csv")
yb = yb[yb["crop"].isin(GRAIN)]
w = yb.pivot_table(index=["crop", "province", "year"],
                   columns="variable", values="value", aggfunc="first").reset_index()

w["net_profit"] = w["产值合计"] - w["总成本"]
w["loss"] = (w["net_profit"] < 0).astype(int)
w["cash_income"] = w["产值合计"] - (w["总成本"]
                                    - w.get("家庭用工折价", 0).fillna(0)
                                    - w.get("自营地折租", 0).fillna(0))
w["profit_margin"] = w["net_profit"] / w["总成本"]

# 成本份额（结构特征，用其滞后值）
for name, col in [("s_labor", "人工成本"), ("s_land", "土地成本"), ("s_fert", "化肥费"),
                  ("s_mach", "机械作业费"), ("s_seed", "种子费")]:
    if col in w.columns:
        w[name] = w[col] / w["总成本"]

keep_level = ["主产品产量", "平均出售价格", "产值合计", "总成本", "人工成本", "土地成本",
              "化肥费", "机械作业费", "种子费", "农药费", "排灌费", "劳动日工价",
              "每亩用工数量", "每亩化肥折纯用量", "流转地租金"]
keep_level = [c for c in keep_level if c in w.columns]

EN = {"主产品产量": "yield_main", "平均出售价格": "sale_price", "产值合计": "revenue",
      "总成本": "total_cost", "人工成本": "cost_labor", "土地成本": "cost_land",
      "化肥费": "cost_fert", "机械作业费": "cost_mach", "种子费": "cost_seed",
      "农药费": "cost_pest", "排灌费": "cost_irrig", "劳动日工价": "wage_day",
      "每亩用工数量": "labor_days", "每亩化肥折纯用量": "fert_kg", "流转地租金": "land_rent"}
w = w.rename(columns=EN)
base_cols = ["crop", "province", "year", "net_profit", "loss", "cash_income",
             "profit_margin", "s_labor", "s_land", "s_fert", "s_mach", "s_seed"] + \
            [EN[c] for c in keep_level]
w = w[[c for c in base_cols if c in w.columns]].sort_values(["crop", "province", "year"])

# ---------- 2. L1 滞后层 ----------
g = w.groupby(["crop", "province"], group_keys=False)
lag_vars = ["net_profit", "loss", "profit_margin", "yield_main", "sale_price",
            "revenue", "total_cost", "cost_labor", "cost_land", "cost_fert",
            "cost_mach", "cost_seed", "cost_pest", "wage_day", "labor_days",
            "fert_kg", "land_rent", "s_labor", "s_land", "s_fert", "s_mach", "s_seed",
            "cash_income"]
lag_vars = [v for v in lag_vars if v in w.columns]
for v in lag_vars:
    w[f"L1_{v}"] = g[v].shift(1)
for v in ["net_profit", "sale_price", "total_cost", "yield_main"]:
    w[f"L2_{v}"] = g[v].shift(2)
    w[f"trend3_{v}"] = g[v].shift(1) - g[v].shift(3)  # 3年变化(滞后)
w["L1_cost_yoy"] = g["total_cost"].shift(1) / g["total_cost"].shift(2) - 1
w["L1_price_yoy"] = g["sale_price"].shift(1) / g["sale_price"].shift(2) - 1

# ---------- 3. L2a 投入品价格 (省×年, 当年可观测) ----------
ndrc = pd.read_csv("/root/paper/cost_elasticity/data/prices_ndrc_annual.csv")
keep_items = ["urea", "npk_cl", "dap", "abc", "ssp", "mulch_film",
              "chlorpyrifos", "machine_tillage", "machine_harvest"]
ndrc = ndrc[ndrc["item"].isin(keep_items)]
np_w = ndrc.pivot_table(index=["province", "year"], columns="item",
                        values="price", aggfunc="mean").reset_index()
np_w.columns = ["province", "year"] + [f"in_{c}" for c in np_w.columns[2:]]
# 投入品价格同比
np_w = np_w.sort_values(["province", "year"])
for c in [c for c in np_w.columns if c.startswith("in_")]:
    np_w[f"{c}_yoy"] = np_w.groupby("province")[c].pct_change()
w = w.merge(np_w, on=["province", "year"], how="left")

# ---------- 4. L2b 原粮收购价特征 (省×品种×年) ----------
gp = pd.read_csv(f"{OUT}/grain_price_features.csv")
w = w.merge(gp, on=["province", "crop", "year"], how="left")

# ---------- 4b. L2b' 成品粮零售价信号 (全国×品种组×年, 2005-2024全覆盖) ----------
rp = pd.read_csv(f"{OUT}/retail_price_features.csv")
w["grp"] = w["crop"].map(lambda c: "rice" if c.startswith("rice") else c)
w = w.merge(rp, on=["grp", "year"], how="left").drop(columns=["grp"])

# ---------- 5. L2c 气象 (省×月 → 生长季聚合) ----------
def load_weather(path, stem, ano_stem=None):
    d = pd.read_csv(path)
    code2name = {v: k for k, v in PROV_CODE.items()}
    d["province"] = d["省码"].map(code2name)
    d = d.rename(columns={"年": "year"})
    ano_stem = ano_stem or f"{stem}距平"
    lvl = [c for c in d.columns if c.startswith(stem) and "距平" not in c and c != "year"]
    ano = [c for c in d.columns if c.startswith(ano_stem)]
    def mcols(cols, months):
        return [c for c in cols if any(c.endswith(f"{m}月") for m in months)]
    grow = list(range(4, 10))
    out = d[["province", "year"]].copy()
    out[f"{stem}_grow"] = d[mcols(lvl, grow)].mean(axis=1)
    out[f"{stem}_ano_grow"] = d[mcols(ano, grow)].mean(axis=1)
    out[f"{stem}_ano_absmax"] = d[mcols(ano, grow)].abs().max(axis=1)
    return out

tmp = load_weather("/root/data/Paper/种粮盈亏预测/data/气温及气温距平_最终版.csv", "气温")
pre = load_weather("/root/data/Paper/种粮盈亏预测/data/降水及降水距平_最终版.csv", "降水量", "降水距平")
tmp.columns = ["province", "year", "temp_grow", "temp_ano_grow", "temp_ano_absmax"]
pre.columns = ["province", "year", "prec_grow", "prec_ano_grow", "prec_ano_absmax"]
w = w.merge(tmp, on=["province", "year"], how="left").merge(pre, on=["province", "year"], how="left")

# ---------- 6. L3 结构层 ----------
w["trend"] = w["year"] - 2004
w["policy_corn_reform"] = ((w["crop"] == "corn") & (w["year"] >= 2016)).astype(int)
w["policy_min_price"] = (w["crop"].str.startswith("rice") | (w["crop"] == "wheat")).astype(int)
REGION = {"黑龙江": "dongbei", "吉林": "dongbei", "辽宁": "dongbei", "内蒙古": "dongbei",
          "河北": "huanghuai", "河南": "huanghuai", "山东": "huanghuai", "山西": "huanghuai", "陕西": "huanghuai",
          "江苏": "changjiang", "安徽": "changjiang", "湖北": "changjiang", "湖南": "changjiang",
          "江西": "changjiang", "浙江": "changjiang", "上海": "changjiang", "四川": "xinan",
          "重庆": "xinan", "贵州": "xinan", "云南": "xinan", "广西": "huanan", "广东": "huanan",
          "福建": "huanan", "海南": "huanan", "甘肃": "xibei", "宁夏": "xibei", "新疆": "xibei",
          "青海": "xibei", "北京": "huanghuai", "天津": "huanghuai", "西藏": "xibei"}
w["region"] = w["province"].map(REGION)

# ---------- 7. 落盘 ----------
w = w[w["year"] >= 2004].reset_index(drop=True)
w.to_csv(f"{OUT}/master_panel.csv", index=False, encoding="utf-8-sig")
print("master_panel:", w.shape)
print(w.groupby("crop").agg(n=("year", "size"), loss_rate=("loss", "mean"),
                            ymin=("year", "min"), ymax=("year", "max")))

# 数据字典
DD = {
    "crop/province/year/region": "面板维度; region=六大产区",
    "net_profit": "目标: 净利润(元/亩)=产值合计-总成本",
    "loss": "目标: 亏损=1(net_profit<0)",
    "cash_income": "现金口径收益(加回家庭用工折价+自营地折租)",
    "L1_*/L2_*": "滞后1/2期的汇编指标(元/亩等)",
    "trend3_*": "滞后1期减滞后3期(3年趋势)",
    "L1_cost_yoy/L1_price_yoy": "滞后成本/售价同比",
    "in_*": "当年投入品价格(发改委采价,省均): 尿素/复合肥/磷肥类/农膜/农药/机耕/机收",
    "in_*_yoy": "投入品价格同比",
    "gp_year_mean": "当年原粮收购价全年均值(元/50kg)[事后版特征]",
    "gp_grow_mean/gp_pre_mean": "生长季(4-9月)/播前(1-4月)收购价均值[预警版可用]",
    "gp_cv/gp_yoy/gp_pre_yoy": "收购价年内变异系数/年度同比/播前同比",
    "temp_grow/prec_grow": "生长季(4-9月)平均气温/降水",
    "*_ano_grow": "生长季距平均值(基准1973-2002)",
    "*_ano_absmax": "生长季距平绝对值最大(极端性)",
    "policy_corn_reform": "2016玉米临储改革后=1",
    "policy_min_price": "最低收购价作物(稻麦)=1",
}
pd.Series(DD).rename("说明").to_csv(f"{OUT}/data_dictionary.csv", encoding="utf-8-sig")
missing = w.isna().mean().sort_values(ascending=False)
print("\nTop missing:\n", missing.head(15))
