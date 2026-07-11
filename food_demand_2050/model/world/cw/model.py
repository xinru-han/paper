"""SILK-MGA model layer: reduced MCP and world-price solver.

Reduction (analogous to the CASM port): the only globally-coupled unknowns
are the **world prices** ``PRF(i)`` of the traded commodities.  Given PRF,
each region's price block (PRFC, PIM, PEX, PDOM, PCN, PFE, PPR) is a closed
formula (trade shares ``theta`` are fixed at base), every supply/demand
quantity follows from the behavioral equations, net trade ``NET`` and the
gross import/export closure follow, and the world market-clearing condition

    sum_r EXP(i,r) = sum_r IMP(i,r)    for every traded i

pins ``PRF(i)``.  We solve that square system with a Newton iteration
(Fischer–Burmeister is only needed where a gross-flow non-negativity bound
binds; at/near the benchmark the bounds are slack).

All quantities are vectorized over (nI, nR).  Lagged levels enter as data
(previous-year quantities); the multiplicative intercepts are calibrated so
that evaluating the equations at the base prices with the previous-year lag
reproduces the base-year quantities exactly.
"""

from __future__ import annotations

import numpy as np


class Model:
    def __init__(self, data, calib):
        self.d = data
        self.c = calib
        self._prep()
        self._calibrate_intercepts()

    # ------------------------------------------------------------------
    def _prep(self):
        d, c = self.d, self.c
        self.nI, self.nR = d.nI, d.nR
        # previous-year (lag) quantity levels
        p = d.prev
        self.AHVlag = d.raw[("area", p)]
        self.YLDlag = d.raw[("yield", p)]
        self.PRDlag = d.raw[("prd", p)]
        self.CRUlag = d.raw[("cru", p)]
        self.CONlag = d.raw[("con", p)]
        self.ESTlag = d.raw[("endstk", p)]           # begin-of-base stock (2022 EOP)
        self.EST0 = d.q0["END"]                       # base-year ending stock
        self.PRFClag = c.PRF0[:, None] * self._rxch(p)

        # which traded commodities carry a world-price unknown
        self.traded_i = np.array(sorted(
            {i for i in range(self.nI) if c.m_itrd[i]}))
        # macro drivers at base
        self.POP0 = self._region_series("POP", d.base)
        self.RGDP0 = self._region_series("RGDP", d.base)
        self.pcrgdp0 = self.RGDP0 / np.maximum(self.POP0, 1e-9) * 1e6
        # oilseed crush conversion (ert): oil/meal output per unit seed
        self.ert = self._crush_ratios()
        # feed distribution shares fdist(feed,meat,r)
        self.fdist = c._scaled_cross(d.ep["FDIST"], 1.0)  # (feed,meat,r)->share

    def _rxch(self, year):
        d = self.d
        rx = np.ones(self.nR)
        for r, ri in d.ri.items():
            rx[ri] = d.macro["RXCHRATE"].get((r, year), 1.0)
        return rx

    def _region_series(self, sym, year):
        d = self.d
        a = np.zeros(self.nR)
        for r, ri in d.ri.items():
            a[ri] = d.macro[sym].get((r, year), 0.0)
        return a

    def _crush_ratios(self):
        """ert[(seed_i, out_j, r)] = PRD0(out)/CRU0(seed) from base data."""
        d, c = self.d, self.c
        q = d.q0
        ert = {}
        for seed, (oil, meal) in d.seed2om.items():
            si = d.ii[seed]
            for out in (oil, meal):
                oi = d.ii[out]
                for r in range(self.nR):
                    cru = q["CRU"][si, r]
                    if cru > 1e-9:
                        ert[(si, oi, r)] = q["PRD"][oi, r] / cru
        return ert

    # ------------------------------------------------------------------
    def set_year(self, year):
        """Point the model at a projection year's macro drivers, exchange
        rates and tariffs.  Intercepts stay fixed (calibrated at base); only
        the exogenous per-year state and the lags (set by the caller) change.
        """
        d, c = self.d, self.c
        c.rxch = self._rxch(year)
        self.POP0 = self._region_series("POP", year)
        self.RGDP0 = self._region_series("RGDP", year)
        self.pcrgdp0 = self.RGDP0 / np.maximum(self.POP0, 1e-9) * 1e6
        # per-year tariffs -> import-parity wedge
        c.Tm = self._tariff_year("TMBASE", year) / 100.0
        c.Tm2 = self._tariff_year("TM2BASE", year) / 100.0
        self.year = year

    def _tariff_year(self, name, year):
        d = self.d
        a = np.zeros((self.nI, self.nR))
        for (i, r, t), v in d.tar[name].items():
            if t == year and i.upper() in d.ii and r.upper() in d.ri:
                a[d.ii[i.upper()], d.ri[r.upper()]] = v
        return a

    def _prices(self, PRF):
        """Full price block (nI,nR) from world prices PRF (nI,)."""
        d, c = self.d, self.c
        rxch = c.rxch
        PRFC = PRF[:, None] * rxch[None, :]
        PIM = (1.0 + c.Tm + c.Z0 * c.Tm2) * PRFC + c.TRANS[:, None]
        PEX = PRFC.copy()
        PDOM = c.theta * PEX + (1.0 - c.theta) * PIM
        PDOM = np.where(c.m_intrd[:, None], PRFC, PDOM)
        ii = d.ii
        if "MLK" in ii and "BUT" in ii and "NDM" in ii:
            imlk = ii["MLK"]
            PDOM[imlk, :] = 0.9 * (PDOM[ii["BUT"], :] / 21.80 +
                                   PDOM[ii["NDM"], :] / 10.59)
            if "FMK" in ii:
                PDOM[ii["FMK"], :] = PDOM[imlk, :] / 0.9
            if "ODA" in ii:
                PDOM[ii["ODA"], :] = PDOM[imlk, :] * 5.0 / 0.9
        PCN = (1.0 + c.Tc) * PDOM
        PFE = PCN + c.FEEDPRFAC * (PRFC - PCN)
        PPR = PDOM + c.TW0
        return dict(PRFC=PRFC, PIM=PIM, PEX=PEX, PDOM=PDOM, PCN=PCN,
                    PFE=PFE, PPR=PPR)

    def _cross(self, cross, price, base=None):
        """Π_j price[j,r]^cross(i,j,r) as (nI,nR)."""
        out = np.ones((self.nI, self.nR))
        for (i, j, r), e in cross.items():
            pj = price[j, r]
            if pj > 0:
                out[i, r] *= pj ** e
        return out

    # ------------------------------------------------------------------
    def _quantities(self, pr, lag, inter):
        """Compute all supply/demand quantities given prices ``pr`` (dict),
        lag levels ``lag`` (dict), and intercepts ``inter`` (dict)."""
        d, c = self.d, self.c
        PPR, PCN, PFE, PRFC = pr["PPR"], pr["PCN"], pr["PFE"], pr["PRFC"]
        nI, nR = self.nI, self.nR

        # ---- crop area & yield ----
        area_price = self._cross(c.yahela, PPR)
        AHV = inter["consarea"] * np.where(lag["AHV"] > 0, lag["AHV"], 0.0) \
            ** c.LAM_CROP * area_price
        YLD = inter["consyld"] * np.where(lag["YLD"] > 0, lag["YLD"], 0.0) \
            ** c.LAM_YLD * np.where(PPR > 0, PPR, 1.0) ** c.yldela
        PRD = np.zeros((nI, nR))
        PRD = np.where(c.m_crop[:, None], AHV * YLD, PRD)

        # ---- meat & milk supply (feed-cost term) ----
        feCost = self._fecost(PFE)
        meat_price = self._cross(c.metelap, PPR)
        inp = np.where(feCost > 0, feCost, 1.0) ** c.inpela_meat
        PRD_meat = inter["conslive"] * np.where(lag["PRD"] > 0, lag["PRD"], 0.0) \
            ** c.LAM_MEAT * meat_price * inp
        PRD = np.where(c.m_meat[:, None], PRD_meat, PRD)

        # ---- oilseed crush -> oil & meal ----
        MGN = self._margin(PPR, PCN)
        crush_price = self._cross(c.oilela, MGN)
        CRU = inter["conscru"] * np.where(lag["CRU"] > 0, lag["CRU"], 0.0) \
            ** c.LAM_CROP * crush_price
        CRU = np.where(c.m_oilseed[:, None], CRU, 0.0)
        # oil/meal production from crush
        for seed, (oil, meal) in d.seed2om.items():
            si = d.ii[seed]
            for out in (oil, meal):
                oi = d.ii[out]
                for r in range(nR):
                    if (si, oi, r) in self.ert:
                        PRD[oi, r] += CRU[si, r] * self.ert[(si, oi, r)]

        # ---- dairy products (proportional to milk production) ----
        dairy_price = self._cross(c.daielap, PPR)
        if "MLK" in d.ii:
            mlk_prd = PRD[d.ii["MLK"], :]
            for cc in d.dairy:
                di = d.ii[cc]
                ratio = np.where(lag["PRD"][d.ii["MLK"], :] > 0,
                                 lag["PRD"][di, :] /
                                 np.maximum(lag["PRD"][d.ii["MLK"], :], 1e-9),
                                 0.0) ** c.LAM_CROP
                PRD[di, :] = inter["consdai"][di, :] * ratio * \
                    dairy_price[di, :] * mlk_prd

        # ---- food demand ----
        food_price = self._cross(c.fodela, PCN)
        PCFOO = inter["consfoo"] * food_price * \
            self.pcrgdp0 ** c.gdpela
        FOO = PCFOO * self.POP0[None, :] / 1e6
        FOO = np.where(c.m_food[:, None], FOO, 0.0)
        # sugar-crop "food" demand = input to sugar production (behavioral)
        isug = d.ii.get("SUG")
        for cc in d.scsb:
            si = d.ii[cc]
            e_out = inter["sugOutEla"].get(si, np.zeros(nR))
            e_in = inter["sugInpEla"].get(si, np.zeros(nR))
            if isug is not None:
                pterm = np.where(PPR[isug] > 0, PPR[isug], 1.0) ** e_out * \
                    np.where(PCN[isug] > 0, PCN[isug], 1.0) ** e_in
            else:
                pterm = 1.0
            FOO[si, :] = inter["consSugDem"][si, :] * pterm

        # ---- biofuel / sugar / ddg production (held at base for benchmark;
        #      responsive block to be added for projections) ----
        # OTO (other oilseed oil) is a 'crop' with no harvested area in the
        # data (produced as a byproduct); hold at base like the fuel/sugar block
        for cc in ("ETH", "BDI", "DDG", "SUG", "OTO"):
            if cc in d.ii:
                PRD[d.ii[cc], :] = inter["PRD0"][d.ii[cc], :]

        # ---- feed demand ----
        FEES, FEE = self._feed(PRD, PFE, inter)

        # ---- other use (scales with total tracked use) ----
        FUE = inter["FUE0"].copy()          # fuel demand held at base (simplified)
        OTH = self._other(FUE, FOO, FEE, CRU, inter)

        # ---- consumption & stock ----
        # EST(t) = EST(t-1) * (PRFC(t)/PRFC(t-1))^ESTELA ; at the base year the
        # lag IS the base ending stock at base PRFC, so the ratio is 1 and the
        # base ending stock is reproduced (GAMS ESTBASEEQ).
        est_lag = lag.get("EST", self.EST0)
        prfc_lag = lag.get("PRFClag", self.c.PRF0[:, None] * self.c.rxch[None, :])
        EST = est_lag * np.where(prfc_lag > 0,
                                 PRFC / np.maximum(prfc_lag, 1e-9),
                                 1.0) ** c.ESTELA
        CON = FUE + FOO + FEE + OTH + CRU
        # milk consumption via processing margin
        if "MLK" in d.ii:
            CON[d.ii["MLK"], :] = self._milk_con(pr, lag, inter)
            PRD_mlk = PRD[d.ii["MLK"], :]
            # milk & non-traded: consumption pinned to production
        NET = PRD + self.ESTlag - CON - EST
        return dict(AHV=AHV, YLD=YLD, PRD=PRD, CRU=CRU, MGN=MGN, FOO=FOO,
                    FEE=FEE, FEES=FEES, FUE=FUE, OTH=OTH, CON=CON, EST=EST,
                    NET=NET, feCost=feCost)

    def _fecost(self, PFE):
        """feCost(meat,r) = Σ_feed FEES0(feed,meat,r)*PFE(feed,r) (base qty)."""
        d, c = self.d, self.c
        q = d.q0
        fe = np.zeros((self.nI, self.nR))
        for (feed, meat, r), sh in self.fdist.items():
            # base feed used by meat = FEE0(feed)*fdist(feed,meat)
            fees0 = q["FEE"][feed, r] * sh
            fe[meat, r] += fees0 * PFE[feed, r]
        return fe

    def _margin(self, PPR, PCN):
        """MGN(oilseed,r) = Σ_out ert*PPR(out)/PCN(seed)."""
        MGN = np.zeros((self.nI, self.nR))
        for (si, oi, r), e in self.ert.items():
            if PCN[si, r] > 0:
                MGN[si, r] += e * PPR[oi, r] / PCN[si, r]
        return MGN

    def _feed(self, PRD, PFE, inter):
        d, c = self.d, self.c
        FEES = np.zeros((self.nI, self.nR))
        # FEES(feed,meat) = consfee*PRD(meat)*fr(feed,meat)*Π PFE^fedela
        for (feed, meat, r), fr in inter["fr"].items():
            price = 1.0
            # fedela(meat,feed,feedj,r): own-price approx via feedj=feed
            e = inter["fedela_own"].get((meat, feed, r), 0.0)
            if PFE[feed, r] > 0 and e:
                price = PFE[feed, r] ** e
            FEES[feed, r] += inter["consfee"] * PRD[meat, r] * fr * price
        FEE = FEES + inter["FEE_OTH"]
        return FEES, FEE

    def _other(self, FUE, FOO, FEE, CRU, inter):
        d, c = self.d, self.c
        base = inter["use0"]
        cur = FUE + FOO + FEE + CRU
        with np.errstate(divide="ignore", invalid="ignore"):
            # where a commodity has no tracked use at base (all consumption
            # is 'other', e.g. China cotton under CASM accounting), hold OTH
            # at its base level instead of scaling by an empty ratio
            ratio = np.where(base > 1e-9, cur / base, 1.0)
        OTH = inter["OTH0"] * ratio
        return OTH

    def _milk_con(self, pr, lag, inter):
        d, c = self.d, self.c
        q = d.q0
        PPR, PCN = pr["PPR"], pr["PCN"]
        imlk = d.ii["MLK"]
        rev = np.zeros(self.nR)
        for cc in d.dairy:
            di = d.ii[cc]
            rev += q["PRD"][di, :] * PPR[di, :]
        denom = np.maximum(q["CON"][imlk, :] * PCN[imlk, :], 1e-5)
        margin = np.where(denom > 0, rev / denom, 0.0)
        conlag = np.where(lag["CON"][imlk, :] > 0, lag["CON"][imlk, :], 0.0)
        return inter["consmlk"] * conlag ** c.LAM_MLKP * \
            margin ** c.mlkela

    # ------------------------------------------------------------------
    def _calibrate_intercepts(self):
        """Set every intercept so the base prices + prev lag reproduce base."""
        d, c = self.d, self.c
        q = d.q0
        pr = self._prices(c.PRF0)
        lag = dict(AHV=self.AHVlag, YLD=self.YLDlag, PRD=self.PRDlag,
                   CRU=self.CRUlag, CON=self.CONlag)
        nI, nR = self.nI, self.nR
        one = np.ones((nI, nR))
        inter = {}

        # supply intercepts (already have area/yield/meat from calib, but
        # recompute here consistently including feed-cost term for meat)
        area_price = self._cross(c.yahela, pr["PPR"])
        inter["consarea"] = self._solve_int(
            q["AREA"], self.AHVlag ** c.LAM_CROP * area_price, c.m_crop)
        inter["consyld"] = self._solve_int(
            q["YLD"], self.YLDlag ** c.LAM_YLD *
            np.where(pr["PPR"] > 0, pr["PPR"], 1.0) ** c.yldela, c.m_crop)
        feCost = self._fecost(pr["PFE"])
        meat_price = self._cross(c.metelap, pr["PPR"])
        inp = np.where(feCost > 0, feCost, 1.0) ** c.inpela_meat
        inter["conslive"] = self._solve_int(
            q["PRD"], self.PRDlag ** c.LAM_MEAT * meat_price * inp, c.m_meat)

        # crush
        MGN = self._margin(pr["PPR"], pr["PCN"])
        crush_price = self._cross(c.oilela, MGN)
        inter["conscru"] = self._solve_int(
            q["CRU"], self.CRUlag ** c.LAM_CROP * crush_price, c.m_oilseed)

        # dairy
        consdai = np.zeros((nI, nR))
        dairy_price = self._cross(c.daielap, pr["PPR"])
        imlk = d.ii.get("MLK")
        if imlk is not None:
            for cc in d.dairy:
                di = d.ii[cc]
                for r in range(nR):
                    ratio = ((self.PRDlag[di, r] /
                              max(self.PRDlag[imlk, r], 1e-9)) ** c.LAM_CROP
                             if self.PRDlag[imlk, r] > 0 else 0.0)
                    denom = ratio * dairy_price[di, r] * q["PRD"][imlk, r]
                    if denom > 1e-12:
                        consdai[di, r] = q["PRD"][di, r] / denom
        inter["consdai"] = consdai

        # food demand
        food_price = self._cross(c.fodela, pr["PCN"])
        raw_foo = food_price * self.pcrgdp0 ** c.gdpela
        pcfoo0 = np.where(self.POP0[None, :] > 0,
                          q["FOO"] / np.maximum(self.POP0[None, :], 1e-9) * 1e6,
                          0.0)
        inter["consfoo"] = self._solve_int(pcfoo0, raw_foo, c.m_food)

        # feed demand: fr(feed,meat,r)=FEES0/PRD0(meat); own-price fedela
        fedela_own = {}
        fed = d.ep["FEDELA"]   # (meat,feed,feedj,r)
        for (meat, feed, feedj, r), e in fed.items():
            if feed == feedj:
                mi = d.ii.get(meat.upper()); fi = d.ii.get(feed.upper())
                ri = d.ri.get(r.upper())
                if None not in (mi, fi, ri):
                    fedela_own[(mi, fi, ri)] = e
        # fr folds in the base own-price term so FEES reproduces base:
        #   FEES = fr*PRD(meat)*PFE(feed)^e  with fr = FEES0/(PRD0*PFE0^e)
        fr = {}
        for (feed, meat, r), sh in self.fdist.items():
            fees0 = q["FEE"][feed, r] * sh
            prd0 = q["PRD"][meat, r]
            if prd0 > 1e-9:
                e = fedela_own.get((meat, feed, r), 0.0)
                pfe0 = pr["PFE"][feed, r]
                base_price = pfe0 ** e if (pfe0 > 0 and e) else 1.0
                fr[(feed, meat, r)] = fees0 / (prd0 * base_price)
        inter["fr"] = fr
        inter["fedela_own"] = fedela_own
        inter["consfee"] = 1.0    # folded into fr (base reproduces at consfee=1)
        # FEE_OTH constant = FEE0 - Σ_meat FEES0
        fees0_sum = np.zeros((nI, nR))
        for (feed, meat, r), sh in self.fdist.items():
            fees0_sum[feed, r] += q["FEE"][feed, r] * sh
        inter["FEE_OTH"] = q["FEE"] - fees0_sum

        # fuel demand held at base; other-use base bookkeeping
        inter["FUE0"] = q["FUE"].copy()
        inter["OTH0"] = q["OTH"].copy()
        inter["use0"] = q["FUE"] + q["FOO"] + q["FEE"] + q["CRU"]
        inter["PRD0"] = q["PRD"].copy()

        # sugar-crop demand: FOO(scsb)=consSugDem*PPR(sug)^sugOutEla*PCN(sug)^sugInpEla
        sugOut = {}; sugIn = {}
        for (i, r), v in d.bio["SUGOUTELA"].items():
            if i.upper() in d.ii and r.upper() in d.ri:
                sugOut.setdefault(d.ii[i.upper()], np.zeros(nR))[d.ri[r.upper()]] = v
        for (i, r), v in d.bio["SUGINPELA"].items():
            if i.upper() in d.ii and r.upper() in d.ri:
                sugIn.setdefault(d.ii[i.upper()], np.zeros(nR))[d.ri[r.upper()]] = v
        inter["sugOutEla"] = sugOut
        inter["sugInpEla"] = sugIn
        isug = d.ii.get("SUG")
        consSug = np.zeros((nI, nR))
        for cc in d.scsb:
            si = d.ii[cc]
            eo = sugOut.get(si, np.zeros(nR)); ei = sugIn.get(si, np.zeros(nR))
            if isug is not None:
                pterm = np.where(pr["PPR"][isug] > 0, pr["PPR"][isug], 1.0) ** eo * \
                    np.where(pr["PCN"][isug] > 0, pr["PCN"][isug], 1.0) ** ei
            else:
                pterm = np.ones(nR)
            consSug[si, :] = np.where(pterm > 1e-12, q["FOO"][si, :] / pterm, 0.0)
        inter["consSugDem"] = consSug

        # milk consumption intercept
        if imlk is not None:
            rev = np.zeros(nR)
            for cc in d.dairy:
                rev += q["PRD"][d.ii[cc], :] * pr["PPR"][d.ii[cc], :]
            denom = np.maximum(q["CON"][imlk, :] * pr["PCN"][imlk, :], 1e-5)
            margin = np.where(denom > 0, rev / denom, 0.0)
            conlag = self.CONlag[imlk, :]
            base_m = np.where(conlag > 0, conlag, 0.0) ** c.LAM_MLKP * \
                np.where(margin > 0, margin, 1.0) ** c.mlkela
            inter["consmlk"] = np.where(base_m > 1e-12,
                                        q["CON"][imlk, :] / base_m, 0.0)
        else:
            inter["consmlk"] = np.zeros(nR)
        self.inter = inter

    def _solve_int(self, target, raw, mask):
        # the multiplicative price term ``raw`` can be legitimately tiny or
        # huge (a product of many cross-price factors); the intercept absorbs
        # it, so only guard against an exact zero.
        with np.errstate(divide="ignore", invalid="ignore"):
            val = np.where(mask[:, None] & (raw > 0) & (target > 0),
                           target / raw, 0.0)
        return np.nan_to_num(val)

    # ------------------------------------------------------------------
    def forward(self, PRF, lag=None):
        if lag is None:
            lag = dict(AHV=self.AHVlag, YLD=self.YLDlag, PRD=self.PRDlag,
                       CRU=self.CRUlag, CON=self.CONlag)
        pr = self._prices(PRF)
        v = self._quantities(pr, lag, self.inter)
        v.update(pr)
        v["PRF"] = PRF
        # gross trade closure
        EXP, IMP = self._trade(v, pr)
        v["EXP"], v["IMP"] = EXP, IMP
        # world excess for traded commodities
        excess = EXP.sum(axis=1) - IMP.sum(axis=1)
        v["excess"] = excess
        return v

    def _trade(self, v, pr):
        c = self.c
        NET = v["NET"]
        PIM, PEX = pr["PIM"], pr["PEX"]
        with np.errstate(over="ignore"):
            imp_beh = c.consimp * np.where(PIM > 0, PIM, 1.0) ** c.impela
            exp_beh = c.consexp * np.where(PEX > 0, PEX, 1.0) ** c.expela
        EXP = np.zeros((self.nI, self.nR))
        IMP = np.zeros((self.nI, self.nR))
        # exp2: importer behavioral, export residual
        m = c.exp2
        IMP[m] = imp_beh[m]
        EXP[m] = NET[m] + IMP[m]
        # expz: import only if net<0
        m = c.expz
        IMP[m] = np.maximum(0.0, -NET[m])
        EXP[m] = NET[m] + IMP[m]
        # imp2: exporter behavioral, import residual
        m = c.imp2
        EXP[m] = exp_beh[m]
        IMP[m] = EXP[m] - NET[m]
        # impz: export only if net>0
        m = c.impz
        EXP[m] = np.maximum(0.0, NET[m])
        IMP[m] = EXP[m] - NET[m]
        # clamp tiny negatives from residual closure
        EXP = np.where(EXP < 0, 0.0, EXP)
        IMP = np.where(IMP < 0, 0.0, IMP)
        return EXP, IMP

    # ------------------------------------------------------------------
    def solve_world(self, PRF0=None, lag=None, tol=1e-8, maxit=60):
        """Newton on world prices for traded commodities: excess(PRF)=0."""
        c = self.c
        ti = self.traded_i
        PRF = (c.PRF0.copy() if PRF0 is None else PRF0.copy())
        for it in range(maxit):
            v = self.forward(PRF, lag)
            F = v["excess"][ti]
            nrm = np.max(np.abs(F))
            if nrm < tol:
                break
            J = self._jac(PRF, ti, lag)
            try:
                dp = np.linalg.solve(J, -F)
            except np.linalg.LinAlgError:
                dp = np.linalg.lstsq(J, -F, rcond=None)[0]
            step = np.max(np.abs(dp / np.maximum(PRF[ti], 1e-9)))
            if step > 0.5:
                dp *= 0.5 / step
            PRF[ti] += dp
            PRF[ti] = np.maximum(PRF[ti], 1e-6)
        v = self.forward(PRF, lag)
        v["resid"] = float(np.max(np.abs(v["excess"][ti])))
        v["iters"] = it
        return v

    def _jac(self, PRF, ti, lag):
        n = len(ti)
        J = np.zeros((n, n))
        f0 = self.forward(PRF, lag)["excess"][ti]
        for k in range(n):
            h = 1e-6 * max(1.0, abs(PRF[ti[k]]))
            P2 = PRF.copy()
            P2[ti[k]] += h
            f1 = self.forward(P2, lag)["excess"][ti]
            J[:, k] = (f1 - f0) / h
        return J

    # ------------------------------------------------------------------
    def benchmark(self):
        """Verify base-year replication: forward(PRF0, prev-lag) reproduces
        base quantities and world markets clear."""
        d, c = self.d, self.c
        v = self.forward(c.PRF0)
        q = d.q0
        rep = {}
        for key, sym in [("PRD", "PRD"), ("CON", "CON"), ("AHV", "AREA"),
                         ("EXP", "EXP"), ("IMP", "IMP")]:
            a, b = v[key], q[sym]
            mask = np.abs(b) > 1e-6
            if mask.any():
                rep[key] = float(np.max(np.abs((a - b)[mask])))
        rep["world_excess"] = float(np.max(np.abs(v["excess"][self.traded_i])))
        return rep, v


if __name__ == "__main__":
    import os
    import warnings
    warnings.filterwarnings("ignore")
    from cw.data import Data
    from cw.calib import Calibration
    dirp = os.environ.get("SILK_DIR", "/root/data/CASM/SILK Model/baseline/2027")
    d = Data(dirp)
    c = Calibration(d)
    m = Model(d, c)
    rep, v = m.benchmark()
    print("SILK benchmark (2023) replication — max abs deviation from base:")
    for k, val in rep.items():
        print(f"  {k:14s} {val:.3e}")
