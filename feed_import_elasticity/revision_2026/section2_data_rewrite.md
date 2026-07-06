# Section 2 (Data and price measurement) — 修订文本

**问题**：原文明确说明"the log unit value is regressed on the log
quantity..."作为主口径构建方法 -- 这正是审改意见Issue 2指出的内生性问题
(将批量折扣与真实需求曲线斜率混淆，且未纳入生成回归量的抽样误差)。

**建议替换第4段**（"For a positive product cell..."起）：

> For a positive product cell, the direct unit value equals the import
> value divided by the import quantity. However, unit values are not pure
> prices: they vary with shipment scale, source-country composition,
> quality, freight, timing, and policy wedges. The main quality-adjusted
> price measure regresses the log unit value on source-country count,
> source concentration (HHI), top-source share, province fixed effects,
> and year-quarter fixed effects -- deliberately EXCLUDING log quantity
> from this main specification, because shipment quantity and price are
> jointly determined by the same demand shock the model seeks to
> estimate, so including it would conflate a genuine bulk-discount supply
> relationship with the demand-curve slope of interest. Missing
> province-quarter-product cells are filled using one of three
> complementary price measures, reported throughout as a sensitivity
> band rather than a single point estimate: (i) "completed", a pooled
> (all-quarter) product-level mean fill; (ii) "loo_quarter_winsor", a
> same-quarter leave-one-out mean fill (a stricter test of the fitted
> price's information content, since a missing cell's imputed value never
> uses that quarter's own data); and (iii) "landed_proxy", the raw
> unadjusted unit value with the same imputation rule, retained as a
> lower-processing benchmark. As a robustness check, we also estimate a
> version of the price-adjustment regression that includes log quantity
> (matching the original specification), reported in Appendix Table A-U;
> the quantity coefficients are uniformly negative (ranging from -0.004
> for cassava to -0.31 for oats and corn), consistent with bulk-shipment
> discounts, but we do not use this specification for the headline
> results because of the endogeneity concern above.

**新增段落（价格插补的测量误差说明，呼应Issue 8）**：

> Because a substantial share of province-quarter-product cells have zero
> recorded trade in a given quarter (Table 1), the corresponding price is
> necessarily imputed rather than directly observed. This is a form of
> classical measurement error whose severity differs across the three
> price measures above; Section 4 reports headline results for the
> "completed" measure and the full sensitivity band across all three in
> the appendix, so that readers can assess how much of the substitution
> evidence depends on the imputation rule.
