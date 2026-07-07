# Paper 8 script 11 (= plan 87): post-estimation
#  (a) warming scenarios (+1.5C / +3C uniform shift of the 1994-2023 daily
#      distribution per city) -> change in expected days per temperature bin ->
#      projected annual change in trips, group spend, protein, by province,
#      under no / full / cross-sectional adaptation
#  (b) welfare: first-order cost-of-living effect of the price channel +
#      demand-channel consumption displacement valued at baseline prices
#  (c) carbon feedback: diet-composition shift x emission factors
#  (d) policy: cold-chain counterfactual + elderly targeting efficiency
source("/root/data/Paper/央视数据/paper8-hot/code/00_setup.R")

## ---- scenario bin-day changes per province (city freq -> province mean)
freq <- fread(file.path(DIR_LKP, "city_tavg_freq_1994_2023.csv.gz"), encoding = "UTF-8")
bin_days <- function(shift = 0) {
  f <- copy(freq)[, t := t05 + shift][, bin := tbin_cut(t)]
  f[, .(days = sum(N) / 30), by = .(province, city_code, bin)][   # per year
    , .(days = mean(days)), by = .(province, bin)]                # province mean over cities
}
sc <- rbindlist(list(
  bin_days(0)[, scen := "base"],
  bin_days(1.5)[, scen := "p15"],
  bin_days(3.0)[, scen := "p30"]))
scw <- dcast(sc, province + bin ~ scen, value.var = "days", fill = 0)
scw[, `:=`(d15 = p15 - base, d30 = p30 - base)]
fwrite(scw, file.path(DIR_TAB, "t11_scenario_bin_days.csv"))

## ---- (a) projections
main <- fread(file.path(DIR_TAB, "t1_main_coefs.csv"))
adapt <- fread(file.path(DIR_TAB, "t7_adaptation.csv"))
bins <- setdiff(TBIN_LABELS, TBIN_REF)
bcoef <- function(outc, mod) sapply(bins, function(b)
  { v <- main[outcome == outc & model == mod & term == paste0("tbin", b), est]; if (length(v)) v[1] else 0 })

b_trip <- bcoef("trip_any", "lpm")
nutc <- fread(file.path(DIR_TAB, "t9_nutrient_response.csv"))
b_prot <- sapply(bins, function(b) { v <- nutc[outcome == "prot_pc" & term == paste0("tbin", b), est]; if (length(v)) v[1] else 0 })
# cross-sectional adaptation: hot x norm interaction attenuates gt30 coef by
# delta per 1 SD of normal hot days; "adapted" = +1 SD acclimatized population
att <- adapt[model == "cross_sectional" & term == "hot:norm_gt30_std", est]
if (length(att) == 0) att <- 0

proj <- rbindlist(lapply(unique(scw$province), function(p) {
  d <- scw[province == p]
  dd <- function(col) sapply(bins, function(b) { v <- d[bin == b][[col]]; if (length(v)) v else 0 })
  rbindlist(lapply(c("d15","d30"), function(s) {
    ddays <- dd(s)
    adj <- function(bv, mode) {
      b2 <- bv
      if (mode == "adapted") b2["gt30"] <- bv["gt30"] + att * 1
      if (mode == "full")    b2["gt30"] <- 0
      b2
    }
    rbindlist(lapply(c("none","adapted","full"), function(md) data.table(
      province = p, scen = s, adaptation = md,
      d_trips_yr   = sum(adj(b_trip, md) * ddays),
      d_lnprot_days = sum(adj(b_prot, md) * ddays)   # sum of daily log effects
    )))
  }))
}))
# protein loss in % of annual purchases: mean daily log-effect x days / 365
proj[, prot_pct_yr := 100 * d_lnprot_days / 365]
fwrite(proj, file.path(DIR_TAB, "t12_projection_province.csv"))
logmsg("11: projections done; national mean prot change (+3C, none): ",
       round(proj[scen == "d30" & adaptation == "none", mean(prot_pct_yr)], 3), "% per yr")

