# itsur_concave.R — C1预案：局部凹性施加（Ryan–Wales 2000 变体）
# 在样本均值点（中心化点，S≈S̄）施加 G(S̄) = Γ + S̄S̄' − diag(S̄) = −AA' 半负定，
# 即 Γ = diag(S̄) − S̄S̄' − AA'，A 为 N×K 下三角（秩K，保留结构性零特征值）。
# S̄ 取样本均值份额（固定常数）⇒ 只有 γ 块非线性：外层 optim 优化 A 的自由元，
# 内层给定 Γ(A) 后其余参数线性，按 GLS profile；Σ 外层迭代更新。
if (!exists("tl_itsur")) stop("请先 source R/itsur.R")

# A自由元（下三角 N×K，去掉最后一行由齐次性决定？）——
# 直接参数化 K×K 下三角 L，令 G_KK = -LL'（K维自由块），
# 完整 G 由齐次性 G ι = 0 恢复：G[n,N] = -sum_K G[n,1:K] 等。
c1_gamma_from_a <- function(a, Sbar, K) {
  L <- matrix(0, K, K); L[lower.tri(L, diag = TRUE)] <- a
  Gkk <- -tcrossprod(L)                       # K×K 半负定
  N <- K + 1
  G <- matrix(0, N, N)
  G[1:K, 1:K] <- Gkk
  for (n in 1:K) { G[n, N] <- -sum(G[n, 1:K]); G[N, n] <- G[n, N] }
  G[N, N] <- -sum(G[N, 1:K])
  # Γ = G − S̄S̄' + diag(S̄)
  G - tcrossprod(Sbar) + diag(Sbar)
}

# 把 γ 块从设计矩阵移到 offset：需要各方程中 γ_nm 对应的regressor
# 复用 tl_build_system 的 X：γ 列乘固定值即 offset。
tl_itsur_c1 <- function(sys, K, Sbar, tol = 1e-9, maxit_sigma = 30) {
  N <- K + 1
  J <- sys$J; n <- sys$n_obs
  pn <- sys$pnames
  gam_idx <- grep("^gamma_[0-9]_[0-9]$", pn)
  Xall <- do.call(rbind, sys$X)
  yall <- unlist(sys$y)
  Xg <- Xall[, gam_idx, drop = FALSE]                    # γ regressors
  lin_idx <- setdiff(which(colSums(abs(Xall)) > 0), gam_idx)
  Xl <- Xall[, lin_idx, drop = FALSE]

  gam_vec_from_G <- function(Gam) {                       # 与 pnames 顺序一致 (n<=m)
    v <- c(); for (nn in 1:K) for (mm in nn:K) v <- c(v, Gam[nn, mm]); v
  }
  Xb_l <- lapply(1:J, function(j) Xl[((j - 1) * n + 1):(j * n), , drop = FALSE])

  # 给定 a 与 Σ^-1，profile 线性参数，返回 -加权SSR 相关目标
  inner <- function(a, W) {
    Gam <- c1_gamma_from_a(a, Sbar, K)
    off <- as.numeric(Xg %*% gam_vec_from_G(Gam))
    yst <- yall - off
    A <- matrix(0, ncol(Xl), ncol(Xl)); b <- numeric(ncol(Xl))
    yb <- lapply(1:J, function(j) yst[((j - 1) * n + 1):(j * n)])
    for (j in 1:J) for (l in 1:J) {
      A <- A + W[j, l] * crossprod(Xb_l[[j]], Xb_l[[l]])
      b <- b + W[j, l] * crossprod(Xb_l[[j]], yb[[l]])
    }
    bl <- solve(A, b)
    res <- matrix(yst - Xl %*% bl, n, J)
    ssr <- 0
    for (j in 1:J) for (l in 1:J) ssr <- ssr + W[j, l] * sum(res[, j] * res[, l])
    list(ssr = ssr, beta_lin = bl, resid = res, A = A)
  }

  # 初值：无约束拟合的 G 投影到最近半负定
  fit0 <- tl_itsur(sys)
  G0 <- tl_recover(fit0, K)$Gamma + tcrossprod(Sbar) - diag(Sbar)
  Gkk0 <- G0[1:K, 1:K]
  e <- eigen(-(Gkk0 + t(Gkk0)) / 2, symmetric = TRUE)
  Pos <- e$vectors %*% diag(pmax(e$values, 1e-6)) %*% t(e$vectors)
  L0 <- t(chol(Pos)); a <- L0[lower.tri(L0, diag = TRUE)]

  Sig <- fit0$Sigma
  for (osig in 1:maxit_sigma) {
    W <- solve(Sig)
    opt <- optim(a, function(x) inner(x, W)$ssr, method = "BFGS",
                 control = list(maxit = 400, reltol = 1e-12))
    a <- opt$par
    sol <- inner(a, W)
    Sig_new <- crossprod(sol$resid) / n
    dS <- max(abs(Sig_new - Sig)); Sig <- Sig_new
    if (dS < tol) break
  }
  Gam <- c1_gamma_from_a(a, Sbar, K)
  theta <- setNames(numeric(length(pn)), pn)
  theta[lin_idx] <- sol$beta_lin
  gv <- gam_vec_from_G(Gam); theta[gam_idx] <- gv
  ll <- -n * J / 2 * (1 + log(2 * pi)) - n / 2 * log(det(Sig))
  list(theta = theta, Sigma = Sig, resid = sol$resid, a = a, Gamma_full = Gam,
       logLik = ll, converged = (dS < tol), iter = osig,
       keep = sort(c(lin_idx, gam_idx)), pnames = pn, eqnames = sys$eqnames)
}
