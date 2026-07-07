# Paper 8 script 09 (= plan 85): displacement vs forgone purchases
# Distributed lags 0..14 of the hot-day (and cold-day) indicator on
# unit x day x group per-capita spend; cumulative effects by perishability.
source("/root/data/Paper/央视数据/paper8-hot/code/00_setup.R")

udc <- fread(file.path(DIR_INT, "unit_day_cat.csv.gz"), encoding = "UTF-8")
udc[, date := as.IDate(date)]
utot <- readRDS(file.path(DIR_INT, "utot_frame.rds"))  # has hot/cold/tbin/controls

# complete unit x date x group grid (zeros where nothing bought)
base <- utot[, .(Province, tier_a, unit, date, n_active, tbin, pbin, holiday_flag,
                 spring_festival_window_7, lockdown, ln_covid, ym, dow, hot)]
base[, cold := as.integer(tbin == "le0")]
gridg <- base[, .(food_group10 = G10), by = names(base)]
gridg <- merge(gridg, udc[, .(Province, tier_a, date, food_group10, spend_pc)],
               by = c("Province","tier_a","date","food_group10"), all.x = TRUE)
gridg[is.na(spend_pc), spend_pc := 0]
gridg[, ug := paste0(unit, "_", food_group10)]
setorder(gridg, ug, date)

LAGS <- 0:14
for (k in LAGS) gridg[, paste0("hot_l", k) := shift(hot, k), by = ug]
for (k in LAGS) gridg[, paste0("cold_l", k) := shift(cold, k), by = ug]

ctrl <- "pbin + holiday_flag + spring_festival_window_7 + lockdown + ln_covid"
res <- list()
for (g in G10) {
  f <- as.formula(paste0("spend_pc ~ ", paste0("hot_l", LAGS, collapse = " + "), " + ",
                         paste0("cold_l", LAGS, collapse = " + "), " + ", ctrl,
                         " | unit^ym + dow"))
  m <- feols(f, data = gridg[food_group10 == g], cluster = ~Province,
             weights = ~n_active, notes = FALSE)
  ct <- as.data.table(coeftable(m), keep.rownames = "term")
  setnames(ct, c("term","est","se","t","p"))
  # cumulative 0..14 with delta-method SE
  V <- vcov(m)
  for (shock in c("hot","cold")) {
    nm <- paste0(shock, "_l", LAGS)
    nm <- nm[nm %in% names(coef(m))]
    csum <- sum(coef(m)[nm])
    cse  <- sqrt(sum(V[nm, nm]))
    ct <- rbind(ct, data.table(term = paste0(shock, "_cum14"), est = csum, se = cse,
                               t = csum/cse, p = 2*pnorm(-abs(csum/cse))))
  }
  res[[g]] <- ct[, group := g]
  logmsg("09: ", g, " cum14(hot) = ", round(ct[term == "hot_cum14", est], 4))
}
res <- rbindlist(res)
mean_spc <- gridg[, .(mean_spend_pc = mean(spend_pc)), by = food_group10]
fwrite(res, file.path(DIR_TAB, "t8_displacement_lags.csv"))
fwrite(mean_spc, file.path(DIR_TAB, "t8_group_spc_means.csv"))
logmsg("09: done")
