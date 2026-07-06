#!/usr/bin/env Rscript
# Revision analyses PART B — MECHANISMS (theory-grounded, text/nightlight dropped)
#   M1 Extensive vs intensive margin (PRIMARY): participation(LPM)/days|worker/per-member
#   M2 Precautionary saving : consumption + real bank-deposit / liquid-savings STOCK
#   M3 Reallocation to local/farm : operated land + home(farm)-income share
#
# DATA NOTES (see also descriptives.md, mech_data_diagnostics.txt):
#   - Sample = 2013-2022 UNBALANCED rotating panel (households rotate in/out;
#     532/3206 hh appear all 10 yrs). Estimation N differs by outcome coverage.
#   - Saving-RATE (1-exp/inc) is NOT used: (a) conceptually a flow ratio, not the
#     precautionary stock response; (b) `totalincome` is ~0/empty before 2021 and
#     `homeincome` only 2019+, so income totals are unreliable pre-2021. We instead
#     use the directly-surveyed deposit STOCK hb13 (2013-2020), which needs no income.
#   - `total_exp` label = "总支出(不含燃料和自产食物消费)" -> a PARTIAL consumption
#     measure; consumption result is caveated accordingly.
#
# ZERO & OUTLIER HANDLING (explicit):
#   - monetary stocks CPI-deflated (base 1978=100); NA kept as NA (never fill 0);
#     negatives -> NA; winsorized at 1%/99% within the available sample;
#     transformed with asinh() so legitimate zeros are retained (not log-dropped).
#   - operated land already top-coded (~163 mu); winsorized 1/99 then asinh.
#   - workday: extensive margin uses a 0/1 participation dummy (no log);
#     intensive margin uses log(days) among migrant-working households (no zeros);
#     per-member uses ln(1+days) so non-participants (zeros) stay in the sample.
suppressMessages({library(data.table); library(fixest)})
setFixest_notes(FALSE)
D <- "/opt/data/research/Paper/新冠对务工的影响/revision/data"
O <- "/opt/data/research/Paper/新冠对务工的影响/revision/output"
dt <- fread(file.path(D,"analysis.csv"))

## controls mirror the baseline
dt[, lnfar_station := log(far_station+1)]
dt[, lnfar_asale   := log(far_asale+1)]
dt[, lnfar_market  := log(far_market+1)]
ctrl <- c("gender","age","health","edu","labor_ratio","pilot","lnhouseholds",
          "lnv_ainccpi","lnfar_station","lnfar_asale","lnfar_market",
          "road_density2","lnlandprice_sum")
fc <- paste(ctrl, collapse=" + ")
dt <- dt[year<2023]

star <- function(p) ifelse(p<.01,"***",ifelse(p<.05,"**",ifelse(p<.1,"*","")))
winz <- function(x,p=.01){ q<-quantile(x,c(p,1-p),na.rm=TRUE)
  x[!is.na(x) & x<q[1]]<-q[1]; x[!is.na(x) & x>q[2]]<-q[2]; x }
save_tab <- function(models, file, title, coef_map, extra=NULL) {
  rows <- names(coef_map)
  hdr <- paste0("| Variable | ", paste(names(models),collapse=" | ")," |")
  sep <- paste0("|",paste(rep("---",length(models)+1),collapse="|"),"|")
  L <- c(paste0("### ",title),"",hdr,sep)
  for(r in rows){ b<-c(); s<-c()
    for(m in models){ ct<-coeftable(m)
      if(r %in% rownames(ct)){est<-ct[r,1];se<-ct[r,2];p<-ct[r,4]
        b<-c(b,sprintf("%.4f%s",est,star(p))); s<-c(s,sprintf("(%.4f)",se))
      } else {b<-c(b,""); s<-c(s,"")}}
    L<-c(L,paste0("| ",coef_map[r]," | ",paste(b,collapse=" | ")," |"),
           paste0("|  | ",paste(s,collapse=" | ")," |"))}
  N<-sapply(models,function(m) format(nobs(m),big.mark=","))
  R2<-sapply(models,function(m) tryCatch(sprintf("%.3f",fitstat(m,"wr2")$wr2),error=function(e)sprintf("%.3f",r2(m,"r2"))))
  L<-c(L,paste0("| N | ",paste(N,collapse=" | ")," |"),
         paste0("| Within R2 | ",paste(R2,collapse=" | ")," |"))
  if(!is.null(extra)) L<-c(L,extra)
  L<-c(L,"","Note: SE clustered by township in parentheses. * p<0.10, ** p<0.05, *** p<0.01.","")
  writeLines(L, file.path(O,file)); cat("wrote",file,"\n")
}

