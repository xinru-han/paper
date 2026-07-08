# =============================================================================
# 01_iv_map.R — inspect corridor IV assets, fix the column mapping (proposal §4
# "第一步必做"), and run internal consistency checks.
# Output: outputs/reports/iv_columns_map.md
# =============================================================================
source("/root/data/Paper/食物消费数据/paper3-foodenv/code/00_setup.R")
con <- log_open("01_iv_map.log")

rep <- c("# Paper 3 — IV column mapping (fixed)", paste0("Generated: ", format(Sys.time())), "",
         "IV construction (GEE run 2026-04-26, see 地形变量与IV_GEE流程说明.md):",
         "`iv_terrain_barrier_{town,county}_gee_Xkm = log(route_cost_distance / euclidean_distance)`",
         "route cost = straight-line path buffered X km, slope-based cost surface;",
         "i.e. the *detour index* of the proposal (ln corridor cost − ln straight dist) is",
         "**already the delivered column** — no further transformation needed.", "")

allc <- list()
for (km in c(1, 2, 5)) {
  d <- fread(F_CORR(km))
  setnames(d, "﻿provn", "provn", skip_absent = TRUE)
  d[, xzc12 := as.character(xzc12)]
  stopifnot(!anyDuplicated(d$xzc12))
  keep <- c("xzc12", "provn", "countyn", "townn", "viln",
            grep("iv_terrain_barrier|straight_dist", names(d), value = TRUE))
  dk <- d[, ..keep]
  setnames(dk,
    c(sprintf("iv_terrain_barrier_town_gee_%dkm", km),  sprintf("iv_terrain_barrier_county_gee_%dkm", km),
      sprintf("town_straight_dist_km_gee_%dkm", km),    sprintf("county_straight_dist_km_gee_%dkm", km)),
    c(sprintf("detour_town_%dkm", km), sprintf("detour_county_%dkm", km),
      sprintf("dist_town_%dkm", km),   sprintf("dist_county_%dkm", km)))
  allc[[as.character(km)]] <- dk
  rep <- c(rep, sprintf("- corridor %dkm: %d villages, detour_town range [%.3f, %.3f], detour_county [%.3f, %.3f]",
                        km, nrow(dk),
                        min(dk[[sprintf("detour_town_%dkm", km)]], na.rm = TRUE),
                        max(dk[[sprintf("detour_town_%dkm", km)]], na.rm = TRUE),
                        min(dk[[sprintf("detour_county_%dkm", km)]], na.rm = TRUE),
                        max(dk[[sprintf("detour_county_%dkm", km)]], na.rm = TRUE)))
}

iv <- Reduce(function(a, b) merge(a, b[, !c("provn","countyn","townn","viln")], by = "xzc12"), allc)

# straight distances should be identical across buffer widths (same endpoints)
rep <- c(rep, "",
  sprintf("- straight-dist consistency (5km vs 1km): town max|Δ| = %.4f km, county = %.4f km",
          max(abs(iv$dist_town_5km - iv$dist_town_1km), na.rm = TRUE),
          max(abs(iv$dist_county_5km - iv$dist_county_1km), na.rm = TRUE)))

# cross-width and town-county correlations of the barrier
cm <- cor(iv[, .(detour_town_1km, detour_town_2km, detour_town_5km,
                 detour_county_1km, detour_county_2km, detour_county_5km)], use = "pairwise")
rep <- c(rep, "", "Correlations of detour measures:", "```",
         capture.output(print(round(cm, 3))), "```", "",
         "Column mapping used throughout the project:",
         "| project variable | source column |", "|---|---|",
         "| detour_town_5km (PRIMARY IV) | iv_terrain_barrier_town_gee_5km |",
         "| detour_county_5km (aux IV / overid) | iv_terrain_barrier_county_gee_5km |",
         "| detour_{town,county}_{1,2}km (robustness) | iv_terrain_barrier_*_gee_{1,2}km |",
         "| dist_town / dist_county (conditioning) | *_straight_dist_km_gee_5km |",
         "",
         "Primary IV choice (pre-registered here): the township corridor — the 5 km retail",
         "environment is supplied through the township market town; the county corridor is",
         "kept for over-identification and robustness. Buffer width 5 km is the main spec,",
         "1/2 km are robustness (narrower corridor = closer to the actual path).")

# NTL auxiliary IV
ntl <- fread(F_NTL)
setnames(ntl, "﻿provn", "provn", skip_absent = TRUE)
ntl[, xzc12 := as.character(xzc12)]
rep <- c(rep, "",
  sprintf("- NTL aux IV: %d villages, iv_early_ntl_peak_dist_9294 range [%.2f, %.2f] (log-km? raw km)",
          nrow(ntl), min(ntl$iv_early_ntl_peak_dist_9294, na.rm = TRUE),
          max(ntl$iv_early_ntl_peak_dist_9294, na.rm = TRUE)))

fwrite(iv, file.path(DIR_DERIV, "iv_village.csv"))
writeLines(rep, file.path(DIR_REP, "iv_columns_map.md"))
cat("saved data/iv_village.csv +", nrow(iv), "villages\n")
log_close(con)
