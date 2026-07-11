# ============================================================================
# v2 shared library: censored EASI demand system with CRE/Mundlak two-step,
# fixed-weight Stone deflation, FGLS, cluster inference and elasticities.
# All estimators accept household frequency weights so that the pairs cluster
# bootstrap can run without duplicating rows.
# ============================================================================

suppressPackageStartupMessages(library(data.table))

CODES9  <- sprintf("G%02d", 1:9)
GROUPS9 <- c("G01_主食","G02_食用油","G03_蔬菜","G04_水果","G05_猪肉",
             "G06_禽类及其他肉类","G07_牛羊肉","G08_海鲜","G09_乳制品")
names(GROUPS9) <- CODES9
Z_COLS <- c("z_cpi","z_covid","z_holiday","z_temp","z_precip","z_wholesale")
DEMO_COLS <- c("low_income","elderly_household","large_family")
MONTH_D <- paste0("m_", sprintf("%02d", 2:12))
YEAR_D  <- c("yr_2021","yr_2022")
EXTRA_BASE_COLS <- character(0)

# ---------------------------------------------------------------------------
# Wide data preparation
# ---------------------------------------------------------------------------
make_wide <- function(panel, price_col = "lp_ext") {
  panel <- panel[is.finite(get(price_col)) & total_food_spend_month > 0]
  panel[, group_code := substr(food_group10, 1, 3)]
  panel[, covid_log := log1p(covid_daily_new_sum)]
  panel[, precip_log := log1p(pmax(precipitation_mm_sum, 0))]
  id_cols <- c("ID","year_month","Province","Family_Type","Family_Size","Family_Income",
               "family_size_midpoint","family_size_oecd","total_food_spend_month",
               "total_food_spend_pc_month","log_total_food_spend_pc_month","fold",
               "income_group_order","low_income","elderly_household","large_family",
               "cpi_yoy_prev_year_100","covid_log","holiday_days","temp_avg_c_mean",
               "precip_log","wholesale_agri_200_mean","nut_spend_month")
  bw <- unique(panel[, ..id_cols], by = c("ID","year_month"))
  cast_one <- function(vc, pfx) {
    x <- dcast(panel, ID + year_month ~ group_code, value.var = vc)
    setnames(x, CODES9, paste0(pfx, "_", CODES9), skip_absent = TRUE)
    x
  }
  cast_list <- list(bw, cast_one("budget_share","w"), cast_one("positive_purchase","pos"),
                    cast_one(price_col,"lp"))
  # carry group-specific purchase-cycle exclusion regressors if present in panel
  pcyc_present <- intersect(PCYC_BASE, names(panel))
  for (v in pcyc_present) cast_list[[length(cast_list) + 1]] <- cast_one(v, v)
  wide <- Reduce(function(a, b) merge(a, b, by = c("ID","year_month"), all.x = TRUE), cast_list)
  setorder(wide, ID, year_month)
  zero_fill <- c(paste0("w_",CODES9), paste0("pos_",CODES9))
  for (v in pcyc_present) zero_fill <- c(zero_fill, paste0(v, "_", CODES9))
  for (v in zero_fill) if (v %in% names(wide)) wide[is.na(get(v)), (v) := 0]
  lp_cols <- paste0("lp_", CODES9)
  wide <- wide[rowSums(!is.finite(as.matrix(wide[, ..lp_cols]))) == 0]
  # scaled covariates
  sc <- c(cpi_yoy_prev_year_100="z_cpi", covid_log="z_covid", holiday_days="z_holiday",
          temp_avg_c_mean="z_temp", precip_log="z_precip", wholesale_agri_200_mean="z_wholesale")
  for (v in names(sc)) {
    m <- mean(wide[[v]], na.rm = TRUE); s <- sd(wide[[v]], na.rm = TRUE)
    if (!is.finite(s) || s == 0) s <- 1
    wide[, (sc[[v]]) := (get(v) - m) / s]
  }
  wide[, month := substr(year_month, 6, 7)]
  wide[, yr := substr(year_month, 1, 4)]
  for (mm in sprintf("%02d", 2:12)) wide[, paste0("m_", mm) := as.integer(month == mm)]
  for (yy in c("2021","2022")) wide[, paste0("yr_", yy) := as.integer(yr == yy)]
  wide
}

