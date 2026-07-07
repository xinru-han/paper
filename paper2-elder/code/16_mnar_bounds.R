# =============================================================================
# 16_mnar_bounds.R — sensitivity of the B-line elder gap to proxy under-recording
# (MNAR). The single biggest threat to the within-household elder deficit is that
# an elder's meals are under-recorded by the household respondent rather than
# genuinely skipped. We bound the true gap with a pattern-mixture / Manski-style
# device: elders with few recorded meals are the suspected under-recorded group;
# re-impute their diversity between "no real deficit" (best case) and "observed"
# (worst case), and report how much under-recording it takes to null the gap.
# Outputs: table22_mnar_bounds.csv
# =============================================================================
source("/root/data/Paper/食物消费数据/paper2-elder/code/00_setup.R")
suppressPackageStartupMessages({ library(fixest); library(data.table) })

bl <- fread(file.path(DIR_DERIV, "bline_sample.csv"), colClasses = list(character = c("nhCode","pid","xzc12")))
bl[, `:=`(fgds10 = num(fgds10), elder = as.integer(elderly == 1),
          female = num(female), n_meals = num(n_meals))]
bl <- bl[!is.na(fgds10) & !is.na(female)]

gap <- function(d) {
  m <- feols(fgds10 ~ elder + female | hh_id, data = d, cluster = ~xzc12)
  ct <- coeftable(m)["elder", ]; c(est = ct["Estimate"], se = ct["Std. Error"], p = ct["Pr(>|t|)"])
}

obs <- gap(bl)

# household non-elder-adult mean FGDS (the "served like the adults" counterfactual)
adult_mean <- bl[elder == 0, .(adult_fgds = mean(fgds10, na.rm = TRUE)), by = hh_id]
bl <- merge(bl, adult_mean, by = "hh_id", all.x = TRUE)

# Pattern-mixture bounds: for elders flagged as potentially under-recorded
# (n_meals < 3), replace their observed FGDS by the household non-elder-adult mean
# (best case: the deficit is entirely a recording artifact). Sweep the flag.
res <- list(data.table(scenario = "observed (worst case: all deficit real)",
                       est = obs["est.Estimate"], se = obs["se.Std. Error"],
                       p = obs["p.Pr(>|t|)"], share_reimputed = 0))
for (thr in c(3, 2)) {           # under-recording suspected below 3 (and 2) meals
  d <- copy(bl)
  flag <- d$elder == 1 & !is.na(d$n_meals) & d$n_meals < thr & !is.na(d$adult_fgds)
  d[flag, fgds10 := adult_fgds]
  g <- gap(d)
  res[[length(res) + 1]] <- data.table(
    scenario = sprintf("best case: elders with <%d recorded meals eat like co-resident adults", thr),
    est = g["est.Estimate"], se = g["se.Std. Error"], p = g["p.Pr(>|t|)"],
    share_reimputed = mean(flag[bl$elder == 1]))
}

# Breakdown value: uniform under-recording delta added to ALL elders' FGDS needed
# to bring the gap to zero (how large a systematic proxy bias would explain it).
breakdown <- -obs["est.Estimate"]      # since gap is negative, add |delta| to elders

t22 <- rbindlist(res, fill = TRUE)
t22[, breakdown_delta_all_elders := as.numeric(breakdown)]
wtab(t22, "table22_mnar_bounds.csv")
cat("MNAR BOUNDS OK\n"); print(t22)
cat(sprintf("\nBreakdown: a uniform +%.3f FGDS-group under-recording applied to every elder would null the gap.\n",
            as.numeric(breakdown)))
