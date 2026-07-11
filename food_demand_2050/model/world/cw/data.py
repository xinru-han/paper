"""CASM-World data layer.

Builds the PEATSim-structure RAWDATA (31 commodities x 13 regions x
{2022, 2023} x vars) for the CASM-World model:

* **Regions** (PEATSim): usa e15 jpn can mex brz arg chn aus nzl kor ind + row
* **China** comes from the CASM balance sheets (0DATA.XLSX, 2022/2023
  columns) — the authoritative source per the user's rule.  Commodities
  CASM does not track (sunflower complex, dairy products detail, biofuels,
  oto) fall back to the world workbook.
* **Other named regions** come from the SILK/PEATSim-family world workbook
  `0model_update20250315.xlsx` (USDA-PSD-based, 2022+2023 — the same vintage
  as the latest FAO data; Japan is included there although FAO SUA lacks it).
* **ROW** = the world workbook's remaining named regions (rus ukr tha egy
  idn irn mys vnm tur phl) + its own ROW, **plus the China discrepancy**:
  whatever CASM adds to (or removes from) China relative to the world
  workbook is subtracted from (added to) ROW so world totals stay exactly
  as published.
* **Parameters** (elasticities/policy/prices) come from PEATSim params.xls;
  macro projections (GDP/POP/exchange rates to 2035) from the SILK
  Macrodata workbook (PEATSim's own macro file stops in 2017).

Units: million tonnes / million ha (CASM's 万 t / 万 ha are divided by 100).
"""

from __future__ import annotations

import os
import numpy as np

from cw.gdxxrw import load_symbols

WORLD_XLSX = ("/root/data/CASM/SILK Model/baseline/2027/"
              "0model_update20250315.xlsx")
PEATSIM_DIR = "/root/data/CASM/PEATSim_Dist507"
SILK_DIR = "/root/data/CASM/SILK Model/baseline/2027"
CASM_DIR = "/root/data/CASM/CASM20260514"

REGIONS = ["usa", "e15", "jpn", "can", "mex", "brz", "arg", "chn", "aus",
           "nzl", "kor", "ind", "row"]
# world-workbook regions folded into ROW
ROW_MEMBERS = ["rus", "ukr", "tha", "egy", "idn", "irn", "mys", "vnm",
               "tur", "phl", "row"]

VARS = ["begstk", "endstk", "area", "prd", "con", "fee", "foo", "fue",
        "cru", "exp", "imp", "oth"]

# CASM commodity -> (PEATSim commodity, conversion factor)
# CASM units 万t -> /100 to Mt; rice paddy -> milled x0.7 (matches PSD)
CASM_MAP = {
    "RICE": ("RIC", 0.70), "WHEA": ("WHE", 1.0), "MAIZ": ("CRN", 1.0),
    "BARL": ("OCG", 1.0), "SORG": ("OCG", 1.0), "OTGR": ("OCG", 1.0),
    "SOYS": ("SBS", 1.0), "SOYO": ("SBO", 1.0), "SOYM": ("SBM", 1.0),
    "RAPS": ("RBS", 1.0), "RAPO": ("RBO", 1.0), "RAPM": ("RBM", 1.0),
    "COTT": ("CTN", 1.0), "SUGA": ("SUG", 1.0),
    # SUGC/SUGB not mapped: CASM records them in refined-sugar equivalent
    # (~8 Mt) while PEATSim's sca/sbe are raw cane/beet (~105 Mt) — China's
    # sugar crops keep the world-workbook values.
    "CATM": ("BFV", 1.0), "PIGM": ("PRK", 1.0),
    "CHKM": ("PLM", 1.0),
    # MILK not mapped: CASM's raw-milk production equals the world workbook
    # (same source, 41.97 Mt) but CASM books consumption as food while
    # PEATSim clears raw milk through dairy processing (PROCEQ), and CASM's
    # milk imports are dairy products in raw-milk equivalent (mlk is
    # non-traded in PEATSim).
}

