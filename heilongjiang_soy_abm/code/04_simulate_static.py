"""
04_simulate_static.py — 静态反事实主体仿真（修改清单 §4/§5 主口径）

将原「2025—2030 逐年前瞻 ABM」改为「以 2024 年经济环境为基准的一期静态反事实」：
  * 主体池 = 每户最后一次可观测状态（366 户），共同置于 2024 年价格/成本/补贴环境；
  * 不滚动年份、不更新状态、不加宏观年冲击、不做 2030 目标反解；
  * 参与率/份额用期望 P_i、E[s_i]（非条件分数logit），参数不确定性来自 β~N(β̂,V̂)；
  * 主线不校准（报告情景相对变化），校准版入附录（§4.5）。
情景 S0–S5（§4.3）。轮作补贴严格新增(strict_new)为主、新增参与户(new_entrant)为稳健(§4.4)。
财政与单位扩种成本仅对财政补贴类情景计算；价格情景另算价格支持成本或只报面积响应(§4.3)。
稳健性口径：last-observed 主口径 / 2024-only / 连续≥3年（§2.2、§4.6）。
验证：2024 在场户样本内 + 2023→2024 留出（Brier/AUC）+ 县分组（§4.6）。
输出：output/scenarios_static/*.csv, output/figures/fig_static_scenarios.png
"""
import pandas as pd
import numpy as np
import json, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
from abm import load_params, run_static, make_scenario