# Fixed-weight Stone deflator: province-month mean shares (weighted)
compute_stone_weights <- function(wide, wt = NULL) {
  if (is.null(wt)) wt <- rep(1, nrow(wide))
  sw <- wide[, {
    W <- wt[.I]
    lapply(.SD, function(col) sum(col * W) / sum(W))
  }, by = .(Province, year_month), .SDcols = paste0("w_", CODES9)]
  setnames(sw, paste0("w_", CODES9), paste0("sw_", CODES9))
  sw
}

# Derive y, y2, relative prices; log_x_col allows equivalence-scale variants
derive_vars <- function(wide, stone_w, omit = "G03", log_x_col = "log_total_food_spend_pc_month") {
  sw_cols <- paste0("sw_", CODES9)
  # order-preserving join (merge() would re-sort rows and break weight alignment)
  wide[stone_w, (sw_cols) := mget(paste0("i.", sw_cols)), on = c("Province","year_month")]
  lp <- as.matrix(wide[, paste0("lp_", CODES9), with = FALSE])
  sw <- as.matrix(wide[, ..sw_cols])
  wide[, stone_idx := rowSums(sw * lp)]
  wide[, y_easi := get(log_x_col) - stone_idx]
  wide[, y_easi2 := y_easi^2]
  eq_codes <- setdiff(CODES9, omit)
  for (cc in eq_codes) wide[, paste0("r_", cc) := get(paste0("lp_", cc)) - get(paste0("lp_", omit))]
  wide
}

# Household (CRE/Mundlak) means of time-varying regressors — weighted means are
# invariant to frequency weights within household, so computed unweighted once.
add_mundlak <- function(wide, omit = "G03") {
  eq_codes <- setdiff(CODES9, omit)
  r_cols <- paste0("r_", eq_codes)
  wide[, mean_y_hh := mean(y_easi), by = ID]
  for (rc in r_cols) wide[, paste0("mn_", rc) := mean(get(rc)), by = ID]
  wide
}

# ---------------------------------------------------------------------------
# Probit (own Newton-Raphson with frequency weights)
# ---------------------------------------------------------------------------
probit_newton <- function(X, y, wt, beta0 = NULL, maxit = 30, tol = 1e-9) {
  p <- ncol(X)
  beta <- if (is.null(beta0)) c(qnorm(pmin(pmax(weighted.mean(y, wt), 1e-4), 1-1e-4)), rep(0, p-1)) else beta0
  dev_old <- Inf
  for (it in seq_len(maxit)) {
    xb <- as.numeric(X %*% beta)
    xb <- pmin(pmax(xb, -8), 8)
    Phi <- pmin(pmax(pnorm(xb), 1e-10), 1 - 1e-10)
    phi <- dnorm(xb)
    # score and expected information (Fisher scoring)
    u <- fifelse(y == 1L, phi / Phi, -phi / (1 - Phi))
    Wd <- wt * phi^2 / (Phi * (1 - Phi))
    g <- as.numeric(crossprod(X, wt * u))
    H <- crossprod(X, X * Wd)
    step <- tryCatch(solve(H, g), error = function(e) solve(H + diag(1e-8, p), g))
    beta <- beta + step
    dev <- -2 * sum(wt * (y * log(Phi) + (1 - y) * log(1 - Phi)))
    if (is.finite(dev_old) && abs(dev_old - dev) < tol * (abs(dev) + 1)) break
    dev_old <- dev
  }
  list(beta = beta, iterations = it, deviance = dev_old)
}

# Purchase-cycle exclusion regressors (SY participation stage). These are the
# group's OWN lagged purchase-timing variables (built by add_purchase_cycle_vars
# in pcyc_lib_v2.R and cast to wide as <base>_<code>); excluded from the
# consumption equation. They sharpen the weak staple/dairy participation probits
# and absorb the stock-up-timing (extensive) margin that otherwise inflates the
# monthly own-price elasticity of storable groups. Active whenever the panel
# carries the columns (script 30 builds them); harmless if absent.
PCYC_BASE <- c("pcyc_bought_lag1","pcyc_recency","pcyc_nohist")

