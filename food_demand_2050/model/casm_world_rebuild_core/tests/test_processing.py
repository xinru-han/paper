from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from casm_world.processing import (
    build_processing_constraints,
    diagnose_processing,
    load_processing_config,
)


ROOT = Path(__file__).resolve().parents[1]


def _config():
    return load_processing_config(ROOT / "config/commodities.yaml")


def _synthetic_observations() -> pd.DataFrame:
    config = _config()
    rows: list[dict] = []

    def add(economy, commodity, role, account, value, source="TEST"):
        rows.append(
            {
                "year": 2023,
                "commodity": commodity,
                "role": role,
                "account": account,
                "unit": "Mt",
                "source_domain": source,
                "economy_id": economy,
                "value": value,
            }
        )

    oil_inputs = {
        "soybean_crush": ("SBS", 100.0, 50.0),
        "sunflower_crush": ("NBS", 80.0, 40.0),
        "rapeseed_crush": ("RBS", 60.0, 30.0),
    }
    for chain, (input_code, first, second) in oil_inputs.items():
        system = config["processing_systems"][chain]
        for economy, input_value in (("AAA", first), ("BBB", second)):
            add(economy, input_code, "balance", "processing", input_value)
            for output, coefficient in system["outputs"].items():
                add(
                    economy,
                    output,
                    "balance",
                    "production",
                    input_value * float(coefficient),
                )

    for economy, cane, beet in (("AAA", 100.0, 50.0), ("BBB", 40.0, 20.0)):
        sugar = 0.1003 * cane + 0.1607 * beet
        add(economy, "SCA", "balance", "processing", cane)
        add(economy, "SBE", "balance", "processing", beet)
        add(economy, "SUG", "balance", "production", sugar)

    for economy, seed_cotton in (("AAA", 100.0), ("BBB", 25.0)):
        add(economy, "CTN", "activity", "production", seed_cotton, "QCL")
        add(
            economy,
            "CTN",
            "balance",
            "production",
            0.3352 * seed_cotton,
            "CB",
        )

    dairy_outputs = {
        "BUT": 0.02,
        "CHE": 0.04,
        "NDM": 0.01,
        "FMK": 0.40,
        "WDM": 0.008,
        "ODA": 0.006,
    }
    for economy, raw_milk in (("AAA", 1_000.0), ("BBB", 500.0)):
        add(economy, "MLK", "balance", "production", raw_milk, "QCL")
        for output, ratio in dairy_outputs.items():
            account = "food" if output == "FMK" else "production"
            add(economy, output, "balance", account, raw_milk * ratio)

    return pd.DataFrame.from_records(rows)


def test_oilseed_mass_sugar_and_ratio_diagnostics_do_not_mutate_data():
    observations = _synthetic_observations()
    original = observations.copy(deep=True)

    audit = diagnose_processing(observations, _config())

    pd.testing.assert_frame_equal(observations, original)
    for chain in ("soybean_crush", "sunflower_crush", "rapeseed_crush"):
        global_mass = audit.global_diagnostics[
            audit.global_diagnostics["chain"].eq(chain)
            & audit.global_diagnostics["diagnostic"].eq("mass_balance")
        ].iloc[0]
        assert global_mass["complete_country_count"] == 2
        assert global_mass["input_volume_coverage_rate"] == pytest.approx(1.0)
        assert global_mass["paired_residual_mt"] == pytest.approx(0.0, abs=1e-12)

    sugar = audit.global_diagnostics[
        audit.global_diagnostics["chain"].eq("sugar_refining")
    ].iloc[0]
    assert sugar["paired_residual_mt"] == pytest.approx(0.0, abs=1e-12)

    fluid_milk = audit.global_diagnostics[
        audit.global_diagnostics["diagnostic"].eq("FMK_to_raw_milk_ratio")
    ].iloc[0]
    assert fluid_milk["paired_relative_residual"] == pytest.approx(0.40)
    assert np.isnan(fluid_milk["paired_residual_mt"])

    status = audit.chain_status.set_index("chain")
    assert status.loc["soybean_crush", "full_requested_chain_ready"]
    assert not status.loc["cotton_ginning", "full_requested_chain_ready"]
    assert not status.loc["dairy_solids", "numeric_constraint_ready"]


