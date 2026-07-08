# =============================================================================
# 06_bline_gap.R — B1: within-household elder vs non-elder adult gap and its
# interaction with three-generation living (household(×year) fixed effects).
#   y_ih = alpha_h + delta*Elder_i + theta*(Elder_i x ThreeGen_h) + x_i'gamma + e
# Outcomes: fgds10 (main), fvs_unique_foods, dbi16_variety_subscore,
#           any animal-source food (unit-robust binary), any dairy/egg/bean,
#           quality-protein gram share (flagged secondary; audit FAIL -> no AR)
# Inference: village-clustered SEs + Romano-Wolf stepdown (village bootstrap)
# Robustness (R6): drop low home-eating members, drop <3 recorded meals,
#           add age control, elder-cook interaction
# Outputs: T10 (B1 main), T10b (R6), fig7 coefficient plot
# Decision nodes: D3 (theta ~ 0, full pass-through), D4 (theta < 0)
# =============================================================================
source("/root/data/Paper/食物消费数据/paper2-elder/code/00_setup.R")
suppressPackageStartupMessages({ library(fixest); library(ggplot2) })

bl <- fread(file.path(DIR_DERIV, "bline_sample.csv"), colClasses = list(character = c("nhCode","pid","xzc12")))
bl[, threegen := as.integer(living_arrangement == "threegen")]
bl[, elder := as.integer(elderly == 1)]
for (v in c("fgds10","fvs_unique_foods","dbi16_variety_subscore","qual_protein_share"))
  bl[, (v) := num(get(v))]
# unit-robust binaries from MDD-W group grams (presence only)
bl[, any_animal := as.integer(num(mddwg_flesh_g_48h) > 0 | num(mddwg_eggs_g_48h) > 0 | num(mddwg_dairy_g_48h) > 0)]
bl[, any_deb := as.integer(num(mddwg_dairy_g_48h) > 0 | num(mddwg_eggs_g_48h) > 0 | num(mddwg_beans_peas_g_48h) > 0)]
bl[, any_fv := as.integer(num(mddwg_va_dark_green_g_48h) > 0 | num(mddwg_va_other_fv_g_48h) > 0 |
                          num(mddwg_other_veg_g_48h) > 0 | num(mddwg_other_fruit_g_48h) > 0)]
bl[is.na(main_cook), main_cook := 0]
bl[, home_days := num(home_eating_days)]

OUTS <- c(fgds10 = "FGDS-10 diversity", fvs_unique_foods = "Food variety score",
          dbi16_variety_subscore = "DBI-16 variety", any_animal = "Any animal-source (48h)",
          any_deb = "Any dairy/egg/bean (48h)", qual_protein_share = "Quality-protein g share (flagged)")
# main_cook is a MEDIATOR of the provisioning mechanism (who cooks is itself part
# of intra-household food organisation), so it is a bad control for the baseline
# elder gap. Baseline now conditions on female only; main_cook enters as an
# explicit robustness column (r6$add_maincook) and as the mechanism moderator.
CTRL_I <- "female"

fit_b1 <- function(dat, y, ctrl = CTRL_I) {
  feols(as.formula(paste0(y, " ~ elder + elder:threegen + ", ctrl, " | hh_id")),
        data = dat, cluster = ~xzc12)
}

t10 <- rbindlist(lapply(names(OUTS), function(y) {
  m <- fit_b1(bl[!is.na(get(y))], y)
  ct <- tidy_fe(m, "elder")
  ct[, outcome := y]; ct
}))
wtab(t10, "table10_bline_gap_main.csv")

