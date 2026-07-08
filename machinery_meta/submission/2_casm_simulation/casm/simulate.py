"""Translation of BASE.GMS: exogenous growth rates from 2SIMULATION.XLSM
and the recursive-dynamic baseline loop 2026-2035."""

from __future__ import annotations

import os
import numpy as np

from .gdxxrw import load_symbols
from .data import Data, T, TBASE, TC, TAH
from .calib import Calibration
from .model import Model, YearParams

_GR_SYMBOLS = ("INCPCGR0 POPHGR0 AYGR0 AAGR0 MMGR0 GDPGR0 PWMGR0 PWEGR0 "
               "IOSTVGR0 EXCHGR0 APGR0 ASMGR0 AFEGR0 IOMEALGR0 IOXWGR0 "
               "AFHGR0 ASUGGR0").split()


class Growth:
    """Growth rates of scenario `sim` as convenient lookup callables.

    `overrides` adjusts the baseline growth rates for a simulation run,
    exactly the way SIM1.GMS etc. modify the BASE assumptions:
        {"AYGR0": {("RICE", "2026"): 1.5, ...}, "GDPGR0": {("2030",): 4.0}}
    Keys are the symbol's own dimensions without the SIM label; values are
    growth rates in percent (same units as 2SIMULATION.XLSM)."""

    def __init__(self, casm_dir, sim="BASE", overrides=None):
        raw = load_symbols(os.path.join(casm_dir, "2simulation.xlsm"),
                           "INDEX!A3", wanted=set(_GR_SYMBOLS))
        self.raw = raw
        self.sim = sim
        for sym, kv in (overrides or {}).items():
            tab = raw[sym]
            for key, val in kv.items():
                key = tuple(str(k).upper() for k in key)
                tab[key[:-1] + (sim, key[-1])] = float(val)

    def g(self, sym, *pre):
        """growth-rate lookup: g('AYGR0', c)(t) -> rate (already /100)."""
        d = self.raw[sym]
        sim = self.sim

        def f(t):
            return d.get(tuple(pre) + (sim, t), 0.0) / 100.0
        return f


