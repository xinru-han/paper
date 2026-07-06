#!/usr/bin/env Rscript
# ============================================================================
# 00_common.R -- common data loader + helpers, sourced by all revision2 scripts
#
# Key fix vs. revision/06_analysis.R (modification plan Sec 3.1):
#   The original script did `dt <- dt[year<2023]` BEFORE constructing the
#   lead variables via shift(type="lead"), which silently turned every
#   2022-exposure -> 2023-outcome lead into NA. This discarded the single
#   most decisive piece of new evidence for the editor's "long-term" concern
#   (post-reopening persistence). Here we load the FULL 2013-2023 panel,
#   construct leads/event-study interactions first, and only then subset
#   per-model to whatever year range that specific analysis needs.
#
#   2023 village-level controls: `lncovid`/`covid` (current-year confirmed
#   cases) are 100% missing in 2023 (reporting stopped after Dec-2022
#   reopening) -> 2023 can only be an OUTCOME year, never an exposure year;
#   this is fine because `ln_exposure2022` (cumulative exposure through 2022,
#   time-invariant) IS available in 2023 (see output/audit_note.md).
#   `road_density2` is 100% missing in 2023 and is dropped from any
#   2023-inclusive spec. `pilot/lnhouseholds/lnv_ainccpi/far_station/
#   far_asale/far_market` are partially missing in 2023 but are close to
#   time-invariant within village (median within-village CV 0.007-0.23 over
#   2013-2022) -> filled via last-observation-carried-forward (LOCF) within
#   village, applied ONLY to 2023 rows (pre-2023 rows are left exactly as in
#   the original pipeline, so the year<2023 estimation sample/coefficients
#   are unaffected and remain comparable to revision/06_analysis.R).
# ============================================================================
suppressMessages({library(data.table); library(fixest); library(ggplot2)})
setFixest_notes(FALSE)

BASE <- "/opt/data/research/Paper/新冠对务工的影响"
D0   <- file.path(BASE,"revision2","data")
O    <- file.path(BASE,"revision2","output")
FIG  <- file.path(BASE,"revision2","figures")
dir.create(O,   showWarnings=FALSE, recursive=TRUE)
dir.create(FIG, showWarnings=FALSE, recursive=TRUE)

load_analysis <- function() {
  dt <- fread(file.path(D0,"analysis.csv"))
  dt[, lnfar_station := log(far_station+1)]
  dt[, lnfar_asale   := log(far_asale+1)]
  dt[, lnfar_market  := log(far_market+1)]

  ## ---- LOCF fill of near-time-invariant village controls, 2023 ROWS ONLY ----
  ## pre-2023 rows are NEVER modified, even if NA, so the year<2023 estimation
  ## sample is byte-for-byte identical to revision/06_analysis.R.
  locf_vars <- c("pilot","lnhouseholds","lnv_ainccpi","lnfar_station","lnfar_asale","lnfar_market")
  dt[, controls_locf2023 := FALSE]
  setorder(dt, vid, year)
  for (v in locf_vars) {
    filled <- dt[, .(vid, year, orig = get(v))][, filled := nafill(orig, type="locf"), by=vid]$filled
    is_2023_na <- dt$year==2023 & is.na(dt[[v]])
    fill_ok <- is_2023_na & !is.na(filled)
    dt[fill_ok, (v) := filled[fill_ok]]
    dt[fill_ok, controls_locf2023 := TRUE]
  }
  setorder(dt, nid, year)

  ## ---- lead outcomes for persistence checks: constructed BEFORE any year filter ----
  dt[, lead1 := shift(ln_a_workday2, 1, type="lead"), by=nid]
  dt[, lead2 := shift(ln_a_workday2, 2, type="lead"), by=nid]

  ## ---- event-study year factor (ref = 2019), covers 2013-2023 ----
  dt[, yearf := relevel(factor(year), ref="2019")]

  dt
}

## Controls: two variants.
##  ctrl_full  -- mirrors revision/06_analysis.R exactly (includes road_density2),
##                use ONLY for year<2023 replications so baseline numbers match.
##  ctrl_2023  -- drops road_density2 (100% missing in 2023), use for any spec
##                that includes 2023 observations.
ctrl_full <- c("gender","age","health","edu","labor_ratio",
               "pilot","lnhouseholds","lnv_ainccpi","lnfar_station","lnfar_asale","lnfar_market",
               "road_density2","lnlandprice_sum")
ctrl_2023 <- c("gender","age","health","edu","labor_ratio",
               "pilot","lnhouseholds","lnv_ainccpi","lnfar_station","lnfar_asale","lnfar_market",
               "lnlandprice_sum")
fc_full <- paste(ctrl_full, collapse=" + ")
fc_2023 <- paste(ctrl_2023, collapse=" + ")

star <- function(p) ifelse(is.na(p),"",ifelse(p<.01,"***",ifelse(p<.05,"**",ifelse(p<.1,"*",""))))

save_tab <- function(models, file, title, coef_map=NULL, extra=NULL, notes=NULL) {
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
  N<-sapply(models,function(m) format(nobs(m),big.mark=","))
  R2<-sapply(models,function(m) tryCatch(sprintf("%.3f",fitstat(m,"wr2")$wr2),error=function(e)sprintf("%.3f",r2(m,"r2"))))
  L<-c(L,paste0("| N | ",paste(N,collapse=" | ")," |"),
         paste0("| Within R2 | ",paste(R2,collapse=" | ")," |"))
  if(!is.null(extra)) L<-c(L,extra)
  if(is.null(notes)) notes <- "Note: SE clustered by township in parentheses. * p<0.10, ** p<0.05, *** p<0.01."
  L<-c(L,"",notes,"")
  writeLines(L, file.path(O,file)); cat("wrote",file,"\n")
}
