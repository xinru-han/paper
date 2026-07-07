# Paper 8 script 08 (= plan 84): adaptation
#  (a) cross-sectional: hot-day response x climate-normal hot days of the unit
#  (b) within-season acclimatization: response to the k-th hot day of the year
# Estimated on the exposure-unit x day aggregate (identical exposure variation).
source("/root/data/Paper/央视数据/paper8-hot/code/00_setup.R")

udc  <- fread(file.path(DIR_INT, "unit_day_cat.csv.gz"), encoding = "UTF-8")
udc[, date := as.IDate(date)]
utot <- udc[, .(spend_pc = sum(spend_pc)), by = .(Province, tier_a, date, n_active)]

expo <- fread(file.path(DIR_INT, "province_tier_day_weather.csv.gz"), encoding = "UTF-8")
expo[, date := as.IDate(date)]
hol  <- fread(file.path(P1, "processed/calendar_holiday_2020_2022.csv"))
hol[, date := as.IDate(date)]
cov  <- fread(file.path(P1, "processed/covid_province_daily_2020_2022.csv"), encoding = "UTF-8")
cov[, date := as.IDate(date)]
lkd  <- fread(file.path(DIR_LKP, "lockdown_windows.csv"), encoding = "UTF-8")

utot <- merge(utot, expo[, .(Province = province, tier_a, date, tavg, tbin, pbin)], by = c("Province","tier_a","date"))
utot <- merge(utot, hol[, .(date, holiday_flag, spring_festival_window_7)], by = "date")
utot <- merge(utot, cov[, .(Province = province, date, covid_daily_new)], by = c("Province","date"), all.x = TRUE)
utot[is.na(covid_daily_new), covid_daily_new := 0][, ln_covid := log1p(covid_daily_new)]
utot[, lockdown := 0L]
for (i in seq_len(nrow(lkd)))
  utot[Province == lkd$province[i] & (lkd$city[i] == "上海" | tier_a == 1L) &
         date %between% c(lkd$start[i], lkd$end[i]), lockdown := 1L]
utot[, `:=`(unit = paste0(Province, "_", tier_a), ym = format(date, "%Y-%m"),
            dow = wday(date), yr = year(date), ln_spend_pc = log(spend_pc),
            hot = as.integer(tbin == "gt30"))]

## climate normal per unit: capital city normals (tier A) / non-capital mean
capmap <- fread(file.path(P1, "processed/capital_city_weather_mapping.csv"), encoding = "UTF-8")
norm_a <- fread(file.path(DIR_LKP, "climate_normal_annual.csv.gz"))
wmeta <- unique(fread(file.path(DIR_INT, "weather_years/city_day_weather_2021.csv"),
                      select = c("city_code","province","city"), encoding = "UTF-8"))
norm_a <- merge(norm_a, wmeta, by = "city_code")
norm_a <- merge(norm_a, capmap[, .(province = Province, capital = matched_city)], by = "province")
unorm <- rbind(
  norm_a[city == capital, .(norm_gt30 = mean(norm_days_gt30)), by = province][, tier_a := 1L],
  norm_a[city != capital, .(norm_gt30 = mean(norm_days_gt30)), by = province][, tier_a := 0L])
mun <- setdiff(unorm[tier_a == 1, province], unorm[tier_a == 0, province])
if (length(mun)) unorm <- rbind(unorm, copy(unorm[tier_a == 1 & province %in% mun])[, tier_a := 0L])
utot <- merge(utot, unorm, by.x = c("Province","tier_a"), by.y = c("province","tier_a"))
utot[, norm_gt30_std := (norm_gt30 - mean(norm_gt30)) / sd(norm_gt30)]

ctrl <- "pbin + holiday_flag + spring_festival_window_7 + lockdown + ln_covid"

## (a) cross-sectional adaptation
m_a <- feols(as.formula(paste0("ln_spend_pc ~ hot * norm_gt30_std + tbin + ", ctrl, " | unit^ym + dow")),
             data = utot, cluster = ~Province, weights = ~n_active, notes = FALSE)

## (b) acclimatization: rank of the hot day within unit x year
setorder(utot, unit, date)
utot[, hot_rank := cumsum(hot), by = .(unit, yr)]
utot[, hot_phase := fcase(hot == 0L, "none",
                          hot_rank <= 5, "hot_1_5",
                          hot_rank <= 15, "hot_6_15",
                          default = "hot_16p")]
utot[, hot_phase := factor(hot_phase, levels = c("none","hot_1_5","hot_6_15","hot_16p"))]
m_b <- feols(as.formula(paste0("ln_spend_pc ~ hot_phase + i(tbin, ref='ref18_24', keep='le0|b0_6|b6_12|b24_30') + ",
                               ctrl, " | unit^ym + dow")),
             data = utot, cluster = ~Province, weights = ~n_active, notes = FALSE)

grab <- function(m, tag) {
  ct <- as.data.table(coeftable(m), keep.rownames = "term")
  setnames(ct, c("term","est","se","t","p")); ct[, model := tag][]
}
out <- rbind(grab(m_a, "cross_sectional"), grab(m_b, "acclimatization"))
fwrite(out, file.path(DIR_TAB, "t7_adaptation.csv"))
saveRDS(utot, file.path(DIR_INT, "utot_frame.rds"))  # reused by 09/11/12
logmsg("08: adaptation done")
print(out[grepl("hot", term)])
