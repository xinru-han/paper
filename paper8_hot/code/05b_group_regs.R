# Paper 8 script 05b (= plan 81, part 2): per-group outcomes on trip days
#   buy indicator (LPM) + conditional spend (PPML) per food group.
source("/root/data/Paper/央视数据/paper8-hot/code/00_setup.R")

hh   <- fread(file.path(DIR_INT, "hh_info.csv"), encoding = "UTF-8",
              select = c("ID","Province","tier_a"))
expo <- fread(file.path(DIR_INT, "province_tier_day_weather.csv.gz"), encoding = "UTF-8")
expo[, date := as.IDate(date)]
hol  <- fread(file.path(P1, "processed/calendar_holiday_2020_2022.csv"),
              select = c("date","holiday_flag","spring_festival_window_7"))
hol[, date := as.IDate(date)]
cov  <- fread(file.path(P1, "processed/covid_province_daily_2020_2022.csv"), encoding = "UTF-8")
cov[, date := as.IDate(date)]
lkd  <- fread(file.path(DIR_LKP, "lockdown_windows.csv"), encoding = "UTF-8")

trips <- fread(file.path(DIR_INT, "trips_hh_day_cat.csv.gz"), encoding = "UTF-8")
trips[, date := as.IDate(date)]
if (DEBUG) trips <- trips[ID %% 20L == 0L]
gsp <- trips[, .(spend_g = sum(spend)), by = .(ID, date, food_group10)]
td <- trips[, .(spend = sum(spend)), by = .(ID, date)]     # trip days
rm(trips); gc()
td <- merge(td, hh, by = "ID")
td <- merge(td, expo[, .(Province = province, tier_a, date, tbin, pbin)],
            by = c("Province","tier_a","date"))
td <- merge(td, hol, by = "date")
td <- merge(td, cov[, .(Province = province, date, covid_daily_new)],
            by = c("Province","date"), all.x = TRUE)
td[is.na(covid_daily_new), covid_daily_new := 0][, ln_covid := log1p(covid_daily_new)]
td[, lockdown := 0L]
for (i in seq_len(nrow(lkd)))
  td[Province == lkd$province[i] & (lkd$city[i] == "上海" | tier_a == 1L) &
       date %between% c(lkd$start[i], lkd$end[i]), lockdown := 1L]
td[, fe_uym := as.integer(factor(paste0(Province, tier_a, format(date, "%y%m"))))]
td[, dow := as.integer(wday(date))]
td[, prov_id := as.integer(factor(Province))]
logmsg("05b: ", nrow(td), " trip days")

grab <- function(m, model, outcome) {
  ct <- as.data.table(coeftable(m), keep.rownames = "term")
  setnames(ct, c("term","est","se","t","p"))
  ct[, `:=`(model = model, outcome = outcome, n = nobs(m))][]
}
ctrl <- "pbin + holiday_flag + spring_festival_window_7 + lockdown + ln_covid"
res_g <- list(); mean_g <- list()
for (g in G10) {
  dg <- merge(td, gsp[food_group10 == g, .(ID, date, spend_g)], by = c("ID","date"), all.x = TRUE)
  dg[is.na(spend_g), spend_g := 0]
  dg[, buy_g := as.integer(spend_g > 0)]
  m1 <- feols(as.formula(paste0("buy_g ~ tbin + ", ctrl, " | ID + fe_uym + dow")),
              data = dg, cluster = ~prov_id, mem.clean = TRUE, notes = FALSE)
  m2 <- tryCatch(fepois(as.formula(paste0("spend_g ~ tbin + ", ctrl, " | ID + fe_uym + dow")),
                        data = dg, cluster = ~prov_id, mem.clean = TRUE, notes = FALSE),
                 error = function(e) { logmsg("05b: PPML failed for ", g, ": ", conditionMessage(e)); NULL })
  res_g[[g]] <- rbind(grab(m1, "lpm", paste0("buy|trip_", g)),
                      if (!is.null(m2)) grab(m2, "ppml", paste0("spend|trip_", g)))
  mean_g[[g]] <- dg[, .(group = g, mean_buy = mean(buy_g), mean_spend = mean(spend_g))]
  rm(dg, m1, m2); gc()
  logmsg("05b: ", g, " done")
}
fwrite(rbindlist(res_g), file.path(DIR_TAB, "t1b_group_coefs.csv"))
fwrite(rbindlist(mean_g), file.path(DIR_TAB, "t1_group_means.csv"))
combine_t1(DIR_TAB)
logmsg("05b: done")