########################################################################
## VARIABLE CONSTRUCTION with zero / outlier handling
########################################################################
## monetary stocks: deflate, NA-safe, winsorize, asinh
dt[, deposit_r := fifelse(is.finite(hb13) & hb13>=0, hb13/cpi*100, NA_real_)]
dt[, cash_r    := fifelse(is.finite(hb14) & hb14>=0, hb14/cpi*100, NA_real_)]
dt[, liq_r     := fifelse(is.finite(hb13)|is.finite(hb14),
                    (fifelse(is.na(hb13),0,hb13)+fifelse(is.na(hb14),0,hb14))/cpi*100, NA_real_)]
dt[!is.na(deposit_r), deposit_rw := winz(deposit_r)]
dt[!is.na(liq_r),     liq_rw     := winz(liq_r)]
dt[, asinh_dep := asinh(deposit_rw)]
dt[, asinh_liq := asinh(liq_rw)]
## operated land: winsorize + asinh (retain landless zeros)
dt[is.finite(operateland) & operateland>=0, land_w := winz(operateland)]
dt[, asinh_land := asinh(land_w)]
## workday margins
dt[is.finite(a_workday2), work_any := as.integer(a_workday2>0)]      # extensive
dt[is.finite(a_workday3) & a_workday3>0, ln_wd3 := log(a_workday3)]  # intensive | worker (no zeros)
# ln_a_workday1 already = log(1+days per member); includes non-participant zeros
## home(farm/operating)-income share, 2019+ only, bounded [0,1]
dt[, tot_wm := workincome + homeincome]
dt[is.finite(tot_wm) & tot_wm>0, home_share := homeincome/tot_wm]
## self-built WAGE income (工资性收入, every year; see 08_income_build.py).
## NB: total income/expenditure cannot be self-aggregated for 2013-2020 (farm-income
## and living-expenditure component tables are absent from this dta); wage income is
## the only cross-year self-buildable income concept, and the most relevant here.
dt[is.finite(wage_built_r) & wage_built_r>=0, wage_rw := winz(wage_built_r)]
dt[, asinh_wage := asinh(wage_rw)]

########################################################################
## DESCRIPTIVE STATISTICS  (variable provenance + summary) -> descriptives.md
########################################################################
descvars <- list(
 c("a_workday1","家庭成员平均务工天数(问卷:总务工天数/家庭成员数)"),
 c("a_workday2","家庭劳动力平均务工天数【主结局】(/劳动力数)"),
 c("a_workday3","家庭务工人员平均务工天数(/实际务工者)"),
 c("work_any","是否有人外出务工 0/1 = 1[a_workday2>0]"),
 c("covid","当年县级确诊数(外部匹配)"),
 c("lncovid","ln(确诊)"),
 c("hb13","年末家庭银行存款 名义元(问卷 hb13)"),
 c("deposit_rw","存款 实际元(1978=100) winsor1/99"),
 c("liq_rw","存款+现金 实际元(hb13+hb14) winsor"),
 c("atotalexpcpi","人均总支出 实际(total_exp/成员/cpi; 不含燃料+自产食物)"),
 c("operateland","实际经营耕地 亩(问卷)"),
 c("wage_rw","自建工资性收入 实际元(分行业打工 hg 2013-20/新项 2021-22, winsor)"),
 c("home_share","家庭经营收入占比 homeincome/(work+home)"),
 c("age","年龄"),c("edu","受教育年限"),c("labor_ratio","劳动力占比"),
 c("far_station","距最近车站码头 km"))
