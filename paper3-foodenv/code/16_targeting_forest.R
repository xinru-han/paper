# =============================================================================
# 16_targeting_forest.R — v2 §19 exploratory heterogeneity forest.
# grf causal_forest with W = detour (continuous exposure, partially linear),
# village-clustered, honest splitting. Output is an EXPLORATORY RANKING TOOL
# (no confidence claims): CATE vs detour/income/self-sufficiency/elder share,
# county-aggregated priority list ("high shortfall x high response").
# =============================================================================
source("/root/data/Paper/食物消费数据/paper3-foodenv/code/00_setup.R")
suppressPackageStartupMessages(library(grf))
con <- log_open("16_forest.log")

pers <- fread(file.path(DIR_DERIV, "p3_person.csv"), colClasses = list(character = c("xzc12","nhCode")))
d <- pers[!is.na(fgds10) & !is.na(detour_town_5km) & !is.na(ln_income) & !is.na(gaez_si) &
          !is.na(ln_vpop) & !is.na(food_ssr_w)]
Xv <- c("ln_income", "hh_size_rec", "dep_ratio", "hb_fridge", "hb_vehicle", "ln_sown",
        "food_ssr_w", "age_yrs_i", "female_i", "ln_vpop", "ln_dist_town",
        "ln_dist_county", "elevation_mean_z", "water_occ_z", "gaez_si")
X <- as.matrix(d[, ..Xv])
cl <- as.integer(factor(d$xzc12))

# demean Y and W within county×year first: the forest must target the same
# within-county variation as the design (raw causal_forest would re-admit the
# cross-county development gradient the FE removes)
d[, county_year := paste(substr(xzc12, 1, 6), data_year, sep = "_")]
d[, `:=`(y_dm = fgds10 - mean(fgds10), w_dm = detour_town_5km - mean(detour_town_5km)),
  by = county_year]

cf <- causal_forest(X, Y = d$y_dm, W = d$w_dm,
                    clusters = cl, honesty = TRUE, num.trees = 2000, seed = 20260708)
ate <- average_treatment_effect(cf)
cat(sprintf("forest 'ATE' (adjusted association, NOT causal): %.3f (se %.3f)\n", ate[1], ate[2]))

tau <- predict(cf)$predictions
d[, cate := tau]

# partial dependence: CATE by quartiles of key village/household features
pd <- rbindlist(lapply(c("detour_town_5km", "ln_income", "food_ssr_w", "dep_ratio"),
  function(v) {
    d[, qt := paste0("Q", pmin(4, 1 + floor(4 * (frank(get(v), ties.method = "average") - 1) / .N)))]
    d[!is.na(qt), .(feature = v, quartile = as.character(qt[1]), mean_cate = mean(cate), n = .N), by = qt][, !"qt"]
  }))
wtab(pd, "t11_forest_partial_dependence.csv")
print(dcast(pd, feature ~ quartile, value.var = "mean_cate"), digits = 3)

# county priority list: shortfall x response (exploratory ranking only)
cnty <- d[, .(mean_fgds10 = mean(fgds10), mean_cate = mean(cate), n = .N),
          by = .(provn, countyn)]
cnty[, shortfall := max(mean_fgds10) - mean_fgds10]
cnty[, priority := frank(-shortfall) + frank(mean_cate)]   # low fgds10 + most-negative CATE
setorder(cnty, priority)
wtab(cnty[1:20], "t11b_county_priority_top20.csv")
cat("\nTop-10 priority counties (exploratory ranking, no confidence claims):\n")
print(cnty[1:10, .(provn, countyn, mean_fgds10, mean_cate, n)], digits = 3)

vi <- data.table(feature = Xv, importance = variable_importance(cf)[, 1])[order(-importance)]
wtab(vi, "t11c_forest_varimp.csv")
fwrite(d[, .(xzc12, cate)], file.path(DIR_DERIV, "forest_cate.csv"))
log_close(con)
