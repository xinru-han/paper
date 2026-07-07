# Paper 8 script 06 (= plan 82): price channel vs demand channel
#  (a) price equation: monitored ln price (province x monitor-date x group) on
#      trailing-10-day mean temperature bins
#  (b) decomposition: total spend response (from 05, PPML) minus the
#      price-channel prediction Sum_k [1{k=g} + E_gk] * gamma_k^b, with E the
#      NSD-repaired Marshallian elasticity matrix from Paper 1 outputs
#      (fallback: literature own-price diagonal), per plan §3.3 / README §六.7.
source("/root/data/Paper/央视数据/paper8-hot/code/00_setup.R")

## ---- (a) price equation
pr <- fread(file.path(P1, "processed/external_food_prices_category_province_monitor_date_cleaned_2020_2022.csv"),
            encoding = "UTF-8")
pr <- pr[price_fill_level == "observed_province_monitor_date" &
           is.finite(external_log_price_monitor)]
pr[, date := as.IDate(date)]
prg <- pr[, .(lnp = mean(external_log_price_monitor)), by = .(province, date, food_group10)]

expo <- fread(file.path(DIR_INT, "province_tier_day_weather.csv.gz"), encoding = "UTF-8")
expo[, date := as.IDate(date)]
capw <- expo[tier_a == 1L][order(province, date)]
capw[, tavg10 := frollmean(tavg, 10, align = "right"), by = province]  # dekad window
prg <- merge(prg, capw[, .(province, date, tavg10)], by = c("province","date"))
prg[, `:=`(tbin10 = tbin_cut(tavg10), ym = format(date, "%Y-%m"))]

# price fill for quantity imputation downstream (all fill levels)
prq <- fread(file.path(P1, "processed/external_food_prices_category_province_monitor_date_cleaned_2020_2022.csv"),
             encoding = "UTF-8",
             select = c("province","date","Category","external_price_mean_monitor","units"))
fwrite(prq, file.path(DIR_INT, "price_cat_province_date.csv.gz"))

gam <- list()
for (g in G10) {
  mg <- feols(lnp ~ tbin10 | province^ym, data = prg[food_group10 == g],
              cluster = ~province, notes = FALSE)
  ct <- as.data.table(coeftable(mg), keep.rownames = "term")
  setnames(ct, c("term","est","se","t","p"))
  gam[[g]] <- ct[, `:=`(group = g, n = nobs(mg))]
}
gam <- rbindlist(gam)
fwrite(gam, file.path(DIR_TAB, "t3_price_equation.csv"))
logmsg("06: price equation done")

# outlet heterogeneity is not identifiable here (P1 file pools outlets);
# noted in README as deferred to the city-level dekad parse (P7 script 70a).

## ---- (b) elasticity matrix with curvature repair
E <- NULL
el_file <- file.path(P1, "repro_run/outputs/demand/marshallian_elasticity_monthly_fast_r.csv")
w_bar <- {
  hmg <- fread(file.path(DIR_INT, "unit_day_cat.csv.gz"), encoding = "UTF-8")
  sh <- hmg[, .(s = sum(spend)), by = food_group10][, s := s / sum(s)]
  setkey(sh, food_group10); sh[J(G10), s]
}
if (file.exists(el_file)) {
  el <- fread(el_file, encoding = "UTF-8")   # wide: demand_group x 10 price cols
  if (all(G10 %in% el$demand_group) && all(G10 %in% names(el))) {
    E <- as.matrix(el[match(G10, demand_group), G10, with = FALSE])
    rownames(E) <- G10
  }
}
eta <- rep(1, 10)
eta_file <- file.path(P1, "repro_run/outputs/demand/food_expenditure_elasticity_monthly_fast_r.csv")
if (file.exists(eta_file)) {
  ee <- fread(eta_file, encoding = "UTF-8")
  gcol <- intersect(c("demand_group","food_group10","group"), names(ee))[1]
  vcol <- setdiff(names(ee), gcol)[1]
  if (!is.na(gcol) && all(G10 %in% ee[[gcol]]))
    eta <- as.numeric(ee[[vcol]][match(G10, ee[[gcol]])])
}
if (!is.null(E) && all(is.finite(E))) {
  # Slutsky (share-weighted): S_ij = w_i (E_ij + w_j * eta_i)
  S <- diag(w_bar) %*% (E + outer(eta, w_bar))
  Ssym <- (S + t(S)) / 2
  ev <- eigen(Ssym)
  ev$values <- pmin(ev$values, 0)              # nearest NSD projection
  S_rep <- ev$vectors %*% diag(ev$values) %*% t(ev$vectors)
  E_rep <- diag(1 / w_bar) %*% S_rep - outer(eta, w_bar)
  rownames(E_rep) <- colnames(E_rep) <- G10
  logmsg("06: elasticities repaired; own-price range ",
         paste(round(range(diag(E_rep)), 2), collapse = " to "))
} else {
  logmsg("06: P1 elasticity file unusable -> literature fallback diagonal")
  E_rep <- diag(c(-0.4,-0.5,-0.6,-0.7,-0.8,-0.8,-0.9,-0.9,-0.7,-0.6))
  rownames(E_rep) <- colnames(E_rep) <- G10
}
saveRDS(list(E = E_rep, w = w_bar), file.path(DIR_INT, "elasticity_repaired.rds"))

## ---- decomposition at the hot bin (and cold bin)
main <- fread(file.path(DIR_TAB, "t1_main_coefs.csv"))
dec <- rbindlist(lapply(c("gt30","le0"), function(b) {
  gmat <- sapply(G10, function(g) {
    v <- gam[group == g & term == paste0("tbin10", b), est]
    if (length(v)) v else 0
  })
  tot <- sapply(G10, function(g)
    main[outcome == paste0("spend|trip_", g) & model == "ppml" & term == paste0("tbin", b), est][1])
  # d ln spend_g from prices = d ln p_g + Sum_k E_gk d ln p_k
  pch <- gmat + as.vector(E_rep %*% gmat)
  data.table(bin = b, group = G10, total_spend_resp = tot,
             price_gamma = gmat, price_channel = pch, demand_channel = tot - pch)
}))
fwrite(dec, file.path(DIR_TAB, "t4_channel_decomposition.csv"))
logmsg("06: channel decomposition written")
print(dec[bin == "gt30"])
