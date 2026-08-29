# China diet counterfactuals in CASM-World rebuild 2050

This study layer leaves the rebuilt CASM-World core unchanged. It translates
the prior China-CASM central diet solutions into annual pathway-to-baseline
food-preference multipliers and applies them only to mainland China's edible
food component before each world equilibrium is solved.

The main design pairs four diet pathways within each SSP. SSP2 is solved
annually for 2023-2050; SSP1, SSP3, SSP4 and SSP5 are solved at 2023 and 2050
to bound macro-driver dependence. Low, central and high response parameters,
plus the model's frozen inner-Cobb-Douglas demand sensitivity, are evaluated
for SSP2 in 2050.

The counterfactual is partial. Vegetables, fruit, eggs, aquatic foods, tubers
and sheep/goat meat are not markets in the 31-product world model. Nutrition
results therefore describe only the model-covered edible basket. Net trade is
an economy-product identity; the model has no bilateral trade allocation.

Run from the copied project root:

```bash
export PYTHONPATH="$PWD/src"
python3 study/china_diet/prepare_diet_paths.py
python3 study/china_diet/run_counterfactuals.py
python3 study/china_diet/analyze_counterfactuals.py
python3 study/china_diet/make_figures.py
python3 -m pytest -q study/china_diet/tests
```

