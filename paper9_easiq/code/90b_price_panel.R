# Paper 9 script 90b: market base prices + household-month panel assembly.
#  Base price p_base (province x month x category):
#   - OBS7: monthly mean of genuinely observed monitor prices
#   - other 6 PK13: province x month MEDIAN unit value across households
#     (proxy fills in the P1 file just copy 常温牛奶's series -> unusable)
#   - composite fresh good: Stone log-price over 8 observed fresh categories,
#     fixed national expenditure weights
source("/root/data/Paper/央视数据/paper9-easiq/code/00_setup.R")

## ---- monitor prices, monthly
pr <- fread(file.path(P1, "processed/external_food_prices_category_province_monitor_date_cleaned_2020_2022.csv"),
            encoding = "UTF-8")
pr[, ym := substr(date, 1, 7)]
obs <- pr[price_fill_level == "observed_province_monitor_date",
          .(p_mon = mean(external_price_mean_monitor, na.rm = TRUE)),
          by = .(Province = province, ym, Category)]

## ---- uv-based base price for the 6 non-observed PK13 categories
uvm <- fread(file.path(DIR_INT, "uv_hh_month_cat.csv.gz"), encoding = "UTF-8")
attr9 <- fread(file.path(DIR_INT, "hhm_attr.csv.gz"), encoding = "UTF-8")
uvm <- merge(uvm, attr9[, .(ID, ym, Province)], by = c("ID","ym"))
uvbase <- uvm[, .(p_uvmed = median(uv), n_cell = .N), by = .(Province, ym, Category)]

NONOBS6 <- setdiff(PK13, OBS7)
pb <- rbind(
  obs[Category %in% OBS7, .(Province, ym, Category, p_base = p_mon, src = "monitor")],
  uvbase[Category %in% NONOBS6 & n_cell >= 5,
         .(Province, ym, Category, p_base = p_uvmed, src = "uv_median")]
)
## fill sparse uv-median cells with province-level all-month median (rare)
gridp <- CJ(Province = unique(attr9$Province), ym = sort(unique(attr9$ym)), Category = PK13, unique = TRUE)
pb <- merge(gridp, pb, by = c("Province","ym","Category"), all.x = TRUE)
pb[, p_fill := median(p_base, na.rm = TRUE), by = .(Province, Category)]
pb[is.na(p_base), `:=`(p_base = p_fill, src = "prov_median_fill")]
pb[, p_fill := NULL]
logmsg("90b: base price fill shares: ", pb[, paste0(names(table(src)), "=", table(src), collapse = ", ")])

## ---- composite fresh Stone price (national expenditure weights over FRESH8)
frw <- fread(file.path(RAW, "Data_merged.csv"), encoding = "UTF-8",
             select = c("Category","Spend"))[Category %in% FRESH8,
             .(s = sum(Spend)), by = Category][, s := s / sum(s)]
comp <- obs[Category %in% FRESH8]
comp <- merge(comp, frw, by = "Category")
comp <- comp[, .(Category = COMP, p_base = exp(sum(s * log(p_mon)) / sum(s)), src = "stone"),
             by = .(Province, ym)]
pball <- rbind(pb, comp[, .(Province, ym, Category, p_base, src)])
fwrite(pball, file.path(DIR_INT, "base_price_prov_month.csv.gz"))

## lnP wide (province x ym), demeaned within category (units/levels absorbed)
pball[, lnp := log(p_base)][, lnp_dm := lnp - mean(lnp), by = Category]
lnPw <- dcast(pball, Province + ym ~ Category, value.var = "lnp_dm")
setnames(lnPw, old = G14, new = paste0("lnp_", seq_along(G14)))  # positional names, order G14
fwrite(lnPw, file.path(DIR_INT, "lnP_wide.csv.gz"))

## ---- shocks at province x month
lkd <- fread(file.path(P8, "data/lookups/lockdown_windows.csv"), encoding = "UTF-8")
lkdm <- rbindlist(lapply(seq_len(nrow(lkd)), function(i) {
  dd <- data.table(date = seq(as.IDate(lkd$start[i]), as.IDate(lkd$end[i]), by = "1 day"))
  dd[, Province := lkd$province[i]][, ym := format(date, "%Y-%m")]
  dd[, .(lock_days = .N), by = .(Province, ym)]
}))[, .(lock_days = sum(lock_days)), by = .(Province, ym)]
cov <- fread(file.path(P1, "processed/covid_province_daily_2020_2022.csv"), encoding = "UTF-8")
covm <- cov[, .(covid_m = sum(covid_daily_new)), by = .(Province = province, ym = substr(date, 1, 7))]
hol <- fread(file.path(P1, "processed/calendar_holiday_2020_2022.csv"))
cny <- hol[, .(cny_share = mean(spring_festival_window_7)), by = .(ym = substr(date, 1, 7))]
expo <- fread(file.path(P8, "data/interim/province_tier_day_weather.csv.gz"), encoding = "UTF-8")
hotm <- expo[, .(hot_days = sum(tavg > 30)), by = .(Province = province, tier_a, ym = substr(date, 1, 7))]

## ---- assemble hh x month main panel
bud <- fread(file.path(DIR_INT, "hhm_budget.csv.gz"), encoding = "UTF-8")
pan <- merge(bud, attr9, by = c("ID","ym"))
pan <- merge(pan, lnPw, by = c("Province","ym"))
pan <- merge(pan, lkdm, by = c("Province","ym"), all.x = TRUE)
pan[is.na(lock_days), lock_days := 0]
pan <- merge(pan, covm, by = c("Province","ym"), all.x = TRUE)
pan[is.na(covid_m), covid_m := 0][, ln_covid := log1p(covid_m)]
pan <- merge(pan, cny, by = "ym")
pan <- merge(pan, hotm, by = c("Province","tier_a","ym"), all.x = TRUE)
pan[is.na(hot_days), hot_days := 0]
pan[, `:=`(ln_x = log(x), ln_inc = log(inc_mid), inv_inc = 1 / inc_mid,
           mo = substr(ym, 6, 7), prov_tier = paste0(Province, "_", tier_a),
           elderly = as.integer(grepl("老年", fam_type)))]
## shares of the 14 goods
for (j in seq_along(G14)) {
  gcol <- G14[j]
  if (!gcol %in% names(pan)) pan[, (gcol) := 0]
  pan[, (paste0("w_", j)) := get(gcol) / x]
}
saveRDS(pan, file.path(DIR_INT, "panel_hhm.rds"))
logmsg("90b: main panel ", nrow(pan), " hh-months, ", uniqueN(pan$ID), " households")

## ---- quality panel: r_prem = ln uv - ln p_base
qd <- merge(uvm, pball[Category %in% PK13, .(Province, ym, Category, p_base)],
            by = c("Province","ym","Category"))
qd[, `:=`(r_prem = log(uv) - log(p_base), lnQ = log(Q), lnX = log(X))]
qd <- merge(qd, pan[, .(ID, ym, ln_x, ln_inc, inv_inc, fsize, elderly, CityTier,
                        tier_a, prov_tier, mo, lock_days, ln_covid, cny_share, hot_days,
                        x)], by = c("ID","ym"))
saveRDS(qd, file.path(DIR_INT, "quality_panel.rds"))
logmsg("90b: quality panel ", nrow(qd), " hh-month-cat rows; r_prem sd = ",
       round(sd(qd$r_prem), 3))
