#!/usr/bin/env Rscript
# ============================================================================
# v2 step 41: frequency benchmark (the "annual benchmark" robustness).
# The full censored system is not identified at annual frequency (3 periods,
# and purchase incidence -> 1 makes the SY probit degenerate). Instead we
# document the storability mechanism with robust reduced-form quantities:
#   (a) purchase rate by group at monthly / quarterly / annual frequency —
#       for storable staples incidence saturates as the window widens, so the
#       purchase-TIMING (extensive) margin mechanically shrinks;
#   (b) among-purchaser intensive own-price elasticity by frequency, from an
#       FE log-quantity regression — the consumption response, which should be
#       modest and stable across frequencies.
# Together with the extensive/intensive margin decomposition (regularity/
# margin_decomposition_v2.csv) this shows the large monthly staple own-price
# elasticity is a purchase-incidence artifact of a storable good, not a high
# consumption elasticity.
# ============================================================================
suppressPackageStartupMessages({ library(data.table) })
base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
source(file.path(base, "src", "31_lib_v2.R"))
odir <- file.path(base, "outputs", "robustness")
dir.create(odir, recursive = TRUE, showWarnings = FALSE)

panel <- fread(file.path(base, "data_derived", "household_month_group9_v2.csv"), encoding = "UTF-8")
panel[, yr := substr(year_month, 1, 4)]
panel[, mo := as.integer(substr(year_month, 6, 7))]
panel[, qtr := paste0(yr, "-Q", ((mo - 1) %/% 3) + 1)]

# demographics carried once per (ID, period): take last month within period
build_period <- function(panel, pcol) {
  g <- panel[, .(spend = sum(spend_month),
                 pos = as.integer(sum(spend_month) > 0),
                 lp = mean(lp_ext),
                 fsz = family_size_midpoint[.N]),
             by = c("ID","Province", pcol, "food_group10")]
  tot <- g[, .(tot_spend = sum(spend)), by = c("ID", pcol)]
  g <- merge(g, tot, by = c("ID", pcol))
  g[, log_x_pc := log(tot_spend / fsz)]
  g[, q_pc := spend / exp(lp) / fsz]           # value-deflated quantity proxy
  setnames(g, pcol, "period")
  g[]
}

freq_rate <- list(); freq_int <- list()
for (fr in c("month","quarter","year")) {
  pcol <- switch(fr, month = "year_month", quarter = "qtr", year = "yr")
  d <- build_period(panel, pcol)
  # (a) purchase rate by group
  rate <- d[, .(frequency = fr, purchase_rate = mean(pos)), by = food_group10]
  freq_rate[[fr]] <- rate
  # (b) among-purchaser intensive own-price elasticity: FE log-q regression
  for (g in GROUPS9) {
    z <- d[food_group10 == g & pos == 1 & is.finite(q_pc) & q_pc > 0]
    z[, prov := factor(Province)]
    z[, per := factor(period)]
    # log q on log price + log expenditure + province & period FE
    m <- tryCatch(lm(log(q_pc) ~ lp + log_x_pc + prov + per, data = z),
                  error = function(e) NULL)
    if (!is.null(m)) {
      b <- coef(m)["lp"]; se <- summary(m)$coefficients["lp","Std. Error"]
      freq_int[[length(freq_int)+1]] <- data.table(
        frequency = fr, food_group10 = g, own_price_intensive = unname(b),
        se = unname(se), n_purchasers = nrow(z))
    }
  }
}
rate_out <- dcast(rbindlist(freq_rate), food_group10 ~ frequency, value.var = "purchase_rate")
setcolorder(rate_out, c("food_group10","month","quarter","year"))
int_out <- rbindlist(freq_int)
fwrite(rate_out, file.path(odir, "purchase_rate_by_frequency_v2.csv"), bom = TRUE)
fwrite(int_out, file.path(odir, "intensive_own_price_by_frequency_v2.csv"), bom = TRUE)

cat("=== purchase rate by frequency ===\n"); print(rate_out)
cat("\n=== among-purchaser intensive own-price elasticity by frequency ===\n")
print(dcast(int_out, food_group10 ~ frequency, value.var = "own_price_intensive"))
cat("\n=== DONE frequency benchmark ===\n")