def test_constraint_matrix_has_auditable_coefficients_and_zero_residuals():
    observations = _synthetic_observations()
    system = build_processing_constraints(observations, _config())

    assert system.matrix.shape == (16, 28)
    equation = system.equations[
        system.equations["economy_id"].eq("AAA")
        & system.equations["chain"].eq("soybean_crush")
        & system.equations["equation_name"].eq("SBO_yield")
    ].iloc[0]
    row = system.matrix.getrow(int(equation["row"])).toarray().ravel()
    variables = system.variables
    input_column = variables.loc[
        variables["economy_id"].eq("AAA")
        & variables["commodity"].eq("SBS")
        & variables["account"].eq("processing"),
        "column",
    ].item()
    output_column = variables.loc[
        variables["economy_id"].eq("AAA")
        & variables["commodity"].eq("SBO")
        & variables["account"].eq("production"),
        "column",
    ].item()
    assert row[input_column] == pytest.approx(-0.1859)
    assert row[output_column] == pytest.approx(1.0)
    assert np.nanmax(np.abs(system.evaluate_observed())) < 1e-12


def test_missing_output_stays_missing_but_observed_zero_is_complete():
    observations = _synthetic_observations()
    missing = observations[
        ~(
            observations["economy_id"].eq("BBB")
            & observations["commodity"].eq("SBM")
            & observations["account"].eq("production")
        )
    ].copy()
    missing.loc[
        missing["economy_id"].eq("AAA")
        & missing["commodity"].eq("NBO")
        & missing["account"].eq("production"),
        "value",
    ] = 0.0

    audit = diagnose_processing(missing, _config())
    soy_mass_bbb = audit.country_diagnostics[
        audit.country_diagnostics["economy_id"].eq("BBB")
        & audit.country_diagnostics["chain"].eq("soybean_crush")
        & audit.country_diagnostics["diagnostic"].eq("mass_balance")
    ].iloc[0]
    assert not soy_mass_bbb["complete"]
    assert np.isnan(soy_mass_bbb["residual_mt"])

    sunflower_oil_aaa = audit.country_diagnostics[
        audit.country_diagnostics["economy_id"].eq("AAA")
        & audit.country_diagnostics["chain"].eq("sunflower_crush")
        & audit.country_diagnostics["diagnostic"].eq("NBO_yield")
    ].iloc[0]
    assert sunflower_oil_aaa["complete"]
    assert np.isfinite(sunflower_oil_aaa["residual_mt"])

    system = audit.constraints
    variable = system.variables[
        system.variables["economy_id"].eq("BBB")
        & system.variables["commodity"].eq("SBM")
        & system.variables["account"].eq("production")
    ].iloc[0]
    assert not variable["observed"]
    assert np.isnan(variable["observed_value"])


def test_real_unbalanced_benchmark_produces_all_requested_chain_statuses():
    observations = pd.read_csv(
        ROOT / "data/processed/benchmark_unbalanced_2023.csv"
    )
    audit = diagnose_processing(observations, _config())

    assert set(audit.chain_status["chain"]) == {
        "soybean_crush",
        "sunflower_crush",
        "rapeseed_crush",
        "sugar_refining",
        "cotton_ginning",
        "dairy_solids",
    }
    assert audit.report["source_data_modified"] is False
    oil_mass = audit.global_diagnostics[
        audit.global_diagnostics["chain"].isin(
            ["soybean_crush", "sunflower_crush", "rapeseed_crush"]
        )
        & audit.global_diagnostics["diagnostic"].eq("mass_balance")
    ]
    assert np.isfinite(oil_mass["paired_residual_mt"]).all()
