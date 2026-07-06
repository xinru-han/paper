# kg/month Unit Conversion and Outlier Cleaning Log

Generated at: 2026-07-06 14:10:28

- Converted official analysis data to kg/month/household and yuan/kg.
- Excluded quantity outlier household-category rows using category-specific P99.5 thresholds.
- Cleaned price outliers before robustness and main-price use.
- Backups of prior analysis files were written to `data/backups/`.

## Summary

- Rows before: 28520
- Rows after: 28208
- Rows dropped: 312
- Households before: 3565
- Households after: 3565