build_probit_X <- function(wide, omit = "G03", code = NULL) {
  eq_codes <- setdiff(CODES9, omit)
  r_cols <- paste0("r_", eq_codes)
  mn_cols <- paste0("mn_", r_cols)
  cols <- c("y_easi", r_cols, DEMO_COLS, Z_COLS, MONTH_D, YEAR_D, "mean_y_hh", mn_cols)
  # group-specific purchase-cycle exclusion regressors, if activated & present
  if (!is.null(code) && length(PCYC_BASE)) {
    pc <- paste0(PCYC_BASE, "_", code)
    pc <- pc[pc %in% names(wide)]
    cols <- c(cols, pc)
  }
  X <- cbind(const = 1, as.matrix(wide[, ..cols]))
  storage.mode(X) <- "double"
  X
}

fit_probits <- function(wide, wt, omit = "G03", beta0_list = NULL) {
  betas <- list(); stats <- list()
  for (code in CODES9) {
    X <- build_probit_X(wide, omit, code = code)
    y <- wide[[paste0("pos_", code)]]
    b0 <- if (!is.null(beta0_list)) beta0_list[[code]] else NULL
    fit <- probit_newton(X, y, wt, beta0 = b0)
    betas[[code]] <- fit$beta
    xb <- pmin(pmax(as.numeric(X %*% fit$beta), -8), 8)
    Phi <- pmin(pmax(pnorm(xb), 1e-6), 1 - 1e-6)
    llf <- sum(wt * (y * log(Phi) + (1 - y) * log(1 - Phi)))
    p0 <- weighted.mean(y, wt)
    lln <- sum(wt) * (p0 * log(p0) + (1 - p0) * log(1 - p0))
    # weighted AUC via rank statistic
    r <- frank(xb, ties.method = "average")
    n1 <- sum(wt * y); n0 <- sum(wt * (1 - y))
    auc <- (sum(wt * y * r) - n1 * (n1 + 1) / 2 / mean(wt)) / (n1 * n0) * mean(wt)
    stats[[code]] <- data.table(code = code, positive_rate = p0,
                                mean_pred = weighted.mean(Phi, wt),
                                brier = weighted.mean((y - Phi)^2, wt),
                                pseudo_r2 = 1 - llf / lln, auc = auc,
                                iterations = fit$iterations)
  }
  list(betas = betas, stats = rbindlist(stats), X_cols = colnames(X))
}

predict_probits <- function(wide, betas, omit = "G03") {
  Phi <- matrix(NA_real_, nrow(wide), 9, dimnames = list(NULL, CODES9))
  phi <- Phi
  for (code in CODES9) {
    X <- build_probit_X(wide, omit, code = code)
    xb <- pmin(pmax(as.numeric(X %*% betas[[code]]), -8), 8)
    Phi[, code] <- pmin(pmax(pnorm(xb), 1e-6), 1 - 1e-6)
    phi[, code] <- dnorm(xb)
  }
  list(Phi = Phi, phi = phi)
}

# ---------------------------------------------------------------------------
# Constrained SY-EASI system (8 equations, symmetric price parameterization)
# ---------------------------------------------------------------------------
# Parameter layout:
#   per-equation base terms (const, y, y2, demos, z, month FE, year FE,
#   Mundlak means)                                          : 8 x n_base
#   shared symmetric price coefficients b_{ij}              : 36
#   shared symmetric y x price coefficients c_{ij}          : 36
#   [optional A(z)] symmetric price x demo_d, d = 1..3      : 3 x 36
#   per-equation sigma (SY correction loading on phi_g)     : 8
# y2p = TRUE replaces the y x price interaction with y^2 x price. This is an
# EASI functional-form variant ("EASI-y2p"), NOT Banks-Blundell-Lewbel QUAIDS
# (no lambda/b(p) structure); it must not be labelled QUAIDS anywhere.
system_layout <- function(omit = "G03", az = FALSE, y2p = FALSE) {
  eq_codes <- setdiff(CODES9, omit)
  G <- length(eq_codes)
  base_terms <- c("const","y_easi","y_easi2", DEMO_COLS, Z_COLS, MONTH_D, YEAR_D,
                  "mean_y_hh", paste0("mn_r_", eq_codes), EXTRA_BASE_COLS)
  up <- which(upper.tri(matrix(0, G, G), diag = TRUE), arr.ind = TRUE)
  pair_names <- paste0("p", up[,1], "_", up[,2])
  pair_index <- matrix(NA_integer_, G, G)
  for (k in seq_len(nrow(up))) { pair_index[up[k,1], up[k,2]] <- k; pair_index[up[k,2], up[k,1]] <- k }
  az_dims <- if (az) DEMO_COLS else character(0)
  term_names <- c(unlist(lapply(eq_codes, function(cc) paste(cc, base_terms, sep = "__"))),
                  paste0("bp__", pair_names),
                  paste0("cyp__", pair_names),
                  unlist(lapply(az_dims, function(d) paste0("az_", d, "__", pair_names))),
                  paste0("sigma__", eq_codes))
  nb <- length(base_terms); np <- nrow(up)
  off_bp <- G * nb
  off_cyp <- off_bp + np
  off_az <- off_cyp + np
  off_sigma <- off_az + length(az_dims) * np
  list(eq_codes = eq_codes, G = G, base_terms = base_terms, up = up,
       pair_index = pair_index, term_names = term_names, nb = nb, np = np,
       off_bp = off_bp, off_cyp = off_cyp, off_az = off_az, off_sigma = off_sigma,
       az = az, az_dims = az_dims, y2p = y2p, omit = omit,
       n_par = length(term_names))
}

