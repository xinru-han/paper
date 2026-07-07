"""
01_build_panel.py — 构建黑龙江玉米—大豆种植决策分析面板（2019–2024）
数据：全国农村固定观察点·黑龙江分样本（双城区230113、甘南县230225、桦南县230822）
输出：output/panel_crop_long.csv, output/panel_hh.csv, output/logs/phase1_report.md
"""
import pandas as pd
import numpy as np
import re, os, warnings

warnings.filterwarnings("ignore")
RAW = "/root/data/数据/黑龙江农户调查"
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "output")
YEARS = [2019, 2020, 2021, 2022, 2023, 2024]

CROP_MAP = {"玉米": "corn", "豆类_大豆": "soy", "稻谷": "rice", "大豆": "soy"}
EDU_MAP = {"未上过学": 0, "小学": 6, "初中": 9, "高中及中专": 12, "大学（大专）及以上": 15}
SENTINELS = {-999, -9999, -99, 9999999}

# 农艺合理域（单产 kg/亩；价格 元/kg；面积 亩）
YIELD_BOUNDS = {"corn": (100, 1000), "soy": (30, 350), "rice": (100, 1000)}
PRICE_BOUNDS = {"corn": (0.8, 3.5), "soy": (2.0, 8.0), "rice": (1.0, 4.5)}
AREA_MAX = 2000.0


def numc(s):
    v = pd.to_numeric(s, errors="coerce")
    return v.mask(v.isin(SENTINELS) | (v < 0))


def crop_prefix(yr):
    return "种植业表1-" if yr == 2024 else "种植业分产品生产及销售情况表"


def cost_prefix(yr):
    return "种植业表3-" if yr == 2024 else "种植业分产品成本投入表"


def find_col(cols, prefix, i, key, exclude=()):
    pat = f"{prefix}{i}-"
    for c in cols:
        if c.startswith(pat) and key in c and not any(e in c for e in exclude):
            return c
    return None


def extract_repeat(df, prefix, fields, max_i=30):
    """fields: dict name -> (key, exclude). Returns long df with hh row index."""
    cols = list(df.columns)
    out = []
    for i in range(1, max_i + 1):
        code_c = find_col(cols, prefix, i, "产品编码")
        if code_c is None:
            break
        sub = pd.DataFrame({"_row": df.index, "code_raw": df[code_c]})
        for name, (key, excl) in fields.items():
            c = find_col(cols, prefix, i, key, excl)
            sub[name] = numc(df[c]) if c is not None else np.nan
        out.append(sub)
    L = pd.concat(out, ignore_index=True)
    L["code_raw"] = L["code_raw"].astype(str).str.strip()
    L["crop"] = L["code_raw"].map(CROP_MAP)
    return L


def head_row(df, yr):
    """户主特征：关系=='户主'的成员，否则成员1。"""
    cols = list(df.columns)
    rel_cols = [c for c in cols if re.match(r"家庭成员\d+-与户主的关系$", c)]
    n_mem = len(rel_cols)
    age = pd.Series(np.nan, index=df.index)
    edu = pd.Series(np.nan, index=df.index)
    male = pd.Series(np.nan, index=df.index)
    filled = pd.Series(False, index=df.index)
    for i in range(1, n_mem + 1):
        rel = df.get(f"家庭成员{i}-与户主的关系")
        if rel is None:
            continue
        is_head = rel.astype(str).str.contains("户主|本人", na=False)
        if i == 1:
            is_head = is_head | rel.isna()  # 成员1缺关系时默认为户主
        take = is_head & ~filled
        if not take.any():
            continue
        a = numc(df.get(f"家庭成员{i}-年龄(周岁)", pd.Series(np.nan, index=df.index)))
        a = a.mask((a < 16) | (a > 100))  # 户主年龄合理域
        ec = [c for c in cols if c.startswith(f"家庭成员{i}-文化程度")]
        if ec:
            e_raw = df[ec[0]]
            e = pd.to_numeric(e_raw, errors="coerce")
            e = e.fillna(e_raw.map(EDU_MAP))
        else:
            e = pd.Series(np.nan, index=df.index)
        g = df.get(f"家庭成员{i}-性别")
        m = g.astype(str).str.contains("男", na=False).astype(float) if g is not None else np.nan
        age[take] = a[take]
        edu[take] = pd.to_numeric(e, errors="coerce")[take]
        male[take] = m[take] if g is not None else np.nan
        filled |= take
    return pd.DataFrame({"head_age": age, "head_edu": edu, "head_male": male})


