# =============================================================================
# 02_build_panel.R — build the Paper 3 analysis panel
#   village block : treatment (retail thickness PCA), IV (detour), terrain/GAEZ
#                   conditioning set, NTL aux IV, village survey food environment
#   household block: controls + 12-category consumption/self-sufficiency/prices
#   person block  : diet diversity outcomes (reused from paper2-elder build,
#                   which reconstructed them from the raw 48h recall exports)
# Outputs: data/p3_village.csv, p3_household.csv, p3_person.csv
#          outputs/reports/build_report.md
# =============================================================================
source("/root/data/Paper/食物消费数据/paper3-foodenv/code/00_setup.R")
con <- log_open("02_build.log")
rep <- c("# Paper 3 build report", paste0("Generated: ", format(Sys.time())), "")

# ---------------------------------------------------------------------------
# 1. village survey food-environment module
# ---------------------------------------------------------------------------
vil <- fread(F_VIL, colClasses = list(character = "xzcCode"))
vs <- vil[, .(xzc12 = xzcCode, data_year,
              vs_super_5km   = num(fe01_01), vs_grocery_5km = num(fe01_02),
              vs_market_5km  = num(fe01_03), vs_meat_5km    = num(fe01_04),
              d_super  = num(fe03_01), d_grocery = num(fe03_02),
              d_market = num(fe03_03), d_meat    = num(fe03_04),
              juli = num(juli), vpop = num(xz02), fe_change = as.character(change))]
# counts: blank = outlet type not present -> 0 (submitted questionnaires)
for (cc in c("vs_super_5km","vs_grocery_5km","vs_market_5km","vs_meat_5km"))
  vs[is.na(get(cc)), (cc) := 0]
vs[, fe03_min := pmin(d_super, d_grocery, d_market, d_meat, na.rm = TRUE)]
vs[is.infinite(fe03_min), fe03_min := NA]
rep <- c(rep, sprintf("- village survey: %d villages (%d in 2023 / %d in 2024); fe03_min missing %d",
                      nrow(vs), sum(vs$data_year == 2023), sum(vs$data_year == 2024),
                      sum(is.na(vs$fe03_min))))

# ---------------------------------------------------------------------------
# 2. POI counts within 5 km (amap+shp merged & deduplicated long file)
# ---------------------------------------------------------------------------
poi <- fread(F_POI, colClasses = list(character = "xzc12"))
setnames(poi, names(poi)[1], sub("^﻿", "", names(poi)[1]))
poi <- poi[num(distance_m) <= 5000]
cat_map <- c(超市 = "grocery", 便利店 = "grocery", 食品杂货店 = "grocery",
             菜市场 = "fresh", 水果店 = "fresh",
             肉店 = "meat", 水产店 = "meat",
             餐馆 = "restaurant", 电商服务站 = "ecommerce", 快递点 = "ecommerce")
poi[, grp := cat_map[hit_keyword]]
pc <- dcast(poi[!is.na(grp)], xzc12 ~ grp, fun.aggregate = length, value.var = "grp")
setnames(pc, setdiff(names(pc), "xzc12"), paste0("poi_", setdiff(names(pc), "xzc12"), "_5km"))
rep <- c(rep, sprintf("- POI file: %d POIs within 5km across %d villages (villages w/o any POI get 0)",
                      nrow(poi), nrow(pc)))

# ---------------------------------------------------------------------------
# 3. IV + terrain + GAEZ + NTL (one row per village)
# ---------------------------------------------------------------------------
iv <- fread(file.path(DIR_DERIV, "iv_village.csv"), colClasses = list(character = "xzc12"))

ter <- fread(F_TERRAIN)
setnames(ter, "﻿provn", "provn", skip_absent = TRUE)
ter <- ter[, .(xzc12 = as.character(xzc12), elevation_mean, slope_mean, tri_mean,
               water_occurrence_mean, permanent_water_mean, seasonal_water_mean)]

gz <- fread(F_GAEZ)
gz <- unique(gz, by = "xzc12")   # 363 rows: 2 duplicated village codes, identical 10km cells
gz <- gz[, .(xzc12 = as.character(xzc12),
             gaez_si = num(gaez_overall_si_10km),
             gaez_constraint = num(gaez_soil_terrain_constraint_10km))]

