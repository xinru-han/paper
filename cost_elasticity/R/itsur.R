# itsur.R — 受约束迭代SUR（translog成本函数系统）核心估计器
# 系统：ln(C/w_N) 方程 + (N-1) 个成本份额方程（删去第N要素"other"）
# 约束：齐次性由 numeraire 构造满足；对称性与跨方程共享由参数映射（设计矩阵拼接）内建
# 纯 base R 矩阵实现，等价于收敛后的 FIML（Berndt 1991, ch.9）
#
# 参数化（要素 n=1..K 为非numeraire要素，K=N-1；numeraire=第N要素）：
#   份额方程 n: S_n = alpha_n + sum_m gamma_nm * lnw_m + gamma_ny * lny + lambda_nt * t + 省FE_n + eps_n
#   成本方程:  lnC* = alpha_0 + sum_n alpha_n lnw_n + alpha_y lny + 0.5 sum_nm gamma_nm lnw_n lnw_m
#              + sum_n gamma_ny lnw_n lny + 0.5 gamma_yy lny^2
#              + lambda_t t + 0.5 lambda_tt t^2 + sum_n lambda_nt t lnw_n + lambda_yt t lny + 省FE_C + u
#   其中 lnw_m = ln(w_m/w_N) 中心化，lnC* = ln(C/w_N) 中心化，lny 中心化，t = year - t_center
#   gamma_nm 对称，只估 n<=m。第N要素参数由 R1-R5 恢复。

# ---- 自由参数索引 ----------------------------------------------------------
# 返回参数名向量与辅助索引
tl_param_names <- function(K, fe_levels_share, fe_levels_cost) {
  gam <- c()
  for (n in 1:K) for (m in n:K) gam <- c(gam, sprintf("gamma_%d_%d", n, m))
  base <- c(sprintf("alpha_%d", 1:K),              # 份额截距
            gam,                                    # 对称gamma（非numeraire块）
            sprintf("gamma_%dy", 1:K),              # 份额-产出交互
            sprintf("lambda_%dt", 1:K),             # 份额-时间交互
            "alpha_0", "alpha_y", "gamma_yy",
            "lambda_t", "lambda_tt", "lambda_yt")
  fe_s <- c()
  for (n in 1:K) if (length(fe_levels_share)) fe_s <- c(fe_s, sprintf("fe%d_%s", n, fe_levels_share))
  fe_c <- if (length(fe_levels_cost)) sprintf("feC_%s", fe_levels_cost) else c()
  c(base, fe_s, fe_c)
}

