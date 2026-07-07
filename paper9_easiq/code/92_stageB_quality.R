# Paper 9 script 92: Stage B — 13 quality-premium equations.
#  FE version (theta): r ~ poly(y,R) + z + lambda_sel + vhat | ID + prov_tier^ym
#  Price version (Psi, Marshallian): r ~ ln_x + 14 lnP + z + ... | ID + prov_tier + mo
#  Homogeneity test per category: sum_k psi_gk + theta_g = 0 (T2 of the theory)
#  Metering-layer IPW for 大米/面粉/坚果 (Volume coverage 63-74%).
source("/root/data/Paper/央视数据/paper9-easiq/code/00_setup.R")

qd  <- readRDS(file.path(DIR_INT, "quality_panel.rds"))
spA <- readRDS(file.path(DIR_INT, "stageA_panel.rds"))
qd <- merge(qd, spA[, .(ID, ym, y, vhat)], by = c("ID","ym"))
## selection term of the category's own purchase probit (from Stage A layer)
lam <- melt(spA[, c("ID","ym", paste0("lam_", 1:13)), with = FALSE],
            id.vars = c("ID","ym"), variable.name = "gidx", value.name = "lam_sel")
lam[, Category := PK13[as.integer(sub("lam_", "", gidx))]][, gidx := NULL]
qd <- merge(qd, lam, by = c("ID","ym","Category"))

## metering-layer IPW (recording probability of Volume given purchase)
PART <- c("大米","面粉","坚果")
tr_cov <- fread(file.path(DIR_TAB, "t1_uv_descriptives.csv"), encoding = "UTF-8")
qd[, ipw := 1]
if (all(PART %in% qd$Category)) {
  raw <- fread(file.path(RAW, "Data_merged.csv"), encoding = "UTF-8",
               select = c("ID","Province","Date","Category","Spend","Volume"))[Category %in% PART & Spend > 0]
  raw[grepl("/", Date), date := as.IDate(Date, format = "%Y/%m/%d")]
  raw[is.na(date), date := as.IDate(substr(Date, 1, 10), format = "%Y-%m-%d")]
  raw[, `:=`(ym = format(date, "%Y-%m"), rec = as.integer(Volume > 0 & is.finite(Volume)),
             ln_sp = log(Spend))]
  for (cc in PART) {
    mrec <- feglm(rec ~ ln_sp | Province + ym, data = raw[Category == cc],
                  family = binomial("logit"), notes = FALSE)
    ph <- raw[Category == cc][as.integer(obs(mrec)), .(ID, ym, phat = predict(mrec, type = "response"))]
    ph <- ph[, .(phat = mean(phat)), by = .(ID, ym)]
    qd[Category == cc, ipw := {
      m <- merge(.SD, ph, by = c("ID","ym"), all.x = TRUE)
      1 / pmin(pmax(fifelse(is.na(m$phat), mean(ph$phat), m$phat), .1), 1)
    }]
  }
  rm(raw); gc()
}

ZB <- "fsize + elderly + lock_days + ln_covid + cny_share + hot_days"
qd[is.na(fsize), fsize := median(qd$fsize, na.rm = TRUE)]

## ---- FE version: theta per category
fe_res <- list(); th_tab <- list()
yq <- readRDS(file.path(DIR_INT, "stageA.rds"))$y_pctl
ybar <- readRDS(file.path(DIR_INT, "stageA.rds"))$ybar
for (cc in PK13) {
  dg <- qd[Category == cc]
  m <- feols(as.formula(paste0("r_prem ~ ", POLY_Y(), " + ", ZB, " + lam_sel + vhat | ID + prov_tier^ym")),
             data = dg, cluster = ~ID + Province, weights = ~ipw, notes = FALSE)
  fe_res[[cc]] <- grab(m, category = cc, model = "FE_theta")
  kap <- coef(m)[paste0("I(y^", 1:R_POLY, ")")]
  V <- vcov(m)[paste0("I(y^", 1:R_POLY, ")"), paste0("I(y^", 1:R_POLY, ")")]
  th_tab[[cc]] <- data.table(
    category = cc,
    eval_at = c("mean", paste0("p", c(10, 25, 50, 75, 90))),
    y0 = c(ybar, yq),
    theta = sapply(c(ybar, yq), function(y0) theta_at(kap, y0)),
    se = sapply(c(ybar, yq), function(y0) theta_se(V, y0)),
    n = nobs(m))
  logmsg("92: FE theta ", cc, " = ", round(th_tab[[cc]][1, theta], 4))
}
fwrite(rbindlist(fe_res), file.path(DIR_TAB, "t3a_stageB_FE_coefs.csv"))
tt <- rbindlist(th_tab); tt[, `:=`(t = theta / se, p = 2 * pnorm(-abs(theta / se)))]
fwrite(tt, file.path(DIR_TAB, "t3_theta.csv"))

## ---- price version: Psi (Marshallian; omega = ln_x)
LNP <- paste0("lnp_", 1:14)
ps_res <- list(); hom <- list()
for (cc in PK13) {
  dg <- qd[Category == cc]
  dg <- merge(dg, spA[, c("ID","ym", LNP), with = FALSE], by = c("ID","ym"))
  m <- feols(as.formula(paste0("r_prem ~ ln_x + ", paste(LNP, collapse = "+"), " + ",
                               ZB, " + lam_sel + vhat | ID + prov_tier + mo")),
             data = dg, cluster = ~ID + Province, weights = ~ipw, notes = FALSE)
  ps_res[[cc]] <- grab(m, category = cc, model = "price_psiM")
  ## homogeneity: sum(psi) + theta = 0, theta here = d r/d ln x = coef ln_x
  bn <- names(coef(m)); pk <- intersect(LNP, bn)
  L <- rep(0, length(bn)); names(L) <- bn
  L[pk] <- 1; L["ln_x"] <- 1
  est <- sum(coef(m)[names(L)] * L)
  seL <- sqrt(as.numeric(t(L) %*% vcov(m) %*% L))
  hom[[cc]] <- data.table(category = cc, sum_psi_plus_theta = est, se = seL,
                          z = est / seL, p = 2 * pnorm(-abs(est / seL)))
}
fwrite(rbindlist(ps_res), file.path(DIR_TAB, "t3b_stageB_price_coefs.csv"))
fwrite(rbindlist(hom), file.path(DIR_TAB, "t6b_homogeneity_test.csv"))
logmsg("92: homogeneity rejected (5%) for ",
       rbindlist(hom)[p < .05, .N], "/13 categories")
logmsg("92: done")
