
"""
03_merge_controls_build_wide.py
Merge quality-adjusted price variables (built separately in 04), livestock
production demand controls, and the Bartik instrument into the analysis-ready
wide panel used for SY probit + FIML AIDS/QUAIDS estimation.
"""
import numpy as np
import pandas as pd
from functools import reduce

PROJ = "/root/data/Paper/饲料进口弹性/revision_2026"
CKPT_DIR = f"{PROJ}/checkpoints"
LS_DIR = "/root/data/Paper/饲料进口弹性/畜产品产量"

FILES = {
    "pork": "猪肉产量万吨.csv",
    "beef": "牛肉产量万吨.csv",
    "mutton": "羊肉产量万吨.csv",
    "poultry_meat": "肉类产量万吨.csv",
    "eggs": "禽蛋产量万吨.csv",
    "milk": "牛奶产量万吨.csv",
}


def clean_ls(fname, varname):
    df = pd.read_csv(f"{LS_DIR}/{fname}", skiprows=2, encoding="utf-8")
    df.columns = [c.strip() for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains("Unnamed")]
    for c in df.columns:
        df[c] = df[c].astype(str).str.replace("\t", "").str.strip()
    df["year"] = pd.to_numeric(df["数据时间"].str.extract(r"(\d{4})")[0], errors="coerce")
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)
    df = df.drop(columns=["数据时间"])
    long = df.melt(id_vars="year", var_name="province", value_name=varname)
    long[varname] = pd.to_numeric(long[varname], errors="coerce")
    return long


def build_livestock_controls():
    frames = [clean_ls(fname, varname) for varname, fname in FILES.items()]
    livestock = reduce(lambda l, r: pd.merge(l, r, on=["year", "province"], how="outer"), frames)
    return livestock


def build_wide_panel():
    panel_long = pd.read_parquet(f"{CKPT_DIR}/panel_long.parquet")
    bartik = pd.read_parquet(f"{CKPT_DIR}/bartik_instrument.parquet")
    livestock = build_livestock_controls()
    panel_long["year"] = panel_long["year_quarter"].str[:4].astype(int)

    panel_long = panel_long.merge(livestock, on=["year", "province"], how="left")
    panel_long = panel_long.merge(bartik, on=["province", "year_quarter"], how="left")

    # Pivot to wide: one row per province-year_quarter, columns per product for
    # value/qty/share/price variables.
    id_cols = ["province", "year_quarter", "year", "total_import_expenditure_usd",
               "positive_budget_flag", "bartik_instrument", "predicted_nonag_trade",
               "pork", "beef", "mutton", "poultry_meat", "eggs", "milk"]
    id_frame = panel_long[id_cols].drop_duplicates(subset=["province", "year_quarter"])

    value_cols = ["import_value_usd", "import_qty_kg", "budget_share",
                  "unit_value_usd_per_kg", "n_sources", "hhi", "top_source_share"]
    wide = id_frame.copy()
    for vc in value_cols:
        piv = panel_long.pivot_table(index=["province", "year_quarter"], columns="product", values=vc)
        piv.columns = [f"{vc}__{p}" for p in piv.columns]
        wide = wide.merge(piv.reset_index(), on=["province", "year_quarter"], how="left")
    return wide


if __name__ == "__main__":
    wide = build_wide_panel()
    wide.to_parquet(f"{CKPT_DIR}/panel_wide.parquet", index=False)
    print(f"Wide panel built: {wide.shape[0]} rows, {wide.shape[1]} columns.")
    print(f"Positive-budget rows: {wide['positive_budget_flag'].sum()}")
