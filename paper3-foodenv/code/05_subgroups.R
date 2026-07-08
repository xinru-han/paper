# =============================================================================
# 05_subgroups.R — T4: women 15-49 (MDD-W), children 6-59m (CDDS), elderly,
# DBI variety. RF (primary) + 2SLS per subgroup. Gram families stay sealed.
# =============================================================================
source("/root/data/Paper/食物消费数据/paper3-foodenv/code/00_setup.R")
con <- log_open("05_subgroups.log")

pers <- fread(file.path(DIR_DERIV, "p3_person.csv"), colClasses = list(character = c("xzc12","nhCode")))
XC <- c(XI, XH, ZV)
XCnoage <- c("female_i", XH, ZV)   # for subgroups defined by age

run_one <- function(d, y, x = XC, label) {
  d <- d[!is.na(get(y))]
  if (nrow(d) < 50) return(data.table(subgroup = label, outcome = y, n = nrow(d)))
  m_rf <- feols(rhs(y, c(IV_RF, x)), d, cluster = ~xzc12)
  f2 <- as.formula(paste(y, "~", paste(x, collapse = "+"), "| county_year |", TREAT, "~", IV_2SLS))
  m_iv <- tryCatch(feols(f2, d, cluster = ~xzc12), error = function(e) NULL)
  a <- coeftable(m_rf)[IV_RF, ]
  if (!is.null(m_iv)) {
    cc <- coeftable(m_iv)[paste0("fit_", TREAT), ]
    kpF <- tryCatch(fitstat(m_iv, "ivwald1")$ivwald1$stat, error = function(e) NA_real_)
  } else { cc <- rep(NA_real_, 4); kpF <- NA_real_ }
  data.table(subgroup = label, outcome = y,
             rf_b = a[1], rf_se = a[2], rf_p = a[4],
             iv_b = cc[1], iv_se = cc[2], kp_F = kpF,
             n = m_rf$nobs, mean_y = mean(d[[y]], na.rm = TRUE))
}

out <- list(
  run_one(pers[mddw_elig == 1], "mddw",   XCnoage, "women 15-49 (MDD-W>=5, LPM)"),
  run_one(pers[mddw_elig == 1], "fgds10", XCnoage, "women 15-49"),
  run_one(pers[cdds_elig_659 == 1], "cdds8", XCnoage, "children 6-59m (CDDS-8, CAUTION n~100)"),
  run_one(pers[cdds_elig_659 == 1], "cdds7", XCnoage, "children 6-59m (CDDS-7)"),
  run_one(pers[elderly == 1], "fgds10", XCnoage, "elderly 60+ (P2 crossref)"),
  run_one(pers[elderly == 0 & child == 0], "fgds10", XCnoage, "non-elderly adults"),
  run_one(pers, "dbi_variety", XC, "all (DBI-16 variety subscore)")
)
t4 <- rbindlist(out, fill = TRUE)
wtab(t4, "t4_subgroups.csv")
print(t4, digits = 3)
cat("\nNote: gram-based families (mddwg_*, dbiv_*) sealed per P2 Task-3 audit FAIL.\n")
log_close(con)
