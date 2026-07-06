source("code/00_setup.R")

data <- read_csv(
  path("data", "analysis_ready", "paper1_revised_analysis_ready_long.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character", xzc12_for_merge_final = "character")
)
data <- prepare_revised_data(data)

food_order <- c("zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo")
rhs <- c(hh_terms_main, resource_terms_revised, market_gaez_terms_revised, price_text_terms_revised, "factor(data_year)")

rows <- list()
for (cat in food_order) {
  d0 <- data[data$food_category == cat, ]
  cat_label <- d0$food_category_label[1]
  fit <- fit_lm_cluster(d0, "production_participation", rhs)
  if (!fit$ok) next
  w <- wald_test(fit$model, fit$vcov, hh_terms_main)
  coefs <- c()
  for (term in hh_terms_main) {
    s <- safe_coef_stats(fit$model, fit$vcov, term)
    names(s) <- paste0(term, c("_coef", "_se", "_t", "_p"))
    coefs <- c(coefs, s)
  }
  pvals <- sapply(hh_terms_main, function(term) safe_coef_stats(fit$model, fit$vcov, term)["p_value"])
  drivers <- hh_terms_main[which(pvals < 0.10)]
  rows[[length(rows) + 1]] <- data.frame(
    food_category = cat,
    food_category_label = cat_label,
    outcome = "production_participation",
    conceptual_outcome = "self_provisioning_participation",
    n = nrow(fit$data),
    n_clusters = length(unique(fit$data$xzc12_for_merge_final)),
    outcome_mean = mean(fit$data$production_participation, na.rm = TRUE),
    r_squared = summary(fit$model)$r.squared,
    hhcomp_wald_chisq = w$stat,
    hhcomp_wald_df = w$df,
    hhcomp_wald_p = w$p,
    t(coefs),
    main_coefficient_drivers = ifelse(length(drivers) == 0, "none_p_lt_0.10", paste(drivers, collapse = ";")),
    stringsAsFactors = FALSE
  )
}

table4 <- do.call(rbind, rows)
table4$nsi <- table4$hhcomp_wald_chisq / mean(table4$hhcomp_wald_chisq, na.rm = TRUE)
table4$signal_label <- mapply(signal_label, table4$hhcomp_wald_p, table4$nsi)
table4$food_category <- factor(table4$food_category, levels = food_order)
table4 <- table4[order(table4$food_category), ]
table4$food_category <- as.character(table4$food_category)

write_csv(table4, path("outputs", "tables", "table4_category_specific_nsi.csv"))
write_simple_json(table4, path("outputs", "model_summaries", "model4_category_specific_nsi.json"), key = "categories")

fig_data <- table4[order(table4$nsi, decreasing = TRUE), ]
png(path("outputs", "figures", "figure2_nsi_by_category.png"), width = 1800, height = 1100, res = 180)
par(mar = c(8, 5, 4, 2))
cols <- ifelse(fig_data$signal_label == "Strong", "#2F6B9A", ifelse(fig_data$signal_label == "Moderate", "#69995D", "#9AA7B1"))
barplot(
  fig_data$nsi,
  names.arg = fig_data$food_category_label,
  las = 2,
  col = cols,
  border = NA,
  ylab = "NSI = category Wald / mean Wald",
  main = "Non-Separability Index by Food Category",
  ylim = c(0, max(fig_data$nsi, na.rm = TRUE) * 1.18)
)
abline(h = 1, lty = 2, col = "#666666")
legend(
  "topright",
  legend = c("Strong", "Moderate", "Weak"),
  fill = c("#2F6B9A", "#69995D", "#9AA7B1"),
  border = NA,
  bty = "n"
)
dev.off()

message("Category-specific NSI completed.")