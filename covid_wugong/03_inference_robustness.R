#!/usr/bin/env Rscript
# ============================================================================
# 03_inference_robustness.R
# P0-2 (modification plan Sec 3.2 / 3.5a): wild cluster bootstrap inference at
# the COUNTY level (xid, 12 clusters -- township clustering at 41 clusters is
# "barely adequate but optimistic"; county-level CRVE with only 12 clusters is
# invalid, per the plan). `fwildclusterboot` is confirmed unavailable for this
# R/CRAN snapshot, so we implement the Cameron-Gelbach-Miller (2008)
# Wild-Cluster-Restricted (WCR) Rademacher bootstrap directly:
#   1. Fit the model with x (var of interest) DROPPED  -> restricted fit, residuals e_r
#   2. For b=1..B: draw Rademacher weights v_g in {-1,+1} per cluster g,
#      construct y*_b = fitted(restricted) + e_r * v_g[cluster]
#      refit the FULL model on y*_b, keep the t-stat on x
#   3. Bootstrap p = mean(|t*_b| >= |t_observed|)   (symmetric two-sided WCR test)
# B = 999 Rademacher draws per model (5 models x ~1min each; kept moderate for
# runtime -- CGM2008 recommend B>=399 is already adequate for a stable p-value
# at conventional significance levels).
# ============================================================================
source("/opt/data/research/Paper/新冠对务工的影响/revision2/scripts/00_common.R")
dt <- load_analysis()
dt0 <- dt[year<2023]

set.seed(20260704)
B <- 999

wcr_bootstrap <- function(data, yvar, xvar, other_rhs, fe, cluster_var, B=999) {
  full_fml <- as.formula(paste0(yvar," ~ ",xvar," + ",other_rhs," | ",fe))
  res_fml  <- as.formula(paste0(yvar," ~ ",other_rhs," | ",fe))

  m_full <- feols(full_fml, data, cluster=as.formula(paste0("~",cluster_var)))
  t_obs  <- coeftable(m_full)[xvar,3]
  b_obs  <- coeftable(m_full)[xvar,1]
  se_obs <- coeftable(m_full)[xvar,2]

  m_res <- feols(res_fml, data)
  removed <- m_res$obs_selection$obsRemoved
  used_idx <- if (is.null(removed)) seq_len(nrow(data)) else setdiff(seq_len(nrow(data)), -removed)
  d2 <- data[used_idx]
  d2[, yhat_r  := as.numeric(m_res$fitted.values)]
  d2[, resid_r := as.numeric(m_res$residuals)]

  clusters <- unique(d2[[cluster_var]])
  G <- length(clusters)
  t_star <- numeric(B)
  for (b in 1:B) {
    w <- sample(c(-1,1), G, replace=TRUE)
    names(w) <- as.character(clusters)
    v <- w[as.character(d2[[cluster_var]])]
    d2[, ystar := yhat_r + resid_r * v]
    m_b <- tryCatch(
      feols(as.formula(paste0("ystar ~ ",xvar," + ",other_rhs," | ",fe)),
            d2, cluster=as.formula(paste0("~",cluster_var))),
      error=function(e) NULL)
    t_star[b] <- if (is.null(m_b) || !(xvar %in% rownames(coeftable(m_b)))) NA_real_
                 else coeftable(m_b)[xvar,3]
  }
  t_star <- t_star[!is.na(t_star)]
  p_wcr <- mean(abs(t_star) >= abs(t_obs))
  list(b=b_obs, se=se_obs, t=t_obs, p_asym=coeftable(m_full)[xvar,4],
       p_wcr=p_wcr, G=G, B_eff=length(t_star), N=nobs(m_full))
}

cat("Running WCR wild cluster bootstrap (county-level, 12 clusters), B =",B,"...\n")

t0 <- Sys.time()
r_base <- wcr_bootstrap(dt0, "ln_a_workday2", "lncovid", fc_full, "tid + year", "xid", B=B)
cat("Baseline done (",round(as.numeric(Sys.time()-t0),1),"s ): b=",r_base$b," p(county,WCR)=",r_base$p_wcr,"\n")

t0 <- Sys.time()
r_pyr <- wcr_bootstrap(dt0, "ln_a_workday2", "lncovid", fc_full, "tid + pid^year", "xid", B=B)
cat("Prov x Year FE done (",round(as.numeric(Sys.time()-t0),1),"s ): b=",r_pyr$b," p(county,WCR)=",r_pyr$p_wcr,"\n")

t0 <- Sys.time()
r_trend <- wcr_bootstrap(dt0, "ln_a_workday2", "lncovid", fc_full, "tid + year + xid[year]", "xid", B=B)
cat("County trends done (",round(as.numeric(Sys.time()-t0),1),"s ): b=",r_trend$b," p(county,WCR)=",r_trend$p_wcr,"\n")

