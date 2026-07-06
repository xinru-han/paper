
"""
08_policy_event_identification.py
Step 7 of the revision pipeline: policy-event price identification (review
Issue 1, remedy 4). Two well-documented trade-policy shocks provide exogenous
cross-province variation in landed price, exploited via a shift-share /
difference-in-differences design:

  1. US sorghum antidumping/countervailing duties: China opened an AD/CVD
     investigation on US sorghum in Feb 2018 and imposed provisional duties
     in Apr 2018 (2018Q2); duties were suspended by late 2018 amid the
     broader US-China trade truce (treated here as 2018Q2-2018Q3 the "shock"
     window).
  2. Australia barley antidumping/countervailing duties: China imposed
     80.5% combined AD/CVD on Australian barley in May 2020 (2020Q2),
     lifted in August 2023 (2023Q3).

For each event, we compute each province's PRE-SHOCK (2017 base year)
exposure share -- i.e., the fraction of that province's sorghum (resp.
barley) import value sourced from the sanctioned country -- and interact it
with an event-time dummy in a province + year-quarter fixed-effects
regression of log quality-adjusted price on the interaction term. A
significant positive coefficient means provinces more exposed to the
sanctioned source saw a larger price increase after the shock -- direct
evidence that price variation in our estimation sample has a genuine
exogenous (policy-driven) component, addressing the review's concern that
Gamma may be estimated from measurement error / imputation-driven "price"
variation rather than real price signal.

Both a single post-indicator DiD specification and a fully dynamic
event-study specification (exposure interacted with each relative-quarter
dummy) are estimated and saved.
"""
import glob
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

DATA_DIR = "/root/data/Paper/饲料进口弹性/data"
PROJ = "/root/data/Paper/饲料进口弹性/revision_2026"
CKPT_DIR = f"{PROJ}/checkpoints"
OUT_DIR = f"{PROJ}/output"

CODE8_MAP = {"10039000": "barley", "10031000": "barley", "10059000": "corn", "10051000": "corn",
             "10079000": "sorghum", "10071000": "sorghum", "10049000": "oats", "10041000": "oats",
             "07141020": "cassava"}

SORGHUM_EVENT_START = "2018Q2"
SORGHUM_EVENT_END = "2018Q4"     # exclusive; shock window = 2018Q2-2018Q3
BARLEY_EVENT_START = "2020Q2"
BARLEY_EVENT_END = "2023Q3"      # exclusive; shock window = 2020Q2-2023Q2


def year_quarter_to_num(yq):
    y, q = int(yq[:4]), int(yq[5:])
    return y * 4 + q


