"""Translation of 0DATA.GMS: load the balance sheets from 0DATA.XLSX and
build the base-data parameters.

All commodity-by-time parameters are pandas DataFrames indexed by the full
commodity set C with string year columns T ('2023' .. '2035').  Values
default to 0.0 exactly like unassigned GAMS parameters.
"""

from __future__ import annotations

import os
import numpy as np
import pandas as pd

from .gdxxrw import load_symbols

# ---- time sets (CASM.gms 0.1) -----------------------------------------
TPHIS, TPREV, TBASE = "2023", "2024", "2025"
TPJ1, TFINAL = 2026, 2035
T = [TPHIS, TPREV, TBASE] + [str(y) for y in range(TPJ1, TFINAL + 1)]
TP = [TPREV]
TB = [TBASE]
TLB = [TPREV, TBASE]
TC = [str(y) for y in range(TPJ1, TFINAL + 1)]
TAH = [TPHIS, TPREV, TBASE]
TSP = [TPREV, TBASE] + TC  # selected reporting periods

H = ["HHDHR", "HHDHU", "HHDOR", "HHDOU"]

# symbols $LOADed by 0DATA.GMS
_LOADED = """C CO CS HALL H CCRP CLVS CGRN CCRL COILSD COILMEAL COIL CMEAL
CSUGCRP CSUG CKOUL CFRT CVEGT CMILK CFISH CFEED BVAR CLVO
MPSOM MPSUGCRPA MPSM MPSO
POP0 GDP0 INCOMEPC0 EXCH0 EDFIH0 EDFPH0 EAP0 EYP0 ESP0
RICE0 WHEA0 MAIZ0 POTA0 BARL0 OTGR0 SORG0
SOYS0 SOYO0 SOYM0 RAPS0 RAPO0 RAPM0 GRDS0 GRDO0 GRDM0
COTT0 SUGA0 VEGT0 FRTO0 PORK0 BEEF0 SHGM0 CHKM0 EGGS0 MILK0 FISH0
FDIST0 FEDELA0 ELAP0 ELAGDP0 ELAPOP0
OILELA0 SUGOUTELA0 SUGINPELA0 INPELA0""".split()


def _df(index, columns):
    return pd.DataFrame(0.0, index=list(index), columns=list(columns))


