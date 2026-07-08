"""Translation of 4OUTPUT.GMS: build every reporting table that GAMS
unloads into 3RESULTCOM.XLSX (BASE scenario)."""

from __future__ import annotations

import os
import numpy as np
import pandas as pd

from .gdxxrw import load_symbols
from .data import Data, T, TAH, TC, TSP, TPHIS


# sheet -> commodity behind it
SHEET_COMMODITY = dict(
    RICEX="RICE", WHEAX="WHEA", MAIZX="MAIZ", BARLX="BARL", POTAX="POTA",
    SOYSX="SOYS", SOYOX="SOYO", SOYMX="SOYM", RAPSX="RAPS", RAPOX="RAPO",
    RAPMX="RAPM", GRDSX="GRDS", GRDOX="GRDO", GRDMX="GRDM", COTTX="COTT",
    SUGAX="SUGA", VEGTX="VEGT", SORGX="SORG", OTGRX="OTGR", FRTOX="FRTO",
    BEEFX="CATM", PORKX="PIGM", SHGMX="SHGM", CHKMX="CHKM", EGGSX="EGGS",
    MILKX="MILK", FISHX="FISH",
)
# aggregate sheets: sheet -> set attribute of Data
SHEET_GROUP = dict(KOULX="CKOUL", GUWUX="CCRL", LISHX="CGRN")
# "one variable, all commodities" sheets
SHEET_VAR = dict(TOSLX="TOSL", PRODX="QXX", AREAX="ACX", YILDX="YCX",
                 NIMPX="QMX", TODMX="TODM", FOODX="QDFX", PFODX="QDFPCX",
                 FEEDX="QDLX", PROCX="QDPX", CRSHX="QDCX", SEEDX="QDSX",
                 WASTX="QDWX", OTHEX="QDOX", STOCX="STVX", NEXPX="QEX",
                 DOMDX="QDTX", PRICX="PDX", DFODX="DFOOD")


