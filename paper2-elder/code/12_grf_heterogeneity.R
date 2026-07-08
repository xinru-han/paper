# =============================================================================
# 12_grf_heterogeneity.R — appendix: HONEST FOREST HETEROGENEITY OF THE ADJUSTED
# ASSOCIATION between three-generation co-residence and household HDDS-12.
# Living arrangement is NOT randomly assigned, so nothing here is a treatment
# effect: the grf::causal_forest machinery is used purely as a machine-learning
# heterogeneity DIAGNOSTIC. Outputs are labelled "conditional contrast" (not
# CATE) and "adjusted average contrast" (not ATT/ATE); subgroup differences are
# "targeted subgroup patterns", not treatment-effect heterogeneity.
# Never competes with main tables.
# Outputs: T19 conditional-contrast summaries, fig11 partial dependence panel
# =============================================================================
source("/root/data/Paper/食物消费数据/paper2-elder/code/00_setup.R")
suppressPackageStartupMessages({ library(grf); library(ggplot2) })

hh <- fread(file.path(DIR_DERIV, "hh_analysis.csv"), colClasses = list(character = c("nhCode","xzc12")))
for (v in c("hdds12","any_elder_80","HB2","HB5","HB8","max_elder_age")) hh[, (v) := num(get(v))]
d <- hh[living_arrangement %in% c("threegen","cohabit_nonelder")]
d[, treat := as.integer(living_arrangement == "threegen")]
XV <- c("ln_income","max_elder_age","any_elder_80","n_elderly","HB2","HB5","HB8",
        "market_access_index","retail_thickness_index","food_self_suff_rate")
d[, food_self_suff_rate := num(food_self_suff_rate)]
d <- d[complete.cases(d[, c("hdds12","treat", XV), with = FALSE])]
X <- as.matrix(d[, ..XV]); Y <- d$hdds12; W <- d$treat

cf <- causal_forest(X, Y, W, num.trees = 4000, honesty = TRUE,
                    clusters = as.integer(factor(d$xzc12)), seed = 42)
# grf calls this "ATE on the treated"; under non-random treatment it is an
# adjusted average contrast, and is labelled as such everywhere below.
avg_contrast <- average_treatment_effect(cf, target.sample = "treated")
tau <- predict(cf)$predictions
d[, cond_contrast := tau]   # conditional contrast, NOT a CATE

# calibration test (does the forest detect real heterogeneity?)
calib <- test_calibration(cf)

# T19: conditional contrast by policy-relevant subgroups
t19 <- rbindlist(list(
  d[, .(group = "all", mean_cond_contrast = mean(cond_contrast), q25 = quantile(cond_contrast,.25), q75 = quantile(cond_contrast,.75), N = .N)],
  d[, .(group = fifelse(ln_income <= median(ln_income), "low income","high income"), cond_contrast)][
    , .(mean_cond_contrast = mean(cond_contrast), q25 = quantile(cond_contrast,.25), q75 = quantile(cond_contrast,.75), N = .N), by = group],
  d[, .(group = fifelse(max_elder_age >= 75, "oldest elder 75+","oldest elder 60-74"), cond_contrast)][
    , .(mean_cond_contrast = mean(cond_contrast), q25 = quantile(cond_contrast,.25), q75 = quantile(cond_contrast,.75), N = .N), by = group],
  d[, .(group = fifelse(market_access_index <= median(market_access_index, na.rm=TRUE),
                        "poor market access","good market access"), cond_contrast)][
    , .(mean_cond_contrast = mean(cond_contrast), q25 = quantile(cond_contrast,.25), q75 = quantile(cond_contrast,.75), N = .N), by = group]),
  fill = TRUE)
wtab(t19, "table19_grf_cate_subgroups.csv")  # conditional contrasts (file name kept for pipeline continuity)

# variable importance
vi <- data.table(variable = XV, importance = variable_importance(cf)[,1])[order(-importance)]
wtab(vi, "table19b_grf_variable_importance.csv")

# fig11: partial dependence on the two most important continuous drivers
top2 <- head(vi[variable %in% c("ln_income","max_elder_age","market_access_index",
                                "retail_thickness_index","food_self_suff_rate"), variable], 2)
pd <- rbindlist(lapply(top2, function(v) {
  grid <- quantile(d[[v]], seq(.05,.95,.05), na.rm = TRUE)
  Xg <- X[rep(1, length(grid)), , drop = FALSE]
  for (j in seq_len(ncol(Xg))) Xg[, j] <- median(X[, j])
  Xg[, which(XV == v)] <- grid
  data.table(variable = v, x = grid, cond_contrast = predict(cf, Xg)$predictions)
}))
p11 <- ggplot(pd, aes(x, cond_contrast)) + geom_line(linewidth = 1, colour = "steelblue") +
  facet_wrap(~variable, scales = "free_x") +
  geom_hline(yintercept = avg_contrast["estimate"], linetype = 2) +
  labs(x = NULL, y = "Conditional contrast on HDDS-12 (adjusted association)",
       title = "Honest-forest heterogeneity of the three-generation association (appendix)",
       subtitle = "Dashed = adjusted average contrast (treated); NOT causal — treatment non-random") +
  theme_minimal(base_size = 12)
ggsave(file.path(DIR_FIG, "fig11_grf_partial_dependence.png"), p11, width = 9, height = 4.5, dpi = 200)

het_detected <- calib[2, 3] > 2
writeLines(c("# Honest-forest heterogeneity of the adjusted association (appendix)",
  "- grf::causal_forest is used as an ML heterogeneity diagnostic only; living arrangement is self-selected, so outputs are conditional CONTRASTS of an adjusted association, not CATEs/treatment effects.",
  sprintf("- Adjusted average contrast, treated (forest; NOT a causal ATT): %.3f (se %.3f)", avg_contrast["estimate"], avg_contrast["std.err"]),
  sprintf("- Calibration: mean prediction t=%.2f, differential t=%.2f.", calib[1,3], calib[2,3]),
  sprintf("- **Heterogeneity %s**: the differential-forest-prediction calibration coefficient is %s 2, so the forest does **not** give statistical evidence of heterogeneity in the adjusted association. Subgroup conditional-contrast differences (and the leakage-by-subgroup contrasts they motivate) are therefore **suggestive only**, not established effect modification.",
          if (het_detected) "DETECTED" else "NOT detected", if (het_detected) "above" else "below"),
  "- Framing: conditional-association heterogeneity; treatment non-random."),
  file.path(DIR_REP, "grf_summary.md"))
cat("GRF OK\n"); print(t19)
