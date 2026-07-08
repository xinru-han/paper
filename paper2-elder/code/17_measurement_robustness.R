# =============================================================================
# 17_measurement_robustness.R — audit items #1 and #2 (econometric audit 2026-07)
# (1) SCALE-FREE A-line outcomes: household HDDS-12 mechanically rises with the
#     number of members observed in the 48h window ("more mouths, more recorded
#     groups"). Household-size dummies are post-treatment (size IS part of the
#     living arrangement), so we complement the headline with outcomes whose
#     scale does not grow with household size:
#       a) mean member FGDS-10 (individual-level diversity, averaged);
#       b) union FGDS-10 over ALL recorded members (10-group ceiling);
#       c) union FGDS-10 EXCLUDING elders (provisioning to the rest of the
#          household — removes the focal elder's mechanical contribution);
#       d) union FGDS-10 EXCLUDING children;
#       e) rarefaction-style: household HDDS-12 conditioning on the number of
#          recorded members and total recorded meals ("fixed observation
#          opportunity").
# (2) RESIDENT-BASED living arrangement: the roster classification counts
#     registered members who may be long-term absent. Rebuild the classification
#     (i) keeping only members at home >=180 days in the past year and
#     (ii) from members actually observed in the 48h diet window; report the
#     agreement rate with the roster classification and re-estimate the A-line
#     and B-line main results under both.
# Outputs: table26_aline_scalefree.csv, table27_resident_agreement.csv,
#          table27b_resident_main_results.csv
# =============================================================================
source("/root/data/Paper/食物消费数据/paper2-elder/code/00_setup.R")
suppressPackageStartupMessages({ library(fixest) })

hh  <- fread(file.path(DIR_DERIV, "hh_analysis.csv"), colClasses = list(character = c("nhCode","xzc12")))
per <- fread(file.path(DIR_DERIV, "person_analysis.csv"), colClasses = list(character = c("nhCode","pid","xzc12")))
mem <- fread(file.path(DIR_DERIV, "member_long.csv"), colClasses = list(character = c("nhCode","pid")))

CTRL <- "ln_income + any_elder_80 + n_elderly"
hh[, `:=`(hdds12 = num(hdds12), county_year = paste(countyn, data_year))]

# ---------------------------------------------------------------------------
# (1) scale-free household diversity outcomes from person-level 48h records
# ---------------------------------------------------------------------------
GRP10 <- c("mddwg_starchy_g_48h","mddwg_beans_peas_g_48h","mddwg_nuts_seeds_g_48h",
           "mddwg_dairy_g_48h","mddwg_flesh_g_48h","mddwg_eggs_g_48h",
           "mddwg_va_dark_green_g_48h","mddwg_va_other_fv_g_48h",
           "mddwg_other_veg_g_48h","mddwg_other_fruit_g_48h")
for (g in GRP10) per[, (g) := as.integer(num(get(g)) > 0)]
per[, `:=`(fgds10 = num(fgds10), n_meals = num(n_meals),
           elderly = num(elderly), child = num(child))]

union_fgds <- function(d) if (nrow(d) == 0) NA_real_ else
  as.numeric(sum(sapply(GRP10, function(g) as.integer(any(d[[g]] == 1, na.rm = TRUE)))))
hp <- per[, .(
  n_members_rec   = .N,
  n_meals_total   = sum(n_meals, na.rm = TRUE),
  mean_fgds10     = mean(fgds10, na.rm = TRUE),
  union_fgds_all      = union_fgds(.SD),
  union_fgds_nonelder = union_fgds(.SD[elderly != 1]),
  union_fgds_nonchild = union_fgds(.SD[child != 1])
), by = .(nhCode, data_year)]

da <- merge(hh[living_arrangement %in% c("cohabit_nonelder","threegen")],
            hp, by = c("nhCode","data_year"), all.x = TRUE)
da[, treat := as.integer(living_arrangement == "threegen")]

fit_a <- function(y, extra = "", dat = da) {
  d <- dat[!is.na(get(y))]
  m <- feols(as.formula(paste0(y, " ~ treat + ", CTRL, extra, " | county_year")),
             data = d, cluster = ~xzc12)
  tidy_fe(m, "^treat")[, outcome := y]
}
t26 <- rbindlist(list(
  fit_a("hdds12")[, spec := "household HDDS-12 (headline, scale-dependent)"],
  fit_a("hdds12", " + n_members_rec + n_meals_total")[
    , spec := "HDDS-12 | fixed n recorded members + total recorded meals (rarefaction-style)"],
  fit_a("mean_fgds10")[, spec := "mean member FGDS-10 (scale-free)"],
  fit_a("union_fgds_all")[, spec := "union FGDS-10, all recorded members"],
  fit_a("union_fgds_nonelder")[, spec := "union FGDS-10, EXCLUDING elders"],
  fit_a("union_fgds_nonchild")[, spec := "union FGDS-10, EXCLUDING children"]
), fill = TRUE)
wtab(t26, "table26_aline_scalefree.csv")

# ---------------------------------------------------------------------------
# (2) resident-based living arrangement
# ---------------------------------------------------------------------------
mem[, age := num(age)]
mem[, dah := pmin(num(days_at_home), 365)]      # cap keying errors (max seen 8365)
mem[, resident := is.na(dah) | dah >= 180]      # NA treated as resident (conservative)

