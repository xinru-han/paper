# CCTV purchase data construction and measurement audit

This study uses the CCTV purchase records, not the rural household survey. All statistical construction in `code/01_build_data.do` is executed in Stata 17. The companion log records every import, merge, identity check and sample count.

Parallel Stata sessions must be launched with distinct `STATATMP` directories. The data build uses `tmp_data_build`; model/corner jobs use separate directories. The initial diagnostic run produced all 84 descriptive rows but then lost a temporary raw file because of a concurrent temporary-name collision. Its log is preserved as `logs/01_build_data_first_temp_collision.log`. A second diagnostic run is preserved as `01_build_data_float_diagnostic.log`. The final full build reimports the unchanged original CSV with `asdouble`, recomputes all statistics, and does not use the optional descriptive-cache argument. Thus original decimal monetary/quantity values are not first rounded to Stata float precision.

## Source provenance

- Transactions: `/root/data/数据/央视数据/Data_merged.csv`, all 10 original columns, including `Price`. The previous `transaction_inputs.dta` is not the input because it omits the original `Price` column.
- Original transaction CSV SHA-256: `8d575c120fbd6d225a5649029a11b95bd08692f07992467df1fee252575af694`.
- Household city tier: `/root/data/数据/央视数据/补充样本城市级别--20260610.xlsx`, sheet `样本城市级别`. The mapping is checked to be unique by household ID before an `m:1` merge.
- Independent prices: `/root/data/Paper/央视数据/Paper1-EASI/processed/external_food_prices_category_province_month_2020_2022.csv`. Only `price_fill_level==observed_province_month` enters the eight- and nine-category systems.
- All 21 transaction categories in 2020-2022 are retained at the audit/universe level. Household ID is imported as text. The original CSV contains 10,420,107 records.

## Categories

| Eight-category good | Original transaction categories |
|---|---|
| 1 Staples | Rice, flour, dried noodles, instant noodles |
| 2 Edible oil | Edible oil |
| 3 Vegetables | Vegetables |
| 4 Fruit | Fruit |
| 5 Pork | Pork |
| 6 Other meat | Poultry, other meat, beef, lamb |
| 7 Aquatic products | Seafood |
| 8 Dairy | Ambient milk, fresh milk, ambient yogurt, fresh yogurt, cheese, butter, adult milk powder |

The nine-category system separates poultry/other meat from beef/lamb; aquatic products and dairy then become goods 8 and 9. Nuts are retained as observed spending in every household file, but are outside these conditional budgets. A tenth category is not priced by copying the oil series: no independent observed nut series is currently available.

## Missing quantity is not zero purchase

`Volume==0` accompanied by positive `Spend` is treated as quantity unavailable, not as nonparticipation. The original `Price` and `Spend/Volume` are audited only where recorded/defined; neither is used as the main demand price. The derived demand quantity `q=m*w/p` is a reference-price purchasing-volume equivalent, not kilograms and not the recorded `Volume`.

`item_transaction_descriptives.csv` contains all 21 categories and four variables (`Spend`, `Volume`, original `Price`, positive-volume unit value), with nonmissing/missing/zero/negative counts, means, standard deviations, minima, 1st/5th/25th/50th/75th/95th/99th percentiles and maxima. `item_active_month_descriptives.csv` separately reports zero-inclusive household-month spending and purchase rates.

## Conservative anomaly handling

No transaction is dropped, winsorized, or altered solely because of a low/high price, quantity or expenditure. Nonpositive/missing recorded expenditure contributes zero to the positive purchase budget and is counted explicitly. Exact repeats of all ten substantive fields are flagged and counted, not automatically removed: the source has no transaction identifier and identical purchases on one date cannot be distinguished from duplicated records. This is a measurement limitation rather than evidence that all repeats are erroneous.

## Household windows and zeros

The active universe is first constructed from all 21 categories, including nut-only household-months. Every transaction month is kept in `household_month_active_universe.dta`. Estimation-window files retain months with strictly positive spending in at least one of the 21 categories; no entirely unrecorded month is inserted and called a zero.

