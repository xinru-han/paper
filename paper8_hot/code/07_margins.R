# Paper 8 script 07 (= plan 83): trip margin vs basket-composition margin
#   Delta spend_g = Delta Pr(trip) * E[spend_g|trip]  (trip margin)
#                 + Pr(trip) * Delta E[spend_g|trip]  (composition margin)
# plus heterogeneity of the trip response (elderly, income tercile, tier).
source("/root/data/Paper/央视数据/paper8-hot/code/00_setup.R")

main  <- fread(file.path(DIR_TAB, "t1_main_coefs.csv"))
gmean <- fread(file.path(DIR_TAB, "t1_group_means.csv"))
dmean <- fread(file.path(DIR_TAB, "t1_dep_means.csv"))

## ---- decomposition from 05 estimates (delta-method-free, report parts)
dec <- rbindlist(lapply(c("gt30","le0","b24_30"), function(b) {
  b_trip <- main[outcome == "trip_any" & model == "lpm" & term == paste0("tbin", b), est][1]
  rbindlist(lapply(G10, function(g) {
    mg <- gmean[group == g]
    # composition margin: PPML semi-elasticity x mean conditional spend
    b_comp <- main[outcome == paste0("spend|trip_", g) & model == "ppml" & term == paste0("tbin", b), est][1]
    trip_margin <- b_trip * mg$mean_spend
    comp_margin <- dmean$trip_any * (exp(b_comp) - 1) * mg$mean_spend
    data.table(bin = b, group = g, beta_trip = b_trip, beta_comp_ppml = b_comp,
               trip_margin_yuan = trip_margin, comp_margin_yuan = comp_margin,
               total_yuan = trip_margin + comp_margin,
               share_trip_margin = trip_margin / (trip_margin + comp_margin))
  }))
}))
fwrite(dec, file.path(DIR_TAB, "t5_margin_decomposition.csv"))
logmsg("07: margin decomposition written")

## ---- heterogeneity of the trip response
hh   <- fread(file.path(DIR_INT, "hh_info.csv"), encoding = "UTF-8")
expo <- fread(file.path(DIR_INT, "province_tier_day_weather.csv.gz"), encoding = "UTF-8")
expo[, date := as.IDate(date)]
hol  <- fread(file.path(P1, "processed/calendar_holiday_2020_2022.csv"))
hol[, date := as.IDate(date)]
cov  <- fread(file.path(P1, "processed/covid_province_daily_2020_2022.csv"), encoding = "UTF-8")
cov[, date := as.IDate(date)]
lkd  <- fread(file.path(DIR_LKP, "lockdown_windows.csv"), encoding = "UTF-8")

grid <- readRDS(file.path(DIR_INT, "panel_hh_day.rds"))
grid <- merge(grid, hh[, .(ID, Province, tier_a, CityTier, Family_Type, income_mid)], by = "ID")
grid[, date := as.IDate(day_i, origin = "1970-01-01")]
grid <- merge(grid, expo[, .(Province = province, tier_a, date, tbin, pbin)], by = c("Province","tier_a","date"))
grid <- merge(grid, hol[, .(date, holiday_flag, spring_festival_window_7)], by = "date")
grid <- merge(grid, cov[, .(Province = province, date, covid_daily_new)], by = c("Province","date"), all.x = TRUE)
grid[is.na(covid_daily_new), covid_daily_new := 0][, ln_covid := log1p(covid_daily_new)]
grid[, lockdown := 0L]
for (i in seq_len(nrow(lkd))) {
  if (lkd$city[i] == "上海")
    grid[Province == lkd$province[i] & date %between% c(lkd$start[i], lkd$end[i]), lockdown := 1L]
  else
    grid[Province == lkd$province[i] & tier_a == 1L & date %between% c(lkd$start[i], lkd$end[i]), lockdown := 1L]
}
grid[, `:=`(unit = paste0(Province, "_", tier_a), ym = format(date, "%Y-%m"), dow = wday(date))]
grid[, `:=`(hot = as.integer(tbin == "gt30"), cold = as.integer(tbin == "le0"),
            elderly = as.integer(Family_Type == "老年家庭"),
            inc_ter = cut(income_mid, quantile(income_mid, c(0,1/3,2/3,1)), include.lowest = TRUE,
                          labels = c("low","mid","high")))]

ctrl <- "pbin + holiday_flag + spring_festival_window_7 + lockdown + ln_covid"
het <- list()
for (spec in c("elderly","inc_ter","CityTier")) {
  f <- as.formula(paste0("trip ~ tbin * factor(", spec, ") + ", ctrl, " | ID + unit^ym + dow"))
  m <- feols(f, data = grid, cluster = ~Province, mem.clean = TRUE, notes = FALSE)
  ct <- as.data.table(coeftable(m), keep.rownames = "term")
  setnames(ct, c("term","est","se","t","p"))
  het[[spec]] <- ct[grepl("tbin", term)][, spec := spec]
  rm(m); gc()
  logmsg("07: heterogeneity ", spec, " done")
}
fwrite(rbindlist(het), file.path(DIR_TAB, "t6_trip_heterogeneity.csv"))
logmsg("07: done")
