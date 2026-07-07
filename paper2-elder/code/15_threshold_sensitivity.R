# =============================================================================
# 15_threshold_sensitivity.R — robustness to the hard-coded age thresholds and
# to pooling survey years. ELDER_AGE (60 vs 65) drives the whole living-
# arrangement classification and the B-line elder flag; CHILD_AGE and the
# 2023/2024 pooling are also probed. Re-derives classification from the roster
# (member_long) so the threshold is a true parameter, not a fixed constant.
# Outputs: table21_threshold_year_sensitivity.csv
# =============================================================================
source("/root/data/Paper/食物消费数据/paper2-elder/code/00_setup.R")
suppressPackageStartupMessages({ library(fixest); library(data.table) })

mem <- fread(file.path(DIR_DERIV, "member_long.csv"), colClasses = list(character = c("nhCode")))
hh  <- fread(file.path(DIR_DERIV, "hh_analysis.csv"), colClasses = list(character = c("nhCode","xzc12")))
per <- fread(file.path(DIR_DERIV, "person_analysis.csv"), colClasses = list(character = c("nhCode","pid","xzc12")))
mem[, age := num(age)]

# rebuild household living arrangement for an arbitrary elder threshold ----------
classify <- function(elder_age, child_age = 18) {
  m <- copy(mem)
  m[, `:=`(eld = as.integer(!is.na(age) & age >= elder_age),
           kid = as.integer(!is.na(age) & age < child_age),
           mid = as.integer(!is.na(age) & age >= child_age & age < elder_age),
           amiss = as.integer(is.na(age)))]
  comp <- m[, .(hh_size = .N, ne = sum(eld), nk = sum(kid), na_ = sum(mid), nm = sum(amiss)),
            by = .(nhCode, data_year)]
  comp[, la := fcase(
    ne == 0, "no_elder",
    nm > 0 & ne >= 1, "other",
    ne >= 1 & na_ >= 1 & nk >= 1, "threegen",
    ne >= 1 & na_ >= 1 & nk == 0, "cohabit_nonelder",
    ne >= 2 & na_ == 0 & nk == 0, "elder_only_multi",
    ne == 1 & hh_size == 1, "elder_alone",
    ne >= 1 & na_ == 0 & nk >= 1, "elder_child",
    default = "other")]
  comp[, .(nhCode, data_year, la)]
}

aline_effect <- function(comp, sample_hh) {
  d <- merge(sample_hh, comp, by = c("nhCode","data_year"))
  d <- d[la %in% c("cohabit_nonelder","threegen")]
  d[, `:=`(treat = as.integer(la == "threegen"), hdds12 = num(hdds12),
           county_year = paste(countyn, data_year))]
  if (d[, uniqueN(treat)] < 2 || nrow(d) < 50) return(NULL)
  m <- feols(hdds12 ~ treat + ln_income + any_elder_80 + n_elderly | county_year,
             data = d, cluster = ~xzc12)
  ct <- coeftable(m)["treat", ]
  data.table(est = ct["Estimate"], se = ct["Std. Error"], p = ct["Pr(>|t|)"],
             n = nrow(d), n_treat = d[, sum(treat)])
}

hh[, `:=`(ln_income = num(ln_income), any_elder_80 = num(any_elder_80), n_elderly = num(n_elderly))]

res <- list()
# A-line: elder threshold 60 vs 65 (pooled years)
for (ea in c(60, 65)) {
  r <- aline_effect(classify(ea), hh)
  if (!is.null(r)) res[[paste0("aline_elder", ea)]] <- r[, spec := sprintf("A-line, elder>=%d, pooled", ea)]
}
# A-line: child threshold 18 vs 15 (elder 60)
for (ca in c(15, 16)) {
  r <- aline_effect(classify(60, ca), hh)
  if (!is.null(r)) res[[paste0("aline_child", ca)]] <- r[, spec := sprintf("A-line, elder>=60, child<%d", ca)]
}
# A-line: by survey year (elder 60)
comp60 <- classify(60)
for (yr in sort(unique(hh$data_year))) {
  r <- aline_effect(comp60, hh[data_year == yr])
  if (!is.null(r)) res[[paste0("aline_yr", yr)]] <- r[, spec := sprintf("A-line, elder>=60, year %s only", yr)]
}

# B-line elder gap at elder threshold 60 vs 65 -----------------------------------
# elder flag from person age; keep mixed households (>=1 elder & >=1 non-elder adult 18-64/59)
bline_gap <- function(elder_age) {
  p <- copy(per)
  p[, age_yrs := num(age_yrs)]
  p[, elder := as.integer(!is.na(age_yrs) & age_yrs >= elder_age)]
  p[, adult := as.integer(!is.na(age_yrs) & age_yrs >= 18)]
  p <- p[adult == 1 & !is.na(num(fgds10))]
  p[, fgds10 := num(fgds10)]; p[, female := num(female)]
  # mixed households: both an elder and a non-elder adult present
  mix <- p[, .(has_e = any(elder == 1), has_a = any(elder == 0)), by = .(nhCode, data_year)][has_e & has_a]
  p <- merge(p, mix[, .(nhCode, data_year)], by = c("nhCode","data_year"))
  p[, hh_id := paste(nhCode, data_year)]
  if (nrow(p) < 100 || p[, uniqueN(elder)] < 2) return(NULL)
  m <- feols(fgds10 ~ elder + female | hh_id, data = p, cluster = ~xzc12)
  ct <- coeftable(m)["elder", ]
  data.table(est = ct["Estimate"], se = ct["Std. Error"], p = ct["Pr(>|t|)"],
             n = nrow(p), n_treat = p[, sum(elder)])
}
for (ea in c(60, 65)) {
  r <- bline_gap(ea)
  if (!is.null(r)) res[[paste0("bline_elder", ea)]] <- r[, spec := sprintf("B-line elder gap, elder>=%d", ea)]
}

t21 <- rbindlist(res, fill = TRUE)[, .(spec, est, se, p, n, n_treat)]
wtab(t21, "table21_threshold_year_sensitivity.csv")
cat("THRESHOLD SENSITIVITY OK\n"); print(t21)
