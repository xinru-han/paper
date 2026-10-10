#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


ROOT = Path("/root/data/Paper/食物消费数据/paper0-EASI/easi_total_anomaly_rebuild")
OUT = ROOT / "outputs"
replicates = pd.read_stata(
    OUT / "easi_reference_bootstrap_replicates.dta",
    convert_categoricals=False,
)
complete = replicates.dropna()
reference = pd.read_csv(OUT / "easi_reference_analytic.csv")
analysis = pd.read_stata(
    ROOT / "data" / "total_anomaly_analysis.dta",
    columns=["village_cluster", "sample_model"],
    convert_categoricals=False,
)

rows = []
for prefix, elasticity_type in (
    ("exp", "expenditure"),
    ("mar", "marshallian"),
    ("hic", "hicksian"),
):
    for good in range(1, 7):
        column = f"{prefix}{good}"
        if elasticity_type == "expenditure":
            point = reference[
                (reference["elasticity_type"] == "expenditure")
                & (reference["demand_good"] == good)
            ]["elasticity"].iloc[0]
            shock = 0
        else:
            point = reference[
                (reference["elasticity_type"] == elasticity_type)
                & (reference["demand_good"] == good)
                & (reference["shock_good"] == good)
            ]["elasticity"].iloc[0]
            shock = good
        se = complete[column].std(ddof=1)
        z = point / se
        p_value = math.erfc(abs(z) / math.sqrt(2))
        rows.append(
            {
                "elasticity_type": elasticity_type,
                "demand_good": good,
                "shock_good": shock,
                "elasticity": point,
                "se": se,
                "z": z,
                "p_value": p_value,
                "ci_low": point - 1.96 * se,
                "ci_high": point + 1.96 * se,
                "reps_requested": len(replicates),
                "reps_successful": len(complete),
                "reps_failed": len(replicates) - len(complete),
                "clusters": analysis.loc[
                    analysis["sample_model"] == 1, "village_cluster"
                ].nunique(),
                "ci_method": "two-step village-cluster bootstrap normal",
            }
        )

pd.DataFrame(rows).to_csv(OUT / "easi_reference_bootstrap.csv", index=False)
