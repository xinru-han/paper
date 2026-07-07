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
# S_obs: n×N 观测份额矩阵（可选）。给定时目标加曲率惩罚
#   penalty = kappa * sum_i max(eigmax(Gamma + S_iS_i' - diag(S_i)), 0)^2
# （Terrell 1996 "在每个样本点施加凹性" 的惩罚化实现；kappa 足够大时≈约束估计）
tl_itsur_c1 <- function(sys, K, Sbar, tol = 1e-9, maxit_sigma = 30,
                        S_obs = NULL, kappa = 0) {
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
  Xb_g <- lapply(1:J, function(j) Xg[((j - 1) * n + 1):(j * n), , drop = FALSE])
  yb   <- lapply(1:J, function(j) yall[((j - 1) * n + 1):(j * n)])

  # SSR(g) 闭式二次型的分块预计算（给定 W）：
  #   SSR = c0 - 2 c1'g + g'C2 g，beta_lin = H (Aly - Alg g)
  precompute <- function(W) {
    Pl <- ncol(Xl); Pg <- ncol(Xg)
    All <- matrix(0, Pl, Pl); Alg <- matrix(0, Pl, Pg); Agg <- matrix(0, Pg, Pg)
    Aly <- numeric(Pl); Agy <- numeric(Pg); Ayy <- 0
    for (j in 1:J) for (l in 1:J) {
      w <- W[j, l]
      All <- All + w * crossprod(Xb_l[[j]], Xb_l[[l]])
      Alg <- Alg + w * crossprod(Xb_l[[j]], Xb_g[[l]])
      Agg <- Agg + w * crossprod(Xb_g[[j]], Xb_g[[l]])
      Aly <- Aly + w * crossprod(Xb_l[[j]], yb[[l]])
      Agy <- Agy + w * crossprod(Xb_g[[j]], yb[[l]])
      Ayy <- Ayy + w * sum(yb[[j]] * yb[[l]])
    }
    H <- solve(All)
    list(H = H, Aly = Aly, Alg = Alg,
         c0 = Ayy - as.numeric(t(Aly) %*% H %*% Aly),
         c1 = as.numeric(Agy - t(Alg) %*% H %*% Aly),
         C2 = Agg - t(Alg) %*% H %*% Alg)
  }

  penalty <- function(Gam) {
    if (is.null(S_obs) || kappa <= 0) return(0)
    pen <- 0
    for (i in seq_len(nrow(S_obs))) {
      Si <- S_obs[i, ]
      ev <- max(eigen(Gam + tcrossprod(Si) - diag(Si), symmetric = TRUE,
                      only.values = TRUE)$values)
      if (ev > 0) pen <- pen + ev^2
    }
    kappa * pen
  }

  inner_obj <- function(a, pc) {
    Gam <- c1_gamma_from_a(a, Sbar, K)
    g <- gam_vec_from_G(Gam)
    pc$c0 - 2 * sum(pc$c1 * g) + as.numeric(t(g) %*% pc$C2 %*% g) + penalty(Gam)
  }

  inner <- function(a, pc) {   # 完整解（收敛后取残差用）
    Gam <- c1_gamma_from_a(a, Sbar, K)
    g <- gam_vec_from_G(Gam)
    bl <- as.numeric(pc$H %*% (pc$Aly - pc$Alg %*% g))
    res <- matrix(yall - Xg %*% g - Xl %*% bl, n, J)
    list(beta_lin = bl, resid = res)
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
    pc <- precompute(W)
    opt <- optim(a, inner_obj, pc = pc, method = "BFGS",
                 control = list(maxit = 400, reltol = 1e-12))
    a <- opt$par
    sol <- inner(a, pc)
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
