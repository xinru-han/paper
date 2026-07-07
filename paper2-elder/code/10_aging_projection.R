# =============================================================================
# 10_aging_projection.R — Post-estimation ②: aging/solo-living projection to 2035
# ACCOUNTING PROJECTION (not causal prediction).
# Two accounting variants:
#  (I) provisioning-anchored (PREFERRED): the structural shift changes household
#      provisioning diversity (A-line HDDS coefficients, identification
#      strongest); elder intake change = pooled pass-through phi1 x delta HDDS.
#  (II) naive individual-means variant: uses elder FGDS-10 reduced-form LA
#      coefficients directly. FLAGGED: solo elders' measured individual
#      diversity is inflated by recording concentration (household recall =
#      their own diet), so (II) understates the structural risk.
# Scenarios: S0 current; S1 2035 (k pp/decade out of three-gen into elder-only/
# alone, k in {4,6,8}); S2 = S1 + community provisioning compensating lambda of
# the provisioning loss (lambda in {25,50,75}%).
# Diversity metrics only (nutrient audit FAIL -> D6).
# Outputs: T17 scenario table, fig10 projection paths
# =============================================================================
source("/root/data/Paper/食物消费数据/paper2-elder/code/00_setup.R")
suppressPackageStartupMessages({ library(fixest); library(ggplot2) })

LA_LEVELS <- c("cohabit_nonelder","elder_only_multi","threegen","elder_alone","elder_child","other")

hh <- fread(file.path(DIR_DERIV, "hh_analysis.csv"), colClasses = list(character = c("nhCode","xzc12")))
hh[, `:=`(hdds12 = num(hdds12), county_year = paste(countyn, data_year),
          LA = relevel(factor(living_arrangement, levels = LA_LEVELS), ref = "cohabit_nonelder"))]
per <- fread(file.path(DIR_DERIV, "person_analysis.csv"), colClasses = list(character = c("nhCode","pid","xzc12")))
eld <- per[elderly == 1 & !is.na(num(fgds10)) & living_arrangement %in% LA_LEVELS]
eld[, `:=`(fgds10 = num(fgds10), county_year = paste(countyn, data_year),
           LA = relevel(factor(living_arrangement, levels = LA_LEVELS), ref = "cohabit_nonelder"))]
eld[is.na(main_cook), main_cook := 0]

# --- ingredients ---------------------------------------------------------------
mA <- feols(hdds12 ~ LA + ln_income + any_elder_80 + n_elderly | county_year, data = hh, cluster = ~xzc12)
mP <- feols(fgds10 ~ num(hdds12_household) + LA + female + main_cook + ln_income | county_year,
            data = eld, cluster = ~xzc12)
mR <- feols(fgds10 ~ LA + female + main_cook + ln_income | county_year, data = eld, cluster = ~xzc12)
phi1 <- coef(mP)[1]
bA <- coef(mA); bR <- coef(mR)
la_coef <- function(b, la) if (la == "cohabit_nonelder") 0 else unname(b[paste0("LA", la)])

# conditional levels (household provisioning and elder intake) by arrangement
hdds_lvl <- sapply(LA_LEVELS, function(la) mean(hh[living_arrangement == "cohabit_nonelder", hdds12], na.rm = TRUE) + la_coef(bA, la))
fgds_lvl <- sapply(LA_LEVELS, function(la) mean(eld[living_arrangement == "cohabit_nonelder", fgds10]) + la_coef(bR, la))
# elder-person distribution across arrangements
s0 <- prop.table(table(factor(eld$living_arrangement, levels = LA_LEVELS)))

shift_dist <- function(s0, k_pp_decade, horizon_yrs = 11) {
  s <- as.numeric(s0); names(s) <- names(s0)
  take <- min(k_pp_decade/100 * horizon_yrs/10, s["threegen"] - .01)
  s["threegen"] <- s["threegen"] - take
  w <- s[c("elder_only_multi","elder_alone")]; w <- w/sum(w)
  s["elder_only_multi"] <- s["elder_only_multi"] + take * w[1]
  s["elder_alone"]      <- s["elder_alone"]      + take * w[2]
  s / sum(s)
}