# Design block for equation g: returns matrix A (n x k_g) and parameter cols
build_Ag <- function(wide, g, lay, Phi, phi) {
  code <- lay$eq_codes[g]
  n <- nrow(wide)
  Bm <- cbind(const = 1, as.matrix(wide[, lay$base_terms[-1], with = FALSE]))
  R <- as.matrix(wide[, paste0("r_", lay$eq_codes), with = FALSE])
  # symmetric mapping: column for pair k in eq g takes value r_j where j pairs with g
  Pm <- matrix(0, n, lay$G)
  for (j in seq_len(lay$G)) Pm[, j] <- R[, j]      # value r_j enters pair (g,j)
  ymult <- if (isTRUE(lay$y2p) || isTRUE(lay$quaids)) wide$y_easi2 else wide$y_easi  # quaids: legacy rds compat
  mult <- Phi[, code]
  blocks <- list(mult * Bm, mult * Pm, mult * (ymult * Pm))
  cols <- list(seq_len(lay$nb) + (g - 1) * lay$nb,
               lay$off_bp + lay$pair_index[g, ],
               lay$off_cyp + lay$pair_index[g, ])
  if (lay$az) {
    for (di in seq_along(lay$az_dims)) {
      zd <- wide[[lay$az_dims[di]]]
      blocks[[length(blocks) + 1]] <- mult * (zd * Pm)
      cols[[length(cols) + 1]] <- lay$off_az + (di - 1) * lay$np + lay$pair_index[g, ]
    }
  }
  blocks[[length(blocks) + 1]] <- matrix(phi[, code], ncol = 1)
  cols[[length(cols) + 1]] <- lay$off_sigma + g
  A <- do.call(cbind, blocks)
  list(A = A, cols = unlist(cols), y = wide[[paste0("w_", code)]])
}

