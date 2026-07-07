"""Translation of 2MODEL.GMS: the single-year mixed complementarity model
and a semismooth Newton solver replacing GAMS/PATH.

The MCP has the classic structure of a partial-equilibrium trade model.
Given producer prices PX every other variable of the model follows
recursively from the behavioural equations, so the year system reduces to

    TRADEEQ(c):  QX(c) + QM(c) - QE(c) - QDT(c) = 0            (PX free)
    EXPTEQ(c):   PX(c) - PWE(c)*EXCH*(1-MARGWE(c)) >= 0  perp  QE(c) >= 0
    IMPTEQ(c):   PWM(c)*EXCH*(1+MARGWM(c)) - PD(c) >= 0  perp  QM(c) >= 0

which we solve with a Fischer-Burmeister semismooth Newton method.
The reduction is exact: every dropped equation is an =E= definition whose
left-hand variable appears nowhere else upstream (verified by the
assertions in Model.__init__).
"""

from __future__ import annotations

import numpy as np

from .data import Data, TBASE
from .calib import Calibration


class YearParams:
    """Parameters entering the one-year model (updated recursively)."""

    def __init__(self, model, t):
        m, d, cal = model, model.d, model.cal
        self.t = t
        self.AY = cal.AY[t].values.copy()
        self.AA = cal.AA[t].values.copy()
        self.ASM = cal.ASM[t].values.copy()
        self.ASUG = cal.ASUG[t].values.copy()
        self.AFH = {h: cal.AFH[h][t].values.copy() for h in d.H}
        self.AFE = cal.AFE[t].copy()
        self.AP = cal.AP[t].values.copy()
        self.IOMEAL = {k: v[t] for k, v in cal.IOMEAL.items()}
        self.IOOILSD = {k: v[t] for k, v in cal.IOOILSD.items()}
        self.IOXS = cal.IOXS[t].values.copy()
        self.IOXO = cal.IOXO[t].values.copy()
        self.IOXW = cal.IOXW[t].values.copy()
        self.IOSTV = cal.IOSTV[t].values.copy()
        self.PWE = cal.PWE[t].values.copy()
        self.PWM = cal.PWM[t].values.copy()
        self.EXCH = cal.EXCH[t]
        self.POPH = {h: cal.POPH.loc[h, t] for h in d.H}
        self.INCPC = {h: cal.INCPC.loc[h, t] for h in d.H}
        self.GDPT = cal.GDPT[t]
        self.qm_fixed_zero = np.zeros(m.n, dtype=bool)  # QM.FX(...)=0 rows