class Output:
    def __init__(self, casm_dir, d: Data, m, res):
        self.d, self.m = d, m
        C, H = d.C, d.H
        n = len(C)

        # ---- X parameters: projections from the solve, history from data --
        X = {}

        def blank():
            return pd.DataFrame(0.0, index=C, columns=T)

        for name in ("QXX ACX YCX QDFX QDFPCX QDLX QDSX QDPX QDCX QDOX QDWX "
                     "QDTX STVX PXX PDX QMX QEX").split():
            X[name] = blank()
        src = dict(QXX="QX", ACX="AC", YCX="YC", QDFX="QDF", QDFPCX="QDFPC",
                   QDLX="QDL", QDSX="QDS", QDPX="QDP", QDCX="QDC", QDOX="QDO",
                   QDWX="QDW", QDTX="QDT", STVX="STV", PXX="PX", PDX="PD")
        for t in TC:
            for xn, rn in src.items():
                X[xn][t] = res[rn][t]
            qm, qe = res["QM"][t], res["QE"][t]
            net = qm - qe
            X["QMX"][t] = np.where(net > 0, net, 0.0)
            X["QEX"][t] = np.where(net < 0, -net, 0.0)
        d0 = dict(QXX=d.QX0, ACX=d.AC0, YCX=d.YC0, QDFX=d.QDF0,
                  QDFPCX=d.QDFPC0, QDLX=d.QDL0, QDSX=d.QDS0, QDPX=d.QDP0,
                  QDCX=d.QDC0, QDOX=d.QDO0, QDWX=d.QDW0, QDTX=d.QDT0,
                  STVX=d.STV0, PXX=d.PX0, PDX=d.PD0)
        for t in TAH:
            for xn, df0 in d0.items():
                X[xn][t] = df0[t]
            qm, qe = d.QM0[t].values, d.QE0[t].values
            net = qm - qe
            X["QMX"][t] = np.where(net > 0, net, 0.0)
            X["QEX"][t] = np.where(net < 0, -net, 0.0)

        # macro
        POPHX = pd.DataFrame(0.0, index=H, columns=T)
        INCPCX = pd.DataFrame(0.0, index=H, columns=T)
        GDPTX = pd.Series(0.0, index=T)
        for t in TC:
            for h in H:
                POPHX.loc[h, t] = res["POPH"][t][h]
                INCPCX.loc[h, t] = res["INCPC"][t][h]
            GDPTX[t] = res["GDPT"][t]
        for t in TAH:
            POPHX[t] = d.POPH0[t]
            INCPCX[t] = d.INCPC0[t]
            GDPTX[t] = d.GDPT0[t]
        POPX = POPHX.sum(axis=0) / 2
        self.POPHX, self.POPX, self.GDPTX = POPHX, POPX, GDPTX

        NETQMEX = X["QMX"] - X["QEX"]
        X["NETQMEX"] = NETQMEX
        self.X = X

        # ---- 4.2.8 emission factors and nutrition coefficients ------------
        par = load_symbols(os.path.join(casm_dir, "1parameter.xlsx"),
                           "INDEX!A6",
                           wanted={"FERTEF0", "BURNEF0", "CROPREF0",
                                   "RICEEF0", "LVSEF0", "ENERG"})

        def par_ct(sym):
            df = pd.DataFrame(0.0, index=C, columns=T)
            for (c, sim, t), v in par[sym].items():
                if c in df.index and sim == "BASE" and t in df.columns:
                    df.loc[c, t] = v
            return df

        FERTEF = par_ct("FERTEF0")
        BURNEF = par_ct("BURNEF0")
        CROPREF = par_ct("CROPREF0")
        RICEEF = par_ct("RICEEF0")
        LVSEF = par_ct("LVSEF0")
        ENERG = pd.DataFrame(0.0, index=C,
                             columns=sorted({k[1] for k in par["ENERG"]}))
        for (c, k), v in par["ENERG"].items():
            if c in ENERG.index:
                ENERG.loc[c, k] = v

        # ---- 4.3 carbon emission and dietary energy ------------------------
        NETQMEXADJ = NETQMEX.sub(NETQMEX[TPHIS], axis=0)
        QXXADJ = pd.DataFrame(0.0, index=C, columns=T)
        ACXADJ = pd.DataFrame(0.0, index=C, columns=T)
        for c in d.CCRP:
            QXXADJ.loc[c] = X["QXX"].loc[c] + NETQMEXADJ.loc[c]
            yc = X["YCX"].loc[c]
            ACXADJ.loc[c] = np.where(yc != 0, QXXADJ.loc[c] / yc.replace(0, 1), 0.0)
        for c in d.CLVS:
            QXXADJ.loc[c] = X["QXX"].loc[c] + NETQMEXADJ.loc[c]
        CO2 = pd.DataFrame(0.0, index=C, columns=T)
        for c in d.CCRP:
            CO2.loc[c] = ACXADJ.loc[c] * (FERTEF.loc[c] + BURNEF.loc[c]
                                          + CROPREF.loc[c] + RICEEF.loc[c])
        for c in d.CLVS:
            CO2.loc[c] = QXXADJ.loc[c] * LVSEF.loc[c]
        self.CO2 = CO2
        self.CO2CRP = CO2.loc[d.CCRP].sum(axis=0) - CO2.loc["POTA"]
        self.CO2LVS = CO2.loc[d.CLVS].sum(axis=0)
        self.CO2TOT = self.CO2CRP + self.CO2LVS

        def nutr(col):
            v = X["QDFPCX"].mul(ENERG["EATSHR"] * ENERG[col] / 10000, axis=0)
            return v * 1000 / 365
        self.ENERGY = nutr("ENERGY")
        self.PROTEIN = nutr("PROTEIN")
        self.FAT = nutr("FAT")
        self.CARBON = nutr("CARBON")
        self.DFOOD = X["QDFPCX"] * 1000 / 365

    # ------------------------------------------------------------------
    def commodity_sheet(self, c) -> pd.DataFrame:
        """Rows of a per-commodity sheet, columns TSP."""
        X = self.X
        rows = {
            "TOTAL SUPPLY": X["QXX"].loc[c] + X["QMX"].loc[c],
            "PRODUCTION": X["QXX"].loc[c],
            "AREA": X["ACX"].loc[c],
            "YIELD": X["YCX"].loc[c] * 1000,
            "NET IMPORT": X["QMX"].loc[c],
            "TOTAL DEMAND": X["QDTX"].loc[c] + X["QEX"].loc[c],
            "TOTAL FOOD DEMAND BY ALL HOUSEHOLD": X["QDFX"].loc[c],
            "PER CAPITA FOOD DEMAND": X["QDFPCX"].loc[c],
            "SEED DEMAND": X["QDSX"].loc[c],
            "FEED DEMAND": X["QDLX"].loc[c],
            "PROCESSING DEMAND": X["QDPX"].loc[c],
            "CRUSH DEMAND": X["QDCX"].loc[c],
            "WASTE DEMAND": X["QDWX"].loc[c],
            "OTHER DEMAND": X["QDOX"].loc[c],
            "STOCK CHANGE": X["STVX"].loc[c],
            "NET EXPORT": X["QEX"].loc[c],
            "DOMESTIC DEMAND": X["QDTX"].loc[c] - X["STVX"].loc[c],
            "ENERGY": self.ENERGY.loc[c],
            "CARBON EMISSION": self.CO2.loc[c],
        }
        return pd.DataFrame(rows).T[TSP]

    def group_sheet(self, group) -> pd.DataFrame:
        X, d = self.X, self.d
        cs = getattr(d, group)
        rows = {
            "TOTAL SUPPLY": X["QXX"].loc[cs].sum() + X["QMX"].loc[cs].sum(),
            "PRODUCTION": X["QXX"].loc[cs].sum(),
            "AREA": X["ACX"].loc[cs].sum(),
            "YIELD": X["YCX"].loc[cs].sum(),   # GAMS sums yields as-is
            "NET IMPORT": X["QMX"].loc[cs].sum(),
            "TOTAL DEMAND": X["QDTX"].loc[cs].sum() + X["QEX"].loc[cs].sum(),
            "TOTAL FOOD DEMAND BY ALL HOUSEHOLD": X["QDFX"].loc[cs].sum(),
            "PER CAPITA FOOD DEMAND": X["QDFPCX"].loc[cs].sum(),
            "SEED DEMAND": X["QDSX"].loc[cs].sum(),
            "FEED DEMAND": X["QDLX"].loc[cs].sum(),
            "PROCESSING DEMAND": X["QDPX"].loc[cs].sum(),
            "CRUSH DEMAND": X["QDCX"].loc[cs].sum(),
            "WASTE DEMAND": X["QDWX"].loc[cs].sum(),
            "OTHER DEMAND": X["QDOX"].loc[cs].sum(),
            "STOCK CHANGE": X["STVX"].loc[cs].sum(),
            "NET EXPORT": X["QEX"].loc[cs].sum(),
            "DOMESTIC DEMAND": X["QDTX"].loc[cs].sum() - X["STVX"].loc[cs].sum(),
            "ENERGY": self.ENERGY.loc[cs].sum(),
            "CARBON EMISSION": self.CO2.loc[cs].sum(),
        }
        return pd.DataFrame(rows).T[TSP]

    def var_sheet(self, key) -> pd.DataFrame:
        X = self.X
        if key == "TOSL":
            v = X["QXX"] + X["QMX"]
        elif key == "TODM":
            v = X["QDTX"] + X["QEX"]
        elif key == "DFOOD":
            v = self.DFOOD
        else:
            v = X[key]
        return v[TSP]

    def macro_sheets(self):
        popu = pd.DataFrame({
            "TOTAL POPULATION": self.POPX,
            "URBAN POPULATION": self.POPHX.loc["HHDHU"],
            "URBANIZATION RATE": self.POPHX.loc["HHDHU"] / self.POPX,
        }).T[TSP]
        pgdp = pd.DataFrame({"PER CAPITA GDP": self.GDPTX / self.POPX}).T[TSP]
        co2e = pd.DataFrame({
            "CROP EMISSION": self.CO2CRP,
            "LIVESTOCK EMISSION": self.CO2LVS,
            "TOTAL EMISSION": self.CO2TOT,
        }).T[TSP]
        d = self.d
        et = self.ENERGY.sum(axis=0)
        pt = self.PROTEIN.sum(axis=0)
        ft = self.FAT.sum(axis=0)
        ct = self.CARBON.sum(axis=0)
        engy = pd.DataFrame({
            "ENERGY": et,
            "PROTEIN": pt,
            "FAT": ft,
            "CARBOHYDRATE": ct,
            "ENERGY FROM PROTEIN": pt * 4 / et,
            "ENERGY FROM FAT": ft * 9 / et,
            "ENERGY FROM CARBOHYDRATE": 1 - pt * 4 / et - ft * 9 / et,
            "ENERGY FROM PLANT": self.ENERGY.loc[d.CCRP].sum() / et,
            "ENERGY FROM OIL": self.ENERGY.loc[d.COIL].sum() / et,
            "ENERGY FROM ANIMAL": self.ENERGY.loc[d.CLVS].sum() / et,
            "PROTEIN FROM PLANT": self.PROTEIN.loc[d.CCRP].sum() / pt,
            "PROTEIN FROM ANIMAL": self.PROTEIN.loc[d.CLVS].sum() / pt,
        }).T[TSP]
        return dict(POPUX=popu, PGDPX=pgdp, CO2EX=co2e, ENGYX=engy)

    # ------------------------------------------------------------------
    def all_sheets(self):
        out = {}
        for sheet, c in SHEET_COMMODITY.items():
            out[sheet] = self.commodity_sheet(c)
        for sheet, grp in SHEET_GROUP.items():
            out[sheet] = self.group_sheet(grp)
        for sheet, key in SHEET_VAR.items():
            out[sheet] = self.var_sheet(key)
        out.update(self.macro_sheets())
        return out
