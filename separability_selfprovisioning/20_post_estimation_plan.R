source("code/00_setup.R")

out_dir <- path("outputs", "post_estimation_plan")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

rbind_fill <- function(lst) {
  lst <- Filter(Negate(is.null), lst)
  if (length(lst) == 0) return(data.frame())
  cols <- unique(unlist(lapply(lst, names), use.names = FALSE))
  out <- lapply(lst, function(x) {
    miss <- setdiff(cols, names(x))
    for (m in miss) x[[m]] <- NA
    x[, cols, drop = FALSE]
  })
  do.call(rbind, out)
}

write_out <- function(x, file) write_csv(x, file.path(out_dir, file))

fmt <- function(x, digits = 4) {
  out <- rep("NA", length(x))
  ok <- !is.na(x)
  intish <- ok & abs(x - round(x)) < sqrt(.Machine$double.eps)
  out[intish] <- format(round(x[intish]), scientific = FALSE, trim = TRUE)
  out[ok & !intish] <- format(signif(x[ok & !intish], digits), scientific = FALSE, trim = TRUE)
  out
}

md_table <- function(df, digits = 4) {
  if (is.null(df) || nrow(df) == 0) return("")
  df2 <- df
  for (nm in names(df2)) {
    if (is.numeric(df2[[nm]])) df2[[nm]] <- fmt(df2[[nm]], digits)
  }
  lines <- c(
    paste0("| ", paste(names(df2), collapse = " | "), " |"),
    paste0("|", paste(rep("---", ncol(df2)), collapse = "|"), "|")
  )
  for (i in seq_len(nrow(df2))) {
    vals <- vapply(df2[i, , drop = FALSE], function(x) as.character(x[1]), character(1))
    vals <- gsub("\\|", "\\\\|", vals)
    lines <- c(lines, paste0("| ", paste(vals, collapse = " | "), " |"))
  }
  paste(lines, collapse = "\n")
}

fit_cluster <- function(d, outcome, rhs_terms, cluster_var = "xzc12_for_merge_final") {
  f <- as.formula(paste(outcome, "~", paste(rhs_terms, collapse = " + ")))
  vars_needed <- unique(c(all.vars(f), cluster_var))
  d0 <- d[complete.cases(d[, vars_needed, drop = FALSE]), ]
  if (nrow(d0) < 100 || length(unique(d0[[outcome]])) < 2) {
    return(list(ok = FALSE, formula = f, data = d0, model = NULL, vcov = NULL))
  }
  model <- lm(f, data = d0)
  vc <- cluster_vcov(model, d0[[cluster_var]])
  list(ok = TRUE, formula = f, data = d0, model = model, vcov = vc)
}

coef_row <- function(fit, term, extra = list()) {
  if (!fit$ok || !term %in% names(coef(fit$model))) {
    row <- data.frame(
      term = term, estimate = NA_real_, std_error_cluster = NA_real_,
      t_stat = NA_real_, p_value = NA_real_, stringsAsFactors = FALSE
    )
  } else {
    est <- coef(fit$model)[term]
    se <- sqrt(diag(fit$vcov))[term]
    row <- data.frame(
      term = term,
      estimate = unname(est),
      std_error_cluster = unname(se),
      t_stat = unname(est / se),
      p_value = unname(2 * pnorm(abs(est / se), lower.tail = FALSE)),
      stringsAsFactors = FALSE
    )
  }
  for (nm in names(extra)) row[[nm]] <- extra[[nm]]
  row
}

