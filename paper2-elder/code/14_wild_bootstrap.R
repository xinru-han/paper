# =============================================================================
# 14_wild_bootstrap.R — few-cluster inference via wild cluster bootstrap-t
# (Cameron-Gelbach-Miller WCR, Rademacher weights, null imposed) for the two
# headline coefficients: A-line three-gen HDDS effect and B-line elder gap/theta.
# Motivation: village-clustered CRVE with village x year FE can understate SEs
# when the effective number of clusters is modest. WCB-t is the standard remedy.
# No external package (fwildclusterboot unavailable); implemented from scratch.
# Outputs: table20_wild_cluster_bootstrap.csv
# =============================================================================
source("/root/data/Paper/食物消费数据/paper2-elder/code/00_setup.R")
suppressPackageStartupMessages({ library(fixest); library(data.table) })

# Generic wild cluster bootstrap-t for one target coefficient in a feols model.
# Imposes the null (H0: beta_target = 0) by refitting the model without the
# target regressor, then perturbing restricted residuals by cluster-level signs.
wcb_t <- function(full_formula, restricted_formula, target, data, cluster,
                  B = 999, seed = 20260707) {
  set.seed(seed)
  d <- copy(data)
  yvar <- all.vars(full_formula)[1]
  m_full <- feols(full_formula, data = d, cluster = cluster)
  ct <- coeftable(m_full)
  if (!target %in% rownames(ct)) return(NULL)
  t_obs <- ct[target, "t value"]
  b_obs <- ct[target, "Estimate"]; se_obs <- ct[target, "Std. Error"]
  m_r <- feols(restricted_formula, data = d, cluster = cluster)
  # predict on the FULL data frame so length matches nrow(d) even when the fit
  # drops NA rows / FE singletons; residuals are y - fitted on the kept rows.
  fit_r <- predict(m_r, newdata = d)
  res_r <- d[[yvar]] - fit_r
  keep  <- is.finite(fit_r) & is.finite(res_r)
  cl <- as.character(d[[all.vars(cluster)]])
  ug <- unique(cl[keep])
  # rebuild the full formula with .ystar as LHS, preserving the fixest "| FE" RHS
  # (update() mangles the pipe part, which silently NA'd every refit).
  rhs_txt <- paste(deparse(full_formula[[3]]), collapse = " ")
  boot_formula <- as.formula(paste(".ystar ~", rhs_txt))
  t_star <- numeric(B)
  for (b in seq_len(B)) {
    w <- setNames(sample(c(-1, 1), length(ug), replace = TRUE), ug)  # Rademacher
    d[, .ystar := fit_r + res_r * w[cl]]
    fb <- tryCatch(feols(boot_formula, data = d[keep], cluster = cluster),
                   error = function(e) NULL)
    if (is.null(fb)) { t_star[b] <- NA; next }
    cb <- coeftable(fb)
    if (!target %in% rownames(cb)) { t_star[b] <- NA; next }
    t_star[b] <- (cb[target, "Estimate"] - 0) / cb[target, "Std. Error"]
  }
  t_star <- t_star[is.finite(t_star)]
  p_wcb <- (1 + sum(abs(t_star) >= abs(t_obs))) / (1 + length(t_star))
  data.table(term = target, est = b_obs, se_crve = se_obs, t_crve = t_obs,
             p_crve = ct[target, "Pr(>|t|)"], p_wcb = p_wcb,
             n_clusters = length(ug), B = length(t_star))
}

out <- list()

# ---- A line: three-gen HDDS effect (county x year FE, village clusters) -------
hh <- fread(file.path(DIR_DERIV, "hh_analysis.csv"), colClasses = list(character = c("nhCode","xzc12")))
hh <- hh[living_arrangement %in% c("cohabit_nonelder","threegen")]
hh[, `:=`(hdds12 = num(hdds12), treat = as.integer(living_arrangement == "threegen"),
          county_year = paste(countyn, data_year),
          ln_income = num(ln_income), any_elder_80 = num(any_elder_80), n_elderly = num(n_elderly))]
out$aline <- wcb_t(
  full_formula       = hdds12 ~ treat + ln_income + any_elder_80 + n_elderly | county_year,
  restricted_formula = hdds12 ~ ln_income + any_elder_80 + n_elderly | county_year,
  target = "treat", data = hh, cluster = ~xzc12)
if (!is.null(out$aline)) out$aline[, spec := "A-line three-gen HDDS (county-year FE)"]

# ---- B line: elder gap and three-gen interaction (household FE) ---------------
bl <- fread(file.path(DIR_DERIV, "bline_sample.csv"), colClasses = list(character = c("nhCode","pid","xzc12")))
bl[, `:=`(fgds10 = num(fgds10), elder = as.integer(elderly == 1),
          threegen = as.integer(living_arrangement == "threegen"),
          female = num(female))]
bl <- bl[!is.na(fgds10) & !is.na(female)]
out$bline_elder <- wcb_t(
  full_formula       = fgds10 ~ elder + elder:threegen + female | hh_id,
  restricted_formula = fgds10 ~ elder:threegen + female | hh_id,
  target = "elder", data = bl, cluster = ~xzc12)
if (!is.null(out$bline_elder)) out$bline_elder[, spec := "B-line elder gap (household FE)"]

out$bline_theta <- wcb_t(
  full_formula       = fgds10 ~ elder + elder:threegen + female | hh_id,
  restricted_formula = fgds10 ~ elder + female | hh_id,
  target = "elder:threegen", data = bl, cluster = ~xzc12)
if (!is.null(out$bline_theta)) out$bline_theta[, spec := "B-line three-gen interaction (household FE)"]

t20 <- rbindlist(out[!sapply(out, is.null)], fill = TRUE)
wtab(t20, "table20_wild_cluster_bootstrap.csv")
cat("WILD BOOTSTRAP OK\n"); print(t20[, .(spec, est, p_crve, p_wcb, n_clusters)])