def offfarm_count(df):
    cols = list(df.columns)
    day_cols = [c for c in cols if re.match(r"家庭成员\d+-.*务工天数", c)]
    if day_cols:
        cnt = sum((numc(df[c]) > 0).astype(int) for c in day_cols)
        return cnt
    # 2024: 从事非农业劳动的时间
    alt = [c for c in cols if re.match(r"家庭成员\d+-.*从事非农业劳动的时间", c)]
    if alt:
        def pos(c):
            v = pd.to_numeric(df[c], errors="coerce")
            if v.notna().sum() > 0:
                return (v > 0).astype(int)
            return df[c].astype(str).str.contains("个月|半年|全年", na=False).astype(int)
        return sum(pos(c) for c in alt)
    return pd.Series(np.nan, index=df.index)


def build_year(yr):
    df = pd.read_excel(f"{RAW}/户问卷{yr}.xlsx")
    df.columns = [str(c).strip() for c in df.columns]
    cols = list(df.columns)

    ids = pd.DataFrame({
        "hh_raw": df["农户代码"].astype(str).str.strip(),
        "county_code": pd.to_numeric(df[[c for c in cols if c == "县代码"][0]], errors="coerce"),
        "county_name": df["县名"].astype(str).str.strip(),
        "village": pd.to_numeric(df["行政村代码"], errors="coerce"),
        "head_name": df["户主姓名"].astype(str).str.strip() if "户主姓名" in cols else "",
        "year": yr,
    })
    ids["_rowid"] = [f"{yr}_{i}" for i in df.index]
    # 行信息完整度（去重时保留信息更全的行）
    ids["_nonnull"] = df.notna().sum(axis=1).values
    acols = [c for c in cols if c.startswith(crop_prefix(yr)) and "播种面积" in c and "来年" not in c]
    ids["_has_crop"] = df[acols].notna().any(axis=1).values if acols else False

    # ---- 作物生产表 ----
    Lp = extract_repeat(df, crop_prefix(yr), {
        "area": ("播种面积", ("来年",)),
        "output": ("产量", ("因灾",)),
        "sale_q": ("总销售量", ()),
        "sale_v": ("总销售收入", ()),
        "ins_pay": ("获得农业保险赔偿", ()),
    })
    Lp = Lp.dropna(subset=["crop"])
    Lp = Lp[(Lp["area"] > 0) & (Lp["area"] <= AREA_MAX)]

    # ---- 成本投入表 ----
    cost_fields = {
        "seed": ("种子、秧苗金额", ()), "fert": ("化肥金额", ()),
        "org1": ("有机肥自产", ()), "org2": ("有机肥外购", ()),
        "pest": ("农药、除草剂费", ()), "film": ("农膜费", ()),
        "irri": ("排灌费", ()), "mach": ("机械费", ()),
        "trans": ("运输仓储费", ()), "intr": ("贷款利息", ()),
        "insfee": ("保险费支出", ()), "other": ("其他费用", ()),
        "hire_d": ("2雇工（工日）", ()), "hire_p": ("3雇工平均价格", ()),
    }
    Lc = extract_repeat(df, cost_prefix(yr), cost_fields)
    Lc = Lc.dropna(subset=["crop"])
    cash_items = ["seed", "fert", "org2", "pest", "film", "irri", "mach", "trans", "intr", "insfee", "other"]
    Lc["hire_cost"] = (Lc["hire_d"].fillna(0) * Lc["hire_p"].fillna(0))
    Lc["cash_cost"] = Lc[cash_items].fillna(0).sum(axis=1) + Lc["hire_cost"]
    Lc = Lc.groupby(["_row", "crop"], as_index=False)["cash_cost"].sum()

    crop = Lp.groupby(["_row", "crop"], as_index=False).agg(
        area=("area", "sum"), output=("output", "sum"),
        sale_q=("sale_q", "sum"), sale_v=("sale_v", "sum"), ins_pay=("ins_pay", "sum"))
    crop = crop.merge(Lc, on=["_row", "crop"], how="left")
    crop = crop.merge(ids[["_rowid", "county_code", "county_name", "village", "year"]],
                      left_on="_row", right_index=True).drop(columns="_row")

    # 单产/价格/亩均成本 + 合理域清洗（越界置缺失，保留种植事实）
    crop["yield"] = crop["output"] / crop["area"]
    crop["price"] = np.where((crop["sale_q"] > 0) & (crop["sale_v"] > 0), crop["sale_v"] / crop["sale_q"], np.nan)
    crop["cost_mu"] = np.where(crop["cash_cost"] > 0, crop["cash_cost"] / crop["area"], np.nan)
    for c, (lo, hi) in YIELD_BOUNDS.items():
        m = crop["crop"] == c
        crop.loc[m & ((crop["yield"] < lo) | (crop["yield"] > hi)), "yield"] = np.nan
    for c, (lo, hi) in PRICE_BOUNDS.items():
        m = crop["crop"] == c
        crop.loc[m & ((crop["price"] < lo) | (crop["price"] > hi)), "price"] = np.nan
    crop.loc[(crop["cost_mu"] > 3000) | (crop["cost_mu"] < 20), "cost_mu"] = np.nan

    # ---- 户特征 ----
    hh = ids.copy()
    hh = pd.concat([hh, head_row(df, yr)], axis=1)
    lab = [c for c in cols if "劳动力（16-59周岁）人数" in c]
    hh["labor_n"] = numc(df[lab[0]]) if lab else np.nan
    hh["offfarm_n"] = offfarm_count(df)
    insq = [c for c in cols if c.startswith("您家是否购买了农业生产保险")]
    if insq:
        hh["insurance"] = df[insq[0]].astype(str).str.contains("是|1", na=False).astype(float)
        hh.loc[df[insq[0]].isna(), "insurance"] = np.nan
    else:  # 2024 无该题，用种植业保险费支出>0 代理
        insfee = Lc_ins = extract_repeat(df, cost_prefix(yr), {"insfee": ("保险费支出", ())})
        f = insfee.groupby("_row")["insfee"].sum()
        hh["insurance"] = (hh.index.map(f).fillna(0) > 0).astype(float)
    # 户报生产者补贴（用于交叉校核）
    for zh, en in [("玉米生产者补贴", "sub_corn_rep"), ("大豆生产者补贴", "sub_soy_rep"),
                   ("轮作补贴", "sub_rot_rep"), ("种粮补贴中，生产者补贴", "sub_prod_rep")]:
        cc = [c for c in cols if zh in c]
        hh[en] = numc(df[cc[0]]) if cc else np.nan
    return crop, hh


