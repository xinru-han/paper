# =============================================================================
# 00_setup.R — Paper 2 (paper2-elder): paths, packages, shared helpers
# Intergenerational Co-residence, Household Food Provisioning,
# and What Older Adults Actually Eat: Evidence from Rural China
# =============================================================================

.libPaths(c("/root/Rlibs", .libPaths()))
suppressPackageStartupMessages({
  library(data.table)
})

# ---- paths ------------------------------------------------------------------
DATA_ROOT <- "/root/data/数据/食物消费调查数据"
PROJ      <- "/root/data/Paper/食物消费数据/paper2-elder"
DIR_DERIV <- file.path(PROJ, "data")
DIR_TAB   <- file.path(PROJ, "outputs/tables")
DIR_FIG   <- file.path(PROJ, "outputs/figures")
DIR_REP   <- file.path(PROJ, "outputs/reports")
DIR_LOG   <- file.path(PROJ, "outputs/logs")
for (d in c(DIR_DERIV, DIR_TAB, DIR_FIG, DIR_REP, DIR_LOG)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

F_HH       <- file.path(DATA_ROOT, "处理后的data/户表数据_已清洗.csv")
F_VIL      <- file.path(DATA_ROOT, "处理后的data/村表数据_已清洗.csv")
F_DIET_P   <- file.path(DATA_ROOT, "导出的数据/2天48小时膳食情况/nutrients/48h_diet_indices_person.csv")
F_DIET_HH  <- file.path(DATA_ROOT, "导出的数据/2天48小时膳食情况/nutrients/48h_diet_indices_household.csv")
F_NUTR_ML  <- file.path(DATA_ROOT, "导出的数据/2天48小时膳食情况/nutrients/48h_nutrients_person_meal_long_corrected.csv")
F_POI      <- file.path(DATA_ROOT, "处理后的data/village_pois_merged_dedup.csv")
F_IDAY23   <- file.path(DATA_ROOT, "原始数据/访问日统计_XZM20240421.xlsx")
F_IDAY24   <- file.path(DATA_ROOT, "原始数据/访问日统计_2025.xlsx")
F_COUNTY_TXT <- "/root/data/数据/县级政府工作报告/县域政府工作报告内容_补版_mk.xlsx"

# ---- conventions (project red lines) ---------------------------------------
# * privacy: huName / vilLat / vilLon / phone must NEVER be written to outputs
# * 幸福院 (n=12 users) must never be a household-level policy treatment
# * elderly = age >= 60 at survey year; child = age < 18; jin = 0.5 kg
# * denominators for food shares use the 12-category sum
FOOD12 <- c("zhushi","doulei","roulei","danlei","nailei","youzhi",
            "shucai","shuiguo","tiaoliao","tang","cha","yan")
FOOD_LAB <- c(zhushi="Staples", doulei="Beans", roulei="Meat", danlei="Eggs",
              nailei="Dairy", youzhi="Oils", shucai="Vegetables", shuiguo="Fruit",
              tiaoliao="Condiments", tang="Sugar", cha="Tea", yan="Tobacco")

ELDER_AGE <- 60
CHILD_AGE <- 18

# ---- helpers ----------------------------------------------------------------
# age in years at survey year from "YYYY-MM" birth string
age_from_birth <- function(birth, year) {
  by <- suppressWarnings(as.integer(substr(birth, 1, 4)))
  by[by < 1900 | by > 2024] <- NA_integer_
  as.integer(year) - by
}

num <- function(x) suppressWarnings(as.numeric(x))

wtab <- function(dt, file) {
  fwrite(dt, file.path(DIR_TAB, file))
  cat("  [table]", file, "\n")
}

stars <- function(p) ifelse(p < .01, "***", ifelse(p < .05, "**", ifelse(p < .1, "*", "")))

fmt_coef <- function(b, se, p) sprintf("%.3f%s (%.3f)", b, stars(p), se)

# tidy a fixest model into a data.table of selected coefficients
tidy_fe <- function(m, keep = NULL) {
  ct <- as.data.table(coeftable(m), keep.rownames = "term")
  setnames(ct, c("term","est","se","t","p"))
  if (!is.null(keep)) ct <- ct[grepl(keep, term)]
  ct[, n := m$nobs]
  ct
}

log_open <- function(name) {
  con <- file(file.path(DIR_LOG, name), open = "wt")
  sink(con, split = TRUE); sink(con, type = "message")
  invisible(con)
}
log_close <- function(con) { sink(type = "message"); sink(); close(con) }

set.seed(20260707)
