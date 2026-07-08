# =============================================================================
# 14_gap_accounting.R — v2 §17 headline: what share of the MDD-W shortfall is
# attributable to the food environment? Under the D1 architecture the point
# estimate is anchored on the (null) reduced form; the AR upper bound of the
# 2SLS coefficient gives the attribution UPPER BOUND. Monte-Carlo interval via
# coefficient draws. Pre-registered PG1 band was 10-30% (African literature);
# the result here is compared against it honestly.
# Counterfactual: raise every village's retail_pc1 to its province P75
# (2SLS scaling), or equivalently flatten detour to province P25 (RF scaling).
# =============================================================================
source("/root/data/Paper/食物消费数据/paper3-foodenv/code/00_setup.R")
con <- log_open("14_gap.log")

pers <- fread(file.path(DIR_DERIV, "p3_person.csv"), colClasses = list(character = c("xzc12","nhCode")))
wom <- pers[mddw_elig == 1 & !is.na(mddw) & !is.na(retail_pc1) & !is.na(detour_town_5km) &
            !is.na(ln_income) & !is.na(gaez_si) & !is.na(ln_vpop)]
XCw <- c("female_i", XH, ZV)   # women subsample: age spline dropped (age defines the group)

base_rate <- mean(wom$mddw)
gap <- 1 - base_rate
cat(sprintf("MDD-W attainment %.1f%% -> shortfall %.1f pp (n=%d women 15-49)\n",
            100 * base_rate, 100 * gap, nrow(wom)))

# ---- scenario deltas --------------------------------------------------------
wom[, prov := provn]
wom[, retail_p75 := quantile(retail_pc1, .75, na.rm = TRUE), by = prov]
wom[, d_retail := pmax(retail_p75 - retail_pc1, 0)]
wom[, detour_p25 := quantile(detour_town_5km, .25, na.rm = TRUE), by = prov]
wom[, d_detour := pmin(detour_p25 - detour_town_5km, 0)]   # negative = isolation removed

# ---- coefficient inputs -----------------------------------------------------
m_rf <- feols(rhs("mddw", c(IV_RF, XCw)), wom, cluster = ~xzc12)
b_rf <- coeftable(m_rf)[IV_RF, 1]; se_rf <- coeftable(m_rf)[IV_RF, 2]
f2 <- as.formula(paste("mddw ~", paste(XCw, collapse = "+"), "| county_year |", TREAT, "~", IV_2SLS))
m_iv <- feols(f2, wom, cluster = ~xzc12)
b_iv <- coeftable(m_iv)[paste0("fit_", TREAT), 1]; se_iv <- coeftable(m_iv)[paste0("fit_", TREAT), 2]

# AR upper bound for the 2SLS coefficient (95%), reused from 04 logic (coarse grid)
ar_up <- local({
  bs <- seq(-2, 3, length.out = 251)
  ts <- vapply(bs, function(b0) {
    dtt <- copy(wom); dtt[, b0 := b0]
    m <- feols(as.formula(paste0("I(mddw - b0*", TREAT, ") ~ ", IV_2SLS, " + ",
                                 paste(XCw, collapse = "+"), " | county_year")), dtt, cluster = ~xzc12)
    coeftable(m)[IV_2SLS, 3]
  }, numeric(1))
  acc <- bs[abs(ts) < qnorm(.975)]
  if (length(acc)) max(acc) else NA_real_
})

# ---- attribution: point + Monte Carlo (500 draws) ---------------------------
mc <- function(b, se, delta, B = 500) {
  draws <- rnorm(B, b, se)
  sapply(draws, function(bb) mean(pmin(pmax(bb * delta, 0), 1), na.rm = TRUE))   # capped LPM uplift
}
up_iv  <- mean(pmin(pmax(b_iv * wom$d_retail, 0), 1))     # 2SLS scaling (point)
up_rf  <- mean(pmin(pmax(b_rf * wom$d_detour, 0), 1))     # RF scaling (point)
up_arb <- mean(pmin(pmax(ar_up * wom$d_retail, 0), 1))    # AR 95% upper bound
mc_iv <- mc(b_iv, se_iv, wom$d_retail); mc_rf <- mc(b_rf, se_rf, wom$d_detour)

t8 <- data.table(
  quantity = c("MDD-W attainment (baseline)", "shortfall (pp)",
               "uplift, 2SLS scaling (pp, point)", "uplift, 2SLS scaling MC 95% CI",
               "uplift, RF scaling (pp, point)", "uplift, RF scaling MC 95% CI",
               "uplift, AR 95% UPPER BOUND (pp)",
               "attribution share of shortfall (point, 2SLS)",
               "attribution share UPPER BOUND (AR)"),
  value = c(sprintf("%.1f%%", 100 * base_rate), sprintf("%.1f", 100 * gap),
            sprintf("%.2f", 100 * up_iv),
            sprintf("[%.2f, %.2f]", 100 * quantile(mc_iv, .025), 100 * quantile(mc_iv, .975)),
            sprintf("%.2f", 100 * up_rf),
            sprintf("[%.2f, %.2f]", 100 * quantile(mc_rf, .025), 100 * quantile(mc_rf, .975)),
            sprintf("%.2f", 100 * up_arb),
            sprintf("%.1f%%", 100 * up_iv / gap),
            sprintf("%.1f%%", 100 * up_arb / gap)))
wtab(t8, "t8_gap_accounting.csv")
print(t8)
cat("\nPG1 pre-registered band was 10-30%: compare the AR upper bound against it.\n")

# by detour quartile (where would any effect be, if present)
wom[, dq := cut(detour_town_5km, quantile(detour_town_5km, 0:4/4, na.rm = TRUE),
                include.lowest = TRUE, labels = paste0("Q", 1:4))]
t8b <- wom[, .(mddw_rate = mean(mddw), n = .N,
               uplift_ar_ub = mean(pmin(pmax(ar_up * d_retail, 0), 1))), by = dq][order(dq)]
wtab(t8b, "t8b_gap_by_detour_quartile.csv")
print(t8b, digits = 3)
log_close(con)
