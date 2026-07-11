# Paper 3 — IV column mapping (fixed)
Generated: 2026-07-11 17:34:59

IV construction (GEE run 2026-04-26, see 地形变量与IV_GEE流程说明.md):
`iv_terrain_barrier_{town,county}_gee_Xkm = log(route_cost_distance / euclidean_distance)`
route cost = straight-line path buffered X km, slope-based cost surface;
i.e. the *detour index* of the proposal (ln corridor cost − ln straight dist) is
**already the delivered column** — no further transformation needed.

- corridor 1km: 361 villages, detour_town range [1.218, 12.645], detour_county [3.226, 12.653]
- corridor 2km: 361 villages, detour_town range [1.188, 12.635], detour_county [3.133, 12.645]
- corridor 5km: 361 villages, detour_town range [1.042, 12.606], detour_county [2.951, 12.629]

- straight-dist consistency (5km vs 1km): town max|Δ| = 0.0000 km, county = 0.0000 km

Correlations of detour measures:
```
                  detour_town_1km detour_town_2km detour_town_5km
detour_town_1km             1.000           0.996           0.986
detour_town_2km             0.996           1.000           0.995
detour_town_5km             0.986           0.995           1.000
detour_county_1km           0.672           0.683           0.687
detour_county_2km           0.676           0.689           0.695
detour_county_5km           0.673           0.689           0.701
                  detour_county_1km detour_county_2km detour_county_5km
detour_town_1km               0.672             0.676             0.673
detour_town_2km               0.683             0.689             0.689
detour_town_5km               0.687             0.695             0.701
detour_county_1km             1.000             0.998             0.990
detour_county_2km             0.998             1.000             0.995
detour_county_5km             0.990             0.995             1.000
```

Column mapping used throughout the project:
| project variable | source column |
|---|---|
| detour_town_5km (PRIMARY IV) | iv_terrain_barrier_town_gee_5km |
| detour_county_5km (aux IV / overid) | iv_terrain_barrier_county_gee_5km |
| detour_{town,county}_{1,2}km (robustness) | iv_terrain_barrier_*_gee_{1,2}km |
| dist_town / dist_county (conditioning) | *_straight_dist_km_gee_5km |

Primary IV choice (pre-registered here): the township corridor — the 5 km retail
environment is supplied through the township market town; the county corridor is
kept for over-identification and robustness. Buffer width 5 km is the main spec,
1/2 km are robustness (narrower corridor = closer to the actual path).

- NTL aux IV: 361 villages, iv_early_ntl_peak_dist_9294 range [1.15, 5.32] (log-km? raw km)
