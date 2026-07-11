# =============================================================================
# 07_purchase_fafh.R — T5b: quantities and the extensive margin (household),
# self-sufficiency substitution, FAFH proxy (person xfy_dining, restaurant POI).
# All reduced form in detour (primary architecture).
# =============================================================================
source("/root/data/Paper/食物消费数据/paper3-foodenv/code/00_setup.R")
con <- log_open("07_purchase.log")

hh <- fread(file.path(DIR_DERIV, "p3_household.csv"), colClasses = list(character = c("xzc12","nhCode")))
hh[, county_year := paste(substr(xzc12, 1, 6), data_year, sep = "_")]
XHH <- c("ln_income", "hh_size_rec", "dep_ratio", "hb_fridge", "hb_vehicle", "ln_sown", ZV)

FOOD9 <- setdiff(FOOD12, c("tang", "cha", "yan"))   # sugar/tea columns are degenerate (n<12); tobacco not food
out <- list()
for (g in FOOD9) {
  bq <- paste0(g, "_buy_jin"); sr <- paste0(g, "_self_suff_rate")
  hh[, buy_any := as.integer(num(get(bq)) > 0)]
  hh[, ln_buy  := log1p(w99(num(get(bq))))]
  hh[, ssr     := pmin(pmax(num(get(sr)), 0), 1)]
  for (yy in c("buy_any", "ln_buy", "ssr")) {
    d <- hh[!is.na(get(yy))]
    m <- tryCatch(feols(rhs(yy, c(IV_RF, XHH)), d, cluster = ~xzc12), error = function(e) NULL)
    if (is.null(m) || !IV_RF %in% rownames(coeftable(m))) next
    a <- coeftable(m)[IV_RF, ]
    out[[length(out) + 1]] <- data.table(cat = g, lab = FOOD_LAB[g],
      perishable = PERISHABLE[g], margin = yy, b = a[1], se = a[2], p = a[4],
      n = m$nobs, mean_y = mean(d[[yy]], na.rm = TRUE))
  }
}
t5b <- rbindlist(out)
wtab(t5b, "t5b_purchase_margins.csv")
cat("Extensive margin (buy_any), perishables first:\n")
print(t5b[margin == "buy_any"][order(-perishable, p)], digits = 3)
cat("\nSelf-sufficiency response:\n")
print(t5b[margin == "ssr"][order(-perishable, p)], digits = 3)

# total food spend + overall self-sufficiency
hh[, ln_food_spend := log1p(w99(num(food_monthly_total)))]
res2 <- list()
for (yy in c("ln_food_spend", "food_ssr_w")) {
  m <- feols(rhs(yy, c(IV_RF, XHH)), hh[!is.na(get(yy))], cluster = ~xzc12)
  a <- coeftable(m)[IV_RF, ]
  res2[[yy]] <- data.table(outcome = yy, b = a[1], se = a[2], p = a[4], n = m$nobs)
}

# FAFH proxy: person dining-out expense (48h) — extensive margin; plus
# village restaurant POI count as the "environment" side
pers <- fread(file.path(DIR_DERIV, "p3_person.csv"), colClasses = list(character = c("xzc12","nhCode")))
pers[, fafh_any := as.integer(!is.na(xfy_dining) & xfy_dining > 0)]
m_f <- feols(rhs("fafh_any", c(IV_RF, XI, XH, ZV)), pers, cluster = ~xzc12)
a <- coeftable(m_f)[IV_RF, ]
res2[["fafh"]] <- data.table(outcome = "fafh_any (person)", b = a[1], se = a[2], p = a[4], n = m_f$nobs)

vg <- fread(file.path(DIR_DERIV, "p3_village.csv"), colClasses = list(character = "xzc12"))
vg[, county_id := substr(xzc12, 1, 6)]
vg[, ln_rest := log1p(poi_restaurant_5km)]
m_r <- feols(rhs("ln_rest", c(IV_RF, ZV), fe = "county_id"), vg, vcov = "hetero")
a <- coeftable(m_r)[IV_RF, ]
res2[["rest"]] <- data.table(outcome = "ln restaurants 5km (village)", b = a[1], se = a[2], p = a[4], n = m_r$nobs)

t5c <- rbindlist(res2)
wtab(t5c, "t5c_spend_selfsuff_fafh.csv")
print(t5c, digits = 3)
log_close(con)