OUT = os.path.join(BASE, "output")
SDIR = f"{OUT}/scenarios_static"
os.makedirs(SDIR, exist_ok=True)
os.makedirs(f"{OUT}/figures", exist_ok=True)
for f in ["/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=f).get_name()
plt.rcParams["axes.unicode_minus"] = False

RAWP = load_params(f"{OUT}/params/behavior_params.json")
panel = pd.read_csv(f"{OUT}/panel_analysis.csv")
panel = panel[panel["village"].notna()].copy().sort_values(["hh_id", "year"])
ptab = pd.read_csv(f"{OUT}/params/price_table.csv")
ctab = pd.read_csv(f"{OUT}/params/cost_table.csv")

# ---------- 经济环境：2024 年实现值为共同基准（2024=不变价基准年） ----------
def med(tab, val, yr, cr):
    return float(tab[(tab["year"] == yr) & (tab["crop"] == cr)][val].median())

P_CORN0, P_SOY0 = med(ptab, "price", 2024, "corn"), med(ptab, "price", 2024, "soy")
C_CORN0, C_SOY0 = med(ctab, "cost_mu", 2024, "corn"), med(ctab, "cost_mu", 2024, "soy")
SUB_CORN0, SUB_SOY0 = 20.0, 350.0
# 静态口径：无逐年农学反馈（§4.1 移除单产逐年上调/下调），朴素预期=基期锁定单产
ECON = {"cost_per_mu": {"corn": C_CORN0, "soy": C_SOY0}, "delta_rot": 0.0, "delta_rep": 0.0}

def mk_params(part_key):
    return {"participation": RAWP[part_key], "share": RAWP["share_unconditional"], "econ": ECON}

P_MAIN = mk_params("participation")
P_W = mk_params("participation_wooldridge")

# ---------- 潜在单产（基期锁定收缩，K=2；与 02 一致） ----------
cs = pd.read_csv(f"{OUT}/panel_crop_long.csv")
cs = cs[cs["crop"].isin(["corn", "soy"])].dropna(subset=["yield"])
cty_med = cs.groupby(["county_name", "crop"])["yield"].median()
prov_med = cs.groupby("crop")["yield"].median()
base_hh = cs[cs["year"] == 2021].groupby(["hh_id", "crop"])["yield"].mean()

def ey_base(hh, cty, crop):
    prior = cty_med.get((cty, crop), prov_med[crop])
    v = base_hh.get((hh, crop), np.nan)
    return prior if pd.isna(v) else (v + 2 * prior) / 3.0

# ---------- 主体构造 ----------
STATIC = ["head_age10", "head_edu", "head_male", "head_health", "labor_n", "offfarm_n",
          "wage_share", "rentin_d", "ln_asset", "insurance", "internet", "head_train_agr",
          "v_coop_n", "logB"]
first = panel.groupby("hh_id").first()
W_BARS = [v[:-4] for v in RAWP["participation_wooldridge"]["vcov_vars"] if v.endswith("_bar")]
def _bar_src(v):
    return "peer_lag" if v == "peer_lag0" else v
hh_bar_mean = {v: panel.groupby("hh_id")[_bar_src(v)].mean()
               for v in W_BARS if _bar_src(v) in panel.columns}

def add_bars(df):
    df = df.copy()
    df["D_init"] = df["hh_id"].map(first["plant_soy"]).astype(float)
    for v in W_BARS:
        col = "bar_" + v
        if v in hh_bar_mean:
            df[col] = df["hh_id"].map(hh_bar_mean[v])
            df[col] = df[col].fillna(df[col].median() if df[col].notna().any() else 0.0)
        else:
            df[col] = 0.0
    return df

def prep_agents(df):
    df = df.copy()
    for c in STATIC:
        df[c] = df[c].fillna(panel[c].median())
    df = add_bars(df)
    df["ey_corn"] = [ey_base(h, c, "corn") for h, c in zip(df["hh_id"], df["county_name"])]
    df["ey_soy"] = [ey_base(h, c, "soy") for h, c in zip(df["hh_id"], df["county_name"])]
    df["s_init"] = df["s"].fillna(0.0)
    df["plant_soy_init"] = df["plant_soy"].astype(float)
    df["structural_zero"] = (df["county_name"] == "双城区").astype(int)
    cols = (["hh_id", "county_name", "village", "B", "ey_corn", "ey_soy", "s_init",
             "plant_soy_init", "structural_zero", "D_init", "state_year"]
            + ["bar_" + v for v in W_BARS] + STATIC)
    return df[cols].reset_index(drop=True)

# 主口径：每户最后一次可观测记录
last = panel.groupby("hh_id").tail(1).copy()
last["state_year"] = last["year"]
agents_main = prep_agents(last)
agents_main.to_csv(f"{SDIR}/agents_lastobs.csv", index=False)
print(f"主体池(last-obs): {len(agents_main)} 户, 双城结构零 {int(agents_main['structural_zero'].sum())}")

# 主体状态年份分布（§5.2）
syd = agents_main.groupby("state_year").size().rename("n_agents").reset_index()
syd["share"] = (syd["n_agents"] / syd["n_agents"].sum()).round(3)
syd.to_csv(f"{SDIR}/agent_state_year_distribution.csv", index=False)
print("状态年份分布:\n", syd.to_string(index=False))

# 稳健性主体池
a2024 = panel[panel["year"] == 2024].copy(); a2024["state_year"] = 2024
agents_2024 = prep_agents(a2024)
abal = panel[panel["balanced3"] == 1].groupby("hh_id").tail(1).copy()
abal["state_year"] = abal["year"]
agents_bal = prep_agents(abal)
print(f"2024-only: {len(agents_2024)} 户; 连续≥3年: {len(agents_bal)} 户")

# ---------- 情景定义（§4.3） ----------
def scen(sub_soy=SUB_SOY0, sub_corn=SUB_CORN0, p_soy=P_SOY0, sub_rot=0.0):
    return make_scenario([2024], P_CORN0, p_soy, sub_corn, sub_soy, sub_rot)

SCN = {
    "S0_基准": dict(sc=scen(), fiscal_cmp=True, rot="strict_new"),
    "S1_大豆补贴+100元": dict(sc=scen(sub_soy=SUB_SOY0 + 100), fiscal_cmp=True, rot="strict_new"),
    "S2_大豆补贴+50%": dict(sc=scen(sub_soy=SUB_SOY0 * 1.5), fiscal_cmp=True, rot="strict_new"),
    "S3_轮作补贴150元": dict(sc=scen(sub_rot=150.0), fiscal_cmp=True, rot="strict_new"),
    "S4_豆价+10%": dict(sc=scen(p_soy=P_SOY0 * 1.10), fiscal_cmp=False, rot="strict_new"),
    "S5_取消玉米补贴": dict(sc=scen(sub_corn=0.0), fiscal_cmp=True, rot="strict_new"),
}
SIM_KW = dict(n_mc=1000, seed=42)   # 公共随机数：所有情景共用 seed → 参数抽样对齐

# ---------- 截距校准（§4.5：主口径不校准；校准版入附录） ----------
obs24_part = panel[(panel["year"] == 2024) &
                   (panel["county_name"] != "双城区")]["plant_soy"].mean()

def calibrate(P, ag, seed=1):
    lo, hi = -5.0, 5.0
    for _ in range(20):
        mid = (lo + hi) / 2
        v = run_static(ag, P, SCN["S0_基准"]["sc"], calib_offset=mid,
                       n_mc=300, seed=seed)["agg"]["soy_particip"]
        if v < obs24_part:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

CAL_MAIN = calibrate(P_MAIN, agents_main)
print(f"观测2024参与率(非双城)={obs24_part:.3f}, 校准偏移 CAL_MAIN={CAL_MAIN:.3f}")

# ---------- 情景运行器 ----------
def run_all(agents, P, calib=0.0, tag=""):
    rows = []
    base = None
    for name, cfg in SCN.items():
        r = run_static(agents, P, cfg["sc"], calib_offset=calib,
                       rot_mode=cfg["rot"], **SIM_KW)["agg"]
        r = dict(r); r["scenario"] = name; r["fiscal_cmp"] = cfg["fiscal_cmp"]
        if name == "S0_基准":
            base = r
        rows.append(r)
    df = pd.DataFrame(rows)
    b_f, b_s = base["fiscal"], base["soy_share"]
    df["d_share_pp"] = (df["soy_share"] - b_s) * 100
    df["d_fiscal"] = df["fiscal"] - b_f
    # 单位扩种成本：仅财政补贴类情景且份额确有增量
    df["cost_per_pp"] = np.where(df["fiscal_cmp"] & (df["d_share_pp"] > 1e-3),
                                 df["d_fiscal"] / df["d_share_pp"], np.nan)
    df["param_set"] = tag
    return df

main_df = run_all(agents_main, P_MAIN, calib=0.0, tag="main_uncalib")
wool_df = run_all(agents_main, P_W, calib=0.0, tag="wooldridge")
cal_df = run_all(agents_main, P_MAIN, calib=CAL_MAIN, tag="main_calibrated")
d2024_df = run_all(agents_2024, P_MAIN, calib=0.0, tag="sample_2024only")
dbal_df = run_all(agents_bal, P_MAIN, calib=0.0, tag="sample_balanced")

COLS = ["scenario", "soy_particip", "soy_particip_lo", "soy_particip_hi", "soy_share",
        "soy_share_lo", "soy_share_hi", "soy_area", "fiscal", "d_share_pp", "d_fiscal",
        "cost_per_pp", "rot_area"]
main_df[COLS].round(4).to_csv(f"{SDIR}/static_scenarios_main.csv", index=False)
wool_df[COLS].round(4).to_csv(f"{SDIR}/static_scenarios_wooldridge.csv", index=False)
cal_df[COLS].round(4).to_csv(f"{SDIR}/static_scenarios_calibrated.csv", index=False)
d2024_df[COLS].round(4).to_csv(f"{SDIR}/static_scenarios_2024only.csv", index=False)
dbal_df[COLS].round(4).to_csv(f"{SDIR}/static_scenarios_balanced.csv", index=False)
print("\n== 静态情景（主线，未校准） ==")
print(main_df[["scenario", "soy_particip", "soy_share", "d_share_pp", "d_fiscal", "cost_per_pp"]]
      .round(4).to_string(index=False))

# ---------- 轮作补贴口径对照：strict_new vs new_entrant（§4.4） ----------
rot_rows = []
for mode in ["strict_new", "new_entrant"]:
    r = run_static(agents_main, P_MAIN, SCN["S3_轮作补贴150元"]["sc"],
                   calib_offset=0.0, rot_mode=mode, **SIM_KW)["agg"]
    b = main_df[main_df["scenario"] == "S0_基准"].iloc[0]
    dpp = (r["soy_share"] - b["soy_share"]) * 100
    rot_rows.append({"rot_mode": mode, "soy_share": r["soy_share"], "d_share_pp": dpp,
                     "rot_area": r["rot_area"], "fiscal": r["fiscal"],
                     "d_fiscal": r["fiscal"] - b["fiscal"],
                     "cost_per_pp": (r["fiscal"] - b["fiscal"]) / dpp if dpp > 1e-3 else np.nan})
rot_df = pd.DataFrame(rot_rows).round(4)
rot_df.to_csv(f"{SDIR}/rotation_caliber.csv", index=False)
print("\n== 轮作补贴口径对照 ==")
print(rot_df.to_string(index=False))

# ---------- S4 价格支持成本（另算，不与财政补贴排序）（§4.3） ----------
s4 = main_df[main_df["scenario"] == "S4_豆价+10%"].iloc[0]
# Cost^price = 0.10 × p_soy2024 × Σ ŷ_i^s B_i E[s_i]（对新增产量的价格支持近似）
sim4 = run_static(agents_main, P_MAIN, SCN["S4_豆价+10%"]["sc"], calib_offset=0.0, **SIM_KW)
soy_output = float(np.sum(agents_main["ey_soy"].values * agents_main["B"].values * sim4["agent_share"]))
cost_price = 0.10 * P_SOY0 * soy_output
pd.DataFrame([{"d_share_pp": s4["d_share_pp"], "soy_output_kg": soy_output,
               "price_support_cost": cost_price,
               "cost_per_pp_price": cost_price / s4["d_share_pp"] if s4["d_share_pp"] > 1e-3 else np.nan}]
             ).round(2).to_csv(f"{SDIR}/s4_price_support_cost.csv", index=False)

# ---------- 验证1：2024 年在场户样本内预测（§4.6-1） ----------
def hh_metrics(pred, obs):
    m = ~np.isnan(obs)
    pr, ob = pred[m], obs[m]
    brier = float(np.mean((pr - ob) ** 2))
    hit = float(np.mean((pr > 0.5) == (ob > 0.5)))
    base = float(ob.mean())
    pos, neg = pr[ob > 0.5], pr[ob <= 0.5]
    auc = float((pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean()) \
        if len(pos) and len(neg) else np.nan
    return {"n": int(m.sum()), "base_rate": base, "hit_rate": hit,
            "brier": brier, "brier_naive": base * (1 - base), "auc": auc}

sim_in = run_static(agents_2024, P_MAIN, SCN["S0_基准"]["sc"], calib_offset=0.0, **SIM_KW)
obs_in = agents_2024["plant_soy_init"].to_numpy(float)
val_in = hh_metrics(sim_in["agent_prob"], obs_in)
# 份额（面积加权）观测 vs 模拟
o_area = (agents_2024["s_init"] * agents_2024["B"]).sum() / agents_2024["B"].sum()
val_in["obs_share"] = float(o_area); val_in["sim_share"] = sim_in["agg"]["soy_share"]
val_in["obs_particip_nz"] = float(agents_2024[agents_2024["structural_zero"] == 0]["plant_soy_init"].mean())
val_in["sim_particip_nz"] = sim_in["agg"]["soy_particip"]
pd.DataFrame([val_in]).round(4).to_csv(f"{SDIR}/static_validation_2024.csv", index=False)
print("\n== 验证1：2024在场户样本内 ==\n", pd.DataFrame([val_in]).round(4).to_string(index=False))

# ---------- 验证2：2023→2024 留出（§4.6-2） ----------
h23, h24 = set(panel[panel["year"] == 2023]["hh_id"]), set(panel[panel["year"] == 2024]["hh_id"])
both = h23 & h24
p23 = panel[(panel["year"] == 2023) & panel["hh_id"].isin(both)].copy()
p23["state_year"] = 2023
ag23 = prep_agents(p23)
sim_ho = run_static(ag23, P_MAIN, SCN["S0_基准"]["sc"], calib_offset=0.0, **SIM_KW)
obs24 = panel[panel["year"] == 2024].set_index("hh_id")
obs_y = ag23["hh_id"].map(obs24["plant_soy"]).to_numpy(float)
val_ho = hh_metrics(sim_ho["agent_prob"], obs_y)
# 分组（含县）观测 vs 模拟
grp_rows = [{"group": "双年在场户合计", "n": len(ag23),
             "obs_particip": panel[(panel["year"] == 2024) & panel["hh_id"].isin(both) &
                                   (panel["county_name"] != "双城区")]["plant_soy"].mean(),
             "sim_particip": sim_ho["agg"]["soy_particip"],
             "obs_share": obs24.loc[obs24.index.isin(both)].eval("area_soy").sum() /
                          obs24.loc[obs24.index.isin(both)].eval("B").sum(),
             "sim_share": sim_ho["agg"]["soy_share"]}]
for cty in ["桦南县", "甘南县", "双城区"]:
    o = obs24[(obs24.index.isin(both)) & (obs24["county_name"] == cty)]
    if len(o) == 0 or cty not in sim_ho["per_county"]:
        continue
    grp_rows.append({"group": cty, "n": len(o), "obs_particip": o["plant_soy"].mean(),
                     "sim_particip": sim_ho["per_county"][cty]["particip"],
                     "obs_share": o["area_soy"].sum() / o["B"].sum(),
                     "sim_share": sim_ho["per_county"][cty]["soy_share"]})
pd.DataFrame([val_ho]).round(4).to_csv(f"{SDIR}/static_validation_holdout.csv", index=False)
grp = pd.DataFrame(grp_rows).round(3)
grp.to_csv(f"{SDIR}/static_validation_groups.csv", index=False)
print("\n== 验证2：2023→2024留出（户级） ==\n", pd.DataFrame([val_ho]).round(4).to_string(index=False))
print("\n== 县分组 ==\n", grp.to_string(index=False))

# ---------- 图（§5.1） ----------
fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
d = main_df.set_index("scenario")
order = list(SCN.keys())
labels = [s.replace("_", " ") for s in order]
x = np.arange(len(order))
sh = d.loc[order, "soy_share"].values * 100
lo = d.loc[order, "soy_share_lo"].values * 100
hi = d.loc[order, "soy_share_hi"].values * 100
ax[0].bar(x, sh, color="#4C72B0", alpha=0.85)
ax[0].errorbar(x, sh, yerr=[sh - lo, hi - sh], fmt="none", ecolor="k", capsize=3, lw=0.8)
ax[0].set_xticks(x); ax[0].set_xticklabels(labels, rotation=30, ha="right", fontsize=7)
ax[0].set_ylabel("大豆面积份额（%）"); ax[0].set_title("(a) 情景大豆份额（2024环境，参数区间）")
fisc = d.loc[order, "fiscal"].values / 1e4
ax[1].bar(x, fisc, color="#C44E52", alpha=0.85)
ax[1].set_xticks(x); ax[1].set_xticklabels(labels, rotation=30, ha="right", fontsize=7)
ax[1].set_ylabel("样本财政支出（万元）"); ax[1].set_title("(b) 财政成本")
plt.tight_layout(); plt.savefig(f"{OUT}/figures/fig_static_scenarios.png", dpi=200); plt.close()

# ---------- 报告 ----------
rep = ["# Phase 4（静态）反事实主体仿真报告\n",
       f"- 基年环境: p=({P_CORN0:.2f},{P_SOY0:.2f}), c=({C_CORN0:.0f},{C_SOY0:.0f}), "
       f"sub=({SUB_CORN0:.0f},{SUB_SOY0:.0f}); n_mc={SIM_KW['n_mc']}",
       f"- 主体池: last-obs {len(agents_main)} / 2024-only {len(agents_2024)} / 连续≥3年 {len(agents_bal)}",
       f"- 校准偏移(附录): {CAL_MAIN:.3f}; 观测2024参与率(非双城)={obs24_part:.3f}\n",
       "## 主体状态年份分布\n", syd.to_string(index=False),
       "\n\n## 静态情景（主线，未校准）\n",
       main_df[["scenario", "soy_particip", "soy_share", "d_share_pp", "d_fiscal", "cost_per_pp"]]
       .round(4).to_string(index=False),
       "\n\n## 静态情景（Wooldridge平行）\n",
       wool_df[["scenario", "soy_particip", "soy_share", "d_share_pp", "cost_per_pp"]]
       .round(4).to_string(index=False),
       "\n\n## 轮作补贴口径对照\n", rot_df.to_string(index=False),
       "\n\n## 验证1（2024在场户样本内）\n", pd.DataFrame([val_in]).round(4).to_string(index=False),
       "\n\n## 验证2（2023→2024留出，户级）\n", pd.DataFrame([val_ho]).round(4).to_string(index=False),
       "\n\n## 县分组验证\n", grp.to_string(index=False)]
with open(f"{OUT}/logs/phase4_static_report.md", "w") as f:
    f.write("\n".join(rep))
print("\ndone 04_static")