scen <- rbindlist(lapply(c(4, 6, 8), function(k) {
  s1 <- shift_dist(s0, k)
  # variant I: provisioning-anchored
  dHDDS <- sum((s1 - as.numeric(s0)) * hdds_lvl)       # change in mean household HDDS faced by elders
  dEld_I <- phi1 * dHDDS
  # variant II: naive individual means (flagged)
  dEld_II <- sum((s1 - as.numeric(s0)) * fgds_lvl)
  base <- rbind(
    data.table(k_pp_decade = k, scenario = "S1 2035 structure", lambda = NA_real_,
               d_hh_hdds = dHDDS, d_elder_fgds_provisioning = dEld_I, d_elder_fgds_naive = dEld_II),
    rbindlist(lapply(c(.25,.5,.75), function(lam)
      data.table(k_pp_decade = k, scenario = sprintf("S2 community provisioning lambda=%.0f%%", 100*lam),
                 lambda = lam, d_hh_hdds = dHDDS * (1-lam),
                 d_elder_fgds_provisioning = dEld_I * (1-lam), d_elder_fgds_naive = NA_real_))))
  base
}))
s0row <- data.table(k_pp_decade = NA_integer_, scenario = "S0 current", lambda = NA_real_,
                    d_hh_hdds = 0, d_elder_fgds_provisioning = 0, d_elder_fgds_naive = 0)
scen <- rbind(s0row, scen)
scen[, mean_elder_fgds10 := mean(eld$fgds10) + d_elder_fgds_provisioning]
wtab(scen, "table17_aging_projection_scenarios.csv")

# --- fig10: paths for k = 6 -----------------------------------------------------
k6 <- scen[k_pp_decade == 6 | scenario == "S0 current"]
m0 <- mean(eld$fgds10)
path <- rbindlist(lapply(seq_len(nrow(k6)), function(i)
  data.table(scenario = k6$scenario[i], year = c(2024, 2035),
             fgds10 = c(m0, k6$mean_elder_fgds10[i]))))
p10 <- ggplot(path, aes(year, fgds10, colour = scenario)) +
  geom_line(linewidth = 1) + geom_point(size = 2.5) +
  scale_x_continuous(breaks = c(2024, 2035)) +
  labs(x = NULL, y = "Mean elder FGDS-10 (48h), provisioning-anchored",
       title = "Rural elders' dietary diversity under the 2035 living-arrangement shift",
       subtitle = "Accounting projection (k = 6 pp/decade out of three-generation households);\nelder change = pass-through phi1 x provisioning (HDDS) change",
       colour = NULL) +
  theme_minimal(base_size = 12) + theme(legend.position = "bottom") +
  guides(colour = guide_legend(ncol = 2))
ggsave(file.path(DIR_FIG, "fig10_aging_projection.png"), p10, width = 9, height = 6, dpi = 200)

hl <- scen[k_pp_decade == 6 & scenario == "S1 2035 structure"]
writeLines(c("# Aging projection (T17/F10)", "",
  "Wording discipline: conditional associations + structural extrapolation; NOT a causal forecast.",
  sprintf("- Pass-through phi1 (pooled): %.3f; A-line HDDS levels by arrangement embedded.", phi1),
  sprintf("- S1 (k=6pp/decade to 2035): household provisioning HDDS falls %.3f groups on average;",
          -hl$d_hh_hdds),
  sprintf("  elder FGDS-10 falls %.4f groups (provisioning-anchored).", -hl$d_elder_fgds_provisioning),
  sprintf("- Naive individual-means variant gives %.4f — biased UP by solo-recording concentration; flagged in text.",
          hl$d_elder_fgds_naive),
  "- S2: community provisioning at lambda={25,50,75}%% mechanically recovers the same share of the loss (accounting identity), reported for policy sizing.",
  "- Sensitivity k in {4,8} in table17. D6: diversity metric only. D7 fallback documented."),
  file.path(DIR_REP, "aging_projection_summary.md"))
cat("PROJECTION OK\n"); print(scen[k_pp_decade == 6 | scenario == "S0 current",
  .(scenario, d_hh_hdds, d_elder_fgds_provisioning, mean_elder_fgds10)])
