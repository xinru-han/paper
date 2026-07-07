# Paper 9 script 96: quality margin under shocks — r and lnQ reported in pairs.
#  (1) income-band jump pecking-order event study (persistent >=3-month jumps)
#  (2) lockdown, (3) pork price x exposure, (4) Spring Festival, (5) hot days
source("/root/data/Paper/央视数据/paper9-easiq/code/00_setup.R")
suppressPackageStartupMessages(library(ggplot2))

qd <- readRDS(file.path(DIR_INT, "quality_panel.rds"))
spA <- readRDS(file.path(DIR_INT, "stageA_panel.rds"))
qd <- merge(qd, spA[, .(ID, ym, y, vhat, ln_inc)], by = c("ID","ym"))
qd[, `:=`(r_dm = r_prem - mean(r_prem), lnQ_dm = lnQ - mean(lnQ)), by = Category]  # pool categories
qd[is.na(fsize), fsize := median(qd$fsize, na.rm = TRUE)]
ZB <- "fsize + elderly + lock_days + ln_covid + cny_share + hot_days"
ZB_noshock <- "fsize + elderly + ln_covid"

## ---- (1) pecking order: persistent income-band jumps
inc <- unique(spA[, .(ID, ym, ln_inc)])[order(ID, ym)]
inc[, `:=`(l1 = shift(ln_inc), f1 = shift(ln_inc, -1), f2 = shift(ln_inc, -2)), by = ID]
inc[, jump := fifelse(!is.na(l1) & ln_inc != l1 & ln_inc == f1 & ln_inc == f2,
                      sign(ln_inc - l1), 0)]
ev <- inc[jump != 0, .(ID, ym_ev = ym, dir = jump)]
ev <- ev[, .SD[1], by = ID]                       # first persistent jump per hh
logmsg("96: persistent jumps — up ", ev[dir > 0, .N], ", down ", ev[dir < 0, .N])
mnum <- function(s) as.integer(substr(s, 1, 4)) * 12L + as.integer(substr(s, 6, 7))
qd[, mn := mnum(ym)]
evq <- merge(qd, ev, by = "ID")
evq[, rel := mn - mnum(ym_ev)]
evq <- evq[rel %between% c(-6, 6)]
es <- list()
for (dd in c(1, -1)) for (out in c("r_dm","lnQ_dm")) {
  m <- feols(as.formula(paste0(out, " ~ i(rel, ref = -1) + ", ZB, " | ID^Category + prov_tier^ym")),
             data = evq[dir == dd], cluster = ~ID, notes = FALSE)
  es[[paste(dd, out)]] <- grab(m, outcome = out, dir = fifelse(dd > 0, "up", "down"))[grepl("rel", term)]
}
est <- rbindlist(es)
fwrite(est, file.path(DIR_TAB, "t8a_pecking_order_es.csv"))
est[, rel := as.integer(gsub(".*::(-?\\d+).*", "\\1", term))]
ggsave(file.path(DIR_FIG, "fig6_pecking_order.png"), width = 9, height = 6, dpi = 150,
  plot = ggplot(est, aes(rel, est, color = outcome)) +
    geom_hline(yintercept = 0, linetype = 2) + geom_vline(xintercept = -0.5, linetype = 3) +
    geom_pointrange(aes(ymin = est - 1.96 * se, ymax = est + 1.96 * se),
                    position = position_dodge(.3)) +
    facet_wrap(~dir) + theme_minimal(base_size = 11) +
    labs(x = "months relative to persistent income-band jump", y = "effect",
         title = "Pecking order: quality premium (r) vs quantity (lnQ)"))

## ---- (2)-(5) shock coefficient pairs (pooled PK13, demeaned outcomes)
shock_pair <- function(dt, rhs_shock, label, fe = "ID^Category + prov_tier + mo") {
  rbindlist(lapply(c("r_dm","lnQ_dm"), function(out) {
    m <- feols(as.formula(paste0(out, " ~ ", rhs_shock, " + y + ", ZB_noshock, " | ", fe)),
               data = dt, cluster = ~Province, notes = FALSE)
    grab(m, outcome = out, shock = label)[!term %in% c("y","vhat","fsize","elderly","ln_covid")]
  }))
}
t8 <- list()
t8$lock <- shock_pair(qd, "lock_days", "lockdown")
t8$cny  <- shock_pair(qd, "cny_share", "spring_festival")
t8$hot  <- shock_pair(qd[Category %in% DAIRY5], "hot_days", "hot_days_dairy")

## pork price x exposure
pr <- fread(file.path(P1, "processed/external_food_prices_category_province_monitor_date_cleaned_2020_2022.csv"),
            encoding = "UTF-8")[Category == "猪肉" & price_fill_level == "observed_province_monitor_date"]
pk <- pr[, .(ln_ppork = log(mean(external_price_mean_monitor))), by = .(Province = province, ym = substr(date, 1, 7))]
expo0 <- fread(file.path(RAW, "Data_merged.csv"), encoding = "UTF-8",
               select = c("ID","Date","Category","Spend"))
expo0[, ym := fifelse(grepl("/", Date), format(as.IDate(Date, format = "%Y/%m/%d"), "%Y-%m"),
                      substr(Date, 1, 7))]
e_i <- expo0[ym <= "2020-06", .(pork_sh = sum(Spend[Category == "猪肉"]) / sum(Spend)), by = ID]
rm(expo0); gc()
qp <- merge(qd, pk, by = c("Province","ym"))
qp <- merge(qp, e_i, by = "ID")
qp[, exp_pork := pork_sh * ln_ppork]
t8$pork <- shock_pair(qp, "exp_pork", "pork_price_exposure", fe = "ID^Category + prov_tier + ym")
fwrite(rbindlist(t8, fill = TRUE), file.path(DIR_TAB, "t8_shock_pairs.csv"))
logmsg("96: done")