def run_base(casm_dir, progress=None, growth_overrides=None):
    d = Data(casm_dir)
    cal = Calibration(d)
    m = Model(d, cal)
    gr = Growth(casm_dir, overrides=growth_overrides)
    C, H, n = d.C, d.H, m.n

    res = {}   # results container: res[name][t] = vector / dict

    # ---- base-year (2025) solve of 2MODEL.GMS -------------------------
    tb = TBASE
    yp = YearParams(m, tb)
    px0 = d.PX0[tb].values.copy()
    px0[~m.PXFREE] = 1.0
    v = m.solve_year(yp, px0, d.QM0[tb].values, d.QE0[tb].values)
    if progress:
        progress(f"{tb}: solved, |F|={v['resid']:.2e}")
    prev_v, prev_yp = v, yp

    # growth lookups (vectorised per year below)
    def vec(sym, index):
        """(index elem, t) -> rate vector for year t"""
        raw = gr.raw[sym]

        def f(t):
            return np.array([raw.get((c, gr.sim, t), 0.0) for c in index]) / 100.0
        return f

    g_ay, g_aa = vec("AYGR0", C), vec("AAGR0", C)
    g_asm, g_asug = vec("ASMGR0", C), vec("ASUGGR0", C)
    g_ap = vec("APGR0", C)
    g_ioxw, g_iostv = vec("IOXWGR0", C), vec("IOSTVGR0", C)
    g_pwm, g_pwe = vec("PWMGR0", C), vec("PWEGR0", C)
    g_pop, g_inc = vec("POPHGR0", H), vec("INCPCGR0", H)

    def g_gdp(t):
        return gr.raw["GDPGR0"].get((gr.sim, t), 0.0) / 100.0

    def g_exch(t):
        return gr.raw["EXCHGR0"].get(("USD", gr.sim, t), 0.0) / 100.0

    def g_afh(t):
        return {h: np.array([gr.raw["AFHGR0"].get((c, h, gr.sim, t), 0.0)
                             for c in C]) / 100.0 for h in H}

    def g_afe(t):
        out = np.zeros((len(d.CFEED), len(d.CLVS)))
        for i, cf in enumerate(d.CFEED):
            for j, cl in enumerate(d.CLVS):
                out[i, j] = gr.raw["AFEGR0"].get((cf, cl, gr.sim, t), 0.0) / 100.0
        return out

    def g_iomeal(cm, cs, t):
        return gr.raw["IOMEALGR0"].get((cm, cs, gr.sim, t), 0.0) / 100.0

    def store(t, v, yp):
        res.setdefault("QX", {})[t] = v["QX"]
        res.setdefault("AC", {})[t] = v["AC"]
        res.setdefault("YC", {})[t] = v["YC"]
        res.setdefault("QM", {})[t] = v["QM"]
        res.setdefault("QE", {})[t] = v["QE"]
        res.setdefault("QDF", {})[t] = v["QDF"]
        res.setdefault("QDFH", {})[t] = v["QDFH"]
        res.setdefault("QDFHPC", {})[t] = v["QDFHPC"]
        res.setdefault("QDL", {})[t] = v["QDL"]
        res.setdefault("QDS", {})[t] = v["QDS"]
        res.setdefault("QDP", {})[t] = v["QDP"]
        res.setdefault("QDC", {})[t] = v["QDC"]
        res.setdefault("QDO", {})[t] = v["QDO"]
        res.setdefault("QDW", {})[t] = v["QDW"]
        res.setdefault("STV", {})[t] = v["STV"]
        res.setdefault("QDT", {})[t] = v["QDT"]
        res.setdefault("PX", {})[t] = v["PX"]
        res.setdefault("PD", {})[t] = v["PD"]
        # per-capita food demand (QDFPCEQ): QDF / SUM(H,POPH) * 1000 * 2
        popall = sum(yp.POPH[h] for h in H)
        res.setdefault("QDFPC", {})[t] = v["QDF"] / popall * 1000 * 2
        res.setdefault("POPH", {})[t] = dict(yp.POPH)
        res.setdefault("INCPC", {})[t] = dict(yp.INCPC)
        res.setdefault("GDPT", {})[t] = yp.GDPT

    # ---- projection loop (BASE.GMS 3.6) --------------------------------
    for t in TC:
        yp = YearParams.__new__(YearParams)
        p = prev_yp
        yp.t = t
        yp.POPH = {h: p.POPH[h] * (1 + g_pop(t)[i]) for i, h in enumerate(H)}
        yp.INCPC = {h: p.INCPC[h] * (1 + g_inc(t)[i]) for i, h in enumerate(H)}
        yp.GDPT = p.GDPT * (1 + g_gdp(t))
        yp.EXCH = p.EXCH * (1 + g_exch(t))
        yp.AY = p.AY * (1 + g_ay(t))
        yp.AA = p.AA * (1 + g_aa(t))
        yp.ASM = p.ASM * (1 + g_asm(t))
        yp.ASUG = p.ASUG * (1 + g_asug(t))
        afh_g = g_afh(t)
        yp.AFH = {h: p.AFH[h] * (1 + afh_g[h]) for h in H}
        yp.AFE = p.AFE * (1 + g_afe(t))
        yp.AP = p.AP * (1 + g_ap(t))
        yp.IOMEAL = {(cm, cs): io * (1 + g_iomeal(cm, cs, t))
                     for (cm, cs), io in p.IOMEAL.items()}
        yp.IOOILSD = dict(p.IOOILSD)
        yp.IOXS = p.IOXS.copy()
        yp.IOXO = p.IOXO.copy()
        yp.IOXW = p.IOXW * (1 + g_ioxw(t))
        yp.IOSTV = p.IOSTV * (1 + g_iostv(t))
        yp.PWE = p.PWE * (1 + g_pwe(t))
        yp.PWM = p.PWM * (1 + g_pwm(t))
        # QM.FX('SUGC'/'SUGB') = QM.L(.,'2023') = 0
        yp.qm_fixed_zero = np.zeros(n, dtype=bool)
        yp.qm_fixed_zero[m.cidx["SUGC"]] = True
        yp.qm_fixed_zero[m.cidx["SUGB"]] = True

        px_start = prev_v["PX"].copy()
        px_start[~m.PXFREE] = 1.0
        v = m.solve_year(yp, px_start, prev_v["QM"], prev_v["QE"])
        if progress:
            progress(f"{t}: solved, |F|={v['resid']:.2e}")
        store(t, v, yp)
        prev_v, prev_yp = v, yp

    return d, cal, m, res
