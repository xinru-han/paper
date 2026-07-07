# Paper 8 script 05c (= plan 81, part 3): unit-level aggregate spec with the
# triple inference report (cluster SE + wild cluster bootstrap + permutation).
source("/root/data/Paper/央视数据/paper8-hot/code/00_setup.R")

utot <- readRDS(file.path(DIR_INT, "utot_frame.rds"))   # built by 08 (light)
ctrl <- "pbin + holiday_flag + spring_festival_window_7 + lockdown + ln_covid"
f_u <- as.formula(paste0("ln_spend_pc ~ tbin + ", ctrl, " | unit^ym + dow"))
m_u <- feols(f_u, data = utot, cluster = ~Province, weights = ~n_active)
ct <- as.data.table(coeftable(m_u), keep.rownames = "term")
setnames(ct, c("term","est","se","t","p"))
fwrite(ct, file.path(DIR_TAB, "t2a_unit_spec.csv"))

## permutation: within each unit, permute the YEAR label of the daily temp series
utot[, `:=`(yr = year(date), mo = month(date), md = mday(date))]
tkey <- utot[, .(unit, yr, mo, md, tbin0 = tbin)]
yrs <- sort(unique(utot$yr))
perm_fit <- function(s) {
  set.seed(s)
  pmap <- rbindlist(lapply(unique(utot$unit), function(u)
    data.table(unit = u, yr = yrs, yr_p = sample(yrs))))
  ut2 <- merge(utot, pmap, by = c("unit","yr"))
  ut2[, tbin_p := tkey[.(ut2$unit, ut2$yr_p, ut2$mo, ut2$md), on = .(unit, yr, mo, md), tbin0]]
  ut2[is.na(tbin_p), tbin_p := tbin]
  mp <- feols(as.formula(paste0("ln_spend_pc ~ tbin_p + ", ctrl, " | unit^ym + dow")),
              data = ut2, weights = ~n_active, notes = FALSE, warn = FALSE)
  coef(mp)
}
logmsg("05c: permutation x499 ...")
perm_mat <- sapply(1:499, perm_fit)

infr <- rbindlist(lapply(c("tbingt30", "tbinle0", "tbinb24_30"), function(cc) {
  b0 <- coef(m_u)[cc]
  pc <- perm_mat[paste0("tbin_p", sub("tbin", "", cc)), ]
  data.table(term = cc, est = b0, se = se(m_u)[cc], p_cluster = pvalue(m_u)[cc],
             p_wcb = wcb_pvalue(m_u, cc, utot, cl_var = "Province", B = 399, wvar = "n_active"),
             p_perm = mean(abs(pc) >= abs(b0)))
}))
fwrite(infr, file.path(DIR_TAB, "t2_inference_triple.csv"))
logmsg("05c: done")
print(infr)