ntl <- fread(F_NTL)
ntl <- ntl[, .(xzc12 = as.character(xzc12), ntl_iv = num(iv_early_ntl_peak_dist_9294))]

vg <- Reduce(function(a, b) merge(a, b, by = "xzc12", all.x = TRUE),
             list(vs, pc, iv[, !c("provn","countyn","townn","viln")], ter, gz, ntl))
for (cc in grep("^poi_", names(vg), value = TRUE)) vg[is.na(get(cc)), (cc) := 0]

# ---------------------------------------------------------------------------
# 4. treatment definitions
# ---------------------------------------------------------------------------
pca_cols <- c("poi_grocery_5km","poi_fresh_5km","poi_meat_5km",
              "vs_super_5km","vs_grocery_5km","vs_market_5km","vs_meat_5km")
stopifnot(all(pca_cols %in% names(vg)))
M <- as.matrix(vg[, lapply(.SD, function(x) log1p(num(x))), .SDcols = pca_cols])
pcafit <- prcomp(M, center = TRUE, scale. = TRUE)
vg[, retail_pc1 := pcafit$x[, 1]]
if (cor(vg$retail_pc1, log1p(vg$poi_grocery_5km)) < 0) vg[, retail_pc1 := -retail_pc1]
vg[, retail_pc1 := z(retail_pc1)]
vg[, retail_lnfresh := log1p(poi_fresh_5km + poi_meat_5km)]        # alt 1
vg[, access_dist    := -log1p(fifelse(is.na(fe03_min), juli, pmin(fe03_min, juli, na.rm = TRUE)))]  # alt 2
rep <- c(rep, sprintf("- retail_pc1: PC1 explains %.1f%% of variance; loadings all %s",
                      100 * summary(pcafit)$importance[2, 1],
                      ifelse(all(sign(pcafit$rotation[, 1]) == sign(pcafit$rotation[1, 1])), "same-signed", "MIXED SIGN")),
         paste0("  loadings: ", paste(sprintf("%s=%.2f", pca_cols, pcafit$rotation[, 1]), collapse = ", ")))

# IV z-scored (raw column has an arbitrary unit offset from the GEE cost surface)
for (km in c(1, 2, 5)) for (dd in c("town", "county")) {
  cc <- sprintf("detour_%s_%dkm", dd, km); vg[, (cc) := z(num(get(cc)))]
}
vg[, ntl_iv := z(log1p(ntl_iv))]

# conditioning set
vg[, `:=`(ln_vpop = log1p(vpop),
          ln_dist_town = log1p(dist_town_5km), ln_dist_county = log1p(dist_county_5km),
          elevation_mean_z = z(elevation_mean), slope_mean_z = z(slope_mean),
          tri_mean_z = z(tri_mean), water_occ_z = z(water_occurrence_mean))]
rep <- c(rep, sprintf("- village analysis block: %d rows; NA in conditioning set: %s",
                      nrow(vg),
                      paste(sapply(c("ln_vpop","ln_dist_town","gaez_si","detour_town_5km"),
                                   function(cc) sum(is.na(vg[[cc]]))), collapse = "/")))

# ---------------------------------------------------------------------------
# 5. household block
# ---------------------------------------------------------------------------
hdr <- names(fread(F_HH, nrows = 0))
food_cols <- as.vector(outer(FOOD12, c("_cons_monthly_jin","_price_wavg_yuan_per_jin","_self_suff_rate"), paste0))
sown_cols <- grep("^liangshi_sc_01_liangshipcL", hdr, value = TRUE)
base_cols <- c("nhCode","data_year","provn","countyn","viln","total_income_w",
               paste0("HB", 1:9), "food_monthly_total","food_self_suff_rate")
