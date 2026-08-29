import pandas as pd
import pytest

from casm_world.calibration import build_interim_equilibrium


def _observations():
    rows = []
    values = {
        ("AAA", "WHE"): {"production": 8.0, "domestic_supply": 7.0},
        ("BBB", "WHE"): {"production": 2.0, "domestic_supply": 4.0},
        ("AAA", "ETH"): {"energy_production": 1.0, "energy_consumption": 0.8},
        ("BBB", "ETH"): {"energy_production": 1.0, "energy_consumption": 1.2},
    }
    for (economy, commodity), accounts in values.items():
        for account, value in accounts.items():
            rows.append(
                {
                    "economy_id": economy,
                    "commodity": commodity,
                    "role": "balance",
                    "account": account,
                    "unit": "Mt",
                    "value": value,
                }
            )
    return pd.DataFrame(rows)


def test_interim_equilibrium_closes_every_product_and_derives_ddg():
    base, report = build_interim_equilibrium(
        _observations(), commodity_codes=["WHE", "ETH", "DDG"], ddg_ratio=0.75
    )
    assert len(base) == 6
    assert base.groupby("commodity")["net_import_2023"].sum().abs().max() < 1e-12
    ddg = base[base["commodity"].eq("DDG")]
    assert ddg["supply_2023"].sum() == pytest.approx(1.5)
    assert report["publishable"] is False


def test_missing_global_product_is_rejected():
    with pytest.raises(ValueError, match="lack positive global"):
        build_interim_equilibrium(
            _observations(), commodity_codes=["WHE", "ETH", "DDG", "SUG"], ddg_ratio=0.75
        )