# GLS/FGLS solve. Sigma = NULL -> equation-by-equation OLS weighting (identity).
# Returns coefficients, residual covariance, and optionally xtx inverse.
fit_system <- function(wide, lay, Phi, phi, wt, Sigma = NULL, n_fgls = 2,
                       ridge = 1e-8, keep_xtx_inv = FALSE) {
  n <- nrow(wide); G <- lay$G; P <- lay$n_par
  Ag <- vector("list", G); yg <- vector("list", G); colg <- vector("list", G)
  for (g in seq_len(G)) {
    z <- build_Ag(wide, g, lay, Phi, phi)
    Ag[[g]] <- z$A; yg[[g]] <- z$y; colg[[g]] <- z$cols
  }
  solve_once <- function(Sinv) {
    xtx <- matrix(0, P, P); xty <- numeric(P)
    for (g in seq_len(G)) for (h in seq_len(G)) {
      s <- Sinv[g, h]
      if (abs(s) < 1e-14) next
      xtx[colg[[g]], colg[[h]]] <- xtx[colg[[g]], colg[[h]]] + s * crossprod(Ag[[g]], wt * Ag[[h]])
      xty[colg[[g]]] <- xty[colg[[g]]] + s * as.numeric(crossprod(Ag[[g]], wt * yg[[h]]))
    }
    base_xtx <- xtx
    xscale <- median(abs(diag(base_xtx)), na.rm = TRUE)
    if (!is.finite(xscale) || xscale <= 0) xscale <- 1
    ridge_grid <- max(ridge, ridge * xscale) * 10^(0:10)
    last_err <- NULL
    for (rr in ridge_grid) {
      xtx <- base_xtx
      diag(xtx) <- diag(xtx) + rr
      sol <- tryCatch(solve(xtx, xty), error = function(e) { last_err <<- e; NULL })
      if (!is.null(sol) && all(is.finite(sol))) return(list(beta = as.numeric(sol), xtx = xtx))
    }
    stop(last_err)
  }
  invert_sigma <- function(S) {
    S <- (S + t(S)) / 2
    sscale <- median(abs(diag(S)), na.rm = TRUE)
    if (!is.finite(sscale) || sscale <= 0) sscale <- 1
    ridge_grid <- max(ridge, ridge * sscale) * 10^(0:10)
    last_err <- NULL
    for (rr in ridge_grid) {
      Sinv <- tryCatch(solve(S + diag(rr, nrow(S))), error = function(e) { last_err <<- e; NULL })
      if (!is.null(Sinv) && all(is.finite(Sinv))) return(Sinv)
    }
    stop(last_err)
  }
  resid_cov <- function(beta) {
    E <- matrix(0, n, G)
    for (g in seq_len(G)) E[, g] <- yg[[g]] - as.numeric(Ag[[g]] %*% beta[colg[[g]]])
    S <- crossprod(E, wt * E) / sum(wt)
    list(S = S, E = E)
  }
  if (is.null(Sigma)) {
    fit <- solve_once(diag(G))
    for (it in seq_len(n_fgls)) {
      rc <- resid_cov(fit$beta)
      Sigma <- rc$S
      fit <- solve_once(invert_sigma(Sigma))
    }
  } else {
    fit <- solve_once(invert_sigma(Sigma))
  }
  rc <- resid_cov(fit$beta)
  beta <- fit$beta; names(beta) <- lay$term_names
  out <- list(beta = beta, Sigma = Sigma %||% rc$S, resid = rc$E, colg = colg)
  if (keep_xtx_inv) {
    out$xtx_inv <- solve(fit$xtx)
    out$xtx <- fit$xtx
    out$xty <- as.numeric(fit$xtx %*% fit$beta)
  }
  # cluster scores for sandwich (computed lazily by caller via system_scores)
  out$Ag_dims <- vapply(Ag, ncol, 1L)
  out
}

`%||%` <- function(x, y) if (is.null(x)) y else x

