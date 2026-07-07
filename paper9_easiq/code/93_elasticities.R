# Paper 9 script 93: elasticity algebra + two-margin table + diagnostics.
#  chi_g(y)  expenditure elasticity of category spend (Stage A)
#  theta_g(y) quality elasticity (Stage B, t3)
#  eta_dir    direct quantity elasticity (ln Q on the Stage-B FE spec)
#  identity diagnostics (system vs accounting, selection gap), income-quality
#  elasticity via the LLI multiplier, quality floor (quantile), dairy
#  within/between decomposition.
source("/root/data/Paper/央视数据/paper9-easiq/code/00_setup.R")

sa <- readRDS(file.path(DIR_INT, "stageA.rds"))
qd <- readRDS(file.path(DIR_INT, "quality_panel.rds"))
spA <- readRDS(file.path(DIR_INT, "stageA_panel.rds"))
qd <- merge(qd, spA[, .(ID, ym, y, vhat)], by = c("ID","ym"))
lnk <- readRDS(file.path(DIR_INT, "income_link.rds"))
th <- fread(file.path(DIR_TAB, "t3_theta.csv"), encoding = "UTF-8")

## ---- chi_g at mean y
chi_at <- function(g, y0) {
  b <- sa$B[g, ]
  1 + sa$PHIbar[g] * sum(seq_len(R_POLY) * b * y0^(seq_len(R_POLY) - 1)) / sa$wbar[g]
}
chi <- data.table(category = PK13,
                  chi = sapply(1:13, function(g) chi_at(g, sa$ybar)))

## ---- eta direct: ln Q, same RHS as Stage B FE version
ZB <- "fsize + elderly + lock_days + ln_covid + cny_share + hot_days"
qd[is.na(fsize), fsize := median(qd$fsize, na.rm = TRUE)]
eta_dir <- rbindlist(lapply(PK13, function(cc) {
  m <- feols(as.formula(paste0("lnQ ~ ", POLY_Y(), " + ", ZB, " + vhat | ID + prov_tier^ym")),
             data = qd[Category == cc], cluster = ~ID + Province, notes = FALSE)
  kap <- coef(m)[paste0("I(y^", 1:R_POLY, ")")]
  V <- vcov(m)[paste0("I(y^", 1:R_POLY, ")"), paste0("I(y^", 1:R_POLY, ")")]
  data.table(category = cc, eta_dir = theta_at(kap, sa$ybar),
             eta_se = theta_se(V, sa$ybar), n = nobs(m))
}))

## ---- T4 two-margin table
t4 <- merge(chi, th[eval_at == "mean", .(category, theta, theta_se = se)], by = "category")
t4 <- merge(t4, eta_dir, by = "category")
t4[, `:=`(eta_derived = chi - theta,
          diag_system_vs_account = chi - (theta + eta_dir),
          income_quality_elast = theta * lnk$mult_within)]
fwrite(t4, file.path(DIR_TAB, "t4_two_margin_elasticities.csv"))
logmsg("93: T4 written; mean theta = ", round(mean(t4$theta), 3),
       " mean chi = ", round(mean(t4$chi), 3))

## ---- T5 diagnostics: selection gap = eta_dir on recorded subsample vs
## (chi - theta); plus residual-method theta (Hovhannisyan style: chi - eta_dir)
t5 <- t4[, .(category, chi_EASI = chi, theta_direct = theta, eta_direct = eta_dir,
             theta_residual = chi - eta_dir,
             gap_system_vs_account = diag_system_vs_account)]
fwrite(t5, file.path(DIR_TAB, "t5_decomposition_diagnostics.csv"))

## ---- price elasticities from Stage A (symmetrized A; numeraire recovered
## by homogeneity: a_g,14 = -sum_k a_gk)
A13 <- sa$A_sym
Afull <- cbind(A13, -rowSums(A13))
eH <- sweep(Afull, 1, sa$wbar[1:13], "/") + matrix(rep(sa$wbar, each = 13), 13)
diag(eH) <- diag(eH) - 1
eM <- eH - outer(t4$chi[match(PK13, t4$category)], sa$wbar)
rownames(eH) <- rownames(eM) <- PK13
colnames(eH) <- colnames(eM) <- G14
fwrite(as.data.table(eM, keep.rownames = "category"), file.path(DIR_TAB, "t4b_marshallian_eM.csv"))
saveRDS(list(eH = eH, eM = eM), file.path(DIR_INT, "price_elasticities.rds"))

## ---- quality floor: quantile theta (Canay two-step: within-transform on ID)
suppressPackageStartupMessages(library(quantreg))
qf <- qd[, .(ID, Category, r_prem, y)]
qf[, `:=`(r_w = r_prem - mean(r_prem) , y_w = y - mean(y)), by = .(ID, Category)]
set.seed(20260707)
qs <- qf[sample(.N, min(.N, 3e5))]
taus <- c(.1, .25, .5, .75, .9)
qtab <- rbindlist(lapply(taus, function(tu) {
  fq <- rq(r_w ~ y_w, tau = tu, data = qs, method = "pfn")
  data.table(tau = tu, theta_q = coef(fq)["y_w"])
}))
fwrite(qtab, file.path(DIR_TAB, "t11b_quality_floor_quantiles.csv"))
logmsg("93: quality floor theta by tau: ",
       paste(round(qtab$theta_q, 3), collapse = " / "))

## ---- dairy within/between (Bils-Klenow style variance + Engel split)
dai <- readRDS(file.path(DIR_INT, "dairy_panel.rds"))
dai <- merge(dai, spA[, .(ID, ym, y, vhat, prov_tier)], by = c("ID","ym"))
dai[, r_total := r_within + r_between]
vshare <- dai[, .(var_within = var(r_within), var_between = var(r_between),
                  cov2 = 2 * cov(r_within, r_between))][ ,
             lapply(.SD, function(v) v / (var_within + var_between + cov2))]
m_w <- feols(r_within ~ y + vhat | ID + prov_tier^ym, data = dai, cluster = ~ID)
m_b <- feols(r_between ~ y + vhat | ID + prov_tier^ym, data = dai, cluster = ~ID)
t11 <- data.table(component = c("within_uv","between_ladder"),
                  theta = c(coef(m_w)["y"], coef(m_b)["y"]),
                  se = c(se(m_w)["y"], se(m_b)["y"]),
                  var_share = c(vshare$var_within, vshare$var_between))
fwrite(t11, file.path(DIR_TAB, "t11_within_between_dairy.csv"))

## ---- heterogeneity: theta by income tercile / elderly / tier
qd <- merge(qd, spA[, .(ID, ym, ln_inc2 = ln_inc)], by = c("ID","ym"))
qd[, inc_ter := cut(ln_inc2, quantile(ln_inc2, c(0, 1/3, 2/3, 1), na.rm = TRUE),
                    labels = c("T1","T2","T3"), include.lowest = TRUE)]
het <- rbindlist(lapply(list(c("inc_ter","T1"), c("inc_ter","T2"), c("inc_ter","T3"),
                             c("elderly","1"), c("elderly","0")), function(sp) {
  dg <- qd[get(sp[1]) == sp[2]]
  m <- feols(as.formula(paste0("r_prem ~ y + ", ZB, " + vhat | ID + prov_tier^ym")),
             data = dg, cluster = ~ID, notes = FALSE)
  data.table(split = paste0(sp[1], "=", sp[2]), theta_lin = coef(m)["y"], se = se(m)["y"], n = nobs(m))
}))
fwrite(het, file.path(DIR_TAB, "t11c_theta_heterogeneity.csv"))
logmsg("93: done")