# ---- 设计矩阵构造 ----------------------------------------------------------
# dat: data.frame，含中心化的 lnw_1..lnw_K（相对numeraire）、lny、tt、lnC（相对numeraire中心化）、
#      S_1..S_K（份额）、prov（factor 省份）
# 返回 list(X, y, J, n_obs, pnames, eqnames)：堆叠系统 y = X theta
tl_build_system <- function(dat, K, use_cost_eq = TRUE, share_time = "linear",
                            year_dummies = NULL) {
  dat <- as.data.frame(dat)   # 防御：data.table 的 [ 语义不同
  n_obs <- nrow(dat)
  prov <- droplevels(factor(dat$prov))
  fe_lv <- levels(prov)[-1]                 # 第一个省为基准
  # share_time = "linear": lambda_nt * t；"gindex": 份额方程用年份哑变量 delta_n_tau（S2规格）
  pn <- tl_param_names(K, fe_lv, if (use_cost_eq) fe_lv else c())
  if (share_time == "gindex") {
    stopifnot(!is.null(year_dummies))
    yd_lv <- year_dummies[-1]               # 基准年
    extra <- c()
    for (n in 1:K) extra <- c(extra, sprintf("delta%d_%s", n, yd_lv))
    pn <- c(pn, extra)
  }
  P <- length(pn)
  idx <- function(name) match(name, pn)

  lnw <- as.matrix(dat[, sprintf("lnw_%d", 1:K), drop = FALSE])
  lny <- dat$lny; tt <- dat$tt
  FEmat <- if (length(fe_lv)) sapply(fe_lv, function(l) as.numeric(prov == l)) else NULL

  blocks_X <- list(); blocks_y <- list(); eqnames <- c()
  # ---- K个份额方程 ----
  for (n in 1:K) {
    Xn <- matrix(0, n_obs, P)
    Xn[, idx(sprintf("alpha_%d", n))] <- 1
    for (m in 1:K) {
      nm <- if (n <= m) sprintf("gamma_%d_%d", n, m) else sprintf("gamma_%d_%d", m, n)
      Xn[, idx(nm)] <- Xn[, idx(nm)] + lnw[, m]
    }
    Xn[, idx(sprintf("gamma_%dy", n))] <- lny
    if (share_time == "linear") {
      Xn[, idx(sprintf("lambda_%dt", n))] <- tt
    } else {
      for (l in year_dummies[-1])
        Xn[, idx(sprintf("delta%d_%s", n, l))] <- as.numeric(dat$year == as.integer(l))
    }
    if (!is.null(FEmat)) for (j in seq_along(fe_lv))
      Xn[, idx(sprintf("fe%d_%s", n, fe_lv[j]))] <- FEmat[, j]
    blocks_X[[length(blocks_X) + 1]] <- Xn
    blocks_y[[length(blocks_y) + 1]] <- dat[[sprintf("S_%d", n)]]
    eqnames <- c(eqnames, sprintf("share_%d", n))
  }
  # ---- 成本方程 ----
  if (use_cost_eq) {
    Xc <- matrix(0, n_obs, P)
    Xc[, idx("alpha_0")] <- 1
    for (n in 1:K) Xc[, idx(sprintf("alpha_%d", n))] <- lnw[, n]
    Xc[, idx("alpha_y")] <- lny
    for (n in 1:K) for (m in n:K) {
      w2 <- if (n == m) 0.5 * lnw[, n]^2 else lnw[, n] * lnw[, m]
      Xc[, idx(sprintf("gamma_%d_%d", n, m))] <- Xc[, idx(sprintf("gamma_%d_%d", n, m))] + w2
    }
    for (n in 1:K) Xc[, idx(sprintf("gamma_%dy", n))] <- lnw[, n] * lny
    Xc[, idx("gamma_yy")] <- 0.5 * lny^2
    Xc[, idx("lambda_t")] <- tt
    Xc[, idx("lambda_tt")] <- 0.5 * tt^2
    if (share_time == "linear")
      for (n in 1:K) Xc[, idx(sprintf("lambda_%dt", n))] <- tt * lnw[, n]
    Xc[, idx("lambda_yt")] <- tt * lny
    if (!is.null(FEmat)) for (j in seq_along(fe_lv))
      Xc[, idx(sprintf("feC_%s", fe_lv[j]))] <- FEmat[, j]
    # 可积性：份额方程含省截距fe_np，则由Shephard引理成本方程须含 sum_n fe_np*lnw_n
    if (!is.null(FEmat)) for (n in 1:K) for (j in seq_along(fe_lv))
      Xc[, idx(sprintf("fe%d_%s", n, fe_lv[j]))] <- FEmat[, j] * lnw[, n]
    blocks_X[[length(blocks_X) + 1]] <- Xc
    blocks_y[[length(blocks_y) + 1]] <- dat$lnC
    eqnames <- c(eqnames, "cost")
  }
  list(X = blocks_X, y = blocks_y, J = length(blocks_X), n_obs = n_obs,
       pnames = pn, eqnames = eqnames)
}