wald_row_from_fit <- function(fit, terms, analysis, outcome, block) {
  if (!fit$ok) {
    return(data.frame(
      analysis = analysis, outcome = outcome, block = block,
      n = nrow(fit$data), n_clusters = NA_integer_, r_squared = NA_real_,
      wald_chisq = NA_real_, wald_df = 0L, wald_p = NA_real_,
      stringsAsFactors = FALSE
    ))
  }
  w <- wald_test(fit$model, fit$vcov, terms)
  data.frame(
    analysis = analysis,
    outcome = outcome,
    block = block,
    n = nrow(fit$data),
    n_clusters = length(unique(fit$data$xzc12_for_merge_final)),
    r_squared = summary(fit$model)$r.squared,
    wald_chisq = w$stat,
    wald_df = w$df,
    wald_p = w$p,
    stringsAsFactors = FALSE
  )
}

rif_quantile <- function(y, tau) {
  y <- y[is.finite(y)]
  q <- as.numeric(stats::quantile(y, probs = tau, na.rm = TRUE, names = FALSE, type = 7))
  den <- stats::density(y, na.rm = TRUE)
  fq <- approx(den$x, den$y, xout = q, rule = 2)$y
  q + (tau - as.numeric(y <= q)) / fq
}

data <- read_csv(
  path("data", "analysis_ready", "paper1_revised_analysis_ready_long.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character", xzc12_for_merge_final = "character")
)
data <- prepare_revised_data(data)

comp <- hh_terms_main
controls <- c(resource_terms_revised, market_gaez_terms_revised, price_text_terms_revised)
controls_raw <- setdiff(controls, "factor(provn_std)")
controls_no_village_absorbed <- c(
  resource_terms_revised,
  "price_hedonic_imputed_w99_yuan_per_jin",
  "factor(data_year)",
  "factor(food_category)"
)
pooled_fe <- c("factor(food_category)", "factor(data_year)")
village_fe <- c("factor(food_category)", "factor(data_year)", "factor(xzc12_for_merge_final)")
hh_block <- comp
outcomes_main <- c("production_participation", "ihs_selfprod_amount")

m3_vars <- unique(c(
  "production_participation", "ihs_selfprod_amount",
  all.vars(as.formula(paste("~", paste(baseline_rhs("M3"), collapse = " + ")))),
  "xzc12_for_merge_final"
))
data_common_m3 <- data[complete.cases(data[, m3_vars, drop = FALSE]), ]

sample_summary <- data.frame(
  input_rows = nrow(data),
  common_m3_rows = nrow(data_common_m3),
  common_m3_households = length(unique(data_common_m3$nhCode)),
  common_m3_village_clusters = length(unique(data_common_m3$xzc12_for_merge_final)),
  self_suff_nonmissing_rows = sum(!is.na(data_common_m3$self_suff_rate)),
  stringsAsFactors = FALSE
)
write_out(sample_summary, "00_sample_summary.csv")

## A0. Stacked two-margin omnibus test.
stack_ext <- data_common_m3
stack_ext$y_stack <- stack_ext$production_participation
stack_ext$margin <- "ext"
stack_int <- data_common_m3
stack_int$y_stack <- stack_int$ihs_selfprod_amount
stack_int$margin <- "int"
stack <- rbind(stack_ext, stack_int)
for (v in c(comp, controls_raw)) {
  stack[[paste0(v, "_ext")]] <- stack[[v]] * as.numeric(stack$margin == "ext")
  stack[[paste0(v, "_int")]] <- stack[[v]] * as.numeric(stack$margin == "int")
}
a0_rhs <- c(
  paste0(c(comp, controls_raw), "_ext"),
  paste0(c(comp, controls_raw), "_int"),
  "factor(margin):factor(food_category)",
  "factor(margin):factor(data_year)",
  "factor(margin):factor(provn_std)"
)
a0_fit <- fit_cluster(stack, "y_stack", a0_rhs)
a0_terms <- c(paste0(comp, "_ext"), paste0(comp, "_int"))
a0 <- wald_row_from_fit(a0_fit, a0_terms, "A0", "participation_and_ihs_stacked", "composition_ext_and_int")
write_out(a0, "A0_stacked_two_margin_omnibus.csv")

