"""
04_simulate.py — ABM 校准、验证与政策情景模拟（审阅修订版）
P12: σ_a=Wooldridge-RE估计值, σ_macro=年份效应样本SD, δ_rot/δ_rep敏感性网格
P6-4: 2024回测只在2023-2024双年在场户上做（同人群对比）
P7:  份额生成器对齐非条件分数logit
平行仿真：pooled(dpi_base)主线 + Wooldridge装置系数（状态依赖净化口径）
输出：output/scenarios/*.csv, output/figures/*.png, output/logs/phase4_report.md
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
from abm import load_params, run_scenario, make_scenario

OUT = os.path.join(BASE, "output")
os.makedirs(f"{OUT}/scenarios", exist_ok=True)
os.makedirs(f"{OUT}/figures", exist_ok=True)
for f in ["/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=f).get_name()
plt.rcParams["axes.unicode_minus"] = False

RAWP = load_params(f"{OUT}/params/behavior_params.json")
panel = pd.read_csv(f"{OUT}/panel_analysis.csv")
panel = panel[panel["village"].notna()].copy()
ptab = pd.read_csv(f"{OUT}/params/price_table.csv")
ctab = pd.read_csv(f"{OUT}/params/cost_table.csv")

# ---------- 经济环境（基年=2024实现值，2024=不变价基准年） ----------
def med(tab, val, yr, cr):
    return float(tab[(tab["year"] == yr) & (tab["crop"] == cr)][val].median())

P_CORN0, P_SOY0 = med(ptab, "price", 2024, "corn"), med(ptab, "price", 2024, "soy")
C_CORN0, C_SOY0 = med(ctab, "cost_mu", 2024, "corn"), med(ctab, "cost_mu", 2024, "soy")
SUB_CORN0, SUB_SOY0 = 20.0, 350.0
ECON = {"cost_per_mu": {"corn": C_CORN0, "soy": C_SOY0}, "delta_rot": 0.05, "delta_rep": 0.05}

# ---------- 随机结构参数（P12：改读估计值） ----------
SIGMA_A = RAWP["participation_wooldridge"].get("sigma_a_RE") or 0.5
if not np.isfinite(SIGMA_A):
    SIGMA_A = 0.5
yr_fe = [v for k, v in RAWP["participation"]["coef"].items() if k.startswith("C(yr)[T.")]
SIGMA_MACRO = float(np.std([0.0] + yr_fe, ddof=1)) if yr_fe else 0.3
print(f"σ_a(RE估计)={SIGMA_A:.3f}, σ_macro(年FE SD)={SIGMA_MACRO:.3f}")

def mk_params(part_key):
    P = {"participation": RAWP[part_key], "share": RAWP["share_unconditional"], "econ": ECON}
    return P

# ---------- Agent 群体 ----------
panel = panel.sort_values(["hh_id", "year"])
last = panel.groupby("hh_id").tail(1).copy()
STATIC = ["head_age10", "head_edu", "head_male", "head_health", "labor_n", "offfarm_n",
          "wage_share", "rentin_d", "ln_asset", "insurance", "internet", "head_train_agr",
          "v_coop_n", "logB"]
for c in STATIC:
    last[c] = last[c].fillna(panel[c].median())
# Wooldridge装置的 agent 常量：首期状态与户内均值。
# 动态覆盖 participation_wooldridge 系数向量中【全部】 *_bar 项（含新增的
# head_age10/edu/health/labor_n 均值），否则 _linpred 会静默丢弃这些均值项。
first = panel.groupby("hh_id").first()
W_BARS = [v[:-4] for v in RAWP["participation_wooldridge"]["vcov_vars"] if v.endswith("_bar")]
def _bar_src(v):
    return "peer_lag" if v == "peer_lag0" else v  # peer_lag0 的源列为 peer_lag
hh_bar_mean = {v: panel.groupby("hh_id")[_bar_src(v)].mean()
               for v in W_BARS if _bar_src(v) in panel.columns}
def add_bars(df):
    df["D_init"] = df["hh_id"].map(first["plant_soy"]).astype(float)
    for v in W_BARS:
        col = "bar_" + v
        if v in hh_bar_mean:
            df[col] = df["hh_id"].map(hh_bar_mean[v])
            fill = df[col].median() if df[col].notna().any() else 0.0
            df[col] = df[col].fillna(fill)
        else:
            df[col] = 0.0
    return df
last = add_bars(last)

cs = pd.read_csv(f"{OUT}/panel_crop_long.csv")
cs = cs[cs["crop"].isin(["corn", "soy"])].dropna(subset=["yield"])
cty_med = cs.groupby(["county_name", "crop"])["yield"].median()
prov_med = cs.groupby("crop")["yield"].median()
hh_hist = cs.groupby(["hh_id", "crop"])["yield"].agg(["sum", "count"])

def ey(hh, cty, crop):
    prior = cty_med.get((cty, crop), prov_med[crop])
    if (hh, crop) in hh_hist.index:
        s_, n_ = hh_hist.loc[(hh, crop)]
        return (s_ + 2 * prior) / (n_ + 2)
    return prior

def prep_agents(df):
    df = df.copy()
    df["ey_corn"] = [ey(h, c, "corn") for h, c in zip(df["hh_id"], df["county_name"])]
    df["ey_soy"] = [ey(h, c, "soy") for h, c in zip(df["hh_id"], df["county_name"])]
    df["s_init"] = df["s"]
    df["plant_soy_init"] = df["plant_soy"].astype(float)
    df["structural_zero"] = (df["county_name"] == "双城区").astype(int)
    cols = (["hh_id", "county_name", "village", "B", "ey_corn", "ey_soy", "s_init",
             "plant_soy_init", "structural_zero", "D_init"]
            + ["bar_" + v for v in W_BARS] + STATIC)
    return df[cols].reset_index(drop=True)

agents = prep_agents(last)
print(f"agents: {len(agents)}, 双城 {int(agents['structural_zero'].sum())}")
agents.to_csv(f"{OUT}/scenarios/agents.csv", index=False)

obs24 = panel[panel["year"] == 2024]
obs_part = obs24[obs24["county_name"] != "双城区"]["plant_soy"].mean()
SIM_KW = dict(n_mc=300, sigma_a=SIGMA_A, sigma_macro=SIGMA_MACRO)

def calibrate(P, ag, seed=1):
    sc = make_scenario([2024], P_CORN0, P_SOY0, SUB_CORN0, SUB_SOY0, 0.0)
    lo, hi = -4.0, 4.0
    for _ in range(18):
        mid = (lo + hi) / 2
        v = run_scenario(ag, P, sc, seed=seed, calib_offset=mid, **SIM_KW)["agg"]["soy_particip"][0]
        if v < obs_part:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

P_MAIN = mk_params("participation")
P_W = mk_params("participation_wooldridge")
CAL_MAIN = calibrate(P_MAIN, agents)
CAL_W = calibrate(P_W, agents)
print(f"calib: main={CAL_MAIN:.3f}, wooldridge={CAL_W:.3f}")

# ---------- 验证1：2023→2024 同人群回测（P6-4） ----------
h23 = set(panel[panel["year"] == 2023]["hh_id"])
h24 = set(obs24["hh_id"])
both = h23 & h24
p23 = panel[(panel["year"] == 2023) & panel["hh_id"].isin(both)].copy()
for c in STATIC:
    p23[c] = p23[c].fillna(panel[c].median())
p23 = add_bars(p23)
ag23 = prep_agents(p23)
sc24 = make_scenario([2024], P_CORN0, P_SOY0, SUB_CORN0, SUB_SOY0, 0.0)
rv = run_scenario(ag23, P_MAIN, sc24, seed=7, calib_offset=CAL_MAIN, **SIM_KW)
obs_b = obs24[obs24["hh_id"].isin(both)]
val_rows = [{"group": "双年在场户合计", "n": len(obs_b),
             "obs_particip": obs_b[obs_b["county_name"] != "双城区"]["plant_soy"].mean(),
             "sim_particip": rv["agg"]["soy_particip"][0],
             "obs_share": obs_b["area_soy"].sum() / obs_b["B"].sum(),
             "sim_share": rv["agg"]["soy_share"][0]}]
for cty in ["桦南县", "甘南县", "双城区"]:
    o = obs_b[obs_b["county_name"] == cty]
    if len(o) == 0 or cty not in rv["per_county"]:
        continue
    val_rows.append({"group": cty, "n": len(o), "obs_particip": o["plant_soy"].mean(),
                     "sim_particip": rv["per_county"][cty]["particip"][0],
                     "obs_share": o["area_soy"].sum() / o["B"].sum(),
                     "sim_share": rv["per_county"][cty]["soy_share"][0]})
val = pd.DataFrame(val_rows).round(3)
print(val.to_string(index=False))
val.to_csv(f"{OUT}/scenarios/validation_2024.csv", index=False)

# 户级预测精度（P6-4补：命中率/Brier/AUC，同人群82户）
pr = np.asarray(rv["agent_prob_last"], float)
obs_y = ag23["hh_id"].map(obs24.set_index("hh_id")["plant_soy"]).to_numpy(float)
m = ~np.isnan(obs_y)
pr_m, obs_m = pr[m], obs_y[m]
brier = float(np.mean((pr_m - obs_m) ** 2))
hit = float(np.mean((pr_m > 0.5) == (obs_m > 0.5)))
base_rate = float(obs_m.mean())
# AUC（Mann-Whitney）
pos, neg = pr_m[obs_m > 0.5], pr_m[obs_m <= 0.5]
if len(pos) and len(neg):
    auc = float((pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean())
else:
    auc = np.nan
vm = pd.DataFrame([{"n": int(m.sum()), "base_rate": base_rate, "hit_rate": hit,
                    "brier": brier, "brier_naive": base_rate * (1 - base_rate), "auc": auc}]).round(4)
vm.to_csv(f"{OUT}/scenarios/validation_hhlevel.csv", index=False)
print("户级回测:", vm.to_string(index=False))

# ---------- 情景 2025–2030（主线 + Wooldridge平行） ----------
YEARS = list(range(2025, 2031))
SCN = {
    "S0_基线": make_scenario(YEARS, P_CORN0, P_SOY0, SUB_CORN0, SUB_SOY0, 0.0),
    "S1_大豆补贴+50%": make_scenario(YEARS, P_CORN0, P_SOY0, SUB_CORN0, SUB_SOY0 * 1.5, 0.0),
    "S2_大豆补贴+100元": make_scenario(YEARS, P_CORN0, P_SOY0, SUB_CORN0, SUB_SOY0 + 100, 0.0),
    "S3_轮作补贴150元": make_scenario(YEARS, P_CORN0, P_SOY0, SUB_CORN0, SUB_SOY0, 150.0),
    "S4_豆价+10%": make_scenario(YEARS, P_CORN0, P_SOY0 * 1.10, SUB_CORN0, SUB_SOY0, 0.0),
    "S5_取消玉米补贴": make_scenario(YEARS, P_CORN0, P_SOY0, 0.0, SUB_SOY0, 0.0),
}
res, rows = {}, []
for name, sc in SCN.items():
    for tag, P_, cal in [("main", P_MAIN, CAL_MAIN), ("wooldridge", P_W, CAL_W)]:
        r = run_scenario(agents, P_, sc, seed=42, calib_offset=cal, **SIM_KW)
        if tag == "main":
            res[name] = r
        a = pd.DataFrame(r["agg"]); a["scenario"] = name; a["param_set"] = tag
        rows.append(a)
allr = pd.concat(rows, ignore_index=True)
allr.to_csv(f"{OUT}/scenarios/scenario_results.csv", index=False)

def terminal(tag):
    t = allr[(allr["year"] == 2030) & (allr["param_set"] == tag)][
        ["scenario", "soy_particip", "soy_share", "soy_share_lo", "soy_share_hi", "fiscal"]].copy()
    b_f = float(t[t["scenario"] == "S0_基线"]["fiscal"].iloc[0])
    b_s = float(t[t["scenario"] == "S0_基线"]["soy_share"].iloc[0])
    t["d_share"] = t["soy_share"] - b_s
    t["d_fiscal"] = t["fiscal"] - b_f
    t["cost_per_pp"] = np.where(t["d_share"] > 1e-4, t["d_fiscal"] / (t["d_share"] * 100), np.nan)
    return t

term = terminal("main")
termW = terminal("wooldridge")
print("== 2030终期（main） =="); print(term.round(4).to_string(index=False))
print("== 2030终期（Wooldridge平行） =="); print(termW.round(4).to_string(index=False))
term.round(4).to_csv(f"{OUT}/scenarios/terminal_2030.csv", index=False)
termW.round(4).to_csv(f"{OUT}/scenarios/terminal_2030_wooldridge.csv", index=False)

# ---------- 验证2：单调性 ----------
mono = []
for extra in [0, 100, 200, 300, 400, 500]:
    sc = make_scenario(YEARS, P_CORN0, P_SOY0, SUB_CORN0, SUB_SOY0 + extra, 0.0)
    r = run_scenario(agents, P_MAIN, sc, seed=42, calib_offset=CAL_MAIN, **SIM_KW)
    mono.append({"extra_sub": extra, "share_2030": r["agg"]["soy_share"][-1],
                 "particip_2030": r["agg"]["soy_particip"][-1],
                 "fiscal_2030": r["agg"]["fiscal"][-1]})
mono = pd.DataFrame(mono)
mono.to_csv(f"{OUT}/scenarios/monotonicity.csv", index=False)
assert mono["share_2030"].is_monotonic_increasing, "单调性验证失败"
print(mono.round(4).to_string(index=False))

# ---------- δ 敏感性（P12） ----------
sens = []
for d_ in [0.0, 0.05, 0.10]:
    ECON2 = dict(ECON, delta_rot=d_, delta_rep=d_)
    P2 = {"participation": RAWP["participation"], "share": RAWP["share_unconditional"], "econ": ECON2}
    for nm in ["S0_基线", "S2_大豆补贴+100元"]:
        r = run_scenario(agents, P2, SCN[nm], seed=42, calib_offset=CAL_MAIN, **SIM_KW)
        sens.append({"delta": d_, "scenario": nm, "share_2030": r["agg"]["soy_share"][-1]})
sens = pd.DataFrame(sens)
sens.to_csv(f"{OUT}/scenarios/delta_sensitivity.csv", index=False)
print(sens.round(4).to_string(index=False))

# ---------- 目标反解 ----------
def share_at(sub_soy):
    sc = make_scenario(YEARS, P_CORN0, P_SOY0, SUB_CORN0, sub_soy, 0.0)
    r = run_scenario(agents, P_MAIN, sc, seed=42, calib_offset=CAL_MAIN, **SIM_KW)
    return r["agg"]["soy_share"][-1], r["agg"]["fiscal"][-1]

inv = []
for tgt in [0.10, 0.15, 0.20]:
    lo_s, hi_s = 0.0, 2500.0
    if share_at(hi_s)[0] < tgt:
        inv.append({"target": tgt, "sub_soy": np.nan, "fiscal": np.nan})
        continue
    for _ in range(14):
        mid_s = (lo_s + hi_s) / 2
        shv, fis = share_at(mid_s)
        if shv < tgt:
            lo_s = mid_s
        else:
            hi_s = mid_s
    inv.append({"target": tgt, "sub_soy": (lo_s + hi_s) / 2, "fiscal": fis})
inv = pd.DataFrame(inv)
inv.to_csv(f"{OUT}/scenarios/target_inversion.csv", index=False)
print(inv.round(2).to_string(index=False))

# ---------- 图 ----------
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for name, r in res.items():
    a = r["agg"]
    ax[0].plot(a["year"], np.array(a["soy_share"]) * 100, marker="o", ms=3, label=name.replace("_", " "))
    ax[1].plot(a["year"], np.array(a["fiscal"]) / 1e4, marker="o", ms=3)
a0 = res["S0_基线"]["agg"]
ax[0].fill_between(a0["year"], np.array(a0["soy_share_lo"]) * 100, np.array(a0["soy_share_hi"]) * 100, alpha=0.15)
ax[0].set_ylabel("大豆面积份额（%）"); ax[0].set_title("(a) 政策情景下大豆份额路径")
ax[1].set_ylabel("样本财政支出（万元）"); ax[1].set_title("(b) 财政成本")
ax[0].legend(fontsize=7)
plt.tight_layout(); plt.savefig(f"{OUT}/figures/fig_scenarios.png", dpi=200); plt.close()

fig, ax = plt.subplots(figsize=(5.5, 4.2))
ax.plot(mono["extra_sub"] + SUB_SOY0, mono["share_2030"] * 100, marker="o")
for tgt, ss in zip(inv["target"], inv["sub_soy"]):
    if not np.isnan(ss):
        ax.axhline(tgt * 100, ls=":", c="gray", lw=0.8)
        ax.axvline(ss, ls=":", c="gray", lw=0.8)
        ax.annotate(f"{tgt:.0%}→{ss:.0f}元/亩", (ss, tgt * 100), fontsize=8,
                    textcoords="offset points", xytext=(5, -10))
ax.set_xlabel("大豆生产者补贴（元/亩）"); ax.set_ylabel("2030年大豆面积份额（%）")
ax.set_title("补贴—份额响应曲线与目标反解")
plt.tight_layout(); plt.savefig(f"{OUT}/figures/fig_inversion.png", dpi=200); plt.close()

# ---------- 报告 ----------
rep = ["# Phase 4 ABM 校准验证与情景模拟（修订版）\n",
       f"- σ_a={SIGMA_A:.3f}(RE估计), σ_macro={SIGMA_MACRO:.3f}(年FE SD), n_mc={SIM_KW['n_mc']}",
       f"- calib_offset: main={CAL_MAIN:.3f}, wooldridge={CAL_W:.3f}",
       f"- 基年环境: p=({P_CORN0:.2f},{P_SOY0:.2f}), c=({C_CORN0:.0f},{C_SOY0:.0f}), sub=({SUB_CORN0:.0f},{SUB_SOY0:.0f})\n",
       "## 同人群回测（2023→2024双年在场户）\n", val.to_string(index=False),
       "\n\n## 2030终期（main）\n", term.round(4).to_string(index=False),
       "\n\n## 2030终期（Wooldridge平行）\n", termW.round(4).to_string(index=False),
       "\n\n## 单调性\n", mono.round(4).to_string(index=False),
       "\n\n## δ敏感性\n", sens.round(4).to_string(index=False),
       "\n\n## 目标反解\n", inv.round(2).to_string(index=False)]
with open(f"{OUT}/logs/phase4_report.md", "w") as f:
    f.write("\n".join(rep))
print("done 04")
