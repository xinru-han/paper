import numpy as np
import pandas as pd

from casm_world.tfp import build_tfp_paths, estimate_tfp_rates


def test_rate_estimation_and_ssp_paths():
    rows = []
    for iso, rate in [("AAA", 0.01), ("BBB", 0.02)]:
        for year in range(2013, 2024):
            rows.append(
                {
                    "ISO3": iso,
                    "Region": "R1",
                    "Year": year,
                    "Variable": "TFP_Index",
                    "Value": 100 * np.exp(rate * (year - 2013)),
                }
            )
    rates = estimate_tfp_rates(
        pd.DataFrame(rows),
        start_year=2013,
        end_year=2023,
        country_weight=1.0,
        lower_bound=-0.005,
        upper_bound=0.035,
    )
    assert rates.set_index("economy_id").at["AAA", "annual_log_rate"] == pytest.approx(0.01)
    paths, report = build_tfp_paths(
        rates,
        model_accounts=["AAA", "OTHER_EASTERN_ASIA"],
        scenario_multipliers={"SSP1": 1.1, "SSP2": 1.0},
        years=range(2023, 2051),
    )
    assert paths[paths.year.eq(2023)].tfp_index_2023.eq(1.0).all()
    assert len(paths) == 2 * 2 * 28
    assert report["fallback_account_count"] == 1


import pytest

