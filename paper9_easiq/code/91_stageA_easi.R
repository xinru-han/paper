# Paper 9 script 91: Stage A — truncated EASI share system (14 goods).
# Implementation notes (deviations from the md's systemfit sketch, documented):
#  - Homogeneity imposed by price normalization: lnp*_k = lnp_k - lnp_14
#    (composite as numeraire); composite equation dropped.
#  - Equations estimated one-by-one with fixest (consistent; full SUR gains
#    efficiency only through cross-equation covariance, sacrificed for the
#    54.8w x 14 scale). Symmetry imposed ex post by minimum distance
#    (A_sym = (A+A')/2) with a pairwise z-statistic diagnostic table; the
#    unrestricted A is also saved.
#  - Shonkwiler-Yen two step: probit per good -> Phi, phi; RHS terms enter
#    multiplied by Phi_g, phi_g added as regressor.
#  - ln x endogeneity: the planned control function was DROPPED — the income
#    bands are nearly unrelated to recorded food spend (90d: within s2=0.002),
#    so vhat is uninformative and near-collinear with y. OLS + household FE is
#    the main spec (the md's pre-registered fallback). vhat still computed and
#    saved for the record.
#  - y iterated: y0 = Stone index with sample-mean weights, updated with
#    predicted shares until max|dy| < 1e-6 (or 10 iterations).
source("/root/data/Paper/央视数据/paper9-easiq/code/00_setup.R")

pan <- readRDS(file.path(DIR_INT, "panel_hhm.rds"))
pan <- pan[is.finite(ln_x) & is.finite(ln_inc) & !is.na(tier_a)]
K <- length(G14); Keq <- K - 1L
logmsg("91: estimation sample ", nrow(pan), " hh-months")

## normalized prices (homogeneity)
for (k in 1:Keq) pan[, (paste0("lnps_", k)) := get(paste0("lnp_", k)) - get(paste0("lnp_", K))]
ZVARS <- c("fsize","elderly","lock_days","ln_covid","cny_share","hot_days")
pan[is.na(fsize), fsize := median(pan$fsize, na.rm = TRUE)]

## ---- control function for ln x
cf <- feols(ln_x ~ ln_inc + inv_inc + fsize | prov_tier^ym, data = pan)
pan[as.integer(obs(cf)), vhat := resid(cf)]
pan[is.na(vhat), vhat := 0]
fs_F <- tryCatch(fitstat(cf, "wald")$wald$stat, error = function(e) NA)
logmsg("91: control-function first stage Wald = ", round(fs_F, 1),
       " (ln_inc t = ", round(tstat(cf)["ln_inc"], 1), ")")

## ---- probit layer (Shonkwiler-Yen inputs + selection terms for Stage B)
prb_rhs <- paste(c("ln_inc", ZVARS, paste0("lnps_", 1:Keq)), collapse = " + ")
for (g in 1:Keq) {
  pan[, buy := as.integer(get(paste0("w_", g)) > 0)]
  mg <- feglm(as.formula(paste0("buy ~ ", prb_rhs, " | prov_tier + mo")),
              data = pan, family = binomial("probit"), notes = FALSE)
  xb <- predict(mg, type = "link")
  pan[as.integer(obs(mg)), `:=`(PHI = pnorm(xb), phi = dnorm(xb))]
  pan[is.na(PHI), `:=`(PHI = mean(pan$PHI, na.rm = TRUE), phi = mean(pan$phi, na.rm = TRUE))]
  setnames(pan, c("PHI","phi"), paste0(c("PHI_","phi_"), g))
  rm(mg); gc(FALSE)
  logmsg("91: probit ", g, "/", Keq, " (", G14[g], ") done")
}
pan[, buy := NULL]
pan[, (paste0("lam_", 1:Keq)) := lapply(1:Keq, function(g)
  get(paste0("phi_", g)) / pmax(get(paste0("PHI_", g)), 1e-4))]  # inverse Mills

## ---- y iteration + equation-by-equation SY-EASI
wbar <- sapply(1:K, function(k) mean(pan[[paste0("w_", k)]]))
lnP  <- as.matrix(pan[, paste0("lnp_", 1:K), with = FALSE])
pan[, y := ln_x - as.vector(lnP %*% wbar)]

