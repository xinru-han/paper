# Nutrition Conversion Audit

Generated: 2026-07-06T10:07:47

## Nutrition table

- Processed rows: 22
- `kcal_per_kg_as_purchased = kcal_per_100g_edible * 10 * edible_share / 100`.
- If reported energy is missing or zero, energy is reconstructed from protein, fat and carbohydrate.
- Non-positive kcal rows after processing: 0

## Grain aggregation

- Grain-equivalent weights are retained for accounting, including potato divided by 5.
- Calorie aggregation uses actual consumption-quantity weights and actual kcal/kg, not the potato /5 grain-equivalent conversion.
- Potato audit: grain_equiv_weight=0.0400321; kcal_weight=0.172533.
- Sum of kcal weights: 1
- Sum of grain-equivalent weights: 1