## Event-study key years as standalone interacted regressors (WCR at county level)
dt_es <- copy(dt0)
for (yy in c(2020,2021,2022)) {
  dt_es[[paste0("expo_",yy)]] <- ifelse(dt_es$year==yy, dt_es$ln_exposure2022, 0)
}
yearf_terms <- "i(year, ref=2019)"
es_helper <- function(target_year){
  other <- paste0(fc_2023," + ", yearf_terms)
  wcr_bootstrap(dt_es, "ln_a_workday2", paste0("expo_",target_year), other, "tid + year", "xid", B=B)
}
t0 <- Sys.time()
r_es2020 <- tryCatch(es_helper(2020), error=function(e){cat("ES2020 WCR failed:",conditionMessage(e),"\n"); NULL})
cat("ES2020 done (",round(as.numeric(Sys.time()-t0),1),"s )\n")
t0 <- Sys.time()
r_es2021 <- tryCatch(es_helper(2021), error=function(e){cat("ES2021 WCR failed:",conditionMessage(e),"\n"); NULL})
cat("ES2021 done (",round(as.numeric(Sys.time()-t0),1),"s )\n")

cat("\n=== SUMMARY ===\n")
for(r in list(r_base,r_pyr,r_trend,r_es2020,r_es2021)) if(!is.null(r)) print(r[c("b","se","p_asym","p_wcr","G","N")])

## ---- write table ----
fmt   <- function(r) sprintf("%.4f", r$b)
fmtse <- function(r) sprintf("(%.4f)", r$se)
fmtp  <- function(p) sprintf("%.4f", p)

rows <- list(
  c("Baseline", fmt(r_base), fmtse(r_base), fmtp(r_base$p_asym), fmtp(r_base$p_wcr)),
  c("Province x Year FE", fmt(r_pyr), fmtse(r_pyr), fmtp(r_pyr$p_asym), fmtp(r_pyr$p_wcr)),
  c("County-specific trends", fmt(r_trend), fmtse(r_trend), fmtp(r_trend$p_asym), fmtp(r_trend$p_wcr))
)
if(!is.null(r_es2020)) rows[[length(rows)+1]] <- c("Event study: 2020 x exposure", fmt(r_es2020), fmtse(r_es2020), fmtp(r_es2020$p_asym), fmtp(r_es2020$p_wcr))
if(!is.null(r_es2021)) rows[[length(rows)+1]] <- c("Event study: 2021 x exposure", fmt(r_es2021), fmtse(r_es2021), fmtp(r_es2021$p_asym), fmtp(r_es2021$p_wcr))

tab_lines <- sapply(rows, function(r) sprintf("| %s | %s | %s | %s | **%s** |", r[1],r[2],r[3],r[4],r[5]))

L <- c(
"### Table R1b (inference robustness). Wild cluster bootstrap p-values at the county level (12 clusters)",
"",
"> `fwildclusterboot` unavailable for this R/CRAN snapshot; implemented as a Cameron-Gelbach-Miller (2008) WCR Rademacher bootstrap, B=999, restricted-residual resampling, refit per draw. Two-sided p = P(|t*| >= |t_obs|).",
"",
"| Model | Coef. | Township-clustered SE (asymptotic) | Asymptotic p (township, 41 clusters) | **WCR bootstrap p (county, 12 clusters)** |",
"|---|---|---|---|---|",
tab_lines,
"",
sprintf("N: baseline=%d, prov x year=%d, county trends=%d%s.",
        r_base$N, r_pyr$N, r_trend$N,
        if(!is.null(r_es2020)) sprintf(", event-study=%d", r_es2020$N) else ""),
"",
"### Pre-trend joint Wald test (2013-2018 event-study coefficients = 0), reference",
"",
"Wald F = 1.132, df1 = 6, df2 = 40, p = 0.362 (township-clustered; see tab_2023_persistence.md for the full event-study table and 01_baseline_and_dynamics_2023.R for the underlying model).",
"",
"Note: WCR = wild cluster restricted bootstrap (Cameron, Gelbach & Miller 2008), Rademacher weights, B=999. Applied at the COUNTY level (xid, 12 clusters) because county-level CRVE with only 12 clusters is invalid (per modification plan Sec 3.2); the main text continues to report township-clustered SEs (41 clusters, adequate under conventional rules of thumb) alongside these bootstrap p-values as the more conservative/valid check.",
""
)
writeLines(L, file.path(O,"tab_inference_robustness.md"))
cat("\nwrote tab_inference_robustness.md\n")

sink(file.path(O,"key_numbers_inference.txt"))
for(nm in c("r_base","r_pyr","r_trend","r_es2020","r_es2021")) {
  r <- get(nm)
  if(!is.null(r)) cat(nm,": b=",r$b," se=",r$se," p_asym=",r$p_asym," p_WCR(county)=",r$p_wcr," N=",r$N,"\n")
}
sink()
cat("DONE 03_inference_robustness.R\n")
