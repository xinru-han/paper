# Paper 8 script 02 (= plan 80a products): weather library
#  (1) climate normals 1981-2010 per city (week-of-year mean/sd, hot/cold days)
#  (2) household exposure series 2019-2023: province x {capital, non-capital mean}
#  (3) scenario inputs: per-city daily tavg frequency table 1994-2023 (0.5C grid)
#      + 1973-2023 trend in hot days
# Requires: 01_weather_parse.py output in data/interim/weather_years/
source("/root/data/Paper/央视数据/paper8-hot/code/00_setup.R")

wdir <- file.path(DIR_INT, "weather_years")
read_years <- function(years, cols = c("city_code","date","tavg","tmax","tmin","precip","province","city")) {
  fl <- file.path(wdir, sprintf("city_day_weather_%d.csv", years))
  fl <- fl[file.exists(fl)]
  rbindlist(lapply(fl, fread, select = cols, encoding = "UTF-8"))
}

## ---- (1) normals 1981-2010
w <- read_years(1981:2010, cols = c("city_code","date","tavg","province","city"))
w[, date := as.IDate(date)][, `:=`(woy = pmin(isoweek(date), 52L), yr = year(date))]
norm_woy <- w[is.finite(tavg), .(tavg_norm = mean(tavg), tavg_norm_sd = sd(tavg)), by = .(city_code, province, city, woy)]
norm_yr <- w[is.finite(tavg), .(d_gt30 = sum(tavg > 30), d_le0 = sum(tavg <= 0), tavg_yr = mean(tavg)), by = .(city_code, yr)][
  , .(norm_days_gt30 = mean(d_gt30), norm_days_le0 = mean(d_le0), tavg_annual_norm = mean(tavg_yr)), by = city_code]
fwrite(norm_woy, file.path(DIR_LKP, "climate_normal_woy.csv.gz"))
fwrite(norm_yr, file.path(DIR_LKP, "climate_normal_annual.csv.gz"))
logmsg("02: normals built (", uniqueN(norm_yr$city_code), " cities)")
rm(w); gc()

## ---- (2) exposure series 2019-2023
capmap <- fread(file.path(P1, "processed/capital_city_weather_mapping.csv"), encoding = "UTF-8")
capmap <- capmap[, .(province = Province, capital = matched_city)]

w <- read_years(2019:2023)
w[, date := as.IDate(date)]
w <- merge(w, capmap, by = "province")  # sample provinces only
w[, is_cap := city == capital]
expo_cap <- w[is_cap == TRUE, .(tavg = mean(tavg, na.rm=TRUE), tmax = mean(tmax, na.rm=TRUE),
                                precip = mean(precip, na.rm=TRUE)), by = .(province, date)][, tier_a := 1L]
expo_non <- w[is_cap == FALSE, .(tavg = mean(tavg, na.rm=TRUE), tmax = mean(tmax, na.rm=TRUE),
                                 precip = mean(precip, na.rm=TRUE)), by = .(province, date)][, tier_a := 0L]
# municipalities have no non-capital cities -> use capital series
mun <- setdiff(unique(expo_cap$province), unique(expo_non$province))
if (length(mun)) expo_non <- rbind(expo_non, copy(expo_cap[province %in% mun])[, tier_a := 0L])
expo <- rbind(expo_cap, expo_non)
expo[, `:=`(tbin = tbin_cut(tavg), pbin = pbin_cut(precip))]
fwrite(expo, file.path(DIR_INT, "province_tier_day_weather.csv.gz"))
logmsg("02: exposure series ", nrow(expo), " rows, ", uniqueN(expo$province), " provinces, ",
       expo[, sum(is.na(tavg))], " missing tavg")

## ---- (3) scenario inputs
w <- read_years(1994:2023, cols = c("city_code","date","tavg","province","city"))
w <- w[is.finite(tavg)]
w[, t05 := round(tavg * 2) / 2]
freq <- w[, .N, by = .(city_code, province, city, t05)]
fwrite(freq, file.path(DIR_LKP, "city_tavg_freq_1994_2023.csv.gz"))
# hot-day trend 1973-2023
rm(w); gc()
w <- read_years(1973:2023, cols = c("city_code","date","tavg"))
w[, yr := year(as.IDate(date))]
trend <- w[is.finite(tavg), .(days_gt30 = sum(tavg > 30)), by = .(city_code, yr)]
fwrite(trend, file.path(DIR_LKP, "city_hotdays_by_year.csv.gz"))
logmsg("02: scenario inputs written")