An absent category within a genuinely active month is a zero category purchase. Nut-only active months have zero covered budget, missing conditional shares/quantities, and remain in the household files. Entire windows with zero eight/nine-category budget do not enter the strictly positive conditional-budget cells; their exclusions are counted. Nut-only months within a positive-budget quarter/year still contribute to its active-month denominator.

Quarter/year spending sums the actual recorded active months. `month_count` is the number of such months; `m=covered_spend/(size_proxy*month_count)` is therefore monthly-equivalent purchasing expenditure per population proxy, not a calendar-time total or an average over imputed zero months. Complete three-month/twelve-month windows are saved separately as sensitivity samples.

In the baseline, `size_proxy` is the population proxy from the window's last recorded month. Thus baseline `m` is monthly-equivalent household purchases divided by the last recorded population proxy, not a genuine month-by-month population-normalized person average when the population interval changes. The predeclared positive-budget baseline is not altered to hide this difference.

The separate `01_permonth_size_sensitivity.do` divides each active month's item purchases by that month's population proxy before taking the mean over actual active months. Its `household_quarter/year_8_permonth_size` and `cells_quarter/year_8_permonth_size` files reclose `m`, shares and reference-price quantity equivalents under the same province-window prices. They retain original household period expenditure variables, add `perproxy_month_spend1..8`, and preserve baseline `m_lastsize`. Within-month conflicting population records still use the last transaction's population interval; true monthly household counts remain unobserved. Family/income classification remains the last recorded window attribute, as in the baseline. This is an explicit population-normalization sensitivity, not a replacement baseline or a solution to unobserved true household size.

The executed per-month population sensitivity preserves all 203,337 positive-budget quarters and 58,150 positive-budget years. Quarter mean `m` changes from 212.764880 to 212.413676; year mean `m` changes from 207.385920 to 206.251286. Month-end population intervals change in 3,482 positive quarters and 3,943 positive years. Within these affected observations, the mean absolute proportional budget difference is 38.3894% and 27.3610%, respectively. Thus a small change in the overall mean does not establish negligible individual measurement differences. Observations with no monthly population-interval change agree within machine precision. `permonth_size_sensitivity.csv` reports both level and proportional differences, including complete-window subsets and extreme differences.

Household attributes are the last recorded attributes within the month, then within the quarter/year. Changes within months/windows are flagged. Family types are exactly the reported young/adult/elderly/adolescent categories. The five income bands remain interval labels; the source does not establish a verified income reporting period. Population proxies are 1.5, 3, 4 and 5.5 for the four observed population intervals; they are not observed household counts.

## Independent price construction

Fifteen transaction categories have acceptable external province-month observation/proxy matches. Main group weights are national category spending shares from 2020-2021 only, restricted to those priced categories and normalized within group. They are constant across province and month. Separate 2021 weights are also saved for sensitivity. Complete group composition, weight sums, and the 24-province by 36-month grids are asserted.

The group index is the exponential of the weighted mean log price, normalized by its mean log level over the 2020-2021 province-month grid. This produces comparable reference-price quantity equivalents without inventing physical aggregate units. Quarter prices use all three natural months in the province-quarter; year prices use all twelve natural months, including months without household transactions. Consequently every household in a province-window faces the same group price index. This is essential for aggregating zero-inclusive quantities into cells.

`category_external_prices_observed.csv` preserves physical unit strings, source varieties, match types and observation counts. `group_price_coverage_8/9.csv` reports the spending represented by actually priced categories; the staple and dairy indices do not directly price every constituent. Other meat prices may be proxies rather than an exact match to the household's purchased variety. External prices avoid the household's mechanical unit-value construction but do not prove price exogeneity.

Training weights exclude the held-out 2022 year. Province-holdout validation needs basket/reference construction that excludes the held-out province as well; the full category province-year spending and observed category-price grids are supplied so validation can rebuild those transformations rather than reuse them blindly.

