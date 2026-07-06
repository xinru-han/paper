options(warn = 1)

root <- getwd()
dir.create(file.path(root, "outputs", "tables"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "logs"), recursive = TRUE, showWarnings = FALSE)

path <- function(...) file.path(root, ...)

read_csv <- function(file, colClasses = NULL) {
  args <- list(
    file = file,
    stringsAsFactors = FALSE,
    check.names = FALSE,
    fileEncoding = "UTF-8"
  )
  if (!is.null(colClasses)) args$colClasses <- colClasses
  out <- do.call(read.csv, args)
  names(out) <- gsub("\ufeff", "", names(out), fixed = TRUE)
  out
}

write_csv <- function(x, file) {
  write.csv(x, file, row.names = FALSE, fileEncoding = "UTF-8")
}

to_num <- function(x) {
  if (is.numeric(x)) return(x)
  suppressWarnings(as.numeric(x))
}

median_impute <- function(data, var) {
  x <- to_num(data[[var]])
  miss <- is.na(x)
  med <- median(x, na.rm = TRUE)
  if (is.na(med)) med <- 0
  x[miss] <- med
  data[[paste0(var, "_imp")]] <- x
  data[[paste0(var, "_missing")]] <- as.integer(miss)
  data
}

cluster_vcov <- function(model, cluster) {
  sandwich::vcovCL(model, cluster = cluster, type = "HC1")
}

wald_test <- function(model, vcov_mat, terms) {
  coefs <- coef(model)
  terms <- intersect(terms, names(coefs))
  terms <- terms[!is.na(coefs[terms])]
  if (length(terms) == 0) {
    return(list(stat = NA_real_, df = 0L, p = NA_real_))
  }
  b <- coefs[terms]
  V <- vcov_mat[terms, terms, drop = FALSE]
  keep <- is.finite(b) & apply(V, 1, function(x) all(is.finite(x)))
  b <- b[keep]
  V <- V[keep, keep, drop = FALSE]
  if (length(b) == 0) {
    return(list(stat = NA_real_, df = 0L, p = NA_real_))
  }
  invV <- tryCatch(solve(V), error = function(e) MASS::ginv(V))
  stat <- as.numeric(t(b) %*% invV %*% b)
  df <- length(b)
  list(stat = stat, df = df, p = 1 - pchisq(stat, df))
}

find_interaction_name <- function(coef_names, term, friction_var) {
  candidates <- c(paste0(term, ":", friction_var), paste0(friction_var, ":", term))
  hit <- candidates[candidates %in% coef_names]
  if (length(hit) == 0) return(NA_character_)
  hit[1]
}

fit_wald_model <- function(data, outcome, terms_to_test, rhs_terms, cluster_var = "xzc12_for_merge_final") {
  f <- as.formula(paste(outcome, "~", paste(rhs_terms, collapse = " + ")))
  vars_needed <- unique(c(all.vars(f), cluster_var))
  d <- data[complete.cases(data[, vars_needed, drop = FALSE]), ]
  if (nrow(d) < 100 || length(unique(d[[outcome]])) < 2) {
    return(list(ok = FALSE, n = nrow(d), n_clusters = NA_integer_, r2 = NA_real_, wald = list(stat = NA_real_, df = 0L, p = NA_real_)))
  }
  model <- lm(f, data = d)
  vc <- cluster_vcov(model, d[[cluster_var]])
  wald <- wald_test(model, vc, terms_to_test)
  list(
    ok = TRUE,
    n = nrow(d),
    n_clusters = length(unique(d[[cluster_var]])),
    r2 = summary(model)$r.squared,
    wald = wald
  )
}

