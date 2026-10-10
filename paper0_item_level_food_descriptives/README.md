# Food item-level descriptives

This directory rebuilds household food quantities and price descriptives at the
71 fixed questionnaire-item level for the 2023 and 2024 rural household survey.
It is intended to support a transparent re-selection of demand-system food
groups before any aggregation is imposed.

## Run

```bash
python3 code/build_item_descriptives.py
```

The default input paths point to the local raw/cleaned survey files under
`/root/data/数据/食物消费调查数据`. Use `--help` to override them.

## Main outputs

- `outputs/FOOD_ITEM_DESCRIPTIVES.xlsx`: review workbook with the complete
  catalogue, pooled and annual quantity statistics, household unit values,
  community price ranges, and validation checks.
- `outputs/item_selection_table.csv`: one pooled row per item for selecting new
  food groups.
- `outputs/analytic_family_selection_table.csv`: 22 unit-compatible candidate
  families; tobacco, alcohol, sugar, and tea are kept separate.
- `outputs/item_consumption_descriptives.csv`: pooled and annual quantity/source
  statistics.
- `outputs/item_household_price_descriptives.csv`: purchase unit values and
  self-production reported prices.
- `outputs/item_community_price_descriptives.csv`: community high/low price
  ranges mapped to household items.
- `outputs/community_category_price_descriptives.csv`: the original community
  questionnaire categories before household-item mapping.
- `outputs/household_item_long.dta`: household-item quantities and unit values
  for subsequent Stata work.
- `outputs/ITEM_LEVEL_SUMMARY.md`: compact Chinese summary and interpretation.

## Definitions

Monthly total consumption is the sum of purchased food directly consumed
(question 04), own-produced food directly consumed (question 07), and gifts
directly consumed (question 09). If question 04 is missing, the script uses the
nonnegative acquisition residual; if that is unavailable, it uses monthly
purchase frequency times quantity per purchase (questions 10 and 11). Question
02 is an acquisition quantity and is used with question 03 only to calculate a
purchase unit value.

Community `最高单价` and `最低单价` are retained as price-range endpoints. They
are not interpreted as prices for identical quality. Household purchase unit
values and self-production reported prices are reported separately. No
winsorisation or curvature restriction is applied in this descriptive build.
Raw quantity means are retained, while a separately named P99-winsorised mean
is supplied for interpretation because it does not overwrite the microdata.

Seven questionnaire placeholder columns (`tiankong*`) are excluded because the
export contains no food-name field. Pooling them would mix unidentified foods.

The household-item DTA and village-endpoint long CSV are produced locally but
excluded from Git because they retain record identifiers. All aggregate tables,
the workbook, audits, code, and documentation are versioned.
