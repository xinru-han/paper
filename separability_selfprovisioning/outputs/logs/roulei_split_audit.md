# Roulei Split Audit

Generated at: 2026-07-06 14:26:59

## Finding

- Raw labels contain meat-detail variables: TRUE.
- Raw labels contain aquatic-detail variables such as `shuichan_1`: TRUE.
- The current analysis-ready household-category long data contains only the aggregate `roulei` category and does not contain separate `meat` and `aquatic_products` outcomes.
- A split would require rebuilding consumption, self-provisioning participation, self-production amount, price, and self-sufficiency outcomes from item-level raw variables.

## Decision

- Roulei split is not performed in this revised rerun.
- Human review is required before making split-category claims.
