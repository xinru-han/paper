# Paper 8 script 05a (= plan 81, part 1): hh x day grid regressions, memory-lean
#   trip (any purchase) and daily spend LPM with household + unit^ym + dow FE.
# Note: hh-level daily-spend PPML dropped for memory (unit-level ln spend in 05c
#   and group-level PPML in 05b cover the semi-elasticity readings).
source("/root/data/Paper/央视数据/paper8-hot/code/00_setup.R")

hh   <- fread(file.path(DIR_INT, "hh_info.csv"), encoding = "UTF-8",
              select = c("ID","Province","CityTier","tier_a"))
expo <- fread(file.path(DIR_INT, "province_tier_day_weather.csv.gz"), encoding = "UTF-8")
expo[, date := as.IDate(date)]
hol  <- fread(file.path(P1, "processed/calendar_holiday_2020_2022.csv"),
              select = c("date","holiday_flag","spring_festival_window_7"))
hol[, date := as.IDate(date)]
cov  <- fread(file.path(P1, "processed/covid_province_daily_2020_2022.csv"), encoding = "UTF-8")
cov[, date := as.IDate(date)]
lkd  <- fread(file.path(DIR_LKP, "lockdown_windows.csv"), encoding = "UTF-8")

grid <- readRDS(file.path(DIR_INT, "panel_hh_day.rds"))
if (DEBUG) grid <- grid[ID %% 20L == 0L]
grid <- merge(grid, hh, by = "ID")
grid[, date := as.IDate(day_i, origin = "1970-01-01")]
grid <- merge(grid, expo[, .(Province = province, tier_a, date, tbin, pbin)],
              by = c("Province","tier_a","date"))
grid <- merge(grid, hol, by = "date")
grid <- merge(grid, cov[, .(Province = province, date, covid_daily_new)],
              by = c("Province","date"), all.x = TRUE)
grid[is.na(covid_daily_new), covid_daily_new := 0][, ln_covid := log1p(covid_daily_new)]
grid[, covid_daily_new := NULL]
grid[, lockdown := 0L]
for (i in seq_len(nrow(lkd)))
  grid[Province == lkd$province[i] & (lkd$city[i] == "上海" | tier_a == 1L) &
         date %between% c(lkd$start[i], lkd$end[i]), lockdown := 1L]
# lean types: single combined FE id + integer dow + province id for cluster
grid[, fe_uym := as.integer(factor(paste0(Province, tier_a, format(date, "%y%m"))))]
grid[, dow := as.integer(wday(date))]
grid[, prov_id := as.integer(factor(Province))]
grid[, c("Province","CityTier","date","day_i","tier_a") := NULL]
gc()
logmsg("05a: frame ready ", nrow(grid), " rows, ", ncol(grid), " cols")

ctrl <- "pbin + holiday_flag + spring_festival_window_7 + lockdown + ln_covid"
m_trip <- feols(as.formula(paste0("trip ~ tbin + ", ctrl, " | ID + fe_uym + dow")),
                data = grid, cluster = ~prov_id, mem.clean = TRUE, notes = FALSE)
grab <- function(m, model, outcome) {
  ct <- as.data.table(coeftable(m), keep.rownames = "term")
  setnames(ct, c("term","est","se","t","p"))
  ct[, `:=`(model = model, outcome = outcome, n = nobs(m))][]
}
r1 <- grab(m_trip, "lpm", "trip_any")
rm(m_trip); gc()
logmsg("05a: trip done")
m_spend <- feols(as.formula(paste0("spend ~ tbin + ", ctrl, " | ID + fe_uym + dow")),
                 data = grid, cluster = ~prov_id, mem.clean = TRUE, notes = FALSE)
r2 <- grab(m_spend, "lpm", "spend_day")
fwrite(rbind(r1, r2), file.path(DIR_TAB, "t1a_grid_coefs.csv"))
fwrite(grid[, .(trip_any = mean(trip), spend_day = mean(spend))],
       file.path(DIR_TAB, "t1_dep_means.csv"))
rm(m_spend); gc()
combine_t1(DIR_TAB)
logmsg("05a: done")