L <- c("### 描述统计（主样本 year<2023；变量与来源）","",
       "| 变量 | 含义/来源 | N | 均值 | 标准差 | 最小 | 中位 | 最大 |",
       "|---|---|---|---|---|---|---|---|")
for(v in descvars){ x<-suppressWarnings(as.numeric(dt[[v[1]]])); x<-x[is.finite(x)]
  f<-function(z) if(abs(z)>=100) formatC(z,format="d",big.mark=",") else sprintf("%.3f",z)
  L<-c(L,sprintf("| %s | %s | %s | %s | %s | %s | %s | %s |",
     v[1],v[2],formatC(length(x),format="d",big.mark=","),
     f(mean(x)),f(sd(x)),f(min(x)),f(median(x)),f(max(x))))}
L<-c(L,"","> 面板为农经所轮换抽样，非平衡：3206户中仅532户全程10年；各变量N因逐年缺失/轮换而不同。",
     "> 储蓄率(1-支出/收入)未采用：概念上为流量比非预防性存量反应；且totalincome在2021前≈0、homeincome仅2019+、total_exp口径残缺。")
writeLines(L, file.path(O,"descriptives.md")); cat("wrote descriptives.md\n")

## zero/outlier diagnostics
diag <- function(name,x){ x<-x[is.finite(x)]
  cat(sprintf("%-16s N=%6d zeros=%5d(%4.1f%%) p1=%.1f p99=%.1f\n",
      name,length(x),sum(x==0),100*mean(x==0),quantile(x,.01),quantile(x,.99)))}
sink(file.path(O,"mech_data_diagnostics.txt"))
cat("Zero / outlier handling diagnostics (estimation sample, year<2023)\n\n")
cat("[M1] participation dummy & workday levels:\n")
cat(sprintf("work_any: N=%d, participation rate=%.3f\n",sum(is.finite(dt$work_any)),mean(dt$work_any,na.rm=TRUE)))
diag("a_workday3(>0)",dt$a_workday3[dt$a_workday3>0])
cat("\n[M2] real bank deposits (2013-2020), winsorized then asinh:\n")
diag("deposit_r",dt[year<=2020]$deposit_r); diag("deposit_rw(1/99)",dt[year<=2020]$deposit_rw)
diag("liq_rw",dt[year<=2020]$liq_rw)
cat("\n[M3] operated land (winsorized) & home-income share:\n")
diag("land_w",dt$land_w); diag("home_share",dt$home_share)
sink(); cat("wrote mech_data_diagnostics.txt\n")

## reference baseline elasticity (for interpreting margins)
m_base <- feols(as.formula(paste0("ln_a_workday2 ~ lncovid + ",fc," | tid + year")), dt, cluster=~tid)

########################################################################
## MECHANISM 1 (PRIMARY) — Extensive vs intensive margin
##   is the persistent drop fewer members going out (participation)
##   or fewer days per active worker (hours / demand side)?
########################################################################
m_ext <- feols(as.formula(paste0("work_any ~ lncovid + ",fc," | tid + year")), dt, cluster=~tid) # LPM extensive
m_int <- feols(as.formula(paste0("ln_wd3 ~ lncovid + ",fc," | tid + year")), dt[a_workday3>0], cluster=~tid) # intensive|worker
m_pm  <- feols(as.formula(paste0("ln_a_workday1 ~ lncovid + ",fc," | tid + year")), dt, cluster=~tid) # per-member (ext+int)
save_tab(list("Participation (LPM)"=m_ext,"Days|worker (intensive)"=m_int,"Per-member (ext+int)"=m_pm),
         "tab_mech1_margin.md","Table R3. Mechanism 1 (primary) — Extensive vs intensive margin",
         coef_map=c("lncovid"="Log(Covid)"))
cat("\n=== M1 MARGIN (primary) ===\n")
print(coeftable(m_ext)["lncovid",c(1,2,4)]); print(coeftable(m_int)["lncovid",c(1,2,4)])
print(coeftable(m_pm)["lncovid",c(1,2,4)])