def load_raw_feed():
    files = sorted(glob.glob(f"{DATA_DIR}/*-feed.csv"))
    dfs = [pd.read_csv(fp, dtype=str) for fp in files]
    raw = pd.concat(dfs, ignore_index=True)
    raw["code8"] = raw["商品编码"].astype(str).str.zfill(8)
    raw["product"] = raw["code8"].map(CODE8_MAP)
    raw = raw[raw["进出口类型"] == "进口"].copy()
    raw = raw[raw["product"].isin(["sorghum", "barley"])].copy()
    raw["year"] = raw["日期"].str[:4].astype(int)
    raw["month"] = raw["日期"].str[5:7].astype(int)
    raw["quarter"] = ((raw["month"] - 1) // 3) + 1
    raw["year_quarter"] = raw["year"].astype(str) + "Q" + raw["quarter"].astype(str)
    raw["val_usd"] = pd.to_numeric(raw["金额"], errors="coerce")
    raw = raw[(raw["year"] >= 2017) & (raw["year"] <= 2023)].copy()
    raw = raw.rename(columns={"地址": "province"})
    return raw


def compute_source_share(df, source_name, base_years=(2017,)):
    base = df[df["year"].isin(base_years)]
    prov_source = base[base["贸易伙伴名称"] == source_name].groupby("province")["val_usd"].sum()
    prov_total = base.groupby("province")["val_usd"].sum()
    return (prov_source / prov_total).fillna(0)


def build_price_exposure_panel(price_variants, product, source_share, event_start, event_end):
    pm = price_variants[(price_variants.price_measure == "completed") &
                         (price_variants["product"] == product)][
        ["province", "year_quarter", "log_price_final"]
    ].copy()
    pm["qnum"] = pm["year_quarter"].apply(year_quarter_to_num)
    start_n, end_n = year_quarter_to_num(event_start), year_quarter_to_num(event_end)
    pm["post_shock"] = ((pm["qnum"] >= start_n) & (pm["qnum"] < end_n)).astype(int)
    pm = pm.merge(source_share.rename("exposure_share").reset_index(), on="province", how="left")
    pm["exposure_share"] = pm["exposure_share"].fillna(0)
    pm["interaction"] = pm["post_shock"] * pm["exposure_share"]
    pm["q_rel"] = pm["qnum"] - start_n
    return pm


def fit_did(panel):
    model = smf.ols("log_price_final ~ interaction + C(province) + C(year_quarter)", data=panel).fit(
        cov_type="cluster", cov_kwds={"groups": panel["province"]}
    )
    return dict(coef=model.params.get("interaction"), se=model.bse.get("interaction"),
                t=model.tvalues.get("interaction"), p=model.pvalues.get("interaction"), n=int(model.nobs))


def fit_event_study(panel, q_min=-6, q_max=10):
    window = panel[(panel["q_rel"] >= q_min) & (panel["q_rel"] <= q_max)].copy()
    terms, colmap = [], {}
    for q in sorted(window["q_rel"].unique()):
        if q == -1:
            continue
        name = f"qm{abs(q)}" if q < 0 else f"qp{q}"
        window[name] = (window["q_rel"] == q).astype(int) * window["exposure_share"]
        terms.append(name)
        colmap[name] = q
    formula = "log_price_final ~ " + " + ".join(terms) + " + C(province) + C(year_quarter)"
    model = smf.ols(formula, data=window).fit(cov_type="cluster", cov_kwds={"groups": window["province"]})
    rows = []
    for name, q in sorted(colmap.items(), key=lambda x: x[1]):
        if name in model.params.index:
            rows.append(dict(q_rel=q, coef=model.params[name], se=model.bse[name], t=model.tvalues[name]))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    price_variants = pd.read_parquet(f"{CKPT_DIR}/price_variants.parquet")
    raw = load_raw_feed()

    sorghum = raw[raw["product"] == "sorghum"].copy()
    barley = raw[raw["product"] == "barley"].copy()
    sorghum_us_share = compute_source_share(sorghum, "美国")
    barley_au_share = compute_source_share(barley, "澳大利亚")

    sorghum_panel = build_price_exposure_panel(price_variants, "sorghum", sorghum_us_share,
                                                 SORGHUM_EVENT_START, SORGHUM_EVENT_END)
    barley_panel = build_price_exposure_panel(price_variants, "barley", barley_au_share,
                                                BARLEY_EVENT_START, BARLEY_EVENT_END)

    did_sorghum = fit_did(sorghum_panel)
    did_barley = fit_did(barley_panel)
    print("Sorghum DiD (US AD, 2018Q2-Q3):", did_sorghum)
    print("Barley DiD (Australia AD/CVD, 2020Q2-2023Q2):", did_barley)

    did_summary = pd.DataFrame([
        dict(event="sorghum_US_antidumping_2018", **did_sorghum),
        dict(event="barley_australia_ADCVD_2020_2023", **did_barley),
    ])
    did_summary.to_csv(f"{OUT_DIR}/policy_event_did_summary.csv", index=False)

    es_sorghum = fit_event_study(sorghum_panel)
    es_barley = fit_event_study(barley_panel)
    es_sorghum["event"] = "sorghum_US_antidumping_2018"
    es_barley["event"] = "barley_australia_ADCVD_2020"
    pd.concat([es_sorghum, es_barley], ignore_index=True).to_csv(
        f"{OUT_DIR}/policy_event_study_coefficients.csv", index=False
    )

    exposure_summary = pd.DataFrame({
        "province": sorghum_us_share.index,
        "sorghum_US_exposure_2017": sorghum_us_share.values,
    }).merge(pd.DataFrame({
        "province": barley_au_share.index,
        "barley_australia_exposure_2017": barley_au_share.values,
    }), on="province", how="outer")
    exposure_summary.to_csv(f"{OUT_DIR}/policy_exposure_shares_by_province.csv", index=False)

    print("\\nAll policy-event outputs saved to", OUT_DIR)
