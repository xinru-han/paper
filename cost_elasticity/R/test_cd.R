# test_cd.R — 估计器回归测试（M14a 升级；每次 estimator 改动后必跑）
# 覆盖两个 DGP：
#   (A) Cobb-Douglas（gamma=0）：弹性闭式命中 + numeraire 不变性。
#   (B) 完整 translog + 省FE + 时间趋势/二次项 + 可积性 FE 项：
#       从估计器所假设的精确 DGP 仿真，验证 Gamma / alpha / lambda_nt / 省FE
#       （含成本方程的 Σ fe_np·lnw_n 可积项）全部恢复——专门防 F-4 类回归缺陷
#       （省FE 破坏可积性时若成本方程漏掉 Σ fe_np·lnw_n，此测试必失败）。
source(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "itsur.R"))
set.seed(20260703)

N <- 5; K <- N - 1
n_prov <- 20; n_year <- 21
n <- n_prov * n_year
prov <- rep(sprintf("p%02d", 1:n_prov), each = n_year)
year <- rep(2004:2024, n_prov)
tt <- year - 2014

# =============================================================================
# (A) Cobb-Douglas
# =============================================================================
alpha_true <- c(0.35, 0.20, 0.15, 0.10, 0.20)
alpha_y_true <- 0.9
lnw_raw <- matrix(rnorm(n * N, 0, 0.5), n, N)
lny_raw <- rnorm(n, 0, 0.3)
lnC_raw <- 1 + lnw_raw %*% alpha_true + alpha_y_true * lny_raw + rnorm(n, 0, 0.01)

dat <- data.frame(prov = prov, year = year, tt = tt)
for (m in 1:K) dat[[sprintf("lnw_%d", m)]] <- scale(lnw_raw[, m] - lnw_raw[, N], scale = FALSE)
dat$lny <- scale(lny_raw, scale = FALSE)
dat$lnC <- scale(lnC_raw - lnw_raw[, N], scale = FALSE)
Snoise <- matrix(rnorm(n * K, 0, 0.005), n, K)
for (m in 1:K) dat[[sprintf("S_%d", m)]] <- alpha_true[m] + Snoise[, m]

fit <- tl_itsur(tl_build_system(dat, K)); stopifnot(fit$converged)
rec <- tl_recover(fit, K)
cat("[A] max|gamma| =", max(abs(rec$Gamma)),
    " max|alpha-true| =", max(abs(rec$alpha - alpha_true)), "\n")
stopifnot(max(abs(rec$Gamma)) < 0.02, max(abs(rec$alpha - alpha_true)) < 0.02)

S <- alpha_true
el <- tl_elasticities(matrix(0, N, N), S)
stopifnot(max(abs(diag(el$eps) - (S - 1))) < 1e-12)
off <- el$eps; diag(off) <- NA
stopifnot(max(abs(sweep(off, 2, S, "-")), na.rm = TRUE) < 1e-12)
stopifnot(max(abs(el$allen[upper.tri(el$allen)] - 1)) < 1e-12)
Mo <- el$morishima; diag(Mo) <- NA
stopifnot(max(abs(Mo - 1), na.rm = TRUE) < 1e-12)
cat("[A] CD elasticity formulas: OK\n")

perm <- c(1, 2, 3, 5, 4)
dat2 <- dat
for (m in 1:K) dat2[[sprintf("lnw_%d", m)]] <- scale(lnw_raw[, perm[m]] - lnw_raw[, perm[N]], scale = FALSE)
dat2$lnC <- scale(lnC_raw - lnw_raw[, perm[N]], scale = FALSE)
S_full <- cbind(sapply(1:K, function(m) dat[[sprintf("S_%d", m)]]),
                1 - rowSums(sapply(1:K, function(m) dat[[sprintf("S_%d", m)]])))
for (m in 1:K) dat2[[sprintf("S_%d", m)]] <- S_full[, perm[m]]
rec2 <- tl_recover(tl_itsur(tl_build_system(dat2, K)), K)
G2_back <- rec2$Gamma[order(perm), order(perm)]
cat("[A] numeraire invariance max|dGamma| =", max(abs(G2_back - rec$Gamma)), "\n")
stopifnot(max(abs(G2_back - rec$Gamma)) < 1e-4)

# =============================================================================
# (B) 完整 translog + 省FE + 趋势/二次 + 可积性 FE 项
# =============================================================================
set.seed(11)
# 真 Gamma：K×K 对称块，numeraire 由行和为零恢复（对称+齐次）
Gkk <- matrix(c( 0.06,-0.02,-0.01,-0.01,
                -0.02, 0.05,-0.01, 0.00,
                -0.01,-0.01, 0.04,-0.01,
                -0.01, 0.00,-0.01, 0.03), K, K, byrow = TRUE)
Gkk <- (Gkk + t(Gkk)) / 2
G_true <- matrix(0, N, N); G_true[1:K, 1:K] <- Gkk
for (nn in 1:K) { G_true[nn, N] <- -sum(G_true[nn, 1:K]); G_true[N, nn] <- G_true[nn, N] }
G_true[N, N] <- -sum(G_true[N, 1:K])