########################################################################
## MECHANISM 2 — Precautionary saving (income-risk / buffer-stock)
##   precaution -> deposits UP.  Uses deposit STOCK (2013-2020, 2020=shock yr)
########################################################################
m_wage <- feols(as.formula(paste0("asinh_wage ~ lncovid + ",fc," | tid + year")), dt[is.finite(asinh_wage)], cluster=~tid)
m_cons <- feols(as.formula(paste0("ln_atotalexpcpi ~ lncovid + ",fc," | tid + year")), dt, cluster=~tid)
dep <- dt[year<=2020 & is.finite(asinh_dep)]
m_dep <- feols(as.formula(paste0("asinh_dep ~ lncovid + ",fc," | tid + year")), dep, cluster=~tid)
liq <- dt[year<=2020 & is.finite(asinh_liq)]
m_liq <- feols(as.formula(paste0("asinh_liq ~ lncovid + ",fc," | tid + year")), liq, cluster=~tid)
save_tab(list("asinh(Wage inc)"=m_wage,"Log(Consumption)"=m_cons,"asinh(Deposits)"=m_dep,"asinh(Liquid)"=m_liq),
         "tab_mech2_precaution.md","Table R4. Mechanism 2 — Income shock & precautionary saving",
         coef_map=c("lncovid"="Log(Covid)"),
         extra="| Sample | 2013-2022 | 2013-2022 | 2013-2020 | 2013-2020 |")
cat("\n=== M2 INCOME SHOCK + PRECAUTION ===\n")
print(coeftable(m_wage)["lncovid",c(1,2,4)]); print(coeftable(m_cons)["lncovid",c(1,2,4)])
print(coeftable(m_dep)["lncovid",c(1,2,4)]); print(coeftable(m_liq)["lncovid",c(1,2,4)])

########################################################################
## MECHANISM 3 — Reallocation to local / farm work
########################################################################
m_land  <- feols(as.formula(paste0("asinh_land ~ lncovid + ",fc," | tid + year")), dt, cluster=~tid)
m_share <- feols(as.formula(paste0("home_share ~ lncovid + ",fc," | tid + year")),
                 dt[year>=2019 & is.finite(home_share)], cluster=~tid)
save_tab(list("asinh(Operated land)"=m_land,"Home-income share"=m_share),
         "tab_mech3_realloc.md","Table R5. Mechanism 3 — Reallocation to local/farm",
         coef_map=c("lncovid"="Log(Covid)"),
         extra="| Sample | 2013-2022 | 2019-2022 |")
cat("\n=== M3 REALLOCATION ===\n")
print(coeftable(m_land)["lncovid",c(1,2,4)]); print(coeftable(m_share)["lncovid",c(1,2,4)])

########################################################################
## headline mechanism numbers
########################################################################
sink(file.path(O,"key_numbers_mech.txt"))
g <- function(m,v="lncovid"){ct<-coeftable(m)[v,]; sprintf("b=%.4f se=%.4f p=%.4f N=%d",ct[1],ct[2],ct[4],nobs(m))}
cat("Baseline (ln workday2)          :",g(m_base),"\n\n")
cat("M1 Participation LPM (ext.)     :",g(m_ext),"\n")
cat("M1 Days|worker (intensive)      :",g(m_int),"\n")
cat("M1 Per-member ln(1+d)           :",g(m_pm),"\n\n")
cat("M2 Wage income asinh (self-built):",g(m_wage),"\n")
cat("M2 Consumption (ln)             :",g(m_cons),"\n")
cat("M2 Deposits asinh (2013-2020)   :",g(m_dep),"\n")
cat("M2 Liquid sav asinh (13-20)     :",g(m_liq),"\n\n")
cat("M3 asinh(Operated land)         :",g(m_land),"\n")
cat("M3 Home-income share (19-22)    :",g(m_share),"\n")
sink()
cat("\nDONE (mechanisms 1-3, reordered: margin primary).\n")
