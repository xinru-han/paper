# =============================================================================
# 12_grf_heterogeneity.R — appendix: honest causal forest heterogeneity of the
# three-generation "treatment" (NON-random -> framed as heterogeneity of the
# conditional association, feeding the S2 targeting hypothesis and leakage
# heterogeneity cross-validation). Never competes with main tables.
# Outputs: T19 CATE summaries, fig11 partial dependence panel
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
ate <- average_treatment_effect(cf, target.sample = "treated")
tau <- predict(cf)$predictions
d[, cate := tau]

# calibration test (does the forest detect real heterogeneity?)
calib <- test_calibration(cf)

# T19: CATE by policy-relevant subgroups
t19 <- rbindlist(list(
  d[, .(group = "all", mean_cate = mean(cate), q25 = quantile(cate,.25), q75 = quantile(cate,.75), N = .N)],
  d[, .(group = fifelse(ln_income <= median(ln_income), "low income","high income"), cate)][
    , .(mean_cate = mean(cate), q25 = quantile(cate,.25), q75 = quantile(cate,.75), N = .N), by = group],
  d[, .(group = fifelse(max_elder_age >= 75, "oldest elder 75+","oldest elder 60-74"), cate)][
    , .(mean_cate = mean(cate), q25 = quantile(cate,.25), q75 = quantile(cate,.75), N = .N), by = group],
  d[, .(group = fifelse(market_access_index <= median(market_access_index, na.rm=TRUE),
                        "poor market access","good market access"), cate)][
    , .(mean_cate = mean(cate), q25 = quantile(cate,.25), q75 = quantile(cate,.75), N = .N), by = group]),
  fill = TRUE)
wtab(t19, "table19_grf_cate_subgroups.csv")

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
  data.table(variable = v, x = grid, cate = predict(cf, Xg)$predictions)
}))
p11 <- ggplot(pd, aes(x, cate)) + geom_line(linewidth = 1, colour = "steelblue") +
  facet_wrap(~variable, scales = "free_x") +
  geom_hline(yintercept = ate["estimate"], linetype = 2) +
  labs(x = NULL, y = "CATE on HDDS-12",
       title = "Causal-forest heterogeneity of the three-generation association (appendix)",
       subtitle = "Dashed = ATT; associations, treatment non-random") +
  theme_minimal(base_size = 12)
ggsave(file.path(DIR_FIG, "fig11_grf_partial_dependence.png"), p11, width = 9, height = 4.5, dpi = 200)

writeLines(c("# GRF heterogeneity (appendix)",
  sprintf("- ATT (forest): %.3f (se %.3f)", ate["estimate"], ate["std.err"]),
  sprintf("- Calibration: mean prediction t=%.2f, differential t=%.2f (differential>2 => real heterogeneity)",
          calib[1,3], calib[2,3]),
  "- Framing: conditional-association heterogeneity; feeds S2 targeting and leakage heterogeneity."),
  file.path(DIR_REP, "grf_summary.md"))
cat("GRF OK\n"); print(t19)