fit_interaction_wald <- function(data, outcome, friction_var, base_hh_terms, extra_controls) {
  interaction_part <- paste0("(", paste(base_hh_terms, collapse = " + "), ") * ", friction_var)
  rhs <- c(interaction_part, extra_controls)
  f <- as.formula(paste(outcome, "~", paste(rhs, collapse = " + ")))
  vars_needed <- unique(c(all.vars(f), "xzc12_for_merge_final"))
  d <- data[complete.cases(data[, vars_needed, drop = FALSE]), ]
  if (nrow(d) < 100 || length(unique(d[[outcome]])) < 2) {
    return(list(ok = FALSE, n = nrow(d), n_clusters = NA_integer_, r2 = NA_real_, wald = list(stat = NA_real_, df = 0L, p = NA_real_)))
  }
  model <- lm(f, data = d)
  vc <- cluster_vcov(model, d$xzc12_for_merge_final)
  interaction_terms <- vapply(
    base_hh_terms,
    function(term) find_interaction_name(names(coef(model)), term, friction_var),
    character(1)
  )
  wald <- wald_test(model, vc, interaction_terms)
  list(
    ok = TRUE,
    n = nrow(d),
    n_clusters = length(unique(d$xzc12_for_merge_final)),
    r2 = summary(model)$r.squared,
    wald = wald
  )
}

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

data <- read_csv(
  path("data", "cleaned", "paper1_household_category_long.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character", xzc12_for_merge_final = "character")
)

impute_vars <- c(
  "household_head_age", "household_head_education", "household_head_gender_male",
  "household_assets_count_proxy", "log1p_total_income_w_w99",
  "log1p_agri_business_income_w99", "log1p_annual_expense_total_w99"
)
for (v in impute_vars[impute_vars %in% names(data)]) {
  data <- median_impute(data, v)
}

data$food_category <- factor(data$food_category)
data$data_year <- factor(data$data_year)
data$provn_std <- factor(data$provn_std)

hh_terms <- c("household_size_reconstructed", "child_share", "elderly_share", "female_share")
resource_terms <- c(
  "log1p_total_income_w_w99_imp", "log1p_total_income_w_w99_missing",
  "log1p_agri_business_income_w99_imp", "log1p_agri_business_income_w99_missing",
  "log1p_annual_expense_total_w99_imp", "log1p_annual_expense_total_w99_missing",
  "total_sown_area", "agricultural_labor_days", "offfarm_labor_days",
  "household_assets_count_proxy_imp", "household_assets_count_proxy_missing",
  "household_head_age_imp", "household_head_age_missing",
  "household_head_education_imp", "household_head_education_missing",
  "household_head_gender_male_imp", "household_head_gender_male_missing"
)
full_controls <- c(
  resource_terms,
  "market_friction_survey", "poi_market_friction_lag1",
  "price_hedonic_imputed_w99_yuan_per_jin",
  "gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km",
  "risk_salience_z_5yr_sum", "governance_capacity_z_5yr_sum",
  "trust_signal_z_5yr_sum", "attention_z_5yr_sum",
  "factor(food_category)", "factor(provn_std)", "factor(data_year)"
)
interaction_controls <- c(
  resource_terms,
  "poi_market_friction_lag1",
  "price_hedonic_imputed_w99_yuan_per_jin",
  "gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km",
  "risk_salience_z_5yr_sum", "governance_capacity_z_5yr_sum",
  "trust_signal_z_5yr_sum", "attention_z_5yr_sum",
  "factor(food_category)", "factor(provn_std)", "factor(data_year)"
)

set.seed(20260602)
B <- 99
outcome_main <- "production_participation"

## 1. Household-composition permutation placebo ---------------------------
real_baseline <- fit_wald_model(data, outcome_main, hh_terms, c(hh_terms, full_controls))

hh_once <- data[!duplicated(data$nhCode), c("nhCode", "provn_std", "data_year", hh_terms)]
hh_row <- match(data$nhCode, hh_once$nhCode)
placebo_draws <- list()

for (b in seq_len(B)) {
  hh_perm <- shuffle_rows_within(hh_once, c("provn_std", "data_year"), hh_terms)
  d_perm <- data
  for (v in hh_terms) {
    d_perm[[paste0(v, "_placebo")]] <- hh_perm[[v]][hh_row]
  }
  placebo_terms <- paste0(hh_terms, "_placebo")
  res <- fit_wald_model(d_perm, outcome_main, placebo_terms, c(placebo_terms, full_controls))
  placebo_draws[[length(placebo_draws) + 1]] <- data.frame(
    placebo_type = "household_composition_permutation",
    draw = b,
    outcome = outcome_main,
    wald_chisq = res$wald$stat,
    wald_df = res$wald$df,
    wald_p = res$wald$p,
    n = res$n,
    n_clusters = res$n_clusters,
    stringsAsFactors = FALSE
  )
}

