# =============================================================================
# 00_setup.R — Paper 3 (paper3-foodenv): paths, packages, shared helpers
# Rugged Roads to a Diverse Diet: Terrain, Rural Food Environments,
# and Nutrition in China
# Proposal: 食物调查数据研究方案/paper3_食物环境与膳食质量_IV.md (v1 + v2 升级包)
# =============================================================================

.libPaths(c("/root/data/数据/Rlibs", .libPaths()))
suppressPackageStartupMessages({
  library(data.table)
  library(fixest)
})

# ---- paths ------------------------------------------------------------------
DATA_ROOT <- "/root/data/数据/食物消费调查数据"
PROC      <- file.path(DATA_ROOT, "处理后的data")
PROJ      <- "/root/data/Paper/食物消费数据/paper3-foodenv"
P2DATA    <- "/root/data/Paper/食物消费数据/paper2-elder/data"   # reused person/member builds
DIR_DERIV <- file.path(PROJ, "data")
DIR_TAB   <- file.path(PROJ, "outputs/tables")
DIR_FIG   <- file.path(PROJ, "outputs/figures")
DIR_REP   <- file.path(PROJ, "outputs/reports")
DIR_LOG   <- file.path(PROJ, "logs")
for (d in c(DIR_DERIV, DIR_TAB, DIR_FIG, DIR_REP, DIR_LOG)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

F_HH        <- file.path(PROC, "户表数据_已清洗.csv")
F_VIL       <- file.path(PROC, "村表数据_已清洗.csv")
F_POI       <- file.path(PROC, "village_pois_merged_dedup.csv")
F_CORR      <- function(km) file.path(PROC, sprintf("paper1_village_topography_iv_corridor_%dkm.csv", km))
F_TERRAIN   <- file.path(PROC, "paper1_village_terrain_water_controls_5km.csv")
F_GAEZ      <- file.path(PROC, "gaez_theme4_10km_village.csv")
F_NTL       <- file.path(PROC, "paper1_village_early_ntl_peak_iv_9294.csv")
F_GOV       <- file.path(PROC, "gov_coords_wgs84.csv")
F_PERSON_P2 <- file.path(P2DATA, "person_analysis.csv")
F_MEMBER_P2 <- file.path(P2DATA, "member_long.csv")
F_COUNTY_TXT <- "/root/data/数据/县级政府工作报告/县域政府工作报告内容_补版_mk.xlsx"

# ---- conventions (project red lines) ---------------------------------------
# * privacy: village coordinates are never written to outputs (aggregate to
#   county or use jitter for any map-like figure)
# * P2 Task-3 nutrient unit audit FAILED (D1/D6 portfolio-wide): absolute
#   nutrient quantities, gram families (mddwg_*_g_48h, dbiv_*_g_48h) and AR
#   adequacy ratios are SEALED. Outcomes here are diversity indices and
#   presence-type binaries only.
# * elderly = age >= 60; jin = 0.5 kg
FOOD12 <- c("zhushi","doulei","roulei","danlei","nailei","youzhi",
            "shucai","shuiguo","tiaoliao","tang","cha","yan")
FOOD_LAB <- c(zhushi="Staples", doulei="Beans", roulei="Meat", danlei="Eggs",
              nailei="Dairy", youzhi="Oils", shucai="Vegetables", shuiguo="Fruit",
              tiaoliao="Condiments", tang="Sugar", cha="Tea", yan="Tobacco")
# perishability (mechanism ranking): 1 = highly perishable fresh food
PERISHABLE <- c(nailei=1, roulei=1, shuiguo=1, shucai=1, danlei=1,
                doulei=0, zhushi=0, youzhi=0, tiaoliao=0, tang=0, cha=0, yan=0)

# main outcome family (person level unless noted)
Y_MAIN <- c("fgds10", "fvs_unique_foods", "hdds12_household")

# ---- helpers ----------------------------------------------------------------
num <- function(x) suppressWarnings(as.numeric(x))
z   <- function(x) (x - mean(x, na.rm = TRUE)) / sd(x, na.rm = TRUE)
w99 <- function(x) { q <- quantile(x, c(.01, .99), na.rm = TRUE); pmin(pmax(x, q[1]), q[2]) }

wtab <- function(dt, file) { fwrite(dt, file.path(DIR_TAB, file)); cat("  [table]", file, "\n") }

stars <- function(p) ifelse(p < .01, "***", ifelse(p < .05, "**", ifelse(p < .1, "*", "")))
fmt_coef <- function(b, se, p) sprintf("%.3f%s (%.3f)", b, stars(p), se)

tidy_fe <- function(m, keep = NULL) {
  ct <- as.data.table(coeftable(m), keep.rownames = "term")
  setnames(ct, 1:5, c("term","est","se","t","p"))
  if (!is.null(keep)) ct <- ct[grepl(keep, term)]
  ct[, n := m$nobs]
  ct
}

# KP-style first-stage F reported by fixest for IV models
get_ivf <- function(m) tryCatch(fitstat(m, "ivwald")[[1]]$stat, error = function(e) NA_real_)

log_open <- function(name) {
  con <- file(file.path(DIR_LOG, name), open = "wt")
  sink(con, split = TRUE); sink(con, type = "message")
  invisible(con)
}
log_close <- function(con) { sink(type = "message"); sink(); close(con) }

# person-level controls / village controls used across scripts
# (age/female median-imputed with missingness dummies: ~35% of recalls are not
#  matched to a roster member; see build_report.md)
XI  <- c("female_i", "age_yrs_i", "I(age_yrs_i^2)", "age_miss")     # individual
XH  <- c("ln_income", "hh_size_rec", "dep_ratio", "hb_fridge", "hb_vehicle", "ln_sown")  # household
# village conditioning set (MAIN): straight distances + population + elevation +
# water + GAEZ agricultural potential/constraint. Own-village slope/TRI are a
# component of the corridor cost itself (r≈0.45 with the IV) — controlling them
# absorbs the instrument; the agriculture bypass they proxy is controlled
# directly by GAEZ. slope/TRI versions live in the robustness battery.
ZV  <- c("ln_dist_town", "ln_dist_county", "ln_vpop", "elevation_mean_z",
         "water_occ_z", "gaez_si", "gaez_constraint")
ZV_TERR <- c(ZV, "slope_mean_z", "tri_mean_z")                       # robustness set
# D1 (pre-registered, see prereg_p3.md): primary spec = REDUCED FORM in
# detour_town_5km; secondary 2SLS uses the best-F pre-registered combo
# (retail_pc1 <- detour_town_1km, person-level KP-F ≈ 11) + AR CIs.
IV_RF   <- "detour_town_5km"   # reduced-form exposure (primary)
IV_2SLS <- "detour_town_1km"   # 2SLS instrument (best pre-registered F)
TREAT   <- "retail_pc1"
FE_MAIN <- "county_year"       # counties are single-year -> equals county FE

rhs <- function(y, x, fe = FE_MAIN, iv = NULL) {
  f <- paste(y, "~", paste(x, collapse = " + "), "|", fe)
  if (!is.null(iv)) f <- paste(f, "|", iv)
  as.formula(f)
}

set.seed(20260708)
