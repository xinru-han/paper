# =============================================================================
# 06_mechanisms_price.R — T5a: does terrain isolation raise local food prices?
# village×category log median paid price (household weighted-average unit values
# aggregated to the village) ~ detour, per category + perishable×detour stack.
# The proposal's village_category_price_candidates.csv (a P1 asset) does not
# exist; prices are built here from the household survey paid prices.
# =============================================================================
source("/root/data/Paper/食物消费数据/paper3-foodenv/code/00_setup.R")
con <- log_open("06_price.log")

hh <- fread(file.path(DIR_DERIV, "p3_household.csv"), colClasses = list(character = c("xzc12","nhCode")))
hh[, county_year := paste(provn, countyn, data_year, sep = "_")]

# village x category median paid price (only among buyers with a valid price)
pl <- list()
for (g in FOOD12) {
  pcol <- paste0(g, "_price_wavg_yuan_per_jin")
  d <- hh[!is.na(num(get(pcol))) & num(get(pcol)) > 0,
          .(price = num(get(pcol)), xzc12, county_year)]
  # trim extreme unit values within category (1%/99%)
  q <- quantile(d$price, c(.01, .99), na.rm = TRUE)
  d <- d[price >= q[1] & price <= q[2]]
  pl[[g]] <- d[, .(ln_p = log(median(price)), n_buyers = .N), by = .(xzc12, county_year)][, cat := g]
}
vprice <- rbindlist(pl)
vg <- fread(file.path(DIR_DERIV, "p3_village.csv"), colClasses = list(character = "xzc12"))
vprice <- merge(vprice, vg[, c("xzc12", "detour_town_5km", "detour_town_1km", ZV), with = FALSE], by = "xzc12")
vprice[, perishable := PERISHABLE[cat]]
cat(sprintf("village x category price cells: %d (median buyers per cell %.0f)\n",
            nrow(vprice), median(vprice$n_buyers)))

# per-category reduced form
out <- list()
for (g in FOOD12) {
  d <- vprice[cat == g & n_buyers >= 3]
  if (nrow(d) < 60) { out[[g]] <- data.table(cat = g, n = nrow(d)); next }
  m <- feols(rhs("ln_p", c(IV_RF, ZV)), d, cluster = ~xzc12)
  a <- coeftable(m)[IV_RF, ]
  out[[g]] <- data.table(cat = g, lab = FOOD_LAB[g], perishable = PERISHABLE[g],
                         b = a[1], se = a[2], p = a[4], n = m$nobs)
}
t5a <- rbindlist(out, fill = TRUE)
wtab(t5a, "t5a_price_by_category.csv")
print(t5a, digits = 3)

# stacked: perishable x detour differential (category FE x county_year FE)
vs <- vprice[n_buyers >= 3]
m_st <- feols(ln_p ~ detour_town_5km * perishable + ln_dist_town + ln_dist_county +
                ln_vpop + elevation_mean_z + water_occ_z + gaez_si + gaez_constraint |
                cat + county_year, vs, cluster = ~xzc12)
t5s <- tidy_fe(m_st, keep = "detour")
wtab(t5s, "t5a2_price_stacked.csv")
cat("\nStacked perishable differential:\n"); print(t5s, digits = 3)
log_close(con)
