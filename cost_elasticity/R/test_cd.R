# test_cd.R — Cobb-Douglas 单元测试（plan §3.2 第5条）
# 仿真CD成本数据（gamma=0），要求：回收 gamma≈0、alpha命中真值、
# 弹性命中CD理论值：eps_nn=S_n-1, eps_nm=S_m, sigma=1, Morishima=1；
# 以及删除不同份额方程的不变性检验。
source(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "itsur.R"))
set.seed(20260703)

N <- 5; K <- N - 1
alpha_true <- c(0.35, 0.20, 0.15, 0.10, 0.20)   # CD份额
alpha_y_true <- 0.9
n_prov <- 20; n_year <- 21
n <- n_prov * n_year
prov <- rep(sprintf("p%02d", 1:n_prov), each = n_year)
year <- rep(2004:2024, n_prov)

lnw_raw <- matrix(rnorm(n * N, 0, 0.5), n, N)
lny_raw <- rnorm(n, 0, 0.3)
tt <- year - 2014
# CD: lnC = a0 + sum alpha_n lnw_n + a_y lny + noise; S_n = alpha_n + noise
lnC_raw <- 1 + lnw_raw %*% alpha_true + alpha_y_true * lny_raw + rnorm(n, 0, 0.01)

dat <- data.frame(prov = prov, year = year, tt = tt)
for (m in 1:K) dat[[sprintf("lnw_%d", m)]] <- scale(lnw_raw[, m] - lnw_raw[, N], scale = FALSE)
dat$lny <- scale(lny_raw, scale = FALSE)
dat$lnC <- scale(lnC_raw - lnw_raw[, N], scale = FALSE)
Snoise <- matrix(rnorm(n * K, 0, 0.005), n, K)
for (m in 1:K) dat[[sprintf("S_%d", m)]] <- alpha_true[m] + Snoise[, m] - rowMeans(Snoise) * 0

sys <- tl_build_system(dat, K)
fit <- tl_itsur(sys)
stopifnot(fit$converged)
rec <- tl_recover(fit, K)

cat("max|gamma|      =", max(abs(rec$Gamma)), "\n")
cat("max|alpha-true| =", max(abs(rec$alpha - alpha_true)), "\n")
stopifnot(max(abs(rec$Gamma)) < 0.02, max(abs(rec$alpha - alpha_true)) < 0.02)

S <- alpha_true
el <- tl_elasticities(matrix(0, N, N), S)
stopifnot(max(abs(diag(el$eps) - (S - 1))) < 1e-12)
off <- el$eps; diag(off) <- NA
stopifnot(max(abs(sweep(off, 2, S, "-")), na.rm = TRUE) < 1e-12)
stopifnot(max(abs(el$allen[upper.tri(el$allen)] - 1)) < 1e-12)
Mo <- el$morishima; diag(Mo) <- NA
stopifnot(max(abs(Mo - 1), na.rm = TRUE) < 1e-12)
cat("CD elasticity formulas: OK\n")

# 不变性：换 numeraire（把要素4作为numeraire而不是5）重估，恢复后的完整Gamma应一致
perm <- c(1, 2, 3, 5, 4)
dat2 <- dat
lnw_full <- lnw_raw
for (m in 1:K) dat2[[sprintf("lnw_%d", m)]] <- scale(lnw_full[, perm[m]] - lnw_full[, perm[N]], scale = FALSE)
dat2$lnC <- scale(lnC_raw - lnw_full[, perm[N]], scale = FALSE)
S_full <- cbind(do.call(cbind, lapply(1:K, function(m) dat[[sprintf("S_%d", m)]])),
                1 - rowSums(sapply(1:K, function(m) dat[[sprintf("S_%d", m)]])))
for (m in 1:K) dat2[[sprintf("S_%d", m)]] <- S_full[, perm[m]]
fit2 <- tl_itsur(tl_build_system(dat2, K))
rec2 <- tl_recover(fit2, K)
G2_back <- rec2$Gamma[order(perm), order(perm)]
cat("numeraire invariance max|dGamma| =", max(abs(G2_back - rec$Gamma)), "\n")
stopifnot(max(abs(G2_back - rec$Gamma)) < 1e-4)
cat("ALL CD TESTS PASSED\n")
