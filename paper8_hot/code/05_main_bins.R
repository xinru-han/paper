# Paper 8 script 05 (= plan 81): main temperature-bin regressions
#  (1) trip margin: any food purchase today (hh x day grid, LPM)
#  (2) daily total food spend (incl. zeros, LPM + PPML)
#  (3) per-group outcomes conditional on a trip day: buy indicator + spend (PPML)
#  Inference: province-clustered SE everywhere; wild cluster bootstrap +
#  permutation test on the unit-level aggregate spec (script writes all three).
source("/root/data/Paper/央视数据/paper8-hot/code/00_setup.R")

## ---- assemble regression frame
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

add_covariates <- function(dt) {
  dt <- merge(dt, expo[, .(Province = province, tier_a, date, tavg, tbin, pbin)],
              by = c("Province","tier_a","date"))
  dt <- merge(dt, hol[, .(date, holiday_flag, spring_festival_window_7, calendar_is_weekend)], by = "date")
  dt <- merge(dt, cov[, .(Province = province, date, covid_daily_new)], by = c("Province","date"), all.x = TRUE)
  dt[is.na(covid_daily_new), covid_daily_new := 0][, ln_covid := log1p(covid_daily_new)]
  dt[, lockdown := 0L]
  for (i in seq_len(nrow(lkd))) {
    if (lkd$city[i] == "上海")
      dt[Province == lkd$province[i] & date >= lkd$start[i] & date <= lkd$end[i], lockdown := 1L]
    else
      dt[Province == lkd$province[i] & tier_a == 1L & date >= lkd$start[i] & date <= lkd$end[i], lockdown := 1L]
  }
  dt[, `:=`(unit = paste0(Province, "_", tier_a), ym = format(date, "%Y-%m"),
            dow = wday(date), woy = pmin(isoweek(date), 52L))]
  dt
}
grid <- add_covariates(grid)
logmsg("05: regression frame ", nrow(grid), " rows (dropped unmatched: weather join)")

ctrl <- "pbin + holiday_flag + spring_festival_window_7 + lockdown + ln_covid"
FE_MAIN <- "ID + unit^ym + dow"

## ---- (1) trip margin
m_trip <- feols(as.formula(paste0("trip ~ tbin + ", ctrl, " | ", FE_MAIN)),
                data = grid, cluster = ~Province, mem.clean = TRUE)
## ---- (2) daily spend
m_spend  <- feols(as.formula(paste0("spend ~ tbin + ", ctrl, " | ", FE_MAIN)),
                  data = grid, cluster = ~Province, mem.clean = TRUE)
m_spendp <- fepois(as.formula(paste0("spend ~ tbin + ", ctrl, " | ", FE_MAIN)),
                   data = grid, cluster = ~Province, mem.clean = TRUE)
logmsg("05: trip/spend done. trip R2 ", round(r2(m_trip, "r2"), 3))

grab <- function(m, model, outcome) {
  ct <- as.data.table(coeftable(m), keep.rownames = "term")
  setnames(ct, c("term","est","se","t","p"))
  ct[, `:=`(model = model, outcome = outcome, n = nobs(m))][]
}
res <- rbind(grab(m_trip, "lpm", "trip_any"), grab(m_spend, "lpm", "spend_day"),
             grab(m_spendp, "ppml", "spend_day"))
mean_dep <- grid[, .(trip_any = mean(trip), spend_day = mean(spend))]

## ---- (3) per-group outcomes on trip days
trips <- fread(file.path(DIR_INT, "trips_hh_day_cat.csv.gz"), encoding = "UTF-8")
trips[, date := as.IDate(date)]
gsp <- trips[, .(spend_g = sum(spend)), by = .(ID, date, food_group10)]
tripdays <- grid[trip == 1L, .(ID, date, Province, tier_a, unit, ym, dow, tbin, pbin,
                               holiday_flag, spring_festival_window_7, lockdown, ln_covid, spend)]
rm(grid); gc()