def assign_hh_id(hh):
    """户键：有效且非批量占位的18位农户代码优先，否则 村代码+户主姓名。

    占位码识别：同一年内被 >5 户共享的代码（多为整村共用一码）或缺失。
    对占位/缺失码的户，若 (村,姓名) 在全样本中唯一对应一个有效代码则回填，
    否则用 V村代码_姓名 作键。年内同键多行 = 重复录入，保留信息更全的行。
    """
    valid18 = hh["hh_raw"].str.match(r"^\d{17}[\dXx]$", na=False)
    bulk = set()
    for yr, g in hh.groupby("year"):
        vc = g["hh_raw"].value_counts()
        bulk |= set(vc[vc > 5].index)
    hh["_code_ok"] = valid18 & ~hh["hh_raw"].isin(bulk)

    # (村,姓名) -> 唯一有效代码 的回填映射
    ok = hh[hh["_code_ok"] & (hh["head_name"] != "") & (hh["head_name"] != "nan")]
    m = ok.groupby(["village", "head_name"])["hh_raw"].agg(["nunique", "first"])
    fill = m[m["nunique"] == 1]["first"]
    key = hh.set_index(["village", "head_name"]).index.map(fill)
    filled = pd.Series(key, index=hh.index)

    hh["hh_id"] = np.where(hh["_code_ok"], hh["hh_raw"],
                  np.where(filled.notna(), filled,
                           "V" + hh["village"].astype("Int64").astype(str) + "_" + hh["head_name"]))
    return hh