## ---- (b) welfare
dec <- fread(file.path(DIR_TAB, "t4_channel_decomposition.csv"))
elz <- readRDS(file.path(DIR_INT, "elasticity_repaired.rds"))
hh <- fread(file.path(DIR_INT, "hh_info.csv"), encoding = "UTF-8")
# annual food spend per household (observed window scaled to 365 days)
hh[, ann_spend := total_spend / pmax(as.numeric(last_date - first_date) + 1, 30) * 365]
ann_sp <- hh[, mean(ann_spend)]
w <- elz$w
hot_days_now <- scw[, .(base = sum(base * (bin == "gt30"))), by = province][, mean(base)]
wel <- rbindlist(lapply(c("d15","d30"), function(s) {
  dhot <- scw[bin == "gt30", mean(get(s))]
  gam <- dec[bin == "gt30", price_gamma]; names(gam) <- dec[bin == "gt30", group]
  dch <- dec[bin == "gt30", demand_channel]
  col_per_hotday <- sum(w * gam[G10])                 # d ln CoL per hot day (1st order)
  data.table(scen = s, extra_hot_days = dhot,
             col_cost_pct = 100 * col_per_hotday * dhot / 365,
             displacement_value_yuan_hh_yr = ann_sp * sum(w * dch) * dhot / 365)
}))
wel[, col_cost_yuan_hh_yr := ann_sp * col_cost_pct / 100]
fwrite(wel, file.path(DIR_TAB, "t13_welfare.csv"))

## ---- (c) carbon feedback (EF kgCO2e per kg, Poore & Nemecek 2018 medians)
EF <- c(G01_主食 = 1.6, G02_食用油 = 3.0, G03_蔬菜 = 0.5, G04_水果 = 0.6,
        G05_猪肉 = 7.2, G06_禽类及其他肉类 = 6.1, G07_牛羊肉 = 25.0,
        G08_海鲜 = 5.1, G09_乳制品 = 2.0, G10_坚果 = 1.5)
# quantity response per group on hot days ~ spend response - own price response
gam <- dec[bin == "gt30", price_gamma]
qresp <- dec[bin == "gt30", total_spend_resp] - gam
mean_spc <- fread(file.path(DIR_TAB, "t8_group_spc_means.csv"))
pr <- fread(file.path(DIR_INT, "price_cat_province_date.csv.gz"), encoding = "UTF-8")
pr[, per_kg := external_price_mean_monitor * fifelse(grepl("升", units), 1.03, 2)]
cat2g <- fread(file.path(DIR_LKP, "category_map.csv"), encoding = "UTF-8")
pg <- merge(pr, cat2g, by = "Category")[, .(p_kg = median(per_kg, na.rm = TRUE)), by = food_group10]
carb <- merge(merge(mean_spc, pg, by = "food_group10"),
              data.table(food_group10 = dec[bin=="gt30", group], qresp = qresp), by = "food_group10")
carb[, dkg_hotday := mean_spend_pc / p_kg * qresp]        # per capita kg change per hot day
carb[, dco2_g_hotday := dkg_hotday * EF[food_group10] * 1000]
fwrite(carb, file.path(DIR_TAB, "t14_carbon_feedback.csv"))
logmsg("11: carbon feedback per hot day (g CO2e pc): ", round(sum(carb$dco2_g_hotday), 1))

## ---- (d) policy
# cold-chain counterfactual: set non-tier-A price gamma to tier-A level
# (price equation is province-level here; implemented as scenario where the
#  hot-day price response is halved, the tier-A/B gap upper bound from P3 RMI)
pol1 <- data.table(scenario = c("as_estimated","cold_chain_tierA"),
                   col_cost_pct_p30 = c(wel[scen=="d30", col_cost_pct],
                                        wel[scen=="d30", col_cost_pct] * 0.5))
# elderly targeting: extra protein gap on hot days x protein price
het <- fread(file.path(DIR_TAB, "t6_trip_heterogeneity.csv"))
eld <- het[spec == "elderly" & grepl("gt30", term) & grepl(":", term), est]
nut9 <- fread(file.path(DIR_TAB, "t9_nutrient_means.csv"))
prot_price <- pg[food_group10 %in% c("G05_猪肉","G07_牛羊肉","G08_海鲜","G09_乳制品"), mean(p_kg)] / 100  # yuan per g protein approx (10% protein)
pol2 <- data.table(elderly_extra_trip_resp = if (length(eld)) eld[1] else NA,
                   mean_prot_pc_g = nut9$mean_prot_pc,
                   yuan_per_g_protein = prot_price)
fwrite(pol1, file.path(DIR_TAB, "t15_policy_coldchain.csv"))
fwrite(pol2, file.path(DIR_TAB, "t15_policy_targeting.csv"))
logmsg("11: done")
