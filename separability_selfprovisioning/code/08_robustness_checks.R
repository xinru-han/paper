source("code/00_setup.R")

data <- read_csv(
  path("data", "analysis_ready", "paper1_revised_analysis_ready_long.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character", xzc12_for_merge_final = "character")
)
data <- prepare_revised_data(data)

fit_wald <- function(d, outcome, terms, controls) {
  fit <- fit_lm_cluster(d, outcome, c(terms, controls))
  if (!fit$ok) {
    return(data.frame(n = nrow(fit$data), n_clusters = NA_integer_, r_squared = NA_real_, wald_chisq = NA_real_, wald_df = 0L, wald_p = NA_real_))
  }
  w <- wald_test(fit$model, fit$vcov, terms)
  data.frame(
    n = nrow(fit$data),
    n_clusters = length(unique(fit$data$xzc12_for_merge_final)),
    r_squared = summary(fit$model)$r.squared,
    wald_chisq = w$stat,
    wald_df = w$df,
    wald_p = w$p
  )
}

controls_no_hh <- c(resource_terms_revised, market_gaez_terms_revised, price_text_terms_revised, category_year_terms_revised)
comp_specs <- list(
  proportion = hh_terms_main,
  dependency = c("household_size_reconstructed", "dependency_ratio", "female_share"),
  counts = c("num_children", "num_elderly", "num_adult_male", "num_adult_female")
)
outcomes <- c("production_participation", "log_selfprod_amount", "ihs_selfprod_amount", "self_suff_rate")

alt_rows <- list()
for (comp in names(comp_specs)) {
  terms <- comp_specs[[comp]]
  for (outcome in outcomes[outcomes %in% names(data)]) {
    res <- fit_wald(data, outcome, terms, controls_no_hh)
    alt_rows[[length(alt_rows) + 1]] <- data.frame(
      composition_spec = comp,
      outcome = outcome,
      conceptual_outcome = ifelse(outcome == "production_participation", "self_provisioning_participation", outcome),
      tested_terms = paste(terms, collapse = " + "),
      res,
      stringsAsFactors = FALSE
    )
  }
}
alt_table <- do.call(rbind, alt_rows)
write_csv(alt_table, path("outputs", "tables", "table6_alternative_composition_outcomes.csv"))

loo_rows <- list()
for (prov in sort(unique(as.character(data$provn_std)))) {
  if (is.na(prov) || prov == "") next
  d <- data[data$provn_std != prov, ]
  res <- fit_wald(d, "production_participation", hh_terms_main, controls_no_hh)
  loo_rows[[length(loo_rows) + 1]] <- data.frame(
    dropped_province = prov,
    outcome = "production_participation",
    conceptual_outcome = "self_provisioning_participation",
    res,
    stringsAsFactors = FALSE
  )
}
loo_table <- do.call(rbind, loo_rows)
write_csv(loo_table, path("outputs", "tables", "table7_leave_one_province.csv"))

shuffle_rows_within <- function(df, group_vars, value_vars) {
  out <- df
  groups <- split(seq_len(nrow(df)), interaction(df[, group_vars], drop = TRUE, lex.order = TRUE))
  for (idx in groups) {
    if (length(idx) <= 1) next
    perm <- sample(idx, length(idx), replace = FALSE)
    out[idx, value_vars] <- df[perm, value_vars]
  }
  out
}

set.seed(20260602)
B <- 99
real <- fit_wald(data, "production_participation", hh_terms_main, controls_no_hh)