## 2. Pseudo-market-friction permutation placebo ---------------------------
real_interaction <- fit_interaction_wald(data, outcome_main, "market_friction_survey", hh_terms, interaction_controls)

vill_once <- data[!duplicated(data$xzc12_for_merge_final), c("xzc12_for_merge_final", "provn_std", "data_year", "market_friction_survey")]
vill_row <- match(data$xzc12_for_merge_final, vill_once$xzc12_for_merge_final)

for (b in seq_len(B)) {
  vill_perm <- shuffle_rows_within(vill_once, c("provn_std", "data_year"), "market_friction_survey")
  d_perm <- data
  d_perm$market_friction_placebo <- vill_perm$market_friction_survey[vill_row]
  res <- fit_interaction_wald(d_perm, outcome_main, "market_friction_placebo", hh_terms, interaction_controls)
  placebo_draws[[length(placebo_draws) + 1]] <- data.frame(
    placebo_type = "market_friction_village_permutation",
    draw = b,
    outcome = outcome_main,
    wald_chisq = res$wald$stat,
    wald_df = res$wald$df,
    wald_p = res$wald$p,
    n = res$n,
    n_clusters = res$n_clusters,
    stringsAsFactors = FALSE
  )
}

draw_table <- do.call(rbind, placebo_draws)
write_csv(draw_table, path("outputs", "tables", "table6_placebo_permutation_draws.csv"))

summarize_placebo <- function(draws, real_stat, real_df, real_p, n, n_clusters) {
  ok <- is.finite(draws$wald_chisq)
  vals <- draws$wald_chisq[ok]
  data.frame(
    n_draws = length(vals),
    real_wald_chisq = real_stat,
    real_wald_df = real_df,
    real_wald_p = real_p,
    randomization_p_ge_real = (sum(vals >= real_stat) + 1) / (length(vals) + 1),
    placebo_mean = mean(vals, na.rm = TRUE),
    placebo_p50 = quantile(vals, 0.50, na.rm = TRUE),
    placebo_p90 = quantile(vals, 0.90, na.rm = TRUE),
    placebo_p95 = quantile(vals, 0.95, na.rm = TRUE),
    placebo_max = max(vals, na.rm = TRUE),
    n = n,
    n_clusters = n_clusters,
    stringsAsFactors = FALSE
  )
}

placebo_summary <- rbind(
  cbind(
    placebo_type = "household_composition_permutation",
    outcome = outcome_main,
    summarize_placebo(
      draw_table[draw_table$placebo_type == "household_composition_permutation", ],
      real_baseline$wald$stat, real_baseline$wald$df, real_baseline$wald$p,
      real_baseline$n, real_baseline$n_clusters
    )
  ),
  cbind(
    placebo_type = "market_friction_village_permutation",
    outcome = outcome_main,
    summarize_placebo(
      draw_table[draw_table$placebo_type == "market_friction_village_permutation", ],
      real_interaction$wald$stat, real_interaction$wald$df, real_interaction$wald$p,
      real_interaction$n, real_interaction$n_clusters
    )
  )
)
write_csv(placebo_summary, path("outputs", "tables", "table6_placebo_permutation.csv"))

