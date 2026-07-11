# Paper 3 build report
Generated: 2026-07-11 17:35:00

- village survey: 361 villages (181 in 2023 / 180 in 2024); fe03_min missing 17
- POI file: 8778 POIs within 5km across 176 villages (villages w/o any POI get 0)
- retail_pc1: PC1 explains 39.2% of variance; loadings all same-signed
  loadings: poi_grocery_5km=-0.47, poi_fresh_5km=-0.50, poi_meat_5km=-0.51, vs_super_5km=-0.31, vs_grocery_5km=-0.08, vs_market_5km=-0.31, vs_meat_5km=-0.27
- village analysis block: 361 rows; NA in conditioning set: 6/0/2/0
- household block: 3565 rows, 3547 with roster aggregates; median sown 2.3 mu
- food_ssr_w rebuilt (delivered overall rate broken): mean 0.26, median 0.22
- person block: 8565 recalls; women 15-49 (mddw eligible): 982; children 6-59m: 101
- age missing (roster-unmatched recalls): 3038 of 8565 -> median-imputed + dummy
- counties appearing in both years: 0 of 40 (county×year FE == county FE)

Sample flow:
- person recalls: 8565
- + household controls merged: 8565
- + village IV/treatment merged: 8544
- final analysis (non-missing y/T/IV/controls): 8386

Sealed outcomes note: absolute nutrient quantities / gram families excluded
portfolio-wide per Paper-2 Task-3 unit audit FAIL (D1/D6).
