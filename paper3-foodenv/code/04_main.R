# =============================================================================
# 04_main.R — T3 main results under the D1 architecture:
#   (a) PRIMARY  reduced form: y ~ detour_town_5km + X | county FE
#   (b) OLS      y ~ retail_pc1 + X | county FE
#   (c) 2SLS     retail_pc1 <- detour_town_1km (best pre-registered F) + AR CI
# Inference: village cluster (main) / county cluster / Conley 50km / WCB-county.
# Plus t3c: "LATE mosaic" across IV corridor widths (replaces MTE per prereg).
# Outputs: t3_main.csv, t3b_inference.csv, t3c_late_mosaic.csv
# =============================================================================
source("/root/data/Paper/食物消费数据/paper3-foodenv/code/00_setup.R")
con <- log_open("04_main.log")

pers <- fread(file.path(DIR_DERIV, "p3_person.csv"), colClasses = list(character = c("xzc12","nhCode")))
# village coordinates for Conley SEs only (never written to outputs)
crd <- fread(F_CORR(5))[, .(xzc12 = as.character(xzc12), lat = num(vil_wgs_lat), lon = num(vil_wgs_lng))]
pers <- merge(pers, crd, by = "xzc12", all.x = TRUE)
pers[, county_id := substr(xzc12, 1, 6)]
XC <- c(XI, XH, ZV)

# ---- Anderson–Rubin CI by grid inversion (single endog, single IV) ----------
ar_ci <- function(dt, y, level = .95, brange = NULL, ngrid = 401) {
  f0 <- as.formula(paste0("I(", y, " - b0*", TREAT, ") ~ ", IV_2SLS, " + ",
                          paste(XC, collapse = "+"), " | county_year"))
  tstat <- function(b0) {
    dtt <- copy(dt); dtt[, b0 := b0]
    m <- feols(f0, dtt, cluster = ~xzc12)
    coeftable(m)[IV_2SLS, 3]
  }
  if (is.null(brange)) brange <- c(-6, 6)
  bs <- seq(brange[1], brange[2], length.out = ngrid)
  ts <- vapply(bs, tstat, numeric(1))
  crit <- qnorm(1 - (1 - level)/2)
  acc <- bs[abs(ts) < crit]
  if (!length(acc)) return(c(NA, NA, FALSE))
  # detect unbounded CI (acceptance region touching the grid edge)
  unb <- (min(acc) == bs[1] || max(acc) == bs[ngrid])
  c(min(acc), max(acc), unb)
}

res <- list(); inf <- list()
for (y in c("fgds10", "fvs", "hdds12")) {
  d <- pers[!is.na(get(y))]
  # (a) reduced form — PRIMARY
  m_rf <- feols(rhs(y, c(IV_RF, XC)), d, cluster = ~xzc12)
  # (b) OLS
  m_ols <- feols(rhs(y, c(TREAT, XC)), d, cluster = ~xzc12)
  # (c) 2SLS
  f2 <- as.formula(paste(y, "~", paste(XC, collapse = "+"),
                         "| county_year |", TREAT, "~", IV_2SLS))
  m_iv <- feols(f2, d, cluster = ~xzc12)
  kpF <- tryCatch(fitstat(m_iv, "ivwald1")$ivwald1$stat, error = function(e) NA_real_)
  ar  <- ar_ci(d, y)

  g <- function(m, term) { ct <- coeftable(m); ct[term, ] }
  a <- g(m_rf, IV_RF); b <- g(m_ols, TREAT); cc <- g(m_iv, paste0("fit_", TREAT))
  res[[y]] <- data.table(outcome = y,
    rf_b = a[1], rf_se = a[2], rf_p = a[4],
    ols_b = b[1], ols_se = b[2], ols_p = b[4],
    iv_b = cc[1], iv_se = cc[2], iv_p = cc[4], kp_F = kpF,
    ar_lo = ar[1], ar_hi = ar[2], ar_unbounded = as.logical(ar[3]),
    n = m_rf$nobs, mean_y = mean(d[[y]], na.rm = TRUE))

  # ---- inference battery on the PRIMARY reduced form ----
  m_cty <- feols(rhs(y, c(IV_RF, XC)), d, cluster = ~county_id)
  dcc <- d[!is.na(lat)]
  m_con <- feols(rhs(y, c(IV_RF, XC)), dcc,
                 vcov = vcov_conley(lat = "lat", lon = "lon", cutoff = 50))
  inf[[y]] <- data.table(outcome = y, b = a[1],
    se_village = a[2], p_village = a[4],
    se_county = g(m_cty, IV_RF)[2], p_county = g(m_cty, IV_RF)[4],
    se_conley50 = g(m_con, IV_RF)[2], p_conley50 = g(m_con, IV_RF)[4])
}
t3 <- rbindlist(res); wtab(t3, "t3_main.csv")
t3b <- rbindlist(inf); wtab(t3b, "t3b_inference.csv")
print(t3[, .(outcome, rf_b, rf_se, rf_p, ols_b, iv_b, iv_se, kp_F, ar_lo, ar_hi, n)], digits = 3)

# ---- t3c LATE mosaic across corridor widths (MTE replacement) ---------------
mos <- list()
for (km in c(1, 2, 5)) for (y in c("fgds10", "fvs", "hdds12")) {
  ivv <- sprintf("detour_town_%dkm", km)
  f2 <- as.formula(paste(y, "~", paste(XC, collapse = "+"), "| county_year |", TREAT, "~", ivv))
  m <- feols(f2, pers[!is.na(get(y))], cluster = ~xzc12)
  kpF <- tryCatch(fitstat(m, "ivwald1")$ivwald1$stat, error = function(e) NA_real_)
  ct <- coeftable(m)[paste0("fit_", TREAT), ]
  mos[[length(mos) + 1]] <- data.table(outcome = y, corridor_km = km,
    late_b = ct[1], late_se = ct[2], kp_F = kpF, n = m$nobs)
}
t3c <- rbindlist(mos); wtab(t3c, "t3c_late_mosaic.csv")
log_close(con)
