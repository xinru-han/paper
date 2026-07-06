#!/usr/bin/env Rscript
# ============================================================================
# 08_mechanisms_table6.R
# Table 6 (M2: precautionary saving / income-shock mechanism) -- ported from the
# ORIGINAL revision/07_mechanisms.R (found by the user in scripts/07_mechanisms.R),
# run against the locally rebuilt analysis.csv. This is the actual "Table 6" the
# modification plan refers to (工资/消费/存款/流动储蓄), NOT the wage-subsample
# robustness check in 06_wage_subsample_attrition.R (that is an ADD-ON column per
# the plan: "已有，加2013-20工资子样本列").
#
# Zero/outlier handling identical to the original: CPI-deflate (1978=100), NA kept
# NA (never filled 0), negatives -> NA, winsorize 1/99, then asinh() (retains zeros).
# ============================================================================
source("/root/data/Paper/covid/repro/scripts/00_common.R")
dt <- load_analysis()
dt <- dt[year<2023]

winz <- function(x,p=.01){ q<-quantile(x,c(p,1-p),na.rm=TRUE)
  x[!is.na(x) & x<q[1]]<-q[1]; x[!is.na(x) & x>q[2]]<-q[2]; x }

## ---- monetary stocks: deflate, NA-safe, winsorize, asinh ----
dt[, deposit_r := fifelse(is.finite(hb13) & hb13>=0, hb13/cpi*100, NA_real_)]
dt[, cash_r    := fifelse(is.finite(hb14) & hb14>=0, hb14/cpi*100, NA_real_)]
dt[, liq_r     := fifelse(is.finite(hb13)|is.finite(hb14),
                    (fifelse(is.na(hb13),0,hb13)+fifelse(is.na(hb14),0,hb14))/cpi*100, NA_real_)]
dt[!is.na(deposit_r), deposit_rw := winz(deposit_r)]
dt[!is.na(liq_r),     liq_rw     := winz(liq_r)]
dt[, asinh_dep := asinh(deposit_rw)]
dt[, asinh_liq := asinh(liq_rw)]

## ---- self-built wage income (corrected per 08_income_build.py; already in analysis.csv) ----
dt[is.finite(wage_built_r) & wage_built_r>=0, wage_rw := winz(wage_built_r)]
dt[, asinh_wage := asinh(wage_rw)]

## ---- consumption (partial measure, "不含燃料和自产食物消费") ----
dt[, ln_atotalexpcpi := log(pmax(atotalexpcpi,0)+1)]

cat("\n=== Deposit missingness diagnostic (Table 6 sample, year<=2020) ===\n")
d2020 <- dt[year<=2020]
cat("N (year<=2020):", nrow(d2020), "\n")
cat("hb13 nonmissing:", sum(!is.na(d2020$hb13)), " missing rate:",
    round(1-mean(!is.na(d2020$hb13)),3), "\n")

## ---- M2 regressions (exactly mirroring 07_mechanisms.R) ----
m_wage <- feols(as.formula(paste0("asinh_wage ~ lncovid + ",fc_full," | tid + year")),
                dt[is.finite(asinh_wage)], cluster=~tid)
m_cons <- feols(as.formula(paste0("ln_atotalexpcpi ~ lncovid + ",fc_full," | tid + year")),
                dt, cluster=~tid)
dep <- dt[year<=2020 & is.finite(asinh_dep)]
m_dep <- feols(as.formula(paste0("asinh_dep ~ lncovid + ",fc_full," | tid + year")), dep, cluster=~tid)
liq <- dt[year<=2020 & is.finite(asinh_liq)]
m_liq <- feols(as.formula(paste0("asinh_liq ~ lncovid + ",fc_full," | tid + year")), liq, cluster=~tid)

cat("\n=== M2 Wage (asinh, self-built) ===\n"); print(coeftable(m_wage)["lncovid",c(1,2,4)])
cat("\n=== M2 Consumption (ln) ===\n"); print(coeftable(m_cons)["lncovid",c(1,2,4)])
cat("\n=== M2 Deposits (asinh, 2013-2020) ===\n"); print(coeftable(m_dep)["lncovid",c(1,2,4)])
cat("\n=== M2 Liquid savings (asinh, 2013-2020) ===\n"); print(coeftable(m_liq)["lncovid",c(1,2,4)])

save_tab(list("asinh(Wage inc)"=m_wage,"Log(Consumption)"=m_cons,"asinh(Deposits)"=m_dep,"asinh(Liquid)"=m_liq),
  "tab6_M2_precaution.md","Table 6. Mechanism 2 -- Income shock & precautionary saving",
  coef_map=c("lncovid"="Log(Covid)"),
  notes=paste0("Note: SE clustered by township. Deposits/liquid columns restricted to year<=2020 ",
  "(hb13 dropped from the questionnaire after 2020: 100% missing 2021-2023; see Q2 diagnostic). ",
  "Monetary stocks CPI-deflated (1978=100), NA kept NA (never filled 0), negatives set to NA, ",
  "winsorized at 1%/99%, transformed with asinh(). Deposit missing rate in the year<=2020 mechanism ",
  "sample = ",round(1-mean(!is.na(d2020$hb13)),3)*100,"% (Table-6 footnote figure)."))

sink(file.path(O,"key_numbers_table6.txt"))
g <- function(m,v="lncovid"){ct<-coeftable(m)[v,]; sprintf("b=%.4f se=%.4f p=%.4f N=%d",ct[1],ct[2],ct[4],nobs(m))}
cat("M2 Wage income asinh (self-built, CORRECTED per 08_income_build.py):",g(m_wage),"\n")
cat("M2 Consumption (ln)                                              :",g(m_cons),"\n")
cat("M2 Deposits asinh (2013-2020)                                    :",g(m_dep),"\n")
cat("M2 Liquid savings asinh (2013-2020)                              :",g(m_liq),"\n")
cat("Deposit missing rate (year<=2020 mechanism sample)               :",round(1-mean(!is.na(d2020$hb13)),3),"\n")
sink()
cat("\nDONE 08_mechanisms_table6.R\n")