## A1. Mundlak between-within decomposition.
for (v in comp) {
  data_common_m3[[paste0(v, "_vm")]] <- ave(data_common_m3[[v]], data_common_m3$xzc12_for_merge_final, FUN = function(x) mean(x, na.rm = TRUE))
}
comp_vm <- paste0(comp, "_vm")
a1_rows <- list()
a1_coef_rows <- list()
for (outcome in c("production_participation", "self_suff_rate", "ihs_selfprod_amount")) {
  fit <- fit_cluster(data_common_m3, outcome, c(comp, comp_vm, controls, pooled_fe))
  a1_rows[[length(a1_rows) + 1]] <- wald_row_from_fit(fit, comp_vm, "A1_Mundlak", outcome, "between_village_means")
  a1_rows[[length(a1_rows) + 1]] <- wald_row_from_fit(fit, comp, "A1_Mundlak", outcome, "within_household_deviation")
  for (term in c(comp, comp_vm)) {
    a1_coef_rows[[length(a1_coef_rows) + 1]] <- coef_row(fit, term, list(analysis = "A1_Mundlak", outcome = outcome))
  }
}
a1 <- rbind_fill(a1_rows)
a1_coef <- rbind_fill(a1_coef_rows)
write_out(a1, "A1_mundlak_wald.csv")
write_out(a1_coef, "A1_mundlak_coefficients.csv")

## A1b. Component-wise and leave-one-out tests.
a1b_rows <- list()
a1b_coef_rows <- list()
models_a1b <- list(
  pooled_participation = fit_cluster(data_common_m3, "production_participation", c(comp, controls, pooled_fe)),
  villageFE_ihs = fit_cluster(data_common_m3, "ihs_selfprod_amount", c(comp, controls_no_village_absorbed, "factor(xzc12_for_merge_final)"))
)
for (nm in names(models_a1b)) {
  fit <- models_a1b[[nm]]
  outcome <- ifelse(nm == "pooled_participation", "production_participation", "ihs_selfprod_amount")
  for (term in comp) {
    a1b_rows[[length(a1b_rows) + 1]] <- wald_row_from_fit(fit, term, "A1b_component", outcome, paste0("single_", term))
    a1b_coef_rows[[length(a1b_coef_rows) + 1]] <- coef_row(fit, term, list(analysis = "A1b_component", outcome = outcome, model = nm))
  }
  for (drop_term in comp) {
    block_terms <- setdiff(comp, drop_term)
    a1b_rows[[length(a1b_rows) + 1]] <- wald_row_from_fit(fit, block_terms, "A1b_leave_one_out", outcome, paste0("drop_", drop_term))
  }
}
write_out(rbind_fill(a1b_rows), "A1b_component_leave_one_out_wald.csv")
write_out(rbind_fill(a1b_coef_rows), "A1b_component_coefficients.csv")

## A2. RIF quantile profile for self-sufficiency.
taus <- c(0.5, 0.6, 0.7, 0.8, 0.9)
d2 <- data_common_m3[!is.na(data_common_m3$self_suff_rate), ]
a2_coef_rows <- list()
a2_stack <- list()
for (tt in taus) {
  rif_vals <- rif_quantile(d2$self_suff_rate, tt)
  d_tau <- d2[is.finite(d2$self_suff_rate), ]
  d_tau$rif_y <- rif_vals
  d_tau$tau <- tt
  fit <- fit_cluster(d_tau, "rif_y", c(comp, controls_no_village_absorbed, "factor(xzc12_for_merge_final)"))
  for (term in comp) {
    a2_coef_rows[[length(a2_coef_rows) + 1]] <- coef_row(fit, term, list(analysis = "A2_RIF", outcome = "self_suff_rate", tau = tt))
  }
  a2_stack[[length(a2_stack) + 1]] <- d_tau
}
a2_coef <- rbind_fill(a2_coef_rows)
write_out(a2_coef, "A2_rif_quantile_coefficients.csv")