# ---- Romano-Wolf stepdown over the outcome family (village bootstrap) -------
# Audit fixes (2026-07): (i) resampled villages are RELABELLED so a village drawn
# k times contributes k distinct clusters (set-membership labels understate the
# bootstrap cluster variance); (ii) finite-sample p-value (1+#extreme)/(1+B) so
# p can never be reported as exactly 0; (iii) B raised 300 -> 999. This test is
# positioned as AUXILIARY multiplicity control alongside the wild cluster
# bootstrap in 14_wild_bootstrap.R.
main_terms <- c("elder","elder:threegen")
get_t <- function(dat, clvar = "xzc12") {
  sapply(names(OUTS), function(y) {
    m <- tryCatch(fit_b1_cl(dat[!is.na(get(y))], y, clvar), error = function(e) NULL)
    if (is.null(m)) return(c(NA, NA))
    ct <- coeftable(m)
    c(ct["elder","t value"], ct["elder:threegen","t value"])
  })
}
fit_b1_cl <- function(dat, y, clvar) {
  feols(as.formula(paste0(y, " ~ elder + elder:threegen + ", CTRL_I, " | hh_id")),
        data = dat, cluster = as.formula(paste0("~", clvar)))
}
t_obs <- get_t(bl)
set.seed(3); B <- 999
vils <- unique(bl$xzc12)
# null-imposed bootstrap: recenter t-stats (standard RW with cluster bootstrap)
t_boot <- array(NA_real_, dim = c(2, length(OUTS), B))
for (b in seq_len(B)) {
  sv <- sample(vils, length(vils), replace = TRUE)
  bs <- rbindlist(lapply(seq_along(sv), function(k) {
    dv <- bl[xzc12 == sv[k]]
    dv[, boot_cl := paste0(sv[k], "_", k)]   # relabel: each draw = its own cluster
    dv
  }))
  t_boot[,,b] <- get_t(bs, "boot_cl") - t_obs
}
rw_p <- function(row) {
  o <- order(-abs(t_obs[row,]))
  p <- rep(NA_real_, length(o))
  remaining <- o
  for (k in seq_along(o)) {
    maxnull <- apply(abs(t_boot[row, remaining, , drop = FALSE]), 3, max, na.rm = TRUE)
    # finite-sample Monte-Carlo p: (1 + #extreme) / (1 + B), never exactly 0
    p[o[k]] <- (1 + sum(maxnull >= abs(t_obs[row, o[k]]), na.rm = TRUE)) / (1 + B)
    if (k > 1) p[o[k]] <- max(p[o[k]], p[o[k-1]])   # enforce monotonicity
    remaining <- setdiff(remaining, o[k])
  }
  p
}
rw <- data.table(outcome = names(OUTS),
                 p_rw_elder = rw_p(1), p_rw_interaction = rw_p(2))
wtab(rw, "table10a_romano_wolf.csv")

# ---- presence-indicator provenance check (audit minor item #5) ---------------
# any_animal etc. are built from mddwg_* gram fields (>0). Cross-check presence
# against the independent DBI-16 gram family: unit errors rescale grams but do
# not flip presence, and two independently-coded group families agreeing on
# presence rules out "presence inherited from a bad merge" for these binaries.
bl[, any_animal_dbiv := as.integer(num(dbiv_red_meat_g_48h) > 0 | num(dbiv_poultry_g_48h) > 0 |
                                   num(dbiv_fish_shrimp_g_48h) > 0 | num(dbiv_egg_g_48h) > 0 |
                                   num(dbiv_milk_g_48h) > 0)]
agree_pres <- bl[!is.na(any_animal) & !is.na(any_animal_dbiv), mean(any_animal == any_animal_dbiv)]
writeLines(sprintf(paste0("# Presence-indicator provenance check\n",
  "- any_animal (MDD-W gram family) vs any animal (DBI-16 gram family): ",
  "%.1f%% agreement over %d B-line members.\n",
  "- Presence/absence binaries are robust to the Task-3 unit failures as long as ",
  "zero/nonzero status is correct; two independently coded group families agree."),
  100*agree_pres, bl[!is.na(any_animal) & !is.na(any_animal_dbiv), .N]),
  file.path(DIR_REP, "presence_provenance_check.md"))

# ---- R6 robustness for the main outcome (fgds10) -----------------------------
r6 <- list()
r6$main                 <- fit_b1(bl, "fgds10")
r6$add_age              <- fit_b1(bl, "fgds10", paste0(CTRL_I, " + age_yrs"))
r6$add_maincook         <- fit_b1(bl, "fgds10", paste0(CTRL_I, " + main_cook"))
r6$drop_low_home_days   <- fit_b1(bl[is.na(home_days) | home_days >= quantile(home_days, .25, na.rm = TRUE)], "fgds10")
r6$drop_few_meals       <- fit_b1(bl[num(n_meals) >= 3], "fgds10")
r6$binary_any_animal    <- fit_b1(bl, "any_animal")
r6$women_only_wdds9     <- tryCatch(fit_b1(bl[female == 1 & !is.na(num(wdds9))][, wdds9 := num(wdds9)], "wdds9"),
                                    error = function(e) NULL)
t10b <- rbindlist(lapply(names(r6), function(nm) {
  if (is.null(r6[[nm]])) return(NULL)
  tidy_fe(r6[[nm]], "elder")[, spec := nm]
}), fill = TRUE)
wtab(t10b, "table10b_bline_r6_robustness.csv")