classify_mem <- function(m) {
  m[, `:=`(eld = as.integer(!is.na(age) & age >= ELDER_AGE),
           kid = as.integer(!is.na(age) & age < CHILD_AGE),
           mid = as.integer(!is.na(age) & age >= CHILD_AGE & age < ELDER_AGE),
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
la_res <- classify_mem(copy(mem)[resident == TRUE])
setnames(la_res, "la", "la_resident")
# 48h-observed classification: members actually appearing in the diet window
la_obs <- classify_mem(per[, .(nhCode, data_year,
                               age = fifelse(!is.na(num(age)), num(age), num(age_yrs)))])
setnames(la_obs, "la", "la_observed")

ag <- merge(hh[, .(nhCode, data_year, la_roster = living_arrangement, xzc12, countyn,
                   county_year, hdds12, ln_income, any_elder_80, n_elderly)],
            la_res, by = c("nhCode","data_year"), all.x = TRUE)
ag <- merge(ag, la_obs, by = c("nhCode","data_year"), all.x = TRUE)

agree <- data.table(
  comparison = c("resident (>=180 days at home) vs roster, all elder households",
                 "resident vs roster, cohabit/threegen subsample",
                 "48h-observed vs roster, all elder households",
                 "48h-observed vs roster, cohabit/threegen subsample"),
  agreement = c(ag[!is.na(la_resident), mean(la_roster == la_resident)],
                ag[la_roster %in% c("cohabit_nonelder","threegen") & !is.na(la_resident),
                   mean(la_roster == la_resident)],
                ag[!is.na(la_observed), mean(la_roster == la_observed)],
                ag[la_roster %in% c("cohabit_nonelder","threegen") & !is.na(la_observed),
                   mean(la_roster == la_observed)]),
  n = c(ag[!is.na(la_resident), .N],
        ag[la_roster %in% c("cohabit_nonelder","threegen") & !is.na(la_resident), .N],
        ag[!is.na(la_observed), .N],
        ag[la_roster %in% c("cohabit_nonelder","threegen") & !is.na(la_observed), .N]))
wtab(agree, "table27_resident_agreement.csv")

# A-line under each classification -------------------------------------------
aline_by <- function(lav, lab) {
  d <- ag[get(lav) %in% c("cohabit_nonelder","threegen")]
  d[, treat := as.integer(get(lav) == "threegen")]
  m <- feols(as.formula(paste0("hdds12 ~ treat + ", CTRL, " | county_year")),
             data = d, cluster = ~xzc12)
  tidy_fe(m, "^treat")[, spec := lab]
}
t27b <- rbindlist(list(
  aline_by("la_roster",   "A-line, roster classification (headline)"),
  aline_by("la_resident", "A-line, resident-based (>=180 days at home)"),
  aline_by("la_observed", "A-line, 48h-observed members")), fill = TRUE)

# B-line elder gap under resident/observed threegen ---------------------------
bl <- fread(file.path(DIR_DERIV, "bline_sample.csv"), colClasses = list(character = c("nhCode","pid","xzc12")))
bl[, `:=`(fgds10 = num(fgds10), female = num(female), elder = as.integer(elderly == 1))]
bl[, dah := pmin(num(days_at_home), 365)]
bl <- merge(bl, la_res, by = c("nhCode","data_year"), all.x = TRUE)
bl <- merge(bl, la_obs, by = c("nhCode","data_year"), all.x = TRUE)
fit_b <- function(d, tg_var, lab) {
  d <- d[!is.na(fgds10) & !is.na(female)]
  d[, threegen := as.integer(get(tg_var) == "threegen")]
  m <- feols(fgds10 ~ elder + elder:threegen + female | hh_id, data = d, cluster = ~xzc12)
  tidy_fe(m, "elder")[, spec := lab]
}
bl[, la_roster := living_arrangement]
t27b <- rbind(t27b,
  fit_b(bl, "la_roster",   "B-line elder gap, roster threegen (headline)"),
  fit_b(bl, "la_resident", "B-line elder gap, resident-based threegen"),
  fit_b(bl[is.na(dah) | dah >= 180], "la_roster",
        "B-line elder gap, members >=180 days at home only"), fill = TRUE)
wtab(t27b, "table27b_resident_main_results.csv")

writeLines(c("# Measurement robustness (audit items #1-#2)", "",
  "## Scale-free A-line outcomes (table26)",
  paste(capture.output(print(t26[, .(spec, est, se, p, n)])), collapse = "\n"), "",
  "## Roster vs resident/observed living-arrangement agreement (table27)",
  paste(capture.output(print(agree)), collapse = "\n"), "",
  "## Main results under resident/observed classifications (table27b)",
  paste(capture.output(print(t27b[, .(spec, term, est, se, p, n)])), collapse = "\n"), "",
  "Interpretation: household HDDS-12 is partly an observation-scale object;",
  "the scale-free outcomes bound how much of the three-generation association",
  "survives once 'more members recorded' is neutralised. The resident/observed",
  "classifications guard against roster members who are registered but absent."),
  file.path(DIR_REP, "measurement_robustness_summary.md"))
cat("MEASUREMENT ROBUSTNESS OK\n")
print(t26[, .(spec, est, se, p)]); print(agree); print(t27b[, .(spec, term, est, p)])