NO_TRADE_OVERRIDE = set()

# CASM variable -> PEATSim var (both sides of the balance sheet)
# supply/production QX; demand components QDF food, QDL feed, QDP processing,
# QDC crush, QDS seed(->oth), QDW waste(->oth), QDO other(->oth), STV stocks
CASM_QMAP = [
    ("QX0", "prd"), ("QM0", "imp"), ("QE0", "exp"), ("QDF0", "foo"),
    ("QDL0", "fee"), ("QDC0", "cru"), ("AC0", "area"),
]
CASM_OTH = ["QDS0", "QDW0", "QDO0", "QDP0"]     # folded into oth


def _up(s):
    return s.strip().upper()


class Data:
    def __init__(self, base="2023", prev="2022"):
        self.base = base
        self.prev = prev
        self._load()
        self._sets()
        self._assemble()
        self._china_override()
        self._base_process()

    # ------------------------------------------------------------------
    def _load(self):
        self.m0 = load_symbols(WORLD_XLSX, "Index!A1")
        self.ep = load_symbols(os.path.join(PEATSIM_DIR, "params.xls"),
                               "Index!A1")
        # PEATSim's basprice is a pre-2010 extrapolation (2023 rice 321 vs
        # actual 500 USD/t).  Base-year world prices must be the latest
        # actuals, so overlay the updated price table; behavioral parameters
        # (elasticities) stay PEATSim's.
        silk_ep = load_symbols(os.path.join(
            SILK_DIR, "elasticityPolicyPrice_update20250315.xls"), "Index!A1")
        self.ep["BASPRICE"] = silk_ep["BASPRICE"]
        self.bio = load_symbols(os.path.join(
            SILK_DIR, "bioElasticities_update20250315.xlsx"), "Index!A1")
        self.macro = load_symbols(os.path.join(
            SILK_DIR, "Macrodata_update20250315.xlsx"), "Index!A1")
        self.tar = load_symbols(os.path.join(SILK_DIR, "TariffCuts.xlsx"),
                                "INDEX!A1")
        self.trans = load_symbols(os.path.join(SILK_DIR, "transfact.xls"),
                                  "INDEX!A1")
        # CASM balance sheets (via the casm package)
        import sys
        sys.path.insert(0, "/root/data/CASM/casm_python")
        import warnings
        warnings.filterwarnings("ignore")
        from casm.data import Data as CasmData
        self.casm = CasmData(CASM_DIR)

    # ------------------------------------------------------------------
    def _sets(self):
        order = ["ric", "whe", "crn", "ocg", "sbs", "sbo", "sbm", "nbs",
                 "nbo", "nbm", "rbs", "rbo", "rbm", "ddg", "eth", "bdi",
                 "oto", "ctn", "sug", "sca", "sbe", "bfv", "prk", "plm",
                 "mlk", "but", "che", "ndm", "fmk", "wdm", "oda"]
        present = {_up(c) for c in self.m0["I"]}
        self.I = [_up(c) for c in order if _up(c) in present]
        self.R = [_up(r) for r in REGIONS]
        self.nI, self.nR = len(self.I), len(self.R)
        self.ii = {c: k for k, c in enumerate(self.I)}
        self.ri = {r: k for k, r in enumerate(self.R)}

        S = lambda *x: set(_up(v) for v in x)
        self.crop = S("ric", "whe", "crn", "ocg", "sbs", "nbs", "rbs", "oto",
                      "ctn", "sca", "sbe")
        self.oilseed = S("sbs", "nbs", "rbs")
        self.oil = S("sbo", "nbo", "rbo")
        self.meal = S("sbm", "nbm", "rbm")
        self.meat = S("bfv", "prk", "plm", "mlk")
        self.dairy = S("but", "che", "ndm", "fmk", "wdm", "oda")
        self.milk = S("mlk")
        self.sugar = S("sug")
        self.scsb = S("sca", "sbe")
        self.fuel = S("eth", "bdi")
        self.feedstock = S("crn", "whe", "ocg", "sca", "sbe", "oto", "rbo",
                           "sbo", "ric", "nbo")
        self.feed = S("ric", "whe", "crn", "ocg", "oto", "ddg") | self.meal \
            | self.oil | self.oilseed
        self.progcrop = S("ric", "whe", "crn", "ocg", "sbs", "nbs", "rbs",
                          "ctn", "sug")
        self.intrd = S("fmk", "oda", "sca", "sbe")
        self.itrd = set(self.I) - self.intrd - self.milk
        self.seed2om = {"SBS": ("SBO", "SBM"), "NBS": ("NBO", "NBM"),
                        "RBS": ("RBO", "RBM")}
        self.food = (set(self.I) - self.milk -
                     S("sca", "sbe", "ddg", "eth", "bdi")) | self.meal

    # ------------------------------------------------------------------
    def _assemble(self):
        """RAWDATA from the world workbook, aggregating ROW members."""
        self.raw = {}
        years = [self.prev, self.base]
        for var in VARS:
            for y in years:
                self.raw[(var, y)] = np.zeros((self.nI, self.nR))
        # named regions directly; ROW members accumulated into 'ROW'
        srcmap = {}
        for r in REGIONS[:-1]:
            srcmap[_up(r)] = _up(r)
        for r in ROW_MEMBERS:
            srcmap[_up(r)] = "ROW"
        for src, dst in srcmap.items():
            tbl = self.m0.get(src)
            if tbl is None:
                continue
            rr = self.ri[dst]
            for (com, yr, v), val in tbl.items():
                vv = v.strip().lower()
                if vv in VARS and yr in years and _up(com) in self.ii:
                    self.raw[(vv, yr)][self.ii[_up(com)], rr] += val / 1000.0
        for y in years:
            area = self.raw[("area", y)]
            prd = self.raw[("prd", y)]
            with np.errstate(divide="ignore", invalid="ignore"):
                self.raw[("yield", y)] = np.where(area > 0, prd / area, 0.0)

    # ------------------------------------------------------------------
    def _china_override(self):
        """Replace China with CASM data; absorb the difference into ROW.

        Only for commodities CASM tracks; others (sunflower, dairy detail,
        biofuels, oto) keep the world-workbook values for China.
        """
        cd = self.casm
        chn = self.ri["CHN"]
        row = self.ri["ROW"]
        self.china_diff = {}                      # (com, year, var) -> diff
        for y in [self.prev, self.base]:
            # gather CASM values per PEATSim commodity
            agg = {}                              # (pcom, var) -> value (Mt)
            for ccom, (pcom, fac) in CASM_MAP.items():
                if ccom not in cd.C:
                    continue
                for sym, var in CASM_QMAP:
                    tbl = getattr(cd, sym)
                    if ccom in tbl.index and y in tbl.columns:
                        agg[(pcom, var)] = agg.get((pcom, var), 0.0) + \
                            float(tbl.loc[ccom, y]) * fac / 100.0
                oth = 0.0
                for sym in CASM_OTH:
                    tbl = getattr(cd, sym)
                    if ccom in tbl.index and y in tbl.columns:
                        oth += float(tbl.loc[ccom, y]) * fac / 100.0
                agg[(pcom, "oth")] = agg.get((pcom, "oth"), 0.0) + oth
                # stocks: STV0 is stock variation; map into endstk-begstk
                if "STV0" in dir(cd):
                    tbl = cd.STV0
                    if ccom in tbl.index and y in tbl.columns:
                        agg[(pcom, "stv")] = agg.get((pcom, "stv"), 0.0) + \
                            float(tbl.loc[ccom, y]) * fac / 100.0
            # ---- apply the China override ----
            edited = np.zeros(self.nI, dtype=bool)
            for (pcom, var), val in agg.items():
                if pcom not in self.ii or var == "stv":
                    continue
                i = self.ii[pcom]
                edited[i] = True
                old = self.raw[(var, y)][i, chn]
                self.raw[(var, y)][i, chn] = val
                self.china_diff[(pcom, y, var)] = val - old
                # production difference goes to ROW so the world total is
                # preserved (the user's rule); trade differences are handled
                # globally by the world-rebalance step in _base_process
                if var in ("prd", "area"):
                    self.raw[(var, y)][i, row] = max(
                        self.raw[(var, y)][i, row] - (val - old), 0.0)
            # China consumption identity: con = tracked uses (CASM accounts)
            # Account closure (ending stocks / ROW residual) only for the
            # base year: the lag year's ending stock must stay equal to the
            # base year's opening stock (workbook consistency), and the lag
            # year never enters the model equations.
            if y != self.base:
                # still recompute China's consumption total for the lag
                for i in np.where(edited)[0]:
                    self.raw[("con", y)][i, chn] = (
                        self.raw[("foo", y)][i, chn] +
                        self.raw[("fee", y)][i, chn] +
                        self.raw[("cru", y)][i, chn] +
                        self.raw[("fue", y)][i, chn] +
                        self.raw[("oth", y)][i, chn])
                area = self.raw[("area", y)]
                prd = self.raw[("prd", y)]
                with np.errstate(divide="ignore", invalid="ignore"):
                    self.raw[("yield", y)] = np.where(area > 0, prd / area, 0.0)
                continue
            for i in np.where(edited)[0]:
                self.raw[("con", y)][i, chn] = (
                    self.raw[("foo", y)][i, chn] +
                    self.raw[("fee", y)][i, chn] +
                    self.raw[("cru", y)][i, chn] +
                    self.raw[("fue", y)][i, chn] +
                    self.raw[("oth", y)][i, chn])
                # China ending stock closes the account (= CASM stock change)
                resid = (self.raw[("prd", y)][i, chn]
                         + self.raw[("imp", y)][i, chn]
                         - self.raw[("exp", y)][i, chn]
                         - self.raw[("con", y)][i, chn])
                end = self.raw[("begstk", y)][i, chn] + resid
                if end < 0:      # stock cannot go negative: park in oth
                    self.raw[("oth", y)][i, chn] += end
                    self.raw[("con", y)][i, chn] += end
                    end = 0.0
                self.raw[("endstk", y)][i, chn] = end
                # ROW's 'other use' is the residual that closes ROW's account
                # (absorbs the China revision, may adjust downward)
                oth_row = (self.raw[("begstk", y)][i, row]
                           + self.raw[("prd", y)][i, row]
                           + self.raw[("imp", y)][i, row]
                           - self.raw[("exp", y)][i, row]
                           - self.raw[("endstk", y)][i, row]
                           - self.raw[("foo", y)][i, row]
                           - self.raw[("fee", y)][i, row]
                           - self.raw[("cru", y)][i, row]
                           - self.raw[("fue", y)][i, row])
                self.raw[("oth", y)][i, row] = oth_row
                self.raw[("con", y)][i, row] = (
                    self.raw[("foo", y)][i, row] +
                    self.raw[("fee", y)][i, row] +
                    self.raw[("cru", y)][i, row] +
                    self.raw[("fue", y)][i, row] + oth_row)
            self._edited = edited
            # yield refresh
            area = self.raw[("area", y)]
            prd = self.raw[("prd", y)]
            with np.errstate(divide="ignore", invalid="ignore"):
                self.raw[("yield", y)] = np.where(area > 0, prd / area, 0.0)

    # ------------------------------------------------------------------
    def _base_process(self):
        """Base-year processing: meal reclass, OTH residual, ROW rebalance."""
        b = self.base
        g = lambda v: self.raw[(v, b)].copy()
        BEG, END = g("begstk"), g("endstk")
        AREA, PRD, CON = g("area"), g("prd"), g("con")
        FEE, FOO, FUE, CRU = g("fee"), g("foo"), g("fue"), g("cru")
        EXP, IMP, OTH = g("exp"), g("imp"), g("oth")

        for m in self.meal:
            i = self.ii[m]
            FEE[i] += FOO[i] + FUE[i]
            FOO[i] = 0.0
            FUE[i] = 0.0

        # OTH residual where not set: CON - FUE - FOO - FEE - CRU
        # (milk keeps CON as-is: raw milk clears through dairy processing)
        oth_calc = CON - FUE - FOO - FEE - CRU
        OTH = np.where(np.abs(OTH) > 1e-9, OTH, oth_calc)
        for mk in self.milk:
            OTH[self.ii[mk]] = 0.0
        OTH[np.abs(OTH) < 1e-9] = 0.0

        # ROW rebalancing to enforce world trade balance
        ir = self.ri["ROW"]
        werr = EXP.sum(axis=1) - IMP.sum(axis=1)
        for i in range(self.nI):
            IMP[i, ir] += werr[i]
            comps = np.array([FOO[i, ir], FEE[i, ir], OTH[i, ir],
                              CRU[i, ir], FUE[i, ir]])
            tot = comps.sum()
            if tot > 1e-9:
                sh = comps / tot
                FOO[i, ir] += werr[i] * sh[0]
                FEE[i, ir] += werr[i] * sh[1]
                OTH[i, ir] += werr[i] * sh[2]
                CRU[i, ir] += werr[i] * sh[3]
                FUE[i, ir] += werr[i] * sh[4]
            else:
                OTH[i, ir] += werr[i]
            CON[i, ir] += werr[i]
            if IMP[i, ir] <= 0:
                EXP[i, ir] -= IMP[i, ir]
                IMP[i, ir] = 0.0

        self.NET0 = EXP - IMP
        self.q0 = dict(BEG=BEG, END=END, AREA=AREA, PRD=PRD, CON=CON,
                       FEE=FEE, FOO=FOO, FUE=FUE, CRU=CRU, EXP=EXP,
                       IMP=IMP, OTH=OTH, YLD=g("yield"))
        self.world_imbalance = np.abs(EXP.sum(axis=1) - IMP.sum(axis=1))
        # write back processed base
        for k, v in [("begstk", BEG), ("endstk", END), ("area", AREA),
                     ("prd", PRD), ("con", CON), ("fee", FEE), ("foo", FOO),
                     ("fue", FUE), ("cru", CRU), ("exp", EXP), ("imp", IMP),
                     ("oth", OTH)]:
            self.raw[(k, b)] = v

    # ------------------------------------------------------------------
    def summary(self):
        print(f"CASM-World data: {self.nI} commodities x {self.nR} regions, "
              f"base {self.base}")
        print("max world trade imbalance:",
              float(self.world_imbalance.max()))
        chn = self.ri["CHN"]
        print("\nChina base (CASM-sourced, Mt):")
        for c in ["RIC", "WHE", "CRN", "SBS", "BFV", "PRK", "MLK"]:
            i = self.ii[c]
            print(f"  {c}: PRD={self.q0['PRD'][i,chn]:.2f} "
                  f"IMP={self.q0['IMP'][i,chn]:.2f} "
                  f"EXP={self.q0['EXP'][i,chn]:.2f} "
                  f"FOO={self.q0['FOO'][i,chn]:.2f} "
                  f"FEE={self.q0['FEE'][i,chn]:.2f}")
        print("\nlargest China-vs-world-workbook adjustments (Mt, base yr):")
        diffs = sorted(((abs(v), k, v) for k, v in self.china_diff.items()
                        if k[1] == self.base), reverse=True)[:8]
        for _, k, v in diffs:
            print(f"  {k[0]} {k[2]}: {v:+.2f}")


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    Data().summary()
