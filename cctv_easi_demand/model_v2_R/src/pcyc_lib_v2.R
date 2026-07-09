# ============================================================================
# Purchase-cycle exclusion variables for the SY participation stage.
# For each (household, group) ordered in calendar time we build regressors that
# capture stock depletion / inter-purchase timing and are plausibly EXCLUDABLE
# from the consumption (share) equation conditional on current prices and real
# expenditure: past purchase timing shifts the probability of a purchase *this*
# period (a big rice bag last month => no purchase this month) but not the
# desired consumption level. These identify the participation/consumption split
# (Shonkwiler-Yen), and sharpen the weak G01/G09 probits.
#   pcyc_bought_lag1_<g>  : bought group g in the immediately preceding calendar
#                           month (0 if that month absent or no purchase)
#   pcyc_recency_<g>      : 1 / (1 + months since last positive purchase),
#                           in [0,1]; 0 when no prior purchase on record
#   pcyc_nohist_<g>       : 1 for the household's first appearance of group g
#                           (no purchase history yet), else 0
# All are built from strictly PAST information (shift within household).
# ============================================================================

add_purchase_cycle_vars <- function(panel) {
  stopifnot(all(c("ID","year_month","food_group10","positive_purchase") %in% names(panel)))
  p <- copy(panel)
  p[, .midx := as.integer(substr(year_month, 1, 4)) * 12L +
        as.integer(substr(year_month, 6, 7))]           # calendar month index
  setorder(p, ID, food_group10, .midx)
  # previous active row within (ID, group)
  p[, .prev_midx := shift(.midx), by = .(ID, food_group10)]
  p[, .prev_pos  := shift(positive_purchase), by = .(ID, food_group10)]
  # running "last month index with a positive purchase", strictly past:
  # shift first (drop the current month) then forward-fill (LOCF).
  p[, .last_buy_midx := nafill(shift(fifelse(positive_purchase == 1L, .midx, NA_integer_)),
                               "locf"), by = .(ID, food_group10)]
  p[, pcyc_bought_lag1 := as.integer(!is.na(.prev_midx) & .prev_midx == .midx - 1L & .prev_pos == 1L)]
  p[is.na(pcyc_bought_lag1), pcyc_bought_lag1 := 0L]
  p[, pcyc_nohist := as.integer(is.na(.last_buy_midx))]
  gap <- p$.midx - p$.last_buy_midx
  p[, pcyc_recency := fifelse(is.na(gap), 0, 1 / (1 + pmax(0L, gap)))]
  p[, c(".midx",".prev_midx",".prev_pos",".last_buy_midx") := NULL]
  p
}