# ---- ITSUR ----------------------------------------------------------------
tl_itsur <- function(sys, tol = 1e-10, maxit = 500, drop_params = NULL) {
  # drop_params: 参数名向量（支持正则），被约束为0 —— 用于LR检验的受限规格
  J <- sys$J; n <- sys$n_obs; P <- length(sys$pnames)
  Xall <- do.call(rbind, sys$X)          # (J*n) x P，方程按块堆叠
  yall <- unlist(sys$y)
  keep <- which(colSums(abs(Xall)) > 0)  # 该规格未用到的参数列剔除
  if (!is.null(drop_params)) {
    dropped <- unique(unlist(lapply(drop_params, function(p) grep(p, sys$pnames))))
    keep <- setdiff(keep, dropped)
  }
  Xk <- Xall[, keep, drop = FALSE]
  # 初值：OLS
  theta <- qr.coef(qr(Xk), yall); theta[is.na(theta)] <- 0
  Sig <- diag(J)
  for (it in 1:maxit) {
    res <- matrix(yall - Xk %*% theta, n, J)   # n x J（列=方程）
    Sig_new <- crossprod(res) / n
    W <- solve(Sig_new)                         # J x J
    # GLS：X' (W ⊗ I) X theta = X' (W ⊗ I) y，块结构手工累加避免大kron
    A <- matrix(0, ncol(Xk), ncol(Xk)); b <- numeric(ncol(Xk))
    Xb <- lapply(1:J, function(j) Xk[((j - 1) * n + 1):(j * n), , drop = FALSE])
    yb <- lapply(1:J, function(j) yall[((j - 1) * n + 1):(j * n)])
    for (j in 1:J) for (l in 1:J) {
      A <- A + W[j, l] * crossprod(Xb[[j]], Xb[[l]])
      b <- b + W[j, l] * crossprod(Xb[[j]], yb[[l]])
    }
    theta_new <- solve(A, b)
    dmax <- max(abs(theta_new - theta))
    theta <- theta_new; Sig <- Sig_new
    if (dmax < tol) break
  }
  res <- matrix(yall - Xk %*% theta, n, J)
  # 参数协方差（GLS公式，供delta法交叉核对；主推断用bootstrap）
  vcov_k <- solve(A)
  th_full <- setNames(numeric(P), sys$pnames); th_full[keep] <- theta
  V_full <- matrix(0, P, P, dimnames = list(sys$pnames, sys$pnames))
  V_full[keep, keep] <- vcov_k
  # 对数似然（多元正态，FIML等价）
  ll <- -n * J / 2 * (1 + log(2 * pi)) - n / 2 * log(det(Sig))
  list(theta = th_full, vcov = V_full, Sigma = Sig, resid = res,
       iter = it, converged = (dmax < tol), dmax = dmax, logLik = ll,
       keep = keep, pnames = sys$pnames, eqnames = sys$eqnames)
}

# ---- 参数恢复：完整 N 要素 gamma 矩阵、alpha、lambda_t ----------------------
tl_recover <- function(fit, K) {
  th <- fit$theta
  N <- K + 1
  G <- matrix(0, N, N)
  for (n in 1:K) for (m in n:K) {
    G[n, m] <- th[sprintf("gamma_%d_%d", n, m)]; G[m, n] <- G[n, m]
  }
  for (n in 1:K) { G[n, N] <- -sum(G[n, 1:K]); G[N, n] <- G[n, N] }
  G[N, N] <- -sum(G[N, 1:K])
  alpha <- c(th[sprintf("alpha_%d", 1:K)], 1 - sum(th[sprintf("alpha_%d", 1:K)]))
  gy <- c(th[sprintf("gamma_%dy", 1:K)], -sum(th[sprintf("gamma_%dy", 1:K)]))
  lt <- th[sprintf("lambda_%dt", 1:K)]
  lt <- c(lt, -sum(lt))
  list(Gamma = G, alpha = unname(alpha), gamma_y = unname(gy), lambda_nt = unname(lt))
}

# ---- 弹性（式5-7），在给定份额向量S处评估 -----------------------------------
tl_elasticities <- function(Gamma, S) {
  N <- length(S)
  eps <- matrix(NA_real_, N, N)
  for (n in 1:N) for (m in 1:N) {
    eps[n, m] <- if (n == m) (Gamma[n, n] + S[n]^2 - S[n]) / S[n]
                 else (Gamma[n, m] + S[n] * S[m]) / S[n]
  }
  sig <- sweep(eps, 2, S, "/")                       # Allen: sigma_nm = eps_nm / S_m
  M <- matrix(NA_real_, N, N)                        # Morishima: M_nm = eps_nm - eps_mm
  for (n in 1:N) for (m in 1:N) M[n, m] <- eps[n, m] - eps[m, m]
  list(eps = eps, allen = sig, morishima = M)
}

# ---- 凹性检验：G(S) = Gamma + SS' - diag(S) 半负定（容忍结构性零特征值） ------
tl_concavity <- function(Gamma, S, tol = 1e-7) {
  G <- Gamma + tcrossprod(S) - diag(S)
  ev <- eigen(G, symmetric = TRUE, only.values = TRUE)$values
  max(ev) <= tol
}

# ---- 拟合份额 --------------------------------------------------------------
tl_fitted_shares <- function(fit, sys, K) {
  n <- sys$n_obs
  Shat <- sapply(1:K, function(j) {
    Xj <- sys$X[[j]]
    as.numeric(Xj[, fit$keep, drop = FALSE] %*% fit$theta[fit$keep])
  })
  cbind(Shat, 1 - rowSums(Shat))   # 第N要素份额由加总恢复
}
