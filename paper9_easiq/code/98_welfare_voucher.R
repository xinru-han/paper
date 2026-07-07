# Paper 9 script 98: welfare buffer + dairy voucher "quality leakage" simulation
# + nutritional content of the quality ladder (7.4).
source("/root/data/Paper/央视数据/paper9-easiq/code/00_setup.R")

qd <- readRDS(file.path(DIR_INT, "quality_panel.rds"))
spA <- readRDS(file.path(DIR_INT, "stageA_panel.rds"))
own <- fread(file.path(DIR_TAB, "t6d_ownprice_before_after.csv"), encoding = "UTF-8")
pb  <- fread(file.path(DIR_INT, "base_price_prov_month.csv.gz"), encoding = "UTF-8")
t4  <- fread(file.path(DIR_TAB, "t4_two_margin_elasticities.csv"), encoding = "UTF-8")

## ---- 7.2 quality buffer: 0.5 * x * sum_g w_g |psi_gg| (dlnp_g)^2
dp <- pb[Category %in% PK13 & ym %in% c("2020-01", "2022-12")]
dp <- dcast(dp, Province + Category ~ ym, value.var = "p_base")
dp[, dlnp := log(`2022-12` / `2020-01`)]
dpn <- dp[, .(dlnp = mean(dlnp, na.rm = TRUE)), by = Category]
wsh <- spA[, lapply(.SD, mean), .SDcols = paste0("w_", 1:13)]
buf <- data.table(category = PK13, w = as.numeric(wsh),
                  psi_own = own$psiM_own[match(PK13, own$category)],
                  dlnp = dpn$dlnp[match(PK13, dpn$Category)])
xbar <- mean(spA$x)
buf[, buffer_yuan_m := 0.5 * xbar * w * abs(psi_own) * dlnp^2]
fwrite(buf, file.path(DIR_TAB, "t13_quality_buffer.csv"))
logmsg("98: total quality buffer = ", round(sum(buf$buffer_yuan_m, na.rm = TRUE), 3),
       " yuan/hh/month (of x = ", round(xbar), ")")

## ---- 7.3 dairy voucher simulation (25% price voucher on the 5 dairy cats)
dlv <- log(0.75)
spA[, ln_inc_ok := is.finite(ln_inc)]
spA[, inc_ter := cut(ln_inc, quantile(ln_inc, c(0, 1/3, 2/3, 1), na.rm = TRUE),
                     labels = c("T1","T2","T3"), include.lowest = TRUE)]
qd <- merge(qd, spA[, .(ID, ym, inc_ter, y, vhat)], by = c("ID","ym"))
ZB <- "fsize + elderly + lock_days + ln_covid + cny_share + hot_days"
qd[is.na(fsize), fsize := median(qd$fsize, na.rm = TRUE)]

## tercile-specific dairy psi_own and eps_q (pooled dairy5, own log base price)
vres <- rbindlist(lapply(c("T1","T2","T3"), function(tt) {
  dg <- merge(qd[Category %in% DAIRY5 & inc_ter == tt],
              pb[Category %in% DAIRY5, .(Province, ym, Category, lnp_own = log(p_base))],
              by = c("Province","ym","Category"))
  mr <- feols(as.formula(paste0("r_prem ~ lnp_own + y + ", ZB, " | ID^Category + mo + Province")),
              data = dg, cluster = ~Province, notes = FALSE)
  mq <- feols(as.formula(paste0("lnQ ~ lnp_own + y + ", ZB, " | ID^Category + mo + Province")),
              data = dg, cluster = ~Province, notes = FALSE)
  base <- dg[, .(Q_mo = sum(Q), X_mo = sum(X), n_hhm = uniqueN(paste(ID, ym)))]
  data.table(tercile = tt, psi_own = coef(mr)["lnp_own"], eps_q = coef(mq)["lnp_own"],
             Q_pm = base$Q_mo / base$n_hhm, X_pm = base$X_mo / base$n_hhm)
}))
vres[, `:=`(dlnQ = eps_q * dlv, dr = psi_own * dlv)]
## leakage: share of the induced value change absorbed by unit-value upgrading
vres[, leakage := dr / (dr + dlnQ)]
## fiscal cost per extra kg/L of dairy: subsidy = 25% of new spend
vres[, `:=`(dQ = Q_pm * (exp(dlnQ) - 1),
            outlay = 0.25 * X_pm * exp(dlnQ + dr))]
vres[, cost_per_unit := outlay / pmax(dQ, 1e-9)]
## cash comparison: same outlay as income transfer -> dlnx = outlay/x; dairy
## quantity gain via eta_dir(dairy avg)
eta_dairy <- t4[category %in% DAIRY5, mean(eta_dir)]
chi_dairy <- t4[category %in% DAIRY5, mean(chi)]
vres[, dQ_cash := Q_pm * (exp(eta_dairy * outlay / xbar) - 1)]
vres[, cash_cost_per_unit := outlay / pmax(dQ_cash, 1e-9)]
fwrite(vres, file.path(DIR_TAB, "t10_voucher_leakage.csv"))
logmsg("98: voucher leakage T1/T2/T3 = ", paste(round(vres$leakage, 3), collapse = " / "))

## ---- 7.4 nutrition content of the dairy ladder
nut <- fread(file.path(P8, "data/lookups/nutrient_coef_cn.csv"), encoding = "UTF-8")
lad <- fread(file.path(DIR_LKP, "quality_ladder.csv"), encoding = "UTF-8")
nd <- merge(lad[Category %in% DAIRY5, .(Category, uv_med)],
            nut[, .(Category, protein, ca_mg)], by = "Category", all.x = TRUE)
if (all(is.na(nd$protein))) logmsg("98: WARNING nutrient join empty — check category names") else {
  m <- lm(log(protein) ~ log(uv_med), data = nd[protein > 0])
  fwrite(data.table(gradient_ln_prot_per_ln_uv = coef(m)[2],
                    se = summary(m)$coefficients[2, 2], n = nobs(m)),
         file.path(DIR_TAB, "t10b_ladder_nutrition_gradient.csv"))
}
fwrite(nd, file.path(DIR_TAB, "t10c_dairy_ladder_nutrients.csv"))
logmsg("98: done")