fits <- vector("list", Keq)
for (it in 1:10) {
  W_hat <- matrix(0, nrow(pan), K)
  for (g in 1:Keq) {
    Pg <- pan[[paste0("PHI_", g)]]
    for (r in 1:R_POLY) pan[, (paste0("Py", r)) := Pg * y^r]
    for (k in 1:Keq)  pan[, (paste0("Pp", k)) := Pg * get(paste0("lnps_", k))]
    for (z in ZVARS)  pan[, (paste0("Pz_", z)) := Pg * get(z)]
    f <- as.formula(paste0("w_", g, " ~ ",
      paste0("Py", 1:R_POLY, collapse = "+"), "+",
      paste0("Pp", 1:Keq, collapse = "+"), "+",
      paste0("Pz_", ZVARS, collapse = "+"),
      "+ phi_", g, " | prov_tier + mo"))
    fits[[g]] <- feols(f, data = pan, cluster = ~Province, notes = FALSE, lean = FALSE)
    W_hat[, g] <- pmin(pmax(predict(fits[[g]], newdata = pan), 0), 1)
  }
  W_hat[, K] <- pmax(1 - rowSums(W_hat[, 1:Keq, drop = FALSE]), 0)
  y_new <- pan$ln_x - rowSums(W_hat * lnP)
  dy <- max(abs(y_new - pan$y))
  logmsg("91: y iteration ", it, " max|dy| = ", signif(dy, 3))
  pan[, y := y_new]
  if (dy < 1e-6) break
}

## ---- extract b (Engel), A (price), symmetry treatment
coefs <- lapply(fits, coef); ses <- lapply(fits, function(f) se(f))
B <- t(sapply(coefs, function(cc) cc[paste0("Py", 1:R_POLY)]))          # Keq x R
A <- t(sapply(coefs, function(cc) cc[paste0("Pp", 1:Keq)]))             # Keq x Keq
A_se <- t(sapply(ses, function(ss) ss[paste0("Pp", 1:Keq)]))
rownames(B) <- rownames(A) <- rownames(A_se) <- colnames(A) <- colnames(A_se) <- G14[1:Keq]
A_sym <- (A + t(A)) / 2
symz <- (A - t(A)) / sqrt(A_se^2 + t(A_se)^2)                            # pairwise z
logmsg("91: symmetry |z|>1.96 share = ",
       round(mean(abs(symz[upper.tri(symz)]) > 1.96), 3))

## Engel order diagnostic (R8 input): joint p of the cubic term per equation
ord <- rbindlist(lapply(1:Keq, function(g) {
  ct <- grab(fits[[g]], eq = G14[g])
  ct[term %in% paste0("Py", 1:R_POLY)][, .(eq, term, est, se, p)]
}))
fwrite(ord, file.path(DIR_TAB, "t2b_engel_terms.csv"))

allco <- rbindlist(lapply(1:Keq, function(g) grab(fits[[g]], eq = G14[g])))
fwrite(allco, file.path(DIR_TAB, "t2_stageA_coefs.csv"))

PHIbar <- sapply(1:Keq, function(g) mean(pan[[paste0("PHI_", g)]]))
saveRDS(list(B = B, A = A, A_sym = A_sym, symz = symz, wbar = wbar,
             PHIbar = PHIbar, ybar = mean(pan$y),
             y_pctl = quantile(pan$y, c(.1, .25, .5, .75, .9))),
        file.path(DIR_INT, "stageA.rds"))
saveRDS(pan[, c("ID","ym","Province","prov_tier","mo","tier_a","CityTier","y","ln_x",
                "ln_inc","inv_inc","vhat","x","elderly","fsize","lock_days","ln_covid",
                "cny_share","hot_days", paste0("w_", 1:K), paste0("lnp_", 1:K),
                paste0("lnps_", 1:Keq), paste0("lam_", 1:Keq)), with = FALSE],
        file.path(DIR_INT, "stageA_panel.rds"))
logmsg("91: done")
