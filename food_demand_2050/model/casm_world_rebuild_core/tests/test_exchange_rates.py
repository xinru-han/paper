import numpy as np
import pandas as pd
import pytest

from casm_world.exchange_rates import (
    build_exchange_rate_paths,
    estimate_real_exchange_rates,
)


def test_estimation_anchor_and_post_2035_hold():
    panel = pd.DataFrame(
        [
            {
                "economy_id": economy,
                "year": year,
                "real_lcu_per_usd": np.exp(rate * (year - 2013)),
            }
            for economy, rate in (("AAA", 0.01), ("TWN", -0.005))
            for year in range(2013, 2024)
        ]
    )
    rates = estimate_real_exchange_rates(
        panel,
        minimum_observations=5,
        country_weight=1.0,
        lower_bound=-0.03,
        upper_bound=0.03,
    )
    assert rates.set_index("economy_id").at["AAA", "annual_log_rate"] == pytest.approx(0.01)
    paths, report = build_exchange_rate_paths(
        rates,
        model_accounts=["AAA", "OTHER_EASTERN_ASIA", "MISSING"],
        scenario_multipliers={"SSP1": 0.5, "SSP3": 1.0},
        years=range(2023, 2051),
        taper_end_year=2035,
    )
    assert paths.loc[paths.year.eq(2023), "real_exchange_rate_index_2023"].eq(1).all()
    post = paths[paths.year.ge(2035)]
    assert post.groupby(["scenario", "economy_id"])[
        "real_exchange_rate_index_2023"
    ].nunique().eq(1).all()
    assert report["fallback_accounts"] == ["MISSING"]
