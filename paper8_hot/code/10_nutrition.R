# Paper 8 script 10 (= plan 86): nutrition layer
#  implied quantities = spend / monitored price (province x date x category),
#  x nutrient coefficients (per kg as-purchased) -> daily purchased nutrients.
#  (a) unit-level: per-capita kcal/protein/fe response to temperature bins
#  (b) diet diversity on trip days (n categories, Shannon)
#  (c) RIF quantile regressions of trip-day protein (q25/50/75)
source("/root/data/Paper/央视数据/paper8-hot/code/00_setup.R")

trips <- fread(file.path(DIR_INT, "trips_hh_day_cat.csv.gz"), encoding = "UTF-8")
trips[, date := as.IDate(date)]
hh <- fread(file.path(DIR_INT, "hh_info.csv"), encoding = "UTF-8")
trips <- merge(trips, hh[, .(ID, Province, tier_a)], by = "ID")

pr <- fread(file.path(DIR_INT, "price_cat_province_date.csv.gz"), encoding = "UTF-8")
pr[, date := as.IDate(date)]
pr <- pr[is.finite(external_price_mean_monitor) & external_price_mean_monitor > 0]
# prices are per 500g (元/500克) except liquids per 升 (~0.97kg for milk)
pr[, per_kg := external_price_mean_monitor * fifelse(grepl("升", units), 1.03, 2)]
# forward-fill monitor prices to daily within province x category
setorder(pr, province, Category, date)
alldays <- CJ(province = unique(pr$province), Category = unique(pr$Category),
              date = seq(as.IDate("2020-01-01"), as.IDate("2022-12-31"), 1))
prd <- pr[alldays, on = .(province, Category, date), roll = 30]
prd <- prd[is.finite(per_kg), .(province, Category, date, per_kg)]

trips <- merge(trips, prd, by.x = c("Province","Category","date"),
               by.y = c("province","Category","date"), all.x = TRUE)
logmsg("10: price match rate ", round(trips[, mean(is.finite(per_kg))], 3))
trips[, qty_kg := spend / per_kg]

nut <- fread(file.path(DIR_LKP, "nutrient_coef_cn.csv"), encoding = "UTF-8")
trips <- merge(trips, nut[, .(Category, kcal, protein, fe_mg)], by = "Category", all.x = TRUE)
trips[, `:=`(kcal_d = qty_kg * kcal, prot_d = qty_kg * protein, fe_d = qty_kg * fe_mg)]

## (a) unit-level nutrient responses
hhd <- trips[is.finite(prot_d), .(kcal = sum(kcal_d), prot = sum(prot_d), fe = sum(fe_d),
                                  n_cat = uniqueN(Category)), by = .(ID, Province, tier_a, date)]
act <- fread(file.path(DIR_INT, "unit_day_cat.csv.gz"), encoding = "UTF-8")[
  , .(n_active = first(n_active)), by = .(Province, tier_a, date = as.IDate(date))]
und <- hhd[, .(kcal = sum(kcal), prot = sum(prot), fe = sum(fe)), by = .(Province, tier_a, date)]
und <- merge(und, act, by = c("Province","tier_a","date"))
und[, `:=`(kcal_pc = kcal/n_active, prot_pc = prot/n_active, fe_pc = fe/n_active)]

utot <- readRDS(file.path(DIR_INT, "utot_frame.rds"))
und <- merge(und, utot[, .(Province, tier_a, date, unit, ym, dow, tbin, pbin, holiday_flag,
                           spring_festival_window_7, lockdown, ln_covid)],
             by = c("Province","tier_a","date"))
ctrl <- "pbin + holiday_flag + spring_festival_window_7 + lockdown + ln_covid"
res <- rbindlist(lapply(c("kcal_pc","prot_pc","fe_pc"), function(y) {
  m <- feols(as.formula(paste0("log(", y, ") ~ tbin + ", ctrl, " | unit^ym + dow")),
             data = und[get(y) > 0], cluster = ~Province, weights = ~n_active, notes = FALSE)
  ct <- as.data.table(coeftable(m), keep.rownames = "term")
  setnames(ct, c("term","est","se","t","p")); ct[, outcome := y][]
}))
fwrite(res, file.path(DIR_TAB, "t9_nutrient_response.csv"))
fwrite(und[, .(mean_kcal_pc = mean(kcal_pc), mean_prot_pc = mean(prot_pc), mean_fe_pc = mean(fe_pc))],
       file.path(DIR_TAB, "t9_nutrient_means.csv"))
logmsg("10: unit-level nutrient responses done")

## (b) diversity + (c) RIF quantiles at household trip-day level
hhd <- merge(hhd, utot[, .(Province, tier_a, date, unit, ym, dow, tbin, pbin, holiday_flag,
                           spring_festival_window_7, lockdown, ln_covid)],
             by = c("Province","tier_a","date"))
m_div <- feols(as.formula(paste0("n_cat ~ tbin + ", ctrl, " | ID + unit^ym + dow")),
               data = hhd, cluster = ~Province, mem.clean = TRUE, notes = FALSE)

rif_reg <- function(y, tau) {
  q <- quantile(y, tau)
  f <- density(y, from = q, to = q, n = 1)$y
  rif <- q + (tau - (y <= q)) / f
  rif
}
resq <- list()
pos <- hhd[prot > 0]
for (tau in c(0.25, 0.5, 0.75)) {
  pos[, rif := rif_reg(log(prot), tau)]
  m <- feols(as.formula(paste0("rif ~ tbin + ", ctrl, " | ID + unit^ym + dow")),
             data = pos, cluster = ~Province, mem.clean = TRUE, notes = FALSE)
  ct <- as.data.table(coeftable(m), keep.rownames = "term")
  setnames(ct, c("term","est","se","t","p"))
  resq[[as.character(tau)]] <- ct[, tau := tau]
  logmsg("10: RIF tau=", tau, " done")
}
ctd <- as.data.table(coeftable(m_div), keep.rownames = "term")
setnames(ctd, c("term","est","se","t","p")); ctd[, tau := NA_real_][, outcome := "n_cat"]
out <- rbind(rbindlist(resq)[, outcome := "rif_ln_protein"], ctd, fill = TRUE)
fwrite(out, file.path(DIR_TAB, "t10_diversity_rif.csv"))
logmsg("10: done")