res_g <- list(); mean_g <- list()
for (g in G10) {
  dg <- merge(tripdays, gsp[food_group10 == g, .(ID, date, spend_g)],
              by = c("ID","date"), all.x = TRUE)
  dg[is.na(spend_g), spend_g := 0]
  dg[, buy_g := as.integer(spend_g > 0)]
  m1 <- feols(as.formula(paste0("buy_g ~ tbin + ", ctrl, " | ", FE_MAIN)),
              data = dg, cluster = ~Province, mem.clean = TRUE, notes = FALSE)
  m2 <- tryCatch(fepois(as.formula(paste0("spend_g ~ tbin + ", ctrl, " | ", FE_MAIN)),
                        data = dg, cluster = ~Province, mem.clean = TRUE, notes = FALSE),
                 error = function(e) NULL)
  res_g[[g]] <- rbind(grab(m1, "lpm", paste0("buy|trip_", g)),
                      if (!is.null(m2)) grab(m2, "ppml", paste0("spend|trip_", g)))
  mean_g[[g]] <- dg[, .(group = g, mean_buy = mean(buy_g), mean_spend = mean(spend_g))]
  rm(dg); gc()
  logmsg("05: group ", g, " done")
}
res <- rbind(res, rbindlist(res_g))
fwrite(res, file.path(DIR_TAB, "t1_main_coefs.csv"))
fwrite(rbindlist(mean_g), file.path(DIR_TAB, "t1_group_means.csv"))
fwrite(mean_dep, file.path(DIR_TAB, "t1_dep_means.csv"))

## ---- unit-level aggregate spec: WCB + permutation for headline coefficients
udc <- fread(file.path(DIR_INT, "unit_day_cat.csv.gz"), encoding = "UTF-8")
udc[, date := as.IDate(date)]
utot <- udc[, .(spend_pc = sum(spend_pc)), by = .(Province, tier_a, date, n_active)]
utot <- add_covariates(utot)
utot[, ln_spend_pc := log(spend_pc)]
f_u <- as.formula(paste0("ln_spend_pc ~ tbin + ", ctrl, " | unit^ym + dow"))
m_u <- feols(f_u, data = utot, cluster = ~Province, weights = ~n_active)

# permutation scheme: within each unit, permute the YEAR label of the daily
# temperature series (same calendar day, different year) -> preserves
# seasonality, breaks the true day-level link. 499 draws.
utot[, `:=`(yr = year(date), mo = month(date), md = mday(date))]
tkey <- utot[, .(unit, yr, mo, md, tbin0 = tbin)]
yrs <- sort(unique(utot$yr))
perm_fit <- function(s) {
  set.seed(s)
  pmap <- rbindlist(lapply(unique(utot$unit), function(u)
    data.table(unit = u, yr = yrs, yr_p = sample(yrs))))
  ut2 <- merge(utot, pmap, by = c("unit","yr"))
  ut2[, tbin_p := tkey[.(ut2$unit, ut2$yr_p, ut2$mo, ut2$md), on = .(unit, yr, mo, md), tbin0]]
  ut2[is.na(tbin_p), tbin_p := tbin]
  mp <- feols(as.formula(paste0("ln_spend_pc ~ tbin_p + ", ctrl, " | unit^ym + dow")),
              data = ut2, weights = ~n_active, notes = FALSE, warn = FALSE)
  coef(mp)
}
perm_mat <- sapply(1:499, perm_fit)

infr <- rbindlist(lapply(c("tbingt30", "tbinle0"), function(cc) {
  b0 <- coef(m_u)[cc]
  pc <- perm_mat[paste0("tbin_p", sub("tbin", "", cc)), ]
  data.table(term = cc, est = b0, se = se(m_u)[cc], p_cluster = pvalue(m_u)[cc],
             p_wcb = wcb_pvalue(m_u, cc, utot, cl_var = "Province", B = 399, wvar = "n_active"),
             p_perm = mean(abs(pc) >= abs(b0)))
}))
fwrite(infr, file.path(DIR_TAB, "t2_inference_triple.csv"))
logmsg("05: done. Triple inference:")
print(infr)
