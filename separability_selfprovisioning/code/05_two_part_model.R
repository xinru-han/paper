source("code/00_setup.R")

data <- read_csv(
  path("data", "analysis_ready", "paper1_revised_analysis_ready_long.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character", xzc12_for_merge_final = "character")
)
data <- prepare_revised_data(data)

rhs <- baseline_rhs("M3")
parts <- list(
  entry_all_observations = list(
    part = "Part 1",
    sample_definition = "all observations",
    outcome = "production_participation",
    data = data
  ),
  conditional_intensity_positive_entry = list(
    part = "Part 2",
    sample_definition = "production_participation == 1",
    outcome = "log_selfprod_amount",
    data = data[data$production_participation == 1, ]
  )
)

rows <- list()
for (nm in names(parts)) {
  p <- parts[[nm]]
  fit <- fit_lm_cluster(p$data, p$outcome, rhs)
  if (!fit$ok) next
  w <- wald_test(fit$model, fit$vcov, hh_terms_main)
  coefs <- c()
  for (term in hh_terms_main) {
    s <- safe_coef_stats(fit$model, fit$vcov, term)
    names(s) <- paste0(term, c("_coef", "_se", "_t", "_p"))
    coefs <- c(coefs, s)
  }
  rows[[length(rows) + 1]] <- data.frame(
    model_part = p$part,
    model_name = nm,
    sample_definition = p$sample_definition,
    outcome = p$outcome,
    conceptual_outcome = ifelse(p$outcome == "production_participation", "self_provisioning_participation", p$outcome),
    n = nrow(fit$data),
    n_clusters = length(unique(fit$data$xzc12_for_merge_final)),
    outcome_mean = mean(fit$data[[p$outcome]], na.rm = TRUE),
    r_squared = summary(fit$model)$r.squared,
    hhcomp_wald_chisq = w$stat,
    hhcomp_wald_df = w$df,
    hhcomp_wald_p = w$p,
    t(coefs),
    interpretation = "",
    stringsAsFactors = FALSE
  )
}

table5 <- do.call(rbind, rows)
if (nrow(table5) == 2) {
  part1_sig <- table5$hhcomp_wald_p[table5$model_part == "Part 1"] < 0.05
  part2_weak <- table5$hhcomp_wald_p[table5$model_part == "Part 2"] >= 0.05
  interp <- if (part1_sig && part2_weak) {
    "Non-separability appears mainly on the entry margin rather than the conditional intensity margin."
  } else if (part1_sig && !part2_weak) {
    "Household composition predicts both entry and conditional self-production intensity."
  } else {
    "Two-part evidence is weak or mixed."
  }
  table5$interpretation <- interp
}

write_csv(table5, path("outputs", "tables", "table5_two_part_model.csv"))
write_simple_json(table5, path("outputs", "model_summaries", "model5_two_part_model.json"), key = "two_part_models")

message("Two-part model completed.")