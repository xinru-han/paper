"""Translation of 1CALIBRATION.GMS: input-output coefficients, dynamic
sets and calibrated intercepts of every behavioural equation.

Statements are executed in the same order as the GAMS source; parameters
carry the same names (without the trailing 0 for the working copies).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .data import Data, T, TB, TBASE


def _df(index, columns):
    return pd.DataFrame(0.0, index=list(index), columns=list(columns))


class Calibration:
    def __init__(self, d: Data):
        self.d = d
        C, H = d.C, d.H
        tb = TBASE

        # ---- 1.1.10 oilseed crush ratios --------------------------------
        # IOOILSD0(COILMEAL,COILSDP,T)$QDC0 = QX0(COILMEAL,T)/QDC0(COILSDP,T)
        self.IOOILSD = {}   # (cm, cs) -> Series over T
        for cm, cs in d.MPSOM:
            s = pd.Series(0.0, index=T)
            for t in T:
                q = d.QDC0.loc[cs, t]
                if q:
                    s[t] = d.QX0.loc[cm, t] / q
            self.IOOILSD[(cm, cs)] = s
        self.IOMEAL = {}
        for cm, cs in d.MPSM:
            s = pd.Series(0.0, index=T)
            for t in T:
                q = d.QDC0.loc[cs, t]
                if q:
                    s[t] = d.QX0.loc[cm, t] / q
            self.IOMEAL[(cm, cs)] = s
        self.IOOIL = {}
        for co, cs in d.MPSO:
            s = pd.Series(0.0, index=T)
            for t in T:
                q = d.QDC0.loc[cs, t]
                if q:
                    s[t] = d.QX0.loc[co, t] / q
            self.IOOIL[(co, cs)] = s

        # ---- 1.1.11 feed use and feed cost -------------------------------
        # FEES0(CFEED,CLVS,T) = QDL0(CFEED,T)*FDIST0(CFEED,CLVS)
        self.FEES0 = {t: d.QDL0[t].loc[d.CFEED].values[:, None]
                      * d.FDIST.values for t in T}
        # early FECOST0 (used by ASM0); PD0 at this point: TB already = PX0
        pd0_early = d.PD0.copy()
        pd0_early[tb] = d.PX0[tb]
        self.FECOST0_early = {t: self.FEES0[t].T @ pd0_early.loc[d.CFEED, t].values
                              for t in T}

        # ---- 1.1.12 feed conversion IOXL ---------------------------------
        self.IOXL = _df(d.CFEED, d.CLVS)
        for cl in ["PIGM", "CATM", "SHGM", "CHKM", "EGGS", "MILK", "FISH"]:
            qx = d.QX0.loc[cl, tb]
            if qx:
                self.IOXL.loc[:, cl] = (d.FDIST[cl].values
                                        * d.QDL0.loc[d.CFEED, tb].values / qx)
        self.IOXL3 = self.IOXL.copy()

        # ---- 1.1.13 input-output ratios ----------------------------------
        self.IOXS = _df(C, T)
        self.IOXP = _df(C, T)
        self.IOXW = _df(C, T)
        self.IOXO = _df(C, T)
        self.IOSTV = _df(C, T)
        ac, qx = d.AC0.values, d.QX0.values
        with np.errstate(divide="ignore", invalid="ignore"):
            self.IOXS.loc[:, :] = np.where(ac != 0, d.QDS0.values / np.where(ac != 0, ac, 1), 0.0)
            m = qx != 0
            qq = np.where(m, qx, 1.0)
            self.IOXO.loc[:, :] = np.where(m, d.QDO0.values / qq, 0.0)
            self.IOXW.loc[:, :] = np.where(m, d.QDW0.values / qq, 0.0)
            self.IOXP.loc[:, :] = np.where(m, d.QDP0.values / qq, 0.0)
            self.IOSTV.loc[:, :] = np.where(m, d.STV0.values / qq, 0.0)

        # ---- 1.1.14 sugar extraction rates -------------------------------
        iosug0 = _df(C, T)
        for t in T:
            if d.QDP0.loc["SUGC", t]:
                iosug0.loc["SUGC", t] = 0.9 * d.QX0.loc["SUGA", t] / d.QDP0.loc["SUGC", t]
            if d.QDP0.loc["SUGB", t]:
                iosug0.loc["SUGB", t] = 0.1 * d.QX0.loc["SUGA", t] / d.QDP0.loc["SUGB", t]
        self.IOSUG = pd.Series(iosug0[tb].values, index=C)  # constant over T

        # ---- 1.1.15/1.1.16 macro, margins, world prices -------------------
        self.POPH = d.POPH0.copy()
        self.INCPC = d.INCPC0.copy()
        self.GDPT = d.GDPT0.copy()
        self.EXCH = d.EXCH0.copy()

        self.MARGWE = pd.Series(0.3, index=C)
        self.MARGWM = pd.Series(0.3, index=C)
        self.MARGD = pd.Series(0.0, index=C)
        d.PD0.loc[:, :] = d.PX0.values                     # PD0(C,T)=PX0(C,T)
        d.PWE0[tb] = (d.PX0[tb] / (1 - self.MARGWE)) / d.EXCH0[tb]
        d.PWM0[tb] = (d.PX0[tb] / (1 + self.MARGWM)) / d.EXCH0[tb]
        self.PWE = d.PWE0.copy()
        self.PWM = d.PWM0.copy()
        for h in d.H:                                      # QDFH0 = pc * pop
            d.QDFH0[h].loc[:, :] = (d.QDFHPC0[h].values
                                    * d.POPH0.loc[h].values[None, :] / 1000)

        # ---- 1.2 dynamic sets ---------------------------------------------
        self.IQDFHPC = {h: d.QDFHPC0[h][tb] > 0 for h in H}
        self.IQDF = d.QDF0[tb] > 0
        self.ILVOTH = pd.Series(False, index=C)
        for c in d.CLVO:
            self.ILVOTH[c] = d.QX0.loc[c, tb] > 0
        self.IFEED = pd.DataFrame(self.FEES0[tb] > 0, index=d.CFEED, columns=d.CLVS)
        self.IQDPM = (d.QDP0[tb] > 0) & (d.ELAGDP > 0)
        self.IQDL = d.QDL0[tb] > 0
        self.IQDP = d.QDP0[tb] > 0
        self.IQDC = d.QDC0[tb] > 0
        self.IAC = d.AC0[tb] > 0
        self.IQDT = d.QDT0[tb] != 0
        self.IQX = d.QX0[tb] != 0
        self.IPD = d.PD0[tb] > 0

        # tiny-value guards (ABORT statements of 1.2.2)
        for h in H:
            assert (d.QDFHPC0[h].loc[self.IQDFHPC[h], tb] >= 1e-5).all()
        assert (d.QDF0.loc[self.IQDF, tb] >= 1e-5).all()
        assert (d.QDL0.loc[self.IQDL, tb] >= 1e-5).all()
        assert (d.QDP0.loc[self.IQDP, tb] >= 1e-5).all()
        assert (d.QDC0.loc[self.IQDC, tb] >= 1e-5).all()
        assert (d.AC0.loc[self.IAC, tb] >= 1e-5).all()

        # ---- 1.3 calibrated intercepts -------------------------------------
        px = d.PX0[tb]
        # AA0: area intercept
        self.AA = _df(C, T)
        for c in C:
            if not self.IAC[c]:
                continue
            e = d.EAP.loc[c]
            mask = e != 0
            if (px[mask] <= 0).any():
                continue
            denom = float(np.prod(px[mask].values ** e[mask].values))
            if denom:
                self.AA.loc[c, tb] = d.AC0.loc[c, tb] / denom
        # AY0: yield intercept
        self.AY = _df(C, T)
        for c in C:
            if not self.IAC[c]:
                continue
            denom = px[c] ** d.EYP[c]
            if denom:
                self.AY.loc[c, tb] = d.YC0.loc[c, tb] / denom
        # ASM0: livestock supply intercept
        self.ASM = _df(C, T)
        fecost_tb = pd.Series(self.FECOST0_early[tb], index=d.CLVS)
        for c in C:
            if not self.ILVOTH[c]:
                continue
            if not fecost_tb.get(c, 0.0):
                continue
            e = d.ESP.loc[c]
            mask = e != 0
            denom = float(np.prod(px[mask].values ** e[mask].values))
            self.ASM.loc[c, tb] = (d.QX0.loc[c, tb] / denom
                                   / fecost_tb[c] ** d.INPELA[c])
        # ASUG0: sugar-crop processing intercept (constant over T)
        self.ASUG = _df(C, T)
        for c in ["SUGC", "SUGB"]:
            a = d.QDP0.loc[c, tb] / ((px["SUGA"] / d.PD0.loc[c, tb])
                                     ** d.SUGOUTELA[c])
            self.ASUG.loc[c, :] = a
        # AFH0: food demand intercept
        self.AFH = {h: _df(C, T) for h in H}
        for h in H:
            iq = self.IQDFHPC[h]
            pdv = d.PD0[tb]
            for c in C:
                if not iq[c]:
                    continue
                e = d.EDFPH[h].loc[c]
                mask = iq.values  # CP$IQDFHPC(CP,H)
                denom = float(np.prod(pdv.values[mask] ** e.values[mask]))
                denom *= d.INCPC0.loc[h, tb] ** d.EDFIH.loc[c, h]
                if denom:
                    self.AFH[h].loc[c, tb] = d.QDFHPC0[h].loc[c, tb] / denom
        # AFE0: feed demand intercept (=1 where defined)
        self.AFE = {t: np.zeros_like(self.FEES0[tb]) for t in T}
        qx_lvs = d.QX0.loc[d.CLVS, tb].values
        with np.errstate(divide="ignore", invalid="ignore"):
            denom = self.IOXL.values * qx_lvs[None, :]
            afe_tb = np.where(self.IFEED.values & (denom != 0),
                              self.FEES0[tb] / np.where(denom != 0, denom, 1), 0.0)
        self.AFE[tb] = afe_tb
        # AP0: processing demand intercept
        self.AP = _df(C, T)
        popsum = d.POPH0[tb].sum()
        for c in C:
            if not self.IQDPM[c]:
                continue
            denom = (d.PD0.loc[c, tb] ** d.ELAP[c]
                     * d.GDPT0[tb] ** d.ELAGDP[c]
                     * popsum ** d.ELAPOP[c])
            self.AP.loc[c, tb] = d.QDP0.loc[c, tb] / denom
        # 1.3.1.2.8 final FECOST0 (recomputed with PD0 = PX0)
        self.FECOST0 = {t: self.FEES0[t].T @ d.PD0.loc[d.CFEED, t].values
                        for t in T}
        # EDFIHT(C,H,T) = EDFIH0 : income elasticity constant over time
        self.EDFIHT = d.EDFIH.copy()


H = ["HHDHR", "HHDHU", "HHDOR", "HHDOU"]
