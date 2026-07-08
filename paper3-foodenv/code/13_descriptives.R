# =============================================================================
# 13_descriptives.R — T1: sample & village food environment by detour quartile.
# =============================================================================
source("/root/data/Paper/食物消费数据/paper3-foodenv/code/00_setup.R")
con <- log_open("13_descriptives.log")

vg <- fread(file.path(DIR_DERIV, "p3_village.csv"), colClasses = list(character = "xzc12"))
pers <- fread(file.path(DIR_DERIV, "p3_person.csv"), colClasses = list(character = c("xzc12","nhCode")))

vg[, dq := cut(detour_town_5km, quantile(detour_town_5km, 0:4/4, na.rm = TRUE),
               include.lowest = TRUE, labels = paste0("Q", 1:4))]
t1v <- vg[!is.na(dq), .(
  n_villages = .N,
  poi_grocery = mean(poi_grocery_5km), poi_fresh = mean(poi_fresh_5km),
  poi_meat = mean(poi_meat_5km), poi_restaurant = mean(poi_restaurant_5km),
  vs_super = mean(vs_super_5km, na.rm = TRUE), vs_market = mean(vs_market_5km, na.rm = TRUE),
  dist_town_km = mean(dist_town_5km, na.rm = TRUE), dist_county_km = mean(dist_county_5km, na.rm = TRUE),
  nearest_outlet_km = mean(fe03_min, na.rm = TRUE),
  elevation_m = mean(elevation_mean, na.rm = TRUE), slope_deg = mean(slope_mean, na.rm = TRUE),
  population = mean(vpop, na.rm = TRUE)), by = dq][order(dq)]
wtab(t1v, "t1_village_by_detour_quartile.csv")

pm <- merge(pers, vg[, .(xzc12, dq)], by = "xzc12")
t1p <- pm[!is.na(dq), .(
  n_recalls = .N, fgds10 = mean(fgds10, na.rm = TRUE), fvs = mean(fvs, na.rm = TRUE),
  hdds12 = mean(hdds12, na.rm = TRUE), mddw_rate = mean(mddw[mddw_elig == 1], na.rm = TRUE),
  income = mean(exp(ln_income) - 1, na.rm = TRUE),
  self_suff = mean(food_ssr_w, na.rm = TRUE),
  fridge = mean(hb_fridge, na.rm = TRUE), vehicle = mean(hb_vehicle, na.rm = TRUE)), by = dq][order(dq)]
wtab(t1p, "t1b_person_by_detour_quartile.csv")
print(t1v, digits = 3); print(t1p, digits = 3)
log_close(con)
