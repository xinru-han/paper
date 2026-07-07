# Paper 8 script 12 (= plan 88): robustness, on the unit-level aggregate spec
#  R1 Tier-A-only (exact weather matching)     R2 drop lockdown unit-days
#  R3 tmax bins instead of tavg                R4 unit^woy FE / IHS outcome
#  R5 placebo: previous-year same-day temp     R6 2021 only (calm COVID year)
source("/root/data/Paper/央视数据/paper8-hot/code/00_setup.R")

utot <- readRDS(file.path(DIR_INT, "utot_frame.rds"))
expo <- fread(file.path(DIR_INT, "province_tier_day_weather.csv.gz"), encoding = "UTF-8")
expo[, date := as.IDate(date)]
utot <- merge(utot, expo[, .(Province = province, tier_a, date, tmax)], by = c("Province","tier_a","date"))
utot[, `:=`(tbin_max = tbin_cut(tmax - 5),   # tmax runs ~5C above tavg; same grid
            ihs = asinh(spend_pc), woy = pmin(isoweek(date), 52L))]
# placebo: previous-year same calendar day tbin
pl <- expo[, .(Province = province, tier_a, date = date + 365L, tbin_lag = tbin_cut(tavg))]
utot <- merge(utot, pl, by = c("Province","tier_a","date"), all.x = TRUE)

ctrl <- "pbin + holiday_flag + spring_festival_window_7 + lockdown + ln_covid"
runs <- list(
  main   = list(d = quote(utot), f = paste0("ln_spend_pc ~ tbin + ", ctrl, " | unit^ym + dow")),
  R1_tierA = list(d = quote(utot[tier_a == 1L]), f = paste0("ln_spend_pc ~ tbin + ", ctrl, " | unit^ym + dow")),
  R2_no_lockdown = list(d = quote(utot[lockdown == 0L]), f = paste0("ln_spend_pc ~ tbin + pbin + holiday_flag + spring_festival_window_7 + ln_covid | unit^ym + dow")),
  R3_tmax = list(d = quote(utot), f = paste0("ln_spend_pc ~ tbin_max + ", ctrl, " | unit^ym + dow")),
  R4_woyFE = list(d = quote(utot), f = paste0("ln_spend_pc ~ tbin + ", ctrl, " | unit^woy + unit^yr + dow")),
  R4_ihs = list(d = quote(utot), f = paste0("ihs ~ tbin + ", ctrl, " | unit^ym + dow")),
  R5_placebo = list(d = quote(utot[!is.na(tbin_lag)]), f = paste0("ln_spend_pc ~ tbin_lag + tbin + ", ctrl, " | unit^ym + dow")),
  R6_2021 = list(d = quote(utot[yr == 2021L]), f = paste0("ln_spend_pc ~ tbin + ", ctrl, " | unit^ym + dow"))
)
res <- rbindlist(lapply(names(runs), function(r) {
  m <- feols(as.formula(runs[[r]]$f), data = eval(runs[[r]]$d),
             cluster = ~Province, weights = ~n_active, notes = FALSE)
  ct <- as.data.table(coeftable(m), keep.rownames = "term")
  setnames(ct, c("term","est","se","t","p"))
  ct[grepl("tbin", term)][, `:=`(spec = r, n = nobs(m))]
}))
fwrite(res, file.path(DIR_TAB, "t16_robustness.csv"))
logmsg("12: robustness done")
print(dcast(res[grepl("gt30", term)], spec ~ term, value.var = "est"))
