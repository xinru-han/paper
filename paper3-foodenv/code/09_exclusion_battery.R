# =============================================================================
# 09_exclusion_battery.R — T7: design-validity battery.
# With a null main effect, the battery's role flips: it must show the design
# HAD power (first stage real, no bypass channels contaminating the null).
#  (1) placebo outcome: adult education years (transport-unrelated)
#  (2) income bypass: detour -> ln income reduced form; main RF w/ and w/o
#      income and household off-farm labor days
#  (3) self-sufficiency-controlled version (mechanism-part control)
#  (4) over-identification: town+county detour (+NTL) Hansen J
# =============================================================================
source("/root/data/Paper/食物消费数据/paper3-foodenv/code/00_setup.R")
con <- log_open("09_exclusion.log")

pers <- fread(file.path(DIR_DERIV, "p3_person.csv"), colClasses = list(character = c("xzc12","nhCode")))
hh   <- fread(file.path(DIR_DERIV, "p3_household.csv"), colClasses = list(character = c("xzc12","nhCode")))
hh[, county_year := paste(provn, countyn, data_year, sep = "_")]
XC <- c(XI, XH, ZV)
rows <- list()
add <- function(label, m, term = IV_RF) {
  a <- coeftable(m)[term, ]
  rows[[length(rows) + 1]] <<- data.table(test = label, term = term,
                                          b = a[1], se = a[2], p = a[4], n = m$nobs)
}

# (1) placebo: household mean adult education years (village exposure)
hh2 <- hh[!is.na(edu_yrs_adult)]
add("placebo: adult education yrs (hh)", feols(rhs("edu_yrs_adult", c(IV_RF, ZV, "ln_income","hh_size_rec")), hh2, cluster = ~xzc12))

# (2) income bypass
add("bypass: ln income (hh RF)", feols(rhs("ln_income", c(IV_RF, ZV, "hh_size_rec","dep_ratio")), hh, cluster = ~xzc12))
add("bypass: off-farm days (hh RF)", feols(rhs("offfarm_days_hh", c(IV_RF, ZV, "hh_size_rec","dep_ratio")), hh[!is.na(offfarm_days_hh)], cluster = ~xzc12))
add("main RF w/o income controls", feols(rhs("fgds10", c(IV_RF, XI, setdiff(XH, "ln_income"), ZV)), pers, cluster = ~xzc12))
add("main RF with income (baseline)", feols(rhs("fgds10", c(IV_RF, XC)), pers, cluster = ~xzc12))

# (3) self-sufficiency-controlled (mechanism part; two-version report)
add("main RF + food self-suff rate", feols(rhs("fgds10", c(IV_RF, XC, "food_ssr_w")),
                                           pers[!is.na(food_ssr_w)], cluster = ~xzc12))

# (4) over-identification (2SLS with 2 then 3 IVs; Hansen J via sargan stat)
for (ivset in list(c("detour_town_1km", "detour_county_1km"),
                   c("detour_town_1km", "detour_county_1km", "ntl_iv"))) {
  f2 <- as.formula(paste("fgds10 ~", paste(XC, collapse = "+"), "| county_year |",
                         TREAT, "~", paste(ivset, collapse = "+")))
  m <- feols(f2, pers[!is.na(ntl_iv)], cluster = ~xzc12)
  sg <- tryCatch(fitstat(m, "sargan")$sargan, error = function(e) list(stat = NA, p = NA))
  a <- coeftable(m)[paste0("fit_", TREAT), ]
  rows[[length(rows) + 1]] <- data.table(
    test = paste0("overid 2SLS (", paste(ivset, collapse = "+"), ")"),
    term = "retail_pc1", b = a[1], se = a[2], p = a[4], n = m$nobs)
  rows[[length(rows) + 1]] <- data.table(
    test = paste0("  Sargan J p (", length(ivset), " IVs)"),
    term = "J", b = sg$stat, se = NA, p = sg$p, n = m$nobs)
}

t7 <- rbindlist(rows)
wtab(t7, "t7_exclusion_battery.csv")
print(t7, digits = 3)
log_close(con)
