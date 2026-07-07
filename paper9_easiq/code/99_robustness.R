# Paper 9 script 99: robustness for the headline theta (mean-y, per category
# pooled to a single linear-y coefficient for comparability across specs).
#  R1 Tier A only | R2 excl. lockdown months | R3 quarterly aggregation
#  R4 tighter trim (2.5/97.5 within cat x prov, on hh-month uv)
#  R5 no IPW | R8 poly order (theta at mean from R=2 and R=4 fits)
#  R9 uv = within-month median instead of spend-weighted mean
source("/root/data/Paper/央视数据/paper9-easiq/code/00_setup.R")

qd <- readRDS(file.path(DIR_INT, "quality_panel.rds"))
spA <- readRDS(file.path(DIR_INT, "stageA_panel.rds"))
qd <- merge(qd, spA[, .(ID, ym, y, vhat)], by = c("ID","ym"))
qd[is.na(fsize), fsize := median(qd$fsize, na.rm = TRUE)]
ZB <- "fsize + elderly + lock_days + ln_covid + cny_share + hot_days"

theta_lin <- function(dt, dep = "r_prem", fe = "ID + prov_tier^ym", spec) {
  rbindlist(lapply(PK13, function(cc) {
    dg <- dt[Category == cc]
    if (nrow(dg) < 500) return(NULL)
    m <- tryCatch(feols(as.formula(paste0(dep, " ~ y + ", ZB, " | ", fe)),
                        data = dg, cluster = ~Province, notes = FALSE), error = function(e) NULL)
    if (is.null(m)) return(NULL)
    data.table(category = cc, spec = spec, theta = coef(m)["y"], se = se(m)["y"], n = nobs(m))
  }))
}

res <- list()
res$main <- theta_lin(qd, spec = "main_linear")
res$R1 <- theta_lin(qd[tier_a == 1L], spec = "R1_tierA")
res$R2 <- theta_lin(qd[lock_days == 0], spec = "R2_no_lockdown")

## R3 quarterly
q3 <- copy(qd)[, qtr := paste0(substr(ym, 1, 4), "Q", ceiling(as.integer(substr(ym, 6, 7)) / 3))]
q3 <- q3[, .(r_prem = weighted.mean(r_prem, X), y = mean(y), vhat = mean(vhat),
             fsize = fsize[1], elderly = elderly[1], lock_days = sum(lock_days),
             ln_covid = mean(ln_covid), cny_share = mean(cny_share), hot_days = sum(hot_days),
             Province = Province[1], prov_tier = prov_tier[1]),
         by = .(ID, qtr, Category)]
setnames(q3, "qtr", "ym")
res$R3 <- theta_lin(q3, fe = "ID + prov_tier^ym", spec = "R3_quarterly")

## R4 tighter trim on hh-month uv
q4 <- copy(qd)
q4[, `:=`(lo = quantile(uv, .025), hi = quantile(uv, .975)), by = .(Category, Province)]
res$R4 <- theta_lin(q4[uv %between% .(lo, hi)], spec = "R4_trim2.5")

## R9 median uv
q9 <- copy(qd)
pbm <- fread(file.path(DIR_INT, "base_price_prov_month.csv.gz"), encoding = "UTF-8")
q9 <- merge(q9, pbm[Category %in% PK13, .(Province, ym, Category, p_base2 = p_base)],
            by = c("Province","ym","Category"))
q9[, r_prem := log(uv_med) - log(p_base2)]
res$R9 <- theta_lin(q9, spec = "R9_median_uv")

## R8 poly order 2 and 4 (theta at mean y)
sa <- readRDS(file.path(DIR_INT, "stageA.rds"))
for (RR in c(2L, 4L)) {
  res[[paste0("R8_", RR)]] <- rbindlist(lapply(PK13, function(cc) {
    py <- paste0("I(y^", 1:RR, ")", collapse = " + ")
    m <- feols(as.formula(paste0("r_prem ~ ", py, " + ", ZB, " | ID + prov_tier^ym")),
               data = qd[Category == cc], cluster = ~Province, notes = FALSE)
    kap <- coef(m)[paste0("I(y^", 1:RR, ")")]
    data.table(category = cc, spec = paste0("R8_poly", RR),
               theta = theta_at(kap, sa$ybar, R = RR),
               se = theta_se(vcov(m)[paste0("I(y^", 1:RR, ")"), paste0("I(y^", 1:RR, ")")], sa$ybar, R = RR),
               n = nobs(m))
  }))
}
t12 <- rbindlist(res)
fwrite(t12, file.path(DIR_TAB, "t12_robustness.csv"))
logmsg("99: done — mean theta by spec:")
print(t12[, .(mean_theta = round(mean(theta), 4)), by = spec])
