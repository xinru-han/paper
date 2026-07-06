# Editor Review Action Log

Generated at: 2026-07-06 14:28:46

Completed with current analysis-ready data:

- Add-one-block diagnostics for M0/M1/M2/M3 sensitivity and M1-to-M2 block attribution.
- Village fixed-effects robustness for overall outcomes and category-specific participation.
- Logit/probit participation robustness for overall and category-specific models.
- Bonferroni, Holm, and BH FDR corrections for category-level Wald tests.
- NSI reframing with participation/self-sufficiency and low-variation flags.
- Fixed common-sample composition and price robustness checks.
- Fixed-factor/no-income/no-expense sensitivity checks.
- Price unit-value and hedonic imputation diagnostics.
- Definition diagnostics for repeated-cross-section status, roster cap, land winsorization, sex coding, oils, and meat/aquatic aggregation.

Still requires manual or raw-item-code work:

- HA2 sex-codebook verification for `female_share` interpretation.
- Item-code review for `youzhi` and detail-level rebuild if meat versus aquatic categories are to be split.
- Raw item-level missing-code recovery before a valid NA-to-zero versus missing-exclusion participation robustness can be run.
- Formal theoretical model and replacement of the placeholder conceptual framework figure.
