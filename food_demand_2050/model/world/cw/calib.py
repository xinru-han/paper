"""SILK-MGA calibration layer (port of the parameter-computation part of
bench.gms).

Given base-year (2023) quantities from :class:`silk.data.Data`, this builds:
  * processed elasticities (with partial-adjustment (1-lambda) scaling),
  * the base price block (PRF0, PRFC0, PIM0, PEX0, PDOM0, PCN0, PFE0, PPR0),
  * the trade-partition indicator sets (impr/expr, imp2/exp2/impz/expz),
  * the multiplicative calibration intercepts so the model reproduces the
    base year exactly.

All quantities/prices are stored as (nI, nR) numpy arrays aligned with
Data.I / Data.R.  Prices are in thousand-USD per tonne (GAMS divides the
raw USD/t world prices by 1000).
"""

from __future__ import annotations

import numpy as np


def _up(s):
    return s.strip().upper()


class Calibration:
    # partial-adjustment speeds
    LAM_CROP = 0.10        # crops, oilseed crush, dairy
    LAM_MEAT = 0.25        # meat incl. milk supply
    LAM_YLD = 0.10
    LAM_MLKP = 0.20        # milk demand (PROCEQ)
    ESTELA = -0.10         # stock price elasticity

    def __init__(self, data):
        self.d = data
        self._arrays()
        self._elasticities()
        self._base_prices()
        self._trade_partition()
        self._intercepts()

    # ------------------------------------------------------------------
    def _msk(self, cset):
        """(nI,) boolean mask for a commodity subset."""
        m = np.zeros(self.d.nI, dtype=bool)
        for c in cset:
            if _up(c) in self.d.ii:
                m[self.d.ii[_up(c)]] = True
        return m

    def _par2(self, table, transpose=False):
        """(i,r)->value dict to (nI,nR) array."""
        a = np.zeros((self.d.nI, self.d.nR))
        for k, v in table.items():
            i, r = (k[0], k[1])
            if _up(i) in self.d.ii and _up(r) in self.d.ri:
                a[self.d.ii[_up(i)], self.d.ri[_up(r)]] = v
        return a

    def _arrays(self):
        d = self.d
        self.m_crop = self._msk(d.crop)
        self.m_meat = self._msk(d.meat)
        self.m_milk = self._msk(d.milk)
        self.m_dairy = self._msk(d.dairy)
        self.m_oilseed = self._msk(d.oilseed)
        self.m_oil = self._msk(d.oil)
        self.m_meal = self._msk(d.meal)
        self.m_feed = self._msk(d.feed)
        self.m_food = self._msk(d.food)
        self.m_itrd = self._msk(d.itrd)
        self.m_intrd = self._msk(d.intrd)
        self.m_sugar = self._msk(d.sugar)
        self.m_scsb = self._msk(d.scsb)
        self.m_fuel = self._msk(d.fuel)
        self.m_feedstock = self._msk(d.feedstock)
        self.m_progcrop = self._msk(d.progcrop)

    # ------------------------------------------------------------------
    def _elasticities(self):
        d = self.d
        ela = d.ep["ELA"]
        sup = np.zeros((d.nI, d.nR))
        imp = np.zeros((d.nI, d.nR))
        inp = np.zeros((d.nI, d.nR))
        for (i, r, fld), v in ela.items():
            if _up(i) not in d.ii or _up(r) not in d.ri:
                continue
            a = {"SUPELA": sup, "IMPELA": imp, "INPELA": inp}.get(_up(fld))
            if a is not None:
                a[d.ii[_up(i)], d.ri[_up(r)]] = v
        # oto yield elasticity forced tiny
        if "OTO" in d.ii:
            sup[d.ii["OTO"], :] = 0.001
        self.yldela = sup.copy()
        self.impela = imp.copy()
        self.expela = -imp.copy()
        self.inpela = inp.copy()

        # per-commodity lambda vector
        lam = np.full(d.nI, self.LAM_CROP)
        lam[self.m_meat] = self.LAM_MEAT
        self.lam = lam
        # (1-lambda) scaling of the price-response elasticities
        s_crop = (1.0 - self.LAM_CROP)
        s_meat = (1.0 - self.LAM_MEAT)
        s_yld = (1.0 - self.LAM_YLD)
        s_mlkp = (1.0 - self.LAM_MLKP)
        self.yldela *= s_yld
        # 3-D cross elasticities scaled and stored as dicts of arrays
        self.yahela = self._scaled_cross(d.ep["YAHELA"], s_crop)   # (i,j,r)
        self.metelap = self._scaled_cross(d.ep["METELAP"], s_meat)
        self.oilela = self._scaled_cross(d.ep["OILELA"], s_crop)
        self.daielap = self._scaled_cross(d.ep["DAIELAP"], s_crop)
        self.fodela = self._scaled_cross(d.ep["FODELA"], 1.0)      # demand: no λ
        self.inpela_meat = self.inpela * s_meat
        # milk demand elasticity (r,)
        self.mlkela = np.zeros(d.nR)
        for (r,), v in d.ep["MLKELA"].items():
            if _up(r) in d.ri:
                self.mlkela[d.ri[_up(r)]] = v * s_mlkp
        # gdp elasticity for food demand (i,r)
        self.gdpela = self._par2(d.ep["GDPELA"])

    def _scaled_cross(self, table, scale):
        """(i,j,r)->value dict scaled by ``scale``; returned as nested dict
        keyed (i_idx, j_idx, r_idx)->value for sparse use."""
        d = self.d
        out = {}
        for (i, j, r), v in table.items():
            if _up(i) in d.ii and _up(j) in d.ii and _up(r) in d.ri:
                out[(d.ii[_up(i)], d.ii[_up(j)], d.ri[_up(r)])] = v * scale
        return out

    # ------------------------------------------------------------------
    def _base_prices(self):
        d = self.d
        q = d.q0
        base = d.base
        # world price (thousand USD/t)
        bp = d.ep["BASPRICE"]
        PRF0 = np.zeros(d.nI)
        for c, i in d.ii.items():
            PRF0[i] = bp.get((base, c), 0.0) / 1000.0
        self.PRF0 = PRF0
        # real exchange rate (r,)
        rx = np.ones(d.nR)
        for r, ri in d.ri.items():
            rx[ri] = d.macro["RXCHRATE"].get((r, base), 1.0)
        self.rxch = rx
        # local-currency world price
        self.PRFC0 = (PRF0[:, None] * rx[None, :])            # (i,r), TRANSM=1

        # tariffs & policy
        Tm = self._tariff("TMBASE") / 100.0
        Tm2 = self._tariff("TM2BASE") / 100.0
        self.Tm, self.Tm2 = Tm, Tm2
        TRANS = np.zeros(d.nI)
        for (c,), v in d.trans["TRANSFACT"].items():
            if _up(c) in d.ii:
                TRANS[d.ii[_up(c)]] = v
        self.TRANS = TRANS
        tsmk = self._par2(d.ep["TSMARKUPB"])
        # consumer tax & quota from policy(i,r,field)
        pol = d.ep["POLICY"]
        Tc = np.zeros((d.nI, d.nR))
        quota = np.zeros((d.nI, d.nR))
        for (i, r, fld), v in pol.items():
            if _up(i) not in d.ii or _up(r) not in d.ri:
                continue
            ii, rr = d.ii[_up(i)], d.ri[_up(r)]
            if _up(fld) == "TCBASE":
                Tc[ii, rr] = v
            elif _up(fld) == "TARQTA0":
                quota[ii, rr] = v / 1000.0     # same /1000 scaling as quantities
        self.Tc = Tc
        self.quota = quota
        # TRQ regime indicator Z0: 1 above quota (or quota==0), else 0
        IMP0 = q["IMP"]
        Z0 = np.where((quota <= 0) | (IMP0 > quota), 1.0, 0.0)
        self.Z0 = Z0

        self.PIM0 = (1.0 + Tm + Z0 * Tm2) * self.PRFC0 + TRANS[:, None] + tsmk
        self.PEX0 = self.PRFC0.copy()                          # expSub=0
        EXP0 = q["EXP"]
        with np.errstate(divide="ignore", invalid="ignore"):
            theta = np.where(EXP0 + IMP0 > 0, EXP0 / (EXP0 + IMP0), 0.5)
        self.theta = theta
        PDOM0 = theta * self.PEX0 + (1.0 - theta) * self.PIM0
        # non-traded -> domestic = local world price
        PDOM0 = np.where(self.m_intrd[:, None], self.PRFC0, PDOM0)
        # milk & dairy hard-coded price relations (per region)
        ii = d.ii
        if "MLK" in ii:
            imlk = ii["MLK"]
            if "BUT" in ii and "NDM" in ii:
                PDOM0[imlk, :] = 0.9 * (PDOM0[ii["BUT"], :] / 21.80 +
                                        PDOM0[ii["NDM"], :] / 10.59)
            if "FMK" in ii:
                PDOM0[ii["FMK"], :] = PDOM0[imlk, :] / 0.9
            if "ODA" in ii:
                PDOM0[ii["ODA"], :] = PDOM0[imlk, :] * 5.0 / 0.9
        self.PDOM0 = PDOM0
        self.PCN0 = (1.0 + Tc) * PDOM0
        # feed price
        FEEDPRFAC = np.zeros((d.nI, d.nR))
        for c in ("WHE", "OCG"):
            if c in ii and "JPN" in d.ri:
                FEEDPRFAC[ii[c], d.ri["JPN"]] = 1.0
        self.FEEDPRFAC = FEEDPRFAC
        self.PFE0 = self.PCN0 + FEEDPRFAC * (self.PRFC0 - self.PCN0)
        # producer price: no target-price wedge in the baseline benchmark
        self.TW0 = np.zeros((d.nI, d.nR))
        self.PPR0 = PDOM0 + self.TW0

    def _tariff(self, name):
        d = self.d
        a = np.zeros((d.nI, d.nR))
        for (i, r, t), v in d.tar[name].items():
            if t == d.base and _up(i) in d.ii and _up(r) in d.ri:
                a[d.ii[_up(i)], d.ri[_up(r)]] = v
        return a

    # ------------------------------------------------------------------
    def _trade_partition(self):
        d = self.d
        q = d.q0
        EXP0, IMP0 = q["EXP"], q["IMP"]
        traded = self.m_itrd[:, None] & np.ones((1, d.nR), dtype=bool)
        # net importer -> import is residual (impr); else export residual
        impr = traded & (EXP0 <= IMP0)
        expr = traded & ~impr
        self.impr, self.expr = impr, expr
        # behavioral trade functions' calibrated constants
        with np.errstate(divide="ignore", invalid="ignore"):
            consimp = np.where(self.PIM0 > 0, IMP0 / self.PIM0 ** self.impela, 0.0)
            consexp = np.where(self.PEX0 > 0, EXP0 / self.PEX0 ** self.expela, 0.0)
        self.consimp = np.nan_to_num(consimp)
        self.consexp = np.nan_to_num(consexp)
        self.imp2 = impr & (self.consexp > 0)
        self.impz = impr & (self.consexp <= 0)
        self.exp2 = expr & (self.consimp > 0)
        self.expz = expr & (self.consimp <= 0)

    # ------------------------------------------------------------------
    def _intercepts(self):
        """Multiplicative intercepts calibrated so equations reproduce base.

        Uses the base(2023)/prev(2022) ratio in the lagged terms, which embeds
        the one-year growth as the perpetual baseline trend (GAMS behavior).
        """
        d = self.d
        q = d.q0
        b, p = d.base, d.prev
        AREA0, PRD0, YLD0 = q["AREA"], q["PRD"], q["YLD"]
        AREAp = d.raw[("area", p)]
        PRDp = d.raw[("prd", p)]
        YLDp = d.raw[("yield", p)]
        eps = 1e-12

        # area intercept: AHV = consarea * AHV_lag^λ * Π PPR^yahela
        # calibrate consarea so base reproduces (holding prices at base)
        lam = self.LAM_CROP
        price_area = self._cross_price_term(self.yahela, self.PPR0)  # (i,r)
        with np.errstate(divide="ignore", invalid="ignore"):
            self.consarea = np.where(
                self.m_crop[:, None] & (AREA0 > 0),
                AREA0 / (np.maximum(AREAp, eps) ** lam * price_area), 0.0)
        # yield intercept
        self.consyld = np.where(
            self.m_crop[:, None] & (YLD0 > 0),
            YLD0 / (np.maximum(YLDp, eps) ** self.LAM_YLD *
                    self.PPR0 ** self.yldela), 0.0)
        # meat supply intercept (feed-cost term deferred; set feCost^inp=1 here
        # by folding it into conslive at base)
        price_meat = self._cross_price_term(self.metelap, self.PPR0)
        with np.errstate(divide="ignore", invalid="ignore"):
            self.conslive = np.where(
                self.m_meat[:, None] & (PRD0 > 0),
                PRD0 / (np.maximum(PRDp, eps) ** self.LAM_MEAT * price_meat), 0.0)
        self.consarea = np.nan_to_num(self.consarea)
        self.consyld = np.nan_to_num(self.consyld)
        self.conslive = np.nan_to_num(self.conslive)
        # NOTE: crush/dairy/demand/biofuel/stock intercepts are added in the
        # model build step; this layer establishes prices + supply intercepts.

    def _cross_price_term(self, cross, price):
        """Π_j price[j,r]^cross(i,j,r) as (nI,nR) array."""
        d = self.d
        out = np.ones((d.nI, d.nR))
        for (i, j, r), e in cross.items():
            pj = price[j, r]
            if pj > 0:
                out[i, r] *= pj ** e
        return out

    # ------------------------------------------------------------------
    def summary(self):
        d = self.d
        ri = d.ri["CHN"]
        print("SILK calibration — China base prices (thousand USD-equiv/t):")
        for c in ["RIC", "WHE", "CRN", "SBS", "BFV", "PRK"]:
            i = d.ii[c]
            print(f"  {c}: PRF0={self.PRF0[i]:.4f} PRFC0={self.PRFC0[i,ri]:.4f} "
                  f"PIM0={self.PIM0[i,ri]:.4f} PDOM0={self.PDOM0[i,ri]:.4f} "
                  f"PCN0={self.PCN0[i,ri]:.4f}")
        print("trade partition counts: imp2=%d exp2=%d impz=%d expz=%d" % (
            self.imp2.sum(), self.exp2.sum(), self.impz.sum(), self.expz.sum()))


if __name__ == "__main__":
    import os
    import warnings
    warnings.filterwarnings("ignore")
    from cw.data import Data
    dirp = os.environ.get("SILK_DIR", "/root/data/CASM/SILK Model/baseline/2027")
    d = Data(dirp)
    Calibration(d).summary()