## Estimation data contract

`household_month_8/9`, `household_quarter_8/9`, and `household_year_8/9` are provided in DTA and CSV. Their fields include household/province/period IDs, family type, income/population intervals, city tier, population proxy, observed active months, covered expenditure, omitted nut spending, `m`, `spend1..K`, `w1..K`, `p1..K`, and `q1..K`.

`cells_quarter_8/9` and `cells_year_8/9` aggregate by province, period, reported family type, income band and population band. No minimum cell-size threshold is applied. Only strictly positive covered-budget windows are eligible; zero categories are not deleted. Cell quantities are arithmetic means of household `q`, cell budget is mean `m`, and cell shares are reconstructed as `w_i=p_i*mean(q_i)/mean(m)`, rather than averaging household shares. All shares are asserted to add to one within numerical tolerance. `nobs` equals the number of household-windows in the cell, `n_households` equals the unique household count within that single window, and `complete_n` counts complete-record windows.

The stricter complete/stable files additionally require that family type, income interval and population interval agree across every recorded transaction, not merely across last-month attributes. Their names end in `_complete_stable`. They are separate sensitivity inputs and do not modify the primary household/cell samples.

The ordinary `changed_type`, `changed_income_band` and `changed_size_band` window flags compare month-end attributes across the window; they are not exhaustive transaction-level conflict flags. `01_window_attribute_checks.do` also aggregates original within-month transaction conflicts. Among 185,908 complete positive-budget quarters, month-end type/income/population changes affect 2,177/10,302/3,442 windows, respectively; original within-month conflicts affect 2,343/10,509/3,457 windows. There is no province change. Their union leaves 171,612 strictly stable quarters. Among 37,903 complete positive-budget years, the corresponding month-end changes are 2,178/10,828/3,398 and within-month conflicts 2,067/9,591/3,005, leaving 24,581 strictly stable years. Since the baseline uses the last recorded population proxy, only the stricter stable sample eliminates ambiguity from changing population intervals. This sensitivity does not assume missing transaction months are zero consumption.

The cell-average estimand is not an exact micro demand model under unrestricted heterogeneous preferences. Frequency changes assess low-frequency purchases, inventories, and recording patterns; they cannot by themselves establish that a month without transactions is an actual zero consumption month.

`01_coarse_cells.do` provides a prespecified aggregation sensitivity, `cells_quarter_8_coarse`, which pools population intervals within province-quarter-family-income cells. It directly averages the same positive-budget household-quarter observations without any extra household deletion or minimum cell-size rule. Prices remain the identical province-quarter indices; shares are reconstructed from mean quantities and mean budget. This tests sensitivity to thin-cell sampling noise and aggregation of zero purchases, rather than selecting a grouping because of desired elasticity signs. The original 14,676 population-stratified cells remain unchanged.

The coarser data contain 5,733 cells representing exactly the original 203,337 positive-budget household-quarter observations. Median cell size rises from 8 to 24; 36 one-household cells remain instead of 1,911. No minimum-size threshold or all-goods-positive restriction is applied. Zero-quantity cells remain for every good (3, 32, 4, 7, 15, 18, 24 and 4, respectively), and the minimum individual budget remains 0.231667. `coarse_cells_summary.csv` records the cell-size distribution and residual zero counts.

## Executed audit outputs

Final counts and frequency-specific zero rates are recorded in `outputs/data_audit/sample_flow.csv` and `frequency_diagnostics.csv`; these are the authoritative run outputs rather than copied numbers from the former rural survey or previous CCTV models.

| Executed quantity | Result |
|---|---:|
| Original transactions | 10,420,107 |
| Original households | 27,653 |
| All-category active household-months | 584,835 |
| Nut-only active household-months retained | 1,167 |
| Positive covered-budget household-months | 583,668 |
| All-category active household-quarters | 203,418 |
| Positive covered-budget household-quarters | 203,337 |
| Positive covered-budget complete quarters | 185,908 |
| Positive covered-budget complete/stable quarters | 171,612 |
| Quarter cells (both eight/nine groups) | 14,676 |
| Median households per quarter cell | 8 |
| One-household quarter cells retained | 1,911 |
| Positive covered-budget household-years | 58,150 |
| Year cells (both eight/nine groups) | 3,730 |
| Positive covered-budget complete years | 37,903 |
| Positive covered-budget complete/stable years | 24,581 |