# ---------------------------------------------------------------------------
# Curvature imposition: constrain the symmetric price coefficient block to
# B = -LL' (negative semidefinite). Because the model is linear given B, the
# FGLS criterion concentrates to a quadratic in the bp block with the Schur
# complement as weight; the constrained estimator solves
#   min_L  (b(L))' Sb (b(L)) - 2 (b(L))' sb,  b(L) = vech(-LL')
# by BFGS over the 36 Cholesky elements. Since ww' - diag(w) is NSD under
# adding-up, B NSD delivers a NSD Slutsky matrix at reference prices
# (Lewbel-Pendakur EASI; cf. Moschini 1998, Ryan & Wales 1998).
# Requires fit_system(..., keep_xtx_inv = TRUE).
# ---------------------------------------------------------------------------
impose_curvature <- function(fit, lay, y_lo = NULL, y_hi = NULL) {
  P <- lay$n_par; G <- lay$G; np <- lay$np
  two_point <- !is.null(y_lo) && !is.null(y_hi)
  b_idx <- lay$off_bp + seq_len(np)                  # bp block
  c_idx <- lay$off_cyp + seq_len(np)                 # cyp block
  q_idx <- if (two_point) c(b_idx, c_idx) else b_idx # constrained block
  f_idx <- setdiff(seq_len(P), q_idx)
  X <- fit$xtx; y <- fit$xty
  Xff_inv_Xfq <- solve(X[f_idx, f_idx], X[f_idx, q_idx])
  Xff_inv_yf  <- solve(X[f_idx, f_idx], y[f_idx])
  Sq <- X[q_idx, q_idx] - X[q_idx, f_idx] %*% Xff_inv_Xfq
  sq <- y[q_idx] - as.numeric(X[q_idx, f_idx] %*% Xff_inv_yf)
  Sq <- (Sq + t(Sq)) / 2
  up <- lay$up
  vech_of <- function(B) B[cbind(up[, 1], up[, 2])]
  unvech <- function(v) {
    M <- matrix(0, G, G)
    M[cbind(up[, 1], up[, 2])] <- v; M[cbind(up[, 2], up[, 1])] <- v
    M
  }
  ltri <- which(lower.tri(matrix(0, G, G), diag = TRUE))
  nl <- length(ltri)
  clip_chol <- function(M) {
    e <- eigen((M + t(M)) / 2, symmetric = TRUE)
    d <- pmin(e$values, -1e-6)
    t(chol(-(e$vectors %*% (d * t(e$vectors))) + diag(1e-8, G)))
  }
  if (two_point) {
    # M(y) = B + y C is affine in y, so NSD at y_lo and y_hi implies NSD on
    # the whole interval. Parameterize M(y_lo) = -L1 L1', M(y_hi) = -L2 L2'.
    bc_of <- function(par) {
      L1 <- matrix(0, G, G); L1[ltri] <- par[seq_len(nl)]
      L2 <- matrix(0, G, G); L2[ltri] <- par[nl + seq_len(nl)]
      M1 <- -tcrossprod(L1); M2 <- -tcrossprod(L2)
      Cm <- (M2 - M1) / (y_hi - y_lo)
      Bm <- M1 - y_lo * Cm
      list(B = Bm, C = Cm, v = c(vech_of(Bm), vech_of(Cm)))
    }
    obj <- function(par) {
      v <- bc_of(par)$v
      as.numeric(t(v) %*% Sq %*% v - 2 * sum(v * sq))
    }
    B0 <- unvech(fit$beta[b_idx]); C0 <- unvech(fit$beta[c_idx])
    par0 <- c(clip_chol(B0 + y_lo * C0)[ltri], clip_chol(B0 + y_hi * C0)[ltri])
  } else {
    bc_of <- function(par) {
      L <- matrix(0, G, G); L[ltri] <- par
      Bm <- -tcrossprod(L)
      list(B = Bm, C = NULL, v = vech_of(Bm))
    }
    obj <- function(par) {
      v <- bc_of(par)$v
      as.numeric(t(v) %*% Sq %*% v - 2 * sum(v * sq))
    }
    par0 <- clip_chol(unvech(fit$beta[b_idx]))[ltri]
  }
  op <- optim(par0, obj, method = "BFGS",
              control = list(maxit = 5000, reltol = 1e-14))
  sol <- bc_of(op$par)
  beta_c <- fit$beta
  beta_c[q_idx] <- sol$v
  beta_c[f_idx] <- as.numeric(Xff_inv_yf - Xff_inv_Xfq %*% sol$v)
  names(beta_c) <- lay$term_names
  vh <- fit$beta[q_idx]
  q_unc <- as.numeric(t(vh) %*% Sq %*% vh - 2 * sum(vh * sq))
  eigs <- function(M) if (is.null(M)) NULL else
    sort(eigen((M + t(M)) / 2, symmetric = TRUE, only.values = TRUE)$values,
         decreasing = TRUE)
  list(beta = beta_c, B = sol$B, C = sol$C, converged = op$convergence == 0,
       criterion_gap = op$value - q_unc, two_point = two_point,
       y_lo = y_lo, y_hi = y_hi,
       B_eigen = eigs(sol$B),
       M_lo_eigen = if (two_point) eigs(sol$B + y_lo * sol$C) else NULL,
       M_hi_eigen = if (two_point) eigs(sol$B + y_hi * sol$C) else NULL)
}

# Cluster-robust sandwich covariance of system coefficients (two-step-naive;
# full two-step uncertainty is carried by the pairs cluster bootstrap).
system_cluster_vcov <- function(wide, lay, Phi, phi, wt, beta, Sigma, xtx_inv,
                                cluster = wide$ID) {
  n <- nrow(wide); G <- lay$G; P <- lay$n_par
  Sinv <- solve(Sigma)
  U <- matrix(0, n, G)   # Sinv-weighted residuals
  E <- matrix(0, n, G)
  Ag <- vector("list", G); colg <- vector("list", G)
  for (g in seq_len(G)) {
    z <- build_Ag(wide, g, lay, Phi, phi)
    Ag[[g]] <- z$A; colg[[g]] <- z$cols
    E[, g] <- z$y - as.numeric(z$A %*% beta[z$cols])
  }
  U <- E %*% Sinv
  Scores <- matrix(0, n, P)
  for (g in seq_len(G)) Scores[, colg[[g]]] <- Scores[, colg[[g]]] + Ag[[g]] * (wt * U[, g])
  cl <- as.integer(factor(cluster))
  Sc <- rowsum(Scores, cl)
  nG <- nrow(Sc)
  meat <- crossprod(Sc) * nG / (nG - 1)   # CR1 small-sample factor
  V <- xtx_inv %*% meat %*% xtx_inv
  dimnames(V) <- list(lay$term_names, lay$term_names)
  V
}