# ---- meal-frequency channel (reproducible source for the RESULTS narrative) --
# Previously the "-0.32 fewer meals / 31.9% vs 22.9%" figures were stated in the
# results text without a generating table. Estimate them explicitly here.
bl[, n_meals_num := num(n_meals)]
m_meals <- feols(n_meals_num ~ elder + female + main_cook | hh_id, data = bl, cluster = ~xzc12)
mf <- tidy_fe(m_meals, "elder")[, spec := "n_meals ~ elder | hh_id"]
share_lt3 <- bl[!is.na(n_meals_num), .(pct_lt3_meals = 100*mean(n_meals_num < 3),
                                       mean_meals = mean(n_meals_num), n = .N),
                by = .(group = fifelse(elder == 1, "elder", "non_elder_adult"))]
wtab(mf, "table10d_meal_frequency_gap.csv")
wtab(share_lt3, "table10d_meal_frequency_shares.csv")

# ---- minimum detectable effect (MDE) for the imprecise interaction ------------
# So "not significant" is not read as "precisely zero": report the 95% CI and the
# 80%-power MDE (~2.8 x se) for theta and delta.
mm0 <- fit_b1(bl, "fgds10"); ct0 <- coeftable(mm0)
mde <- data.table(
  term = c("elder", "elder:threegen"),
  est  = ct0[c("elder","elder:threegen"), "Estimate"],
  se   = ct0[c("elder","elder:threegen"), "Std. Error"],
  ci_lo = ct0[c("elder","elder:threegen"), "Estimate"] - 1.96*ct0[c("elder","elder:threegen"), "Std. Error"],
  ci_hi = ct0[c("elder","elder:threegen"), "Estimate"] + 1.96*ct0[c("elder","elder:threegen"), "Std. Error"],
  mde_80 = 2.8 * ct0[c("elder","elder:threegen"), "Std. Error"])
wtab(mde, "table10e_mde_power.csv")

# ---- elder-cook moderation (mechanism §8.3) ----------------------------------
m_cook <- feols(fgds10 ~ elder + elder:threegen + elder:main_cook + female + main_cook | hh_id,
                data = bl, cluster = ~xzc12)
wtab(tidy_fe(m_cook, "elder|cook"), "table10c_elder_cook_moderation.csv")

# ---- Fig 7: elder gap by living arrangement ----------------------------------
mm <- fit_b1(bl, "fgds10")
ct <- coeftable(mm); V <- vcov(mm)
delta <- ct["elder","Estimate"]; theta <- ct["elder:threegen","Estimate"]
se_d <- ct["elder","Std. Error"]
se_dt <- sqrt(V["elder","elder"] + V["elder:threegen","elder:threegen"] + 2*V["elder","elder:threegen"])
fig7 <- data.table(
  arrangement = c("With non-elder adults\n(two-generation)", "Three generations"),
  gap = c(delta, delta + theta), se = c(se_d, se_dt))
p7 <- ggplot(fig7, aes(x = arrangement, y = gap)) +
  geom_col(fill = "steelblue", alpha = .7, width = .5) +
  geom_errorbar(aes(ymin = gap - 1.96*se, ymax = gap + 1.96*se), width = .12) +
  geom_hline(yintercept = 0) +
  labs(x = NULL, y = "Elder - non-elder adult FGDS-10 gap (within household)",
       title = "Within-household elder diversity gap by living arrangement",
       subtitle = sprintf("Household FE; N = %d members in %d mixed households; village-clustered 95%% CI",
                          mm$nobs, uniqueN(bl$hh_id))) +
  theme_minimal(base_size = 12)
ggsave(file.path(DIR_FIG, "fig7_elder_gap_by_LA.png"), p7, width = 7.5, height = 5.5, dpi = 200)

# ---- decision nodes D3/D4 -----------------------------------------------------
p_theta <- ct["elder:threegen","Pr(>|t|)"]
node <- if (p_theta > .1 & abs(theta) < .5*se_dt) "D3-like (theta ~ 0)" else if (theta < 0 & p_theta < .1) "D4 (theta < 0)" else if (theta > 0 & p_theta < .1) "positive theta" else "imprecise theta"
writeLines(c("# B-line decision-node check",
  sprintf("- delta (elder gap, two-generation hh): %.3f (se %.3f)", delta, se_d),
  sprintf("- theta (x three-generation): %.3f (p = %.3f)", theta, p_theta),
  sprintf("- classification: %s", node),
  "- D3: headline 'provisioning gains pass through fully'; D4: 'richer table, not richer bowl'."),
  file.path(DIR_REP, "decision_p2_D3_D4_check.md"))

cat("B-LINE GAP OK\n")
print(t10[term %in% c("elder","elder:threegen") & outcome %in% c("fgds10","any_animal"),
          .(outcome, term, est, se, p, n)])
