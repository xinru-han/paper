# =============================================================================
# 18_bline_identification.R — C: separate "intra-household allocation against
# elders" from "age-related physiological/appetite differences" in the B-line gap.
# The household-FE elder gap is consistent with BOTH stories. Two probes:
#  (1) Generation-ladder placebo: within the same households, estimate the FGDS
#      gap of BOTH children and elders relative to prime-age adults. If the gap is
#      a pure age-need gradient, children (also atypical need) should differ too;
#      an elder-specific deficit shows up as elder >> child in magnitude.
#  (2) Health-stratified elder gap: split elders by self-reported health/chronic
#      disease. A deficit concentrated in unhealthy elders points to physiology;
#      a deficit that persists among healthy elders points to allocation.
# (DRI need-standardisation is NOT used: nutrients are sealed by the Task-3 audit
#  FAIL, and FGDS is a diversity metric without a DRI reference.)
# Outputs: table24_generation_ladder.csv, table25_elder_health_strata.csv
# =============================================================================
source("/root/data/Paper/食物消费数据/paper2-elder/code/00_setup.R")
suppressPackageStartupMessages({ library(fixest); library(data.table) })

per <- fread(file.path(DIR_DERIV, "person_analysis.csv"), colClasses = list(character = c("nhCode","pid","xzc12")))
per[, `:=`(fgds10 = num(fgds10), age_yrs = num(age_yrs), female = num(female),
           elder = as.integer(elderly == 1), kid = as.integer(child == 1),
           nonelder_adult = as.integer(nonelder_adult == 1))]
per <- per[!is.na(fgds10)]
per[, hh_id := paste(nhCode, data_year)]

# ---- (1) generation ladder: child & elder vs prime-age adult, household FE -----
# reference category = non-elder adult (18-59). gen = {child, adult(ref), elder}
per[, gen := fifelse(elder == 1, "elder", fifelse(kid == 1, "child", "adult"))]
per[, gen := relevel(factor(gen), ref = "adult")]
# keep households with within-household variation in generation
hh_mix <- per[, .(ng = uniqueN(gen)), by = hh_id][ng >= 2, hh_id]
pl <- per[hh_id %in% hh_mix]
m_ladder <- feols(fgds10 ~ gen + female | hh_id, data = pl, cluster = ~xzc12)
t24 <- tidy_fe(m_ladder, "^gen")[, spec := "generation ladder (ref = prime-age adult), household FE"]
wtab(t24, "table24_generation_ladder.csv")

# subset that specifically contains BOTH a child and a non-elder adult (clean
# placebo: child-vs-adult gap where no elder-allocation story applies)
hh_ck <- per[, .(has_c = any(kid == 1), has_a = any(nonelder_adult == 1)), by = hh_id][has_c & has_a, hh_id]
pc <- per[hh_id %in% hh_ck & gen %in% c("adult","child")]
pc[, gen := droplevels(pc$gen)]
if (pc[, uniqueN(gen)] == 2 && nrow(pc) > 50) {
  m_child <- feols(fgds10 ~ gen + female | hh_id, data = pc, cluster = ~xzc12)
  wtab(tidy_fe(m_child, "^gen")[, spec := "placebo: child vs prime-age adult (households with both)"],
       "table24b_child_placebo.csv")
}

# ---- (2) elder gap stratified by elder health ---------------------------------
# Audit fix (2026-07): the earlier split used median(health) over the WHOLE
# B-line sample. Elders' modal self-rated health is 1 (the best code), so the
# cutpoint was 1 and virtually every household landed in the "less healthy"
# stratum — table25 had a single row and could not be cited. Two non-degenerate
# household-level splits on the ELDER's health are used instead:
#   (a) chronic disease: any co-resident elder lists >=1 chronic condition
#       (disease_raw JSON array non-empty);
#   (b) self-rated health: any co-resident elder rates health worse than the
#       best code (health_code >= 2; 1 = best in this survey's coding).
bl <- fread(file.path(DIR_DERIV, "bline_sample.csv"), colClasses = list(character = c("nhCode","pid","xzc12")))
bl[, `:=`(fgds10 = num(fgds10), elder = as.integer(elderly == 1), female = num(female),
          health = num(health_code), hh_id = paste(nhCode, data_year))]
bl[, has_disease := as.integer(grepl("[0-9]", disease_raw))]
bl <- bl[!is.na(fgds10) & !is.na(female)]
elderh <- bl[elder == 1, .(
  elder_disease   = as.integer(any(has_disease == 1, na.rm = TRUE)),
  elder_srh_worse = as.integer(any(!is.na(health) & health >= 2))), by = hh_id]
bl <- merge(bl, elderh, by = "hh_id", all.x = TRUE)
strat_fit <- function(flagvar, val, lab) {
  d <- bl[get(flagvar) == val]
  if (nrow(d) < 80 || d[, uniqueN(elder)] < 2) return(NULL)
  m <- feols(fgds10 ~ elder + female | hh_id, data = d, cluster = ~xzc12)
  ct <- coeftable(m)["elder", ]
  data.table(stratum = lab, est = ct["Estimate"], se = ct["Std. Error"],
             p = ct["Pr(>|t|)"], n = nrow(d), n_households = uniqueN(d$hh_id))
}
strata <- rbindlist(list(
  strat_fit("elder_disease",   1, "elder reports chronic disease"),
  strat_fit("elder_disease",   0, "elder reports no chronic disease"),
  strat_fit("elder_srh_worse", 1, "elder self-rated health worse than best"),
  strat_fit("elder_srh_worse", 0, "elder self-rated health = best code")), fill = TRUE)
wtab(strata, "table25_elder_health_strata.csv")

cat("B-LINE IDENTIFICATION OK\n")
print(t24[, .(term, est, se, p)])
if (exists("strata")) print(strata)
