# Preliminary input audit

Static audit of the processed source data on 2026-07-12:

- Household table: 3,565 unique text household IDs.
- Exact household-to-village merge on the first 12 ID characters plus survey year:
  3,554 direct matches and 11 unmatched households.
- The unmatched households belong to two village-year keys absent from the village
  questionnaire: `421002101213` (one household) and `510521117218` (ten households).
- `01_build_village_prices.do` retains these observations and labels their
  geographically derived price source. It does not manufacture or modify IDs.

The supplied Stata 17 binary cannot run in this container because its license is
not applicable. Consequently, generated CSV/DTA estimation results must be
created by running `code/00_run_all.do` in a licensed Stata environment.