Recorded zero quantity is 77.1002255543% of transactions, and missing original `Price` is 77.1000528114%. There are 8,031,806 positive-spending transactions with zero recorded quantity. Original positive `Price` and positive-volume unit value differ beyond relative tolerance `1e-6` in 3,682 transactions; this is counted rather than silently reconciled.

There are 689,776 records in exact-repeat groups. If every extra exact repeat were erroneous, total positive purchase spending would fall by at most 1.891542% under this particular exact-match definition; vegetables are much more affected, with an 8.409883% bound. This is a bound/diagnostic, not confirmation of duplicate transactions. `item_duplicate_price_audit.csv` provides the original and exact-unique lower-bound totals by item. The `duplicate_multiplicity_sum` column in `category_province_year_spending.csv` is the sum of repeat multiplicities, not a count of distinct flagged rows; the dedicated audit's `rows_in_duplicate_groups` is the appropriate flagged-row count. Its metadata label was corrected without changing spending, prices, or model inputs.

Eight-group complete-positive purchase rates (all groups purchased) are 6.488963% monthly, 34.630194% quarterly and 74.691314% yearly. For nine groups they are 2.990056%, 22.213861% and 63.819432%. Thus quarterly/yearly aggregation greatly reduces zeros but does not justify declaring the individual zero-purchase problem absent.

The monthly-equivalent positive covered budget per population proxy has mean/median of 217.137/148.767 RMB at monthly frequency, 212.765/152.857 RMB at quarterly frequency, and 207.386/152.969 RMB at yearly frequency. These are covered-purchase budgets, not total food consumption or reported income. Quarter budgets span 0.231667 to 4,577.344 RMB; no tail observation is deleted on the basis of the resulting elasticities.

`01_validate_data.do` ran successfully for all three windows and both classifications: exact construction of covered spending, active-month normalization, nonnegative zero-inclusive quantities, `p*q=m*w`, and share adding-up all passed the stated tolerances. `01_refresh_descriptives.do` recomputes the descriptive postfiles with an explicit double type for every statistic: Stata's `postfile double` prefix is not assumed to carry over to subsequent unnamed types. This refresh does not alter any estimation input.

## Frozen whole-province validation transformations

Province fold membership is frozen as `mod(province-1,5)+1`. `01_build_cv_prices.do` reconstructs both food-category basket weights and log-price normalization inside each fold, using only non-test provinces in 2020-2021. All three natural months are still used for each province-quarter, including test prices as observed covariates. `cells_quarter_8/9_cvfold1..5.csv` retains the baseline budgets/shares/counts, replaces prices with the corresponding fold-specific indices, and recalculates `q=m*w/p`. `cv_fold` is the province's fixed membership; `heldout_fold` identifies the transformation used in the particular file. Both classifications and every fold were executed and checked; original baseline cells remain unchanged.

## Independent prediction-code checks

`01_review_prediction.do` exercises ordinary roots, exact grid roots, a mixed valid/invalid vector, roots near a grid point, and a deliberately nonmonotone cost function with two roots. It is a synthetic numerical test, not empirical inference or bootstrap. Its CSV files distinguish expected valid cases from deliberate invalid cases. These tests were supplied to the root implementation for correction of global-vector failure propagation and duplicate grid-root counting.

After those corrections, all five explicit numerical assertions pass: grid and near-grid roots are counted once, one invalid budget row does not destroy its valid neighbor, and a genuinely two-root case is rejected. The reported root count is a numerical finite-grid/turning-point check on the stated utility search interval, not a global mathematical proof of uniqueness outside that interval.