sel <- intersect(c(base_cols, food_cols, sown_cols), hdr)
hh <- fread(F_HH, select = sel, colClasses = list(character = "nhCode"))
hh[, xzc12 := substr(nhCode, 1, 12)]
hh[, sown_mu := rowSums(.SD, na.rm = TRUE), .SDcols = intersect(sown_cols, names(hh))]
hh[, ln_sown := log1p(w99(sown_mu))]
hh[, ln_income := log1p(w99(num(total_income_w)))]
hh[, hb_fridge  := as.integer(num(HB8) > 0)]; hh[is.na(hb_fridge), hb_fridge := 0]
hh[, hb_vehicle := as.integer(num(HB1) > 0 | num(HB2) > 0)]; hh[is.na(hb_vehicle), hb_vehicle := 0]

# roster aggregates for all households (from paper2 member build)
mem <- fread(F_MEMBER_P2, colClasses = list(character = "nhCode"))
magg <- mem[, .(hh_size_rec = .N, n_eld = sum(elderly, na.rm = TRUE),
                n_chd = sum(child, na.rm = TRUE),
                offfarm_days_hh = sum(num(offfarm_days), na.rm = TRUE),
                edu_yrs_adult = mean(fifelse(!child, num(education_code), NA_real_), na.rm = TRUE)),
             by = nhCode]
magg[, dep_ratio := (n_eld + n_chd) / hh_size_rec]
hh <- merge(hh, magg, by = "nhCode", all.x = TRUE)
rep <- c(rep, sprintf("- household block: %d rows, %d with roster aggregates; median sown %.1f mu",
                      nrow(hh), sum(!is.na(hh$hh_size_rec)), median(hh$sown_mu, na.rm = TRUE)))

# purchases (mechanism): monthly purchased quantity per category
for (g in FOOD12) {
  cq <- paste0(g, "_cons_monthly_jin"); sr <- paste0(g, "_self_suff_rate")
  hh[, (paste0(g, "_buy_jin")) := pmax(num(get(cq)), 0) * (1 - pmin(pmax(num(get(sr)), 0), 1))]
}
# overall self-sufficiency: the delivered food_self_suff_rate column is broken
# (unit mismatch, median 0.0008); rebuild as the consumption-weighted mean of
# the (sane) category-level rates
ssr_mat <- sapply(FOOD12, function(g) pmin(pmax(num(hh[[paste0(g, "_self_suff_rate")]]), 0), 1))
wt_mat  <- sapply(FOOD12, function(g) pmax(num(hh[[paste0(g, "_cons_monthly_jin")]]), 0))
wt_mat[is.na(ssr_mat)] <- NA
hh[, food_ssr_w := rowSums(ssr_mat * wt_mat, na.rm = TRUE) / pmax(rowSums(wt_mat, na.rm = TRUE), 1e-9)]
rep <- c(rep, sprintf("- food_ssr_w rebuilt (delivered overall rate broken): mean %.2f, median %.2f",
                      mean(hh$food_ssr_w, na.rm = TRUE), median(hh$food_ssr_w, na.rm = TRUE)))

# ---------------------------------------------------------------------------
# 6. person block (reuse paper2 build; nutrient/gram outcomes stay SEALED)
# ---------------------------------------------------------------------------
per <- fread(F_PERSON_P2, colClasses = list(character = c("nhCode")))
per <- per[, .(nhCode, data_year, pid, xzc12 = as.character(xzc12), provn, countyn,
               fgds10 = num(fgds10), fvs = num(fvs_unique_foods),
               hdds12 = num(hdds12_household),
               mddw = num(mddw), mddw_elig = num(mddw_woman_15_49),
               cdds8 = num(cdds8_who2021), cdds7 = num(cdds7_who2010),
               cdds_elig = num(child_mdd_eligible_6to23m),
               age_months = num(age_months_approx),
               dbi_variety = num(dbi16_variety_subscore),
               female = num(female), age_yrs = num(age_yrs),
               elderly = num(elderly), child = num(child),
               xfy_dining = num(xfy_dining), interview_month, hh_id)]
# child dietary diversity: proposal defines the subgroup as 6-59 months
per[, cdds_elig_659 := as.integer(!is.na(age_months) & age_months >= 6 & age_months < 60)]
rep <- c(rep, sprintf("- person block: %d recalls; women 15-49 (mddw eligible): %d; children 6-59m: %d",
                      nrow(per), sum(per$mddw_elig == 1, na.rm = TRUE), sum(per$cdds_elig_659 == 1)))

