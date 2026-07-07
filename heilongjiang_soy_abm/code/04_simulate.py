"""
04_simulate.py — ABM 校准、验证与政策情景模拟
(1) agent 群体：每户最近一次观测（含2024状态），双城=结构性零参与
(2) 校准：calib_offset 使基年(2024)模拟参与率匹配观测（桦南+甘南）
(3) 验证：2023状态出发回测2024分县参与率/份额；补贴单调性
(4) 情景 S0–S5（2025–2030）+ 财政成本 + 目标反解（10/15/20%份额）
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

# 中文字体
for f in ["/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=f).get_name()
        break
plt.rcParams["axes.unicode_minus"] = False

P = load_params(f"{OUT}/params/behavior_params.json")
panel = pd.read_csv(f"{OUT}/panel_analysis.csv")
ptab = pd.read_csv(f"{OUT}/params/price_table.csv")
ctab = pd.read_csv(f"{OUT}/params/cost_table.csv")

# ---------- 经济环境参数（基年=2024 实现值） ----------
def med(tab, val, yr, cr):
    r = tab[(tab["year"] == yr) & (tab["crop"] == cr)]
    return float(r[val].median())

P_CORN0, P_SOY0 = med(ptab, "price", 2024, "corn"), med(ptab, "price", 2024, "soy")
C_CORN0, C_SOY0 = med(ctab, "cost_mu", 2024, "corn"), med(ctab, "cost_mu", 2024, "soy")
SUB_CORN0, SUB_SOY0 = 20.0, 350.0
P["econ"] = {"cost_per_mu": {"corn": C_CORN0, "soy": C_SOY0},
             "delta_rot": 0.05, "delta_rep": 0.05}
print(f"基年环境: p_corn={P_CORN0:.2f} p_soy={P_SOY0:.2f} c_corn={C_CORN0:.0f} c_soy={C_SOY0:.0f}")

# ---------- Agent 群体：每户最近观测 ----------
panel = panel.sort_values(["hh_id", "year"])
last = panel.groupby("hh_id").tail(1).copy()
med_fill = {c: last[c].median() for c in ["head_age10", "head_edu", "labor_n"]}
for c, v in med_fill.items():
    last[c] = last[c].fillna(v)

# 户潜在单产：户历史均值向县中位数收缩（K=2），无历史用县中位数
cs = pd.read_csv(f"{OUT}/panel_crop_long.csv")
cs = cs[cs["crop"].isin(["corn", "soy"])].dropna(subset=["yield"])
cty_med = cs.groupby(["county_name", "crop"])["yield"].median()
prov_med = cs.groupby("crop")["yield"].median()
hh_hist = cs.groupby(["hh_id", "crop"])["yield"].agg(["sum", "count"])

def ey(hh, cty, crop):
    prior = cty_med.get((cty, crop), prov_med[crop])
    if (hh, crop) in hh_hist.index:
        s, n = hh_hist.loc[(hh, crop)]
        return (s + 2 * prior) / (n + 2)
    return prior

last["ey_corn"] = [ey(h, c, "corn") for h, c in zip(last["hh_id"], last["county_name"])]
last["ey_soy"] = [ey(h, c, "soy") for h, c in zip(last["hh_id"], last["county_name"])]
last["s_init"] = last["s"]
last["plant_soy_init"] = last["plant_soy"].astype(float)
last["structural_zero"] = (last["county_name"] == "双城区").astype(int)
agents = last[["hh_id", "county_name", "village", "B", "logB", "head_age10", "head_edu",
               "labor_n", "ey_corn", "ey_soy", "s_init", "plant_soy_init", "structural_zero"]].reset_index(drop=True)
print(f"agents: {len(agents)}, 双城 {agents['structural_zero'].sum()}")
agents.to_csv(f"{OUT}/scenarios/agents.csv", index=False)

# 观测基准（2024，非双城参与率 & 全样本面积份额）
obs24 = panel[panel["year"] == 2024]
obs_part = obs24[obs24["county_name"] != "双城区"]["plant_soy"].mean()
obs_share = obs24["area_soy"].sum() / obs24["B"].sum()
print(f"观测2024: 参与率(非双城)={obs_part:.3f}, 面积份额={obs_share:.3f}")

SIM_KW = dict(n_mc=300, sigma_a=0.5, sigma_macro=0.3)

def one_year_part(offset, seed=1):
    sc = make_scenario([2024], P_CORN0, P_SOY0, SUB_CORN0, SUB_SOY0, 0.0)
    r = run_scenario(agents, P, sc, seed=seed, calib_offset=offset, **SIM_KW)
    return r["agg"]["soy_particip"][0], r

# ---------- 校准 calib_offset（二分法） ----------
lo, hi = -3.0, 3.0
for _ in range(18):
    mid = (lo + hi) / 2
    v, _ = one_year_part(mid)
    if v < obs_part:
        lo = mid
    else:
        hi = mid
CALIB = (lo + hi) / 2
v0, r0 = one_year_part(CALIB)
print(f"calib_offset={CALIB:.3f}, 模拟基年参与率={v0:.3f} (目标 {obs_part:.3f})")

# ---------- 验证1：2023状态出发回测2024 ----------
p23 = panel[panel["year"] == 2023].copy()
for c, v in med_fill.items():
    p23[c] = p23[c].fillna(v)
p23["ey_corn"] = [ey(h, c, "corn") for h, c in zip(p23["hh_id"], p23["county_name"])]
p23["ey_soy"] = [ey(h, c, "soy") for h, c in zip(p23["hh_id"], p23["county_name"])]
p23["s_init"] = p23["s"]; p23["plant_soy_init"] = p23["plant_soy"].astype(float)
p23["structural_zero"] = (p23["county_name"] == "双城区").astype(int)
ag23 = p23[agents.columns].reset_index(drop=True)
sc24 = make_scenario([2024], P_CORN0, P_SOY0, SUB_CORN0, SUB_SOY0, 0.0)
rv = run_scenario(ag23, P, sc24, seed=7, calib_offset=CALIB, **SIM_KW)
val_rows = []
for cty in ["桦南县", "甘南县", "双城区"]:
    o = obs24[obs24["county_name"] == cty]
    sim_p = rv["per_county"][cty]["particip"][0]
    sim_s = rv["per_county"][cty]["soy_share"][0]
    val_rows.append({"county": cty, "obs_particip": o["plant_soy"].mean(),
                     "sim_particip": sim_p, "obs_share": o["area_soy"].sum() / o["B"].sum(),
                     "sim_share": sim_s, "n_obs": len(o)})
val = pd.DataFrame(val_rows).round(3)
print(val.to_string(index=False))
val.to_csv(f"{OUT}/scenarios/validation_2024.csv", index=False)

# ---------- 情景 2025–2030 ----------
YEARS = list(range(2025, 2031))
n = len(YEARS)
SCN = {
    "S0_基线": make_scenario(YEARS, P_CORN0, P_SOY0, SUB_CORN0, SUB_SOY0, 0.0),
    "S1_大豆补贴+50%": make_scenario(YEARS, P_CORN0, P_SOY0, SUB_CORN0, SUB_SOY0 * 1.5, 0.0),
    "S2_大豆补贴+100元": make_scenario(YEARS, P_CORN0, P_SOY0, SUB_CORN0, SUB_SOY0 + 100, 0.0),
    "S3_轮作补贴150元": make_scenario(YEARS, P_CORN0, P_SOY0, SUB_CORN0, SUB_SOY0, 150.0),
    "S4_豆价+10%": make_scenario(YEARS, P_CORN0, P_SOY0 * 1.10, SUB_CORN0, SUB_SOY0, 0.0),
    "S5_取消玉米补贴": make_scenario(YEARS, P_CORN0, P_SOY0, 0.0, SUB_SOY0, 0.0),
}
res = {}
rows = []
for name, sc in SCN.items():
    r = run_scenario(agents, P, sc, seed=42, calib_offset=CALIB, **SIM_KW)
    res[name] = r
    a = pd.DataFrame(r["agg"]); a["scenario"] = name
    rows.append(a)
allr = pd.concat(rows, ignore_index=True)
allr.to_csv(f"{OUT}/scenarios/scenario_results.csv", index=False)
term = allr[allr["year"] == 2030][["scenario", "soy_particip", "soy_share", "soy_share_lo", "soy_share_hi", "fiscal"]]
base_fis = float(term[term["scenario"] == "S0_基线"]["fiscal"].iloc[0])
base_sh = float(term[term["scenario"] == "S0_基线"]["soy_share"].iloc[0])
term = term.assign(d_share=lambda d: d["soy_share"] - base_sh,
                   d_fiscal=lambda d: d["fiscal"] - base_fis)
term["cost_per_pp"] = np.where(term["d_share"] > 1e-4, term["d_fiscal"] / (term["d_share"] * 100), np.nan)
print(term.round(4).to_string(index=False))
term.round(4).to_csv(f"{OUT}/scenarios/terminal_2030.csv", index=False)

# ---------- 验证2：补贴单调性 ----------
mono = []
for extra in [0, 100, 200, 300, 400, 500]:
    sc = make_scenario(YEARS, P_CORN0, P_SOY0, SUB_CORN0, SUB_SOY0 + extra, 0.0)
    r = run_scenario(agents, P, sc, seed=42, calib_offset=CALIB, **SIM_KW)
    mono.append({"extra_sub": extra, "share_2030": r["agg"]["soy_share"][-1],
                 "particip_2030": r["agg"]["soy_particip"][-1],
                 "fiscal_2030": r["agg"]["fiscal"][-1]})
mono = pd.DataFrame(mono)
print(mono.round(4).to_string(index=False))
mono.to_csv(f"{OUT}/scenarios/monotonicity.csv", index=False)
assert mono["share_2030"].is_monotonic_increasing, "单调性验证失败"

# ---------- 目标反解：2030 份额 10/15/20% 所需大豆补贴 ----------
def share_at(sub_soy):
    sc = make_scenario(YEARS, P_CORN0, P_SOY0, SUB_CORN0, sub_soy, 0.0)
    r = run_scenario(agents, P, sc, seed=42, calib_offset=CALIB, **SIM_KW)
    return r["agg"]["soy_share"][-1], r["agg"]["fiscal"][-1]

inv = []
for tgt in [0.10, 0.15, 0.20]:
    lo_s, hi_s = 0.0, 2500.0
    sh_hi, _ = share_at(hi_s)
    if sh_hi < tgt:
        inv.append({"target": tgt, "sub_soy": np.nan, "fiscal": np.nan}); continue
    for _ in range(14):
        mid_s = (lo_s + hi_s) / 2
        shv, fis = share_at(mid_s)
        if shv < tgt:
            lo_s = mid_s
        else:
            hi_s = mid_s
    inv.append({"target": tgt, "sub_soy": (lo_s + hi_s) / 2, "fiscal": fis})
inv = pd.DataFrame(inv)
print(inv.round(2).to_string(index=False))
inv.to_csv(f"{OUT}/scenarios/target_inversion.csv", index=False)

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
rep = ["# Phase 4 ABM 校准验证与情景模拟\n",
       f"- 基年环境: p_corn={P_CORN0:.2f}, p_soy={P_SOY0:.2f}, cost_corn={C_CORN0:.0f}, cost_soy={C_SOY0:.0f}, sub=({SUB_CORN0:.0f},{SUB_SOY0:.0f})",
       f"- agents={len(agents)} (双城 {int(agents['structural_zero'].sum())} 结构零)；n_mc={SIM_KW['n_mc']}, sigma_a={SIM_KW['sigma_a']}, sigma_macro={SIM_KW['sigma_macro']}",
       f"- calib_offset={CALIB:.3f}；基年模拟参与率 {v0:.3f} vs 观测 {obs_part:.3f}\n",
       "## 留出验证（2023→2024 回测）\n", val.to_string(index=False),
       "\n\n## 2030 终期结果\n", term.round(4).to_string(index=False),
       "\n\n## 补贴单调性\n", mono.round(4).to_string(index=False),
       "\n\n## 目标反解\n", inv.round(2).to_string(index=False)]
with open(f"{OUT}/logs/phase4_report.md", "w") as f:
    f.write("\n".join(rep))
print("done")
