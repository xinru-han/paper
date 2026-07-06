source("code/00_setup.R")

data <- read_csv(
  path("data", "analysis_ready", "paper1_revised_analysis_ready_long.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character", xzc12_for_merge_final = "character")
)
data <- prepare_revised_data(data)

iv_specs <- list(
  terrain_town_2km = "iv_terrain_barrier_town_gee_2km",
  terrain_town_1km = "iv_terrain_barrier_town_gee_1km",
  terrain_town_5km = "iv_terrain_barrier_town_gee_5km",
  terrain_county_2km = "iv_terrain_barrier_county_gee_2km",
  early_ntl_9294 = "iv_early_ntl_peak_dist_9294"
)
endog_vars <- c("market_friction_survey", "child_market", "elderly_market", "female_market")
z_terms <- c("iv_main", "child_iv", "elderly_iv", "female_iv")
exog_terms <- c(
  hh_terms_main, resource_terms_revised, "poi_market_friction_lag1",
  price_text_terms_revised,
  "gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km",
  "factor(food_category)", "factor(provn_std)", "factor(data_year)"
)

hh_once <- data[!duplicated(data$nhCode), ]
rows <- list()
fs_detail <- list()

for (iv_name in names(iv_specs)) {
  iv_var <- iv_specs[[iv_name]]
  if (!iv_var %in% names(data)) next
  x <- to_num(hh_once[[iv_var]])
  y <- to_num(hh_once$market_friction_survey)
  ok <- is.finite(x) & is.finite(y)
  cor_val <- if (sum(ok) >= 3) cor(x[ok], y[ok]) else NA_real_

  d0 <- data
  d0$iv_main <- to_num(d0[[iv_var]])
  d0$child_market <- d0$child_share * d0$market_friction_survey
  d0$elderly_market <- d0$elderly_share * d0$market_friction_survey
  d0$female_market <- d0$female_share * d0$market_friction_survey
  d0$child_iv <- d0$child_share * d0$iv_main
  d0$elderly_iv <- d0$elderly_share * d0$iv_main
  d0$female_iv <- d0$female_share * d0$iv_main

  fstats <- c()
  for (endog in endog_vars) {
    rhs <- c(exog_terms, z_terms)
    fit <- fit_lm_cluster(d0, endog, rhs)
    if (!fit$ok) next
    w <- wald_test(fit$model, fit$vcov, z_terms)
    Fval <- w$stat / w$df
    fstats <- c(fstats, Fval)
    fs_detail[[length(fs_detail) + 1]] <- data.frame(
      iv_spec = iv_name,
      iv_variable = iv_var,
      endogenous_variable = endog,
      first_stage_wald_chisq = w$stat,
      first_stage_df = w$df,
      first_stage_F = Fval,
      first_stage_p = w$p,
      n = nrow(fit$data),
      n_clusters = length(unique(fit$data$xzc12_for_merge_final)),
      stringsAsFactors = FALSE
    )
  }
  rows[[length(rows) + 1]] <- data.frame(
    iv_spec = iv_name,
    iv_variable = iv_var,
    n_households_for_correlation = sum(ok),
    correlation_with_market_friction_survey = cor_val,
    min_first_stage_F = min(fstats, na.rm = TRUE),
    median_first_stage_F = median(fstats, na.rm = TRUE),
    weak_iv_flag = min(fstats, na.rm = TRUE) < 10,
    appendix_only = TRUE,
    interpretation = ifelse(min(fstats, na.rm = TRUE) < 10, "weak_first_stage_appendix_only", "first_stage_not_weak"),
    stringsAsFactors = FALSE
  )
}

tableB <- do.call(rbind, rows)
fs_table <- do.call(rbind, fs_detail)
write_csv(tableB, path("outputs", "tables", "tableB_iv_diagnostics_appendix.csv"))
write_csv(fs_table, path("outputs", "tables", "tableB_iv_first_stage_detail_appendix.csv"))
write_simple_json(tableB, path("outputs", "model_summaries", "modelB_iv_diagnostics_appendix.json"), key = "iv_diagnostics")

weak_lines <- paste0(
  "- ", tableB$iv_spec, ": corr = ", sprintf("%.3f", tableB$correlation_with_market_friction_survey),
  ", min F = ", sprintf("%.3f", tableB$min_first_stage_F),
  ", median F = ", sprintf("%.3f", tableB$median_first_stage_F),
  ", weak = ", tableB$weak_iv_flag, "."
)
log_lines <- c(
  "# IV Diagnostics Appendix",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "- IV diagnostics are appendix/exploratory only under the revised plan.",
  "- IV results are not used as the main identification basis.",
  "",
  "## Summary",
  "",
  weak_lines
)
writeLines(log_lines, path("outputs", "logs", "iv_diagnostics_appendix.md"), useBytes = TRUE)

message("Appendix IV diagnostics completed.")