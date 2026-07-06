source("code/00_setup.R")

data <- read_csv(
  path("data", "analysis_ready", "paper1_revised_analysis_ready_long.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character", xzc12_for_merge_final = "character")
)
data <- prepare_revised_data(data)

outcomes <- c("production_participation", "log_selfprod_amount", "ihs_selfprod_amount")
frictions <- list(
  survey_market_friction = "market_friction_survey",
  poi_market_friction = "poi_market_friction_lag1",
  combined_market_friction = "combined_market_friction"
)

rows <- list()
for (fspec in names(frictions)) {
  fvar <- frictions[[fspec]]
  extra_market <- if (fvar == "market_friction_survey") "poi_market_friction_lag1" else if (fvar == "poi_market_friction_lag1") "market_friction_survey" else character(0)
  rhs <- c(
    paste0("(", paste(hh_terms_main, collapse = " + "), ") * ", fvar),
    resource_terms_revised, extra_market,
    price_text_terms_revised,
    "gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km",
    "factor(provn_std)", category_year_terms_revised
  )
  for (outcome in outcomes) {
    fit <- fit_lm_cluster(data, outcome, rhs)
    if (!fit$ok) next
    interaction_terms <- vapply(hh_terms_main, function(term) find_interaction_name(names(coef(fit$model)), term, fvar), character(1))
    w <- wald_test(fit$model, fit$vcov, interaction_terms)
    rows[[length(rows) + 1]] <- data.frame(
      friction_spec = fspec,
      friction_variable = fvar,
      outcome = outcome,
      n = nrow(fit$data),
      n_clusters = length(unique(fit$data$xzc12_for_merge_final)),
      r_squared = summary(fit$model)$r.squared,
      interaction_wald_chisq = w$stat,
      interaction_wald_df = w$df,
      interaction_wald_p = w$p,
      evidence_label = ifelse(!is.na(w$p) && w$p < 0.05, "supports_amplification", "weak_or_no_amplification_evidence"),
      stringsAsFactors = FALSE
    )
  }
}

tableA <- do.call(rbind, rows)
write_csv(tableA, path("outputs", "tables", "tableA_market_friction_interactions_appendix.csv"))
write_simple_json(tableA, path("outputs", "model_summaries", "modelA_market_interactions_appendix.json"), key = "market_interactions")

log_lines <- c(
  "# Appendix Mechanism Diagnostics",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Market-friction interactions",
  "",
  "- Market-friction interactions are appendix/exploratory diagnostics under the revised plan.",
  "- They should not be used as the main identification claim unless strong and stable evidence emerges.",
  "- Default interpretation if weak: Market-friction interactions do not provide strong support for a cross-sectional amplification mechanism in the current specification."
)
writeLines(log_lines, path("outputs", "logs", "appendix_mechanism_diagnostics.md"), useBytes = TRUE)

message("Appendix market-friction interactions completed.")