# ---------------------------------------------------------------------------
# Prediction and elasticities
# ---------------------------------------------------------------------------
# Recomputes derived vars AND participation probabilities under perturbation.
predict_shares <- function(wide, lay, beta, probit_betas, stone_w, latent = FALSE) {
  pp <- predict_probits(wide, probit_betas, lay$omit)
  if (latent) { pp$Phi[] <- 1; pp$phi[] <- 0 }   # latent (uncensored) system
  n <- nrow(wide)
  pred <- matrix(0, n, 9, dimnames = list(NULL, CODES9))
  for (g in seq_len(lay$G)) {
    z <- build_Ag(wide, g, lay, pp$Phi, pp$phi)
    pred[, lay$eq_codes[g]] <- as.numeric(z$A %*% beta[z$cols])
  }
  pred[, lay$omit] <- 1 - rowSums(pred[, lay$eq_codes, drop = FALSE])
  raw_gap <- pred[, lay$omit]
  pred[pred < 1e-8] <- 1e-8
  pred <- pred / rowSums(pred)
  attr(pred, "resid_share_range") <- quantile(raw_gap, c(0, 0.005, 0.5, 0.995, 1))
  pred
}

perturb_wide <- function(wide, stone_w, lay, what = c("none","exp","price"), code = NULL, h = 0.01,
                         log_x_col = "log_total_food_spend_pc_month") {
  out <- copy(wide)
  what <- match.arg(what)
  if (what == "exp") {
    out[, total_food_spend_pc_month := total_food_spend_pc_month * (1 + h)]
    out[, (log_x_col) := get(log_x_col) + log(1 + h)]
  } else if (what == "price") {
    out[[paste0("lp_", code)]] <- out[[paste0("lp_", code)]] + log(1 + h)
  }
  derive_vars(out, stone_w, lay$omit, log_x_col)   # Mundlak means kept at base values
  out
}

# ---------------------------------------------------------------------------
# Analytic elasticities at a representative point (wbar, ybar), latent system.
# Recovers the omitted group's price row/column via homogeneity + symmetry.
# Under the two-point curvature constraint, diag(wbar) %*% EH is NSD by
# construction (= Gamma(ybar) + wbar wbar' - diag(wbar), both parts NSD).
# ---------------------------------------------------------------------------
build_gamma9 <- function(beta, lay, ybar) {
  G <- lay$G
  unvech <- function(v) {
    M <- matrix(0, G, G)
    M[cbind(lay$up[, 1], lay$up[, 2])] <- v
    M[cbind(lay$up[, 2], lay$up[, 1])] <- v
    M
  }
  Gam8 <- unvech(beta[lay$off_bp + seq_len(lay$np)]) +
          ybar * unvech(beta[lay$off_cyp + seq_len(lay$np)])
  Gam9 <- matrix(0, 9, 9, dimnames = list(CODES9, CODES9))
  Gam9[lay$eq_codes, lay$eq_codes] <- Gam8
  Gam9[lay$eq_codes, lay$omit] <- -rowSums(Gam8)
  Gam9[lay$omit, lay$eq_codes] <- -colSums(Gam8)
  Gam9[lay$omit, lay$omit] <- sum(Gam8)
  Gam9
}

