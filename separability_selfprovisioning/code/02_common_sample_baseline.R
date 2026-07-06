source("code/00_setup.R")

data <- read_csv(
  path("data", "analysis_ready", "paper1_revised_analysis_ready_long.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character", xzc12_for_merge_final = "character")
)
data <- prepare_revised_data(data)

outcomes <- c("production_participation", "log_selfprod_amount", "ihs_selfprod_amount")
m3_vars <- unique(c(
  outcomes,
  all.vars(as.formula(paste("~", paste(baseline_rhs("M3"), collapse = " + ")))),
  "xzc12_for_merge_final"
))
common <- complete.cases(data[, m3_vars, drop = FALSE])
data_common <- data[common, ]

specs <- c("M0", "M1", "M2", "M3")
rows <- list()
coef_rows <- list()

for (outcome in outcomes) {
  for (spec in specs) {
    fit <- fit_lm_cluster(data_common, outcome, baseline_rhs(spec))
    if (!fit$ok) next
    w <- wald_test(fit$model, fit$vcov, hh_terms_main)
    rows[[length(rows) + 1]] <- data.frame(
      outcome = outcome,
      conceptual_outcome = ifelse(outcome == "production_participation", "self_provisioning_participation", outcome),
      spec = spec,
      common_m3_sample = TRUE,
      n = nrow(fit$data),
      n_clusters = length(unique(fit$data$xzc12_for_merge_final)),
      r_squared = summary(fit$model)$r.squared,
      hhcomp_wald_chisq = w$stat,
      hhcomp_wald_df = w$df,
      hhcomp_wald_p = w$p,
      stringsAsFactors = FALSE
    )
    for (term in hh_terms_main) {
      s <- safe_coef_stats(fit$model, fit$vcov, term)
      coef_rows[[length(coef_rows) + 1]] <- data.frame(
        outcome = outcome,
        spec = spec,
        term = term,
        estimate = s["estimate"],
        std_error_cluster = s["std_error_cluster"],
        t_stat = s["t_stat"],
        p_value = s["p_value"],
        direction = ifelse(is.na(s["estimate"]), "NA", ifelse(s["estimate"] > 0, "positive", ifelse(s["estimate"] < 0, "negative", "zero"))),
        n = nrow(fit$data),
        n_clusters = length(unique(fit$data$xzc12_for_merge_final)),
        r_squared = summary(fit$model)$r.squared,
        stringsAsFactors = FALSE
      )
    }
  }
}

table2 <- do.call(rbind, rows)
coef_table <- do.call(rbind, coef_rows)

write_csv(table2, path("outputs", "tables", "table2_common_sample_baseline.csv"))
write_csv(coef_table, path("outputs", "tables", "table2_common_sample_baseline_coefficients_raw.csv"))
write_simple_json(table2, path("outputs", "model_summaries", "model2_common_sample_baseline.json"))

orig_rows <- nrow(data)
common_rows <- nrow(data_common)
log_lines <- c(
  "# Common Sample Log",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "- M0-M3 are estimated on the common complete-case M3 sample.",
  paste0("- Original revised rows: ", orig_rows),
  paste0("- Common M3 rows: ", common_rows),
  paste0("- Common M3 clusters: ", length(unique(data_common$xzc12_for_merge_final))),
  paste0("- Rows excluded from common M3 sample: ", orig_rows - common_rows),
  paste0("- Excluded share: ", sprintf("%.4f", (orig_rows - common_rows) / orig_rows)),
  "",
  "## Variables defining the common M3 sample",
  "",
  paste0("- `", m3_vars, "`")
)
writeLines(log_lines, path("outputs", "logs", "common_sample_log.md"), useBytes = TRUE)

message("Common-sample baseline completed.")