def main():
    os.makedirs(f"{OUT}/logs", exist_ok=True)
    crops, hhs = [], []
    for yr in YEARS:
        c, h = build_year(yr)
        crops.append(c)
        hhs.append(h)
        print(f"{yr}: hh={len(h)}, crop rows={len(c)}, corn={int((c['crop']=='corn').sum())}, soy={int((c['crop']=='soy').sum())}")
    crop = pd.concat(crops, ignore_index=True)
    hh = pd.concat(hhs, ignore_index=True)

    hh = assign_hh_id(hh)
    # 年内同键去重：优先有作物数据、其次信息更全的行；作物长表只保留主行的记录
    hh = hh.sort_values(["_has_crop", "_nonnull"], ascending=False)
    n0 = len(hh)
    hh = hh.drop_duplicates(["hh_id", "year"], keep="first")
    print(f"dedup: dropped {n0 - len(hh)} duplicate hh-year rows")
    crop = crop[crop["_rowid"].isin(set(hh["_rowid"]))]
    crop = crop.merge(hh[["_rowid", "hh_id"]], on="_rowid", how="left")
    hh = hh.drop(columns=["_nonnull", "_has_crop", "_code_ok"])

    # ---- 户×年主表 ----
    cs = crop[crop["crop"].isin(["corn", "soy"])]
    w = cs.pivot_table(index=["hh_id", "year"], columns="crop", values="area", aggfunc="sum").fillna(0)
    w = w.rename(columns={"corn": "area_corn", "soy": "area_soy"}).reset_index()
    if "area_soy" not in w:
        w["area_soy"] = 0.0
    w["B"] = w["area_corn"] + w["area_soy"]
    w = w[w["B"] > 0]
    w["s"] = w["area_soy"] / w["B"]
    w["plant_soy"] = (w["area_soy"] > 0).astype(int)

    panel = w.merge(hh, on=["hh_id", "year"], how="left")

    # 滞后项
    panel = panel.sort_values(["hh_id", "year"])
    panel["s_lag"] = panel.groupby("hh_id")["s"].shift(1)
    panel["year_lag"] = panel.groupby("hh_id")["year"].shift(1)
    gap = panel["year"] - panel["year_lag"]
    panel.loc[gap != 1, "s_lag"] = np.nan
    panel["plant_soy_lag"] = np.where(panel["s_lag"].notna(), (panel["s_lag"] > 0).astype(float), np.nan)

    # 村内同伴（leave-one-out，上一年）
    vy = panel.groupby(["village", "year"]).agg(sum_s=("s", "sum"), n=("s", "size")).reset_index()
    panel = panel.merge(vy, on=["village", "year"], how="left")
    panel["peer_now"] = np.where(panel["n"] > 1, (panel["sum_s"] - panel["s"]) / (panel["n"] - 1), np.nan)
    pl = panel[["hh_id", "year", "peer_now"]].copy()
    pl["year"] += 1
    pl = pl.rename(columns={"peer_now": "peer_lag"})
    panel = panel.merge(pl, on=["hh_id", "year"], how="left").drop(columns=["sum_s", "n"])

    panel["logB"] = np.log(panel["B"])
    panel["head_age10"] = panel["head_age"] / 10.0

    crop.to_csv(f"{OUT}/panel_crop_long.csv", index=False)
    panel.to_csv(f"{OUT}/panel_hh.csv", index=False)

    # ---- 报告 ----
    rep = ["# Phase 1 面板构建报告\n"]
    rep.append(f"- 作物长表 {len(crop)} 行；户年主表（B>0）{len(panel)} 行，{panel['hh_id'].nunique()} 户\n")
    rep.append("\n## 分县分年大豆参与率与面积份额（面积加权）\n")
    g = panel.groupby(["county_name", "year"]).apply(
        lambda d: pd.Series({"N": len(d), "particip": d["plant_soy"].mean(),
                             "share_w": d["area_soy"].sum() / d["B"].sum()})).reset_index()
    rep.append(g.to_string(index=False))
    dur = panel.groupby("hh_id")["year"].nunique()
    rep.append(f"\n\n- 连续观测≥3年的户数：{(dur>=3).sum()}；4年及以上：{(dur>=4).sum()}\n")
    with open(f"{OUT}/logs/phase1_report.md", "w") as f:
        f.write("\n".join(str(x) for x in rep))
    print(g.to_string(index=False))
    print("panel saved:", len(panel), "hh:", panel["hh_id"].nunique())


if __name__ == "__main__":
    main()