a_sh   <- c(0.35, 0.20, 0.15, 0.10)                 # 份额截距（非numeraire）
gy     <- c(0.02, -0.01, 0.00, -0.01)               # gamma_ny（非numeraire）
lam_nt <- c(-0.004, 0.003, 0.001, -0.001)           # lambda_nt（非numeraire）
a0 <- 0.5; a_y <- 0.9; g_yy <- 0.05
lam_t <- 0.03; lam_tt <- -0.002; lam_yt <- 0.01

# 省FE：份额方程 fe_np（K×省），base 省(p01)=0；成本方程 feC_p，base=0
# fe_np 取较大幅度：漏掉可积项 Σfe_np·lnw_n 时该项(sd≈0.05)全数进入成本残差 → 必被下方断言捕获
fe_np  <- matrix(rnorm(K * n_prov, 0, 0.06), K, n_prov); fe_np[, 1] <- 0
feC_p  <- rnorm(n_prov, 0, 0.05); feC_p[1] <- 0
prov_id <- as.integer(factor(prov))

# 中心化回归元（全局均值0，令截距可精确恢复）
lnwB <- matrix(rnorm(n * K, 0, 0.4), n, K)
lnwB <- scale(lnwB, scale = FALSE)
lnyB <- as.numeric(scale(rnorm(n, 0, 0.3), scale = FALSE))

# 份额（n=1..K）：S_n = a_sh_n + sum_m G_nm lnw_m + gy_n lny + lam_nt_n t + fe_np + eps
Sh <- matrix(0, n, K)
for (nn in 1:K)
  Sh[, nn] <- a_sh[nn] + lnwB %*% G_true[nn, 1:K] + gy[nn] * lnyB +
              lam_nt[nn] * tt + fe_np[nn, prov_id]
Sh <- Sh + matrix(rnorm(n * K, 0, 5e-4), n, K)

# 成本：含 0.5ΣΣG lnw lnw、Σgy lnw lny、趋势/二次、feC_p，及可积项 Σ fe_np·lnw_n
quad <- 0.5 * rowSums((lnwB %*% G_true[1:K, 1:K]) * lnwB)
integ <- rowSums(sapply(1:K, function(nn) fe_np[nn, prov_id] * lnwB[, nn]))
lnC <- a0 + lnwB %*% a_sh + a_y * lnyB + quad +
       rowSums(sapply(1:K, function(nn) gy[nn] * lnwB[, nn] * lnyB)) + 0.5 * g_yy * lnyB^2 +
       lam_t * tt + 0.5 * lam_tt * tt^2 +
       rowSums(sapply(1:K, function(nn) lam_nt[nn] * tt * lnwB[, nn])) + lam_yt * tt * lnyB +
       feC_p[prov_id] + integ + rnorm(n, 0, 5e-4)

datB <- data.frame(prov = prov, year = year, tt = tt, lny = lnyB, lnC = as.numeric(lnC))
for (m in 1:K) { datB[[sprintf("lnw_%d", m)]] <- lnwB[, m]; datB[[sprintf("S_%d", m)]] <- Sh[, m] }

fitB <- tl_itsur(tl_build_system(datB, K), tol = 1e-11); stopifnot(fitB$converged)
recB <- tl_recover(fitB, K)
th <- fitB$theta

e_G   <- max(abs(recB$Gamma - G_true))
e_a   <- max(abs(recB$alpha[1:K] - a_sh))
e_lam <- max(abs(recB$lambda_nt[1:K] - lam_nt))
# 可积性 FE 项恢复（成本方程的 Σ fe_np·lnw_n 系数即 fe_np 本身）
fe_hat <- sapply(2:n_prov, function(j) sapply(1:K, function(nn)
  th[sprintf("fe%d_%s", nn, sprintf("p%02d", j))]))
e_fe  <- max(abs(fe_hat - fe_np[, 2:n_prov]))
# 成本方程专属参数（份额方程不识别；F-4 漏可积项时经由成本残差污染这些系数）
e_cost <- max(abs(c(th["alpha_0"] - a0, th["alpha_y"] - a_y, th["gamma_yy"] - g_yy,
                    th["lambda_t"] - lam_t, th["lambda_tt"] - lam_tt, th["lambda_yt"] - lam_yt)))
# 成本方程拟合残差 SD：正确规格≈噪声(5e-4)；漏可积项时 Σfe·lnw(sd≈0.05)全进残差 → 放大~100×
cost_resid_sd <- sd(fitB$resid[, fitB$eqnames == "cost"])
cat(sprintf("[B] max|dGamma|=%.2e |dalpha|=%.2e |dlambda_nt|=%.2e |dFE|=%.2e |dCostPar|=%.2e costResidSD=%.2e\n",
            e_G, e_a, e_lam, e_fe, e_cost, cost_resid_sd))
stopifnot(e_G < 5e-3, e_a < 5e-3, e_lam < 2e-3, e_fe < 1e-2,
          e_cost < 5e-3, cost_resid_sd < 5e-3)   # 后两项是 F-4 可积性守门断言
cat("[B] full translog + provFE + integrability recovery: OK\n")

cat("ALL ESTIMATOR REGRESSION TESTS PASSED\n")