class Model:
    def __init__(self, d: Data, cal: Calibration):
        self.d, self.cal = d, cal
        C = d.C
        self.n = n = len(C)
        self.cidx = {c: i for i, c in enumerate(C)}
        tb = TBASE

        idx = lambda names: np.array([self.cidx[c] for c in names], dtype=int)
        self.i_feed = idx(d.CFEED)
        self.i_lvs = idx(d.CLVS)
        self.i_oil = idx(d.COIL)
        self.i_meal = idx(d.CMEAL)

        # masks over C
        self.IAC = cal.IAC.values
        self.ILVOTH = cal.ILVOTH.values
        self.IQDT = cal.IQDT.values
        self.IQX = cal.IQX.values
        self.IPD = cal.IPD.values
        self.IQDPM = cal.IQDPM.values
        self.IQDP = cal.IQDP.values
        self.PXFREE = (d.PX0[tb] != 0).values
        self.IQDFHPC = {h: cal.IQDFHPC[h].values for h in d.H}

        # --- structural sanity: the reduction must match the GAMS pairing ---
        assert (self.PXFREE == self.IQDT).all(), "PX unknowns must equal TRADEEQ rows"
        assert (~self.IQDT | self.IPD).all(), "IMPTEQ needs PD for every IQDT row"
        # every positive base processing demand is covered by an equation
        sugcrp = np.zeros(n, dtype=bool)
        for c in d.CSUGCRP:
            sugcrp[self.cidx[c]] = True
        self.SUGCRP = sugcrp
        assert not (self.IQDPM & sugcrp).any()
        assert (~self.IQDP | self.IQDPM | sugcrp).all(), "QDP without an equation"
        # feed demand only for CFEED commodities
        qdl_pos = (d.QDL0[tb] > 0).values
        infeed = np.zeros(n, dtype=bool)
        infeed[self.i_feed] = True
        assert (~qdl_pos | infeed).all()
        # crush demand only for oilseeds
        qdc_pos = (d.QDC0[tb] > 0).values
        inoilsd = np.zeros(n, dtype=bool)
        inoilsd[idx(d.COILSD)] = True
        assert (~qdc_pos | inoilsd).all()

        # elasticities as numpy
        self.EAP = d.EAP.values
        self.EYP = d.EYP.values
        self.ESP = d.ESP.values
        self.EDFPH = {}
        for h in d.H:
            e = d.EDFPH[h].values.copy()
            e[:, ~self.IQDFHPC[h]] = 0.0  # CP restricted to IQDFHPC(CP,H)
            self.EDFPH[h] = e
        self.EDFIH = {h: d.EDFIH[h].values for h in d.H}
        self.ELAP = d.ELAP.values
        self.ELAGDP = d.ELAGDP.values
        self.ELAPOP = d.ELAPOP.values
        self.SUGOUTELA = d.SUGOUTELA.values
        self.INPELA = d.INPELA.values
        self.MARGWE = cal.MARGWE.values
        self.MARGWM = cal.MARGWM.values
        self.MARGD = cal.MARGD.values

        self.IOXL = cal.IOXL.values
        self.IOSUG = cal.IOSUG.values
        self.i_suga = self.cidx["SUGA"]
        self.MPSM = [(self.cidx[m], self.cidx[s]) for m, s in d.MPSM]
        self.MPSUGCRPA = [(self.cidx[a], self.cidx[b]) for a, b in d.MPSUGCRPA]

        # fixed base-year trade of oils and meals (2MODEL 2.1.2)
        self.QMM = np.zeros(n)
        self.QMO = np.zeros(n)
        self.QEM = np.zeros(n)
        self.QEO = np.zeros(n)
        self.QMM[self.i_meal] = d.QM0.loc[d.CMEAL, tb].values
        self.QMO[self.i_oil] = d.QM0.loc[d.COIL, tb].values
        self.QEM[self.i_meal] = d.QE0.loc[d.CMEAL, tb].values
        self.QEO[self.i_oil] = d.QE0.loc[d.COIL, tb].values

        # prices with elasticities pointing at them must be nonzero
        pxz = ~self.PXFREE
        assert not (self.EAP[self.IAC][:, pxz] != 0).any()
        assert not (self.ESP[self.ILVOTH][:, pxz] != 0).any()
        for h in d.H:
            assert not (self.EDFPH[h][self.IQDFHPC[h]][:, pxz] != 0).any()

        # residual scaling (pure conditioning, does not change the solution)
        self.scale_q = np.maximum(d.QDT0[tb].abs().values, 1.0)
        self.scale_p = np.maximum(d.PX0[tb].values, 1.0)

    # ------------------------------------------------------------------
    def forward(self, px, yp: YearParams):
        """All model variables implied by producer prices px (full C vector)."""
        n, d = self.n, self.d
        logpx = np.log(np.where(px > 0, px, 1.0))
        pd_ = np.where(self.IPD, px * (1.0 + self.MARGD), 0.0)
        logpd = np.log(np.where(pd_ > 0, pd_, 1.0))

        # supply: crops
        YC = np.zeros(n)
        AC = np.zeros(n)
        m = self.IAC
        YC[m] = yp.AY[m] * px[m] ** self.EYP[m]
        AC[m] = yp.AA[m] * np.exp(self.EAP[m] @ logpx)
        QX = np.zeros(n)
        QX[m] = YC[m] * AC[m]

        # supply: livestock (FECOST substituted in closed form)
        kcost = (yp.AFE * self.IOXL * pd_[self.i_feed][:, None]).sum(axis=0)
        lv = self.ILVOTH[self.i_lvs]
        Plvs = yp.ASM[self.i_lvs] * np.exp(self.ESP[self.i_lvs] @ logpx)
        eta = self.INPELA[self.i_lvs]
        QXl = np.zeros(len(self.i_lvs))
        pos = lv & (kcost > 0)
        QXl[pos] = (Plvs[pos] * kcost[pos] ** eta[pos]) ** (1.0 / (1.0 - eta[pos]))
        z0 = lv & (kcost == 0) & (eta == 0)
        QXl[z0] = Plvs[z0]
        QX[self.i_lvs] = np.where(self.ILVOTH[self.i_lvs], QXl, QX[self.i_lvs])
        FECOST = QXl * kcost

        # food demand
        QDFHPC = {}
        QDF = np.zeros(n)
        QDFH = {}
        for h in d.H:
            q = np.zeros(n)
            mh = self.IQDFHPC[h]
            q[mh] = (yp.AFH[h][mh] * np.exp(self.EDFPH[h][mh] @ logpd)
                     * yp.INCPC[h] ** self.EDFIH[h][mh])
            QDFHPC[h] = q
            QDFH[h] = q * yp.POPH[h] / 1000.0
            QDF += QDFH[h]

        # feed demand
        FEES = yp.AFE * self.IOXL * QXl[None, :]
        QDL = np.zeros(n)
        QDL[self.i_feed] = FEES.sum(axis=1)

        # oil and meal supply (fixed base-year trade)
        QX[self.i_meal] = QDL[self.i_meal] - self.QMM[self.i_meal] + self.QEM[self.i_meal]
        QX[self.i_oil] = QDF[self.i_oil] - self.QMO[self.i_oil] + self.QEO[self.i_oil]

        # crush demand from meal output
        QDC = np.zeros(n)
        for im, isd in self.MPSM:
            io = yp.IOMEAL[(d.C[im], d.C[isd])]
            if io:
                QDC[isd] += QX[im] / io

        # processing demand
        QDP = np.zeros(n)
        mq = self.IQDPM
        popsum = sum(yp.POPH[h] for h in d.H)
        QDP[mq] = (yp.AP[mq] * pd_[mq] ** self.ELAP[mq]
                   * yp.GDPT ** self.ELAGDP[mq] * popsum ** self.ELAPOP[mq])
        ms = self.IQDP & self.SUGCRP
        QDP[ms] = yp.ASUG[ms] * (px[self.i_suga] / px[ms]) ** self.SUGOUTELA[ms]

        # sugar output
        for isg, icrp in self.MPSUGCRPA:
            QX[isg] += self.IOSUG[icrp] * QDP[icrp]

        # remaining demand components
        QDW = yp.IOXW * QX
        QDS = np.where(self.IAC, yp.IOXS * AC, 0.0)
        QDO = yp.IOXO * QX
        STV = yp.IOSTV * QX
        QDT = np.where(self.IQDT,
                       QDF + QDL + QDS + QDP + QDC + QDO + QDW + STV, 0.0)

        return dict(PX=px, PD=pd_, YC=YC, AC=AC, QX=QX, QDF=QDF, QDFH=QDFH,
                    QDFHPC=QDFHPC, FEES=FEES, FECOST=FECOST, QDL=QDL,
                    QDC=QDC, QDP=QDP, QDW=QDW, QDS=QDS, QDO=QDO, STV=STV,
                    QDT=QDT)

    # ------------------------------------------------------------------
    def _unknown_layout(self, yp):
        iP = np.where(self.PXFREE)[0]
        iM = np.where(self.IQDT & ~yp.qm_fixed_zero)[0]
        iE = np.where(self.IQX)[0]
        return iP, iM, iE

    def residual(self, z, yp: YearParams, qm_fix_vals=None):
        n = self.n
        iP, iM, iE = self._unknown_layout(yp)
        nP, nM = len(iP), len(iM)
        px = np.zeros(n)
        px[iP] = np.exp(z[:nP])
        QM = np.zeros(n)
        if qm_fix_vals is not None:
            QM += qm_fix_vals
        QM[iM] = z[nP:nP + nM]
        QE = np.zeros(n)
        QE[iE] = z[nP + nM:]

        v = self.forward(px, yp)
        F = np.empty_like(z)
        F[:nP] = (v["QX"][iP] + QM[iP] - QE[iP] - v["QDT"][iP]) / self.scale_q[iP]

        gapE = (px[iE] - yp.PWE[iE] * yp.EXCH * (1.0 - self.MARGWE[iE])) / self.scale_p[iE]
        gapM = (yp.PWM[iM] * yp.EXCH * (1.0 + self.MARGWM[iM]) - v["PD"][iM]) / self.scale_p[iM]
        qe = QE[iE] / self.scale_q[iE]
        qm = QM[iM] / self.scale_q[iM]

        def fb(a, b):
            return np.sqrt(a * a + b * b + 1e-24) - a - b

        F[nP:nP + nM] = fb(qm, gapM)
        F[nP + nM:] = fb(qe, gapE)
        return F

    # ------------------------------------------------------------------
    def solve_year(self, yp: YearParams, px0, qm0, qe0, qm_fix_vals=None,
                   tol=1e-10, maxit=80):
        """Semismooth Newton with numerical Jacobian and line search."""
        iP, iM, iE = self._unknown_layout(yp)
        nP, nM, nE = len(iP), len(iM), len(iE)
        z = np.concatenate([np.log(px0[iP]),
                            np.maximum(qm0[iM], 0.0),
                            np.maximum(qe0[iE], 0.0)])
        F = self.residual(z, yp, qm_fix_vals)
        best = np.linalg.norm(F, np.inf)
        for it in range(maxit):
            nrm = np.linalg.norm(F, np.inf)
            if nrm < tol:
                break
            J = self._jacobian(z, F, yp, qm_fix_vals)
            try:
                dz = np.linalg.solve(J, -F)
            except np.linalg.LinAlgError:
                dz = np.linalg.lstsq(J, -F, rcond=None)[0]
            # keep the step sane in log-price space
            step = np.max(np.abs(dz[:nP])) if nP else 0.0
            if step > 2.0:
                dz *= 2.0 / step
            lam, ok = 1.0, False
            f0 = 0.5 * float(F @ F)
            for _ in range(40):
                z_try = z + lam * dz
                F_try = self.residual(z_try, yp, qm_fix_vals)
                if 0.5 * float(F_try @ F_try) < f0 * (1 - 1e-4 * lam) or \
                   np.linalg.norm(F_try, np.inf) < nrm * 0.999:
                    ok = True
                    break
                lam *= 0.5
            if not ok:
                break
            z, F = z_try, F_try
        nrm = np.linalg.norm(F, np.inf)
        if nrm > 1e-7:
            raise RuntimeError(f"MCP solve failed in {yp.t}: |F|={nrm:.2e}")

        n = self.n
        px = np.zeros(n)
        px[iP] = np.exp(z[:nP])
        QM = np.zeros(n)
        if qm_fix_vals is not None:
            QM += qm_fix_vals
        QM[iM] = np.maximum(z[nP:nP + nM], 0.0)
        QE = np.zeros(n)
        QE[iE] = np.maximum(z[nP + nM:], 0.0)
        v = self.forward(px, yp)
        v["QM"], v["QE"] = QM, QE
        v["resid"] = nrm
        return v

    def _jacobian(self, z, F, yp, qm_fix_vals):
        m = len(z)
        J = np.empty((m, m))
        for j in range(m):
            h = 1e-7 * max(1.0, abs(z[j]))
            zj = z.copy()
            zj[j] += h
            J[:, j] = (self.residual(zj, yp, qm_fix_vals) - F) / h
        return J
