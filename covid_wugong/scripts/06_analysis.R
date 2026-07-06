#!/usr/bin/env Rscript
# Revision analyses PART A: baseline, identification, long-term dynamics.
# Mechanisms (1 precautionary saving, 2 extensive/intensive margin,
# 3 reallocation) are in 07_mechanisms.R. Text/nightlight mechanisms DROPPED.
suppressMessages({library(data.table); library(fixest)})
setFixest_notes(FALSE)
D  <- "/opt/data/research/Paper/新冠对务工的影响/revision/data"
O  <- "/opt/data/research/Paper/新冠对务工的影响/revision/output"
dt <- fread(file.path(D,"analysis.csv"))

## ---- construct log distance controls to mirror the paper ----
dt[, lnfar_station := log(far_station+1)]
dt[, lnfar_asale   := log(far_asale+1)]
dt[, lnfar_market  := log(far_market+1)]

ctrl <- c("gender","age","health","edu","labor_ratio",
          "pilot","lnhouseholds","lnv_ainccpi","lnfar_station","lnfar_asale","lnfar_market",
          "road_density2","lnlandprice_sum")
fc <- paste(ctrl, collapse=" + ")
dt <- dt[year<2023]
setorder(dt, nid, year)

star <- function(p) ifelse(p<.01,"***",ifelse(p<.05,"**",ifelse(p<.1,"*","")))
save_tab <- function(models, file, title, coef_map=NULL) {
  rn <- unique(unlist(lapply(models,function(m) rownames(coeftable(m)))))
  if(is.null(coef_map)){nm<-rn; names(nm)<-rn; coef_map<-nm}
  rows <- names(coef_map)
  hdr <- paste0("| Variable | ", paste(names(models),collapse=" | ")," |")
  sep <- paste0("|",paste(rep("---",length(models)+1),collapse="|"),"|")
  L <- c(paste0("### ",title),"",hdr,sep)
  for(r in rows){
    b<-c(); s<-c()
    for(m in models){ ct<-coeftable(m)
      if(r %in% rownames(ct)){ est<-ct[r,1]; se<-ct[r,2]; p<-ct[r,4]
        b<-c(b,sprintf("%.4f%s",est,star(p))); s<-c(s,sprintf("(%.4f)",se))
      } else {b<-c(b,""); s<-c(s,"")}
    }
    L<-c(L,paste0("| ",coef_map[r]," | ",paste(b,collapse=" | ")," |"),
           paste0("|  | ",paste(s,collapse=" | ")," |"))
  }
  N<-sapply(models,function(m) format(nobs(m),big.mark=","));
  R2<-sapply(models,function(m) tryCatch(sprintf("%.3f",fitstat(m,"wr2")$wr2),error=function(e)sprintf("%.3f",r2(m,"r2"))))
  L<-c(L,paste0("| N | ",paste(N,collapse=" | ")," |"),
         paste0("| Within R2 | ",paste(R2,collapse=" | ")," |"),
         "","Note: SE clustered by township in parentheses. * p<0.10, ** p<0.05, *** p<0.01.","")
  writeLines(L, file.path(O,file)); cat("wrote",file,"\n")
}

########################################################################
## 1. BASELINE (reproduce)
########################################################################
f_base <- as.formula(paste0("ln_a_workday2 ~ lncovid + ",fc," | tid + year"))
m_base <- feols(f_base, dt, cluster=~tid)
cat("\n=== BASELINE ===\n"); print(coeftable(m_base)["lncovid",])

########################################################################
## 2. IDENTIFICATION
########################################################################
## 2a. Event study / parallel trends: exposure(2022 cum) x year, ref 2019
dt[, yearf := relevel(factor(year), ref="2019")]
m_es <- feols(ln_a_workday2 ~ i(year, ln_exposure2022, ref=2019) +
              .[ctrl] | tid + year, dt, cluster=~tid)
cat("\n=== EVENT STUDY (exposure x year, ref 2019) ===\n")
es <- coeftable(m_es); print(es[grep("year::",rownames(es)),c(1,2,4)])

## 2b. province-by-year FE
m_pyr <- feols(as.formula(paste0("ln_a_workday2 ~ lncovid + ",fc," | tid + pid^year")),
               dt, cluster=~tid)
## 2c. county-specific linear trends
m_trend <- feols(as.formula(paste0("ln_a_workday2 ~ lncovid + ",fc," | tid + year + xid[year]")),
                 dt, cluster=~tid)
## 2d. IV: distance-to-Wuhan x post instruments lncovid
m_iv <- feols(as.formula(paste0("ln_a_workday2 ~ ",fc," | tid + year | lncovid ~ iv_dist_post")),
              dt, cluster=~tid)
cat("\n=== IV (dist-Wuhan x post) ===\n"); print(coeftable(m_iv)["fit_lncovid",])
cat("First-stage F:\n"); print(fitstat(m_iv,"ivf1")$ivf1$stat)

save_tab(list("Baseline"=m_base,"Prov×Year FE"=m_pyr,"County trends"=m_trend,"IV: dist-Wuhan"=m_iv),
         "tab_identification.md","Table R1. Identification robustness",
         coef_map=c("lncovid"="Log(Covid)","fit_lncovid"="Log(Covid) [IV]"))

########################################################################
## 3. LONG-TERM DYNAMICS (leads = persistence)
########################################################################
dt[, lead1 := shift(ln_a_workday2, 1, type="lead"), by=nid]
dt[, lead2 := shift(ln_a_workday2, 2, type="lead"), by=nid]
m_l0 <- feols(as.formula(paste0("ln_a_workday2 ~ lncovid + ",fc," | tid + year")), dt, cluster=~tid)
m_l1 <- feols(as.formula(paste0("lead1 ~ lncovid + ",fc," | tid + year")), dt, cluster=~tid)
m_l2 <- feols(as.formula(paste0("lead2 ~ lncovid + ",fc," | tid + year")), dt, cluster=~tid)
save_tab(list("t (contemp.)"=m_l0,"t+1"=m_l1,"t+2"=m_l2),
         "tab_dynamics.md","Table R2. Dynamic (lead) effects — persistence",
         coef_map=c("lncovid"="Log(Covid)"))
cat("\n=== DYNAMICS ===\n")
for(m in list(m_l0,m_l1,m_l2)) print(coeftable(m)["lncovid",c(1,2,4)])

########################################################################
## save headline identification/dynamics numbers
########################################################################
sink(file.path(O,"key_numbers.txt"))
cat("Baseline lncovid:\n"); print(coeftable(m_base)["lncovid",])
cat("\nIV lncovid:\n"); print(coeftable(m_iv)["fit_lncovid",])
cat("First-stage F:",fitstat(m_iv,"ivf1")$ivf1$stat,"\n")
sink()
cat("\nDONE (baseline + identification + dynamics). Mechanisms -> 07_mechanisms.R\n")
