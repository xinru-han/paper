# =============================================================================
# 10_robustness.R — T-robust battery (proposal §9):
# corridor widths, terrain-augmented conditioning (slope/TRI), Poisson counts,
# winsor off, drop near-county-seat villages, survey years separately,
# county clustering + wild cluster bootstrap on the primary RF, BH-FDR family.
# =============================================================================
source("/root/data/Paper/食物消费数据/paper3-foodenv/code/00_setup.R")
con <- log_open("10_robustness.log")

pers <- fread(file.path(DIR_DERIV, "p3_person.csv"), colClasses = list(character = c("xzc12","nhCode")))
pers[, county_id := substr(xzc12, 1, 6)]
XC <- c(XI, XH, ZV)
rows <- list()
add <- function(label, m, term = IV_RF) {
  ct <- coeftable(m)
  if (!term %in% rownames(ct)) return(invisible(NULL))
  a <- ct[term, ]
  rows[[length(rows) + 1]] <<- data.table(spec = label, term = term,
                                          b = a[1], se = a[2], p = a[4], n = m$nobs)
}

# R1 corridor widths (reduced form)
for (km in c(1, 2, 5))
  add(sprintf("RF fgds10, detour_town_%dkm", km),
      feols(rhs("fgds10", c(sprintf("detour_town_%dkm", km), XC)), pers, cluster = ~xzc12),
      sprintf("detour_town_%dkm", km))

# R2 terrain-augmented conditioning (slope/TRI added; instrument partially absorbed)
add("RF fgds10 + slope/TRI controls",
    feols(rhs("fgds10", c(IV_RF, XI, XH, ZV_TERR)), pers, cluster = ~xzc12))

# R3 county-detour exposure
add("RF fgds10, detour_county_5km",
    feols(rhs("fgds10", c("detour_county_5km", XC)), pers, cluster = ~xzc12), "detour_county_5km")

# R4 Poisson for count outcomes
for (y in c("fgds10", "fvs")) {
  m <- fepois(rhs(y, c(IV_RF, XC)), pers[!is.na(get(y)) & get(y) >= 0], cluster = ~xzc12)
  add(sprintf("Poisson %s", y), m)
}

# R5 drop villages within 5km straight of the county seat
sub <- pers[exp(ln_dist_county) - 1 > 5]
add("RF fgds10, drop <5km from county seat",
    feols(rhs("fgds10", c(IV_RF, XC)), sub, cluster = ~xzc12))

# R6 survey years separately
for (yy in c(2023, 2024))
  add(sprintf("RF fgds10, %d only", yy),
      feols(rhs("fgds10", c(IV_RF, XC)), pers[data_year == yy], cluster = ~xzc12))

# R7 county clustering + wild cluster bootstrap (63 clusters)
m_cty <- feols(rhs("fgds10", c(IV_RF, XC)), pers, cluster = ~county_id)
add("RF fgds10, county cluster", m_cty)
# WCB (Rademacher, null imposed), from-scratch as in paper2 script 14
wcb_p <- local({
  d <- pers[!is.na(fgds10)]
  fr <- as.formula(paste("fgds10 ~", paste(XC, collapse = "+"), "| county_year"))
  ff <- as.formula(paste("fgds10 ~", IV_RF, "+", paste(XC, collapse = "+"), "| county_year"))
  m_r <- feols(fr, d); fit_r <- predict(m_r, newdata = d)
  res_r <- d$fgds10 - fit_r
  keep <- is.finite(fit_r) & is.finite(res_r)
  m_f <- feols(ff, d, cluster = ~county_id)
  t_obs <- coeftable(m_f)[IV_RF, 3]
  cl <- d$county_id; ug <- unique(cl[keep])
  B <- 999; t_star <- numeric(B)
  bf <- as.formula(paste(".ystar ~", IV_RF, "+", paste(XC, collapse = "+"), "| county_year"))
  for (b in seq_len(B)) {
    w <- setNames(sample(c(-1, 1), length(ug), replace = TRUE), ug)
    d[, .ystar := fit_r + res_r * w[cl]]
    fb <- tryCatch(feols(bf, d[keep], cluster = ~county_id), error = function(e) NULL)
    t_star[b] <- if (is.null(fb)) NA else coeftable(fb)[IV_RF, 3]
  }
  t_star <- t_star[is.finite(t_star)]
  (1 + sum(abs(t_star) >= abs(t_obs))) / (1 + length(t_star))
})
rows[[length(rows) + 1]] <- data.table(spec = "RF fgds10, WCB-county p (B=999)",
                                       term = IV_RF, b = NA, se = NA, p = wcb_p, n = NA)

# R8 BH-FDR across the main outcome family (RF p-values)
fam <- sapply(c("fgds10", "fvs", "hdds12"), function(y)
  coeftable(feols(rhs(y, c(IV_RF, XC)), pers[!is.na(get(y))], cluster = ~xzc12))[IV_RF, 4])
fdr <- p.adjust(fam, "BH")
for (i in seq_along(fam))
  rows[[length(rows) + 1]] <- data.table(spec = paste0("BH-FDR ", names(fam)[i]),
                                         term = IV_RF, b = NA, se = NA, p = fdr[i], n = NA)

t12 <- rbindlist(rows)
wtab(t12, "t12_robustness.csv")
print(t12, digits = 3)
log_close(con)