stk <- do.call(rbind, a2_stack)
stk$tau_c <- stk$tau - mean(taus)
for (v in comp) stk[[paste0(v, "_tau_c")]] <- stk[[v]] * stk$tau_c
trend_terms <- paste0(comp, "_tau_c")
a2_trend_fit <- fit_cluster(stk, "rif_y", c(comp, trend_terms, controls_no_village_absorbed, "factor(xzc12_for_merge_final)"))
a2_trend <- wald_row_from_fit(a2_trend_fit, "elderly_share_tau_c", "A2_RIF_trend", "self_suff_rate", "elderly_share_by_tau")
a2_trend_all <- wald_row_from_fit(a2_trend_fit, trend_terms, "A2_RIF_trend", "self_suff_rate", "all_composition_by_tau")
a2_trend_coef <- rbind_fill(lapply(trend_terms, function(term) {
  coef_row(a2_trend_fit, term, list(analysis = "A2_RIF_trend", outcome = "self_suff_rate"))
}))
write_out(rbind(a2_trend, a2_trend_all), "A2_rif_trend_wald.csv")
write_out(a2_trend_coef, "A2_rif_trend_coefficients.csv")

## A3. Composition x market-access/friction interactions.
market_vars <- c("poi_market_friction_lag1", "market_friction_survey")
a3_rows <- list()
a3_coef_rows <- list()
for (outcome in c("ihs_selfprod_amount", "self_suff_rate")) {
  d3 <- data_common_m3
  for (cv in comp) {
    for (mv in market_vars) {
      d3[[paste0(cv, "_X_", mv)]] <- d3[[cv]] * d3[[mv]]
    }
  }
  int_terms <- as.vector(outer(comp, market_vars, function(x, y) paste0(x, "_X_", y)))
  elderly_int <- int_terms[grepl("^elderly_share_X_", int_terms)]
  fit <- fit_cluster(d3, outcome, c(comp, int_terms, controls_no_village_absorbed, "factor(xzc12_for_merge_final)"))
  a3_rows[[length(a3_rows) + 1]] <- wald_row_from_fit(fit, int_terms, "A3_market_interactions", outcome, "all_composition_market_interactions")
  a3_rows[[length(a3_rows) + 1]] <- wald_row_from_fit(fit, elderly_int, "A3_market_interactions", outcome, "elderly_market_interactions")
  for (term in int_terms) {
    a3_coef_rows[[length(a3_coef_rows) + 1]] <- coef_row(fit, term, list(analysis = "A3_market_interactions", outcome = outcome))
  }
}
write_out(rbind_fill(a3_rows), "A3_market_interactions_wald.csv")
write_out(rbind_fill(a3_coef_rows), "A3_market_interactions_coefficients.csv")

## A4. Category-attribute meta-regression; dairy excluded.
category_tests <- read_csv(path("outputs", "tables", "table3_category_specific_tests.csv"))
cat_map <- data.frame(
  food_category = c("danlei", "youzhi", "shucai", "shuiguo", "doulei", "roulei", "zhushi"),
  cat = c("eggs", "oils", "veg", "fruit", "beans", "meat", "staple"),
  perish = c(3, 1, 3, 3, 1, 3, 1),
  courty = c(3, 2, 3, 2, 2, 1, 2),
  thin = c(2, 2, 1, 2, 2, 1, 1),
  stringsAsFactors = FALSE
)
meta <- merge(
  category_tests[category_tests$outcome == "production_participation", c("food_category", "food_category_label", "hhcomp_wald_chisq", "hhcomp_wald_p", "n")],
  cat_map,
  by = "food_category"
)
meta$bandwidth <- rowMeans(meta[, c("perish", "courty", "thin")])
sp <- suppressWarnings(cor.test(meta$hhcomp_wald_chisq, meta$bandwidth, method = "spearman", exact = FALSE))
lm_meta <- lm(hhcomp_wald_chisq ~ bandwidth, data = meta, weights = n)
meta_summary <- data.frame(
  analysis = "A4_category_attribute_meta",
  n_categories = nrow(meta),
  spearman_rho = unname(sp$estimate),
  spearman_p = sp$p.value,
  wls_bandwidth_coef = coef(lm_meta)["bandwidth"],
  wls_bandwidth_se = sqrt(diag(vcov(lm_meta)))["bandwidth"],
  wls_bandwidth_p = summary(lm_meta)$coefficients["bandwidth", "Pr(>|t|)"],
  stringsAsFactors = FALSE
)
write_out(meta, "A4_category_attribute_meta_data.csv")
write_out(meta_summary, "A4_category_attribute_meta_summary.csv")

