"""SILK-MGA recursive-dynamic projection (port of future/futuresec.gms).

Solves the world-price MCP year by year for 2024–2035.  Each year:
  * exogenous drivers (population, real GDP, exchange rate, tariffs) are set
    to that year's values via ``Model.set_year``;
  * the lagged levels (area, yield, production, crush, milk consumption,
    ending stock and its local price) are carried forward from the prior
    solved year;
  * the world market clears (``Model.solve_world``) and results are stored.

The multiplicative intercepts are calibrated once at the base year and hold
fixed; because they embed the 2022->2023 ratio in the lag terms, the baseline
carries that one-year growth forward as a trend (GAMS behavior).
"""

from __future__ import annotations

import numpy as np

from cw.data import Data
from cw.calib import Calibration
from cw.model import Model


PROJECTION_YEARS = [str(y) for y in range(2024, 2036)]


def run_baseline(years=PROJECTION_YEARS, progress=None):
    d = Data()
    c = Calibration(d)
    m = Model(d, c)

    # base-year solution (2023) provides the first lag
    v0 = m.forward(c.PRF0)
    res = {d.base: v0}
    lag = _lag_from(v0, m)
    PRF = c.PRF0.copy()

    for y in years:
        m.set_year(y)
        v = m.solve_world(PRF0=PRF, lag=lag)
        res[y] = v
        if progress:
            progress(f"{y}: solved, world |excess|={v['resid']:.2e}, "
                     f"iters={v['iters']}")
        lag = _lag_from(v, m)
        PRF = v["PRF"].copy()
    return d, c, m, res


def _lag_from(v, m):
    """Assemble the lag dict for the next year from a solved year ``v``."""
    return dict(
        AHV=v["AHV"], YLD=v["YLD"], PRD=v["PRD"], CRU=v["CRU"],
        CON=v["CON"],
        EST=v["EST"],
        PRFClag=v["PRFC"],
    )


if __name__ == "__main__":
    import os
    import warnings
    warnings.filterwarnings("ignore")
    d, c, m, res = run_baseline(progress=print)
    print("\nSILK baseline solved for", len(res) - 1, "projection years.")
    # China trajectory sample
    inv = {v: k for k, v in d.ii.items()}
    ri = d.ri["CHN"]
    print("\nChina baseline (million t): PRD / net-import by year")
    for cc in ["RIC", "WHE", "CRN", "SBS", "BFV", "PRK"]:
        i = d.ii[cc]
        row = []
        for y in ["2023", "2025", "2030", "2035"]:
            vv = res[y]
            net = vv["IMP"][i, ri] - vv["EXP"][i, ri]
            row.append(f"{y}:{vv['PRD'][i,ri]:.1f}/{net:+.1f}")
        print(f"  {cc:4s} " + "  ".join(row))
