# Paper 9 script 95: method validation — Deaton/McKelvey forensic comparison.
#  (a) "price-blind" quality Engel curves at three cluster resolutions
#      (Deaton's identifying assumption = no price variation within cluster);
#      truth = theta from the observed-price design (t3).
#  (b) bias vs within-cluster price-variation share (McKelvey's prediction).
#  (c) naive uv-based own-price elasticity vs observed-price version.
#  Note: exact Yu-Abler (2009) correction formulas are not reproducible
#  offline; we report the recovery diagnostic theta_true / gamma_naive, which
#  is the object their correction targets. Labeled as such in T7.
source("/root/data/Paper/央视数据/paper9-easiq/code/00_setup.R")
suppressPackageStartupMessages(library(ggplot2))

qd <- readRDS(file.path(DIR_INT, "quality_panel.rds"))
spA <- readRDS(file.path(DIR_INT, "stageA_panel.rds"))
qd <- merge(qd, spA[, .(ID, ym, y, vhat)], by = c("ID","ym"))
th <- fread(file.path(DIR_TAB, "t3_theta.csv"), encoding = "UTF-8")[eval_at == "mean",
                                                                    .(category, theta_true = theta)]
pb <- fread(file.path(DIR_INT, "base_price_prov_month.csv.gz"), encoding = "UTF-8")
qd[, `:=`(ln_uv = log(uv), qtr = paste0(substr(ym, 1, 4), "Q", ceiling(as.integer(substr(ym, 6, 7)) / 3)))]
ZB <- "fsize + elderly + lock_days + ln_covid + cny_share + hot_days"
qd[is.na(fsize), fsize := median(qd$fsize, na.rm = TRUE)]

## (a) Deaton-style: ln uv (NOT premium) with cluster FE only; theta = dlnuv/dy
specs <- list(fine = "ID + prov_tier^ym", quarter = "ID + Province^qtr", province = "ID + Province",
              xsec_fine = "prov_tier^ym", xsec_province = "Province")  # Deaton's actual cross-sectional setting
dt7 <- rbindlist(lapply(names(specs), function(sn) rbindlist(lapply(PK13, function(cc) {
  m <- feols(as.formula(paste0("ln_uv ~ y + ", ZB, " | ", specs[[sn]])),
             data = qd[Category == cc], cluster = ~Province, notes = FALSE)
  data.table(category = cc, cluster_def = sn, theta_naive = coef(m)["y"], se = se(m)["y"])
}))))
dt7 <- merge(dt7, th, by = "category")
dt7[, `:=`(bias = theta_naive - theta_true, recovery = theta_true / theta_naive)]

## (b) within-cluster price variation share per category (province-level base
## price varies across months within Province / Province^qtr clusters)
pv <- merge(qd[, .(ID, ym, Province, qtr, Category, ln_uv)],
            pb[Category %in% PK13, .(Province, ym, Category, lnp = log(p_base))],
            by = c("Province","ym","Category"))
vr <- pv[, {
  vp_prov <- var(lnp - ave(lnp, Province))         # price var within Province cluster
  vu_prov <- var(ln_uv - ave(ln_uv, Province))
  .(price_var_share_prov = vp_prov / vu_prov)
}, by = Category]
dt7 <- merge(dt7, vr, by.x = "category", by.y = "Category", all.x = TRUE)
fwrite(dt7, file.path(DIR_TAB, "t7_deaton_mckelvey.csv"))
logmsg("95: mean |bias| fine/quarter/province = ",
       paste(dt7[, round(mean(abs(bias)), 4), by = cluster_def]$V1, collapse = " / "))

## (c) naive own-price elasticity using uv as price (no observed price):
## lnQ ~ ln_uv (classic uv regression) vs lnQ ~ ln p_obs
ce <- rbindlist(lapply(PK13, function(cc) {
  dg <- merge(qd[Category == cc], pb[Category == cc, .(Province, ym, lnp = log(p_base))],
              by = c("Province","ym"))
  m1 <- feols(lnQ ~ ln_uv + y | ID + mo + Province, data = dg, cluster = ~Province, notes = FALSE)
  m2 <- feols(lnQ ~ lnp  + y | ID + mo + Province, data = dg, cluster = ~Province, notes = FALSE)
  data.table(category = cc, eps_uv_naive = coef(m1)["ln_uv"], eps_pobs = coef(m2)["lnp"])
}))
fwrite(ce, file.path(DIR_TAB, "t7b_price_elasticity_uv_vs_obs.csv"))

## F5 bias scatter
pl <- dt7[cluster_def == "province"]
ggsave(file.path(DIR_FIG, "fig5_mckelvey_bias.png"), width = 7, height = 6, dpi = 150,
  plot = ggplot(pl, aes(theta_true, theta_naive)) +
    geom_abline(linetype = 2) + geom_point(aes(size = price_var_share_prov), color = "firebrick") +
    geom_text(aes(label = category), size = 2.6, vjust = -0.8) +
    labs(x = "theta (observed-price design)", y = "theta (Deaton price-blind, province cluster)",
         size = "within-cluster\nprice-var share",
         title = "McKelvey bias: price-blind vs observed-price quality elasticity") +
    theme_minimal(base_size = 11))
logmsg("95: done")