## 3. Leave-one-province robustness ---------------------------------------
loo_rows <- list()
for (prov in sort(unique(as.character(data$provn_std)))) {
  if (is.na(prov) || prov == "") next
  d_loo <- data[data$provn_std != prov, ]
  bres <- fit_wald_model(d_loo, outcome_main, hh_terms, c(hh_terms, full_controls))
  ires <- fit_interaction_wald(d_loo, outcome_main, "market_friction_survey", hh_terms, interaction_controls)
  loo_rows[[length(loo_rows) + 1]] <- data.frame(
    dropped_province = prov,
    outcome = outcome_main,
    baseline_n = bres$n,
    baseline_n_clusters = bres$n_clusters,
    baseline_r_squared = bres$r2,
    baseline_hhcomp_wald_chisq = bres$wald$stat,
    baseline_hhcomp_wald_df = bres$wald$df,
    baseline_hhcomp_wald_p = bres$wald$p,
    interaction_n = ires$n,
    interaction_n_clusters = ires$n_clusters,
    interaction_r_squared = ires$r2,
    interaction_wald_chisq = ires$wald$stat,
    interaction_wald_df = ires$wald$df,
    interaction_wald_p = ires$wald$p,
    stringsAsFactors = FALSE
  )
}
loo_table <- do.call(rbind, loo_rows)
write_csv(loo_table, path("outputs", "tables", "table6_leave_one_province.csv"))

## 4. Alternative outcomes and household-composition definitions ----------
comp_specs <- list(
  proportion = c("household_size_reconstructed", "child_share", "elderly_share", "female_share"),
  dependency = c("household_size_reconstructed", "dependency_ratio", "female_share"),
  counts = c("num_children", "num_elderly", "num_adult_male", "num_adult_female")
)
alt_outcomes <- c("production_participation", "log_selfprod_amount", "ihs_selfprod_amount", "self_suff_rate")
alt_rows <- list()
for (comp_name in names(comp_specs)) {
  terms <- comp_specs[[comp_name]]
  for (outcome in alt_outcomes[alt_outcomes %in% names(data)]) {
    res <- fit_wald_model(data, outcome, terms, c(terms, full_controls))
    alt_rows[[length(alt_rows) + 1]] <- data.frame(
      composition_spec = comp_name,
      outcome = outcome,
      tested_terms = paste(terms, collapse = " + "),
      n = res$n,
      n_clusters = res$n_clusters,
      r_squared = res$r2,
      wald_chisq = res$wald$stat,
      wald_df = res$wald$df,
      wald_p = res$wald$p,
      stringsAsFactors = FALSE
    )
  }
}
alt_table <- do.call(rbind, alt_rows)
write_csv(alt_table, path("outputs", "tables", "table6_alternative_composition_outcomes.csv"))

log_lines <- c(
  "# Placebo and Robustness Checks",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Estimation Notes",
  "",
  paste0("- Permutation checks use B = ", B, " draws with seed 20260602."),
  "- Household-composition placebo shuffles the full household-composition vector across households within province-year strata.",
  "- Pseudo-market placebo shuffles village survey market friction across villages within province-year strata.",
  "- Leave-one-province checks rerun the baseline household-composition Wald and the survey market-friction interaction Wald.",
  "- Alternative-composition checks compare proportion, dependency-ratio, and count-based household structure definitions.",
  "- No condiment, sugar, tea, household fixed effect, village fixed effect, village-year fixed effect, DID, or panel specification is used.",
  "",
  "## Key Placebo Summary",
  "",
  paste0(
    "- Household-composition permutation: real Wald = ",
    sprintf("%.3f", real_baseline$wald$stat),
    ", randomization p = ",
    sprintf("%.3f", placebo_summary$randomization_p_ge_real[placebo_summary$placebo_type == "household_composition_permutation"]),
    "."
  ),
  paste0(
    "- Market-friction permutation: real interaction Wald = ",
    sprintf("%.3f", real_interaction$wald$stat),
    ", randomization p = ",
    sprintf("%.3f", placebo_summary$randomization_p_ge_real[placebo_summary$placebo_type == "market_friction_village_permutation"]),
    "."
  ),
  "",
  "## Outputs",
  "",
  "- `outputs/tables/table6_placebo_permutation.csv`",
  "- `outputs/tables/table6_placebo_permutation_draws.csv`",
  "- `outputs/tables/table6_leave_one_province.csv`",
  "- `outputs/tables/table6_alternative_composition_outcomes.csv`"
)
writeLines(log_lines, path("outputs", "logs", "robustness_log.md"), useBytes = TRUE)

message("Placebo and robustness checks completed.")