# Commercialization Rate Audit

Generated at: 2026-07-06 13:52:53

## Finding

- `commercialization_rate` is not present in the current analysis-ready household-category file.
- Current analysis-ready columns only contain self-provisioning participation, self-production amount, consumption, self-sufficiency, and price variables.
- Raw labels indicate sales and self-use quantities exist for some production modules, but denominators differ by module and category.
- A clean commercialization rate therefore requires a separate denominator audit before inclusion.

## Matching variables found in analysis-ready data

- None.

## Decision

- Do not construct `commercialization_rate` in the revised main rerun.
- Record as HUMAN REVIEW REQUIRED: denominator unclear.
