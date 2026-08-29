import pandas as pd

from casm_world.policy import build_tariff_paths, complete_tariff_reference


def test_missing_reference_is_not_zero_and_post_2035_is_held():
    codebook = pd.DataFrame(
        {
            "economy_id": ["AAA", "BBB", "CCC"],
            "region_code": ["001", "001", "002"],
        }
    )
    observed = pd.DataFrame(
        {
            "economy_id": ["AAA", "CCC"],
            "observation_year": [2022, 2021],
            "tariff_rate_percent": [10.0, 20.0],
            "region_code": ["001", "002"],
        }
    )
    reference, _ = complete_tariff_reference(
        observed, model_accounts=["AAA", "BBB", "DDD"], codebook=codebook
    )
    keyed = reference.set_index("economy_id")
    assert keyed.at["BBB", "tariff_rate_percent_2023"] == 10.0
    assert keyed.at["DDD", "tariff_rate_percent_2023"] == 15.0
    paths, report = build_tariff_paths(
        reference,
        commodity_codes=["RIC", "WHE"],
        scenario_multipliers={"SSP1": 0.5, "SSP3": 1.5},
        years=range(2023, 2051),
        target_year=2035,
    )
    assert not paths["tariff_rate_percent"].isna().any()
    assert paths[paths.year.ge(2035)].groupby(
        ["scenario", "economy_id", "commodity"]
    )["tariff_rate_percent"].nunique().eq(1).all()
    assert report["silent_zero_fill"] is False
