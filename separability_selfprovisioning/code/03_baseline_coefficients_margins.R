source("code/00_setup.R")

raw_coef <- read_csv(path("outputs", "tables", "table2_common_sample_baseline_coefficients_raw.csv"))

stable_rows <- list()
for (outcome in unique(raw_coef$outcome)) {
  for (term in hh_terms_main) {
    idx <- raw_coef$outcome == outcome & raw_coef$term == term
    d <- raw_coef[idx, ]
    signs <- unique(d$direction[!is.na(d$direction) & d$direction != "NA" & d$direction != "zero"])
    stable <- length(signs) == 1
    for (i in seq_len(nrow(d))) {
      stable_rows[[length(stable_rows) + 1]] <- data.frame(
        outcome = d$outcome[i],
        conceptual_outcome = ifelse(d$outcome[i] == "production_participation", "self_provisioning_participation", d$outcome[i]),
        spec = d$spec[i],
        term = d$term[i],
        estimate = d$estimate[i],
        std_error_cluster = d$std_error_cluster[i],
        t_stat = d$t_stat[i],
        p_value = d$p_value[i],
        direction = d$direction[i],
        marginal_effect_interpretation = ifelse(
          d$outcome[i] == "production_participation",
          "LPM coefficient: percentage-point change in self-provisioning participation for a one-unit change in the covariate.",
          "OLS coefficient for transformed self-production amount."
        ),
        sign_stable_across_M0_M3 = stable,
        stable_direction = ifelse(stable, signs[1], "not_stable"),
        n = d$n[i],
        n_clusters = d$n_clusters[i],
        r_squared = d$r_squared[i],
        stringsAsFactors = FALSE
      )
    }
  }
}

table3 <- do.call(rbind, stable_rows)
write_csv(table3, path("outputs", "tables", "table3_baseline_coefficients_margins.csv"))
write_simple_json(table3, path("outputs", "model_summaries", "model3_baseline_coefficients_margins.json"), key = "coefficients")

fig_data <- table3[table3$outcome == "production_participation" & table3$spec == "M3", ]
fig_data$lower <- fig_data$estimate - 1.96 * fig_data$std_error_cluster
fig_data$upper <- fig_data$estimate + 1.96 * fig_data$std_error_cluster

png(path("outputs", "figures", "figure3_household_composition_coefficients.png"), width = 1800, height = 1100, res = 180)
par(mar = c(6, 7, 4, 2))
y <- seq_len(nrow(fig_data))
plot(
  fig_data$estimate, y,
  xlim = range(c(fig_data$lower, fig_data$upper, 0), na.rm = TRUE),
  ylim = c(0.5, nrow(fig_data) + 0.5),
  yaxt = "n",
  ylab = "",
  xlab = "Coefficient with 95% CI",
  pch = 19,
  col = "#2F6B9A",
  main = "M3 Household-Composition Coefficients"
)
segments(fig_data$lower, y, fig_data$upper, y, col = "#2F6B9A", lwd = 2)
abline(v = 0, lty = 2, col = "#777777")
axis(2, at = y, labels = fig_data$term, las = 1)
dev.off()

message("Baseline coefficient interpretation completed.")