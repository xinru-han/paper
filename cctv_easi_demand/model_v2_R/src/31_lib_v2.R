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
  wide <- Reduce(function(a, b) merge(a, b, by = c("ID","year_month"), all.x = TRUE),
                 list(bw, cast_one("budget_share","w"), cast_one("positive_purchase","pos"),
                      cast_one(price_col,"lp")))
  setorder(wide, ID, year_month)
  for (v in c(paste0("w_",CODES9), paste0("pos_",CODES9))) wide[is.na(get(v)), (v) := 0]
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

build_probit_X <- function(wide, omit = "G03") {
  eq_codes <- setdiff(CODES9, omit)
  r_cols <- paste0("r_", eq_codes)
  mn_cols <- paste0("mn_", r_cols)
  cols <- c("y_easi", r_cols, DEMO_COLS, Z_COLS, MONTH_D, YEAR_D, "mean_y_hh", mn_cols)
  X <- cbind(const = 1, as.matrix(wide[, ..cols]))
  storage.mode(X) <- "double"
  X
}

fit_probits <- function(wide, wt, omit = "G03", beta0_list = NULL) {
  X <- build_probit_X(wide, omit)
  betas <- list(); stats <- list()
  for (code in CODES9) {
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
  X <- build_probit_X(wide, omit)
  Phi <- matrix(NA_real_, nrow(wide), 9, dimnames = list(NULL, CODES9))
  phi <- Phi
  for (code in CODES9) {
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
system_layout <- function(omit = "G03", az = FALSE, quaids = FALSE) {
  eq_codes <- setdiff(CODES9, omit)
  G <- length(eq_codes)
  base_terms <- c("const","y_easi","y_easi2", DEMO_COLS, Z_COLS, MONTH_D, YEAR_D,
                  "mean_y_hh", paste0("mn_r_", eq_codes))
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
       az = az, az_dims = az_dims, quaids = quaids, omit = omit,
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
  ymult <- if (lay$quaids) wide$y_easi2 else wide$y_easi
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
    diag(xtx) <- diag(xtx) + ridge
    list(beta = as.numeric(solve(xtx, xty)), xtx = xtx)
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
      fit <- solve_once(solve(Sigma))
    }
  } else {
    fit <- solve_once(solve(Sigma))
  }
  rc <- resid_cov(fit$beta)
  beta <- fit$beta; names(beta) <- lay$term_names
  out <- list(beta = beta, Sigma = Sigma %||% rc$S, resid = rc$E, colg = colg)
  if (keep_xtx_inv) out$xtx_inv <- solve(fit$xtx)
  # cluster scores for sandwich (computed lazily by caller via system_scores)
  out$Ag_dims <- vapply(Ag, ncol, 1L)
  out
}

`%||%` <- function(x, y) if (is.null(x)) y else x

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
  meat <- crossprod(Sc)
  V <- xtx_inv %*% meat %*% xtx_inv
  dimnames(V) <- list(lay$term_names, lay$term_names)
  V
}

# ---------------------------------------------------------------------------
# Prediction and elasticities
# ---------------------------------------------------------------------------
# Recomputes derived vars AND participation probabilities under perturbation.
predict_shares <- function(wide, lay, beta, probit_betas, stone_w) {
  pp <- predict_probits(wide, probit_betas, lay$omit)
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

quantity_matrix <- function(wide, shares) {
  prices <- exp(as.matrix(wide[, paste0("lp_", CODES9), with = FALSE]))
  shares * wide$total_food_spend_pc_month / prices
}

# Aggregate (weighted-mean-quantity) elasticities plus subgroup versions
compute_elasticities <- function(wide, lay, beta, probit_betas, stone_w, wt,
                                 h = 0.01, subgroups = NULL,
                                 log_x_col = "log_total_food_spend_pc_month") {
  base_sh <- predict_shares(wide, lay, beta, probit_betas, stone_w)
  q0 <- quantity_matrix(wide, base_sh)
  wexp <- perturb_wide(wide, stone_w, lay, "exp", h = h, log_x_col = log_x_col)
  q_exp <- quantity_matrix(wexp, predict_shares(wexp, lay, beta, probit_betas, stone_w))
  wm <- function(M, idx) {
    W <- wt[idx]
    colSums(M[idx, , drop = FALSE] * W) / sum(W)
  }
  agg <- function(q1, idx) ((wm(q1, idx) - wm(q0, idx)) / wm(q0, idx)) / h
  all_idx <- rep(TRUE, nrow(wide))
  price_q <- vector("list", 9); names(price_q) <- CODES9
  for (code in CODES9) {
    wp <- perturb_wide(wide, stone_w, lay, "price", code = code, h = h, log_x_col = log_x_col)
    price_q[[code]] <- quantity_matrix(wp, predict_shares(wp, lay, beta, probit_betas, stone_w))
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