analytic_elasticities <- function(beta, lay, wbar, ybar) {
  stopifnot(length(wbar) == 9)
  wbar <- as.numeric(wbar); names(wbar) <- CODES9
  Gam9 <- build_gamma9(beta, lay, ybar)
  by <- setNames(numeric(9), CODES9)
  by2 <- setNames(numeric(9), CODES9)
  for (g in seq_len(lay$G)) {
    cc <- lay$eq_codes[g]
    by[cc]  <- beta[(g - 1) * lay$nb + which(lay$base_terms == "y_easi")]
    by2[cc] <- beta[(g - 1) * lay$nb + which(lay$base_terms == "y_easi2")]
  }
  by[lay$omit]  <- -sum(by[lay$eq_codes])
  by2[lay$omit] <- -sum(by2[lay$eq_codes])
  e_exp <- 1 + (by + 2 * ybar * by2) / wbar
  EH <- Gam9 / wbar - diag(9) + matrix(wbar, 9, 9, byrow = TRUE)
  EM <- EH - e_exp %o% wbar
  Sm <- diag(wbar) %*% EH
  Ssym <- (Sm + t(Sm)) / 2
  eig <- sort(eigen(Ssym, symmetric = TRUE, only.values = TRUE)$values, decreasing = TRUE)
  dimnames(EH) <- dimnames(EM) <- list(CODES9, CODES9)
  list(exp = e_exp, hick = EH, mar = EM, eigenvalues = eig,
       curvature_ok = all(eig <= 1e-8), wbar = wbar, ybar = ybar)
}

# Household-month-level curvature check on the latent system:
# S_i = Gamma(y_i) + w_i w_i' - diag(w_i), w_i = predicted latent shares.
household_curvature_check <- function(wide, lay, beta, probit_betas, stone_w) {
  w_pred <- predict_shares(wide, lay, beta, probit_betas, stone_w, latent = TRUE)
  B9 <- build_gamma9(beta, lay, 0)
  C9 <- build_gamma9(beta, lay, 1) - B9
  y <- wide$y_easi
  n <- nrow(wide)
  eig_max <- numeric(n)
  for (i in seq_len(n)) {
    w <- w_pred[i, ]
    S <- B9 + y[i] * C9 + tcrossprod(w) - diag(w)
    eig_max[i] <- eigen((S + t(S)) / 2, symmetric = TRUE, only.values = TRUE)$values[1]
  }
  eig_max
}

quantity_matrix <- function(wide, shares) {
  prices <- exp(as.matrix(wide[, paste0("lp_", CODES9), with = FALSE]))
  shares * wide$total_food_spend_pc_month / prices
}

# Aggregate (weighted-mean-quantity) elasticities plus subgroup versions
compute_elasticities <- function(wide, lay, beta, probit_betas, stone_w, wt, latent = FALSE,
                                 h = 0.01, subgroups = NULL,
                                 log_x_col = "log_total_food_spend_pc_month") {
  base_sh <- predict_shares(wide, lay, beta, probit_betas, stone_w, latent)
  q0 <- quantity_matrix(wide, base_sh)
  wexp <- perturb_wide(wide, stone_w, lay, "exp", h = h, log_x_col = log_x_col)
  q_exp <- quantity_matrix(wexp, predict_shares(wexp, lay, beta, probit_betas, stone_w, latent))
  wm <- function(M, idx) {
    W <- wt[idx]
    colSums(M[idx, , drop = FALSE] * W) / sum(W)
  }
  agg <- function(q1, idx) ((wm(q1, idx) - wm(q0, idx)) / wm(q0, idx)) / h
  all_idx <- rep(TRUE, nrow(wide))
  price_q <- vector("list", 9); names(price_q) <- CODES9
  for (code in CODES9) {
    wp <- perturb_wide(wide, stone_w, lay, "price", code = code, h = h, log_x_col = log_x_col)
    price_q[[code]] <- quantity_matrix(wp, predict_shares(wp, lay, beta, probit_betas, stone_w, latent))
  }
  make_set <- function(idx) {
    ev <- agg(q_exp, idx)
    mar <- sapply(CODES9, function(code) agg(price_q[[code]], idx))  # rows=demand, cols=price
    wbar <- {
      W <- wt[idx]
      colSums(as.matrix(wide[idx, paste0("w_", CODES9), with = FALSE]) * W) / sum(W)
    }
    hick <- mar + ev %o% wbar
    Sm <- diag(wbar) %*% hick
    Ssym <- (Sm + t(Sm)) / 2
    eig <- sort(eigen(Ssym, symmetric = TRUE, only.values = TRUE)$values, decreasing = TRUE)
    list(exp = ev, mar = mar, hick = hick, wbar = wbar, eigenvalues = eig,
         n = sum(idx), curvature_ok = all(eig <= 1e-8))
  }
  out <- list(all = make_set(all_idx),
              resid_share_range = attr(base_sh, "resid_share_range"))
  if (!is.null(subgroups)) out$sub <- lapply(subgroups, make_set)
  out
}
