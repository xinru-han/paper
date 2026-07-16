#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path("/root/data/Paper/食物消费数据/paper0-EASI/easi_total_anomaly_rebuild")
OUT = ROOT / "outputs"
FOODS = {
    1: "Staples",
    2: "Beans",
    3: "Meat",
    4: "Edible oil",
    5: "Vegetables",
    6: "Fruit",
}


def fmt(value, digits=4):
    if pd.isna(value):
        return "NA"
    return f"{float(value):.{digits}f}"


def section(lines, title):
    lines.extend(["", "=" * 78, title, "=" * 78])


def main():
    lines = [
        "TOTAL-CONSUMPTION FOOD DEMAND: ANOMALY REBUILD",
        "Generated from the unrestricted AIDS/QUAIDS/EASI pipeline.",
        "No Cholesky curvature constraint or elasticity sign projection is used.",
    ]

    section(lines, "1. SAMPLE FLOW")
    flow = pd.read_csv(OUT / "sample_flow.csv")
    for r in flow.itertuples():
        lines.append(f"{int(r.sequence):>2}. {r.stage}: {int(r.observations):,}")

    section(lines, "2. PHYSICAL QUANTITY AUDIT")
    physical = pd.read_csv(OUT / "physical_quantity_audit.csv")
    for r in physical.itertuples():
        lines.append(
            f"{FOODS[r.group]:<12} cap={fmt(r.cap_jin_pc_month,1)} "
            f"jin/person/month; flagged={int(r.flagged):,}; "
            f"observed max={fmt(r.max_observed,2)}"
        )

    section(lines, "3. FIVE-MAD TOTAL AND SELF-PRODUCTION TAILS")
    qa = pd.read_csv(OUT / "quantity_source_anomaly_audit.csv")
    qa = qa[(qa["threshold"] == 5) & qa["source"].isin(["total", "self"])]
    for r in qa.itertuples():
        lines.append(
            f"{FOODS[r.group]:<12} {r.source:<5} flagged={int(r.flagged):>3}; "
            f"min/median/max flagged={fmt(r.min_flagged,2)}/"
            f"{fmt(r.median_flagged,2)}/{fmt(r.max_flagged,2)}"
        )

    section(lines, "4. COMMUNITY PRICE DIAGNOSTICS")
    pv = pd.read_csv(OUT / "price_variation.csv")
    for r in pv.itertuples():
        lines.append(
            f"{FOODS[r.group]:<12} mean={fmt(r.mean)} median={fmt(r.p50)} "
            f"p99={fmt(r.p99)} max={fmt(r.max)} "
            f"own-village representative share={fmt(r.direct_share,3)}"
        )
    uv = pd.read_csv(OUT / "unit_value_price_validation.csv")
    lines.append("")
    lines.append("Household unit values are validation only:")
    for r in uv.itertuples():
        lines.append(
            f"{FOODS[r.group]:<12} median UV/community ratio="
            f"{fmt(r.median_uv_price_ratio,3)}; log correlation="
            f"{fmt(r.log_correlation,3)}"
        )

    section(lines, "5. MODEL SELECTION ON THE COMMON PREFERRED SAMPLE")
    ms = pd.read_csv(OUT / "model_selection.csv")
    for r in ms.itertuples():
        lines.append(
            f"{r.model.upper():<7} order={int(r.order)} converged={int(r.converged)} "
            f"N={fmt(r.N,0)} BIC={fmt(r.bic,2)} "
            f"Engel-order p={fmt(r.Engel_order_p,4)} "
            f"selected={int(r.bic_preferred)}"
        )

    section(lines, "6. TWO-STEP GMM SPECIFICATION TESTS")
    for model in ("aids", "quaids", "easi"):
        tests = pd.read_csv(OUT / f"{model}_tests.csv")
        hansen = tests[tests.test == "Hansen_overidentification"].iloc[0]
        first = tests[tests.test == "excluded_instruments_first_stage"].iloc[0]
        lines.append(
            f"{model.upper():<7} Hansen p={fmt(hansen.p_value)}; "
            f"excluded-instrument p={fmt(first.p_value)}"
        )

    section(lines, "7. EASI REFERENCE ELASTICITIES: VILLAGE-CLUSTER BOOTSTRAP")
    boot = pd.read_csv(OUT / "easi_reference_bootstrap.csv")
    for etype in ("expenditure", "marshallian", "hicksian"):
        lines.append("")
        lines.append(etype.upper())
        subset = boot[boot.elasticity_type == etype]
        for r in subset.itertuples():
            lines.append(
                f"{FOODS[r.demand_good]:<12} estimate={fmt(r.elasticity)} "
                f"SE={fmt(r.se)} p={fmt(r.p_value)} "
                f"95% CI=[{fmt(r.ci_low)}, {fmt(r.ci_high)}]"
            )

    section(lines, "8. UNRESTRICTED EASI HICKSIAN OWN-PRICE SAMPLE SENSITIVITY")
    status = pd.read_csv(OUT / "easi_sample_sensitivity_status.csv").set_index("sample")
    files = {"main": OUT / "easi_reference_analytic.csv"}
    for sample in status.index:
        if sample != "main":
            files[sample] = OUT / f"easi_{sample}_reference_analytic.csv"
    for sample, path in files.items():
        if not path.exists():
            continue
        ref = pd.read_csv(path)
        own = ref[
            (ref.elasticity_type == "hicksian")
            & (ref.demand_good == ref.shock_good)
        ]
        vals = ", ".join(
            f"{FOODS[int(r.demand_good)]}={fmt(r.elasticity)}"
            for r in own.itertuples()
        )
        hp = status.loc[sample, "hansen_p"] if sample in status.index else float("nan")
        lines.append(f"{sample:<14} Hansen p={fmt(hp)} | {vals}")

    section(lines, "9. HOUSEHOLD ELASTICITY DISTRIBUTION ON COMMON 0.5% SHARE SUPPORT")
    for model in ("aids", "quaids", "easi"):
        d = pd.read_csv(OUT / f"{model}_elasticities_support005.csv")
        own = d[
            (d.elasticity_type == "hicksian") & (d.demand_good == d.shock_good)
        ]
        lines.append("")
        lines.append(model.upper())
        for r in own.itertuples():
            lines.append(
                f"{FOODS[r.demand_good]:<12} median={fmt(r.p50)} "
                f"p10={fmt(r.p10)} p90={fmt(r.p90)} "
                f"negative share={fmt(r.negative_rate,3)} "
                f"N support={int(r.n_valid):,}"
            )

    section(lines, "10. INTERPRETATION")
    lines.extend(
        [
            "The main elasticity sign is determined by cleaned quantities and comparable",
            "representative-product community prices. The bootstrap provides inference",
            "without a delta-method sign repair. Household distribution summaries exclude",
            "near-zero fitted-share denominators but impose no curvature restriction.",
        ]
    )

    text = "\n".join(lines) + "\n"
    (ROOT / "COMPLETE_RESULTS.txt").write_text(text, encoding="utf-8")
    (ROOT / "docs" / "RESULTS_SUMMARY.md").write_text(
        "```\n" + text + "```\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