## A5. External validity robustness.
a5_rows <- list()
for (yr in sort(unique(data_common_m3$data_year))) {
  d_yr <- data_common_m3[data_common_m3$data_year == yr, ]
  rhs_year <- setdiff(c(comp, controls, "factor(food_category)", "factor(provn_std)"), "factor(data_year)")
  fit <- fit_cluster(d_yr, "production_participation", rhs_year)
  a5_rows[[length(a5_rows) + 1]] <- wald_row_from_fit(fit, comp, "A5_wave_split", "production_participation", paste0("wave_", yr))
}
for (prov in sort(unique(data_common_m3$provn_std))) {
  d_prov <- data_common_m3[data_common_m3$provn_std != prov, ]
  fit_part <- fit_cluster(d_prov, "production_participation", c(comp, controls, pooled_fe))
  fit_ihs <- fit_cluster(d_prov, "ihs_selfprod_amount", c(comp, controls_no_village_absorbed, "factor(xzc12_for_merge_final)"))
  a5_rows[[length(a5_rows) + 1]] <- wald_row_from_fit(fit_part, comp, "A5_leave_one_province_out", "production_participation", paste0("exclude_", prov))
  a5_rows[[length(a5_rows) + 1]] <- wald_row_from_fit(fit_ihs, comp, "A5_leave_one_province_out", "ihs_selfprod_amount", paste0("exclude_", prov))
}
write_out(rbind_fill(a5_rows), "A5_external_validity_wald.csv")

## Compact report for manuscript integration.
report <- c(
  "# Post-Estimation Results for Paper 1",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "All models use R/base `lm()` with village-clustered `sandwich::vcovCL()` inference, following the existing project pipeline.",
  "",
  "## Sample",
  "",
  md_table(sample_summary),
  "",
  "## A0. Two-margin omnibus test",
  "",
  md_table(a0),
  "",
  "## A1. Mundlak between-within decomposition",
  "",
  md_table(a1[, c("outcome", "block", "n", "n_clusters", "wald_chisq", "wald_df", "wald_p")]),
  "",
  "## A1b. Component and leave-one-out tests",
  "",
  "See `A1b_component_leave_one_out_wald.csv` and `A1b_component_coefficients.csv`.",
  "",
  "## A2. RIF quantile profile",
  "",
  md_table(a2_coef[a2_coef$term == "elderly_share", c("tau", "term", "estimate", "std_error_cluster", "p_value")]),
  "",
  md_table(rbind(a2_trend, a2_trend_all)[, c("block", "wald_chisq", "wald_df", "wald_p")]),
  "",
  "## A3. Composition by market friction interactions",
  "",
  md_table(read_csv(file.path(out_dir, "A3_market_interactions_wald.csv"))[, c("outcome", "block", "wald_chisq", "wald_df", "wald_p")]),
  "",
  "## A4. Category-attribute meta-regression",
  "",
  md_table(meta_summary),
  "",
  "## A5. External validity",
  "",
  "See `A5_external_validity_wald.csv`."
)
writeLines(report, file.path(out_dir, "post_estimation_results.md"), useBytes = TRUE)

message("Post-estimation plan analyses completed: ", out_dir)
