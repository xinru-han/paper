
"""
02_build_bartik_instrument.py
Construct the nonagricultural-import Bartik (shift-share) instrument for
endogenous five-product import expenditure, using the FULL customs micro
data (all HS chapters, 进口数据/2017.csv .. 2023.csv) -- not just the
HS01-24 food/agri subset used for the feed-grain panel.

Design (predicted-trade / shift-share level instrument, Bartik 1991 /
Card 2001 style): for each province p and quarter t,

    predicted_nonag_trade_{p,t} = sum_k  base_share_{p,k} * national_sector_value_{k,t}

where k indexes HS2 non-agricultural sectors (chapters 25-97), base_share_{p,k}
is province p's average 2017 share of national imports in sector k, and
national_sector_value_{k,t} is the total (all-China) import value in sector k
at quarter t. The instrument is log(predicted_nonag_trade); its variation
comes entirely from how each province's FIXED 2017 sectoral exposure
interacts with national sector-level shocks over time, which is the standard
shift-share exclusion-restriction argument (the estimating equation always
also includes province and year-quarter fixed effects, so only the
interaction/shift component identifies the instrument's effect).

Several alternative designs (leave-one-out sector growth rates at HS2 and
HS4 granularity, quarter-over-quarter vs year-over-year growth) were tested
and yielded much weaker first stages (partial F below 1); those diagnostics
are recorded in bartik_design_search.csv for transparency. The predicted-
trade level design at HS2 granularity was selected as the primary instrument
(partial F approx 14.5, exceeding the conventional weak-instrument
threshold), and is reported as such in the revised paper -- markedly weaker
than the resubmitted draft's originally claimed F=88.83, which used a
different (undocumented, since the original construction code was not
available) instrument definition.
"""
import duckdb
import numpy as np
import pandas as pd

IMPORT_DIR = "/root/data/Paper/饲料进口弹性/进口数据"
CKPT_DIR = "/root/data/Paper/饲料进口弹性/revision_2026/checkpoints"
OUT_DIR = "/root/data/Paper/饲料进口弹性/revision_2026/output"

YEARS = list(range(2017, 2024))


def load_nonag_hs2_province_quarter():
    con = duckdb.connect()
    files_glob = ",".join([f"'{IMPORT_DIR}/{y}.csv'" for y in YEARS])
    query = f"""
    WITH raw AS (
      SELECT * FROM read_csv_auto([{files_glob}], ALL_VARCHAR=TRUE, union_by_name=TRUE)
    ),
    typed AS (
      SELECT
        "进出口类型" AS trade_type,
        "商品编码" AS hs8,
        "地址" AS province,
        TRY_CAST(REPLACE("金额", ',', '') AS DOUBLE) AS val_usd,
        CAST(SUBSTR("日期",1,4) AS INTEGER) AS year,
        CAST(SUBSTR("日期",6,2) AS INTEGER) AS month
      FROM raw
      WHERE "进出口类型" = '进口'
    )
    SELECT
      province, year,
      CAST(FLOOR((month-1)/3.0) AS INTEGER) + 1 AS quarter,
      SUBSTR(hs8,1,2) AS hs2,
      SUM(val_usd) AS val_usd
    FROM typed
    WHERE hs8 IS NOT NULL AND LENGTH(hs8) >= 2
    GROUP BY 1,2,3,4
    """
    raw = con.execute(query).fetchdf()
    raw["hs2_int"] = pd.to_numeric(raw["hs2"], errors="coerce")
    nonag = raw[raw["hs2_int"] >= 25].copy()  # HS25-97 = non-agricultural chapters
    nonag["year_quarter"] = nonag["year"].astype(str) + "Q" + nonag["quarter"].astype(str)
    return nonag


def build_predicted_trade_instrument(sector_hs2):
    base = sector_hs2[sector_hs2.year == 2017].groupby(["province", "hs2"])["val_usd"].mean().reset_index(
        name="base_val"
    )
    sector_national_base = base.groupby("hs2")["base_val"].sum().rename("sector_national_base")
    base = base.merge(sector_national_base, on="hs2")
    base["base_share"] = base["base_val"] / base["sector_national_base"]

    nat_q = sector_hs2.groupby(["hs2", "year_quarter"])["val_usd"].sum().reset_index(name="nat_sector_total")

    pred = base[["province", "hs2", "base_share"]].merge(nat_q, on="hs2", how="left")
    pred["contrib"] = pred["base_share"] * pred["nat_sector_total"]
    predicted = pred.groupby(["province", "year_quarter"])["contrib"].sum().reset_index(
        name="predicted_nonag_trade"
    )
    predicted["bartik_instrument"] = np.log(predicted["predicted_nonag_trade"].clip(lower=1))
    return predicted[["province", "year_quarter", "predicted_nonag_trade", "bartik_instrument"]]


if __name__ == "__main__":
    sector_hs2 = load_nonag_hs2_province_quarter()
    bartik = build_predicted_trade_instrument(sector_hs2)
    bartik.to_parquet(f"{CKPT_DIR}/bartik_instrument.parquet", index=False)
    print(f"Bartik instrument built: {bartik.shape[0]} province-quarter rows, "
          f"{bartik['bartik_instrument'].notna().sum()} non-missing.")