# ---------------------------------------------------------------------------
# 7. merges + FE structure + sample flow
# ---------------------------------------------------------------------------
hh2 <- merge(hh, vg[, !c("data_year")], by = "xzc12", all.x = TRUE)
pers <- merge(per,
              hh2[, .(nhCode, ln_income_hh = ln_income, hh_size_rec, dep_ratio,
                      hb_fridge, hb_vehicle, ln_sown, food_ssr_w,
                      offfarm_days_hh, edu_yrs_adult)],
              by = "nhCode", all.x = TRUE)
pers <- merge(pers, vg[, !c("data_year")], by = "xzc12", all.x = TRUE)
pers[, ln_income := ln_income_hh][, ln_income_hh := NULL]
# roster-unmatched recalls: median-impute age/female with missingness dummies
pers[, age_miss := as.integer(is.na(age_yrs))]
pers[, age_yrs_i := fifelse(is.na(age_yrs), median(age_yrs, na.rm = TRUE), age_yrs)]
pers[, female_i := fifelse(is.na(female), 0.5, num(female))]
med_dep <- median(pers$dep_ratio, na.rm = TRUE)
pers[is.na(dep_ratio), dep_ratio := med_dep]
pers[is.na(hh_size_rec), hh_size_rec := median(pers$hh_size_rec, na.rm = TRUE)]
rep <- c(rep, sprintf("- age missing (roster-unmatched recalls): %d of %d -> median-imputed + dummy",
                      sum(pers$age_miss), nrow(pers)))
# County names are not canonical in the survey exports (e.g. the same code is
# recorded as both "永吉市" and "永吉县"). Use the GB/T 2260 county prefix.
pers[, county_id   := substr(xzc12, 1, 6)]
pers[, county_year := paste(county_id, data_year, sep = "_")]
hh2[, county_id   := substr(xzc12, 1, 6)]
hh2[, county_year := paste(county_id, data_year, sep = "_")]
vg2 <- merge(vg, unique(per[, .(xzc12, provn, countyn)]), by = "xzc12", all.x = TRUE)
vg2 <- unique(vg2, by = "xzc12")
vg2[, county_id := substr(xzc12, 1, 6)]
vg2[, county_year := paste(county_id, data_year, sep = "_")]

# do counties appear in both survey years? (决定 county×year FE 的实际含义)
cyr <- unique(pers[, .(county_id, data_year)])[, .N, by = county_id]
rep <- c(rep, sprintf("- counties appearing in both years: %d of %d (county×year FE %s)",
                      sum(cyr$N == 2), nrow(cyr),
                      ifelse(sum(cyr$N == 2) > 0, "binds beyond county FE", "== county FE")))

flow <- data.table(step = c("person recalls", "+ household controls merged", "+ village IV/treatment merged",
                            "final analysis (non-missing y/T/IV/controls)"),
                   n = c(nrow(per), sum(!is.na(pers$ln_income)), sum(!is.na(pers$detour_town_5km)),
                         nrow(pers[!is.na(fgds10) & !is.na(retail_pc1) & !is.na(detour_town_5km) &
                                   !is.na(ln_income) & !is.na(ln_vpop) & !is.na(gaez_si)])))
rep <- c(rep, "", "Sample flow:", knitr_kable <- paste0("- ", flow$step, ": ", flow$n))

# village count consistency assertion
stopifnot(nrow(vg) == 361, uniqueN(pers$xzc12) == 361)

fwrite(vg2,  file.path(DIR_DERIV, "p3_village.csv"))
fwrite(hh2,  file.path(DIR_DERIV, "p3_household.csv"))
fwrite(pers, file.path(DIR_DERIV, "p3_person.csv"))
rep <- c(rep, "", "Sealed outcomes note: absolute nutrient quantities / gram families excluded",
         "portfolio-wide per Paper-2 Task-3 unit audit FAIL (D1/D6).")
writeLines(rep, file.path(DIR_REP, "build_report.md"))
cat("build done:", nrow(vg2), "villages,", nrow(hh2), "households,", nrow(pers), "persons\n")
log_close(con)