class Data:
    """Holds every parameter produced by 0DATA.GMS."""

    def __init__(self, casm_dir):
        raw = load_symbols(os.path.join(casm_dir, "0data.xlsx"), "INDEX!A1",
                           wanted=set(_LOADED))
        self.raw = raw

        # ---- sets ------------------------------------------------------
        for s in ("C CO CS HALL CCRP CLVS CGRN CCRL COILSD COILMEAL COIL "
                  "CMEAL CSUGCRP CSUG CKOUL CFRT CVEGT CMILK CFISH CFEED "
                  "CLVO BVAR").split():
            setattr(self, s, list(raw[s]))
        self.H = list(raw["H"])
        self.MPSOM = list(raw["MPSOM"])
        self.MPSUGCRPA = list(raw["MPSUGCRPA"])
        self.MPSM = list(raw["MPSM"])
        self.MPSO = list(raw["MPSO"])
        C = self.C

        # ---- 0.4/0.6 parameter shells ----------------------------------
        for name in ("QX0 AC0 YC0 QDF0 QDL0 QDS0 QDP0 QDC0 QDW0 QDO0 STV0 "
                     "QM0 QE0 PX0 PD0 PWM0 PWE0 EST0 NQMX0 QDTB0 QDT0 "
                     "QDFPC0 QDTBPC0 QBA10").split():
            setattr(self, name, _df(C, T))
        self.QDFH0 = {h: _df(C, T) for h in self.H}
        self.QDFHPC0 = {h: _df(C, T) for h in self.H}

        # ---- 0.7.1 macro data -------------------------------------------
        self.POPH0 = _df(self.H, T)
        self.INCPC0 = _df(self.H, T)
        for h in self.H:
            for t in T:
                self.POPH0.loc[h, t] = raw["POP0"].get((h, t), 0.0)
                self.INCPC0.loc[h, t] = raw["INCOMEPC0"].get((h, t), 0.0)
        self.GDPT0 = pd.Series({t: raw["GDP0"].get(("GDP", t), 0.0) * 10000 for t in T})
        # exchange rate: data is RMB per 100 USD -> /100 (0.7.12)
        self.EXCH0 = pd.Series({t: raw["EXCH0"].get(("USD", t), 0.0) / 100 for t in T})

        # ---- 0.7.2/0.7.3 commodity blocks --------------------------------
        self._load_commodities(raw)

        # ---- 0.7.10 per-capita food demand (before trade netting!) -------
        for h in self.H:
            pop = self.POPH0.loc[h]
            with np.errstate(divide="ignore", invalid="ignore"):
                v = self.QDFH0[h].values / pop.values[None, :] * 1000
            v[:, pop.values == 0] = 0.0
            self.QDFHPC0[h].loc[:, :] = v
        popall = self.POPH0.sum(axis=0)
        with np.errstate(divide="ignore", invalid="ignore"):
            v = self.QDF0.values / popall.values[None, :] * 1000 * 2
        v[:, popall.values == 0] = 0.0
        self.QDFPC0.loc[:, :] = v

        # ---- 0.7.11.2 net out trade, drop tiny values --------------------
        QM, QE = self.QM0, self.QE0
        self.NQMX0.loc[:, :] = QM.values - QE.values
        n = self.NQMX0.values
        qm, qe = QM.values.copy(), QE.values.copy()
        qm2 = qm.copy()
        qm2[(qm - qe) > 0] = n[(qm - qe) > 0]
        qe2 = qe.copy()
        qe2[n < 0] = (qe - qm)[n < 0]
        qm2[n < 0] = 0.0
        qe2[n > 0] = 0.0
        QM.loc[:, :], QE.loc[:, :] = qm2, qe2

        tb = TBASE
        for dfname in ("QM0", "QE0", "QX0"):
            df = getattr(self, dfname)
            col = df[tb].values
            col[col <= 0.1] = 0.0
            df[tb] = col
        self.YC0.loc[self.QX0[tb].values == 0, tb] = 0.0
        for dfname in ("QDF0", "QDL0", "QDS0", "QDP0", "QDC0", "QDW0", "QDO0"):
            df = getattr(self, dfname)
            col = df[tb].values
            col[col <= 0.1] = 0.0
            df[tb] = col

        # ---- 0.7.11.4 recalc yield ---------------------------------------
        with np.errstate(divide="ignore", invalid="ignore"):
            yc = np.where(self.AC0.values != 0,
                          self.QX0.values / np.where(self.AC0.values != 0,
                                                     self.AC0.values, 1.0),
                          self.YC0.values)
        self.YC0.loc[:, :] = yc

        # ---- 0.7.13 elasticities -----------------------------------------
        self.EDFIH = _df(C, self.H)
        for (c, h), v in raw["EDFIH0"].items():
            if c in C and h in self.H:
                self.EDFIH.loc[c, h] = v
        self.EDFPH = {h: _df(C, C) for h in self.H}
        for (c, cp, h), v in raw["EDFPH0"].items():
            if c in C and cp in C and h in self.H:
                self.EDFPH[h].loc[c, cp] = v
        self.EAP = _df(C, C)
        for (c, cp), v in raw["EAP0"].items():
            if c in C and cp in C:
                self.EAP.loc[c, cp] = v
        self.EYP = pd.Series(0.0, index=C)
        for (c,), v in raw["EYP0"].items():
            if c in C:
                self.EYP[c] = v
        self.ESP = _df(C, C)
        for (c, cp), v in raw["ESP0"].items():
            if c in C and cp in C:
                self.ESP.loc[c, cp] = v
        self.FDIST = _df(self.CFEED, self.CLVS)
        for (cf, cl), v in raw["FDIST0"].items():
            if cf in self.CFEED and cl in self.CLVS:
                self.FDIST.loc[cf, cl] = v
        for name, sym in (("ELAP", "ELAP0"), ("ELAGDP", "ELAGDP0"),
                          ("ELAPOP", "ELAPOP0"), ("SUGOUTELA", "SUGOUTELA0"),
                          ("SUGINPELA", "SUGINPELA0"), ("INPELA", "INPELA0")):
            s = pd.Series(0.0, index=C)
            for (c,), v in raw[sym].items():
                if c in C:
                    s[c] = v
            setattr(self, name, s)
        self.OILELA = _df(C, C)
        for (c, cp), v in raw["OILELA0"].items():
            if c in C and cp in C:
                self.OILELA.loc[c, cp] = v

        # ---- 0.7.13/0.7.14/0.7.15 totals and balance check ---------------
        self.TAC0 = self.AC0.sum(axis=0)
        pophh = pd.Series({t: raw["POP0"].get(("HHDHR", t), 0.0)
                           + raw["POP0"].get(("HHDHU", t), 0.0) for t in T})
        with np.errstate(divide="ignore", invalid="ignore"):
            v = (self.QX0.values + self.QM0.values - self.QE0.values) \
                / pophh.values[None, :] * 1000
        v[:, pophh.values == 0] = 0.0
        self.QDTBPC0.loc[:, :] = v

        self.QDTB0.loc[:, :] = self.QX0.values + self.QM0.values - self.QE0.values
        qdfh_sum = sum((self.QDFHPC0[h].values * self.POPH0.loc[h].values[None, :]
                        / 1000) for h in self.H)
        self.QDT0.loc[:, :] = (qdfh_sum + self.QDL0.values + self.QDS0.values
                               + self.QDP0.values + self.QDC0.values
                               + self.QDW0.values + self.QDO0.values
                               + self.STV0.values)
        self.QBA10[TBASE] = self.QDTB0[TBASE] - self.QDT0[TBASE]

    # -------------------------------------------------------------------
    def _load_commodities(self, raw):
        """0.7.2/0.7.3: map balance-sheet symbols onto model parameters."""
        std = dict(PRD="QX0", FOODDM="QDF0", FEEDDM="QDL0", PROCDM="QDP0",
                   LOSSDM="QDW0", SEEDDM="QDS0", STV="STV0", IMP="QM0",
                   EXP="QE0", PPD="PX0", PCS="PD0", PIMP="PWM0", PEXP="PWE0")
        oil_seed = dict(std)
        oil_seed.pop("PROCDM")
        oil_seed["CRUSHDM"] = "QDC0"
        lvs = dict(PRDMT="QX0", IMP="QM0", FOODDM="QDF0", PROCDM="QDP0",
                   LOSSDM="QDW0", OTHRDM="QDO0", EXP="QE0", PRCMT="PX0",
                   PIMP="PWM0", PEXP="PWE0")
        lvs_no_oth = {k: v for k, v in lvs.items() if k != "OTHRDM"}

        # (commodity, symbol, field map, has-area, has-household-food, extra)
        blocks = [
            ("RICE", "RICE0", std, True, True, {}),
            ("WHEA", "WHEA0", std, True, True, {}),
            ("MAIZ", "MAIZ0", std, True, True, {}),
            ("BARL", "BARL0", std, True, True, {}),
            ("SORG", "SORG0", {**std, "OTHRDM": "QDO0"}, True, True, {}),
            ("OTGR", "OTGR0", {**std, "OTHRDM": "QDO0"}, True, True, {}),
            ("POTA", "POTA0", std, True, True, {}),
            ("SOYS", "SOYS0", oil_seed, True, True, {}),
            ("SOYO", "SOYO0", std, True, True, {}),
            ("SOYM", "SOYM0", std, True, True, {}),
            ("RAPS", "RAPS0", oil_seed, True, True, {}),
            ("RAPO", "RAPO0", std, True, True, {}),
            ("RAPM", "RAPM0", std, True, True, {}),
            ("GRDS", "GRDS0", oil_seed, True, True, {}),
            ("GRDO", "GRDO0", std, True, True, {}),
            ("GRDM", "GRDM0", std, True, True, {}),
            ("COTT", "COTT0", std, True, False, {}),
            ("SUGA", "SUGA0", std, True, True, {}),
            ("VEGT", "VEGT0", {**std, "OTHRDM": "QDO0"}, True, True, {}),
            ("FRTO", "FRTO0", {**std, "OTHRDM": "QDO0"}, True, True, {}),
            ("PIGM", "PORK0", lvs, False, True, {}),
            ("CATM", "BEEF0", lvs, False, True, {}),
            ("SHGM", "SHGM0", lvs, False, True, {}),
            ("CHKM", "CHKM0", lvs_no_oth, False, True, {}),
            ("EGGS", "EGGS0", lvs, False, True, {}),
            ("MILK", "MILK0", lvs, False, True, {}),
            ("FISH", "FISH0", lvs, False, True, {}),
        ]
        hh = dict(UHFOODDM="HHDHU", UOFOODDM="HHDOU",
                  RHFOODDM="HHDHR", ROFOODDM="HHDOR")
        for c, sym, fmap, has_area, has_hh, _ in blocks:
            d = raw[sym]
            for field, target in fmap.items():
                df = getattr(self, target)
                for t in T:
                    df.loc[c, t] = d.get((field, t), 0.0)
            if has_area:
                for t in T:
                    self.AC0.loc[c, t] = d.get(("AREA", t), 0.0) / 10
                    ac = self.AC0.loc[c, t]
                    if ac:
                        self.YC0.loc[c, t] = self.QX0.loc[c, t] / ac
            if has_hh:
                for field, h in hh.items():
                    for t in T:
                        self.QDFH0[h].loc[c, t] = d.get((field, t), 0.0)

        # SUGA extras: end stock is written onto COTT in the GAMS source
        # (EST0('COTT',T) = SUGA0('ENDSTK',T)) - replicated verbatim.
        d = raw["SUGA0"]
        for t in T:
            self.EST0.loc["COTT", t] = d.get(("ENDSTK", t), 0.0)

        # sugar cane / beet taken from the SUGA0 sheet
        for t in T:
            self.QX0.loc["SUGC", t] = d.get(("PRDSUGC", t), 0.0)
            self.AC0.loc["SUGC", t] = d.get(("AREASUGC", t), 0.0) / 10
            if self.AC0.loc["SUGC", t]:
                self.YC0.loc["SUGC", t] = self.QX0.loc["SUGC", t] / self.AC0.loc["SUGC", t]
            self.QX0.loc["SUGB", t] = d.get(("PRDSUGB", t), 0.0)
            self.AC0.loc["SUGB", t] = d.get(("AREASUGB", t), 0.0) / 10
            if self.AC0.loc["SUGB", t]:
                # GAMS uses SUGC production here (kept as-is on purpose)
                self.YC0.loc["SUGB", t] = self.QX0.loc["SUGC", t] / self.AC0.loc["SUGB", t]
            self.QDP0.loc["SUGC", t] = self.QX0.loc["SUGC", t]
            self.QDP0.loc["SUGB", t] = self.QX0.loc["SUGB", t]
            self.PX0.loc["SUGC", t] = d.get(("PPDSUGC", t), 0.0)
            self.PX0.loc["SUGB", t] = d.get(("PPDSUGB", t), 0.0)