hh_once <- data[!duplicated(data$nhCode), c("nhCode", "provn_std", "data_year", hh_terms_main)]
hh_row <- match(data$nhCode, hh_once$nhCode)
draws <- list()
for (b in seq_len(B)) {
  hh_perm <- shuffle_rows_within(hh_once, c("provn_std", "data_year"), hh_terms_main)
  d <- data
  placebo_terms <- paste0(hh_terms_main, "_placebo")
  for (i in seq_along(hh_terms_main)) {
    d[[placebo_terms[i]]] <- hh_perm[[hh_terms_main[i]]][hh_row]
  }
  res <- fit_wald(d, "production_participation", placebo_terms, controls_no_hh)
  draws[[length(draws) + 1]] <- data.frame(
    draw = b,
    wald_chisq = res$wald_chisq,
    wald_df = res$wald_df,
    wald_p = res$wald_p,
    n = res$n,
    n_clusters = res$n_clusters,
    stringsAsFactors = FALSE
  )
}
draw_table <- do.call(rbind, draws)
vals <- draw_table$wald_chisq[is.finite(draw_table$wald_chisq)]
perm_summary <- data.frame(
  placebo_type = "household_composition_permutation",
  outcome = "production_participation",
  n_draws = length(vals),
  true_wald_chisq = real$wald_chisq,
  true_wald_df = real$wald_df,
  true_wald_p = real$wald_p,
  placebo_mean = mean(vals),
  placebo_p50 = quantile(vals, 0.50),
  placebo_p90 = quantile(vals, 0.90),
  placebo_p95 = quantile(vals, 0.95),
  placebo_max = max(vals),
  randomization_p_value = (sum(vals >= real$wald_chisq) + 1) / (length(vals) + 1),
  n = real$n,
  n_clusters = real$n_clusters,
  stringsAsFactors = FALSE
)
write_csv(perm_summary, path("outputs", "tables", "table8_household_composition_permutation.csv"))
write_csv(draw_table, path("outputs", "tables", "table8_household_composition_permutation_draws.csv"))

png(path("outputs", "figures", "figure4_household_composition_permutation.png"), width = 1600, height = 1000, res = 180)
hist(vals, breaks = 18, col = "#9AA7B1", border = "white", main = "Household-Composition Permutation Wald Statistics", xlab = "Placebo Wald chi-square")
abline(v = real$wald_chisq, col = "#B23A48", lwd = 3)
legend("topright", legend = c("True Wald"), lwd = 3, col = "#B23A48", bty = "n")
dev.off()

## Appendix pseudo-market-friction permutation.
interaction_wald <- function(d, friction_var) {
  rhs <- c(
    paste0("(", paste(hh_terms_main, collapse = " + "), ") * ", friction_var),
    resource_terms_revised, "poi_market_friction_lag1",
    price_text_terms_revised,
    "gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km",
    "factor(provn_std)", category_year_terms_revised
  )
  fit <- fit_lm_cluster(d, "production_participation", rhs)
  if (!fit$ok) return(NA_real_)
  terms <- vapply(hh_terms_main, function(term) find_interaction_name(names(coef(fit$model)), term, friction_var), character(1))
  wald_test(fit$model, fit$vcov, terms)$stat
}

real_market <- interaction_wald(data, "market_friction_survey")
vill_once <- data[!duplicated(data$xzc12_for_merge_final), c("xzc12_for_merge_final", "provn_std", "data_year", "market_friction_survey")]
vill_row <- match(data$xzc12_for_merge_final, vill_once$xzc12_for_merge_final)
market_vals <- numeric(B)
for (b in seq_len(B)) {
  vp <- shuffle_rows_within(vill_once, c("provn_std", "data_year"), "market_friction_survey")
  d <- data
  d$market_friction_placebo <- vp$market_friction_survey[vill_row]
  market_vals[b] <- interaction_wald(d, "market_friction_placebo")
}
market_perm <- data.frame(
  placebo_type = "market_friction_village_permutation",
  outcome = "production_participation",
  n_draws = sum(is.finite(market_vals)),
  true_interaction_wald = real_market,
  placebo_mean = mean(market_vals, na.rm = TRUE),
  placebo_p95 = quantile(market_vals, 0.95, na.rm = TRUE),
  randomization_p_value = (sum(market_vals >= real_market, na.rm = TRUE) + 1) / (sum(is.finite(market_vals)) + 1),
  stringsAsFactors = FALSE
)
write_csv(market_perm, path("outputs", "tables", "tableA_market_friction_permutation_appendix.csv"))

model6 <- rbind(
  data.frame(model = "alternative_composition_outcomes", rows = nrow(alt_table), stringsAsFactors = FALSE),
  data.frame(model = "leave_one_province", rows = nrow(loo_table), stringsAsFactors = FALSE),
  data.frame(model = "household_composition_permutation", rows = nrow(perm_summary), stringsAsFactors = FALSE)
)
write_simple_json(model6, path("outputs", "model_summaries", "model6_robustness.json"), key = "robustness_outputs")

message("Robustness checks completed.")