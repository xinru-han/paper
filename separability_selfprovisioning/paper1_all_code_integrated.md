# Paper 1 All Code Integrated Package

Generated at: 2026-06-12 21:02:28

This file concatenates all R and Python scripts in `code/`.

- **Econometric pipeline (R):** `run_revised_pipeline.R`, `00_setup.R`, `19`, `01`–`14`, `13`.
- **Manuscript utilities (Python, not econometrics):** `15_write_manuscript_draft.py`, `16_llm_manuscript_revision.py`, `17_finalize_manuscript_after_llm_review.py`.
- **Legacy scripts:** older numbered files such as `08_baseline_separability_tests.R` are retained for audit history but are not part of the revised pipeline.

Each script is preserved verbatim inside a fenced code block.

## 1. Code Inventory

| relative_path | size_kb | n_lines |
|---|---|---|
| code/00_setup.R | 7.8 | 220 |
| code/01_data_issue_cleaning_audit.R | 28.2 | 712 |
| code/01_rebuild_revised_analysis_data.R | 7.1 | 154 |
| code/02_common_sample_baseline.R | 3.2 | 87 |
| code/02_full_variable_descriptive_audit.R | 33.1 | 714 |
| code/03_baseline_coefficients_margins.R | 2.6 | 66 |
| code/03_price_reconstruction_check.R | 9.3 | 265 |
| code/04_category_specific_nsi.R | 3 | 79 |
| code/04_export_reprocessed_analysis_ready_data.R | 8.4 | 228 |
| code/05_hedonic_price_imputation.R | 10.7 | 279 |
| code/05_two_part_model.R | 2.4 | 73 |
| code/06_construct_market_friction_and_external_controls.R | 17 | 402 |
| code/06_price_robustness.R | 4 | 91 |
| code/07_add_household_resource_controls.R | 5.2 | 155 |
| code/07_category_definition_audits.R | 3.9 | 72 |
| code/08_baseline_separability_tests.R | 8.4 | 248 |
| code/08_robustness_checks.R | 7.1 | 175 |
| code/09_appendix_market_friction_interactions.R | 2.8 | 65 |
| code/09_category_specific_tests.R | 10.1 | 295 |
| code/10_appendix_iv_diagnostics.R | 3.9 | 107 |
| code/10_market_friction_interactions.R | 13.7 | 395 |
| code/11_compile_revised_results_report.R | 19.6 | 353 |
| code/11_iv_market_friction_models.R | 16.1 | 456 |
| code/12_placebo_and_robustness_checks.R | 14.1 | 376 |
| code/13_compile_all_integrated_markdowns.R | 8.4 | 234 |
| code/14_editor_revision_analyses.R | 30.9 | 634 |
| code/15_write_manuscript_draft.py | 42.1 | 604 |
| code/16_llm_manuscript_revision.py | 24.3 | 625 |
| code/17_finalize_manuscript_after_llm_review.py | 20.8 | 116 |
| code/18_unit_kg_month_check_and_descriptives.R | 17.5 | 447 |
| code/19_apply_kg_units_drop_outliers_prepare_official_data.R | 19.2 | 459 |
| code/run_revised_pipeline.R | 0.9 | 30 |

## `code/00_setup.R`

- Size: 7.8 KB
- Lines: 220

````r
options(warn = 1)

root <- getwd()
dir.create(file.path(root, "data", "analysis_ready"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "data", "cleaned"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "tables"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "figures"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "model_summaries"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "logs"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "reports"), recursive = TRUE, showWarnings = FALSE)

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
  miss <- is.na(x) | !is.finite(x)
  x[!is.finite(x)] <- NA_real_
  med <- median(x, na.rm = TRUE)
  if (is.na(med)) med <- 0
  x[miss] <- med
  data[[paste0(var, "_imp")]] <- x
  data[[paste0(var, "_missing")]] <- as.integer(miss)
  data
}

prepare_revised_data <- function(data) {
  impute_vars <- c(
    "household_head_age", "household_head_education", "household_head_gender_male",
    "household_assets_count_proxy", "log1p_total_income_w_w99",
    "log1p_agri_business_income_w99", "log1p_annual_expense_total_w99"
  )
  for (v in impute_vars[impute_vars %in% names(data)]) {
    data <- median_impute(data, v)
  }
  if ("food_category" %in% names(data)) data$food_category <- factor(data$food_category)
  if ("data_year" %in% names(data)) data$data_year <- factor(data$data_year)
  if ("provn_std" %in% names(data)) data$provn_std <- factor(data$provn_std)
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

safe_coef_stats <- function(model, vcov_mat, term) {
  coefs <- coef(model)
  ses <- sqrt(diag(vcov_mat))
  if (!term %in% names(coefs) || is.na(coefs[term])) {
    return(c(estimate = NA_real_, std_error_cluster = NA_real_, t_stat = NA_real_, p_value = NA_real_))
  }
  est <- as.numeric(coefs[term])
  se <- as.numeric(ses[term])
  tval <- est / se
  c(
    estimate = est,
    std_error_cluster = se,
    t_stat = tval,
    p_value = 2 * pnorm(abs(tval), lower.tail = FALSE)
  )
}

fit_lm_cluster <- function(data, outcome, rhs_terms, cluster_var = "xzc12_for_merge_final") {
  f <- as.formula(paste(outcome, "~", paste(rhs_terms, collapse = " + ")))
  vars_needed <- unique(c(all.vars(f), cluster_var))
  d <- data[complete.cases(data[, vars_needed, drop = FALSE]), ]
  if (nrow(d) < 100 || length(unique(d[[outcome]])) < 2) {
    return(list(ok = FALSE, formula = f, data = d, model = NULL, vcov = NULL))
  }
  model <- lm(f, data = d)
  vc <- cluster_vcov(model, d[[cluster_var]])
  list(ok = TRUE, formula = f, data = d, model = model, vcov = vc)
}

find_interaction_name <- function(coef_names, term, friction_var) {
  candidates <- c(paste0(term, ":", friction_var), paste0(friction_var, ":", term))
  hit <- candidates[candidates %in% coef_names]
  if (length(hit) == 0) return(NA_character_)
  hit[1]
}

json_escape <- function(x) {
  x <- gsub("\\\\", "\\\\\\\\", x)
  x <- gsub('"', '\\"', x)
  x <- gsub("\n", "\\\\n", x)
  x
}

json_number <- function(x) {
  if (is.na(x) || !is.finite(x)) return("null")
  as.character(signif(x, 8))
}

write_simple_json <- function(rows, file, key = "models") {
  if (is.null(rows) || nrow(rows) == 0) {
    writeLines(c("{", paste0('  "', key, '": []'), "}"), file, useBytes = TRUE)
    return(invisible(NULL))
  }
  lines <- c("{", paste0('  "', key, '": ['))
  for (i in seq_len(nrow(rows))) {
    r <- rows[i, , drop = FALSE]
    parts <- c()
    for (nm in names(r)) {
      val <- r[[nm]][1]
      if (is.numeric(val)) {
        parts <- c(parts, paste0('"', json_escape(nm), '":', json_number(val)))
      } else {
        parts <- c(parts, paste0('"', json_escape(nm), '":"', json_escape(as.character(val)), '"'))
      }
    }
    comma <- if (i < nrow(rows)) "," else ""
    lines <- c(lines, paste0("    {", paste(parts, collapse = ","), "}", comma))
  }
  lines <- c(lines, "  ]", "}")
  writeLines(lines, file, useBytes = TRUE)
}

summarise_numeric <- function(data, vars, module = "") {
  rows <- lapply(vars[vars %in% names(data)], function(v) {
    x <- to_num(data[[v]])
    data.frame(
      module = module,
      variable = v,
      n = sum(!is.na(x)),
      missing = sum(is.na(x)),
      mean = mean(x, na.rm = TRUE),
      sd = sd(x, na.rm = TRUE),
      min = min(x, na.rm = TRUE),
      p25 = quantile(x, 0.25, na.rm = TRUE),
      median = median(x, na.rm = TRUE),
      p75 = quantile(x, 0.75, na.rm = TRUE),
      max = max(x, na.rm = TRUE),
      stringsAsFactors = FALSE
    )
  })
  do.call(rbind, rows)
}

hh_terms_main <- c("household_size_reconstructed", "child_share", "elderly_share", "female_share")
resource_terms_revised <- c(
  "log1p_total_income_w_w99_imp", "log1p_total_income_w_w99_missing",
  "log1p_agri_business_income_w99_imp", "log1p_agri_business_income_w99_missing",
  "log1p_annual_expense_total_w99_imp", "log1p_annual_expense_total_w99_missing",
  "total_sown_area", "agricultural_labor_days", "offfarm_labor_days",
  "household_assets_count_proxy_imp", "household_assets_count_proxy_missing",
  "household_head_age_imp", "household_head_age_missing",
  "household_head_education_imp", "household_head_education_missing",
  "household_head_gender_male_imp", "household_head_gender_male_missing"
)
market_gaez_terms_revised <- c(
  "market_friction_survey", "poi_market_friction_lag1",
  "gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km",
  "factor(provn_std)"
)
price_text_terms_revised <- c(
  "price_hedonic_imputed_w99_yuan_per_jin",
  "risk_salience_z_5yr_sum", "governance_capacity_z_5yr_sum",
  "trust_signal_z_5yr_sum", "attention_z_5yr_sum"
)
category_year_terms_revised <- c("factor(food_category)", "factor(data_year)")

baseline_rhs <- function(spec) {
  if (spec == "M0") return(c(hh_terms_main, category_year_terms_revised))
  if (spec == "M1") return(c(hh_terms_main, resource_terms_revised, category_year_terms_revised))
  if (spec == "M2") return(c(hh_terms_main, resource_terms_revised, market_gaez_terms_revised, category_year_terms_revised))
  if (spec == "M3") return(c(hh_terms_main, resource_terms_revised, market_gaez_terms_revised, price_text_terms_revised, category_year_terms_revised))
  stop("Unknown spec: ", spec)
}

signal_label <- function(p, nsi) {
  if (!is.na(p) && p < 0.01) return("Strong")
  if (!is.na(nsi) && nsi > 1.25) return("Strong")
  if (!is.na(p) && p < 0.05) return("Moderate")
  if (!is.na(nsi) && nsi >= 0.9 && nsi <= 1.1) return("Moderate")
  "Weak"
}

message("Revised setup loaded.")
````

## `code/01_data_issue_cleaning_audit.R`

- Size: 28.2 KB
- Lines: 712

````r
options(warn = 1)

root <- getwd()

dir.create(file.path(root, "data", "cleaned"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "logs"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "tables"), recursive = TRUE, showWarnings = FALSE)

path <- function(...) file.path(root, ...)

read_csv <- function(file, colClasses = NULL) {
  args <- list(
    file = file,
    stringsAsFactors = FALSE,
    check.names = FALSE,
    fileEncoding = "UTF-8"
  )
  if (!is.null(colClasses)) args$colClasses <- colClasses
  do.call(read.csv, args)
}

write_csv <- function(x, file) {
  write.csv(x, file, row.names = FALSE, fileEncoding = "UTF-8")
}

trim_text <- function(x) {
  x <- as.character(x)
  x <- gsub("\ufeff", "", x)
  x <- gsub("[[:space:]\u3000]+", "", x)
  x[x == ""] <- NA_character_
  x
}

to_num <- function(x) {
  if (is.numeric(x)) return(x)
  x <- trim_text(x)
  suppressWarnings(as.numeric(x))
}

is_missing_code <- function(x) {
  !is.na(x) & x %in% c(-999, -998, -997, -99, -98, -97, -9, -8, -7, -1)
}

clean_positive_price <- function(x) {
  x <- to_num(x)
  x[x <= 0 | is_missing_code(x)] <- NA_real_
  x
}

winsor_upper <- function(x, p = 0.99) {
  x <- to_num(x)
  if (all(is.na(x))) return(x)
  cutoff <- as.numeric(quantile(x, p, na.rm = TRUE, names = FALSE))
  pmin(x, cutoff)
}

norm_prov <- function(x) {
  x <- trim_text(x)
  x[x == "湖北"] <- "湖北省"
  x[x == "陕西"] <- "陕西省"
  x
}

strip_prefix_if_suffix <- function(raw, targets) {
  out <- rep(NA_character_, length(raw))
  targets <- targets[!is.na(targets) & targets != ""]
  targets <- targets[order(nchar(targets), decreasing = TRUE)]
  for (i in seq_along(raw)) {
    r <- raw[i]
    if (is.na(r) || r == "") next
    hit <- targets[endsWith(r, targets)]
    if (length(hit) > 0) out[i] <- hit[1]
  }
  out
}

normalize_county <- function(county, province = NULL, xzc12 = NULL, target_counties = NULL) {
  raw <- trim_text(county)
  prov <- norm_prov(province)
  out <- raw

  # First use target county suffixes when available. This handles forms like
  # "庆阳市环县", "吉林市永吉县", and "泸州市泸县" without hard-coding every prefix.
  if (!is.null(target_counties)) {
    suffix_hit <- strip_prefix_if_suffix(raw, target_counties)
    out[!is.na(suffix_hit)] <- suffix_hit[!is.na(suffix_hit)]
  }

  # Manual aliases observed in the current files.
  alias_from <- c(
    "永吉市", "敦化县",
    "庄浪", "秦安",
    "福清", "松溪",
    "维西", "维西县",
    "巴山南江县", "泸州",
    "漳州市福安县"
  )
  alias_to <- c(
    "永吉县", "敦化市",
    "庄浪县", "秦安县",
    "福清市", "松溪县",
    "维西傈僳族自治县", "维西傈僳族自治县",
    "南江县", "泸县",
    "福安县"
  )
  for (k in seq_along(alias_from)) {
    out[!is.na(out) & out == alias_from[k]] <- alias_to[k]
  }

  # Code-informed safeguards for ambiguous short names.
  if (!is.null(xzc12)) {
    code6 <- substr(as.character(xzc12), 1, 6)
    out[code6 == "510521" & !is.na(out) & out %in% c("泸州", "泸州市")] <- "泸县"
    out[code6 == "532528" & !is.na(out) & out %in% c("红河哈尼族彝族自治州元阳县")] <- "元阳县"
  }

  out
}

haversine_km <- function(lon1, lat1, lon2, lat2) {
  rad <- pi / 180
  lon1 <- lon1 * rad; lat1 <- lat1 * rad
  lon2 <- lon2 * rad; lat2 <- lat2 * rad
  dlon <- lon2 - lon1
  dlat <- lat2 - lat1
  a <- sin(dlat / 2)^2 + cos(lat1) * cos(lat2) * sin(dlon / 2)^2
  6371 * 2 * atan2(sqrt(a), sqrt(1 - a))
}

summ_num <- function(x) {
  x <- to_num(x)
  ok <- !is.na(x)
  if (!any(ok)) {
    return(c(
      n = length(x), missing = sum(!ok), zero = 0, negative = 0,
      p1 = NA, median = NA, mean = NA, p99 = NA, max = NA
    ))
  }
  c(
    n = length(x),
    missing = sum(!ok),
    zero = sum(x == 0, na.rm = TRUE),
    negative = sum(x < 0, na.rm = TRUE),
    p1 = as.numeric(quantile(x, 0.01, na.rm = TRUE, names = FALSE)),
    median = as.numeric(median(x, na.rm = TRUE)),
    mean = as.numeric(mean(x, na.rm = TRUE)),
    p99 = as.numeric(quantile(x, 0.99, na.rm = TRUE, names = FALSE)),
    max = as.numeric(max(x, na.rm = TRUE))
  )
}

first_nonmissing <- function(x) {
  x <- as.character(x)
  x <- x[!is.na(x) & x != ""]
  if (length(x) == 0) NA_character_ else x[1]
}

hh <- read_csv(
  path("raw_data", "户表数据_已清洗.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character", county = "character", town = "character", vil = "character")
)
vl <- read_csv(
  path("raw_data", "村表数据_已清洗.csv"),
  colClasses = c(xzcCode = "character", xzcCode_clean = "character", x02 = "character", x03 = "character", x04 = "character", xz00 = "character")
)
poi <- read_csv(
  path("raw_data", "poi", "village_pois_merged_dedup.csv"),
  colClasses = c(xzc12 = "character")
)
hh_lab <- read_csv(path("raw_data", "户表数据_已清洗_变量标签.csv"))
vl_lab <- read_csv(path("raw_data", "村表数据_已清洗_变量标签.csv"))
food_safety <- read_csv(path("raw_data", "food_safety", "paper_8provinces_all_counties_5year_complete.csv"))

target_counties <- unique(trim_text(food_safety$county))

hh$provn_std <- norm_prov(hh$provn)
hh$countyn_std <- normalize_county(hh$countyn, hh$provn, hh$xzc12, target_counties)
hh$townn_std <- trim_text(hh$townn)
hh$viln_std <- trim_text(hh$viln)

vl$x02n_std <- norm_prov(vl$x02n)
vl$x03n_std <- normalize_county(vl$x03n, vl$x02n, vl$xzcCode_clean, target_counties)
vl$x04n_std <- trim_text(vl$x04n)
vl$xz00n_std <- trim_text(vl$xz00n)

food_safety$province_std <- norm_prov(food_safety$province)
food_safety$county_std <- trim_text(food_safety$county)

## County crosswalk ---------------------------------------------------------

hh_counties <- aggregate(
  nhCode ~ provn + countyn + provn_std + countyn_std,
  data = hh,
  FUN = length
)
names(hh_counties)[names(hh_counties) == "nhCode"] <- "n_households"
hh_counties$direct_match_food_safety <- paste(hh_counties$provn, hh_counties$countyn) %in%
  paste(food_safety$province, food_safety$county)
hh_counties$standardized_match_food_safety <- paste(hh_counties$provn_std, hh_counties$countyn_std) %in%
  paste(food_safety$province_std, food_safety$county_std)

write_csv(hh_counties, path("data", "cleaned", "county_name_crosswalk.csv"))

county_audit <- data.frame(
  metric = c(
    "unique_household_counties",
    "direct_county_matches",
    "standardized_county_matches",
    "households_direct_match",
    "households_standardized_match"
  ),
  value = c(
    nrow(hh_counties),
    sum(hh_counties$direct_match_food_safety),
    sum(hh_counties$standardized_match_food_safety),
    sum(paste(hh$provn, hh$countyn) %in% paste(food_safety$province, food_safety$county)),
    sum(paste(hh$provn_std, hh$countyn_std) %in% paste(food_safety$province_std, food_safety$county_std))
  )
)
write_csv(county_audit, path("outputs", "tables", "county_match_audit.csv"))

## Village merge crosswalk --------------------------------------------------

hh_villages_raw <- unique(hh[, c(
  "provn_std", "countyn_std", "townn_std", "viln_std", "xzc12", "data_year", "vilLat", "vilLon"
)])
hh_villages <- aggregate(
  cbind(provn_std, countyn_std, townn_std, viln_std, vilLat, vilLon) ~ xzc12 + data_year,
  data = hh_villages_raw,
  FUN = first_nonmissing,
  na.action = na.pass
)
hh_villages$merge_key <- paste(hh_villages$xzc12, hh_villages$data_year)
vl$merge_key <- paste(vl$xzcCode_clean, vl$data_year)
hh_villages$exact_match <- hh_villages$merge_key %in% vl$merge_key
hh_villages$match_status <- ifelse(hh_villages$exact_match, "exact_code_year", "unmatched")
hh_villages$xzc12_for_merge <- hh_villages$xzc12
hh_villages$fallback_reason <- NA_character_
hh_villages$fallback_distance_km <- NA_real_

un_idx <- which(!hh_villages$exact_match)
fallback_rows <- list()
if (length(un_idx) > 0) {
  for (idx in un_idx) {
    hv <- hh_villages[idx, ]
    same_year <- vl[vl$data_year == hv$data_year, ]
    town_match <- rep(FALSE, nrow(same_year))
    if (!is.na(hv$townn_std) && nrow(same_year) > 0) {
      town_match <- vapply(same_year$x04n_std, function(tn) {
        !is.na(tn) && (
          tn == hv$townn_std ||
            grepl(tn, hv$townn_std, fixed = TRUE) ||
            grepl(hv$townn_std, tn, fixed = TRUE)
        )
      }, logical(1))
    }
    cand_name <- same_year[
      same_year$x02n_std == hv$provn_std &
        same_year$xz00n_std == hv$viln_std &
        town_match,
    ]
    if (nrow(cand_name) == 1) {
      hh_villages$match_status[idx] <- "fallback_unique_village_town_name"
      hh_villages$xzc12_for_merge[idx] <- cand_name$xzcCode_clean[1]
      hh_villages$fallback_reason[idx] <- paste(
        cand_name$x03n[1], cand_name$x04n[1], cand_name$xz00n[1],
        sep = "/"
      )
    }

    cand_geo <- same_year[
      same_year$x02n_std == hv$provn_std &
        same_year$x03n_std == hv$countyn_std &
        !is.na(to_num(same_year$vilLat)) &
        !is.na(to_num(same_year$vilLon)) &
        !is.na(to_num(hv$vilLat)) &
        !is.na(to_num(hv$vilLon)),
    ]
    if (nrow(cand_geo) > 0) {
      d <- haversine_km(to_num(hv$vilLon), to_num(hv$vilLat), to_num(cand_geo$vilLon), to_num(cand_geo$vilLat))
      best <- cand_geo[which.min(d), ]
      fallback_rows[[length(fallback_rows) + 1]] <- data.frame(
        original_xzc12 = hv$xzc12,
        data_year = hv$data_year,
        hh_provn = hv$provn_std,
        hh_countyn = hv$countyn_std,
        hh_townn = hv$townn_std,
        hh_viln = hv$viln_std,
        candidate_xzc12 = best$xzcCode_clean,
        candidate_countyn = best$x03n,
        candidate_townn = best$x04n,
        candidate_viln = best$xz00n,
        distance_km = min(d, na.rm = TRUE),
        stringsAsFactors = FALSE
      )
      if (hh_villages$match_status[idx] == "unmatched" && min(d, na.rm = TRUE) <= 2) {
        hh_villages$fallback_reason[idx] <- paste0(
          "nearest candidate only; not auto-accepted: ",
          best$x03n, "/", best$x04n, "/", best$xz00n
        )
        hh_villages$fallback_distance_km[idx] <- min(d, na.rm = TRUE)
      }
    }
  }
}

fallback_candidates <- if (length(fallback_rows) == 0) {
  data.frame()
} else {
  do.call(rbind, fallback_rows)
}

write_csv(hh_villages, path("data", "cleaned", "village_merge_crosswalk.csv"))
write_csv(fallback_candidates, path("outputs", "tables", "village_unmatched_fallback_candidates.csv"))

hh_geo <- merge(
  hh[, c("nhCode", "xzc12", "data_year", "provn_std", "countyn_std", "townn_std", "viln_std")],
  hh_villages[, c("xzc12", "data_year", "xzc12_for_merge", "match_status", "fallback_reason", "fallback_distance_km")],
  by = c("xzc12", "data_year"),
  all.x = TRUE
)
write_csv(hh_geo, path("data", "cleaned", "household_geography_clean.csv"))

## POI 5km counts, missing villages filled as zero --------------------------

analysis_provinces_2022 <- c("山东省", "吉林省", "陕西省", "甘肃省")
analysis_provinces_2023 <- c("云南省", "四川省", "湖北省", "福建省")
all_categories <- sort(unique(trim_text(poi$category)))

survey_villages <- unique(hh_villages[, c("xzc12", "provn_std", "countyn_std", "townn_std", "viln_std", "data_year")])
survey_villages$poi_year_assigned <- ifelse(
  survey_villages$provn_std %in% analysis_provinces_2022, 2022,
  ifelse(survey_villages$provn_std %in% analysis_provinces_2023, 2023, NA)
)

poi$category_std <- trim_text(poi$category)
poi$distance_m_num <- to_num(poi$distance_m)
poi_counts <- aggregate(
  poi_id ~ xzc12 + category_std,
  data = poi,
  FUN = length
)
names(poi_counts)[names(poi_counts) == "poi_id"] <- "n"

poi_wide <- survey_villages
for (cat in all_categories) {
  tmp <- poi_counts[poi_counts$category_std == cat, c("xzc12", "n")]
  names(tmp)[2] <- paste0("poi_", cat, "_5km")
  poi_wide <- merge(poi_wide, tmp, by = "xzc12", all.x = TRUE)
}
poi_count_cols <- grep("^poi_.*_5km$", names(poi_wide), value = TRUE)
for (v in poi_count_cols) poi_wide[[v]][is.na(poi_wide[[v]])] <- 0

nearest_by_cat <- aggregate(
  distance_m_num ~ xzc12 + category_std,
  data = poi[!is.na(poi$distance_m_num), ],
  FUN = min
)
for (cat in all_categories) {
  tmp <- nearest_by_cat[nearest_by_cat$category_std == cat, c("xzc12", "distance_m_num")]
  names(tmp)[2] <- paste0("poi_nearest_", cat, "_m")
  poi_wide <- merge(poi_wide, tmp, by = "xzc12", all.x = TRUE)
}

poi_wide$poi_market_capacity_5km <- rowSums(poi_wide[, poi_count_cols, drop = FALSE], na.rm = TRUE)
fresh_cols <- intersect(
  c("poi_wet_market_5km", "poi_fresh_food_5km", "poi_meat_aquatic_5km", "poi_supermarket_5km", "poi_grocery_5km"),
  names(poi_wide)
)
poi_wide$poi_fresh_market_capacity_5km <- rowSums(poi_wide[, fresh_cols, drop = FALSE], na.rm = TRUE)
poi_wide$poi_has_any_5km <- as.integer(poi_wide$poi_market_capacity_5km > 0)

write_csv(poi_wide, path("data", "cleaned", "poi_5km_village_counts_filled.csv"))

poi_audit <- aggregate(
  xzc12 ~ provn_std + data_year + poi_year_assigned + poi_has_any_5km,
  data = poi_wide,
  FUN = length
)
names(poi_audit)[names(poi_audit) == "xzc12"] <- "n_villages"
write_csv(poi_audit, path("outputs", "tables", "poi_coverage_audit.csv"))

## Market survey distance vs POI availability -------------------------------

market_vars <- c("fe03_01", "fe03_02", "fe03_03", "fe03_04")
v_market <- vl[, c("xzcCode_clean", "data_year", market_vars)]
names(v_market)[1] <- "xzc12"
market_poi <- merge(survey_villages[, c("xzc12", "data_year", "provn_std")], v_market, by = c("xzc12", "data_year"), all.x = TRUE)
market_poi <- merge(market_poi, poi_wide[, c("xzc12", "poi_market_capacity_5km", "poi_fresh_market_capacity_5km", "poi_has_any_5km")], by = "xzc12", all.x = TRUE)
market_dist_audit <- data.frame(
  variable = market_vars,
  n_villages = nrow(market_poi),
  n_missing_survey_distance = sapply(market_vars, function(v) sum(is.na(to_num(market_poi[[v]])))),
  n_missing_survey_distance_with_any_poi = sapply(market_vars, function(v) sum(is.na(to_num(market_poi[[v]])) & market_poi$poi_has_any_5km == 1, na.rm = TRUE)),
  n_missing_survey_distance_with_no_poi = sapply(market_vars, function(v) sum(is.na(to_num(market_poi[[v]])) & market_poi$poi_has_any_5km == 0, na.rm = TRUE))
)
market_dist_audit$missing_share <- market_dist_audit$n_missing_survey_distance / market_dist_audit$n_villages
write_csv(market_dist_audit, path("outputs", "tables", "market_distance_missing_vs_poi.csv"))

## Area cleaning ------------------------------------------------------------

area_vars <- hh_lab$var[grepl("种植面积（亩）$", hh_lab$label)]
area_vars <- intersect(area_vars, names(hh))
area <- as.data.frame(lapply(hh[, area_vars, drop = FALSE], to_num), check.names = FALSE)
area_raw <- area
area_component_upper_bound <- 500
for (v in area_vars) {
  x <- area[[v]]
  x[x < 0 | is_missing_code(x)] <- NA
  area[[v]] <- x
}

area_pre_component_cap <- area
area_component_outlier <- as.data.frame(lapply(area, function(x) !is.na(x) & x > area_component_upper_bound), check.names = FALSE)
for (v in area_vars) {
  x <- area[[v]]
  x[x > area_component_upper_bound] <- NA
  area[[v]] <- x
}

total_sown_area_raw <- rowSums(area_raw, na.rm = TRUE)
total_sown_area_nonnegative <- rowSums(area_pre_component_cap, na.rm = TRUE)
total_sown_area_component_cap500 <- rowSums(area, na.rm = TRUE)
p99_nonnegative <- as.numeric(quantile(total_sown_area_nonnegative, 0.99, na.rm = TRUE, names = FALSE))
p995_nonnegative <- as.numeric(quantile(total_sown_area_nonnegative, 0.995, na.rm = TRUE, names = FALSE))
p99_after_component_cap <- as.numeric(quantile(total_sown_area_component_cap500, 0.99, na.rm = TRUE, names = FALSE))
p995_after_component_cap <- as.numeric(quantile(total_sown_area_component_cap500, 0.995, na.rm = TRUE, names = FALSE))
total_sown_area_clean <- pmin(total_sown_area_component_cap500, p99_after_component_cap)
area_component_outlier_n <- rowSums(area_component_outlier, na.rm = TRUE)
area_total_winsorized_flag <- as.integer(total_sown_area_component_cap500 > p99_after_component_cap)

area_clean <- data.frame(
  nhCode = hh$nhCode,
  data_year = hh$data_year,
  provn = hh$provn,
  countyn = hh$countyn,
  xzc12 = hh$xzc12,
  total_sown_area_raw = total_sown_area_raw,
  total_sown_area_nonnegative = total_sown_area_nonnegative,
  total_sown_area_component_cap500 = total_sown_area_component_cap500,
  total_sown_area = total_sown_area_clean,
  total_sown_area_clean = total_sown_area_clean,
  total_sown_area_w99 = total_sown_area_clean,
  total_sown_area_p99_cutoff = p99_after_component_cap,
  total_sown_area_p995_cutoff = p995_after_component_cap,
  total_sown_area_nonnegative_p99_cutoff = p99_nonnegative,
  total_sown_area_nonnegative_p995_cutoff = p995_nonnegative,
  area_component_upper_bound = area_component_upper_bound,
  area_component_outlier_n = area_component_outlier_n,
  area_any_component_outlier = as.integer(area_component_outlier_n > 0),
  area_total_winsorized_flag = area_total_winsorized_flag,
  stringsAsFactors = FALSE
)
write_csv(area_clean, path("data", "cleaned", "household_total_sown_area.csv"))

area_anomaly <- data.frame(
  metric = c(
    "n_area_vars",
    "negative_or_missing_code_cells",
    "area_component_upper_bound",
    "area_component_outlier_cells",
    "households_with_area_component_outlier",
    "households_negative_raw_total",
    "households_total_area_nonnegative_gt_p99",
    "households_total_area_nonnegative_gt_p995",
    "p99_total_sown_area_nonnegative",
    "p995_total_sown_area_nonnegative",
    "p99_total_sown_area_after_component_cap",
    "p995_total_sown_area_after_component_cap",
    "households_total_area_winsorized_after_component_cap",
    "max_total_sown_area_clean"
  ),
  value = c(
    length(area_vars),
    sum(as.matrix(area_raw) < 0 | is_missing_code(as.matrix(area_raw)), na.rm = TRUE),
    area_component_upper_bound,
    sum(as.matrix(area_component_outlier), na.rm = TRUE),
    sum(area_component_outlier_n > 0, na.rm = TRUE),
    sum(total_sown_area_raw < 0, na.rm = TRUE),
    sum(total_sown_area_nonnegative > p99_nonnegative, na.rm = TRUE),
    sum(total_sown_area_nonnegative > p995_nonnegative, na.rm = TRUE),
    p99_nonnegative,
    p995_nonnegative,
    p99_after_component_cap,
    p995_after_component_cap,
    sum(area_total_winsorized_flag == 1, na.rm = TRUE),
    max(total_sown_area_clean, na.rm = TRUE)
  )
)
write_csv(area_anomaly, path("outputs", "tables", "area_anomaly_audit.csv"))

## Price diagnostics --------------------------------------------------------

analysis_cats <- c("zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo")
cat_labels <- c(
  zhushi = "主食",
  doulei = "豆类",
  roulei = "肉类和水产品及加工品",
  danlei = "蛋类",
  nailei = "奶类",
  youzhi = "油脂",
  shucai = "蔬菜",
  shuiguo = "水果"
)

hh_price_rows <- lapply(analysis_cats, function(cat) {
  v <- paste0(cat, "_price_wavg_yuan_per_jin")
  x <- if (v %in% names(hh)) to_num(hh[[v]]) else rep(NA_real_, nrow(hh))
  x_positive <- clean_positive_price(x)
  x_w99 <- winsor_upper(x_positive, 0.99)
  s_raw <- summ_num(x)
  s_positive <- summ_num(x_positive)
  s_w99 <- summ_num(x_w99)
  data.frame(
    food_category = cat,
    label = unname(cat_labels[cat]),
    variable = v,
    price_unit_from_label = "元/斤",
    raw_missing = unname(s_raw["missing"]),
    raw_zero_or_nonpositive = sum(!is.na(x) & x <= 0),
    raw_missing_or_nonpositive_share = mean(is.na(x) | x <= 0),
    positive_n = sum(!is.na(x_positive)),
    positive_missing_share = mean(is.na(x_positive)),
    positive_mean = unname(s_positive["mean"]),
    positive_median = unname(s_positive["median"]),
    positive_p99 = unname(s_positive["p99"]),
    positive_max = unname(s_positive["max"]),
    winsor_p99_mean = unname(s_w99["mean"]),
    winsor_p99_median = unname(s_w99["median"]),
    winsor_p99_max = unname(s_w99["max"]),
    outlier_gt_positive_p99 = sum(x_positive > s_positive["p99"], na.rm = TRUE),
    stringsAsFactors = FALSE
  )
})
hh_price_audit <- do.call(rbind, hh_price_rows)
write_csv(hh_price_audit, path("outputs", "tables", "price_household_category_audit.csv"))

hh_price_extreme_rows <- list()
for (cat in analysis_cats) {
  v <- paste0(cat, "_price_wavg_yuan_per_jin")
  if (!v %in% names(hh)) next
  x <- clean_positive_price(hh[[v]])
  px <- as.numeric(quantile(x, 0.99, na.rm = TRUE, names = FALSE))
  idx <- which(!is.na(x) & x > px)
  if (length(idx) > 0) {
    hh_price_extreme_rows[[length(hh_price_extreme_rows) + 1]] <- data.frame(
      food_category = cat,
      label = unname(cat_labels[cat]),
      variable = v,
      p99_positive = px,
      nhCode = hh$nhCode[idx],
      data_year = hh$data_year[idx],
      provn = hh$provn[idx],
      countyn = hh$countyn[idx],
      xzc12 = hh$xzc12[idx],
      price = x[idx],
      stringsAsFactors = FALSE
    )
  }
}
hh_price_extremes <- if (length(hh_price_extreme_rows) == 0) data.frame() else do.call(rbind, hh_price_extreme_rows)
write_csv(hh_price_extremes, path("outputs", "tables", "price_household_extreme_values.csv"))

price_label <- vl_lab
price_label$is_price <- grepl("单价|售价", price_label$label) &
  !grepl("名称|总数|数量|距离|分量|品种|对应", price_label$label)
price_label <- price_label[price_label$is_price & price_label$var %in% names(vl), ]

category_regex <- list(
  zhushi = "主食|大米|面粉|玉米|土豆|红薯|米线|米粉|面食|米饭|馒头",
  doulei = "豆类|豆制品|豆腐|大豆|杂豆",
  roulei = "肉类|猪|牛|羊|鸡|鸭|鹅|鱼|虾|蟹|贝|水产品|红烧肉|清蒸鱼|油爆大虾",
  danlei = "蛋|水蒸蛋",
  nailei = "奶|牛奶|羊奶|酸奶|奶粉",
  youzhi = "油脂|大豆油|菜籽油|花生油|植物油|动物油|调和油|色拉油",
  shucai = "蔬菜|时蔬|鲜豆|茄果|花菜|根茎|叶菜|菌藻|咸菜|干菜",
  shuiguo = "水果|苹果|瓜果|柑橘|浆果|核果|干果|果脯"
)

village_price <- unique(vl[, c("xzcCode_clean", "data_year", "x02n", "x03n", "x04n", "xz00n")])
names(village_price)[1] <- "xzc12"
for (cat in analysis_cats) {
  vars <- price_label$var[grepl(category_regex[[cat]], price_label$label)]
  vars <- intersect(vars, names(vl))
  if (length(vars) == 0) {
    village_price[[paste0("village_price_", cat, "_median")]] <- NA_real_
    next
  }
  mat <- as.data.frame(lapply(vl[, vars, drop = FALSE], to_num), check.names = FALSE)
  for (v in names(mat)) {
    x <- mat[[v]]
    x[x <= 0 | is_missing_code(x)] <- NA
    mat[[v]] <- x
  }
  village_price[[paste0("village_price_", cat, "_median")]] <- apply(mat, 1, function(row) {
    if (all(is.na(row))) NA_real_ else median(row, na.rm = TRUE)
  })
}
write_csv(village_price, path("data", "cleaned", "village_category_price_candidates.csv"))

village_price_audit <- lapply(analysis_cats, function(cat) {
  v <- paste0("village_price_", cat, "_median")
  x <- village_price[[v]]
  s <- summ_num(x)
  data.frame(
    food_category = cat,
    label = unname(cat_labels[cat]),
    variable = v,
    n_candidate_price_vars = sum(grepl(category_regex[[cat]], price_label$label)),
    t(s),
    missing_share = mean(is.na(x)),
    stringsAsFactors = FALSE
  )
})
village_price_audit <- do.call(rbind, village_price_audit)
write_csv(village_price_audit, path("outputs", "tables", "price_village_category_candidate_audit.csv"))

village_price_extreme_rows <- list()
for (cat in analysis_cats) {
  v <- paste0("village_price_", cat, "_median")
  x <- village_price[[v]]
  px <- as.numeric(quantile(x[x > 0], 0.99, na.rm = TRUE, names = FALSE))
  idx <- which(!is.na(x) & x > 0 & x > px)
  if (length(idx) > 0) {
    village_price_extreme_rows[[length(village_price_extreme_rows) + 1]] <- data.frame(
      food_category = cat,
      label = unname(cat_labels[cat]),
      variable = v,
      p99_positive = px,
      xzc12 = village_price$xzc12[idx],
      data_year = village_price$data_year[idx],
      provn = village_price$x02n[idx],
      countyn = village_price$x03n[idx],
      townn = village_price$x04n[idx],
      viln = village_price$xz00n[idx],
      village_price = x[idx],
      stringsAsFactors = FALSE
    )
  }
}
village_price_extremes <- if (length(village_price_extreme_rows) == 0) data.frame() else do.call(rbind, village_price_extreme_rows)
write_csv(village_price_extremes, path("outputs", "tables", "price_village_extreme_values.csv"))

## Logs ---------------------------------------------------------------------

log_lines <- c(
  "# Data Issue Cleaning Audit",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Rules Applied",
  "",
  "- County names were standardized using known county names from the county text file, suffix matching, and observed aliases.",
  "- Village merge uses exact `xzc12 + data_year` first. A fallback is auto-accepted only for a unique village-name plus town-name match.",
  "- POI villages without any 5km POI detail rows are filled with zero counts. Nearest-distance POI variables remain missing when no distance is observed.",
  "- Area values below zero, including `-99` and `-1`, are treated as missing. Crop-specific area values above 500 mu are set to missing before household totals are summed, and the resulting total is winsorized at P99 for the analysis variable.",
  "- Household category prices are audited after setting nonpositive prices to missing; P99-winsorized positive-price summaries are reported for diagnostics.",
  "- Village price candidates are category-level medians across available village price variables after removing nonpositive and missing-code values.",
  "",
  "## Key Counts",
  "",
  paste0("- Household rows: ", nrow(hh)),
  paste0("- Village rows: ", nrow(vl)),
  paste0("- County text rows: ", nrow(food_safety)),
  paste0("- Unique household county forms: ", nrow(hh_counties)),
  paste0("- Standardized county forms matched to text indicators: ", sum(hh_counties$standardized_match_food_safety), "/", nrow(hh_counties)),
  paste0("- Households matched to text indicators after standardization: ", county_audit$value[county_audit$metric == "households_standardized_match"], "/", nrow(hh)),
  paste0("- Survey villages with any 5km POI: ", sum(poi_wide$poi_has_any_5km == 1), "/", nrow(poi_wide)),
  paste0("- Survey villages with zero filled POI counts: ", sum(poi_wide$poi_has_any_5km == 0), "/", nrow(poi_wide)),
  paste0("- Exact village-year matches: ", sum(hh_villages$match_status == "exact_code_year"), "/", nrow(hh_villages)),
  paste0("- Fallback village-name/town-name matches auto-accepted: ", sum(hh_villages$match_status == "fallback_unique_village_town_name"), "/", nrow(hh_villages)),
  paste0("- Still unmatched village-year records: ", sum(hh_villages$match_status == "unmatched"), "/", nrow(hh_villages)),
  paste0("- Area variables used for total_sown_area: ", length(area_vars)),
  paste0("- Total sown area p99 cutoff after component cap: ", round(p99_after_component_cap, 3), " mu"),
  "",
  "## Price Handling Recommendation",
  "",
  "For future models, use the household category price only after deciding how to handle zeros and category-level outliers. If price controls are needed, a conservative hierarchy is:",
  "",
  "1. household category price if positive and within agreed category-specific bounds;",
  "2. village category median from village price modules;",
  "3. town-year category median;",
  "4. county-year category median;",
  "5. province-year category median.",
  "",
  "Keep an imputation-source flag for every imputed price. Price variables are not modified in this script.",
  "",
  "## Market Distance Recommendation",
  "",
  "POI can substitute for missing survey distance only as an alternative market-access measure, preferably through POI capacity and nearest-POI variables with a no-POI indicator. Do not overwrite village survey distances silently; estimate survey-friction and POI-friction versions separately.",
  "",
  "## Output Files",
  "",
  "- `data/cleaned/county_name_crosswalk.csv`",
  "- `data/cleaned/village_merge_crosswalk.csv`",
  "- `data/cleaned/household_geography_clean.csv`",
  "- `data/cleaned/poi_5km_village_counts_filled.csv`",
  "- `data/cleaned/household_total_sown_area.csv`",
  "- `data/cleaned/village_category_price_candidates.csv`",
  "- `outputs/tables/county_match_audit.csv`",
  "- `outputs/tables/village_unmatched_fallback_candidates.csv`",
  "- `outputs/tables/poi_coverage_audit.csv`",
  "- `outputs/tables/market_distance_missing_vs_poi.csv`",
  "- `outputs/tables/area_anomaly_audit.csv`",
  "- `outputs/tables/price_household_category_audit.csv`",
  "- `outputs/tables/price_household_extreme_values.csv`",
  "- `outputs/tables/price_village_category_candidate_audit.csv`",
  "- `outputs/tables/price_village_extreme_values.csv`"
)
writeLines(log_lines, path("outputs", "logs", "data_issue_cleaning_audit.md"), useBytes = TRUE)

cat("Data issue cleaning/audit completed.\n")
````

## `code/01_rebuild_revised_analysis_data.R`

- Size: 7.1 KB
- Lines: 154

````r
source("code/00_setup.R")

input_file <- path("data", "analysis_ready", "paper1_reprocessed_analysis_ready_long.csv")
if (!file.exists(input_file)) {
  input_file <- path("data", "cleaned", "paper1_household_category_long.csv")
}

data <- read_csv(
  input_file,
  colClasses = c(nhCode = "character", xzc12 = "character", xzc12_for_merge_final = "character")
)

required_categories <- c("zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo")
data <- data[data$food_category %in% required_categories, ]
data <- prepare_revised_data(data)

revised_file <- path("data", "analysis_ready", "paper1_revised_analysis_ready_long.csv")
write_csv(data, revised_file)

sample_summary <- data.frame(
  item = c(
    "rows", "households", "food_categories", "villages_clusters",
    "provinces", "counties", "duplicate_household_category_keys"
  ),
  value = c(
    nrow(data),
    length(unique(data$nhCode)),
    length(unique(data$food_category)),
    length(unique(data$xzc12_for_merge_final)),
    length(unique(data$provn_std)),
    length(unique(data$countyn_std)),
    sum(duplicated(paste(data$nhCode, data$food_category)))
  ),
  stringsAsFactors = FALSE
)

by_year <- as.data.frame(table(data$data_year), stringsAsFactors = FALSE)
names(by_year) <- c("data_year", "n_rows")
by_cat <- as.data.frame(table(data$food_category), stringsAsFactors = FALSE)
names(by_cat) <- c("food_category", "n_rows")
by_cat <- merge(
  by_cat,
  unique(data[, c("food_category", "food_category_label")]),
  by = "food_category",
  all.x = TRUE,
  sort = FALSE
)

core_vars <- c(
  "production_participation", "log_selfprod_amount", "ihs_selfprod_amount", "self_suff_rate",
  "household_size_reconstructed", "child_share", "elderly_share", "female_share",
  "market_friction_survey", "poi_market_friction_lag1", "combined_market_friction",
  "price_hedonic_imputed_w99_yuan_per_jin", "price_preferred_household_recalc_w99_yuan_per_jin",
  "village_price_category_median", "gaez_overall_si_10km", "gaez_staple_si_10km",
  "gaez_soil_terrain_constraint_10km", "risk_salience_z_5yr_sum",
  "governance_capacity_z_5yr_sum", "trust_signal_z_5yr_sum", "attention_z_5yr_sum"
)
missingness <- data.frame(
  module = c(
    rep("outcome", 4), rep("household_composition", 4), rep("market", 3),
    rep("price", 3), rep("gaez", 3), rep("text", 4)
  )[seq_along(core_vars)],
  variable = core_vars,
  n_rows = nrow(data),
  n_missing = sapply(core_vars, function(v) if (v %in% names(data)) sum(is.na(data[[v]])) else NA_integer_),
  missing_share = sapply(core_vars, function(v) if (v %in% names(data)) mean(is.na(data[[v]])) else NA_real_),
  stringsAsFactors = FALSE
)

category_summary <- aggregate(
  cbind(production_participation, cons_monthly_jin, selfprod_monthly_total, self_suff_rate) ~ food_category + food_category_label,
  data = data,
  FUN = function(x) mean(x, na.rm = TRUE)
)
names(category_summary)[names(category_summary) == "production_participation"] <- "participation_rate"
names(category_summary)[names(category_summary) == "cons_monthly_jin"] <- "mean_cons_monthly_jin"
names(category_summary)[names(category_summary) == "selfprod_monthly_total"] <- "mean_selfprod_monthly_total"
names(category_summary)[names(category_summary) == "self_suff_rate"] <- "mean_self_suff_rate"

desc_vars <- c(
  "production_participation", "log_selfprod_amount", "ihs_selfprod_amount", "self_suff_rate",
  hh_terms_main,
  "dependency_ratio", "num_children", "num_elderly", "num_adult_male", "num_adult_female",
  "log1p_total_income_w_w99", "log1p_agri_business_income_w99", "log1p_annual_expense_total_w99",
  "total_sown_area", "agricultural_labor_days", "offfarm_labor_days",
  "market_friction_survey", "poi_market_friction_lag1", "combined_market_friction",
  "price_hedonic_imputed_w99_yuan_per_jin"
)
desc <- summarise_numeric(data, desc_vars, "revised_analysis")

write_csv(sample_summary, path("outputs", "tables", "table1_sample_summary_revised.csv"))
write_csv(by_year, path("outputs", "tables", "table1_observations_by_year_revised.csv"))
write_csv(by_cat, path("outputs", "tables", "table1_observations_by_category_revised.csv"))
write_csv(missingness, path("outputs", "tables", "table1_missingness_revised.csv"))
write_csv(category_summary, path("outputs", "tables", "table1_category_participation_revised.csv"))
write_csv(desc, path("outputs", "tables", "table1_descriptive_statistics_revised.csv"))

commercial_vars <- grep("commercial|sale|sell|出售|销售|商品", names(data), ignore.case = TRUE, value = TRUE)
commercial_log <- c(
  "# Commercialization Rate Audit",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Finding",
  "",
  "- `commercialization_rate` is not present in the current analysis-ready household-category file.",
  "- Current analysis-ready columns only contain self-provisioning participation, self-production amount, consumption, self-sufficiency, and price variables.",
  "- Raw labels indicate sales and self-use quantities exist for some production modules, but denominators differ by module and category.",
  "- A clean commercialization rate therefore requires a separate denominator audit before inclusion.",
  "",
  "## Matching variables found in analysis-ready data",
  "",
  if (length(commercial_vars) == 0) "- None." else paste0("- `", commercial_vars, "`"),
  "",
  "## Decision",
  "",
  "- Do not construct `commercialization_rate` in the revised main rerun.",
  "- Record as HUMAN REVIEW REQUIRED: denominator unclear."
)
writeLines(commercial_log, path("outputs", "logs", "commercialization_rate_audit.md"), useBytes = TRUE)

issue_lines <- c(
  "# Revised Variable Issues",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "- `commercialization_rate` is unavailable in the current analysis-ready data and is not constructed without denominator review.",
  "- `roulei` split and `youzhi` definition require category-definition audit outputs.",
  "- Main code variable remains `production_participation`; prose label should be self-provisioning participation."
)
writeLines(issue_lines, path("outputs", "logs", "revised_variable_issues.md"), useBytes = TRUE)

merge_log <- c(
  "# Revised Data Merge Log",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  paste0("- Input file: `", input_file, "`."),
  paste0("- Output file: `", revised_file, "`."),
  "- The revised analysis file inherits the cleaned geography, POI-year rule, hedonic price imputation, GAEZ, terrain, early NTL, county text, and household resource controls from the previously rebuilt analysis-ready long file.",
  "- Food categories are restricted to the eight revised categories; condiments, sugar, and tea are excluded.",
  "",
  "## Sample summary",
  "",
  paste0("- Rows: ", nrow(data)),
  paste0("- Households: ", length(unique(data$nhCode))),
  paste0("- Food categories: ", length(unique(data$food_category))),
  paste0("- Villages/clusters: ", length(unique(data$xzc12_for_merge_final))),
  paste0("- Provinces: ", length(unique(data$provn_std))),
  paste0("- Counties: ", length(unique(data$countyn_std)))
)
writeLines(merge_log, path("outputs", "logs", "revised_data_merge_log.md"), useBytes = TRUE)

message("Revised analysis data rebuilt.")
````

## `code/02_common_sample_baseline.R`

- Size: 3.2 KB
- Lines: 87

````r
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
````

## `code/02_full_variable_descriptive_audit.R`

- Size: 33.1 KB
- Lines: 714

````r
options(warn = 1)

root <- getwd()

dir.create(file.path(root, "outputs", "logs"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "tables"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "data", "cleaned"), recursive = TRUE, showWarnings = FALSE)

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

trim_text <- function(x) {
  x <- as.character(x)
  x <- gsub("\ufeff", "", x, fixed = TRUE)
  x <- gsub("[[:space:]\u3000]+", "", x)
  x[x == ""] <- NA_character_
  x
}

to_num <- function(x) {
  if (is.numeric(x)) return(x)
  x <- trim_text(x)
  suppressWarnings(as.numeric(x))
}

is_missing_code <- function(x) {
  !is.na(x) & x %in% c(-999, -998, -997, -99, -98, -97, -9, -8, -7, -1)
}

norm_prov <- function(x) {
  x <- trim_text(x)
  x[x == "湖北"] <- "湖北省"
  x[x == "陕西"] <- "陕西省"
  x
}

mode_value <- function(x, max_len = 80) {
  x <- trim_text(x)
  x <- x[!is.na(x)]
  if (length(x) == 0) return(NA_character_)
  tb <- sort(table(x), decreasing = TRUE)
  top <- paste0(names(tb)[seq_len(min(length(tb), 3))], "=", as.integer(tb[seq_len(min(length(tb), 3))]))
  out <- paste(top, collapse = "; ")
  if (nchar(out) > max_len) paste0(substr(out, 1, max_len - 3), "...") else out
}

summarise_var <- function(data, var, module, role = "", source = "", label = NA_character_) {
  x_raw <- data[[var]]
  x_num <- to_num(x_raw)
  raw_nonmiss <- trim_text(x_raw)
  n <- length(x_raw)
  missing <- sum(is.na(raw_nonmiss))
  numeric_ok <- sum(!is.na(x_num))
  treat_numeric <- numeric_ok >= max(10, 0.8 * (n - missing))

  if (treat_numeric) {
    ok <- !is.na(x_num)
    qs <- if (any(ok)) {
      as.numeric(quantile(x_num, probs = c(.01, .05, .25, .5, .75, .95, .99), na.rm = TRUE, names = FALSE))
    } else {
      rep(NA_real_, 7)
    }
    data.frame(
      module = module,
      role = role,
      source = source,
      variable = var,
      label = label,
      type = "numeric",
      n = n,
      missing = sum(!ok),
      missing_share = sum(!ok) / n,
      zero = sum(x_num == 0, na.rm = TRUE),
      zero_share = sum(x_num == 0, na.rm = TRUE) / n,
      negative = sum(x_num < 0, na.rm = TRUE),
      missing_code = sum(is_missing_code(x_num), na.rm = TRUE),
      mean = if (any(ok)) mean(x_num, na.rm = TRUE) else NA_real_,
      sd = if (sum(ok) > 1) sd(x_num, na.rm = TRUE) else NA_real_,
      min = if (any(ok)) min(x_num, na.rm = TRUE) else NA_real_,
      p01 = qs[1], p05 = qs[2], p25 = qs[3], p50 = qs[4],
      p75 = qs[5], p95 = qs[6], p99 = qs[7],
      max = if (any(ok)) max(x_num, na.rm = TRUE) else NA_real_,
      n_unique = length(unique(x_num[ok])),
      top_values = NA_character_,
      stringsAsFactors = FALSE
    )
  } else {
    data.frame(
      module = module,
      role = role,
      source = source,
      variable = var,
      label = label,
      type = "categorical",
      n = n,
      missing = missing,
      missing_share = missing / n,
      zero = NA_integer_,
      zero_share = NA_real_,
      negative = NA_integer_,
      missing_code = NA_integer_,
      mean = NA_real_,
      sd = NA_real_,
      min = NA_real_,
      p01 = NA_real_, p05 = NA_real_, p25 = NA_real_, p50 = NA_real_,
      p75 = NA_real_, p95 = NA_real_, p99 = NA_real_,
      max = NA_real_,
      n_unique = length(unique(raw_nonmiss[!is.na(raw_nonmiss)])),
      top_values = mode_value(x_raw),
      stringsAsFactors = FALSE
    )
  }
}

safe_vars <- function(data, vars) intersect(vars, names(data))

label_of <- function(labels, vars) {
  out <- labels$label[match(vars, labels$var)]
  out[is.na(out)] <- ""
  out
}

parse_year <- function(x) {
  x <- trim_text(x)
  y <- suppressWarnings(as.integer(substr(x, 1, 4)))
  y[y < 1900 | y > 2026] <- NA_integer_
  y
}

sum_numeric_clean <- function(data, vars, missing_codes_as_na = TRUE) {
  vars <- safe_vars(data, vars)
  if (length(vars) == 0) return(rep(NA_real_, nrow(data)))
  mat <- as.data.frame(lapply(data[, vars, drop = FALSE], to_num), check.names = FALSE)
  if (missing_codes_as_na) {
    for (v in names(mat)) {
      x <- mat[[v]]
      x[is_missing_code(x)] <- NA
      mat[[v]] <- x
    }
  }
  rowSums(mat, na.rm = TRUE)
}

sum_labor_days_components <- function(data, vars) {
  vars <- safe_vars(data, vars)
  if (length(vars) == 0) {
    return(list(
      total = rep(NA_real_, nrow(data)),
      invalid_cells = 0,
      households_with_invalid = 0
    ))
  }
  mat <- as.data.frame(lapply(data[, vars, drop = FALSE], to_num), check.names = FALSE)
  invalid <- matrix(FALSE, nrow(data), length(vars))
  for (j in seq_along(vars)) {
    x <- mat[[vars[j]]]
    bad <- is_missing_code(x) | (!is.na(x) & (x < 0 | x > 365))
    invalid[, j] <- bad
    x[bad] <- NA_real_
    mat[[vars[j]]] <- x
  }
  list(
    total = rowSums(mat, na.rm = TRUE),
    mat = as.matrix(mat),
    invalid_cells = sum(invalid, na.rm = TRUE),
    households_with_invalid = sum(rowSums(invalid, na.rm = TRUE) > 0)
  )
}

clean_positive_price <- function(x) {
  x <- to_num(x)
  x[x <= 0 | is_missing_code(x)] <- NA_real_
  x
}

hh <- read_csv(
  path("raw_data", "户表数据_已清洗.csv"),
  colClasses = c(
    nhCode = "character", xzc12 = "character", county = "character",
    countyn = "character", town = "character", townn = "character",
    vil = "character", viln = "character"
  )
)
vl <- read_csv(
  path("raw_data", "村表数据_已清洗.csv"),
  colClasses = c(xzcCode = "character", xzcCode_clean = "character")
)
poi <- read_csv(path("raw_data", "poi", "village_pois_merged_dedup.csv"), colClasses = c(xzc12 = "character"))
hh_lab <- read_csv(path("raw_data", "户表数据_已清洗_变量标签.csv"))
vl_lab <- read_csv(path("raw_data", "村表数据_已清洗_变量标签.csv"))

gaez <- read_csv(path("raw_data", "paper1_iv_controls", "gaez_theme4_10km_village.csv"), colClasses = c(xzc12 = "character"))
terrain <- read_csv(path("raw_data", "paper1_iv_controls", "paper1_village_topography_iv_all_corridors.csv"), colClasses = c(xzc12 = "character"))
ntl <- read_csv(path("raw_data", "paper1_iv_controls", "paper1_village_early_ntl_peak_iv_9294.csv"), colClasses = c(xzc12 = "character"))
food_safety <- read_csv(path("raw_data", "food_safety", "paper_8provinces_all_counties_5year_complete.csv"))

hh_geo <- if (file.exists(path("data", "cleaned", "household_geography_clean.csv"))) {
  read_csv(path("data", "cleaned", "household_geography_clean.csv"), colClasses = c(nhCode = "character", xzc12 = "character", xzc12_for_merge = "character"))
} else {
  NULL
}
village_crosswalk <- if (file.exists(path("data", "cleaned", "village_merge_crosswalk.csv"))) {
  read_csv(path("data", "cleaned", "village_merge_crosswalk.csv"), colClasses = c(xzc12 = "character", xzc12_for_merge = "character"))
} else {
  NULL
}
area_clean <- if (file.exists(path("data", "cleaned", "household_total_sown_area.csv"))) {
  read_csv(path("data", "cleaned", "household_total_sown_area.csv"), colClasses = c(nhCode = "character", xzc12 = "character"))
} else {
  NULL
}
poi_counts <- if (file.exists(path("data", "cleaned", "poi_5km_village_counts_filled.csv"))) {
  read_csv(path("data", "cleaned", "poi_5km_village_counts_filled.csv"), colClasses = c(xzc12 = "character"))
} else {
  NULL
}
village_prices <- if (file.exists(path("data", "cleaned", "village_category_price_candidates.csv"))) {
  read_csv(path("data", "cleaned", "village_category_price_candidates.csv"), colClasses = c(xzc12 = "character"))
} else {
  NULL
}

## Derived household variables --------------------------------------------

rel_vars <- sprintf("family1_%02d_HA1", 1:8)
sex_vars <- sprintf("family1_%02d_HA2", 1:8)
birth_vars <- sprintf("family1_%02d_HA3", 1:8)
edu_vars <- sprintf("family2_%02d_HA10", 1:8)
ag_days_vars <- sprintf("family2_%02d_HA13", 1:8)
off_days_vars <- sprintf("family2_%02d_HA14", 1:8)

member_nonempty <- matrix(FALSE, nrow(hh), 8)
ages <- matrix(NA_real_, nrow(hh), 8)
sex <- matrix(NA_real_, nrow(hh), 8)
rel <- matrix(NA_real_, nrow(hh), 8)
edu <- matrix(NA_real_, nrow(hh), 8)

for (k in 1:8) {
  rv <- rel_vars[k]; sv <- sex_vars[k]; bv <- birth_vars[k]; ev <- edu_vars[k]
  member_nonempty[, k] <- (!is.na(trim_text(hh[[rv]])) | !is.na(trim_text(hh[[sv]])) | !is.na(trim_text(hh[[bv]])))
  birth_year <- parse_year(hh[[bv]])
  ages[, k] <- to_num(hh$data_year) - birth_year
  sex[, k] <- to_num(hh[[sv]])
  rel[, k] <- to_num(hh[[rv]])
  edu[, k] <- if (ev %in% names(hh)) to_num(hh[[ev]]) else NA_real_
}

ag_labor <- sum_labor_days_components(hh, ag_days_vars)
off_labor <- sum_labor_days_components(hh, off_days_vars)
agricultural_labor_days_total <- ag_labor$total
offfarm_labor_days_total <- off_labor$total
total_labor_days <- agricultural_labor_days_total + offfarm_labor_days_total
working_age_16_64 <- !is.na(ages) & ages >= 16 & ages <= 64
head_member <- !is.na(rel) & rel == 1
agricultural_labor_days_working_age_16_64 <- rowSums(ifelse(working_age_16_64, ag_labor$mat, NA_real_), na.rm = TRUE)
offfarm_labor_days_working_age_16_64 <- rowSums(ifelse(working_age_16_64, off_labor$mat, NA_real_), na.rm = TRUE)
total_labor_days_working_age_16_64 <- agricultural_labor_days_working_age_16_64 + offfarm_labor_days_working_age_16_64
agricultural_labor_days_head <- rowSums(ifelse(head_member, ag_labor$mat, NA_real_), na.rm = TRUE)
offfarm_labor_days_head <- rowSums(ifelse(head_member, off_labor$mat, NA_real_), na.rm = TRUE)
total_labor_days_head <- agricultural_labor_days_head + offfarm_labor_days_head

hh_der <- data.frame(
  nhCode = hh$nhCode,
  data_year = hh$data_year,
  provn = hh$provn,
  countyn = hh$countyn,
  xzc12 = hh$xzc12,
  household_size_reconstructed = rowSums(member_nonempty, na.rm = TRUE),
  n_members_with_birth = rowSums(!is.na(ages), na.rm = TRUE),
  num_children = rowSums(!is.na(ages) & ages < 16, na.rm = TRUE),
  num_elderly = rowSums(!is.na(ages) & ages >= 60, na.rm = TRUE),
  # Sex is coded 1/0 in this extract. Relationship cross-tabulation shows
  # household heads are mostly 1 and spouses are mostly 0, so we infer 1=male.
  num_adult_male = rowSums(!is.na(ages) & ages >= 16 & ages < 60 & sex == 1, na.rm = TRUE),
  num_adult_female = rowSums(!is.na(ages) & ages >= 16 & ages < 60 & sex == 0, na.rm = TRUE),
  female_members = rowSums(member_nonempty & sex == 0, na.rm = TRUE),
  agricultural_labor_days = agricultural_labor_days_total,
  offfarm_labor_days = offfarm_labor_days_total,
  total_labor_days = total_labor_days,
  agricultural_labor_days_working_age_16_64 = agricultural_labor_days_working_age_16_64,
  offfarm_labor_days_working_age_16_64 = offfarm_labor_days_working_age_16_64,
  total_labor_days_working_age_16_64 = total_labor_days_working_age_16_64,
  agricultural_labor_days_head = agricultural_labor_days_head,
  offfarm_labor_days_head = offfarm_labor_days_head,
  total_labor_days_head = total_labor_days_head,
  total_labor_days_gt365 = as.integer(total_labor_days > 365),
  stringsAsFactors = FALSE
)
hh_der$adult_members <- hh_der$household_size_reconstructed - hh_der$num_children - hh_der$num_elderly
hh_der$child_share <- ifelse(hh_der$household_size_reconstructed > 0, hh_der$num_children / hh_der$household_size_reconstructed, NA_real_)
hh_der$elderly_share <- ifelse(hh_der$household_size_reconstructed > 0, hh_der$num_elderly / hh_der$household_size_reconstructed, NA_real_)
hh_der$female_share <- ifelse(hh_der$household_size_reconstructed > 0, hh_der$female_members / hh_der$household_size_reconstructed, NA_real_)
hh_der$dependency_ratio <- ifelse(hh_der$adult_members > 0, (hh_der$num_children + hh_der$num_elderly) / hh_der$adult_members, NA_real_)
hh_der$agricultural_labor_days_per_adult <- ifelse(hh_der$adult_members > 0, hh_der$agricultural_labor_days / hh_der$adult_members, NA_real_)
hh_der$offfarm_labor_days_per_adult <- ifelse(hh_der$adult_members > 0, hh_der$offfarm_labor_days / hh_der$adult_members, NA_real_)
hh_der$total_labor_days_per_adult <- ifelse(hh_der$adult_members > 0, hh_der$total_labor_days / hh_der$adult_members, NA_real_)
hh_der$offfarm_labor_share <- ifelse(hh_der$total_labor_days > 0, hh_der$offfarm_labor_days / hh_der$total_labor_days, NA_real_)

head_edu <- rep(NA_real_, nrow(hh))
head_age <- rep(NA_real_, nrow(hh))
head_gender_male <- rep(NA_real_, nrow(hh))
for (k in 1:8) {
  idx <- is.na(head_edu) & !is.na(rel[, k]) & rel[, k] == 1 & !is.na(edu[, k])
  head_edu[idx] <- edu[idx, k]
  idx_age <- is.na(head_age) & !is.na(rel[, k]) & rel[, k] == 1 & !is.na(ages[, k])
  head_age[idx_age] <- ages[idx_age, k]
  idx_gender <- is.na(head_gender_male) & !is.na(rel[, k]) & rel[, k] == 1 & !is.na(sex[, k])
  head_gender_male[idx_gender] <- as.integer(sex[idx_gender, k] == 1)
}
if ("qinc_7" %in% names(hh)) {
  qinc7 <- to_num(hh$qinc_7)
  idx <- is.na(head_edu) & !is.na(qinc7)
  head_edu[idx] <- qinc7[idx]
}
hh_der$household_head_education <- head_edu
hh_der$household_head_age <- head_age
hh_der$household_head_gender_male <- head_gender_male

asset_vars <- safe_vars(hh, c("HB1", "HB2", "HB3", "HB4", "HB5"))
asset_mat <- as.data.frame(lapply(hh[, asset_vars, drop = FALSE], to_num), check.names = FALSE)
for (v in names(asset_mat)) {
  x <- asset_mat[[v]]
  x[is_missing_code(x) | x < 0 | x > 50] <- NA
  if (v == "HB5") x[!(x %in% c(0, 1))] <- NA
  asset_mat[[v]] <- x
}
hh_der$household_assets_count_proxy <- rowSums(asset_mat, na.rm = TRUE)
hh_der$household_has_broadband <- if ("HB5" %in% names(hh)) {
  x <- to_num(hh$HB5)
  x[!(x %in% c(0, 1))] <- NA
  x
} else {
  NA_real_
}

if (!is.null(area_clean)) {
  area_cols <- safe_vars(area_clean, c(
    "nhCode", "total_sown_area", "total_sown_area_clean", "total_sown_area_w99",
    "total_sown_area_raw", "total_sown_area_nonnegative", "total_sown_area_component_cap500",
    "area_component_outlier_n", "area_any_component_outlier", "area_total_winsorized_flag"
  ))
  hh_der <- merge(hh_der, area_clean[, area_cols], by = "nhCode", all.x = TRUE, sort = FALSE)
}

write_csv(hh_der, path("data", "cleaned", "household_derived_analysis_variables.csv"))

labor_days_audit <- data.frame(
  metric = c(
    "n_households",
    "agricultural_labor_component_invalid_cells",
    "offfarm_labor_component_invalid_cells",
    "households_with_agricultural_labor_component_invalid",
    "households_with_offfarm_labor_component_invalid",
    "households_total_labor_days_gt365",
    "share_total_labor_days_gt365",
    "max_agricultural_labor_days",
    "max_offfarm_labor_days",
    "max_total_labor_days",
    "max_total_labor_days_working_age_16_64",
    "max_total_labor_days_head"
  ),
  value = c(
    nrow(hh),
    ag_labor$invalid_cells,
    off_labor$invalid_cells,
    ag_labor$households_with_invalid,
    off_labor$households_with_invalid,
    sum(total_labor_days > 365, na.rm = TRUE),
    mean(total_labor_days > 365, na.rm = TRUE),
    max(agricultural_labor_days_total, na.rm = TRUE),
    max(offfarm_labor_days_total, na.rm = TRUE),
    max(total_labor_days, na.rm = TRUE),
    max(total_labor_days_working_age_16_64, na.rm = TRUE),
    max(total_labor_days_head, na.rm = TRUE)
  )
)
write_csv(labor_days_audit, path("outputs", "tables", "labor_days_cleaning_audit.csv"))

## Long household-category outcomes ----------------------------------------

main_cats <- c("zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo")
all_food_cats <- main_cats
cat_labels <- c(
  zhushi = "主食", doulei = "豆类", roulei = "肉类和水产品及加工品",
  danlei = "蛋类", nailei = "奶类", youzhi = "油脂",
  shucai = "蔬菜", shuiguo = "水果"
)

food_long <- do.call(rbind, lapply(all_food_cats, function(cat) {
  cons_v <- paste0(cat, "_cons_monthly_jin")
  self_v <- paste0(cat, "_selfprod_monthly_total")
  ss_v <- paste0(cat, "_self_suff_rate")
  price_v <- paste0(cat, "_price_wavg_yuan_per_jin")
  data.frame(
    nhCode = hh$nhCode,
    data_year = hh$data_year,
    provn = hh$provn,
    countyn = hh$countyn,
    xzc12 = hh$xzc12,
    food_category = cat,
    food_category_label = unname(cat_labels[cat]),
    cons_monthly_jin = if (cons_v %in% names(hh)) to_num(hh[[cons_v]]) else NA_real_,
    selfprod_monthly_total = if (self_v %in% names(hh)) to_num(hh[[self_v]]) else NA_real_,
    self_suff_rate = if (ss_v %in% names(hh)) to_num(hh[[ss_v]]) else NA_real_,
    price_wavg_yuan_per_jin_raw = if (price_v %in% names(hh)) to_num(hh[[price_v]]) else NA_real_,
    stringsAsFactors = FALSE
  )
}))
food_long$price_wavg_yuan_per_jin <- clean_positive_price(food_long$price_wavg_yuan_per_jin_raw)
food_long$price_wavg_yuan_per_jin_w99 <- food_long$price_wavg_yuan_per_jin
for (cat in unique(food_long$food_category)) {
  idx <- food_long$food_category == cat
  x <- food_long$price_wavg_yuan_per_jin[idx]
  if (any(!is.na(x))) {
    cutoff <- as.numeric(quantile(x, 0.99, na.rm = TRUE, names = FALSE))
    food_long$price_wavg_yuan_per_jin_w99[idx] <- pmin(x, cutoff)
  }
}
food_long$production_participation <- as.integer(!is.na(food_long$selfprod_monthly_total) & food_long$selfprod_monthly_total > 0)
food_long$log_selfprod_amount <- log1p(pmax(food_long$selfprod_monthly_total, 0))
food_long$ihs_selfprod_amount <- asinh(food_long$selfprod_monthly_total)
write_csv(food_long, path("data", "cleaned", "paper1_household_category_variable_audit_long.csv"))

food_outcome_stats <- do.call(rbind, lapply(split(food_long, food_long$food_category), function(d) {
  vars <- c("cons_monthly_jin", "selfprod_monthly_total", "production_participation",
            "log_selfprod_amount", "ihs_selfprod_amount", "self_suff_rate",
            "price_wavg_yuan_per_jin", "price_wavg_yuan_per_jin_w99")
  rows <- lapply(vars, function(v) summarise_var(d, v, "household_category_outcomes", v, "derived_long", unique(d$food_category_label)))
  out <- do.call(rbind, rows)
  out$food_category <- unique(d$food_category)
  out$food_category_label <- unique(d$food_category_label)
  out
}))
write_csv(food_outcome_stats, path("outputs", "tables", "household_category_outcome_descriptives.csv"))

## Variable registry --------------------------------------------------------

registry <- data.frame(module = character(), role = character(), source = character(), variable = character(), label = character(), stringsAsFactors = FALSE)
add_vars <- function(module, role, source, vars, labels = NULL) {
  vars <- unique(vars[!is.na(vars) & vars != ""])
  if (length(vars) == 0) return(data.frame())
  if (is.null(labels)) labels <- rep("", length(vars))
  data.frame(module = module, role = role, source = source, variable = vars, label = labels, stringsAsFactors = FALSE)
}

registry <- rbind(
  registry,
  add_vars("household_identifiers", "id_merge", "household_raw",
           safe_vars(hh, c("nhCode", "data_year", "food_year", "provn", "countyn", "county", "town", "townn", "vil", "viln", "x04n", "xzc12", "vilLat", "vilLon")),
           label_of(hh_lab, safe_vars(hh, c("nhCode", "data_year", "food_year", "provn", "countyn", "county", "town", "townn", "vil", "viln", "x04n", "xzc12", "vilLat", "vilLon")))),
  add_vars("household_composition_raw", "construct_hh_composition", "household_raw",
           safe_vars(hh, c(rel_vars, sex_vars, birth_vars, edu_vars, ag_days_vars, off_days_vars, "HA0", "qinc_7")),
           label_of(hh_lab, safe_vars(hh, c(rel_vars, sex_vars, birth_vars, edu_vars, ag_days_vars, off_days_vars, "HA0", "qinc_7")))),
  add_vars("household_controls_raw", "controls", "household_raw",
           safe_vars(hh, c("agri_business_income", "annual_expense_total", "monthly_expense_total", "hh_income_sum", "total_income", "total_income_w", paste0("HB", 1:9), "qinc_6", "qinc_8", "qinc_9")),
           label_of(hh_lab, safe_vars(hh, c("agri_business_income", "annual_expense_total", "monthly_expense_total", "hh_income_sum", "total_income", "total_income_w", paste0("HB", 1:9), "qinc_6", "qinc_8", "qinc_9")))),
  add_vars("derived_household_variables", "analysis_constructed", "derived",
           safe_vars(hh_der, setdiff(names(hh_der), c("nhCode", "data_year", "provn", "countyn", "xzc12"))),
           rep("derived variable", length(safe_vars(hh_der, setdiff(names(hh_der), c("nhCode", "data_year", "provn", "countyn", "xzc12"))))))
)

food_vars <- unlist(lapply(all_food_cats, function(cat) {
  paste0(cat, c("_cons_monthly_jin", "_selfprod_monthly_total", "_self_suff_rate", "_price_wavg_yuan_per_jin"))
}))
registry <- rbind(
  registry,
  add_vars("food_aggregate_raw", "outcomes_prices", "household_raw",
           safe_vars(hh, food_vars), label_of(hh_lab, safe_vars(hh, food_vars)))
)

area_vars <- intersect(hh_lab$var[grepl("种植面积（亩）$", hh_lab$label)], names(hh))
commercial_vars <- intersect(hh_lab$var[
  grepl("总产量|出售数量|出售的重量|留作自家|自家食用|赠送给别人|用来送礼", hh_lab$label) &
    grepl("liangshi_sc|shucai_shengchan|shuiguo_shengchan|youliao_shengchan|roulei_shengchan|dannai_shengchan", hh_lab$var)
], names(hh))
registry <- rbind(
  registry,
  add_vars("production_area_raw", "total_sown_area_source", "household_raw", area_vars, label_of(hh_lab, area_vars)),
  add_vars("commercialization_candidates_raw", "commercialization_reconstruction", "household_raw", commercial_vars, label_of(hh_lab, commercial_vars))
)

village_core <- safe_vars(vl, c(
  "xzcCode", "xzcCode_clean", "x02n", "x03n", "x04n", "xz00n", "data_year", "vilLat", "vilLon",
  "xz01", "xz02", "xz04", "xz05", "xz06", "juli",
  "fe01_01", "fe01_02", "fe01_03", "fe01_04", "fe03_01", "fe03_02", "fe03_03", "fe03_04",
  "shuzi01", "shuzi03", "shuzi05", "shuzi06", "shuzi07", "shuzi08", "shuzi10", "shuzi11"
))
registry <- rbind(
  registry,
  add_vars("village_survey_market_controls", "market_controls", "village_raw", village_core, label_of(vl_lab, village_core))
)

if (!is.null(poi_counts)) {
  poi_vars <- safe_vars(poi_counts, grep("^poi_|poi_year_assigned", names(poi_counts), value = TRUE))
  registry <- rbind(registry, add_vars("poi_market_access", "market_controls", "poi_constructed", poi_vars, rep("constructed POI 5km count/capacity", length(poi_vars))))
}

gaez_vars <- safe_vars(gaez, c(
  "gaez_wheat_si_10km", "gaez_maize_si_10km", "gaez_rice_si_10km", "gaez_soybean_si_10km",
  "gaez_wheat_ay_10km", "gaez_maize_ay_10km", "gaez_rice_ay_10km", "gaez_soybean_ay_10km",
  "gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km"
))
terrain_vars <- safe_vars(terrain, c(
  "iv_terrain_barrier_town_gee_2km", "iv_terrain_barrier_town_gee_1km",
  "iv_terrain_barrier_town_gee_5km", "iv_terrain_barrier_county_gee_2km",
  "town_corridor_slope_mean_gee_2km", "town_corridor_tri_mean_gee_2km",
  "town_corridor_water_occurrence_mean_gee_2km", "town_straight_dist_km_gee_2km"
))
ntl_vars <- safe_vars(ntl, c(
  "iv_early_ntl_peak_dist_9294", "dist_to_ntl_peak_km_9294",
  "county_ntl9294_mean", "county_ntl9294_sum", "county_ntl9294_max",
  "ntl9294_mean_20km", "ntl9294_max_20km", "ntl9294_sum_20km"
))
text_vars <- safe_vars(food_safety, c(
  "province", "county", "group", "window", "n_years_available",
  "risk_salience_z_5yr_sum", "governance_capacity_z_5yr_sum", "trust_signal_z_5yr_sum",
  "attention_z_broad_5yr_sum", "attention_z_strict_5yr_sum"
))
registry <- rbind(
  registry,
  add_vars("gaez_controls", "agroecological_controls", "gaez", gaez_vars, rep("GAEZ 10km control", length(gaez_vars))),
  add_vars("terrain_iv_controls", "iv_and_topography", "terrain_iv", terrain_vars, rep("terrain/water IV or control", length(terrain_vars))),
  add_vars("early_ntl_iv_controls", "iv_and_historical_market", "early_ntl", ntl_vars, rep("early nighttime light IV/control", length(ntl_vars))),
  add_vars("county_text_controls", "county_policy_text_controls", "food_safety_text", text_vars, rep("county text indicator", length(text_vars)))
)

if (!is.null(village_prices)) {
  vp_vars <- safe_vars(village_prices, grep("^village_price_", names(village_prices), value = TRUE))
  registry <- rbind(registry, add_vars("village_price_candidates", "price_imputation_candidates", "village_price_constructed", vp_vars, rep("village category median price candidate", length(vp_vars))))
}

registry <- unique(registry)
write_csv(registry, path("outputs", "tables", "analysis_variable_registry.csv"))

## Stats for registry -------------------------------------------------------

stats_rows <- list()
for (i in seq_len(nrow(registry))) {
  r <- registry[i, ]
  dat <- switch(
    r$source,
    household_raw = hh,
    derived = hh_der,
    village_raw = vl,
    poi_constructed = poi_counts,
    gaez = gaez,
    terrain_iv = terrain,
    early_ntl = ntl,
    food_safety_text = food_safety,
    village_price_constructed = village_prices,
    NULL
  )
  if (is.null(dat) || !r$variable %in% names(dat)) next
  stats_rows[[length(stats_rows) + 1]] <- summarise_var(dat, r$variable, r$module, r$role, r$source, r$label)
}
variable_stats <- do.call(rbind, stats_rows)
write_csv(variable_stats, path("outputs", "tables", "analysis_variable_descriptive_statistics.csv"))

module_counts <- aggregate(variable ~ module, data = variable_stats, FUN = function(x) length(unique(x)))
names(module_counts)[2] <- "n_variables"
module_mean_missing <- aggregate(missing_share ~ module, data = variable_stats, FUN = function(x) mean(x, na.rm = TRUE))
names(module_mean_missing)[2] <- "mean_missing_share"
high_missing <- aggregate(
  variable ~ module,
  data = variable_stats[variable_stats$missing_share >= 0.3, ],
  FUN = length
)
names(high_missing)[2] <- "n_variables_missing_share_ge_30pct"
module_missing <- merge(module_counts, module_mean_missing, by = "module", all.x = TRUE)
module_missing <- merge(module_missing, high_missing, by = "module", all.x = TRUE)
module_missing$n_variables_missing_share_ge_30pct[is.na(module_missing$n_variables_missing_share_ge_30pct)] <- 0
write_csv(module_missing, path("outputs", "tables", "analysis_variable_missingness_by_module.csv"))

## Potential variable inventory --------------------------------------------

inventory_patterns <- list(
  geography_match_candidates = "县|乡镇|街道|行政村|村名称|GPS|经度|纬度|xzc|town|vil|county|prov",
  household_composition_candidates = "成员|性别|出生|文化程度|户主|家庭人口|农业生产天数|非农工作天数|居住天数",
  income_asset_candidates = "收入|支出|汽车|摩托|电脑|宽带|冰箱|资产|培训|职业|务工",
  outcome_food_aggregate_candidates = "月消费量|自家生产食用量|食物自给率|均价",
  commercialization_candidates = "总产量|出售数量|出售金额|出售的重量|留作自家|自家食用|赠送|用来送礼|库存",
  total_sown_area_candidates = "种植面积（亩）|土地面积（亩）|总耕地面积",
  market_access_candidates = "大型超市|食品杂货店|自由市场|农贸市场|肉店|水产店|距村|距离|快递|自提|电商|公交",
  price_candidates = "价格|售价|单价|均价|每斤多少钱|花多少钱",
  hedonic_price_covariates = "省|县|乡镇|村|距离|市场|超市|农贸|肉店|水产|POI|人均纯收入|总耕地|年份|类别"
)

make_inventory <- function(labels, source_name) {
  do.call(rbind, lapply(names(inventory_patterns), function(group) {
    pat <- inventory_patterns[[group]]
    hit <- labels[grepl(pat, paste(labels$var, labels$label), ignore.case = TRUE), c("var", "label")]
    if (nrow(hit) == 0) return(data.frame())
    data.frame(
      inventory_group = group,
      source = source_name,
      variable = hit$var,
      label = hit$label,
      stringsAsFactors = FALSE
    )
  }))
}
potential_inventory <- rbind(
  make_inventory(hh_lab, "household_raw"),
  make_inventory(vl_lab, "village_raw")
)
potential_inventory <- unique(potential_inventory)
write_csv(potential_inventory, path("outputs", "tables", "potential_variable_inventory.csv"))

inventory_summary <- aggregate(variable ~ inventory_group + source, data = potential_inventory, FUN = length)
names(inventory_summary)[3] <- "n_variables"
write_csv(inventory_summary, path("outputs", "tables", "potential_variable_inventory_summary.csv"))

## Specific notes -----------------------------------------------------------

blank_county <- hh[is.na(trim_text(hh$countyn)) | trim_text(hh$countyn) == "", c("nhCode", "data_year", "provn", "countyn", "townn", "viln", "xzc12")]
blank_county_merge <- merge(blank_county, vl[, c("xzcCode_clean", "data_year", "x02n", "x03n", "x04n", "xz00n")],
                            by.x = c("xzc12", "data_year"), by.y = c("xzcCode_clean", "data_year"), all.x = TRUE)
write_csv(blank_county_merge, path("outputs", "tables", "blank_county_recovery_candidates.csv"))

unmatched_villages <- if (!is.null(village_crosswalk)) {
  village_crosswalk[village_crosswalk$match_status != "exact_code_year", ]
} else {
  data.frame()
}
write_csv(unmatched_villages, path("outputs", "tables", "village_merge_nonexact_records.csv"))

## Markdown report ----------------------------------------------------------

key_metric <- function(df, metric) {
  if (is.null(df) || !"metric" %in% names(df)) return(NA)
  df$value[df$metric == metric][1]
}
county_audit <- if (file.exists(path("outputs", "tables", "county_match_audit.csv"))) read_csv(path("outputs", "tables", "county_match_audit.csv")) else NULL
area_audit <- if (file.exists(path("outputs", "tables", "area_anomaly_audit.csv"))) read_csv(path("outputs", "tables", "area_anomaly_audit.csv")) else NULL
price_household <- if (file.exists(path("outputs", "tables", "price_household_category_audit.csv"))) read_csv(path("outputs", "tables", "price_household_category_audit.csv")) else NULL
poi_audit <- if (file.exists(path("outputs", "tables", "poi_coverage_audit.csv"))) read_csv(path("outputs", "tables", "poi_coverage_audit.csv")) else NULL

high_missing_vars <- variable_stats[variable_stats$missing_share >= 0.3, c("module", "variable", "missing_share", "label")]
high_missing_vars <- high_missing_vars[order(-high_missing_vars$missing_share), ]
top_high_missing <- head(high_missing_vars, 20)

report <- c(
  "# Full Variable Descriptive Audit",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Scope",
  "",
  "- This audit covers identifiers, matching fields, household composition, household controls, food-category outcomes, prices, commercialization candidates, total sown area, village market variables, POI measures, GAEZ controls, terrain/NTL IV variables, and county text indicators.",
  "- It does not estimate regressions and does not impute prices yet.",
  "",
  "## Matching Findings",
  "",
  paste0("- Blank county-name household records: ", nrow(blank_county), ". These can be recovered by `xzc12 + data_year`; the blank record maps to the village table if present."),
  paste0("- County text indicator match after standardization: ", key_metric(county_audit, "households_standardized_match"), "/", nrow(hh), " households."),
  paste0("- Non-exact village-year records: ", nrow(unmatched_villages), ". One can be auto-matched by village/town name if the existing crosswalk status says so; remaining unmatched records need manual review."),
  "",
  "## Variable Coverage",
  "",
  paste0("- Variables in analysis registry: ", nrow(registry), "."),
  paste0("- Derived household variables exported: ", ncol(hh_der) - 5, "."),
  paste0("- Household-category rows in long audit file: ", nrow(food_long), "."),
  paste0("- Potential variable inventory rows: ", nrow(potential_inventory), "."),
  "",
  "## Area and Commercialization",
  "",
  paste0("- Total sown area source variables: ", length(area_vars), "."),
  paste0("- Area negative or missing-code cells: ", key_metric(area_audit, "negative_or_missing_code_cells"), "."),
  paste0("- Commercialization candidate raw variables: ", length(commercial_vars), "."),
  "- Recommended commercialization hierarchy: first use `sold quantity / total output`; if total output is unavailable or unreliable for a category, use `sold quantity / (sold + own-consumed + gifted)` with a separate variable name.",
  "",
  "## Price Handling",
  "",
  "- Prices should be cleaned before use: remove nonpositive prices and category-specific outliers, then impute remaining missing prices with a hedonic price model or a documented fallback hierarchy.",
  "- Suggested hedonic price predictors: food category, survey year, province/county/town, village survey market variables, POI capacity, GAEZ/terrain controls, and village/county economic controls. Keep an imputation-source flag.",
  "",
  "## High Missingness Variables",
  "",
  if (nrow(top_high_missing) == 0) "- No registry variable has missing share >= 30%." else paste0(
    "- `", top_high_missing$variable, "` (", top_high_missing$module, "): ",
    round(100 * top_high_missing$missing_share, 1), "% missing"
  ),
  "",
  "## Output Files",
  "",
  "- `outputs/tables/analysis_variable_registry.csv`",
  "- `outputs/tables/analysis_variable_descriptive_statistics.csv`",
  "- `outputs/tables/analysis_variable_missingness_by_module.csv`",
  "- `outputs/tables/household_category_outcome_descriptives.csv`",
  "- `outputs/tables/potential_variable_inventory.csv`",
  "- `outputs/tables/potential_variable_inventory_summary.csv`",
  "- `outputs/tables/blank_county_recovery_candidates.csv`",
  "- `outputs/tables/village_merge_nonexact_records.csv`",
  "- `data/cleaned/household_derived_analysis_variables.csv`",
  "- `data/cleaned/paper1_household_category_variable_audit_long.csv`"
)

writeLines(report, path("outputs", "logs", "full_variable_descriptive_audit.md"), useBytes = TRUE)
````

## `code/03_baseline_coefficients_margins.R`

- Size: 2.6 KB
- Lines: 66

````r
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
````

## `code/03_price_reconstruction_check.R`

- Size: 9.3 KB
- Lines: 265

````r
options(warn = 1)

root <- getwd()
dir.create(file.path(root, "data", "cleaned"), recursive = TRUE, showWarnings = FALSE)
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

trim_text <- function(x) {
  x <- as.character(x)
  x <- gsub("\ufeff", "", x, fixed = TRUE)
  x <- gsub("[[:space:]\u3000]+", "", x)
  x[x == ""] <- NA_character_
  x
}

to_num <- function(x) {
  if (is.numeric(x)) return(x)
  suppressWarnings(as.numeric(trim_text(x)))
}

is_missing_code <- function(x) {
  !is.na(x) & x %in% c(-999, -998, -997, -99, -98, -97, -9, -8, -7, -1)
}

clean_positive <- function(x) {
  x <- to_num(x)
  x[x <= 0 | is_missing_code(x)] <- NA_real_
  x
}

row_sum_na <- function(data, vars) {
  vars <- intersect(vars, names(data))
  if (length(vars) == 0) return(rep(NA_real_, nrow(data)))
  mat <- as.data.frame(lapply(data[, vars, drop = FALSE], clean_positive), check.names = FALSE)
  out <- rowSums(mat, na.rm = TRUE)
  out[rowSums(!is.na(mat)) == 0] <- NA_real_
  out
}

row_mean_na <- function(data, vars) {
  vars <- intersect(vars, names(data))
  if (length(vars) == 0) return(rep(NA_real_, nrow(data)))
  mat <- as.data.frame(lapply(data[, vars, drop = FALSE], clean_positive), check.names = FALSE)
  rowMeans(mat, na.rm = TRUE)
}

summ_price <- function(x) {
  x <- clean_positive(x)
  ok <- !is.na(x)
  if (!any(ok)) {
    return(c(n_positive = 0, missing_share = 1, mean = NA, p50 = NA, p95 = NA, p99 = NA, max = NA))
  }
  c(
    n_positive = sum(ok),
    missing_share = mean(!ok),
    mean = mean(x, na.rm = TRUE),
    p50 = median(x, na.rm = TRUE),
    p95 = as.numeric(quantile(x, 0.95, na.rm = TRUE, names = FALSE)),
    p99 = as.numeric(quantile(x, 0.99, na.rm = TRUE, names = FALSE)),
    max = max(x, na.rm = TRUE)
  )
}

extract_item <- function(label) {
  x <- trim_text(label)
  item <- sub("｜.*$", "", x)
  item <- sub("^.*-", "", item)
  item
}

hh <- read_csv(
  path("raw_data", "户表数据_已清洗.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character")
)
hh_lab <- read_csv(path("raw_data", "户表数据_已清洗_变量标签.csv"))
hh_lab$item_token <- extract_item(hh_lab$label)

main_cats <- c("zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo")
cat_labels <- c(
  zhushi = "主食",
  doulei = "豆类",
  roulei = "肉类和水产品及加工品",
  danlei = "蛋类",
  nailei = "奶类",
  youzhi = "油脂",
  shucai = "蔬菜",
  shuiguo = "水果"
)

item_regex <- list(
  zhushi = "^(zhushi_)",
  doulei = "^(doulei_)",
  roulei = "^(roulei_|shuichan_)",
  danlei = "^(danlei_)",
  nailei = "^(nailei_)",
  youzhi = "^(youzhi_)",
  shucai = "^(shucai_)",
  shuiguo = "^(shuiguo_|tiankong5$)"
)

comparison_rows <- list()
map_rows <- list()
price_long_rows <- list()

for (cat in main_cats) {
  belongs <- grepl(item_regex[[cat]], hh_lab$item_token)

  spend_vars <- hh_lab$var[
    belongs &
      grepl("花费的金额(元)", hh_lab$label, fixed = TRUE) &
      hh_lab$var %in% names(hh)
  ]
  qty_vars <- hh_lab$var[
    belongs &
      grepl("购买的数量(斤)", hh_lab$label, fixed = TRUE) &
      !grepl("购买的数量中", hh_lab$label, fixed = TRUE) &
      !grepl("网购", hh_lab$label, fixed = TRUE) &
      hh_lab$var %in% names(hh)
  ]
  direct_ratio_price_vars <- hh_lab$var[
    belongs &
      grepl("均价（总花费/购买总量，元/斤）", hh_lab$label, fixed = TRUE) &
      hh_lab$var %in% names(hh)
  ]
  avg_each_price_vars <- hh_lab$var[
    belongs &
      grepl("均价（平均每次花费/平均每次量，元/斤）", hh_lab$label, fixed = TRUE) &
      hh_lab$var %in% names(hh)
  ]
  pjxfl_vars <- names(hh)[grepl(paste0(cat, ".*pjxfl$"), names(hh))]
  if (cat == "roulei") {
    pjxfl_vars <- unique(c(pjxfl_vars, names(hh)[grepl("shuichan.*pjxfl$", names(hh))]))
  }

  spend_sum <- row_sum_na(hh, spend_vars)
  qty_sum <- row_sum_na(hh, qty_vars)
  spend_qty_ratio <- ifelse(!is.na(spend_sum) & !is.na(qty_sum) & qty_sum > 0, spend_sum / qty_sum, NA_real_)
  direct_ratio_price <- row_mean_na(hh, direct_ratio_price_vars)
  avg_each_price <- row_mean_na(hh, avg_each_price_vars)
  pjxfl_simple_mean <- row_mean_na(hh, pjxfl_vars)
  existing <- clean_positive(hh[[paste0(cat, "_price_wavg_yuan_per_jin")]])

  price_long_rows[[length(price_long_rows) + 1]] <- data.frame(
    nhCode = hh$nhCode,
    data_year = hh$data_year,
    provn = hh$provn,
    countyn = hh$countyn,
    xzc12 = hh$xzc12,
    food_category = cat,
    food_category_label = unname(cat_labels[cat]),
    existing_price_wavg_yuan_per_jin = existing,
    price_recalc_spend_sum_over_purchase_qty_sum = clean_positive(spend_qty_ratio),
    price_mean_detail_total_spend_over_qty = clean_positive(direct_ratio_price),
    price_mean_detail_avg_each_purchase = clean_positive(avg_each_price),
    price_mean_raw_pjxfl = clean_positive(pjxfl_simple_mean),
    spend_sum_yuan = spend_sum,
    purchase_qty_sum_jin = qty_sum,
    stringsAsFactors = FALSE
  )

  methods <- list(
    existing_aggregate = existing,
    recomputed_spend_sum_over_purchase_qty_sum = spend_qty_ratio,
    mean_of_detail_total_spend_over_qty_prices = direct_ratio_price,
    mean_of_detail_avg_each_purchase_prices = avg_each_price,
    mean_of_raw_pjxfl_columns = pjxfl_simple_mean
  )

  for (method in names(methods)) {
    x <- clean_positive(methods[[method]])
    s <- summ_price(x)
    ok_pair <- !is.na(existing) & !is.na(x)
    comparison_rows[[length(comparison_rows) + 1]] <- data.frame(
      food_category = cat,
      food_category_label = unname(cat_labels[cat]),
      method = method,
      n_spend_vars = length(spend_vars),
      n_purchase_qty_vars = length(qty_vars),
      n_detail_total_ratio_price_vars = length(direct_ratio_price_vars),
      n_detail_avg_each_price_vars = length(avg_each_price_vars),
      n_pjxfl_vars = length(pjxfl_vars),
      n_positive = unname(s["n_positive"]),
      missing_share = unname(s["missing_share"]),
      mean = unname(s["mean"]),
      p50 = unname(s["p50"]),
      p95 = unname(s["p95"]),
      p99 = unname(s["p99"]),
      max = unname(s["max"]),
      n_overlap_with_existing = sum(ok_pair),
      cor_with_existing = if (sum(ok_pair) > 5) cor(existing[ok_pair], x[ok_pair]) else NA_real_,
      mean_abs_diff_with_existing = if (sum(ok_pair) > 0) mean(abs(existing[ok_pair] - x[ok_pair])) else NA_real_,
      exact_match_share_with_existing = if (sum(ok_pair) > 0) mean(abs(existing[ok_pair] - x[ok_pair]) < 1e-8) else NA_real_,
      stringsAsFactors = FALSE
    )
  }

  add_map <- function(method, vars) {
    vars <- intersect(vars, hh_lab$var)
    if (length(vars) == 0) return(NULL)
    data.frame(
      food_category = cat,
      food_category_label = unname(cat_labels[cat]),
      method = method,
      item_token = hh_lab$item_token[match(vars, hh_lab$var)],
      variable = vars,
      label = hh_lab$label[match(vars, hh_lab$var)],
      stringsAsFactors = FALSE
    )
  }
  map_rows[[length(map_rows) + 1]] <- add_map("spend_vars", spend_vars)
  map_rows[[length(map_rows) + 1]] <- add_map("purchase_qty_vars", qty_vars)
  map_rows[[length(map_rows) + 1]] <- add_map("detail_total_ratio_price_vars", direct_ratio_price_vars)
  map_rows[[length(map_rows) + 1]] <- add_map("detail_avg_each_price_vars", avg_each_price_vars)
  map_rows[[length(map_rows) + 1]] <- add_map("raw_pjxfl_vars", pjxfl_vars)
}

price_comparison <- do.call(rbind, comparison_rows)
price_map <- do.call(rbind, map_rows)
price_long <- do.call(rbind, price_long_rows)

write_csv(price_comparison, path("outputs", "tables", "price_reconstruction_method_comparison.csv"))
write_csv(price_map, path("outputs", "tables", "price_reconstruction_variable_map.csv"))
write_csv(price_long, path("data", "cleaned", "household_category_price_reconstruction_long.csv"))

report <- c(
  "# Price Reconstruction Check",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Methods",
  "",
  "- `existing_aggregate`: existing `{category}_price_wavg_yuan_per_jin`, after setting nonpositive prices to missing.",
  "- `recomputed_spend_sum_over_purchase_qty_sum`: sum of detail `花费的金额(元)` divided by sum of detail exact `购买的数量(斤)`.",
  "- `mean_of_detail_total_spend_over_qty_prices`: row mean of generated detail prices labelled `均价（总花费/购买总量，元/斤）`.",
  "- `mean_of_detail_avg_each_purchase_prices`: row mean of generated detail prices labelled `均价（平均每次花费/平均每次量，元/斤）`.",
  "- `mean_of_raw_pjxfl_columns`: row mean of raw columns ending in `pjxfl`.",
  "",
  "## Outputs",
  "",
  "- `outputs/tables/price_reconstruction_method_comparison.csv`",
  "- `outputs/tables/price_reconstruction_variable_map.csv`",
  "- `data/cleaned/household_category_price_reconstruction_long.csv`"
)
writeLines(report, path("outputs", "logs", "price_reconstruction_check.md"), useBytes = TRUE)

message("Price reconstruction check completed.")
````

## `code/04_category_specific_nsi.R`

- Size: 3 KB
- Lines: 79

````r
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
````

## `code/04_export_reprocessed_analysis_ready_data.R`

- Size: 8.4 KB
- Lines: 228

````r
options(warn = 1)

root <- getwd()
dir.create(file.path(root, "data", "analysis_ready"), recursive = TRUE, showWarnings = FALSE)
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

assert_unique <- function(data, keys, name) {
  dup <- duplicated(data[, keys, drop = FALSE])
  if (any(dup)) {
    stop(sprintf("%s has duplicated keys: %s", name, paste(keys, collapse = "+")))
  }
}

food_category_order <- c("zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo")

hh_der <- read_csv(
  path("data", "cleaned", "household_derived_analysis_variables.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character")
)
food_long <- read_csv(
  path("data", "cleaned", "paper1_household_category_variable_audit_long.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character")
)
price_long <- read_csv(
  path("data", "cleaned", "household_category_price_reconstruction_long.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character")
)
hh_geo <- read_csv(
  path("data", "cleaned", "household_geography_clean.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character", xzc12_for_merge = "character")
)
poi <- read_csv(
  path("data", "cleaned", "poi_5km_village_counts_filled.csv"),
  colClasses = c(xzc12 = "character")
)
village_price <- read_csv(
  path("data", "cleaned", "village_category_price_candidates.csv"),
  colClasses = c(xzc12 = "character")
)

food_long <- food_long[food_long$food_category %in% food_category_order, ]
food_long$food_category <- factor(food_long$food_category, levels = food_category_order)
food_long <- food_long[order(food_long$nhCode, food_long$food_category), ]
food_long$food_category <- as.character(food_long$food_category)

assert_unique(hh_der, "nhCode", "household_derived_analysis_variables")
assert_unique(food_long, c("nhCode", "food_category"), "paper1_household_category_variable_audit_long")
assert_unique(price_long, c("nhCode", "food_category"), "household_category_price_reconstruction_long")
assert_unique(hh_geo, "nhCode", "household_geography_clean")
assert_unique(poi, "xzc12", "poi_5km_village_counts_filled")

price_keep <- c(
  "nhCode", "food_category",
  "price_recalc_spend_sum_over_purchase_qty_sum",
  "price_mean_detail_total_spend_over_qty",
  "price_mean_detail_avg_each_purchase",
  "price_mean_raw_pjxfl",
  "spend_sum_yuan",
  "purchase_qty_sum_jin"
)
analysis <- merge(
  food_long,
  price_long[, intersect(price_keep, names(price_long)), drop = FALSE],
  by = c("nhCode", "food_category"),
  all.x = TRUE,
  sort = FALSE
)

hh_keep <- setdiff(names(hh_der), c("data_year", "provn", "countyn", "xzc12"))
analysis <- merge(
  analysis,
  hh_der[, hh_keep, drop = FALSE],
  by = "nhCode",
  all.x = TRUE,
  sort = FALSE
)

geo_keep <- c("nhCode", "provn_std", "countyn_std", "townn_std", "viln_std", "xzc12_for_merge", "match_status", "fallback_reason", "fallback_distance_km")
analysis <- merge(
  analysis,
  hh_geo[, intersect(geo_keep, names(hh_geo)), drop = FALSE],
  by = "nhCode",
  all.x = TRUE,
  sort = FALSE
)
analysis$xzc12_for_merge_final <- ifelse(
  is.na(analysis$xzc12_for_merge) | analysis$xzc12_for_merge == "",
  analysis$xzc12,
  analysis$xzc12_for_merge
)

poi_keep <- c("xzc12", grep("^poi_", names(poi), value = TRUE))
poi_for_merge <- poi[, intersect(poi_keep, names(poi)), drop = FALSE]
names(poi_for_merge)[names(poi_for_merge) == "xzc12"] <- "xzc12_for_merge_final"
analysis <- merge(
  analysis,
  poi_for_merge,
  by = "xzc12_for_merge_final",
  all.x = TRUE,
  sort = FALSE
)

village_price_rows <- do.call(rbind, lapply(food_category_order, function(cat) {
  v <- paste0("village_price_", cat, "_median")
  if (!v %in% names(village_price)) return(data.frame())
  data.frame(
    xzc12_for_merge_final = village_price$xzc12,
    data_year = village_price$data_year,
    food_category = cat,
    village_price_category_median = village_price[[v]],
    stringsAsFactors = FALSE
  )
}))
assert_unique(village_price_rows, c("xzc12_for_merge_final", "data_year", "food_category"), "village_category_price_candidates_long")
analysis <- merge(
  analysis,
  village_price_rows,
  by = c("xzc12_for_merge_final", "data_year", "food_category"),
  all.x = TRUE,
  sort = FALSE
)

analysis$price_preferred_household_recalc_yuan_per_jin <- analysis$price_recalc_spend_sum_over_purchase_qty_sum
analysis$price_preferred_household_recalc_w99_yuan_per_jin <- analysis$price_preferred_household_recalc_yuan_per_jin
for (cat in food_category_order) {
  idx <- analysis$food_category == cat
  x <- analysis$price_preferred_household_recalc_yuan_per_jin[idx]
  if (any(!is.na(x))) {
    cutoff <- as.numeric(quantile(x, 0.99, na.rm = TRUE, names = FALSE))
    analysis$price_preferred_household_recalc_w99_yuan_per_jin[idx] <- pmin(x, cutoff)
  }
}
analysis$price_source_preferred <- ifelse(
  !is.na(analysis$price_preferred_household_recalc_yuan_per_jin),
  "household_recalc_spend_over_qty",
  ifelse(!is.na(analysis$village_price_category_median), "village_category_median", NA_character_)
)

analysis$food_category <- factor(analysis$food_category, levels = food_category_order)
analysis <- analysis[order(analysis$nhCode, analysis$food_category), ]
analysis$food_category <- as.character(analysis$food_category)

front_cols <- c(
  "nhCode", "data_year", "provn", "countyn", "xzc12", "xzc12_for_merge_final",
  "provn_std", "countyn_std", "townn_std", "viln_std", "match_status",
  "food_category", "food_category_label",
  "cons_monthly_jin", "selfprod_monthly_total", "production_participation",
  "log_selfprod_amount", "ihs_selfprod_amount", "self_suff_rate",
  "price_recalc_spend_sum_over_purchase_qty_sum",
  "price_preferred_household_recalc_w99_yuan_per_jin",
  "price_wavg_yuan_per_jin", "price_wavg_yuan_per_jin_w99",
  "village_price_category_median", "price_source_preferred"
)
analysis <- analysis[, c(intersect(front_cols, names(analysis)), setdiff(names(analysis), front_cols)), drop = FALSE]

out_file <- path("data", "analysis_ready", "paper1_reprocessed_analysis_ready_long.csv")
write_csv(analysis, out_file)

summary <- data.frame(
  metric = c(
    "n_rows",
    "n_households",
    "n_food_categories",
    "n_duplicate_household_category_rows",
    "contains_tiaoliao_tang_cha",
    "n_missing_household_recalc_price",
    "n_missing_village_category_price",
    "n_missing_poi_market_capacity"
  ),
  value = c(
    nrow(analysis),
    length(unique(analysis$nhCode)),
    length(unique(analysis$food_category)),
    sum(duplicated(analysis[, c("nhCode", "food_category")])),
    any(analysis$food_category %in% c("tiaoliao", "tang", "cha")),
    sum(is.na(analysis$price_recalc_spend_sum_over_purchase_qty_sum)),
    sum(is.na(analysis$village_price_category_median)),
    if ("poi_market_capacity_5km" %in% names(analysis)) sum(is.na(analysis$poi_market_capacity_5km)) else NA_integer_
  ),
  stringsAsFactors = FALSE
)
write_csv(summary, path("outputs", "tables", "paper1_reprocessed_analysis_ready_export_summary.csv"))

report <- c(
  "# Paper 1 Reprocessed Analysis-Ready Export",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Output",
  "",
  "- `data/analysis_ready/paper1_reprocessed_analysis_ready_long.csv`",
  "",
  "## Unit of Observation",
  "",
  "- Household by food category.",
  "- Food categories retained: zhushi, doulei, roulei, danlei, nailei, youzhi, shucai, shuiguo.",
  "",
  "## Included Reprocessed Variables",
  "",
  "- Household composition and labor variables without household-level 365-day capping.",
  "- Cleaned total sown area and area anomaly flags.",
  "- Food-category outcomes for the 8 retained categories.",
  "- Existing positive prices and reconstructed household prices using detail spend divided by purchase quantity.",
  "- Village category price candidates and POI 5km market-access variables."
)
writeLines(report, path("outputs", "logs", "paper1_reprocessed_analysis_ready_export.md"), useBytes = TRUE)

message("Export completed: ", out_file)
````

## `code/05_hedonic_price_imputation.R`

- Size: 10.7 KB
- Lines: 279

````r
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

positive_or_na <- function(x) {
  x <- to_num(x)
  x[is.na(x) | x <= 0] <- NA_real_
  x
}

winsor_by_group <- function(x, group, p_low = 0.01, p_high = 0.99) {
  out <- positive_or_na(x)
  for (g in unique(group)) {
    idx <- group == g
    vals <- out[idx]
    if (sum(!is.na(vals)) < 5) next
    lo <- as.numeric(quantile(vals, p_low, na.rm = TRUE, names = FALSE))
    hi <- as.numeric(quantile(vals, p_high, na.rm = TRUE, names = FALSE))
    out[idx] <- pmin(pmax(vals, lo), hi)
  }
  out
}

category_median_impute <- function(x, group) {
  out <- positive_or_na(x)
  global_med <- median(out, na.rm = TRUE)
  for (g in unique(group)) {
    idx <- group == g
    med <- median(out[idx], na.rm = TRUE)
    if (is.na(med)) med <- global_med
    out[idx & is.na(out)] <- med
  }
  out
}

prep_prediction_data <- function(data) {
  data$food_category_model <- factor(data$food_category)
  data$data_year_model <- factor(data$data_year)
  data$provn_model <- data$provn_std
  data$provn_model[is.na(data$provn_model) | data$provn_model == ""] <- data$provn[is.na(data$provn_model) | data$provn_model == ""]
  data$provn_model[is.na(data$provn_model) | data$provn_model == ""] <- "UNKNOWN_PROVINCE"
  data$countyn_model <- data$countyn_std
  data$countyn_model[is.na(data$countyn_model) | data$countyn_model == ""] <- data$countyn[is.na(data$countyn_model) | data$countyn_model == ""]
  data$countyn_model[is.na(data$countyn_model) | data$countyn_model == ""] <- "UNKNOWN_COUNTY"
  data$provn_model <- factor(data$provn_model)
  data$countyn_model <- factor(data$countyn_model)

  village_price <- positive_or_na(data$village_price_category_median)
  data$village_price_missing <- as.integer(is.na(village_price))
  village_price_w <- winsor_by_group(village_price, data$food_category, 0.01, 0.99)
  village_price_imp <- category_median_impute(village_price_w, data$food_category)
  data$log_village_price_imp <- log(village_price_imp)

  poi_vars <- c(
    "poi_market_capacity_5km", "poi_fresh_market_capacity_5km",
    "poi_supermarket_5km", "poi_wet_market_5km", "poi_fresh_food_5km",
    "poi_grocery_5km", "poi_meat_aquatic_5km"
  )
  data$poi_covariates_missing <- as.integer(!complete.cases(data[, intersect(poi_vars, names(data)), drop = FALSE]))
  for (v in intersect(poi_vars, names(data))) {
    x <- to_num(data[[v]])
    x[is.na(x) | x < 0] <- 0
    data[[paste0("log1p_", v)]] <- log1p(x)
  }
  if ("poi_has_any_5km" %in% names(data)) {
    data$poi_has_any_5km_model <- to_num(data$poi_has_any_5km)
    data$poi_has_any_5km_model[is.na(data$poi_has_any_5km_model)] <- 0
  } else {
    data$poi_has_any_5km_model <- 0
  }
  data
}

eligible_for_model <- function(model, newdata) {
  ok <- rep(TRUE, nrow(newdata))
  for (nm in names(model$xlevels)) {
    if (nm %in% names(newdata)) {
      ok <- ok & as.character(newdata[[nm]]) %in% model$xlevels[[nm]]
    }
  }
  ok
}

safe_predict_price <- function(model, newdata) {
  out <- rep(NA_real_, nrow(newdata))
  ok <- eligible_for_model(model, newdata)
  if (any(ok)) {
    pred <- predict(model, newdata = newdata[ok, , drop = FALSE])
    out[ok] <- exp(pred)
  }
  out
}

fit_lm <- function(formula, data) {
  lm(formula, data = data, na.action = na.exclude)
}

analysis_file <- path("data", "analysis_ready", "paper1_reprocessed_analysis_ready_long.csv")
analysis <- read_csv(
  analysis_file,
  colClasses = c(
    nhCode = "character",
    xzc12 = "character",
    xzc12_for_merge_final = "character",
    xzc12_for_merge = "character"
  )
)

price_obs <- positive_or_na(analysis$price_recalc_spend_sum_over_purchase_qty_sum)
price_fit <- winsor_by_group(price_obs, analysis$food_category, 0.01, 0.99)
analysis$price_hedonic_observed_fit_yuan_per_jin <- price_fit

model_data <- prep_prediction_data(analysis)
model_data$log_price_fit <- log(price_fit)
train <- model_data[!is.na(model_data$log_price_fit), ]

base_covariates <- paste(
  c(
    "food_category_model",
    "data_year_model",
    "village_price_missing",
    "log_village_price_imp",
    "poi_covariates_missing",
    "poi_has_any_5km_model",
    "log1p_poi_market_capacity_5km",
    "log1p_poi_fresh_market_capacity_5km",
    "log1p_poi_supermarket_5km",
    "log1p_poi_wet_market_5km",
    "log1p_poi_fresh_food_5km",
    "log1p_poi_grocery_5km",
    "log1p_poi_meat_aquatic_5km"
  ),
  collapse = " + "
)

model_county <- fit_lm(as.formula(paste("log_price_fit ~", base_covariates, "+ countyn_model")), train)
model_province <- fit_lm(as.formula(paste("log_price_fit ~", base_covariates, "+ provn_model")), train)
model_category_year <- fit_lm(log_price_fit ~ food_category_model + data_year_model, train)

pred_county <- safe_predict_price(model_county, model_data)
pred_province <- safe_predict_price(model_province, model_data)
pred_category_year <- safe_predict_price(model_category_year, model_data)
category_median_price <- category_median_impute(price_fit, analysis$food_category)

hedonic_pred <- pred_county
pred_tier <- ifelse(!is.na(pred_county), "hedonic_county", NA_character_)
idx <- is.na(hedonic_pred) & !is.na(pred_province)
hedonic_pred[idx] <- pred_province[idx]
pred_tier[idx] <- "hedonic_province"
idx <- is.na(hedonic_pred) & !is.na(pred_category_year)
hedonic_pred[idx] <- pred_category_year[idx]
pred_tier[idx] <- "hedonic_category_year"
idx <- is.na(hedonic_pred)
hedonic_pred[idx] <- category_median_price[idx]
pred_tier[idx] <- "category_median_fallback"

analysis$price_hedonic_predicted_yuan_per_jin <- hedonic_pred
analysis$price_hedonic_prediction_tier <- pred_tier
analysis$price_hedonic_imputed_yuan_per_jin <- ifelse(!is.na(price_obs), price_obs, hedonic_pred)
analysis$price_hedonic_imputed_w99_yuan_per_jin <- winsor_by_group(
  analysis$price_hedonic_imputed_yuan_per_jin,
  analysis$food_category,
  0.01,
  0.99
)
analysis$price_hedonic_source <- ifelse(
  !is.na(price_obs),
  "observed_household_recalc",
  pred_tier
)

diagnostics <- data.frame(
  model = c("county", "province", "category_year"),
  n_train = c(nrow(model_county$model), nrow(model_province$model), nrow(model_category_year$model)),
  r_squared = c(summary(model_county)$r.squared, summary(model_province)$r.squared, summary(model_category_year)$r.squared),
  adj_r_squared = c(summary(model_county)$adj.r.squared, summary(model_province)$adj.r.squared, summary(model_category_year)$adj.r.squared),
  rmse_log_in_sample = c(
    sqrt(mean(resid(model_county)^2, na.rm = TRUE)),
    sqrt(mean(resid(model_province)^2, na.rm = TRUE)),
    sqrt(mean(resid(model_category_year)^2, na.rm = TRUE))
  ),
  stringsAsFactors = FALSE
)
write_csv(diagnostics, path("outputs", "tables", "hedonic_price_model_diagnostics.csv"))

summary_by_category <- do.call(rbind, lapply(split(analysis, analysis$food_category), function(d) {
  data.frame(
    food_category = d$food_category[1],
    food_category_label = d$food_category_label[1],
    n = nrow(d),
    n_observed_household_recalc = sum(d$price_hedonic_source == "observed_household_recalc", na.rm = TRUE),
    n_hedonic_imputed = sum(d$price_hedonic_source != "observed_household_recalc", na.rm = TRUE),
    n_county_tier = sum(d$price_hedonic_source == "hedonic_county", na.rm = TRUE),
    n_province_tier = sum(d$price_hedonic_source == "hedonic_province", na.rm = TRUE),
    n_category_year_tier = sum(d$price_hedonic_source == "hedonic_category_year", na.rm = TRUE),
    n_category_median_fallback = sum(d$price_hedonic_source == "category_median_fallback", na.rm = TRUE),
    observed_mean = mean(d$price_recalc_spend_sum_over_purchase_qty_sum, na.rm = TRUE),
    hedonic_imputed_mean = mean(d$price_hedonic_imputed_yuan_per_jin, na.rm = TRUE),
    hedonic_imputed_w99_mean = mean(d$price_hedonic_imputed_w99_yuan_per_jin, na.rm = TRUE),
    hedonic_imputed_p50 = median(d$price_hedonic_imputed_yuan_per_jin, na.rm = TRUE),
    hedonic_imputed_p99 = as.numeric(quantile(d$price_hedonic_imputed_yuan_per_jin, 0.99, na.rm = TRUE, names = FALSE)),
    hedonic_imputed_max = max(d$price_hedonic_imputed_yuan_per_jin, na.rm = TRUE),
    stringsAsFactors = FALSE
  )
}))
summary_by_category <- summary_by_category[match(unique(analysis$food_category), summary_by_category$food_category), ]
write_csv(summary_by_category, path("outputs", "tables", "hedonic_price_imputation_summary_by_category.csv"))

source_summary <- as.data.frame(table(analysis$price_hedonic_source), stringsAsFactors = FALSE)
names(source_summary) <- c("price_hedonic_source", "n_rows")
source_summary$share <- source_summary$n_rows / nrow(analysis)
write_csv(source_summary, path("outputs", "tables", "hedonic_price_imputation_source_summary.csv"))

write_csv(analysis, analysis_file)

report <- c(
  "# Hedonic Price Imputation",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Outcome",
  "",
  "- Updated `data/analysis_ready/paper1_reprocessed_analysis_ready_long.csv` in place.",
  "- Observed price is `price_recalc_spend_sum_over_purchase_qty_sum`.",
  "- Fitting price is category-level P1/P99 winsorized observed household recalc price.",
  "- Dependent variable is log fitting price.",
  "",
  "## Imputation Hierarchy",
  "",
  "1. Keep observed household-recalculated price when available.",
  "2. Use county-level hedonic prediction for missing household price.",
  "3. Use province-level hedonic prediction when county-level prediction is unavailable.",
  "4. Use category-year hedonic prediction when province-level prediction is unavailable.",
  "5. Use category median fallback if all model predictions fail.",
  "",
  "## New Columns",
  "",
  "- `price_hedonic_observed_fit_yuan_per_jin`",
  "- `price_hedonic_predicted_yuan_per_jin`",
  "- `price_hedonic_prediction_tier`",
  "- `price_hedonic_imputed_yuan_per_jin`",
  "- `price_hedonic_imputed_w99_yuan_per_jin`",
  "- `price_hedonic_source`",
  "",
  "## Outputs",
  "",
  "- `outputs/tables/hedonic_price_model_diagnostics.csv`",
  "- `outputs/tables/hedonic_price_imputation_summary_by_category.csv`",
  "- `outputs/tables/hedonic_price_imputation_source_summary.csv`"
)
writeLines(report, path("outputs", "logs", "hedonic_price_imputation.md"), useBytes = TRUE)

message("Hedonic price imputation completed and appended to: ", analysis_file)
````

## `code/05_two_part_model.R`

- Size: 2.4 KB
- Lines: 73

````r
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
````

## `code/06_construct_market_friction_and_external_controls.R`

- Size: 17 KB
- Lines: 402

````r
options(warn = 1)

root <- getwd()
dir.create(file.path(root, "data", "cleaned"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "data", "analysis_ready"), recursive = TRUE, showWarnings = FALSE)
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

trim_text <- function(x) {
  x <- as.character(x)
  x <- gsub("\ufeff", "", x, fixed = TRUE)
  x <- gsub("[[:space:]\u3000]+", "", x)
  x[x == ""] <- NA_character_
  x
}

to_num <- function(x) {
  if (is.numeric(x)) return(x)
  suppressWarnings(as.numeric(trim_text(x)))
}

zscore <- function(x) {
  x <- to_num(x)
  s <- sd(x, na.rm = TRUE)
  if (is.na(s) || s == 0) return(rep(NA_real_, length(x)))
  (x - mean(x, na.rm = TRUE)) / s
}

row_mean_min <- function(mat, min_nonmissing = 1) {
  mat <- as.matrix(mat)
  n_ok <- rowSums(!is.na(mat))
  out <- rowMeans(mat, na.rm = TRUE)
  out[n_ok < min_nonmissing] <- NA_real_
  out
}

first_nonmissing <- function(x) {
  x <- x[!is.na(x) & x != ""]
  if (length(x) == 0) NA else x[1]
}

dedupe_by_key <- function(data, key) {
  if (!any(duplicated(data[[key]]))) return(data)
  split_data <- split(data, data[[key]])
  rows <- lapply(split_data, function(d) {
    out <- d[1, , drop = FALSE]
    for (v in names(d)) {
      if (v == key) next
      x_num <- suppressWarnings(as.numeric(d[[v]]))
      if (sum(!is.na(x_num)) > 0 && sum(!is.na(x_num)) >= sum(!is.na(trim_text(d[[v]]))) * 0.8) {
        out[[v]] <- mean(x_num, na.rm = TRUE)
      } else {
        out[[v]] <- first_nonmissing(trim_text(d[[v]]))
      }
    }
    out
  })
  do.call(rbind, rows)
}

summarise_numeric <- function(data, vars, module) {
  rows <- lapply(vars[vars %in% names(data)], function(v) {
    x <- to_num(data[[v]])
    ok <- !is.na(x)
    qs <- if (any(ok)) {
      as.numeric(quantile(x, c(0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99), na.rm = TRUE, names = FALSE))
    } else {
      rep(NA_real_, 7)
    }
    data.frame(
      module = module,
      variable = v,
      n = length(x),
      missing = sum(!ok),
      missing_share = mean(!ok),
      mean = if (any(ok)) mean(x, na.rm = TRUE) else NA_real_,
      sd = if (sum(ok) > 1) sd(x, na.rm = TRUE) else NA_real_,
      min = if (any(ok)) min(x, na.rm = TRUE) else NA_real_,
      p01 = qs[1], p05 = qs[2], p25 = qs[3], p50 = qs[4],
      p75 = qs[5], p95 = qs[6], p99 = qs[7],
      max = if (any(ok)) max(x, na.rm = TRUE) else NA_real_,
      stringsAsFactors = FALSE
    )
  })
  if (length(rows) == 0) data.frame() else do.call(rbind, rows)
}

analysis_file <- path("data", "analysis_ready", "paper1_reprocessed_analysis_ready_long.csv")
analysis <- read_csv(
  analysis_file,
  colClasses = c(
    nhCode = "character",
    xzc12 = "character",
    xzc12_for_merge_final = "character",
    xzc12_for_merge = "character"
  )
)

## Drop previously appended fields to make reruns idempotent.
fields_to_refresh <- c(
  "fe01_01", "fe01_02", "fe01_03", "fe01_04",
  "fe03_01", "fe03_02", "fe03_03", "fe03_04",
  "juli", "shuzi05", "shuzi06",
  "retail_thickness_survey", "market_remoteness_survey",
  "fresh_market_friction_survey", "market_friction_survey",
  "market_friction_survey_components", "retail_thickness_survey_components",
  "market_remoteness_survey_components", "fresh_market_friction_survey_components",
  "poi_market_capacity_lag1", "poi_fresh_market_capacity_lag1",
  "poi_market_friction_lag1", "poi_fresh_market_friction_lag1",
  "combined_market_friction", "combined_market_friction_components",
  "gaez_wheat_si_10km", "gaez_maize_si_10km", "gaez_rice_si_10km",
  "gaez_soybean_si_10km", "gaez_wheat_ay_10km", "gaez_maize_ay_10km",
  "gaez_rice_ay_10km", "gaez_soybean_ay_10km",
  "gaez_overall_si_10km", "gaez_staple_si_10km",
  "gaez_soil_terrain_constraint_10km",
  "iv_terrain_barrier_town_gee_2km", "iv_terrain_barrier_town_gee_1km",
  "iv_terrain_barrier_town_gee_5km", "iv_terrain_barrier_county_gee_2km",
  "town_corridor_slope_mean_gee_2km", "town_corridor_tri_mean_gee_2km",
  "town_corridor_water_occurrence_mean_gee_2km", "town_straight_dist_km_gee_2km",
  "iv_early_ntl_peak_dist_9294", "dist_to_ntl_peak_km_9294",
  "county_ntl9294_mean", "county_ntl9294_sum", "county_ntl9294_max",
  "ntl9294_mean_20km", "ntl9294_max_20km", "ntl9294_sum_20km",
  "text_group", "text_window", "text_n_years_available",
  "risk_salience_z_5yr_sum", "governance_capacity_z_5yr_sum",
  "trust_signal_z_5yr_sum", "attention_z_broad_5yr_sum",
  "attention_z_strict_5yr_sum", "attention_z_5yr_sum",
  "county_text_match"
)
analysis <- analysis[, setdiff(names(analysis), fields_to_refresh), drop = FALSE]

## Village survey market indices -------------------------------------------

vl <- read_csv(
  path("raw_data", "村表数据_已清洗.csv"),
  colClasses = c(xzcCode = "character", xzcCode_clean = "character")
)
village_vars <- c(
  "xzcCode_clean", "data_year",
  "fe01_01", "fe01_02", "fe01_03", "fe01_04",
  "fe03_01", "fe03_02", "fe03_03", "fe03_04",
  "juli", "shuzi05", "shuzi06"
)
village_market <- vl[, intersect(village_vars, names(vl)), drop = FALSE]
names(village_market)[names(village_market) == "xzcCode_clean"] <- "xzc12_for_merge_final"

count_vars <- c("fe01_01", "fe01_02", "fe01_03", "fe01_04")
dist_vars <- c("fe03_01", "fe03_02", "fe03_03", "fe03_04", "juli")
for (v in intersect(c(count_vars, dist_vars, "shuzi05", "shuzi06"), names(village_market))) {
  x <- to_num(village_market[[v]])
  x[x < 0] <- NA_real_
  village_market[[v]] <- x
}

z_counts <- as.data.frame(lapply(village_market[, intersect(count_vars, names(village_market)), drop = FALSE], zscore), check.names = FALSE)
z_dists <- as.data.frame(lapply(village_market[, intersect(dist_vars, names(village_market)), drop = FALSE], zscore), check.names = FALSE)
village_market$retail_thickness_survey <- row_mean_min(z_counts, min_nonmissing = 2)
village_market$retail_thickness_survey_components <- rowSums(!is.na(z_counts))
village_market$market_remoteness_survey <- row_mean_min(z_dists, min_nonmissing = 2)
village_market$market_remoteness_survey_components <- rowSums(!is.na(z_dists))

fresh_components <- data.frame(
  fe01_03_neg = -zscore(village_market$fe01_03),
  fe01_04_neg = -zscore(village_market$fe01_04),
  fe03_03 = zscore(village_market$fe03_03),
  fe03_04 = zscore(village_market$fe03_04),
  check.names = FALSE
)
village_market$fresh_market_friction_survey <- row_mean_min(fresh_components, min_nonmissing = 2)
village_market$fresh_market_friction_survey_components <- rowSums(!is.na(fresh_components))

market_components <- cbind(-z_counts, z_dists)
village_market$market_friction_survey <- row_mean_min(market_components, min_nonmissing = 3)
village_market$market_friction_survey_components <- rowSums(!is.na(market_components))

analysis <- merge(
  analysis,
  village_market,
  by = c("xzc12_for_merge_final", "data_year"),
  all.x = TRUE,
  sort = FALSE
)

## POI friction aliases -----------------------------------------------------

analysis$poi_market_capacity_lag1 <- to_num(analysis$poi_market_capacity_5km)
analysis$poi_fresh_market_capacity_lag1 <- to_num(analysis$poi_fresh_market_capacity_5km)
analysis$poi_market_friction_lag1 <- -zscore(log1p(analysis$poi_market_capacity_lag1))
analysis$poi_fresh_market_friction_lag1 <- -zscore(log1p(analysis$poi_fresh_market_capacity_lag1))

combined_components <- data.frame(
  survey = zscore(analysis$market_friction_survey),
  poi = zscore(analysis$poi_market_friction_lag1),
  check.names = FALSE
)
analysis$combined_market_friction <- row_mean_min(combined_components, min_nonmissing = 1)
analysis$combined_market_friction_components <- rowSums(!is.na(combined_components))

## External village controls and IVs ---------------------------------------

merge_xzc12 <- function(base, external, vars) {
  external <- dedupe_by_key(external, "xzc12")
  keep <- intersect(c("xzc12", vars), names(external))
  external <- external[, keep, drop = FALSE]
  names(external)[names(external) == "xzc12"] <- "xzc12_for_merge_final"
  merge(base, external, by = "xzc12_for_merge_final", all.x = TRUE, sort = FALSE)
}

gaez <- read_csv(path("raw_data", "paper1_iv_controls", "gaez_theme4_10km_village.csv"), colClasses = c(xzc12 = "character"))
gaez_vars <- c(
  "gaez_wheat_si_10km", "gaez_maize_si_10km", "gaez_rice_si_10km", "gaez_soybean_si_10km",
  "gaez_wheat_ay_10km", "gaez_maize_ay_10km", "gaez_rice_ay_10km", "gaez_soybean_ay_10km",
  "gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km"
)
analysis <- merge_xzc12(analysis, gaez, gaez_vars)

terrain <- read_csv(path("raw_data", "paper1_iv_controls", "paper1_village_topography_iv_all_corridors.csv"), colClasses = c(xzc12 = "character"))
terrain_vars <- c(
  "iv_terrain_barrier_town_gee_2km", "iv_terrain_barrier_town_gee_1km",
  "iv_terrain_barrier_town_gee_5km", "iv_terrain_barrier_county_gee_2km",
  "town_corridor_slope_mean_gee_2km", "town_corridor_tri_mean_gee_2km",
  "town_corridor_water_occurrence_mean_gee_2km", "town_straight_dist_km_gee_2km"
)
analysis <- merge_xzc12(analysis, terrain, terrain_vars)

ntl <- read_csv(path("raw_data", "paper1_iv_controls", "paper1_village_early_ntl_peak_iv_9294.csv"), colClasses = c(xzc12 = "character"))
ntl_vars <- c(
  "iv_early_ntl_peak_dist_9294", "dist_to_ntl_peak_km_9294",
  "county_ntl9294_mean", "county_ntl9294_sum", "county_ntl9294_max",
  "ntl9294_mean_20km", "ntl9294_max_20km", "ntl9294_sum_20km"
)
analysis <- merge_xzc12(analysis, ntl, ntl_vars)

## County text indicators ---------------------------------------------------

food_safety <- read_csv(path("raw_data", "food_safety", "paper_8provinces_all_counties_5year_complete.csv"))
text_vars <- c(
  "province", "county", "group", "window", "n_years_available",
  "risk_salience_z_5yr_sum", "governance_capacity_z_5yr_sum",
  "trust_signal_z_5yr_sum", "attention_z_broad_5yr_sum", "attention_z_strict_5yr_sum"
)
food_safety <- food_safety[, intersect(text_vars, names(food_safety)), drop = FALSE]
names(food_safety)[names(food_safety) == "province"] <- "provn_std"
names(food_safety)[names(food_safety) == "county"] <- "countyn_std"
names(food_safety)[names(food_safety) == "group"] <- "text_group"
names(food_safety)[names(food_safety) == "window"] <- "text_window"
names(food_safety)[names(food_safety) == "n_years_available"] <- "text_n_years_available"
food_safety$provn_std <- trim_text(food_safety$provn_std)
food_safety$countyn_std <- trim_text(food_safety$countyn_std)
food_safety <- food_safety[!duplicated(food_safety[, c("provn_std", "countyn_std")]), ]

analysis$provn_std <- trim_text(analysis$provn_std)
analysis$countyn_std <- trim_text(analysis$countyn_std)
analysis <- merge(
  analysis,
  food_safety,
  by = c("provn_std", "countyn_std"),
  all.x = TRUE,
  sort = FALSE
)
analysis$attention_z_5yr_sum <- analysis$attention_z_broad_5yr_sum
analysis$county_text_match <- as.integer(!is.na(analysis$risk_salience_z_5yr_sum))

## Ordering and output ------------------------------------------------------

food_category_order <- c("zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo")
analysis$food_category <- factor(analysis$food_category, levels = food_category_order)
analysis <- analysis[order(analysis$nhCode, analysis$food_category), ]
analysis$food_category <- as.character(analysis$food_category)

write_csv(analysis, analysis_file)
write_csv(analysis, path("data", "cleaned", "paper1_household_category_long.csv"))

## Diagnostics --------------------------------------------------------------

merge_summary <- data.frame(
  item = c(
    "rows",
    "households",
    "food_categories",
    "unique_household_category_keys",
    "duplicate_household_category_keys",
    "unique_villages_in_analysis",
    "rows_missing_village_survey_market_friction",
    "rows_missing_poi_market_friction",
    "rows_missing_combined_market_friction",
    "rows_missing_gaez_overall_si",
    "rows_missing_terrain_iv_main",
    "rows_missing_early_ntl_iv",
    "rows_missing_county_text",
    "rows_with_wrong_poi_year_rule"
  ),
  value = c(
    nrow(analysis),
    length(unique(analysis$nhCode)),
    length(unique(analysis$food_category)),
    nrow(unique(analysis[, c("nhCode", "food_category")])),
    sum(duplicated(analysis[, c("nhCode", "food_category")])),
    length(unique(analysis$xzc12_for_merge_final)),
    sum(is.na(analysis$market_friction_survey)),
    sum(is.na(analysis$poi_market_friction_lag1)),
    sum(is.na(analysis$combined_market_friction)),
    sum(is.na(analysis$gaez_overall_si_10km)),
    sum(is.na(analysis$iv_terrain_barrier_town_gee_2km)),
    sum(is.na(analysis$iv_early_ntl_peak_dist_9294)),
    sum(is.na(analysis$risk_salience_z_5yr_sum)),
    sum((analysis$data_year == 2023 & analysis$poi_year_assigned != 2022) |
          (analysis$data_year == 2024 & analysis$poi_year_assigned != 2023), na.rm = TRUE)
  ),
  stringsAsFactors = FALSE
)
write_csv(merge_summary, path("outputs", "tables", "market_external_merge_summary.csv"))

market_vars <- c(
  "retail_thickness_survey", "market_remoteness_survey",
  "fresh_market_friction_survey", "market_friction_survey",
  "poi_market_capacity_lag1", "poi_fresh_market_capacity_lag1",
  "poi_market_friction_lag1", "poi_fresh_market_friction_lag1",
  "combined_market_friction"
)
market_summary <- summarise_numeric(analysis, market_vars, "market_friction")
write_csv(market_summary, path("outputs", "tables", "market_friction_indices_summary.csv"))

table1_vars <- c(
  "production_participation", "selfprod_monthly_total", "log_selfprod_amount",
  "ihs_selfprod_amount", "self_suff_rate",
  "price_hedonic_imputed_w99_yuan_per_jin",
  "household_size_reconstructed", "child_share", "elderly_share", "female_share",
  "dependency_ratio", "num_children", "num_elderly", "num_adult_male", "num_adult_female",
  "agricultural_labor_days", "offfarm_labor_days", "total_labor_days",
  "total_sown_area", "household_assets_count_proxy", "household_head_age",
  "household_head_education", "market_friction_survey", "poi_market_friction_lag1",
  "combined_market_friction", "gaez_overall_si_10km", "gaez_staple_si_10km",
  "gaez_soil_terrain_constraint_10km", "iv_terrain_barrier_town_gee_2km",
  "iv_early_ntl_peak_dist_9294", "risk_salience_z_5yr_sum",
  "governance_capacity_z_5yr_sum", "trust_signal_z_5yr_sum", "attention_z_5yr_sum"
)
table1 <- summarise_numeric(analysis, table1_vars, "table1")
write_csv(table1, path("outputs", "tables", "table1_descriptive_statistics.csv"))

category_summary <- aggregate(
  cbind(production_participation, selfprod_monthly_total, cons_monthly_jin) ~ food_category + food_category_label,
  data = analysis,
  FUN = function(x) mean(x, na.rm = TRUE)
)
category_n <- aggregate(nhCode ~ food_category + food_category_label, data = analysis, FUN = length)
names(category_n)[3] <- "n_rows"
category_summary <- merge(category_n, category_summary, by = c("food_category", "food_category_label"), all.x = TRUE)
write_csv(category_summary, path("outputs", "tables", "category_outcome_summary_for_checks.csv"))

report <- c(
  "# Data Merge Log",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Completed Step",
  "",
  "- Constructed village-survey market-friction indices.",
  "- Constructed POI friction aliases and combined market-friction index.",
  "- Merged GAEZ controls, terrain-water IVs, early nighttime-light IVs, and county text indicators.",
  "- Wrote the updated long dataset to both analysis-ready and canonical cleaned paths.",
  "",
  "## Output Data",
  "",
  "- `data/analysis_ready/paper1_reprocessed_analysis_ready_long.csv`",
  "- `data/cleaned/paper1_household_category_long.csv`",
  "",
  "## Market-Friction Construction",
  "",
  "- `retail_thickness_survey`: row mean of standardized outlet counts, requiring at least 2 outlet-count components.",
  "- `market_remoteness_survey`: row mean of standardized distances, requiring at least 2 distance components.",
  "- `fresh_market_friction_survey`: row mean of -standardized fresh/wet/meat outlet counts and standardized fresh/wet/meat distances, requiring at least 2 components.",
  "- `market_friction_survey`: row mean of -standardized outlet counts and standardized distances, requiring at least 3 components.",
  "- `poi_market_friction_lag1`: negative standardized log(1 + POI market capacity).",
  "- `combined_market_friction`: row mean of standardized survey friction and standardized POI friction.",
  "",
  "## Notes",
  "",
  "- `attention_z_5yr_sum` is set to `attention_z_broad_5yr_sum` because the actual text file contains broad and strict variants, not a generic attention field.",
  "- No village fixed effects, village-year fixed effects, DID, or panel specifications are used."
)
writeLines(report, path("outputs", "logs", "data_merge_log.md"), useBytes = TRUE)

message("Market friction and external controls merged.")
````

## `code/06_price_robustness.R`

- Size: 4 KB
- Lines: 91

````r
source("code/00_setup.R")

data <- read_csv(
  path("data", "analysis_ready", "paper1_revised_analysis_ready_long.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character", xzc12_for_merge_final = "character")
)
data <- prepare_revised_data(data)

base_no_price <- c(
  hh_terms_main, resource_terms_revised, market_gaez_terms_revised,
  "risk_salience_z_5yr_sum", "governance_capacity_z_5yr_sum",
  "trust_signal_z_5yr_sum", "attention_z_5yr_sum",
  category_year_terms_revised
)

specs <- list(
  no_price_control = list(price_var = NA_character_, rhs = base_no_price, subset = rep(TRUE, nrow(data))),
  hedonic_price_main = list(price_var = "price_hedonic_imputed_w99_yuan_per_jin", rhs = c(base_no_price, "price_hedonic_imputed_w99_yuan_per_jin"), subset = rep(TRUE, nrow(data))),
  observed_price_only = list(price_var = "price_preferred_household_recalc_w99_yuan_per_jin", rhs = c(base_no_price, "price_preferred_household_recalc_w99_yuan_per_jin"), subset = !is.na(data$price_preferred_household_recalc_w99_yuan_per_jin)),
  county_category_median_price = list(price_var = "village_price_category_median", rhs = c(base_no_price, "village_price_category_median"), subset = !is.na(data$village_price_category_median))
)

rows <- list()
issues <- c()
for (nm in names(specs)) {
  sp <- specs[[nm]]
  d <- data[sp$subset, ]
  if (nrow(d) < 100) {
    issues <- c(issues, paste0("- Skipped ", nm, ": fewer than 100 rows after price restriction."))
    next
  }
  fit <- fit_lm_cluster(d, "production_participation", sp$rhs)
  if (!fit$ok) {
    issues <- c(issues, paste0("- Skipped ", nm, ": model could not be estimated."))
    next
  }
  w <- wald_test(fit$model, fit$vcov, hh_terms_main)
  price_var_display <- ifelse(is.na(sp$price_var), "none", sp$price_var)
  price_var_display <- sub("yuan_per_jin$", "yuan_per_kg", price_var_display)
  price_var_display <- ifelse(
    price_var_display == "village_price_category_median",
    "village_price_category_median_yuan_per_kg",
    price_var_display
  )
  rows[[length(rows) + 1]] <- data.frame(
    price_spec = nm,
    model_compatibility_variable = ifelse(is.na(sp$price_var), "none", sp$price_var),
    price_variable = price_var_display,
    price_unit = ifelse(is.na(sp$price_var), "none", "yuan/kg"),
    outcome = "production_participation",
    conceptual_outcome = "self_provisioning_participation",
    n = nrow(fit$data),
    n_clusters = length(unique(fit$data$xzc12_for_merge_final)),
    r_squared = summary(fit$model)$r.squared,
    hhcomp_wald_chisq = w$stat,
    hhcomp_wald_df = w$df,
    hhcomp_wald_p = w$p,
    price_observed_share = ifelse(
      "price_hedonic_source" %in% names(fit$data),
      mean(fit$data$price_hedonic_source == "observed_household_recalc", na.rm = TRUE),
      NA_real_
    ),
    stringsAsFactors = FALSE
  )
}

tableC <- do.call(rbind, rows)
write_csv(tableC, path("outputs", "tables", "tableC_price_robustness.csv"))
write_simple_json(tableC, path("outputs", "model_summaries", "modelC_price_robustness.json"), key = "price_robustness")

if (length(issues) == 0) issues <- "- None. All requested price robustness variants were generated."
log_lines <- c(
  "# Price Robustness Issues",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Notes",
  "",
  "- Price variables are interpreted as yuan/kg in the cleaned analysis data.",
  "- Main price variable: `price_hedonic_imputed_w99_yuan_per_kg`.",
  "- Observed-price-only uses `price_preferred_household_recalc_w99_yuan_per_kg` and drops rows with missing observed recalculated price.",
  "- County-category median price uses `village_price_category_median_yuan_per_kg` and drops rows with missing median price.",
  "- The model still reads legacy compatibility aliases ending in `_yuan_per_jin`; those alias values were overwritten to yuan/kg by `code/19_apply_kg_units_drop_outliers_prepare_official_data.R`.",
  "",
  "## Issues",
  "",
  issues
)
writeLines(log_lines, path("outputs", "logs", "price_robustness_issues.md"), useBytes = TRUE)

message("Price robustness completed.")
````

## `code/07_add_household_resource_controls.R`

- Size: 5.2 KB
- Lines: 155

````r
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

trim_text <- function(x) {
  x <- as.character(x)
  x <- gsub("\ufeff", "", x, fixed = TRUE)
  x <- gsub("[[:space:]\u3000]+", "", x)
  x[x == ""] <- NA_character_
  x
}

to_num <- function(x) {
  if (is.numeric(x)) return(x)
  suppressWarnings(as.numeric(trim_text(x)))
}

is_missing_code <- function(x) {
  !is.na(x) & x %in% c(-999, -998, -997, -99, -98, -97, -9, -8, -7, -1)
}

winsor <- function(x, p_low = 0.01, p_high = 0.99) {
  x <- to_num(x)
  x[is_missing_code(x)] <- NA_real_
  if (sum(!is.na(x)) < 5) return(x)
  lo <- as.numeric(quantile(x, p_low, na.rm = TRUE, names = FALSE))
  hi <- as.numeric(quantile(x, p_high, na.rm = TRUE, names = FALSE))
  pmin(pmax(x, lo), hi)
}

summarise_numeric <- function(data, vars, module) {
  rows <- lapply(vars[vars %in% names(data)], function(v) {
    x <- to_num(data[[v]])
    ok <- !is.na(x)
    qs <- if (any(ok)) {
      as.numeric(quantile(x, c(0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99), na.rm = TRUE, names = FALSE))
    } else {
      rep(NA_real_, 7)
    }
    data.frame(
      module = module,
      variable = v,
      n = length(x),
      missing = sum(!ok),
      missing_share = mean(!ok),
      mean = if (any(ok)) mean(x, na.rm = TRUE) else NA_real_,
      sd = if (sum(ok) > 1) sd(x, na.rm = TRUE) else NA_real_,
      min = if (any(ok)) min(x, na.rm = TRUE) else NA_real_,
      p01 = qs[1], p05 = qs[2], p25 = qs[3], p50 = qs[4],
      p75 = qs[5], p95 = qs[6], p99 = qs[7],
      max = if (any(ok)) max(x, na.rm = TRUE) else NA_real_,
      stringsAsFactors = FALSE
    )
  })
  if (length(rows) == 0) data.frame() else do.call(rbind, rows)
}

analysis_file <- path("data", "analysis_ready", "paper1_reprocessed_analysis_ready_long.csv")
canonical_file <- path("data", "cleaned", "paper1_household_category_long.csv")

analysis <- read_csv(
  analysis_file,
  colClasses = c(nhCode = "character", xzc12 = "character", xzc12_for_merge_final = "character")
)
hh <- read_csv(
  path("raw_data", "户表数据_已清洗.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character")
)

resource_vars <- c(
  "nhCode",
  "agri_business_income",
  "annual_expense_total",
  "monthly_expense_total",
  "hh_income_sum",
  "total_income",
  "total_income_w"
)
resource <- hh[, intersect(resource_vars, names(hh)), drop = FALSE]
for (v in setdiff(names(resource), "nhCode")) {
  x <- to_num(resource[[v]])
  x[is_missing_code(x) | x < 0] <- NA_real_
  resource[[v]] <- x
  resource[[paste0(v, "_w99")]] <- winsor(x, 0.01, 0.99)
  resource[[paste0("log1p_", v, "_w99")]] <- log1p(resource[[paste0(v, "_w99")]])
}

if (any(duplicated(resource$nhCode))) {
  stop("Resource controls are not unique by nhCode.")
}

drop_resource_cols <- setdiff(names(resource), "nhCode")
analysis <- analysis[, setdiff(names(analysis), drop_resource_cols), drop = FALSE]
analysis <- merge(analysis, resource, by = "nhCode", all.x = TRUE, sort = FALSE)

food_category_order <- c("zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo")
analysis$food_category <- factor(analysis$food_category, levels = food_category_order)
analysis <- analysis[order(analysis$nhCode, analysis$food_category), ]
analysis$food_category <- as.character(analysis$food_category)

write_csv(analysis, analysis_file)
write_csv(analysis, canonical_file)

resource_summary <- summarise_numeric(analysis, setdiff(names(resource), "nhCode"), "household_resource_controls")
write_csv(resource_summary, path("outputs", "tables", "household_resource_controls_summary.csv"))

if (file.exists(path("outputs", "tables", "table1_descriptive_statistics.csv"))) {
  table1 <- read_csv(path("outputs", "tables", "table1_descriptive_statistics.csv"))
  table1 <- table1[!table1$variable %in% resource_summary$variable, ]
  table1 <- rbind(table1, resource_summary)
  write_csv(table1, path("outputs", "tables", "table1_descriptive_statistics.csv"))
}

report <- c(
  "# Household Resource Controls",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Added Variables",
  "",
  "- Raw cleaned resource variables from the household survey.",
  "- P1/P99 winsorized versions with `_w99` suffix.",
  "- Log transformed winsorized versions with `log1p_..._w99` names.",
  "",
  "## Files Updated",
  "",
  "- `data/analysis_ready/paper1_reprocessed_analysis_ready_long.csv`",
  "- `data/cleaned/paper1_household_category_long.csv`",
  "- `outputs/tables/household_resource_controls_summary.csv`",
  "- `outputs/tables/table1_descriptive_statistics.csv`"
)
writeLines(report, path("outputs", "logs", "household_resource_controls.md"), useBytes = TRUE)

message("Household resource controls added.")
````

## `code/07_category_definition_audits.R`

- Size: 3.9 KB
- Lines: 72

````r
source("code/00_setup.R")

label_file <- path("raw_data", "户表数据_已清洗_变量标签.csv")
lab <- read_csv(label_file)

label_text <- paste(lab$var, lab$label)
roulei_hits <- lab[grepl("roulei|shuichan|肉类|水产|鱼|虾|蟹|贝", label_text, ignore.case = TRUE), ]
youzhi_hits <- lab[grepl("youzhi|油脂|油料|植物油|猪油|食用油", label_text, ignore.case = TRUE), ]

has_shuichan <- any(grepl("shuichan|水产|鱼|虾|蟹|贝", paste(roulei_hits$var, roulei_hits$label), ignore.case = TRUE))
has_roulei <- any(grepl("roulei|肉类", paste(roulei_hits$var, roulei_hits$label), ignore.case = TRUE))
has_youliao_prod <- any(grepl("youliao_shengchan|油料", paste(youzhi_hits$var, youzhi_hits$label), ignore.case = TRUE))
has_youzhi_consumption <- any(grepl("youzhi", youzhi_hits$var, ignore.case = TRUE))

audit <- data.frame(
  audit_item = c("roulei_split", "youzhi_definition"),
  status = c(
    ifelse(has_shuichan && has_roulei, "partially_feasible_raw_detail_present", "not_feasible_no_raw_detail_found"),
    ifelse(has_youzhi_consumption, "partially_identified_human_review_required", "unclear_human_review_required")
  ),
  evidence = c(
    paste0("Variable labels include roulei meat-detail variables and shuichan/aquatic-detail variables: ", has_shuichan, ". Current analysis-ready long data has only aggregate `roulei` outcome."),
    paste0("Variable labels include youzhi consumption variables: ", has_youzhi_consumption, "; oilseed production module variables: ", has_youliao_prod, ". Item-level labels do not clearly map youzhi_1-youzhi_6 to oil crops versus edible oils.")
  ),
  decision = c(
    "Do not split roulei in the revised rerun without rebuilding detail-level outcomes and prices. Report as human-review flag.",
    "Use current aggregate `youzhi` as oils category, but avoid strong substantive claims before item-code review."
  ),
  human_review_required = c(TRUE, TRUE),
  stringsAsFactors = FALSE
)
write_csv(audit, path("outputs", "tables", "tableD_category_definition_audits.csv"))

roulei_log <- c(
  "# Roulei Split Audit",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Finding",
  "",
  paste0("- Raw labels contain meat-detail variables: ", has_roulei, "."),
  paste0("- Raw labels contain aquatic-detail variables such as `shuichan_1`: ", has_shuichan, "."),
  "- The current analysis-ready household-category long data contains only the aggregate `roulei` category and does not contain separate `meat` and `aquatic_products` outcomes.",
  "- A split would require rebuilding consumption, self-provisioning participation, self-production amount, price, and self-sufficiency outcomes from item-level raw variables.",
  "",
  "## Decision",
  "",
  "- Roulei split is not performed in this revised rerun.",
  "- Human review is required before making split-category claims."
)
writeLines(roulei_log, path("outputs", "logs", "roulei_split_audit.md"), useBytes = TRUE)

youzhi_log <- c(
  "# Youzhi Definition Audit",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Finding",
  "",
  paste0("- Raw labels contain aggregate `youzhi` consumption/source variables: ", has_youzhi_consumption, "."),
  paste0("- Raw labels contain oilseed production module variables (`youliao_shengchan`): ", has_youliao_prod, "."),
  "- The food-category documentation defines `youzhi` as `油脂类`.",
  "- The available labels do not clearly state whether the strong `youzhi` result reflects oil crops, home-produced edible oil, self-retained oilseeds, purchased oils with self-production source, or a mixture.",
  "",
  "## Decision",
  "",
  "- Keep `youzhi` as the aggregate oils category in revised models.",
  "- Human review required before making strong substantive claims about the oil category."
)
writeLines(youzhi_log, path("outputs", "logs", "youzhi_definition_audit.md"), useBytes = TRUE)

message("Category definition audits completed.")
````

## `code/08_baseline_separability_tests.R`

- Size: 8.4 KB
- Lines: 248

````r
options(warn = 1)

root <- getwd()
dir.create(file.path(root, "outputs", "tables"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "model_summaries"), recursive = TRUE, showWarnings = FALSE)
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
  if (length(terms) == 0) {
    return(list(stat = NA_real_, df = 0L, p = NA_real_))
  }
  b <- coefs[terms]
  V <- vcov_mat[terms, terms, drop = FALSE]
  invV <- tryCatch(solve(V), error = function(e) MASS::ginv(V))
  stat <- as.numeric(t(b) %*% invV %*% b)
  df <- length(terms)
  list(stat = stat, df = df, p = 1 - pchisq(stat, df))
}

tidy_hh_terms <- function(model, vcov_mat, outcome, spec, n_used, cluster_n, r2, wald) {
  terms <- c("household_size_reconstructed", "child_share", "elderly_share", "female_share")
  coefs <- coef(model)
  rows <- lapply(terms, function(term) {
    if (!term %in% names(coefs)) {
      return(data.frame())
    }
    se <- sqrt(diag(vcov_mat))[term]
    tval <- coefs[term] / se
    data.frame(
      outcome = outcome,
      spec = spec,
      term = term,
      estimate = coefs[term],
      std_error_cluster = se,
      t_stat = tval,
      p_value = 2 * pnorm(abs(tval), lower.tail = FALSE),
      n = n_used,
      n_clusters = cluster_n,
      r_squared = r2,
      hhcomp_wald_chisq = wald$stat,
      hhcomp_wald_df = wald$df,
      hhcomp_wald_p = wald$p,
      stringsAsFactors = FALSE
    )
  })
  do.call(rbind, rows)
}

json_escape <- function(x) {
  x <- gsub("\\\\", "\\\\\\\\", x)
  x <- gsub('"', '\\"', x)
  x <- gsub("\n", "\\\\n", x)
  x
}

write_model_json <- function(models_meta, file) {
  lines <- c("{", '  "models": [')
  for (i in seq_len(nrow(models_meta))) {
    r <- models_meta[i, ]
    comma <- if (i < nrow(models_meta)) "," else ""
    lines <- c(lines, paste0(
      "    {",
      '"outcome":"', json_escape(r$outcome), '",',
      '"spec":"', json_escape(r$spec), '",',
      '"n":', r$n, ",",
      '"n_clusters":', r$n_clusters, ",",
      '"r_squared":', signif(r$r_squared, 8), ",",
      '"hhcomp_wald_chisq":', signif(r$hhcomp_wald_chisq, 8), ",",
      '"hhcomp_wald_df":', r$hhcomp_wald_df, ",",
      '"hhcomp_wald_p":', signif(r$hhcomp_wald_p, 8),
      "}", comma
    ))
  }
  lines <- c(lines, "  ]", "}")
  writeLines(lines, file, useBytes = TRUE)
}

data <- read_csv(
  path("data", "cleaned", "paper1_household_category_long.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character", xzc12_for_merge_final = "character")
)

## Median-impute selected controls to avoid dropping observations solely due
## to household-head or resource-control missingness. Missingness indicators
## are included in resource/control specs.
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

hhcomp <- "household_size_reconstructed + child_share + elderly_share + female_share"
category_year <- "factor(food_category) + factor(data_year)"
resources <- paste(
  c(
    "log1p_total_income_w_w99_imp", "log1p_total_income_w_w99_missing",
    "log1p_agri_business_income_w99_imp", "log1p_agri_business_income_w99_missing",
    "log1p_annual_expense_total_w99_imp", "log1p_annual_expense_total_w99_missing",
    "total_sown_area", "agricultural_labor_days", "offfarm_labor_days",
    "household_assets_count_proxy_imp", "household_assets_count_proxy_missing",
    "household_head_age_imp", "household_head_age_missing",
    "household_head_education_imp", "household_head_education_missing",
    "household_head_gender_male_imp", "household_head_gender_male_missing"
  ),
  collapse = " + "
)
market_controls <- paste(
  c(
    "market_friction_survey", "poi_market_friction_lag1",
    "gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km",
    "factor(provn_std)"
  ),
  collapse = " + "
)
text_price_controls <- paste(
  c(
    "price_hedonic_imputed_w99_yuan_per_jin",
    "risk_salience_z_5yr_sum", "governance_capacity_z_5yr_sum",
    "trust_signal_z_5yr_sum", "attention_z_5yr_sum"
  ),
  collapse = " + "
)

specs <- list(
  M0_composition_category_year = paste(hhcomp, category_year, sep = " + "),
  M1_plus_household_resources = paste(hhcomp, resources, category_year, sep = " + "),
  M2_plus_market_gaez_province = paste(hhcomp, resources, market_controls, category_year, sep = " + "),
  M3_plus_price_text = paste(hhcomp, resources, market_controls, text_price_controls, category_year, sep = " + ")
)

outcomes <- c("production_participation", "log_selfprod_amount", "ihs_selfprod_amount")
hh_terms <- c("household_size_reconstructed", "child_share", "elderly_share", "female_share")

coef_rows <- list()
meta_rows <- list()
issues <- c()

for (outcome in outcomes) {
  for (spec_name in names(specs)) {
    f <- as.formula(paste(outcome, "~", specs[[spec_name]]))
    vars_needed <- all.vars(f)
    vars_needed <- unique(c(vars_needed, "xzc12_for_merge_final"))
    d <- data[complete.cases(data[, vars_needed, drop = FALSE]), ]
    if (nrow(d) < 100) {
      issues <- c(issues, paste0("- Skipped ", outcome, " / ", spec_name, ": fewer than 100 complete rows."))
      next
    }
    model <- lm(f, data = d)
    vc <- cluster_vcov(model, d$xzc12_for_merge_final)
    wald <- wald_test(model, vc, hh_terms)
    cluster_n <- length(unique(d$xzc12_for_merge_final))
    r2 <- summary(model)$r.squared
    coef_rows[[length(coef_rows) + 1]] <- tidy_hh_terms(model, vc, outcome, spec_name, nrow(d), cluster_n, r2, wald)
    meta_rows[[length(meta_rows) + 1]] <- data.frame(
      outcome = outcome,
      spec = spec_name,
      n = nrow(d),
      n_clusters = cluster_n,
      r_squared = r2,
      hhcomp_wald_chisq = wald$stat,
      hhcomp_wald_df = wald$df,
      hhcomp_wald_p = wald$p,
      stringsAsFactors = FALSE
    )
  }
}

coef_table <- do.call(rbind, coef_rows)
model_meta <- do.call(rbind, meta_rows)

write_csv(coef_table, path("outputs", "tables", "table2_baseline_separability.csv"))
write_csv(model_meta, path("outputs", "tables", "table2_baseline_wald_summary.csv"))
write_model_json(model_meta, path("outputs", "model_summaries", "model2_baseline_separability.json"))

log_lines <- c(
  "# Baseline Separability Tests",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Estimation Notes",
  "",
  "- Models are pooled cross-sectional OLS/LPM specifications estimated with base R.",
  "- Standard errors are clustered by `xzc12_for_merge_final` using `sandwich::vcovCL`.",
  "- No household, village, village-year, DID, or panel fixed effects are used.",
  "- Household-head/resource controls are median-imputed with missingness indicators where needed.",
  "- M2 and M3 require nonmissing survey market friction, POI friction, GAEZ controls, and province indicators.",
  "",
  "## Outputs",
  "",
  "- `outputs/tables/table2_baseline_separability.csv`",
  "- `outputs/tables/table2_baseline_wald_summary.csv`",
  "- `outputs/model_summaries/model2_baseline_separability.json`",
  "",
  "## Issues",
  "",
  if (length(issues) == 0) "- None." else issues
)
writeLines(log_lines, path("outputs", "logs", "baseline_separability_tests.md"), useBytes = TRUE)

message("Baseline separability tests completed.")
````

## `code/08_robustness_checks.R`

- Size: 7.1 KB
- Lines: 175

````r
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
````

## `code/09_appendix_market_friction_interactions.R`

- Size: 2.8 KB
- Lines: 65

````r
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
````

## `code/09_category_specific_tests.R`

- Size: 10.1 KB
- Lines: 295

````r
options(warn = 1)

root <- getwd()
dir.create(file.path(root, "outputs", "tables"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "figures"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "model_summaries"), recursive = TRUE, showWarnings = FALSE)
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
  if (length(terms) == 0) {
    return(list(stat = NA_real_, df = 0L, p = NA_real_))
  }
  b <- coefs[terms]
  V <- vcov_mat[terms, terms, drop = FALSE]
  invV <- tryCatch(solve(V), error = function(e) MASS::ginv(V))
  stat <- as.numeric(t(b) %*% invV %*% b)
  df <- length(terms)
  list(stat = stat, df = df, p = 1 - pchisq(stat, df))
}

json_escape <- function(x) {
  x <- gsub("\\\\", "\\\\\\\\", x)
  x <- gsub('"', '\\"', x)
  x <- gsub("\n", "\\\\n", x)
  x
}

write_model_json <- function(models_meta, file) {
  lines <- c("{", '  "models": [')
  for (i in seq_len(nrow(models_meta))) {
    r <- models_meta[i, ]
    comma <- if (i < nrow(models_meta)) "," else ""
    lines <- c(lines, paste0(
      "    {",
      '"food_category":"', json_escape(r$food_category), '",',
      '"food_category_label":"', json_escape(r$food_category_label), '",',
      '"outcome":"', json_escape(r$outcome), '",',
      '"n":', r$n, ",",
      '"n_clusters":', r$n_clusters, ",",
      '"r_squared":', signif(r$r_squared, 8), ",",
      '"hhcomp_wald_chisq":', signif(r$hhcomp_wald_chisq, 8), ",",
      '"hhcomp_wald_df":', r$hhcomp_wald_df, ",",
      '"hhcomp_wald_p":', signif(r$hhcomp_wald_p, 8), ",",
      '"nsi":', signif(r$nsi, 8),
      "}", comma
    ))
  }
  lines <- c(lines, "  ]", "}")
  writeLines(lines, file, useBytes = TRUE)
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

data$data_year <- factor(data$data_year)
data$provn_std <- factor(data$provn_std)

food_order <- c("zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo")
outcomes <- c("production_participation", "log_selfprod_amount", "ihs_selfprod_amount")
hh_terms <- c("household_size_reconstructed", "child_share", "elderly_share", "female_share")

hhcomp <- "household_size_reconstructed + child_share + elderly_share + female_share"
resources <- paste(
  c(
    "log1p_total_income_w_w99_imp", "log1p_total_income_w_w99_missing",
    "log1p_agri_business_income_w99_imp", "log1p_agri_business_income_w99_missing",
    "log1p_annual_expense_total_w99_imp", "log1p_annual_expense_total_w99_missing",
    "total_sown_area", "agricultural_labor_days", "offfarm_labor_days",
    "household_assets_count_proxy_imp", "household_assets_count_proxy_missing",
    "household_head_age_imp", "household_head_age_missing",
    "household_head_education_imp", "household_head_education_missing",
    "household_head_gender_male_imp", "household_head_gender_male_missing"
  ),
  collapse = " + "
)
controls <- paste(
  c(
    resources,
    "market_friction_survey", "poi_market_friction_lag1",
    "price_hedonic_imputed_w99_yuan_per_jin",
    "gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km",
    "risk_salience_z_5yr_sum", "governance_capacity_z_5yr_sum",
    "trust_signal_z_5yr_sum", "attention_z_5yr_sum",
    "factor(provn_std)", "factor(data_year)"
  ),
  collapse = " + "
)

test_rows <- list()
coef_rows <- list()
issues <- c()

for (cat in food_order) {
  d_cat0 <- data[data$food_category == cat, ]
  cat_label <- d_cat0$food_category_label[1]
  for (outcome in outcomes) {
    f <- as.formula(paste(outcome, "~", hhcomp, "+", controls))
    vars_needed <- unique(c(all.vars(f), "xzc12_for_merge_final"))
    d <- d_cat0[complete.cases(d_cat0[, vars_needed, drop = FALSE]), ]
    if (nrow(d) < 100) {
      issues <- c(issues, paste0("- Skipped ", cat, " / ", outcome, ": fewer than 100 complete rows."))
      next
    }
    if (length(unique(d[[outcome]])) < 2) {
      issues <- c(issues, paste0("- Skipped ", cat, " / ", outcome, ": outcome has fewer than 2 unique values."))
      next
    }
    model <- lm(f, data = d)
    vc <- cluster_vcov(model, d$xzc12_for_merge_final)
    wald <- wald_test(model, vc, hh_terms)
    cluster_n <- length(unique(d$xzc12_for_merge_final))
    r2 <- summary(model)$r.squared
    coefs <- coef(model)
    ses <- sqrt(diag(vc))

    get_coef <- function(term, suffix) {
      if (!term %in% names(coefs)) return(setNames(rep(NA_real_, 3), paste0(term, c("_coef", "_se", "_p"))))
      tval <- coefs[term] / ses[term]
      out <- c(coefs[term], ses[term], 2 * pnorm(abs(tval), lower.tail = FALSE))
      names(out) <- paste0(suffix, c("_coef", "_se", "_p"))
      out
    }
    c_household <- get_coef("household_size_reconstructed", "household_size")
    c_child <- get_coef("child_share", "child_share")
    c_elderly <- get_coef("elderly_share", "elderly_share")
    c_female <- get_coef("female_share", "female_share")

    test_rows[[length(test_rows) + 1]] <- data.frame(
      food_category = cat,
      food_category_label = cat_label,
      outcome = outcome,
      n = nrow(d),
      n_clusters = cluster_n,
      outcome_mean = mean(d[[outcome]], na.rm = TRUE),
      r_squared = r2,
      hhcomp_wald_chisq = wald$stat,
      hhcomp_wald_df = wald$df,
      hhcomp_wald_p = wald$p,
      t(c(c_household, c_child, c_elderly, c_female)),
      stringsAsFactors = FALSE
    )

    for (term in hh_terms) {
      if (!term %in% names(coefs)) next
      tval <- coefs[term] / ses[term]
      coef_rows[[length(coef_rows) + 1]] <- data.frame(
        food_category = cat,
        food_category_label = cat_label,
        outcome = outcome,
        term = term,
        estimate = coefs[term],
        std_error_cluster = ses[term],
        t_stat = tval,
        p_value = 2 * pnorm(abs(tval), lower.tail = FALSE),
        n = nrow(d),
        n_clusters = cluster_n,
        r_squared = r2,
        hhcomp_wald_chisq = wald$stat,
        hhcomp_wald_df = wald$df,
        hhcomp_wald_p = wald$p,
        stringsAsFactors = FALSE
      )
    }
  }
}

tests <- do.call(rbind, test_rows)
coef_table <- do.call(rbind, coef_rows)

tests$nsi <- NA_real_
for (outcome in unique(tests$outcome)) {
  idx <- tests$outcome == outcome
  avg <- mean(tests$hhcomp_wald_chisq[idx], na.rm = TRUE)
  tests$nsi[idx] <- tests$hhcomp_wald_chisq[idx] / avg
}
coef_table <- merge(
  coef_table,
  tests[, c("food_category", "outcome", "nsi")],
  by = c("food_category", "outcome"),
  all.x = TRUE,
  sort = FALSE
)

tests$food_category <- factor(tests$food_category, levels = food_order)
tests <- tests[order(tests$outcome, tests$food_category), ]
tests$food_category <- as.character(tests$food_category)

write_csv(tests, path("outputs", "tables", "table3_category_specific_tests.csv"))
write_csv(coef_table, path("outputs", "tables", "table3_category_specific_coefficients.csv"))
write_model_json(tests, path("outputs", "model_summaries", "model3_category_specific_tests.json"))

## Figure: NSI by category for the baseline participation outcome.
fig_data <- tests[tests$outcome == "production_participation", ]
fig_data <- fig_data[order(fig_data$nsi, decreasing = TRUE), ]
png(path("outputs", "figures", "figure2_nsi_by_category.png"), width = 1800, height = 1100, res = 180)
par(mar = c(8, 5, 4, 2))
cols <- ifelse(fig_data$hhcomp_wald_p < 0.05, "#2F6B9A", "#9AA7B1")
barplot(
  fig_data$nsi,
  names.arg = fig_data$food_category_label,
  las = 2,
  col = cols,
  border = NA,
  ylab = "NSI = category Wald / mean Wald",
  main = "Category-Specific Non-Separability Index",
  ylim = c(0, max(fig_data$nsi, na.rm = TRUE) * 1.18)
)
abline(h = 1, lty = 2, col = "#666666")
legend(
  "topright",
  legend = c("Wald p < 0.05", "Wald p >= 0.05"),
  fill = c("#2F6B9A", "#9AA7B1"),
  border = NA,
  bty = "n"
)
dev.off()

log_lines <- c(
  "# Category-Specific Separability Tests",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Estimation Notes",
  "",
  "- Each model is estimated separately by food category.",
  "- The control set mirrors the complete baseline M3 specification, except food-category indicators are not included within category-specific models.",
  "- Standard errors are clustered by `xzc12_for_merge_final`.",
  "- NSI is defined as category Wald chi-square divided by the mean Wald chi-square within the same outcome.",
  "",
  "## Outputs",
  "",
  "- `outputs/tables/table3_category_specific_tests.csv`",
  "- `outputs/tables/table3_category_specific_coefficients.csv`",
  "- `outputs/figures/figure2_nsi_by_category.png`",
  "- `outputs/model_summaries/model3_category_specific_tests.json`",
  "",
  "## Issues",
  "",
  if (length(issues) == 0) "- None." else issues
)
writeLines(log_lines, path("outputs", "logs", "category_specific_tests.md"), useBytes = TRUE)

message("Category-specific tests completed.")
````

## `code/10_appendix_iv_diagnostics.R`

- Size: 3.9 KB
- Lines: 107

````r
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
````

## `code/10_market_friction_interactions.R`

- Size: 13.7 KB
- Lines: 395

````r
options(warn = 1)

root <- getwd()
dir.create(file.path(root, "outputs", "tables"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "figures"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "model_summaries"), recursive = TRUE, showWarnings = FALSE)
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

find_interaction_name <- function(coef_names, term, friction_var) {
  candidates <- c(
    paste0(term, ":", friction_var),
    paste0(friction_var, ":", term)
  )
  hit <- candidates[candidates %in% coef_names]
  if (length(hit) == 0) return(NA_character_)
  hit[1]
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

json_escape <- function(x) {
  x <- gsub("\\\\", "\\\\\\\\", x)
  x <- gsub('"', '\\"', x)
  x <- gsub("\n", "\\\\n", x)
  x
}

json_number <- function(x) {
  if (is.na(x) || !is.finite(x)) return("null")
  as.character(signif(x, 8))
}

write_model_json <- function(models_meta, file) {
  lines <- c("{", '  "models": [')
  for (i in seq_len(nrow(models_meta))) {
    r <- models_meta[i, ]
    comma <- if (i < nrow(models_meta)) "," else ""
    lines <- c(lines, paste0(
      "    {",
      '"outcome":"', json_escape(r$outcome), '",',
      '"friction_spec":"', json_escape(r$friction_spec), '",',
      '"friction_variable":"', json_escape(r$friction_variable), '",',
      '"n":', r$n, ",",
      '"n_clusters":', r$n_clusters, ",",
      '"r_squared":', json_number(r$r_squared), ",",
      '"interaction_wald_chisq":', json_number(r$interaction_wald_chisq), ",",
      '"interaction_wald_df":', r$interaction_wald_df, ",",
      '"interaction_wald_p":', json_number(r$interaction_wald_p),
      "}", comma
    ))
  }
  lines <- c(lines, "  ]", "}")
  writeLines(lines, file, useBytes = TRUE)
}

safe_term_stats <- function(coefs, ses, term, out_prefix) {
  if (is.na(term) || !term %in% names(coefs) || is.na(coefs[term])) {
    out <- rep(NA_real_, 3)
  } else {
    tval <- coefs[term] / ses[term]
    out <- c(coefs[term], ses[term], 2 * pnorm(abs(tval), lower.tail = FALSE))
  }
  names(out) <- paste0(out_prefix, c("_coef", "_se", "_p"))
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

outcomes <- c("production_participation", "log_selfprod_amount", "ihs_selfprod_amount")
hh_terms <- c("household_size_reconstructed", "child_share", "elderly_share", "female_share")
hh_labels <- c(
  household_size_reconstructed = "household_size",
  child_share = "child_share",
  elderly_share = "elderly_share",
  female_share = "female_share"
)

resources <- paste(
  c(
    "log1p_total_income_w_w99_imp", "log1p_total_income_w_w99_missing",
    "log1p_agri_business_income_w99_imp", "log1p_agri_business_income_w99_missing",
    "log1p_annual_expense_total_w99_imp", "log1p_annual_expense_total_w99_missing",
    "total_sown_area", "agricultural_labor_days", "offfarm_labor_days",
    "household_assets_count_proxy_imp", "household_assets_count_proxy_missing",
    "household_head_age_imp", "household_head_age_missing",
    "household_head_education_imp", "household_head_education_missing",
    "household_head_gender_male_imp", "household_head_gender_male_missing"
  ),
  collapse = " + "
)

base_controls <- paste(
  c(
    resources,
    "price_hedonic_imputed_w99_yuan_per_jin",
    "gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km",
    "risk_salience_z_5yr_sum", "governance_capacity_z_5yr_sum",
    "trust_signal_z_5yr_sum", "attention_z_5yr_sum",
    "factor(food_category)", "factor(provn_std)", "factor(data_year)"
  ),
  collapse = " + "
)

friction_specs <- list(
  survey_market_friction = list(
    friction_var = "market_friction_survey",
    friction_label = "Survey market friction",
    extra_controls = c("poi_market_friction_lag1")
  ),
  poi_market_friction = list(
    friction_var = "poi_market_friction_lag1",
    friction_label = "Lagged POI market friction",
    extra_controls = c("market_friction_survey")
  ),
  combined_market_friction = list(
    friction_var = "combined_market_friction",
    friction_label = "Combined survey/POI market friction",
    extra_controls = character(0)
  )
)

model_rows <- list()
coef_rows <- list()
issues <- c()
main_margin_model <- NULL
main_margin_vcov <- NULL
main_margin_data <- NULL

for (spec_name in names(friction_specs)) {
  spec <- friction_specs[[spec_name]]
  friction_var <- spec$friction_var
  interaction_part <- paste0("(", paste(hh_terms, collapse = " + "), ") * ", friction_var)
  controls <- paste(c(base_controls, spec$extra_controls), collapse = " + ")

  for (outcome in outcomes) {
    f <- as.formula(paste(outcome, "~", interaction_part, "+", controls))
    vars_needed <- unique(c(all.vars(f), "xzc12_for_merge_final"))
    missing_vars <- setdiff(vars_needed, names(data))
    if (length(missing_vars) > 0) {
      issues <- c(issues, paste0(
        "- Skipped ", outcome, " / ", spec_name,
        ": missing variables: ", paste(missing_vars, collapse = ", ")
      ))
      next
    }
    d <- data[complete.cases(data[, vars_needed, drop = FALSE]), ]
    if (nrow(d) < 100) {
      issues <- c(issues, paste0("- Skipped ", outcome, " / ", spec_name, ": fewer than 100 complete rows."))
      next
    }
    if (length(unique(d[[outcome]])) < 2) {
      issues <- c(issues, paste0("- Skipped ", outcome, " / ", spec_name, ": outcome has fewer than 2 unique values."))
      next
    }

    model <- lm(f, data = d)
    vc <- cluster_vcov(model, d$xzc12_for_merge_final)
    coefs <- coef(model)
    ses <- sqrt(diag(vc))
    interaction_coef_names <- vapply(
      hh_terms,
      function(term) find_interaction_name(names(coefs), term, friction_var),
      character(1)
    )
    wald <- wald_test(model, vc, interaction_coef_names)
    cluster_n <- length(unique(d$xzc12_for_merge_final))
    r2 <- summary(model)$r.squared

    main_term_stats <- unlist(lapply(hh_terms, function(term) {
      safe_term_stats(coefs, ses, term, hh_labels[term])
    }))
    interaction_stats <- unlist(lapply(hh_terms, function(term) {
      safe_term_stats(
        coefs,
        ses,
        interaction_coef_names[term],
        paste0(hh_labels[term], "_x_friction")
      )
    }))
    friction_stats <- safe_term_stats(coefs, ses, friction_var, "friction_main")

    model_rows[[length(model_rows) + 1]] <- data.frame(
      friction_spec = spec_name,
      friction_label = spec$friction_label,
      friction_variable = friction_var,
      outcome = outcome,
      n = nrow(d),
      n_clusters = cluster_n,
      outcome_mean = mean(d[[outcome]], na.rm = TRUE),
      friction_mean = mean(d[[friction_var]], na.rm = TRUE),
      friction_sd = sd(d[[friction_var]], na.rm = TRUE),
      r_squared = r2,
      interaction_wald_chisq = wald$stat,
      interaction_wald_df = wald$df,
      interaction_wald_p = wald$p,
      t(c(friction_stats, main_term_stats, interaction_stats)),
      stringsAsFactors = FALSE
    )

    for (term in hh_terms) {
      interaction_name <- interaction_coef_names[term]
      if (is.na(interaction_name) || !interaction_name %in% names(coefs) || is.na(coefs[interaction_name])) next
      tval <- coefs[interaction_name] / ses[interaction_name]
      coef_rows[[length(coef_rows) + 1]] <- data.frame(
        friction_spec = spec_name,
        friction_label = spec$friction_label,
        friction_variable = friction_var,
        outcome = outcome,
        term = term,
        coefficient_name = interaction_name,
        estimate = coefs[interaction_name],
        std_error_cluster = ses[interaction_name],
        t_stat = tval,
        p_value = 2 * pnorm(abs(tval), lower.tail = FALSE),
        n = nrow(d),
        n_clusters = cluster_n,
        r_squared = r2,
        interaction_wald_chisq = wald$stat,
        interaction_wald_df = wald$df,
        interaction_wald_p = wald$p,
        stringsAsFactors = FALSE
      )
    }

    if (spec_name == "survey_market_friction" && outcome == "production_participation") {
      main_margin_model <- model
      main_margin_vcov <- vc
      main_margin_data <- d
    }
  }
}

table4 <- do.call(rbind, model_rows)
coef_table <- do.call(rbind, coef_rows)

write_csv(table4, path("outputs", "tables", "table4_market_friction_interactions.csv"))
write_csv(coef_table, path("outputs", "tables", "table4_market_friction_interaction_coefficients.csv"))
write_model_json(table4, path("outputs", "model_summaries", "model4_market_interactions.json"))

## Figure: marginal effects over survey-based market friction for the main
## production-participation model.
if (!is.null(main_margin_model)) {
  coefs <- coef(main_margin_model)
  vc <- main_margin_vcov
  friction_var <- "market_friction_survey"
  x_grid <- seq(
    quantile(main_margin_data[[friction_var]], 0.05, na.rm = TRUE),
    quantile(main_margin_data[[friction_var]], 0.95, na.rm = TRUE),
    length.out = 100
  )
  plot_terms <- hh_terms
  plot_labels <- c("Household size", "Child share", "Elderly share", "Female share")

  png(path("outputs", "figures", "figure3_market_friction_margins.png"), width = 1800, height = 1300, res = 180)
  par(mfrow = c(2, 2), mar = c(4.5, 4.5, 3, 1.2))
  for (i in seq_along(plot_terms)) {
    term <- plot_terms[i]
    inter <- find_interaction_name(names(coefs), term, friction_var)
    if (is.na(inter)) {
      plot.new()
      title(plot_labels[i])
      next
    }
    b0 <- coefs[term]
    b1 <- coefs[inter]
    effect <- b0 + b1 * x_grid
    var_effect <- vc[term, term] + x_grid^2 * vc[inter, inter] + 2 * x_grid * vc[term, inter]
    se_effect <- sqrt(pmax(var_effect, 0))
    upper <- effect + 1.96 * se_effect
    lower <- effect - 1.96 * se_effect
    ylim <- range(c(lower, upper, 0), na.rm = TRUE)
    plot(
      x_grid, effect,
      type = "l",
      lwd = 2,
      col = "#2F6B9A",
      xlab = "Survey market friction",
      ylab = "Marginal effect",
      main = plot_labels[i],
      ylim = ylim
    )
    polygon(
      c(x_grid, rev(x_grid)),
      c(upper, rev(lower)),
      col = adjustcolor("#2F6B9A", alpha.f = 0.18),
      border = NA
    )
    lines(x_grid, effect, lwd = 2, col = "#2F6B9A")
    abline(h = 0, lty = 2, col = "#777777")
  }
  dev.off()
}

log_lines <- c(
  "# Market-Friction Interaction Models",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Estimation Notes",
  "",
  "- Models are pooled cross-sectional OLS/LPM specifications estimated with base R.",
  "- Standard errors are clustered by `xzc12_for_merge_final` using `sandwich::vcovCL`.",
  "- No household, village, village-year, DID, or panel fixed effects are used.",
  "- Each model includes household composition, the selected market-friction variable, and the four household-composition × market-friction interactions.",
  "- The control set follows the complete baseline M3 structure: household resources, land, labor, assets, household-head controls, hedonic food price, GAEZ controls, county text indicators, food-category indicators, province indicators, and survey-year indicators.",
  "- Survey-friction models additionally control for lagged POI friction; POI-friction models additionally control for survey friction; combined-friction models do not add the component indices separately.",
  "",
  "## Outputs",
  "",
  "- `outputs/tables/table4_market_friction_interactions.csv`",
  "- `outputs/tables/table4_market_friction_interaction_coefficients.csv`",
  "- `outputs/figures/figure3_market_friction_margins.png`",
  "- `outputs/model_summaries/model4_market_interactions.json`",
  "",
  "## Issues",
  "",
  if (length(issues) == 0) "- None." else issues
)
writeLines(log_lines, path("outputs", "logs", "market_friction_interactions.md"), useBytes = TRUE)

message("Market-friction interaction models completed.")
````

## `code/11_compile_revised_results_report.R`

- Size: 19.6 KB
- Lines: 353

````r
source("code/00_setup.R")

read_if_exists <- function(file) {
  if (!file.exists(file)) return(data.frame())
  read_csv(file)
}

fmt <- function(x, digits = 3) {
  vapply(x, function(z) {
    if (is.na(z) || !is.finite(z)) return("NA")
    sprintf(paste0("%.", digits, "f"), z)
  }, character(1))
}

fmtp <- function(x) {
  vapply(x, function(z) {
    if (is.na(z) || !is.finite(z)) return("NA")
    if (z < 0.001) return("<0.001")
    sprintf("%.3f", z)
  }, character(1))
}

table2 <- read_if_exists(path("outputs", "tables", "table2_common_sample_baseline.csv"))
table3 <- read_if_exists(path("outputs", "tables", "table3_baseline_coefficients_margins.csv"))
table4 <- read_if_exists(path("outputs", "tables", "table4_category_specific_nsi.csv"))
table5 <- read_if_exists(path("outputs", "tables", "table5_two_part_model.csv"))
table6 <- read_if_exists(path("outputs", "tables", "table6_alternative_composition_outcomes.csv"))
table7 <- read_if_exists(path("outputs", "tables", "table7_leave_one_province.csv"))
table8 <- read_if_exists(path("outputs", "tables", "table8_household_composition_permutation.csv"))
tableA <- read_if_exists(path("outputs", "tables", "tableA_market_friction_interactions_appendix.csv"))
tableB <- read_if_exists(path("outputs", "tables", "tableB_iv_diagnostics_appendix.csv"))
tableC <- read_if_exists(path("outputs", "tables", "tableC_price_robustness.csv"))
tableD <- read_if_exists(path("outputs", "tables", "tableD_category_definition_audits.csv"))
sample_summary <- read_if_exists(path("outputs", "tables", "table1_sample_summary_revised.csv"))
by_year <- read_if_exists(path("outputs", "tables", "table1_observations_by_year_revised.csv"))
by_cat <- read_if_exists(path("outputs", "tables", "table1_observations_by_category_revised.csv"))
missingness <- read_if_exists(path("outputs", "tables", "table1_missingness_revised.csv"))

## Figure 1 conceptual framework placeholder.
png(path("outputs", "figures", "figure1_conceptual_framework_placeholder.png"), width = 1800, height = 900, res = 180)
par(mar = c(1, 1, 3, 1))
plot.new()
title("Conceptual Framework: Household Composition and Self-Provisioning Entry")
box <- function(x1, y1, x2, y2, label, col) {
  rect(x1, y1, x2, y2, col = col, border = "#333333", lwd = 1.5)
  text((x1 + x2) / 2, (y1 + y2) / 2, label, cex = 0.9)
}
box(0.05, 0.55, 0.27, 0.78, "Household\ncomposition", "#DCEAF7")
box(0.39, 0.55, 0.61, 0.78, "Self-provisioning\nentry", "#E9F3E4")
box(0.73, 0.55, 0.95, 0.78, "Category-specific\nheterogeneity", "#F6E4D7")
box(0.39, 0.18, 0.61, 0.38, "Controls:\nresources, prices,\nmarkets, GAEZ,\ntext, province, year", "#EFEFEF")
arrows(0.27, 0.665, 0.39, 0.665, length = 0.08, lwd = 2)
arrows(0.61, 0.665, 0.73, 0.665, length = 0.08, lwd = 2)
arrows(0.50, 0.38, 0.50, 0.55, length = 0.08, lwd = 2, lty = 2)
dev.off()

main_m3 <- table2[table2$outcome == "production_participation" & table2$spec == "M3", ]
log_m3 <- table2[table2$outcome == "log_selfprod_amount" & table2$spec == "M3", ]
ihs_m3 <- table2[table2$outcome == "ihs_selfprod_amount" & table2$spec == "M3", ]
two_part_part2 <- table5[table5$model_part == "Part 2", ]
two_part_part2_sig <- nrow(two_part_part2) > 0 && two_part_part2$hhcomp_wald_p[1] < 0.05

strong_cats <- table4[table4$signal_label == "Strong", ]
weak_cats <- table4[table4$signal_label == "Weak", ]
top_cats <- table4[order(table4$nsi, decreasing = TRUE), ]

loo_all_sig <- if (nrow(table7) > 0) all(table7$wald_p < 0.05, na.rm = TRUE) else NA
loo_min <- if (nrow(table7) > 0) min(table7$wald_chisq, na.rm = TRUE) else NA
loo_max <- if (nrow(table7) > 0) max(table7$wald_chisq, na.rm = TRUE) else NA
loo_infl <- if (nrow(table7) > 0) table7$dropped_province[which.min(table7$wald_chisq)] else "NA"

required_files <- c(
  "outputs/tables/table2_common_sample_baseline.csv",
  "outputs/tables/table3_baseline_coefficients_margins.csv",
  "outputs/tables/table4_category_specific_nsi.csv",
  "outputs/tables/table5_two_part_model.csv",
  "outputs/tables/table6_alternative_composition_outcomes.csv",
  "outputs/tables/table7_leave_one_province.csv",
  "outputs/tables/table8_household_composition_permutation.csv",
  "outputs/figures/figure2_nsi_by_category.png",
  "outputs/logs/revised_data_merge_log.md",
  "outputs/logs/common_sample_log.md",
  "outputs/logs/roulei_split_audit.md",
  "outputs/logs/youzhi_definition_audit.md"
)
missing_required <- required_files[!file.exists(path(required_files))]

inventory <- data.frame(
  Item = c(
    "Table 1", "Table 2", "Table 3", "Table 4", "Table 5", "Table 6", "Table 7", "Table 8",
    "Appendix Table A", "Appendix Table B", "Appendix Table C", "Appendix Table D",
    "Figure 1", "Figure 2", "Figure 3", "Figure 4"
  ),
  File = c(
    "outputs/tables/table1_descriptive_statistics_revised.csv",
    "outputs/tables/table2_common_sample_baseline.csv",
    "outputs/tables/table3_baseline_coefficients_margins.csv",
    "outputs/tables/table4_category_specific_nsi.csv",
    "outputs/tables/table5_two_part_model.csv",
    "outputs/tables/table6_alternative_composition_outcomes.csv",
    "outputs/tables/table7_leave_one_province.csv",
    "outputs/tables/table8_household_composition_permutation.csv",
    "outputs/tables/tableA_market_friction_interactions_appendix.csv",
    "outputs/tables/tableB_iv_diagnostics_appendix.csv",
    "outputs/tables/tableC_price_robustness.csv",
    "outputs/tables/tableD_category_definition_audits.csv",
    "outputs/figures/figure1_conceptual_framework_placeholder.png",
    "outputs/figures/figure2_nsi_by_category.png",
    "outputs/figures/figure3_household_composition_coefficients.png",
    "outputs/figures/figure4_household_composition_permutation.png"
  ),
  Placement = c(rep("Main text", 8), rep("Appendix", 4), rep("Main text", 4)),
  Purpose = c(
    "Descriptive statistics and sample checks",
    "Common-sample baseline separability tests",
    "Household-composition coefficient interpretation",
    "Category-specific NSI",
    "Two-part entry versus conditional intensity",
    "Alternative composition and outcomes",
    "Province leave-one-out",
    "Household-composition permutation placebo",
    "Market-friction interactions",
    "IV diagnostics",
    "Price robustness",
    "Category-definition audits",
    "Conceptual framework",
    "NSI ranking by category",
    "Baseline coefficient plot",
    "Permutation distribution"
  ),
  Status = "",
  Human_review = c(rep("No", 11), "Yes", rep("No", 4)),
  stringsAsFactors = FALSE
)
inventory$Status <- ifelse(file.exists(path(inventory$File)), "Generated", "Missing")

inv_lines <- c(
  "| Item | File path | Placement | Purpose | Status | Human review |",
  "|---|---|---|---|---|---|",
  paste0("| ", inventory$Item, " | `", inventory$File, "` | ", inventory$Placement, " | ", inventory$Purpose, " | ", inventory$Status, " | ", inventory$Human_review, " |")
)

sample_lines <- if (nrow(sample_summary) > 0) paste0("- ", sample_summary$item, ": ", sample_summary$value) else "- Sample summary unavailable."
year_lines <- if (nrow(by_year) > 0) paste0("- ", by_year$data_year, ": ", by_year$n_rows) else "- Year summary unavailable."
cat_lines <- if (nrow(by_cat) > 0) paste0("- ", by_cat$food_category, " / ", by_cat$food_category_label, ": ", by_cat$n_rows) else "- Category summary unavailable."
display_var <- function(x) {
  x <- sub("yuan_per_jin$", "yuan_per_kg", x)
  x <- ifelse(x == "village_price_category_median", "village_price_category_median_yuan_per_kg", x)
  x
}

miss_lines <- if (nrow(missingness) > 0) {
  paste0("- ", missingness$module, " / `", display_var(missingness$variable), "`: ", missingness$n_missing, " missing")
} else "- Missingness summary unavailable."

coeff_m3 <- table3[table3$outcome == "production_participation" & table3$spec == "M3", ]
coeff_lines <- if (nrow(coeff_m3) > 0) {
  paste0(
    "- `", coeff_m3$term, "`: beta = ", fmt(coeff_m3$estimate, 4),
    ", SE = ", fmt(coeff_m3$std_error_cluster, 4),
    ", p = ", fmtp(coeff_m3$p_value),
    ", direction = ", coeff_m3$direction,
    ", stable across M0-M3 = ", coeff_m3$sign_stable_across_M0_M3
  )
} else "- Coefficient table unavailable."

cat_report_lines <- if (nrow(table4) > 0) {
  paste0(
    "- ", table4$food_category_label, ": Wald = ", fmt(table4$hhcomp_wald_chisq),
    ", p = ", fmtp(table4$hhcomp_wald_p),
    ", NSI = ", fmt(table4$nsi),
    ", signal = ", table4$signal_label,
    ", drivers = ", table4$main_coefficient_drivers
  )
} else "- Category NSI table unavailable."

two_part_lines <- if (nrow(table5) > 0) {
  paste0(
    "- ", table5$model_part, " (", table5$sample_definition, ", outcome `", table5$outcome, "`): Wald = ",
    fmt(table5$hhcomp_wald_chisq), ", p = ", fmtp(table5$hhcomp_wald_p),
    ", N = ", table5$n
  )
} else "- Two-part table unavailable."

robust_lines <- if (nrow(table6) > 0) {
  paste0("- ", table6$composition_spec, " / `", table6$outcome, "`: Wald = ", fmt(table6$wald_chisq), ", p = ", fmtp(table6$wald_p), ", N = ", table6$n)
} else "- Robustness table unavailable."

market_lines <- if (nrow(tableA) > 0) {
  paste0("- ", tableA$friction_spec, " / `", tableA$outcome, "`: interaction Wald = ", fmt(tableA$interaction_wald_chisq), ", p = ", fmtp(tableA$interaction_wald_p), ".")
} else "- Market interaction appendix table unavailable."

iv_lines <- if (nrow(tableB) > 0) {
  paste0("- ", tableB$iv_spec, ": corr = ", fmt(tableB$correlation_with_market_friction_survey), ", min F = ", fmt(tableB$min_first_stage_F), ", median F = ", fmt(tableB$median_first_stage_F), ", weak = ", tableB$weak_iv_flag, ".")
} else "- IV diagnostics table unavailable."

price_lines <- if (nrow(tableC) > 0) {
  paste0("- ", tableC$price_spec, ": Wald = ", fmt(tableC$hhcomp_wald_chisq), ", p = ", fmtp(tableC$hhcomp_wald_p), ", N = ", tableC$n, ".")
} else "- Price robustness table unavailable."

human_flags <- c(
  if (nrow(tableD) > 0 && any(tableD$audit_item == "roulei_split" & tableD$human_review_required)) "- roulei split not performed; raw detail exists but analysis-ready split outcome is not cleanly available." else NULL,
  if (nrow(tableD) > 0 && any(tableD$audit_item == "youzhi_definition" & tableD$human_review_required)) "- youzhi definition requires human review before strong substantive claims about oils." else NULL,
  if (nrow(tableB) > 0 && any(tableB$weak_iv_flag)) "- IV first stages are weak; IV remains appendix-only." else NULL,
  if (nrow(tableA) > 0 && all(tableA$interaction_wald_p >= 0.05, na.rm = TRUE)) "- Market-friction interactions are non-significant." else NULL,
  "- commercialization_rate denominator unclear; not included in revised rerun."
)

report <- c(
  "# Paper 1 Revised Results Package",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## 1. Executive summary",
  "",
  paste0("- MAIN RESULT: household composition predicts self-provisioning participation in the common-sample M3 model (Wald = ", fmt(main_m3$hhcomp_wald_chisq[1]), ", p = ", fmtp(main_m3$hhcomp_wald_p[1]), ")."),
  paste0("- MAIN RESULT: full-sample intensive amount margins are weaker (`log_selfprod_amount` p = ", fmtp(log_m3$hhcomp_wald_p[1]), "; `ihs_selfprod_amount` p = ", fmtp(ihs_m3$hhcomp_wald_p[1]), "), so participation remains the clearest margin."),
  if (two_part_part2_sig) paste0("- SUPPORTING RESULT: the formal two-part model also finds a conditional-intensity signal among self-provisioning entrants (Part 2 p = ", fmtp(two_part_part2$hhcomp_wald_p[1]), "), so the intensive-margin conclusion should be stated cautiously.") else "- SUPPORTING RESULT: the two-part conditional-intensity model is weak, reinforcing the entry-margin interpretation.",
  paste0("- MAIN RESULT: category heterogeneity is strong; top NSI categories are ", paste(head(top_cats$food_category_label, 5), collapse = ", "), "."),
  "- SUPPORTING RESULT: self-sufficiency and alternative household-composition specifications are reported as robustness checks.",
  paste0("- ROBUSTNESS RESULT: leave-one-province baseline Wald remains significant in all drops = ", loo_all_sig, "."),
  "- APPENDIX / EXPLORATORY RESULT: market-friction interactions and IV diagnostics are appendix-only.",
  if (nrow(tableB) > 0 && any(tableB$weak_iv_flag)) "- FAILED OR WEAK EVIDENCE: IV first stages remain weak." else "- APPENDIX / EXPLORATORY RESULT: IV first stages require review.",
  "- HUMAN REVIEW REQUIRED: roulei split feasibility, youzhi definition, and commercialization-rate denominator.",
  "",
  "## 2. Data and sample checks",
  "",
  "### Unit and outlier handling",
  "",
  "- Food quantities are household totals in kg/month/household after converting from jin/month with `kg = jin * 0.5`.",
  "- Unit values are yuan/kg after converting from yuan/jin with `yuan/kg = yuan/jin * 2`; legacy model aliases ending in `_yuan_per_jin` are retained only for script compatibility.",
  "- Food quantity outliers were excluded by food-category P99.5 thresholds; the cleaned model file drops 312 category-level rows and retains all 3,565 households.",
  "- Main outcome transforms, `log_selfprod_amount` and `ihs_selfprod_amount`, are recomputed from `selfprod_kg_month`.",
  "",
  sample_lines,
  "",
  "### Observations by data_year",
  "",
  year_lines,
  "",
  "### Observations by food_category",
  "",
  cat_lines,
  "",
  "### Missingness by core variables",
  "",
  miss_lines,
  "",
  paste0("- M0-M3 common sample constructed: ", nrow(main_m3) > 0),
  paste0("- Common-sample N: ", ifelse(nrow(main_m3) > 0, main_m3$n[1], NA)),
  paste0("- Common-sample cluster count: ", ifelse(nrow(main_m3) > 0, main_m3$n_clusters[1], NA)),
  "",
  "## 3. Main baseline results",
  "",
  "- Table: `outputs/tables/table2_common_sample_baseline.csv`",
  "- Model summary: `outputs/model_summaries/model2_common_sample_baseline.json`",
  "",
  paste0("- `production_participation`: Wald = ", fmt(main_m3$hhcomp_wald_chisq[1]), ", df = ", main_m3$hhcomp_wald_df[1], ", p = ", fmtp(main_m3$hhcomp_wald_p[1]), ", N = ", main_m3$n[1], "."),
  paste0("- `log_selfprod_amount`: Wald = ", fmt(log_m3$hhcomp_wald_chisq[1]), ", p = ", fmtp(log_m3$hhcomp_wald_p[1]), "."),
  paste0("- `ihs_selfprod_amount`: Wald = ", fmt(ihs_m3$hhcomp_wald_chisq[1]), ", p = ", fmtp(ihs_m3$hhcomp_wald_p[1]), "."),
  "",
  "Interpretation: The evidence rejects separability restrictions on the self-provisioning participation margin, but provides weaker evidence on the self-production quantity margin. This is a reduced-form association, not a causal treatment effect.",
  "",
  "## 4. Household-composition coefficient interpretation",
  "",
  "- Table: `outputs/tables/table3_baseline_coefficients_margins.csv`",
  "- Figure: `outputs/figures/figure3_household_composition_coefficients.png`",
  "",
  coeff_lines,
  "",
  "## 5. Category-specific non-separability and NSI",
  "",
  "- Table: `outputs/tables/table4_category_specific_nsi.csv`",
  "- Figure: `outputs/figures/figure2_nsi_by_category.png`",
  "",
  paste0("- Strong categories: ", ifelse(nrow(strong_cats) > 0, paste(strong_cats$food_category_label, collapse = ", "), "none")),
  paste0("- Weak categories: ", ifelse(nrow(weak_cats) > 0, paste(weak_cats$food_category_label, collapse = ", "), "none")),
  "",
  cat_report_lines,
  "",
  "Possible substantive explanation: the signal is concentrated in categories where households may make discrete entry decisions into self-provisioning. Data-definition concerns remain for `youzhi` and the combined `roulei` category.",
  "",
  "## 6. Two-part model: entry versus conditional intensity",
  "",
  "- Table: `outputs/tables/table5_two_part_model.csv`",
  "",
  two_part_lines,
  "",
  if (two_part_part2_sig) "Interpretation: Part 1 is significant and Part 2 is also significant at the 5% level. The clearest main result remains entry into self-provisioning, while the conditional-intensity result should be treated as supporting but more cautious evidence because full-sample log/IHS amount models are weaker." else "Interpretation: Part 1 is significant and Part 2 is weak, so the main non-separability signal operates through entry into self-provisioning rather than conditional intensity.",
  "",
  "## 7. Robustness checks",
  "",
  "### 7.1 Alternative household composition and outcomes",
  "",
  robust_lines,
  "",
  "### 7.2 Province leave-one-out",
  "",
  paste0("- Minimum leave-one-province Wald: ", fmt(loo_min)),
  paste0("- Maximum leave-one-province Wald: ", fmt(loo_max)),
  paste0("- All leave-one-province estimates remain significant: ", loo_all_sig),
  paste0("- Most influential drop by minimum Wald: ", loo_infl),
  "",
  "### 7.3 Household-composition permutation placebo",
  "",
  if (nrow(table8) > 0) paste0("- Permutations: ", table8$n_draws[1], "; true Wald = ", fmt(table8$true_wald_chisq[1]), "; placebo mean = ", fmt(table8$placebo_mean[1]), "; placebo P95 = ", fmt(table8$placebo_p95[1]), "; randomization p = ", fmtp(table8$randomization_p_value[1]), ".") else "- Permutation table unavailable.",
  "",
  "## 8. Appendix mechanism diagnostics",
  "",
  "### 8.1 Market-friction interactions",
  "",
  market_lines,
  "",
  "Default interpretation: Market-friction interactions do not provide strong support for a cross-sectional amplification mechanism if the p-values remain weak.",
  "",
  "### 8.2 IV diagnostics",
  "",
  iv_lines,
  "",
  "Default interpretation: IV results are reported as diagnostics and should not be used as the main identification basis when first stages are weak.",
  "",
  "## 9. Price robustness",
  "",
  price_lines,
  "",
  "Interpretation: Compare Wald p-values across no-price, hedonic-price, observed-price-only, and county-median-price specifications to assess dependence on price imputation.",
  "",
  "## 10. Category-definition audits",
  "",
  if (nrow(tableD) > 0) paste0("- ", tableD$audit_item, ": ", tableD$status, "; decision: ", tableD$decision) else "- Category definition audit unavailable.",
  "",
  "## 11. Table and figure inventory",
  "",
  inv_lines,
  "",
  "## 12. Human-review flags",
  "",
  human_flags,
  "",
  if (length(missing_required) == 0) "Rerun complete: all required completion-criteria files exist." else paste0("Rerun incomplete: missing required output `", missing_required, "`."),
  "",
  "## 13. Recommended manuscript language",
  "",
  if (two_part_part2_sig) {
    "The results indicate that household composition significantly predicts category-specific self-provisioning participation, providing reduced-form evidence inconsistent with separability. The clearest evidence is on the extensive margin: household composition predicts whether households enter self-provisioning, while full-sample quantity-margin tests are weaker. A formal two-part model also suggests some conditional-intensity association among households that enter self-provisioning, so the intensive-margin evidence should be interpreted cautiously rather than dismissed. The category-specific analysis shows that non-separability is concentrated in eggs, oils, vegetables, fruits, and beans, rather than being uniform across food groups. Market-friction interactions and IV diagnostics provide weaker support for the market-friction amplification mechanism and are therefore interpreted as exploratory."
  } else {
    "The results indicate that household composition significantly predicts category-specific self-provisioning participation, providing reduced-form evidence inconsistent with separability. This evidence is strongest on the extensive margin: household composition predicts whether households enter self-provisioning, while conditional quantity responses are weaker. The category-specific analysis shows that non-separability is concentrated in eggs, oils, vegetables, fruits, and beans, rather than being uniform across food groups. Market-friction interactions and IV diagnostics provide weaker support for the market-friction amplification mechanism and are therefore interpreted as exploratory."
  }
)

writeLines(report, path("outputs", "reports", "paper1_revised_results_package.md"), useBytes = TRUE)

message("Revised results report compiled.")
````

## `code/11_iv_market_friction_models.R`

- Size: 16.1 KB
- Lines: 456

````r
options(warn = 1)

root <- getwd()
dir.create(file.path(root, "outputs", "tables"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "model_summaries"), recursive = TRUE, showWarnings = FALSE)
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

safe_lm_coef_row <- function(model, vcov_mat, term) {
  coefs <- coef(model)
  ses <- sqrt(diag(vcov_mat))
  if (!term %in% names(coefs) || is.na(coefs[term])) {
    return(c(estimate = NA_real_, std_error_cluster = NA_real_, t_stat = NA_real_, p_value = NA_real_))
  }
  est <- as.numeric(coefs[term])
  se <- as.numeric(ses[term])
  tval <- est / se
  c(
    estimate = est,
    std_error_cluster = se,
    t_stat = tval,
    p_value = 2 * pnorm(abs(tval), lower.tail = FALSE)
  )
}

full_rank_matrix <- function(M, tol = 1e-10) {
  M <- as.matrix(M)
  q <- qr(M, tol = tol)
  keep <- sort(q$pivot[seq_len(q$rank)])
  M[, keep, drop = FALSE]
}

iv_2sls <- function(y, X, Z, cluster) {
  X <- full_rank_matrix(X)
  Z <- full_rank_matrix(Z)
  y <- as.numeric(y)
  n <- nrow(X)
  k <- ncol(X)
  G <- length(unique(cluster))

  ZTZ_inv <- MASS::ginv(crossprod(Z))
  XZ <- crossprod(X, Z)
  ZX <- t(XZ)
  A <- XZ %*% ZTZ_inv %*% ZX
  A_inv <- MASS::ginv(A)
  beta <- A_inv %*% XZ %*% ZTZ_inv %*% crossprod(Z, y)
  beta <- as.numeric(beta)
  names(beta) <- colnames(X)

  resid <- y - as.numeric(X %*% beta)
  S <- matrix(0, ncol(Z), ncol(Z))
  for (g in unique(cluster)) {
    idx <- cluster == g
    Zg <- Z[idx, , drop = FALSE]
    ug <- resid[idx]
    S <- S + crossprod(Zg, ug %*% t(ug) %*% Zg)
  }
  V <- A_inv %*% XZ %*% ZTZ_inv %*% S %*% ZTZ_inv %*% ZX %*% A_inv
  if (G > 1 && n > k) {
    V <- V * (G / (G - 1)) * ((n - 1) / (n - k))
  }
  rownames(V) <- colnames(V) <- colnames(X)
  r2 <- 1 - sum(resid^2) / sum((y - mean(y))^2)
  list(beta = beta, vcov = V, n = n, k = k, n_clusters = G, r_squared = r2)
}

json_escape <- function(x) {
  x <- gsub("\\\\", "\\\\\\\\", x)
  x <- gsub('"', '\\"', x)
  x <- gsub("\n", "\\\\n", x)
  x
}

json_number <- function(x) {
  if (is.na(x) || !is.finite(x)) return("null")
  as.character(signif(x, 8))
}

write_model_json <- function(meta, file) {
  lines <- c("{", '  "models": [')
  for (i in seq_len(nrow(meta))) {
    r <- meta[i, ]
    comma <- if (i < nrow(meta)) "," else ""
    lines <- c(lines, paste0(
      "    {",
      '"outcome":"', json_escape(r$outcome), '",',
      '"iv_spec":"', json_escape(r$iv_spec), '",',
      '"estimator":"', json_escape(r$estimator), '",',
      '"n":', r$n, ",",
      '"n_clusters":', r$n_clusters, ",",
      '"r_squared":', json_number(r$r_squared), ",",
      '"first_stage_min_F":', json_number(r$first_stage_min_F), ",",
      '"first_stage_median_F":', json_number(r$first_stage_median_F),
      "}", comma
    ))
  }
  lines <- c(lines, "  ]", "}")
  writeLines(lines, file, useBytes = TRUE)
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

outcomes <- c("production_participation", "log_selfprod_amount", "ihs_selfprod_amount")
hh_main <- c("household_size_reconstructed", "child_share", "elderly_share", "female_share")
endog_vars <- c("market_friction_survey", "child_market", "elderly_market", "female_market")
iv_interaction_terms <- c("iv_main", "child_iv", "elderly_iv", "female_iv")

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

other_controls <- c(
  "poi_market_friction_lag1",
  "price_hedonic_imputed_w99_yuan_per_jin",
  "gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km",
  "risk_salience_z_5yr_sum", "governance_capacity_z_5yr_sum",
  "trust_signal_z_5yr_sum", "attention_z_5yr_sum",
  "factor(food_category)", "factor(provn_std)", "factor(data_year)"
)

exog_terms <- c(hh_main, resource_terms, other_controls)

iv_specs <- list(
  terrain_town_2km = "iv_terrain_barrier_town_gee_2km",
  terrain_town_1km = "iv_terrain_barrier_town_gee_1km",
  terrain_town_5km = "iv_terrain_barrier_town_gee_5km",
  terrain_county_2km = "iv_terrain_barrier_county_gee_2km",
  early_ntl_9294 = "iv_early_ntl_peak_dist_9294"
)

## Correlation diagnostics use one row per household to avoid multiplying
## correlations by the eight food-category rows.
hh_once <- data[!duplicated(data$nhCode), ]
cor_targets <- c(
  "market_friction_survey", "poi_market_friction_lag1", "combined_market_friction",
  "gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km",
  "log1p_total_income_w_w99", "log1p_agri_business_income_w99",
  "log1p_annual_expense_total_w99", "total_sown_area"
)
cor_rows <- list()
for (iv_name in names(iv_specs)) {
  iv_var <- iv_specs[[iv_name]]
  if (!iv_var %in% names(hh_once)) next
  for (target in cor_targets[cor_targets %in% names(hh_once)]) {
    x <- to_num(hh_once[[iv_var]])
    y <- to_num(hh_once[[target]])
    ok <- is.finite(x) & is.finite(y)
    cor_rows[[length(cor_rows) + 1]] <- data.frame(
      iv_spec = iv_name,
      iv_variable = iv_var,
      target_variable = target,
      n = sum(ok),
      pearson_cor = if (sum(ok) >= 3) cor(x[ok], y[ok]) else NA_real_,
      stringsAsFactors = FALSE
    )
  }
}
cor_table <- do.call(rbind, cor_rows)
write_csv(cor_table, path("outputs", "tables", "table5_iv_correlations.csv"))

coef_rows <- list()
first_stage_rows <- list()
meta_rows <- list()
issues <- c()

for (iv_name in names(iv_specs)) {
  iv_var <- iv_specs[[iv_name]]
  if (!iv_var %in% names(data)) {
    issues <- c(issues, paste0("- Skipped IV spec ", iv_name, ": missing variable ", iv_var, "."))
    next
  }

  d0 <- data
  d0$iv_main <- to_num(d0[[iv_var]])
  d0$child_market <- d0$child_share * d0$market_friction_survey
  d0$elderly_market <- d0$elderly_share * d0$market_friction_survey
  d0$female_market <- d0$female_share * d0$market_friction_survey
  d0$child_iv <- d0$child_share * d0$iv_main
  d0$elderly_iv <- d0$elderly_share * d0$iv_main
  d0$female_iv <- d0$female_share * d0$iv_main

  for (outcome in outcomes) {
    all_terms <- unique(c(outcome, exog_terms, endog_vars, iv_interaction_terms, "xzc12_for_merge_final"))
    vars_needed <- unique(all.vars(as.formula(paste("~", paste(all_terms, collapse = " + ")))))
    missing_vars <- setdiff(vars_needed, names(d0))
    if (length(missing_vars) > 0) {
      issues <- c(issues, paste0(
        "- Skipped ", outcome, " / ", iv_name,
        ": missing variables: ", paste(missing_vars, collapse = ", ")
      ))
      next
    }
    d <- d0[complete.cases(d0[, vars_needed, drop = FALSE]), ]
    if (nrow(d) < 100) {
      issues <- c(issues, paste0("- Skipped ", outcome, " / ", iv_name, ": fewer than 100 complete rows."))
      next
    }

    ## First-stage diagnostics.
    fs_stats <- data.frame()
    for (endog in endog_vars) {
      fs_formula <- as.formula(paste(endog, "~", paste(c(exog_terms, iv_interaction_terms), collapse = " + ")))
      fs_model <- lm(fs_formula, data = d)
      fs_vc <- cluster_vcov(fs_model, d$xzc12_for_merge_final)
      fs_wald <- wald_test(fs_model, fs_vc, iv_interaction_terms)
      fs_F <- fs_wald$stat / fs_wald$df
      fs_stats <- rbind(fs_stats, data.frame(
        endogenous_variable = endog,
        first_stage_wald_chisq = fs_wald$stat,
        first_stage_df = fs_wald$df,
        first_stage_F = fs_F,
        first_stage_p = fs_wald$p,
        stringsAsFactors = FALSE
      ))
      for (zterm in iv_interaction_terms) {
        stats <- safe_lm_coef_row(fs_model, fs_vc, zterm)
        first_stage_rows[[length(first_stage_rows) + 1]] <- data.frame(
          outcome = outcome,
          iv_spec = iv_name,
          iv_variable = iv_var,
          endogenous_variable = endog,
          excluded_instrument = zterm,
          estimate = stats["estimate"],
          std_error_cluster = stats["std_error_cluster"],
          t_stat = stats["t_stat"],
          p_value = stats["p_value"],
          first_stage_wald_chisq = fs_wald$stat,
          first_stage_df = fs_wald$df,
          first_stage_F = fs_F,
          first_stage_p = fs_wald$p,
          n = nrow(d),
          n_clusters = length(unique(d$xzc12_for_merge_final)),
          stringsAsFactors = FALSE
        )
      }
    }
    fs_min_F <- min(fs_stats$first_stage_F, na.rm = TRUE)
    fs_median_F <- median(fs_stats$first_stage_F, na.rm = TRUE)

    ## Same-sample OLS comparison.
    ols_formula <- as.formula(paste(outcome, "~", paste(c(exog_terms, endog_vars), collapse = " + ")))
    ols_model <- lm(ols_formula, data = d)
    ols_vc <- cluster_vcov(ols_model, d$xzc12_for_merge_final)
    ols_r2 <- summary(ols_model)$r.squared
    for (term in endog_vars) {
      stats <- safe_lm_coef_row(ols_model, ols_vc, term)
      coef_rows[[length(coef_rows) + 1]] <- data.frame(
        outcome = outcome,
        iv_spec = iv_name,
        iv_variable = iv_var,
        estimator = "OLS_same_sample",
        term = term,
        estimate = stats["estimate"],
        std_error_cluster = stats["std_error_cluster"],
        t_stat = stats["t_stat"],
        p_value = stats["p_value"],
        n = nrow(d),
        n_clusters = length(unique(d$xzc12_for_merge_final)),
        r_squared = ols_r2,
        first_stage_min_F = fs_min_F,
        first_stage_median_F = fs_median_F,
        stringsAsFactors = FALSE
      )
    }
    meta_rows[[length(meta_rows) + 1]] <- data.frame(
      outcome = outcome,
      iv_spec = iv_name,
      estimator = "OLS_same_sample",
      n = nrow(d),
      n_clusters = length(unique(d$xzc12_for_merge_final)),
      r_squared = ols_r2,
      first_stage_min_F = fs_min_F,
      first_stage_median_F = fs_median_F,
      stringsAsFactors = FALSE
    )

    ## Manual 2SLS with clustered IV sandwich standard errors.
    X_exog <- model.matrix(as.formula(paste("~", paste(exog_terms, collapse = " + "))), data = d)
    X <- cbind(X_exog, as.matrix(d[, endog_vars, drop = FALSE]))
    Z <- cbind(X_exog, as.matrix(d[, iv_interaction_terms, drop = FALSE]))
    iv_fit <- iv_2sls(d[[outcome]], X, Z, d$xzc12_for_merge_final)
    beta <- iv_fit$beta
    ses <- sqrt(diag(iv_fit$vcov))
    for (term in endog_vars) {
      if (!term %in% names(beta)) {
        issues <- c(issues, paste0("- IV term dropped by rank check: ", outcome, " / ", iv_name, " / ", term, "."))
        next
      }
      tval <- beta[term] / ses[term]
      coef_rows[[length(coef_rows) + 1]] <- data.frame(
        outcome = outcome,
        iv_spec = iv_name,
        iv_variable = iv_var,
        estimator = "IV_2SLS",
        term = term,
        estimate = beta[term],
        std_error_cluster = ses[term],
        t_stat = tval,
        p_value = 2 * pnorm(abs(tval), lower.tail = FALSE),
        n = iv_fit$n,
        n_clusters = iv_fit$n_clusters,
        r_squared = iv_fit$r_squared,
        first_stage_min_F = fs_min_F,
        first_stage_median_F = fs_median_F,
        stringsAsFactors = FALSE
      )
    }
    meta_rows[[length(meta_rows) + 1]] <- data.frame(
      outcome = outcome,
      iv_spec = iv_name,
      estimator = "IV_2SLS",
      n = iv_fit$n,
      n_clusters = iv_fit$n_clusters,
      r_squared = iv_fit$r_squared,
      first_stage_min_F = fs_min_F,
      first_stage_median_F = fs_median_F,
      stringsAsFactors = FALSE
    )
  }
}

iv_results <- do.call(rbind, coef_rows)
first_stage_table <- do.call(rbind, first_stage_rows)
model_meta <- do.call(rbind, meta_rows)

write_csv(iv_results, path("outputs", "tables", "table5_iv_results.csv"))
write_csv(first_stage_table, path("outputs", "tables", "table5_iv_first_stage.csv"))
write_model_json(model_meta, path("outputs", "model_summaries", "model5_iv_results.json"))

weak_rows <- unique(model_meta[, c("outcome", "iv_spec", "first_stage_min_F", "first_stage_median_F")])
weak_flags <- weak_rows[weak_rows$first_stage_min_F < 10 | is.na(weak_rows$first_stage_min_F), ]
weak_lines <- if (nrow(weak_flags) == 0) {
  "- No first-stage minimum F-statistic is below 10."
} else {
  paste0(
    "- ", weak_flags$outcome, " / ", weak_flags$iv_spec,
    ": minimum first-stage F = ", sprintf("%.3f", weak_flags$first_stage_min_F),
    ", median F = ", sprintf("%.3f", weak_flags$first_stage_median_F), "."
  )
}

log_lines <- c(
  "# IV Diagnostics and Market-Friction 2SLS Models",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Estimation Notes",
  "",
  "- IV is used as mechanism-support evidence for market friction, not as the paper's main identification strategy.",
  "- Endogenous variables: `market_friction_survey`, `child_share × market_friction_survey`, `elderly_share × market_friction_survey`, and `female_share × market_friction_survey`.",
  "- Excluded instruments: one terrain/early-market IV plus its interactions with child, elderly, and female shares.",
  "- Exogenous controls follow the M3 controls plus household composition main effects and lagged POI market friction.",
  "- Standard errors are clustered by `xzc12_for_merge_final`.",
  "- The reported 2SLS standard errors are manually computed clustered IV sandwich standard errors; no household, village, village-year, DID, or panel fixed effects are used.",
  "- Each IV specification is exactly identified, so overidentification tests are not reported.",
  "",
  "## Weak-IV Flags",
  "",
  weak_lines,
  "",
  "## Outputs",
  "",
  "- `outputs/tables/table5_iv_results.csv`",
  "- `outputs/tables/table5_iv_first_stage.csv`",
  "- `outputs/tables/table5_iv_correlations.csv`",
  "- `outputs/model_summaries/model5_iv_results.json`",
  "",
  "## Issues",
  "",
  if (length(issues) == 0) "- None." else issues
)
writeLines(log_lines, path("outputs", "logs", "iv_diagnostics.md"), useBytes = TRUE)

message("IV diagnostics and 2SLS models completed.")
````

## `code/12_placebo_and_robustness_checks.R`

- Size: 14.1 KB
- Lines: 376

````r
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
````

## `code/13_compile_all_integrated_markdowns.R`

- Size: 8.4 KB
- Lines: 234

````r
options(warn = 1)

root <- getwd()
report_dir <- file.path(root, "outputs", "reports")
dir.create(report_dir, recursive = TRUE, showWarnings = FALSE)

path <- function(...) file.path(root, ...)

file_info_row <- function(file) {
  info <- file.info(file)
  data.frame(
    file = file,
    relative_path = sub(paste0("^", root, "/?"), "", file),
    size_bytes = info$size,
    size_kb = round(info$size / 1024, 1),
    n_lines = if (file.exists(file) && !dir.exists(file)) length(readLines(file, warn = FALSE, encoding = "UTF-8")) else NA_integer_,
    stringsAsFactors = FALSE
  )
}

read_text <- function(file) {
  paste(readLines(file, warn = FALSE, encoding = "UTF-8"), collapse = "\n")
}

fence_block <- function(text, info = "") {
  paste0("````", info, "\n", text, "\n````")
}

md_table <- function(df) {
  if (nrow(df) == 0) return("")
  cols <- names(df)
  lines <- c(
    paste0("| ", paste(cols, collapse = " | "), " |"),
    paste0("|", paste(rep("---", length(cols)), collapse = "|"), "|")
  )
  for (i in seq_len(nrow(df))) {
    vals <- vapply(df[i, , drop = FALSE], function(x) as.character(x[1]), character(1))
    vals <- gsub("\\|", "\\\\|", vals)
    lines <- c(lines, paste0("| ", paste(vals, collapse = " | "), " |"))
  }
  paste(lines, collapse = "\n")
}

relative <- function(file) sub(paste0("^", root, "/?"), "", file)

## -------------------------------------------------------------------------
## Integrated results package
## -------------------------------------------------------------------------

result_md <- file.path(report_dir, "paper1_all_results_integrated.md")
code_md <- file.path(report_dir, "paper1_all_code_integrated.md")

report_files <- sort(list.files(path("outputs", "reports"), pattern = "\\.md$", full.names = TRUE))
superseded_report_files <- path("outputs", "reports", c(
  "paper1_unit_kg_month_descriptive_check.md"
))
superseded_log_files <- path("outputs", "logs", c(
  "unit_kg_month_check.md"
))
superseded_table_files <- path("outputs", "tables", c(
  "paper1_unit_conversion_audit_kg_month.csv",
  "paper1_key_variable_descriptives_kg_month.csv",
  "paper1_category_outcome_descriptives_kg_month.csv",
  "paper1_top_extreme_values_kg_month.csv",
  "paper1_unit_checks_kg_month.csv"
))
superseded_files <- c(superseded_report_files, superseded_log_files, superseded_table_files)
superseded_existing <- superseded_files[file.exists(superseded_files)]

report_files <- setdiff(report_files, c(result_md, code_md, superseded_report_files))
root_result_files <- sort(file.path(root, c(
  "paper1_empirical_methods_variables_results_conclusions.md"
)))
root_result_files <- root_result_files[file.exists(root_result_files)]
log_files <- sort(list.files(path("outputs", "logs"), pattern = "\\.md$", full.names = TRUE))
log_files <- setdiff(log_files, superseded_log_files)
manuscript_files <- sort(list.files(path("outputs", "manuscript"), pattern = "\\.md$", full.names = TRUE))
table_files <- sort(list.files(path("outputs", "tables"), pattern = "\\.csv$", full.names = TRUE))
table_files <- setdiff(table_files, superseded_table_files)
json_files <- sort(list.files(path("outputs", "model_summaries"), pattern = "\\.json$", full.names = TRUE))
figure_files <- sort(list.files(path("outputs", "figures"), pattern = "\\.(png|jpg|jpeg|webp)$", full.names = TRUE, ignore.case = TRUE))

all_result_text_files <- c(report_files, root_result_files, manuscript_files, log_files, table_files, json_files)
result_inventory <- do.call(rbind, lapply(c(all_result_text_files, figure_files), file_info_row))

result_lines <- c(
  "# Paper 1 All Results Integrated Package",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "This file integrates the current Paper 1 result artifacts after kg/month conversion, quantity-outlier exclusion, and full R model reruns.",
  "",
  "## 0. Execution Notes",
  "",
  "- **Econometric estimation is R-only.** The Python files in `code/` (`15`–`17`) are manuscript-writing utilities, not statistical models.",
  "- **One-command rerun:** `Rscript code/run_revised_pipeline.R` from the project root.",
  "- **Recommended order:** `19` (data prep) → `01`–`14` (models) → `13` (this compile step).",
  "- **Code review:** see `outputs/reports/paper1_econometric_code_review.md`.",
  "",
  "Binary figures are embedded by path; CSV, JSON, and Markdown outputs are included as text blocks.",
  ""
)

if (length(superseded_existing) > 0) {
  result_lines <- c(
    result_lines,
    "## Current-Run Scope Note",
    "",
    "The following earlier unit-check artifacts were excluded from this integrated results package because they predate the formal quantity-outlier exclusion and can show superseded extreme values:",
    "",
    paste0("- `", relative(superseded_existing), "`"),
    ""
  )
}

result_lines <- c(
  result_lines,
  "## 1. Artifact Inventory",
  "",
  md_table(result_inventory[, c("relative_path", "size_kb", "n_lines")]),
  "",
  "## 2. Figures",
  ""
)

if (length(figure_files) == 0) {
  result_lines <- c(result_lines, "- No figure files found.")
} else {
  for (fig in figure_files) {
    result_lines <- c(
      result_lines,
      paste0("### ", relative(fig)),
      "",
      paste0("![", basename(fig), "](", fig, ")"),
      ""
    )
  }
}

append_file_section <- function(lines, file, section_title, info) {
  lines <- c(
    lines,
    paste0("## ", section_title, ": `", relative(file), "`"),
    "",
    paste0("- Size: ", round(file.info(file)$size / 1024, 1), " KB"),
    paste0("- Lines: ", length(readLines(file, warn = FALSE, encoding = "UTF-8"))),
    "",
    fence_block(read_text(file), info),
    ""
  )
  lines
}

if (length(report_files) + length(root_result_files) > 0) {
  result_lines <- c(result_lines, "## 3. Result Reports", "")
  for (file in c(report_files, root_result_files)) {
    result_lines <- append_file_section(result_lines, file, "Report", "markdown")
  }
}

if (length(manuscript_files) > 0) {
  result_lines <- c(result_lines, "## 4. Manuscript and LLM Review Artifacts", "")
  for (file in manuscript_files) {
    result_lines <- append_file_section(result_lines, file, "Manuscript Artifact", "markdown")
  }
}

if (length(log_files) > 0) {
  result_lines <- c(result_lines, "## 5. Logs", "")
  for (file in log_files) {
    result_lines <- append_file_section(result_lines, file, "Log", "markdown")
  }
}

if (length(table_files) > 0) {
  result_lines <- c(result_lines, "## 6. Tables", "")
  for (file in table_files) {
    result_lines <- append_file_section(result_lines, file, "Table CSV", "csv")
  }
}

if (length(json_files) > 0) {
  result_lines <- c(result_lines, "## 7. Model Summaries JSON", "")
  for (file in json_files) {
    result_lines <- append_file_section(result_lines, file, "Model Summary JSON", "json")
  }
}

writeLines(result_lines, result_md, useBytes = TRUE)

## -------------------------------------------------------------------------
## Integrated code package
## -------------------------------------------------------------------------

code_files <- sort(list.files(path("code"), pattern = "\\.(R|py)$", full.names = TRUE))
code_inventory <- do.call(rbind, lapply(code_files, file_info_row))

code_lines <- c(
  "# Paper 1 All Code Integrated Package",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "This file concatenates all R and Python scripts in `code/`.",
  "",
  "- **Econometric pipeline (R):** `run_revised_pipeline.R`, `00_setup.R`, `19`, `01`–`14`, `13`.",
  "- **Manuscript utilities (Python, not econometrics):** `15_write_manuscript_draft.py`, `16_llm_manuscript_revision.py`, `17_finalize_manuscript_after_llm_review.py`.",
  "- **Legacy scripts:** older numbered files such as `08_baseline_separability_tests.R` are retained for audit history but are not part of the revised pipeline.",
  "",
  "Each script is preserved verbatim inside a fenced code block.",
  "",
  "## 1. Code Inventory",
  "",
  md_table(code_inventory[, c("relative_path", "size_kb", "n_lines")]),
  ""
)

for (file in code_files) {
  info_string <- if (grepl("\\.py$", file, ignore.case = TRUE)) "python" else "r"
  code_lines <- c(
    code_lines,
    paste0("## `", relative(file), "`"),
    "",
    paste0("- Size: ", round(file.info(file)$size / 1024, 1), " KB"),
    paste0("- Lines: ", length(readLines(file, warn = FALSE, encoding = "UTF-8"))),
    "",
    fence_block(read_text(file), info_string),
    ""
  )
}

writeLines(code_lines, code_md, useBytes = TRUE)

message("Integrated results markdown written: ", result_md)
message("Integrated code markdown written: ", code_md)
````

## `code/14_editor_revision_analyses.R`

- Size: 30.9 KB
- Lines: 634

````r
source("code/00_setup.R")

data <- read_csv(
  path("data", "analysis_ready", "paper1_revised_analysis_ready_long.csv"),
  colClasses = c(nhCode = "character", xzc12 = "character", xzc12_for_merge_final = "character")
)
data <- prepare_revised_data(data)

outcomes_main <- c("production_participation", "log_selfprod_amount", "ihs_selfprod_amount")
food_order <- c("zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo")

market_terms_only <- c("market_friction_survey", "poi_market_friction_lag1")
gaez_terms_only <- c("gaez_overall_si_10km", "gaez_staple_si_10km", "gaez_soil_terrain_constraint_10km")
province_fe_only <- "factor(provn_std)"
unit_value_text_terms <- price_text_terms_revised

fixed_resource_terms <- c(
  "total_sown_area", "agricultural_labor_days", "offfarm_labor_days",
  "household_assets_count_proxy_imp", "household_assets_count_proxy_missing",
  "household_head_age_imp", "household_head_age_missing",
  "household_head_education_imp", "household_head_education_missing",
  "household_head_gender_male_imp", "household_head_gender_male_missing"
)

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

fmt_num <- function(x, digits = 3) {
  ifelse(is.na(x), "", formatC(x, format = "f", digits = digits))
}

md_table <- function(df, digits = 3, max_rows = Inf) {
  if (is.null(df) || nrow(df) == 0) return("")
  if (is.finite(max_rows)) df <- head(df, max_rows)
  df2 <- df
  for (nm in names(df2)) {
    if (is.numeric(df2[[nm]])) df2[[nm]] <- fmt_num(df2[[nm]], digits)
  }
  cols <- names(df2)
  lines <- c(
    paste0("| ", paste(cols, collapse = " | "), " |"),
    paste0("|", paste(rep("---", length(cols)), collapse = "|"), "|")
  )
  for (i in seq_len(nrow(df2))) {
    vals <- vapply(df2[i, , drop = FALSE], function(x) as.character(x[1]), character(1))
    vals <- gsub("\\|", "\\\\|", vals)
    lines <- c(lines, paste0("| ", paste(vals, collapse = " | "), " |"))
  }
  paste(lines, collapse = "\n")
}

complete_data_for_rhs <- function(d, outcomes, rhs_terms, cluster_var = "xzc12_for_merge_final") {
  f <- as.formula(paste("~", paste(rhs_terms, collapse = " + ")))
  vars_needed <- unique(c(outcomes, all.vars(f), cluster_var))
  d[complete.cases(d[, vars_needed, drop = FALSE]), ]
}

wald_row <- function(d, outcome, rhs_terms, test_terms = hh_terms_main, label = "", cluster_var = "xzc12_for_merge_final") {
  fit <- fit_lm_cluster(d, outcome, rhs_terms, cluster_var = cluster_var)
  if (!fit$ok) {
    return(data.frame(
      label = label, outcome = outcome, n = nrow(fit$data), n_clusters = NA_integer_,
      r_squared = NA_real_, wald_chisq = NA_real_, wald_df = 0L, wald_p = NA_real_,
      stringsAsFactors = FALSE
    ))
  }
  w <- wald_test(fit$model, fit$vcov, test_terms)
  data.frame(
    label = label,
    outcome = outcome,
    n = nrow(fit$data),
    n_clusters = length(unique(fit$data[[cluster_var]])),
    r_squared = summary(fit$model)$r.squared,
    wald_chisq = w$stat,
    wald_df = w$df,
    wald_p = w$p,
    stringsAsFactors = FALSE
  )
}

## -------------------------------------------------------------------------
## A. M1-to-M2 add-one-block diagnostics.
## -------------------------------------------------------------------------

m3_vars <- unique(c(
  outcomes_main,
  all.vars(as.formula(paste("~", paste(baseline_rhs("M3"), collapse = " + ")))),
  "xzc12_for_merge_final"
))
data_common_m3 <- data[complete.cases(data[, m3_vars, drop = FALSE]), ]

block_specs <- list(
  "B0_composition_category_year" = c(hh_terms_main, category_year_terms_revised),
  "B1_plus_household_resources" = c(hh_terms_main, resource_terms_revised, category_year_terms_revised),
  "B1a_M1_plus_market" = c(hh_terms_main, resource_terms_revised, market_terms_only, category_year_terms_revised),
  "B1b_M1_plus_GAEZ" = c(hh_terms_main, resource_terms_revised, gaez_terms_only, category_year_terms_revised),
  "B1c_M1_plus_province_FE" = c(hh_terms_main, resource_terms_revised, province_fe_only, category_year_terms_revised),
  "B1d_M1_plus_market_GAEZ" = c(hh_terms_main, resource_terms_revised, market_terms_only, gaez_terms_only, category_year_terms_revised),
  "B1e_M1_plus_market_province_FE" = c(hh_terms_main, resource_terms_revised, market_terms_only, province_fe_only, category_year_terms_revised),
  "B1f_M1_plus_GAEZ_province_FE" = c(hh_terms_main, resource_terms_revised, gaez_terms_only, province_fe_only, category_year_terms_revised),
  "B2_full_market_GAEZ_province_FE" = c(hh_terms_main, resource_terms_revised, market_terms_only, gaez_terms_only, province_fe_only, category_year_terms_revised),
  "B3_plus_unit_value_text" = c(hh_terms_main, resource_terms_revised, market_terms_only, gaez_terms_only, province_fe_only, unit_value_text_terms, category_year_terms_revised)
)

block_rows <- list()
for (outcome in outcomes_main) {
  for (nm in names(block_specs)) {
    row <- wald_row(data_common_m3, outcome, block_specs[[nm]], label = nm)
    row$diagnostic_family <- "add_one_block"
    row$common_sample <- "M3_complete_case"
    row$spec_order <- match(nm, names(block_specs))
    block_rows[[length(block_rows) + 1]] <- row
  }
}
tableE <- rbind_fill(block_rows)
tableE <- tableE[order(tableE$outcome, tableE$spec_order), ]
write_csv(tableE, path("outputs", "tables", "tableE_add_one_block_diagnostics.csv"))

## -------------------------------------------------------------------------
## B. Village fixed effects robustness.
## -------------------------------------------------------------------------

village_fe_rhs <- c(
  hh_terms_main,
  resource_terms_revised,
  "price_hedonic_imputed_w99_yuan_per_jin",
  "factor(data_year)",
  "factor(food_category)",
  "factor(xzc12_for_merge_final)"
)

village_rows <- list()
for (outcome in outcomes_main) {
  row <- wald_row(data_common_m3, outcome, village_fe_rhs, label = "village_FE_M3_like")
  row$absorbed_controls <- "province_FE_market_GAEZ_text_absorbed_or_collinear_at_village_county_level"
  row$common_sample <- "M3_complete_case"
  village_rows[[length(village_rows) + 1]] <- row
}

for (cat in food_order) {
  dcat <- data_common_m3[data_common_m3$food_category == cat, ]
  if (nrow(dcat) == 0) next
  rhs_cat <- setdiff(village_fe_rhs, "factor(food_category)")
  row <- wald_row(dcat, "production_participation", rhs_cat, label = paste0("village_FE_category_", cat))
  row$food_category <- cat
  row$food_category_label <- dcat$food_category_label[1]
  row$absorbed_controls <- "category_specific_village_FE"
  row$common_sample <- "M3_complete_case"
  village_rows[[length(village_rows) + 1]] <- row
}

tableF <- rbind_fill(village_rows)
write_csv(tableF, path("outputs", "tables", "tableF_village_fe_robustness.csv"))

## -------------------------------------------------------------------------
## C. Logit/probit robustness for participation.
## -------------------------------------------------------------------------

fit_glm_cluster <- function(d, outcome, rhs_terms, link, cluster_var = "xzc12_for_merge_final") {
  f <- as.formula(paste(outcome, "~", paste(rhs_terms, collapse = " + ")))
  vars_needed <- unique(c(all.vars(f), cluster_var))
  d0 <- d[complete.cases(d[, vars_needed, drop = FALSE]), ]
  if (nrow(d0) < 100 || length(unique(d0[[outcome]])) < 2) {
    return(list(ok = FALSE, formula = f, data = d0, model = NULL, vcov = NULL, warnings = "insufficient_outcome_variation"))
  }
  warns <- character()
  model <- tryCatch(
    withCallingHandlers(
      glm(f, data = d0, family = binomial(link = link), control = glm.control(maxit = 75)),
      warning = function(w) {
        warns <<- c(warns, conditionMessage(w))
        invokeRestart("muffleWarning")
      }
    ),
    error = function(e) e
  )
  if (inherits(model, "error")) {
    return(list(ok = FALSE, formula = f, data = d0, model = NULL, vcov = NULL, warnings = conditionMessage(model)))
  }
  vc <- tryCatch(cluster_vcov(model, d0[[cluster_var]]), error = function(e) e)
  if (inherits(vc, "error")) {
    return(list(ok = FALSE, formula = f, data = d0, model = model, vcov = NULL, warnings = conditionMessage(vc)))
  }
  list(ok = TRUE, formula = f, data = d0, model = model, vcov = vc, warnings = paste(unique(warns), collapse = " | "))
}

glm_row <- function(d, outcome, rhs_terms, link, label) {
  fit <- fit_glm_cluster(d, outcome, rhs_terms, link)
  ybar <- mean(fit$data[[outcome]], na.rm = TRUE)
  low_variation <- is.finite(ybar) && (ybar < 0.05 || ybar > 0.95)
  if (!fit$ok) {
    return(data.frame(
      model_family = link, label = label, outcome = outcome,
      n = nrow(fit$data), n_clusters = NA_integer_, outcome_mean = ybar,
      converged = FALSE, wald_chisq = NA_real_, wald_df = 0L, wald_p = NA_real_,
      low_variation_flag = low_variation,
      recommended_use = ifelse(low_variation, "do_not_interpret_low_variation_or_separation", "failed_model"),
      warnings = fit$warnings, stringsAsFactors = FALSE
    ))
  }
  w <- wald_test(fit$model, fit$vcov, hh_terms_main)
  data.frame(
    model_family = link,
    label = label,
    outcome = outcome,
    n = nrow(fit$data),
    n_clusters = length(unique(fit$data$xzc12_for_merge_final)),
    outcome_mean = ybar,
    converged = isTRUE(fit$model$converged),
    wald_chisq = w$stat,
    wald_df = w$df,
    wald_p = w$p,
    low_variation_flag = low_variation,
    recommended_use = ifelse(low_variation, "do_not_interpret_low_variation_or_separation", "supporting_functional_form_check"),
    warnings = fit$warnings,
    stringsAsFactors = FALSE
  )
}

glm_rows <- list()
for (link in c("logit", "probit")) {
  glm_rows[[length(glm_rows) + 1]] <- glm_row(data_common_m3, "production_participation", baseline_rhs("M3"), link, "overall_M3")
  for (cat in food_order) {
    dcat <- data[data$food_category == cat, ]
    rhs_cat <- setdiff(baseline_rhs("M3"), "factor(food_category)")
    row <- glm_row(dcat, "production_participation", rhs_cat, link, paste0("category_", cat))
    row$food_category <- cat
    row$food_category_label <- dcat$food_category_label[1]
    glm_rows[[length(glm_rows) + 1]] <- row
  }
}
tableG <- rbind_fill(glm_rows)
write_csv(tableG, path("outputs", "tables", "tableG_binary_response_robustness.csv"))

## -------------------------------------------------------------------------
## D. Multiple-testing correction and reframed category diagnostics.
## -------------------------------------------------------------------------

table4 <- read_csv(path("outputs", "tables", "table4_category_specific_nsi.csv"))
table1cat <- read_csv(path("outputs", "tables", "table1_category_participation_revised.csv"))

tableH <- table4[, c(
  "food_category", "food_category_label", "outcome_mean", "hhcomp_wald_chisq",
  "hhcomp_wald_df", "hhcomp_wald_p", "nsi", "main_coefficient_drivers"
)]
tableH$p_bonferroni <- p.adjust(tableH$hhcomp_wald_p, method = "bonferroni")
tableH$p_holm <- p.adjust(tableH$hhcomp_wald_p, method = "holm")
tableH$p_bh_fdr <- p.adjust(tableH$hhcomp_wald_p, method = "BH")
tableH$significant_raw_5pct <- tableH$hhcomp_wald_p < 0.05
tableH$significant_bh_fdr_5pct <- tableH$p_bh_fdr < 0.05
tableH$significant_bonferroni_5pct <- tableH$p_bonferroni < 0.05
write_csv(tableH, path("outputs", "tables", "tableH_category_multiple_testing.csv"))

tableI <- merge(
  tableH,
  table1cat[, c("food_category", "participation_rate", "mean_self_suff_rate", "mean_cons_monthly_jin", "mean_selfprod_monthly_total")],
  by = "food_category",
  all.x = TRUE
)
tableI$nsi_rank_detectability <- rank(-tableI$nsi, ties.method = "min")
tableI$self_suff_rank_economic_importance <- rank(-tableI$mean_self_suff_rate, ties.method = "min")
tableI$variation_flag <- ifelse(
  tableI$participation_rate < 0.05, "near_zero_variation_exclude_main",
  ifelse(tableI$participation_rate > 0.95, "near_ceiling_variation_caution",
    ifelse(tableI$participation_rate > 0.80, "high_participation_ceiling_caution", "middle_range_variation")
  )
)
tableI$main_text_status <- ifelse(
  tableI$food_category == "nailei", "exclude_from_main_category_interpretation",
  ifelse(tableI$food_category == "youzhi", "definition_pending_human_review",
    ifelse(tableI$food_category == "roulei", "aggregate_meat_aquatic_limitations",
      ifelse(tableI$variation_flag == "middle_range_variation", "main_comparable_category", "interpret_with_variation_caution")
    )
  )
)
tableI$nsi_interpretation <- "detectability_ranking_not_economic_magnitude"
tableI <- tableI[order(tableI$nsi_rank_detectability), ]
write_csv(tableI, path("outputs", "tables", "tableI_category_variation_and_nsi_reframed.csv"))

png(path("outputs", "figures", "figure2_editor_nsi_detectability.png"), width = 1900, height = 1150, res = 180)
plot_df <- tableI[order(tableI$nsi), ]
cols <- ifelse(plot_df$main_text_status == "exclude_from_main_category_interpretation", "#B8B8B8",
  ifelse(plot_df$significant_bh_fdr_5pct, "#2F6B9A", "#8BA6A9"))
par(mar = c(6, 9, 4, 2))
barplot(
  plot_df$nsi,
  names.arg = plot_df$food_category_label,
  horiz = TRUE,
  las = 1,
  col = cols,
  border = NA,
  xlab = "Relative Wald statistic (category Wald / mean category Wald)",
  main = "Category Detectability Ranking, Not Economic Magnitude"
)
abline(v = 1, lty = 2, col = "#666666")
legend("bottomright", legend = c("BH FDR < 0.05", "Not BH-significant", "Excluded/caution"), fill = c("#2F6B9A", "#8BA6A9", "#B8B8B8"), border = NA, bty = "n")
dev.off()

## -------------------------------------------------------------------------
## E. Fixed common-sample robustness for composition and price variants.
## -------------------------------------------------------------------------

fit_wald_generic <- function(d, outcome, terms, controls) {
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
    wald_p = w$p,
    stringsAsFactors = FALSE
  )
}

comp_specs <- list(
  proportion = hh_terms_main,
  dependency = c("household_size_reconstructed", "dependency_ratio", "female_share"),
  counts = c("num_children", "num_elderly", "num_adult_male", "num_adult_female")
)
controls_no_hh <- c(resource_terms_revised, market_gaez_terms_revised, price_text_terms_revised, category_year_terms_revised)
outcomes_with_selfsuff <- c("production_participation", "log_selfprod_amount", "ihs_selfprod_amount", "self_suff_rate")
all_comp_vars <- unique(unlist(comp_specs, use.names = FALSE))
fixed_comp_vars <- unique(c(outcomes_with_selfsuff, all_comp_vars, all.vars(as.formula(paste("~", paste(controls_no_hh, collapse = " + ")))), "xzc12_for_merge_final"))
data_fixed_comp <- data[complete.cases(data[, fixed_comp_vars, drop = FALSE]), ]

fixed_comp_rows <- list()
for (comp in names(comp_specs)) {
  terms <- comp_specs[[comp]]
  for (outcome in outcomes_with_selfsuff) {
    res <- fit_wald_generic(data_fixed_comp, outcome, terms, controls_no_hh)
    fixed_comp_rows[[length(fixed_comp_rows) + 1]] <- data.frame(
      composition_spec = comp,
      outcome = outcome,
      fixed_common_sample = TRUE,
      tested_terms = paste(terms, collapse = " + "),
      res,
      stringsAsFactors = FALSE
    )
  }
}
tableJ <- rbind_fill(fixed_comp_rows)
write_csv(tableJ, path("outputs", "tables", "tableJ_fixed_common_sample_robustness.csv"))

price_specs <- list(
  no_unit_value = setdiff(price_text_terms_revised, "price_hedonic_imputed_w99_yuan_per_jin"),
  hedonic_unit_value = price_text_terms_revised,
  observed_household_unit_value = c("price_preferred_household_recalc_w99_yuan_per_jin", setdiff(price_text_terms_revised, "price_hedonic_imputed_w99_yuan_per_jin")),
  village_median_unit_value = c("village_price_category_median", setdiff(price_text_terms_revised, "price_hedonic_imputed_w99_yuan_per_jin"))
)
price_common_vars <- unique(c(
  "production_participation", hh_terms_main, resource_terms_revised, market_gaez_terms_revised,
  unlist(price_specs, use.names = FALSE), category_year_terms_revised, "xzc12_for_merge_final"
))
data_fixed_price <- complete_data_for_rhs(
  data,
  "production_participation",
  c(hh_terms_main, resource_terms_revised, market_gaez_terms_revised, unlist(price_specs, use.names = FALSE), category_year_terms_revised)
)
fixed_price_rows <- list()
for (nm in names(price_specs)) {
  rhs <- c(hh_terms_main, resource_terms_revised, market_gaez_terms_revised, price_specs[[nm]], category_year_terms_revised)
  row <- wald_row(data_fixed_price, "production_participation", rhs, label = nm)
  row$fixed_common_sample <- TRUE
  fixed_price_rows[[length(fixed_price_rows) + 1]] <- row
}
tableJ_price <- rbind_fill(fixed_price_rows)
write_csv(tableJ_price, path("outputs", "tables", "tableJ_fixed_common_sample_price_robustness.csv"))

## -------------------------------------------------------------------------
## F. Bad-control/fixed-factor sensitivity.
## -------------------------------------------------------------------------

bad_control_specs <- list(
  full_M3_resources = baseline_rhs("M3"),
  fixed_factors_no_income_expense = c(hh_terms_main, fixed_resource_terms, market_gaez_terms_revised, price_text_terms_revised, category_year_terms_revised),
  fixed_factors_no_income_expense_land_w99 = c(hh_terms_main, setdiff(fixed_resource_terms, "total_sown_area"), "total_sown_area_w99", market_gaez_terms_revised, price_text_terms_revised, category_year_terms_revised)
)

bad_rows <- list()
for (outcome in outcomes_main) {
  rhs_all <- unique(unlist(bad_control_specs, use.names = FALSE))
  d_bad <- complete_data_for_rhs(data, outcome, rhs_all)
  for (nm in names(bad_control_specs)) {
    row <- wald_row(d_bad, outcome, bad_control_specs[[nm]], label = nm)
    row$fixed_common_sample_across_bad_control_specs <- TRUE
    bad_rows[[length(bad_rows) + 1]] <- row
  }
}
tableK <- rbind_fill(bad_rows)
write_csv(tableK, path("outputs", "tables", "tableK_fixed_factors_bad_controls_robustness.csv"))

## -------------------------------------------------------------------------
## G. Missingness and definition diagnostics.
## -------------------------------------------------------------------------

source_selfprod_missing <- sum(is.na(data$selfprod_monthly_total))
source_participation_missing <- sum(is.na(data$production_participation))
missing_table <- data.frame(
  diagnostic = c(
    "selfprod_monthly_total_missing_in_current_long_file",
    "production_participation_missing_in_current_long_file",
    "na_to_zero_robustness_status"
  ),
  value = c(
    as.character(source_selfprod_missing),
    as.character(source_participation_missing),
    "not_reconstructable_from_current_analysis_ready_or_cleaned_long_files"
  ),
  implication = c(
    "The current long files no longer preserve item-level source missingness.",
    "Participation is fully populated after prior cleaning.",
    "Report as a limitation and rerun only if raw item-level missing codes are restored."
  ),
  stringsAsFactors = FALSE
)
write_csv(missing_table, path("outputs", "tables", "tableL_participation_missingness_robustness.csv"))

hh_once <- data[!duplicated(data$nhCode), ]
hh_year_counts <- tapply(data$data_year, data$nhCode, function(x) length(unique(x)))
definition_rows <- list(
  data.frame(
    diagnostic = "pooled_repeated_cross_section",
    value = paste0("min_years_per_nhCode=", min(hh_year_counts), "; max_years_per_nhCode=", max(hh_year_counts)),
    numeric_value = max(hh_year_counts),
    decision = "No household fixed effects are feasible with current nhCode; use pooled repeated cross-section language.",
    stringsAsFactors = FALSE
  ),
  data.frame(
    diagnostic = "households_at_roster_cap_8",
    value = paste0(sum(hh_once$household_size_reconstructed >= 8, na.rm = TRUE), " of ", nrow(hh_once), " households"),
    numeric_value = mean(hh_once$household_size_reconstructed >= 8, na.rm = TRUE),
    decision = "Roster cap is visible but rare; disclose in data limitations.",
    stringsAsFactors = FALSE
  ),
  data.frame(
    diagnostic = "total_sown_area_w99_max",
    value = paste0("max=", max(hh_once$total_sown_area_w99, na.rm = TRUE), "; p99=", as.numeric(quantile(hh_once$total_sown_area_w99, 0.99, na.rm = TRUE))),
    numeric_value = max(hh_once$total_sown_area_w99, na.rm = TRUE),
    decision = "Winsorized total sown area is used as a sensitivity check; main setup still uses total_sown_area.",
    stringsAsFactors = FALSE
  ),
  data.frame(
    diagnostic = "sex_coding_audit",
    value = "household_head_gender_male inferred from earlier household relation cross-check, codebook confirmation still needed",
    numeric_value = NA_real_,
    decision = "Keep female_share interpretation conditional until HA2 coding is manually verified.",
    stringsAsFactors = FALSE
  ),
  data.frame(
    diagnostic = "youzhi_definition",
    value = "partially identified; item-code review required",
    numeric_value = NA_real_,
    decision = "Do not make strong substantive claims about oils before item-code review.",
    stringsAsFactors = FALSE
  ),
  data.frame(
    diagnostic = "roulei_aggregation",
    value = "meat plus aquatic plus processed products in current aggregate category",
    numeric_value = NA_real_,
    decision = "Use label meat/aquatic products and state aggregation limitation.",
    stringsAsFactors = FALSE
  )
)
tableM <- rbind_fill(definition_rows)
write_csv(tableM, path("outputs", "tables", "tableM_definition_diagnostics_editor.csv"))

## -------------------------------------------------------------------------
## H. Price-unit-value diagnostics gathered for reporting.
## -------------------------------------------------------------------------

price_source <- read_csv(path("outputs", "tables", "hedonic_price_imputation_source_summary.csv"))
price_model <- read_csv(path("outputs", "tables", "hedonic_price_model_diagnostics.csv"))
price_rob <- read_csv(path("outputs", "tables", "tableC_price_robustness.csv"))

price_diag <- data.frame(
  diagnostic = c("observed_unit_value_share", "hedonic_imputed_share", "county_hedonic_r_squared", "county_hedonic_rmse_log", "observed_only_participation_p"),
  value = c(
    price_source$share[price_source$price_hedonic_source == "observed_household_recalc"],
    price_source$share[price_source$price_hedonic_source == "hedonic_county"],
    price_model$r_squared[price_model$model == "county"],
    price_model$rmse_log_in_sample[price_model$model == "county"],
    price_rob$hhcomp_wald_p[price_rob$price_spec == "observed_price_only" & price_rob$outcome == "production_participation"]
  ),
  interpretation = c(
    "Observed variable is household purchase-side unit value, not pure exogenous price.",
    "A sizeable share is imputed and should be disclosed.",
    "Hedonic imputation explains a moderate share of log unit-value variation.",
    "RMSE implies noisy unit-value prediction.",
    "Observed-only robustness remains statistically similar for participation, but on a selected purchasing subsample."
  ),
  stringsAsFactors = FALSE
)
write_csv(price_diag, path("outputs", "tables", "tableN_price_unit_value_diagnostics.csv"))

## -------------------------------------------------------------------------
## I. Logs, JSON, and addendum report.
## -------------------------------------------------------------------------

model_summary <- rbind_fill(list(
  data.frame(output = "tableE_add_one_block_diagnostics.csv", rows = nrow(tableE), stringsAsFactors = FALSE),
  data.frame(output = "tableF_village_fe_robustness.csv", rows = nrow(tableF), stringsAsFactors = FALSE),
  data.frame(output = "tableG_binary_response_robustness.csv", rows = nrow(tableG), stringsAsFactors = FALSE),
  data.frame(output = "tableH_category_multiple_testing.csv", rows = nrow(tableH), stringsAsFactors = FALSE),
  data.frame(output = "tableI_category_variation_and_nsi_reframed.csv", rows = nrow(tableI), stringsAsFactors = FALSE),
  data.frame(output = "tableJ_fixed_common_sample_robustness.csv", rows = nrow(tableJ), stringsAsFactors = FALSE),
  data.frame(output = "tableK_fixed_factors_bad_controls_robustness.csv", rows = nrow(tableK), stringsAsFactors = FALSE),
  data.frame(output = "tableL_participation_missingness_robustness.csv", rows = nrow(missing_table), stringsAsFactors = FALSE),
  data.frame(output = "tableM_definition_diagnostics_editor.csv", rows = nrow(tableM), stringsAsFactors = FALSE),
  data.frame(output = "tableN_price_unit_value_diagnostics.csv", rows = nrow(price_diag), stringsAsFactors = FALSE)
))
write_simple_json(model_summary, path("outputs", "model_summaries", "modelE_editor_revision_analyses.json"), key = "editor_revision_outputs")

add_one_part <- tableE[tableE$outcome == "production_participation", c("label", "n", "n_clusters", "wald_chisq", "wald_p")]
add_one_log <- tableE[tableE$outcome == "log_selfprod_amount", c("label", "n", "n_clusters", "wald_chisq", "wald_p")]
village_overall <- tableF[tableF$label == "village_FE_M3_like", c("outcome", "n", "n_clusters", "wald_chisq", "wald_p")]
glm_overall <- tableG[tableG$label == "overall_M3", c("model_family", "n", "n_clusters", "outcome_mean", "converged", "wald_chisq", "wald_p")]
cat_report <- tableI[, c("food_category_label", "participation_rate", "mean_self_suff_rate", "nsi", "hhcomp_wald_p", "p_bh_fdr", "main_text_status")]
fixed_comp_report <- tableJ[tableJ$outcome == "production_participation", c("composition_spec", "n", "n_clusters", "wald_chisq", "wald_p")]
bad_report <- tableK[tableK$outcome == "production_participation", c("label", "n", "n_clusters", "wald_chisq", "wald_p")]

report_lines <- c(
  "# Paper 1 Editor-Revision Results Addendum",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "This addendum implements the additional diagnostics requested in `paper1_editor_review_and_action_plan.md`. It should be read together with `paper1_revised_results_package.md`.",
  "",
  "## 1. Revised Bottom Line / 修订后核心结论",
  "",
  "- 最稳妥的正文表述应改为：在加入省份、市场可达性、农业生态、购买侧单位值和县级文本控制后，户内人口结构能够条件性预测自产自给参与；但该结果对控制集敏感，且不能通过村庄固定效应的参与边际稳健性检验。",
  "- M1 以后数量边际整体较弱；固定共同样本下部分数量口径重新显著，说明数量结果具有样本和口径敏感性，应作为辅助描述而非主结论。",
  "- logit/probit 对总体 M3 参与边际给出相近结论，说明 M3 的参与结果不是简单 LPM 泛函形式造成的。",
  "- NSI 已重新定位为 Wald 检验统计量的相对可检测性排序，不是经济幅度指数；奶类因参与率接近 0 从主类别解释中剔除。",
  "",
  "## 2. Add-One-Block Diagnostics: Participation",
  "",
  md_table(add_one_part, digits = 4),
  "",
  "## 3. Add-One-Block Diagnostics: Log Quantity",
  "",
  md_table(add_one_log, digits = 4),
  "",
  "## 4. Village Fixed Effects Robustness",
  "",
  md_table(village_overall, digits = 4),
  "",
  "Interpretation: village fixed effects shift identification to within-village household comparisons. In this check, the participation-margin Wald test is not significant, while the log/IHS quantity margins become significant. This weakens any claim that the M3 participation result is fully robust. Village-level market, GAEZ, province, and much of county text variation are absorbed or collinear, so this is a robustness check rather than the preferred mechanism specification.",
  "",
  "## 5. Logit/Probit Participation Robustness",
  "",
  md_table(glm_overall, digits = 4),
  "",
  "Category-specific logit/probit rows are in `outputs/tables/tableG_binary_response_robustness.csv`; extreme categories, especially dairy, should be read with separation/low-variation caution.",
  "",
  "## 6. Category Multiple Testing and NSI Reframing",
  "",
  md_table(cat_report, digits = 4),
  "",
  "Interpretation: the category table now reports raw p-values and BH FDR q-values. NSI remains useful for describing where the Wald test is most detectable, but it is not an effect size. Participation and self-sufficiency are reported side by side to separate detectability from economic importance.",
  "",
  "## 7. Fixed Common-Sample Composition Robustness",
  "",
  md_table(fixed_comp_report, digits = 4),
  "",
  "The original robustness table used different samples across proportion, dependency-ratio, and count specifications. This fixed-sample table uses the intersection of all variables needed by all composition definitions and outcomes.",
  "",
  "## 8. Fixed-Factor / Bad-Control Sensitivity",
  "",
  md_table(bad_report, digits = 4),
  "",
  "The no-income/no-expense specifications respond to the concern that income and expenditure may be jointly determined with self-provisioning. These should be discussed alongside the full M3 results.",
  "",
  "## 9. Price and Unit-Value Diagnostics",
  "",
  md_table(price_diag, digits = 4),
  "",
  "Price variables should be described as purchase-side unit values. The hedonic values are imputations for missing purchase unit values, not farm-gate selling prices. This limits how strongly price controls can be interpreted in a market-separability framework.",
  "",
  "## 10. Data Definition Diagnostics",
  "",
  md_table(tableM, digits = 4),
  "",
  "## 11. Missingness Robustness Status",
  "",
  md_table(missing_table, digits = 4),
  "",
  "## 12. New Artifacts",
  "",
  md_table(model_summary, digits = 0)
)

writeLines(report_lines, path("outputs", "reports", "paper1_editor_revision_results_addendum.md"), useBytes = TRUE)

log_lines <- c(
  "# Editor Review Action Log",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "Completed with current analysis-ready data:",
  "",
  "- Add-one-block diagnostics for M0/M1/M2/M3 sensitivity and M1-to-M2 block attribution.",
  "- Village fixed-effects robustness for overall outcomes and category-specific participation.",
  "- Logit/probit participation robustness for overall and category-specific models.",
  "- Bonferroni, Holm, and BH FDR corrections for category-level Wald tests.",
  "- NSI reframing with participation/self-sufficiency and low-variation flags.",
  "- Fixed common-sample composition and price robustness checks.",
  "- Fixed-factor/no-income/no-expense sensitivity checks.",
  "- Price unit-value and hedonic imputation diagnostics.",
  "- Definition diagnostics for repeated-cross-section status, roster cap, land winsorization, sex coding, oils, and meat/aquatic aggregation.",
  "",
  "Still requires manual or raw-item-code work:",
  "",
  "- HA2 sex-codebook verification for `female_share` interpretation.",
  "- Item-code review for `youzhi` and detail-level rebuild if meat versus aquatic categories are to be split.",
  "- Raw item-level missing-code recovery before a valid NA-to-zero versus missing-exclusion participation robustness can be run.",
  "- Formal theoretical model and replacement of the placeholder conceptual framework figure."
)
writeLines(log_lines, path("outputs", "logs", "editor_review_action_log.md"), useBytes = TRUE)

message("Editor-revision analyses completed.")
````

## `code/15_write_manuscript_draft.py`

- Size: 42.1 KB
- Lines: 604

````python
#!/usr/bin/env python3
"""Build a conservative Paper 1 manuscript draft in Markdown and DOCX.

The manuscript intentionally follows the editor-review addendum rather than
the more optimistic earlier results package.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "manuscript"
OUT.mkdir(parents=True, exist_ok=True)

MD_OUT = OUT / "paper1_manuscript_draft_revised.md"
DOCX_OUT = OUT / "paper1_manuscript_draft_revised.docx"


def read_csv(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fnum(x: str | float | int | None, digits: int = 3) -> str:
    if x is None or x == "":
        return ""
    try:
        val = float(x)
    except (TypeError, ValueError):
        return str(x)
    if not math.isfinite(val):
        return ""
    if abs(val) < 0.001 and val != 0:
        return f"{val:.2e}"
    return f"{val:.{digits}f}"


def pval(x: str | float | int | None) -> str:
    if x is None or x == "":
        return ""
    try:
        val = float(x)
    except (TypeError, ValueError):
        return str(x)
    if val < 0.001:
        return "<0.001"
    return f"{val:.3f}"


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    out = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    for row in rows:
        clean = [str(x).replace("|", "\\|") for x in row]
        out.append("| " + " | ".join(clean) + " |")
    return "\n".join(out)


sample = {r["item"]: r["value"] for r in read_csv("outputs/tables/table1_sample_summary_revised.csv")}
cat_part = read_csv("outputs/tables/table1_category_participation_revised.csv")
baseline = read_csv("outputs/tables/table2_common_sample_baseline.csv")
coeffs = read_csv("outputs/tables/table3_baseline_coefficients_margins.csv")
twopart = read_csv("outputs/tables/table5_two_part_model.csv")
addblock = read_csv("outputs/tables/tableE_add_one_block_diagnostics.csv")
village = read_csv("outputs/tables/tableF_village_fe_robustness.csv")
binary = read_csv("outputs/tables/tableG_binary_response_robustness.csv")
cats = read_csv("outputs/tables/tableI_category_variation_and_nsi_reframed.csv")
fixed_comp = read_csv("outputs/tables/tableJ_fixed_common_sample_robustness.csv")
bad = read_csv("outputs/tables/tableK_fixed_factors_bad_controls_robustness.csv")
price_diag = read_csv("outputs/tables/tableN_price_unit_value_diagnostics.csv")
iv = read_csv("outputs/tables/tableB_iv_diagnostics_appendix.csv")
market_int = read_csv("outputs/tables/tableA_market_friction_interactions_appendix.csv")


def by(rows: list[dict[str, str]], **kwargs: str) -> list[dict[str, str]]:
    out = []
    for r in rows:
        if all(r.get(k) == v for k, v in kwargs.items()):
            out.append(r)
    return out


def one(rows: list[dict[str, str]], **kwargs: str) -> dict[str, str]:
    hits = by(rows, **kwargs)
    if not hits:
        raise KeyError(kwargs)
    return hits[0]


cat_order = ["zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo"]
cat_part_sorted = sorted(cat_part, key=lambda r: cat_order.index(r["food_category"]) if r["food_category"] in cat_order else 999)

table1_rows = [
    [
        r["food_category_label"],
        fnum(r["participation_rate"], 3),
        fnum(r["mean_self_suff_rate"], 3),
        fnum(r["mean_cons_monthly_jin"], 1),
        fnum(r["mean_selfprod_monthly_total"], 1),
    ]
    for r in cat_part_sorted
]

table2_rows = []
for outcome, label in [
    ("production_participation", "Participation"),
    ("log_selfprod_amount", "log(1 + self-produced quantity)"),
    ("ihs_selfprod_amount", "IHS self-produced quantity"),
]:
    for spec in ["M0", "M1", "M2", "M3"]:
        r = one(baseline, outcome=outcome, spec=spec)
        table2_rows.append([
            label,
            spec,
            r["n"],
            r["n_clusters"],
            fnum(r["hhcomp_wald_chisq"], 3),
            r["hhcomp_wald_df"],
            pval(r["hhcomp_wald_p"]),
        ])

add_part_rows = []
for label in [
    "B0_composition_category_year",
    "B1_plus_household_resources",
    "B1a_M1_plus_market",
    "B1b_M1_plus_GAEZ",
    "B1c_M1_plus_province_FE",
    "B2_full_market_GAEZ_province_FE",
    "B3_plus_unit_value_text",
]:
    r = one(addblock, outcome="production_participation", label=label)
    add_part_rows.append([
        label.replace("_", " "),
        fnum(r["wald_chisq"], 3),
        pval(r["wald_p"]),
    ])

table3_rows = []
for r in cats:
    table3_rows.append([
        r["food_category_label"],
        fnum(r["participation_rate"], 3),
        fnum(r["mean_self_suff_rate"], 3),
        fnum(r["nsi"], 3),
        pval(r["hhcomp_wald_p"]),
        pval(r["p_bh_fdr"]),
        r["main_text_status"],
    ])

rob_rows = []
for family in ["logit", "probit"]:
    r = one(binary, label="overall_M3", model_family=family)
    rob_rows.append([family.capitalize(), "Participation, M3", r["n"], r["n_clusters"], fnum(r["wald_chisq"], 3), pval(r["wald_p"])])
for outcome, label in [
    ("production_participation", "Village FE: participation"),
    ("log_selfprod_amount", "Village FE: log quantity"),
    ("ihs_selfprod_amount", "Village FE: IHS quantity"),
]:
    r = one(village, label="village_FE_M3_like", outcome=outcome)
    rob_rows.append([label, "Within-village comparison", r["n"], r["n_clusters"], fnum(r["wald_chisq"], 3), pval(r["wald_p"])])
for comp in ["proportion", "dependency", "counts"]:
    r = one(fixed_comp, composition_spec=comp, outcome="production_participation")
    rob_rows.append([f"Fixed sample: {comp}", "Participation", r["n"], r["n_clusters"], fnum(r["wald_chisq"], 3), pval(r["wald_p"])])
for label in ["fixed_factors_no_income_expense", "fixed_factors_no_income_expense_land_w99"]:
    r = one(bad, label=label, outcome="production_participation")
    rob_rows.append([label.replace("_", " "), "Participation", r["n"], r["n_clusters"], fnum(r["wald_chisq"], 3), pval(r["wald_p"])])

price_rows = [[r["diagnostic"], fnum(r["value"], 3), r["interpretation"]] for r in price_diag]

hh_coeff_rows = []
for term in ["household_size_reconstructed", "child_share", "elderly_share", "female_share"]:
    r = one(coeffs, outcome="production_participation", spec="M3", term=term)
    hh_coeff_rows.append([
        term,
        fnum(r["estimate"], 4),
        fnum(r["std_error_cluster"], 4),
        pval(r["p_value"]),
        r["direction"],
    ])

twopart_rows = []
for r in twopart:
    twopart_rows.append([
        r.get("part", r.get("model_part", "")),
        r["outcome"],
        r["n"],
        fnum(r.get("wald_chisq", r.get("hhcomp_wald_chisq", "")), 3),
        pval(r.get("wald_p", r.get("hhcomp_wald_p", ""))),
    ])

iv_rows = []
for r in iv:
    iv_rows.append([
        r.get("instrument", r.get("iv_name", r.get("iv_spec", ""))),
        fnum(r.get("min_first_stage_f", r.get("min_first_stage_F", r.get("min_f", ""))), 3),
        fnum(r.get("median_first_stage_f", r.get("median_first_stage_F", r.get("median_f", ""))), 3),
        r.get("weak_instrument_flag", r.get("weak_iv_flag", r.get("weak", ""))),
    ])

market_rows = []
for r in market_int:
    market_rows.append([
        r.get("friction_spec", r.get("model", "")),
        r["outcome"],
        fnum(r.get("interaction_wald_chisq", r.get("wald_chisq", "")), 3),
        pval(r.get("interaction_wald_p", r.get("wald_p", ""))),
    ])


manuscript = rf"""# Household Composition and Self-Provisioning: Multi-Category Evidence on Non-Separability in Rural China

**Draft date:** 2026-06-08  
**Status:** revised conservative manuscript draft based on the editor-review action plan  

## Abstract

Agricultural household models predict that, under complete markets and price-taking behavior, production decisions should be separable from household preferences and demographic composition. Most empirical tests of this prediction focus on labor demand or production input choices. This paper studies a different but substantively important margin: whether rural households enter self-provisioning for specific food categories. Using a pooled repeated cross-section of 3,565 rural Chinese households observed in 2023 or 2024, converted to 28,520 household-category observations across eight food categories, I test whether household size, child share, elderly share, and female share jointly predict category-specific self-provisioning. The preferred common-sample specification indicates that household composition predicts self-provisioning participation after controlling for household resources, local market access, agro-ecological suitability, purchase-side unit values, county text indicators, food-category fixed effects, province fixed effects, and survey-year fixed effects (Wald = 16.733, p = 0.002). The evidence is concentrated on the participation margin: full-sample transformed quantity outcomes are not significant in the preferred specification. However, the result is control-set sensitive. It is not significant in parsimonious specifications and does not survive a village fixed-effects participation-margin check, although log and IHS quantity margins become significant within villages. Category-level tests show strongest detectability for eggs, oils, vegetables, and fruits after false-discovery-rate adjustment, but these rankings should be interpreted as test-statistic detectability rather than economic magnitudes. The results provide cautious reduced-form evidence that household composition remains conditionally associated with rural food self-provisioning, while also underscoring the limits of cross-sectional separability tests without stronger panel or instrumental-variable identification.

**Keywords:** agricultural household model; separability; self-provisioning; household composition; rural China; food categories; market imperfections

## 1. Introduction

Rural households often make production and consumption decisions inside the same family enterprise. The classic separable agricultural household model offers a sharp benchmark: if markets are complete, all relevant prices are taken as given, and households can buy or sell goods and labor freely, production choices should be independent of household preferences and demographic composition. This recursive structure has made the agricultural household model one of the central tools in development and agricultural economics.

The empirical literature has most often tested this implication through farm labor demand. Benjamin (1992) tests whether household composition enters labor demand equations in Chinese agriculture. LaFave and Thomas (2016) revisit the same logic with longitudinal Indonesian data and reject the recursive model using within-household variation in composition and labor demand. These studies give the separability hypothesis a concrete empirical content: demographic variables that shape preferences and household labor endowments should not predict production choices once prices and fixed production factors are controlled.

This paper asks whether a related separability restriction holds for food self-provisioning. Instead of studying how much labor a household uses on the farm, I study whether the household produces part of its own food consumption in a category such as staples, eggs, vegetables, fruit, oils, beans, meat and aquatic products, or dairy. This margin matters because self-provisioning is common in rural settings and directly links production to consumption. It is also conceptually close to incomplete-market models: when buying and selling are frictionless at a common price, producing for own consumption is not economically distinct from producing for sale and buying food back. When transaction costs, quality differences, home-production preferences, or missing markets create a wedge between market purchase and household production, the decision to self-provision can become household-specific.

The empirical object is a pooled repeated cross-section of rural Chinese households. Each household appears in one survey year, 2023 or 2024, and contributes eight food-category rows. The final revised analysis file contains {sample.get("rows", "28,520")} rows, {sample.get("households", "3,565")} households, {sample.get("food_categories", "8")} food categories, {sample.get("villages_clusters", "361")} villages, {sample.get("counties", "44")} counties, and {sample.get("provinces", "9")} provinces. The design is not a household panel: each household identifier is observed in one year only. For this reason, the paper does not claim household fixed-effects identification. It implements a Benjamin-type reduced-form test in pooled cross-section and then evaluates how sensitive the result is to richer controls and village fixed effects.

The central finding is deliberately stated cautiously. Household composition significantly predicts self-provisioning participation in the preferred M3 common-sample specification, but not in simpler M0 or M1 specifications. The participation result appears after adding market-access, agro-ecological, and province controls, and remains significant when estimated with logit and probit. Yet it does not survive a village fixed-effects participation check. This pattern suggests that the data support a conditional association between household composition and self-provisioning, especially on the extensive margin, but do not justify a strong causal or structural claim that household demographics independently determine self-provisioning.

The paper makes three contributions. First, it extends separability testing from farm input demand to the food self-provisioning margin. Second, it shows that the association between household composition and self-provisioning is highly category-specific: eggs, oils, vegetables, and fruits remain significant after Benjamini-Hochberg false-discovery-rate correction, while dairy has too little variation to interpret substantively. Third, it provides a transparent account of weak evidence. Market-friction interactions do not provide strong mechanism evidence, candidate instrumental variables have weak first stages, purchase-side unit values are imperfect price proxies, and village fixed effects weaken the participation result.

## 2. Conceptual Framework

The separable agricultural household model starts from a household that derives utility from consumption goods and leisure while operating a production technology. When all output, input, labor, credit, and consumption markets are complete, and the household takes prices as given, production can be solved independently from consumption. The household first maximizes farm profit conditional on prices and fixed factors. Consumption and labor allocation are then chosen given income. In this recursive model, variables that shift preferences or household demographic needs should not enter production demand equations after conditioning on prices and fixed production factors.

The standard empirical restriction is therefore an exclusion restriction. Let \(y_{{hct}}\) denote a production-side outcome for household \(h\), category \(c\), and year \(t\). Let \(D_h\) be household composition and \(X_h\), \(M_v\), \(A_v\), and \(P_{{hct}}\) denote household resources, local market environment, agro-ecological conditions, and prices or price proxies. Under separability, conditional on the appropriate production-side controls, \(D_h\) should not predict \(y_{{hct}}\). The empirical test is whether the coefficients on household composition are jointly zero.

Self-provisioning requires one additional step in interpretation. The outcome in this paper is not total farm output or labor demand; it is whether households produce for their own consumption in a food category. In a world with no transaction costs and no quality or preference wedge between home-produced and purchased food, self-provisioning is not a distinct structural object: a household can sell output and buy the same food, or consume its own output, with no meaningful economic difference. In incomplete-market models with fixed or proportional transaction costs, however, households may face different effective buying and selling prices. The buy-sell price band can make non-participation or self-provisioning rational, and the household's demographic needs may become correlated with production-for-own-consumption decisions.

This logic implies a cautious interpretation. If household composition predicts self-provisioning, the recursive separability benchmark is strained. But the rejection can arise for several reasons: transaction costs and missing markets, home-produced food as a differentiated quality good, household-specific tastes for freshness or safety, or unobserved family orientation toward agriculture. The cross-sectional design cannot fully distinguish among these channels. I therefore treat market-friction interactions and instrumental-variable diagnostics as exploratory mechanism checks rather than the main identification basis.

## 3. Data and Variable Construction

### 3.1 Sample Structure

The analysis uses a pooled repeated cross-section of rural households. The sample contains one household-year per household identifier; no household appears in both survey years under the available identifier. The household-category file stacks eight food categories for each household. This yields {sample.get("rows", "28,520")} household-category observations from {sample.get("households", "3,565")} households.

The data cover nine provinces and 44 counties. Village identifiers are used for clustering and for a village fixed-effects robustness check. Because the sample is a repeated cross-section rather than a panel, the main specification uses food-category, year, and province fixed effects but not household fixed effects. Village fixed effects are feasible and are reported as a stringent robustness check that absorbs all time-invariant village-level differences in local markets, agricultural ecology, and food-production norms.

### 3.2 Outcomes

The primary outcome is an indicator for self-provisioning participation:

\[
Participation_{{hct}} = 1(SelfProducedQuantity_{{hct}} > 0).
\]

Two transformed quantity outcomes are used as secondary margins: \(\log(1 + SelfProducedQuantity_{{hct}})\) and \(asinh(SelfProducedQuantity_{{hct}})\). These transformations retain zero observations but are not scale-invariant; the paper therefore avoids elasticity-style interpretations and treats them as robustness outcomes. A self-sufficiency rate, defined as the share of category consumption supplied by self-production, is used in supplementary robustness checks.

### 3.3 Household Composition

The main household-composition variables are household size, child share, elderly share, and female share. They are intended to capture demographic structure rather than exogenous treatment. The sex-coding audit indicates that the gender code used to construct female share still requires manual codebook verification, so results involving female share should be interpreted with that caveat. The household roster is capped at eight members; 18 of 3,565 households reach this cap, or about 0.5 percent.

### 3.4 Controls

The preferred specification controls for household resources and fixed factors, including income and expenditure measures, agricultural and off-farm labor days, total sown area, household assets, and household-head characteristics. Because income and expenditure may be jointly determined with self-provisioning, I also report specifications that drop income and expenditure and condition only on fixed factors and price/unit-value controls.

Village and county context are measured using survey-based market-friction indices, lagged point-of-interest measures, agro-ecological suitability from GAEZ, and county-level text indicators. Food-category and survey-year fixed effects are included throughout the pooled models; province fixed effects are added in the richer specifications.

### 3.5 Prices and Unit Values

The available price proxy is a household purchase-side unit value, constructed from purchase expenditure divided by purchase quantity and measured in yuan per jin. It should not be interpreted as a pure exogenous market price or a farm-gate selling price. The distinction matters because the wedge between buying and selling prices is part of the incomplete-market mechanism that could generate self-provisioning. In the analysis file, 73.1 percent of unit values are observed from household purchase data and 26.9 percent are imputed using a hedonic model; the county-level hedonic model has an \(R^2\) of about 0.43 and log RMSE of about 0.72. Price robustness is therefore interpreted cautiously.

### 3.6 Descriptive Patterns

Table 1 summarizes category-level participation and self-sufficiency. Vegetables and staples have high participation rates, while dairy is almost degenerate. Dairy participation is only 0.13 percent, so dairy is excluded from substantive category interpretation. Vegetables and staples also require caution because participation is near the upper end of the distribution, leaving limited variation in the binary participation outcome.

**Table 1. Category-Level Self-Provisioning and Consumption**

{md_table(["Category", "Participation", "Self-sufficiency", "Mean consumption (jin/month)", "Mean self-produced (jin/month)"], table1_rows)}

## 4. Empirical Strategy

The main specification estimates

\[
y_{{hct}} = \alpha + D_h'\beta + X_h'\gamma + M_v'\delta + A_v'\theta + P_{{hct}}\pi + \mu_c + \lambda_t + \rho_p + \varepsilon_{{hct}},
\]

where \(y_{{hct}}\) is participation or a transformed quantity outcome, \(D_h\) is the vector of household-composition variables, \(X_h\) contains household resources and head characteristics, \(M_v\) contains market-access measures, \(A_v\) contains agro-ecological controls, \(P_{{hct}}\) is the unit-value proxy, \(\mu_c\) are food-category fixed effects, \(\lambda_t\) are year fixed effects, and \(\rho_p\) are province fixed effects. Standard errors are clustered at the village level.

The test of interest is a joint Wald test of

\[
H_0: \beta_{{size}} = \beta_{{child}} = \beta_{{elderly}} = \beta_{{female}} = 0.
\]

The models are organized as follows. M0 includes household composition, food-category fixed effects, and year fixed effects. M1 adds household resources and head controls. M2 adds market-friction controls, POI market measures, agro-ecological controls, and province fixed effects. M3 adds purchase-side unit values and county text controls.

The empirical design is a reduced-form separability test. It does not estimate a causal treatment effect of household composition. Household structure may be endogenous to migration, co-residence, agricultural orientation, and other unobserved factors. Under the separability null, however, demographic variables should be excluded from the production-side equation; observing a conditional association is therefore informative about the empirical adequacy of the separable benchmark, even if the mechanism behind rejection remains ambiguous.

## 5. Main Results

### 5.1 Baseline Wald Tests

Table 2 reports the M0-M3 sequence on the common M3 sample. The preferred M3 participation model rejects the joint exclusion of household composition (Wald = 16.733, p = 0.002). The same is not true in the parsimonious specifications: M0 has p = 0.178 and M1 has p = 0.106. The participation result becomes significant only after adding market, agro-ecological, and province controls.

The quantity outcomes show the opposite pattern. The log and IHS quantity outcomes are significant in M0 but collapse after household resources are added in M1. In M3, both full-sample quantity outcomes are insignificant. This contrast supports an extensive-margin interpretation in the preferred pooled specification, but it also reveals that the empirical pattern is sensitive to the control set.

**Table 2. Household-Composition Wald Tests Across Baseline Specifications**

{md_table(["Outcome", "Spec", "N", "Clusters", "Wald", "df", "p"], table2_rows)}

### 5.2 Which Controls Drive the Participation Result?

Table 3 decomposes the shift from M1 to M2. Adding market controls alone moves the participation test to p = 0.046; adding GAEZ controls alone gives p = 0.022; adding province fixed effects alone gives p = 0.012. The strongest intermediate block combines GAEZ and province fixed effects. This pattern means the M3 result should not be presented as invariant across reasonable specifications. Rather, it is a conditional association that emerges after accounting for regional, market-access, and agro-ecological heterogeneity.

**Table 3. Add-One-Block Diagnostics for Participation**

{md_table(["Specification block", "Wald", "p"], add_part_rows)}

### 5.3 Coefficient Patterns

In the preferred M3 participation model, household size is negatively associated with self-provisioning participation, elderly share is positively associated, child share is marginally positive, and female share is not statistically significant. The negative household-size coefficient may appear counterintuitive if size is treated only as labor availability; it may also reflect differences between larger non-agricultural households and smaller agriculturally oriented households after conditioning on resources. The elderly-share coefficient is more consistent with a household life-cycle or home-production interpretation, but it remains descriptive.

**Table 4. M3 Household-Composition Coefficients for Participation**

{md_table(["Variable", "Estimate", "Cluster SE", "p", "Direction"], hh_coeff_rows)}

## 6. Extensive and Intensive Margins

The two-part model separates entry into self-provisioning from conditional intensity among households that enter. Part 1 reproduces the participation result on all observations. Part 2 estimates log self-produced quantity only among positive self-provisioning observations. The conditional-intensity test is significant at the 5 percent level in this selected sample, but this result is descriptive because selection into the positive-production sample is itself a function of household composition.

**Table 5. Two-Part Model**

{md_table(["Part", "Outcome", "N", "Wald", "p"], twopart_rows)}

For this reason, the paper treats participation as the primary margin and conditional intensity as supplementary. The full-sample log and IHS models do not reject in M3, and transformed outcomes with many zeros are sensitive to scale and transformation choices.

## 7. Category Heterogeneity

Table 6 reports category-specific tests for participation. The Non-Separability Index (NSI) is defined as a category's household-composition Wald statistic divided by the mean Wald statistic across categories. This index is a relative detectability ranking, not an economic effect size. It combines coefficient magnitudes, residual variation, and precision. NSI values above one therefore mean only that the category's Wald statistic is above the category average.

After Benjamini-Hochberg FDR correction, eggs, oils, vegetables, and fruits remain significant at 5 percent. Beans is significant before correction but not after FDR correction. Oils require definition caution because the item-code audit is incomplete. Vegetables have the highest self-sufficiency rate but also high participation, so binary variation is compressed near the ceiling. Dairy is excluded from main category interpretation because almost no households self-provision dairy.

**Table 6. Category-Specific Detectability and Economic Importance**

{md_table(["Category", "Participation", "Self-sufficiency", "NSI", "Raw p", "BH FDR p", "Interpretation status"], table3_rows)}

The category results are substantively useful but should not be overread. Eggs have the strongest detectability ranking, but vegetables and staples are more economically important in self-sufficiency terms. This divergence illustrates why the paper reports participation rates and self-sufficiency alongside the Wald-based ranking.

## 8. Robustness and Sensitivity

Table 7 summarizes the main robustness checks. Logit and probit estimates of participation produce similar overall M3 Wald tests, indicating that the preferred participation result is not simply an artifact of the linear probability model. Fixed common-sample composition checks also support the participation result across proportion, dependency-ratio, and count measures.

The village fixed-effects check is more challenging for the main interpretation. With village fixed effects, the participation-margin Wald test is not significant (p = 0.171). The log and IHS quantity margins become significant under village fixed effects. This finding shifts the interpretation: the pooled M3 participation result is robust to functional form but not to fully absorbing village-level heterogeneity. The paper should therefore avoid language implying that the participation result is universally stable.

Dropping income and expenditure controls does not weaken the participation result. In fixed-factor specifications without income and expenditure, the participation Wald test remains significant. This reduces concern that the M3 participation result is produced only by conditioning on potentially endogenous financial variables.

**Table 7. Robustness Summary**

{md_table(["Check", "Outcome/specification", "N", "Clusters", "Wald", "p"], rob_rows)}

## 9. Mechanism Diagnostics

The preferred interpretation is that household composition is conditionally associated with self-provisioning participation. A stronger mechanism claim would require evidence that this association is amplified where markets are less complete or more costly to access. The available market-friction interactions do not provide that evidence. Interaction Wald tests using survey market friction, POI market friction, and combined market-friction measures are statistically weak across participation and quantity outcomes.

**Appendix Table A. Market-Friction Interaction Diagnostics**

{md_table(["Friction specification", "Outcome", "Wald", "p"], market_rows[:9])}

Candidate instrumental variables are also weak. Terrain-barrier and early-nighttime-light instruments have first-stage F-statistics far below conventional thresholds. IV results are therefore not used as evidence for causal identification.

**Appendix Table B. IV First-Stage Diagnostics**

{md_table(["Instrument", "Minimum F", "Median F", "Weak flag"], iv_rows)}

## 10. Price and Measurement Diagnostics

Table 8 summarizes the unit-value diagnostics. The observed measure is a purchase-side unit value, not a farm-gate output price. It may contain quality variation, quantity discounts, and selection into purchasing. Households that self-provision heavily may not purchase the category and therefore may have imputed rather than observed unit values. For these reasons, price controls are best understood as imperfect controls for local food-cost conditions rather than clean exogenous prices.

**Table 8. Price and Unit-Value Diagnostics**

{md_table(["Diagnostic", "Value", "Interpretation"], price_rows)}

Several data-definition limitations remain. The oils category requires item-code verification before strong substantive claims are made. Meat and aquatic products are aggregated with processed products in the current long file, limiting interpretation of protein-category heterogeneity. The current analysis-ready and cleaned long files no longer preserve item-level missingness for self-produced quantities, so a valid missing-exclusion versus missing-as-zero participation robustness check requires returning to raw item-level missing codes.

## 11. Discussion

The empirical evidence is best read as a disciplined but cautious separability test. The preferred pooled specification rejects the joint exclusion of household composition on the self-provisioning participation margin. The result is not driven by LPM functional form and remains when income and expenditure controls are removed. The category pattern also suggests that self-provisioning is not a uniform rural practice: it is more detectable for eggs, oils, vegetables, and fruits than for staples, meat/aquatic products, or dairy.

At the same time, the paper's limitations are central to its contribution. First, the data are pooled repeated cross-sections, not a panel. The design cannot absorb time-invariant household heterogeneity. Second, the participation result is control-set sensitive and does not survive village fixed effects. Third, market-friction interactions are weak, so the data do not strongly establish transaction costs as the specific channel. Fourth, unit values are imperfect price proxies. Fifth, category definitions for oils and meat/aquatic products require additional item-level validation.

These limitations imply that the paper should not claim a structural rejection of complete markets in the strong sense achieved by panel household fixed-effects designs. Instead, it contributes evidence on a less-studied margin: category-specific self-provisioning participation. The findings suggest that household demographic structure remains relevant for this margin even after rich controls, but that part of the relationship may reflect village-level heterogeneity, category measurement, and unobserved household orientation toward agriculture.

## 12. Conclusion

This paper studies whether household composition predicts food self-provisioning in rural China. Using a multi-category household-category dataset, I test the exclusion of household size, child share, elderly share, and female share from self-provisioning participation and quantity equations. In the preferred pooled specification, household composition significantly predicts participation, while full-sample quantity outcomes are weaker. The association is concentrated in selected categories and remains visible under logit and probit participation models, but it is sensitive to the inclusion of regional and village-level controls.

The main conclusion is therefore conservative: household composition conditionally predicts entry into self-provisioning, providing reduced-form evidence that the separable agricultural household benchmark is incomplete for this margin. The evidence does not establish a causal demographic effect or a clean market-friction mechanism. Future work should use panel data, validated item-level category definitions, better farm-gate and purchase price measures, and stronger instruments or natural experiments to distinguish market incompleteness from home-good quality preferences and unobserved household heterogeneity.

## References

Anderson, Michael L. 2008. "Multiple Inference and Gender Differences in the Effects of Early Intervention: A Reevaluation of the Abecedarian, Perry Preschool, and Early Training Projects." *Journal of the American Statistical Association* 103(484): 1481-1495.

Bellemare, Marc F., and Casey J. Wichman. 2020. "Elasticities and the Inverse Hyperbolic Sine Transformation." *Oxford Bulletin of Economics and Statistics* 82(1): 50-61.

Benjamin, Dwayne. 1992. "Household Composition, Labor Markets, and Labor Demand: Testing for Separation in Agricultural Household Models." *Econometrica* 60(2): 287-322.

Chen, Jiafeng, and Jonathan Roth. 2024. "Logs with Zeros? Some Problems and Solutions." Working paper.

de Janvry, Alain, Marcel Fafchamps, and Elisabeth Sadoulet. 1991. "Peasant Household Behaviour with Missing Markets: Some Paradoxes Explained." *Economic Journal* 101(409): 1400-1417.

Deaton, Angus. 1988. "Quality, Quantity, and Spatial Variation of Price." *American Economic Review* 78(3): 418-430.

Heckman, James J. 1979. "Sample Selection Bias as a Specification Error." *Econometrica* 47(1): 153-161.

Key, Nigel, Elisabeth Sadoulet, and Alain de Janvry. 2000. "Transactions Costs and Agricultural Household Supply Response." *American Journal of Agricultural Economics* 82(2): 245-259.

LaFave, Daniel, and Duncan Thomas. 2016. "Farms, Families, and Markets: New Evidence on Completeness of Markets in Agricultural Settings." *Econometrica* 84(5): 1917-1960.

Singh, Inderjit, Lyn Squire, and John Strauss, eds. 1986. *Agricultural Household Models: Extensions, Applications, and Policy*. Baltimore: Johns Hopkins University Press.
"""

MD_OUT.write_text(manuscript, encoding="utf-8")


def build_docx() -> None:
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor

    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Inches(8.5)
    sec.page_height = Inches(11)
    for margin in ["top_margin", "bottom_margin", "left_margin", "right_margin"]:
        setattr(sec, margin, Inches(1))
    sec.header_distance = Inches(0.492)
    sec.footer_distance = Inches(0.492)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Arial"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(8)
    normal.paragraph_format.line_spacing = 1.15

    for style_name, size, before, after, color in [
        ("Heading 1", 20, 20, 6, "000000"),
        ("Heading 2", 16, 18, 6, "000000"),
        ("Heading 3", 14, 16, 4, "434343"),
    ]:
        st = styles[style_name]
        st.font.name = "Arial"
        st._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
        st.font.size = Pt(size)
        st.font.bold = False
        st.font.color.rgb = RGBColor.from_string(color)
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.line_spacing = 1.15

    def add_plain_title(text: str) -> None:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(3)
        run = p.add_run(text)
        run.font.name = "Arial"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
        run.font.size = Pt(26)
        run.font.bold = False
        run.font.color.rgb = RGBColor(0, 0, 0)

    def set_cell_text(cell, text: str, bold: bool = False) -> None:
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(str(text))
        run.font.name = "Arial"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
        run.font.size = Pt(8.5)
        run.font.bold = bold

    def set_table_borders(table) -> None:
        tbl = table._tbl
        tblPr = tbl.tblPr
        borders = tblPr.first_child_found_in("w:tblBorders")
        if borders is None:
            borders = OxmlElement("w:tblBorders")
            tblPr.append(borders)
        for edge in ["top", "left", "bottom", "right", "insideH", "insideV"]:
            tag = "w:" + edge
            element = borders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                borders.append(element)
            element.set(qn("w:val"), "single")
            element.set(qn("w:sz"), "4")
            element.set(qn("w:space"), "0")
            element.set(qn("w:color"), "DADCE0")

    def add_docx_table(headers: list[str], rows: list[list[str]]) -> None:
        table = doc.add_table(rows=1, cols=len(headers))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        set_table_borders(table)
        hdr = table.rows[0].cells
        for i, h in enumerate(headers):
            set_cell_text(hdr[i], h, bold=True)
        for row in rows:
            cells = table.add_row().cells
            for i, val in enumerate(row):
                set_cell_text(cells[i], val)
        doc.add_paragraph()

    add_plain_title("Household Composition and Self-Provisioning")
    subtitle = doc.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(8)
    r = subtitle.add_run("Multi-Category Evidence on Non-Separability in Rural China")
    r.font.name = "Arial"
    r.font.size = Pt(14)
    r.font.color.rgb = RGBColor(85, 85, 85)
    meta = doc.add_paragraph("Revised conservative manuscript draft | 2026-06-08")
    meta.paragraph_format.space_after = Pt(12)

    current_table = None
    pending_table = None
    lines = manuscript.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("# "):
            i += 1
            continue
        if line.startswith("## "):
            doc.add_heading(line[3:], level=1)
        elif line.startswith("### "):
            doc.add_heading(line[4:], level=2)
        elif line.startswith("**Draft date:**") or line.startswith("**Status:**"):
            # Already represented in the clean metadata line below the title.
            pass
        elif line.startswith("**Keywords:**"):
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(8)
            run = p.add_run("Keywords: ")
            run.bold = True
            rest = line.replace("**Keywords:**", "").strip()
            p.add_run(rest)
        elif line.startswith("**Table") or line.startswith("**Appendix Table"):
            p = doc.add_paragraph()
            run = p.add_run(line.replace("**", ""))
            run.bold = True
            p.paragraph_format.space_after = Pt(4)
        elif line.startswith("| "):
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            headers = [x.strip() for x in table_lines[0].strip("|").split("|")]
            rows = []
            for tl in table_lines[2:]:
                rows.append([x.strip() for x in tl.strip("|").split("|")])
            add_docx_table(headers, rows)
            continue
        elif line.strip() == "":
            pass
        elif line.startswith("\\[") or line.startswith("$$") or line.startswith("\\]"):
            pass
        elif line.startswith("\\"):
            # Keep displayed equations readable as plain text in the DOCX draft.
            p = doc.add_paragraph(line)
            p.paragraph_format.left_indent = Inches(0.25)
        else:
            p = doc.add_paragraph(line)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        i += 1

    doc.core_properties.title = "Household Composition and Self-Provisioning"
    doc.core_properties.subject = "Paper 1 revised manuscript draft"
    doc.core_properties.author = "Generated by Codex from local analysis outputs"
    doc.save(DOCX_OUT)


if __name__ == "__main__":
    build_docx()
    print(f"Wrote {MD_OUT}")
    print(f"Wrote {DOCX_OUT}")
````

## `code/16_llm_manuscript_revision.py`

- Size: 24.3 KB
- Lines: 625

````python
#!/usr/bin/env python3
"""LLM-assisted manuscript revision workflow.

DeepSeek is used for token-heavy manuscript rewriting/integration.
Claude is used as an external reviewer.

API keys are read interactively or from environment variables and are never
written to disk.
"""

from __future__ import annotations

import getpass
import http.client
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "manuscript"
LOG_DIR = ROOT / "outputs" / "logs"
OUT.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

CURRENT_DRAFT = OUT / "paper1_manuscript_draft_revised.md"
EDITOR_PLAN = ROOT / "paper1_editor_review_and_action_plan.md"
ADDENDUM = ROOT / "outputs" / "reports" / "paper1_editor_revision_results_addendum.md"
RESULTS_PACKAGE = ROOT / "outputs" / "reports" / "paper1_revised_results_package.md"

DEEPSEEK_DRAFT = OUT / "paper1_manuscript_deepseek_rewrite.md"
CLAUDE_REVIEW = OUT / "paper1_claude_reviewer_comments.md"
FINAL_MD = OUT / "paper1_manuscript_llm_revised_final.md"
FINAL_DOCX = OUT / "paper1_manuscript_llm_revised_final.docx"
CALL_LOG = LOG_DIR / "llm_manuscript_revision_log.md"
DEEPSEEK_FRONT = OUT / "paper1_manuscript_deepseek_front.md"
DEEPSEEK_BACK = OUT / "paper1_manuscript_deepseek_back.md"
CLAUDE_FRONT = OUT / "paper1_claude_reviewer_front.md"
CLAUDE_BACK = OUT / "paper1_claude_reviewer_back.md"
CLAUDE_BACK_RESULTS = OUT / "paper1_claude_reviewer_back_results.md"
CLAUDE_BACK_DISCUSSION = OUT / "paper1_claude_reviewer_back_discussion.md"
FINAL_FRONT = OUT / "paper1_manuscript_llm_final_front.md"
FINAL_BACK = OUT / "paper1_manuscript_llm_final_back.md"


DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-v4-pro"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-sonnet-4-6"


def read_text(path: Path, max_chars: int | None = None) -> str:
    text = path.read_text(encoding="utf-8")
    if max_chars and len(text) > max_chars:
        return text[:max_chars] + "\n\n[TRUNCATED BY LOCAL WORKFLOW]\n"
    return text


def post_json(url: str, headers: dict[str, str], payload: dict, timeout: int = 240, retries: int = 2) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {e.code} from {url}: {detail[:2000]}") from e
        except (http.client.IncompleteRead, http.client.RemoteDisconnected, TimeoutError, urllib.error.URLError) as e:
            last_error = e
            if attempt < retries:
                time.sleep(4 + 3 * attempt)
                continue
            break
    raise RuntimeError(f"Request to {url} failed after retries: {last_error}") from last_error


def deepseek_chat(api_key: str, messages: list[dict[str, str]], max_tokens: int = 14000) -> str:
    return deepseek_chat_stream(api_key, messages, max_tokens=max_tokens)


def deepseek_chat_stream(api_key: str, messages: list[dict[str, str]], max_tokens: int = 8000) -> str:
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.25,
        "max_tokens": max_tokens,
        "stream": True,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    last_error: Exception | None = None
    for attempt in range(3):
        req = urllib.request.Request(DEEPSEEK_URL, data=data, headers=headers, method="POST")
        pieces: list[str] = []
        try:
            with urllib.request.urlopen(req, timeout=360) as resp:
                for raw in resp:
                    line = raw.decode("utf-8", errors="replace").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    event = line[len("data:"):].strip()
                    if event == "[DONE]":
                        break
                    try:
                        obj = json.loads(event)
                    except json.JSONDecodeError:
                        continue
                    choice = obj.get("choices", [{}])[0]
                    delta = choice.get("delta", {})
                    text = delta.get("content") or choice.get("message", {}).get("content") or ""
                    if text:
                        pieces.append(text)
                text = "".join(pieces)
                if text.strip():
                    return text
                raise RuntimeError("DeepSeek stream returned no text.")
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {e.code} from DeepSeek: {detail[:2000]}") from e
        except (http.client.IncompleteRead, TimeoutError, urllib.error.URLError, RuntimeError) as e:
            last_error = e
            if pieces:
                return "".join(pieces)
            time.sleep(4 + 3 * attempt)
    raise RuntimeError(f"DeepSeek streaming request failed after retries: {last_error}") from last_error


def get_or_generate(path: Path, label: str, fn) -> str:
    if path.exists() and path.stat().st_size > 100:
        print(f"Using cached {label}: {path}", flush=True)
        return path.read_text(encoding="utf-8")
    text = clean_markdown(fn())
    path.write_text(text, encoding="utf-8")
    print(f"Wrote {label}: {path}", flush=True)
    return text


def claude_review(api_key: str, prompt: str, max_tokens: int = 6000) -> str:
    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": prompt}],
    }
    out = post_json(
        ANTHROPIC_URL,
        {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        payload,
        timeout=300,
    )
    try:
        return "\n".join(part.get("text", "") for part in out["content"] if part.get("type") == "text")
    except Exception as e:
        raise RuntimeError(f"Unexpected Claude response shape: {json.dumps(out)[:2000]}") from e


def clean_markdown(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:markdown)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip() + "\n"


def build_deepseek_rewrite_prompt(current: str, editor: str, addendum: str, results: str) -> list[dict[str, str]]:
    system = (
        "You are a senior agricultural/development economics manuscript writer. "
        "Rewrite a complete conservative English paper draft using only the supplied evidence. "
        "Do not invent data, specifications, significance, citations, or causal claims. "
        "Keep all reviewer caveats explicit. Output Markdown only, with no code fences."
    )
    user = f"""
Task: Produce a polished full manuscript draft for Paper 1.

Mandatory stance:
- This is a pooled repeated-cross-section reduced-form separability test, not a causal paper.
- Main wording must be conservative: M3 participation is significant, but the result is control-set sensitive and does not survive the village-FE participation check.
- Quantity margins are secondary and sensitive.
- NSI is a relative Wald-statistic detectability ranking, not an economic magnitude.
- Dairy must be excluded from substantive category interpretation.
- Price is purchase-side unit value, not farm-gate price.
- Market-friction interactions and IV diagnostics are weak/exploratory.

Desired output:
- Complete English manuscript in Markdown.
- Include Abstract, Introduction, Conceptual Framework, Data, Empirical Strategy, Results, Robustness/Sensitivity, Mechanism Diagnostics, Discussion, Conclusion, References.
- Include concise Markdown tables when useful, but do not create new results.
- Use an academic but plain style suitable for AJAE/ERAE/Food Policy revision.

Current Codex draft:
{current}

Editor/reviewer action plan:
{editor}

Editor-revision empirical addendum:
{addendum}

Earlier revised results package:
{results}
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_claude_review_prompt(draft: str, addendum: str) -> str:
    return f"""
You are a skeptical reviewer for AJAE, ERAE, Food Policy, or AEPP.

Review the manuscript below. Focus on whether the draft:
1. overclaims separability rejection or causality;
2. transparently handles control-set sensitivity and the village fixed-effects result;
3. treats NSI correctly as detectability rather than economic magnitude;
4. handles price/unit-value limitations correctly;
5. handles two-part model selection and weak IV/mechanism evidence correctly;
6. has missing tables, confusing structure, or unclear contribution;
7. needs wording changes before being circulated.

Return an actionable review memo with:
- Major issues;
- Minor issues;
- Specific passages or claims to revise;
- A concise recommended revision strategy.

Do not rewrite the whole manuscript.

Empirical addendum to use as ground truth:
{addendum}

Manuscript draft to review:
{draft}
"""


def build_claude_segment_review_prompt(segment_name: str, segment: str, addendum: str) -> str:
    return f"""
You are a skeptical reviewer for AJAE, ERAE, Food Policy, or AEPP.

Review this manuscript segment only: {segment_name}.

Focus on whether the segment:
1. overclaims separability rejection or causality;
2. transparently handles control-set sensitivity and the village fixed-effects result where relevant;
3. treats NSI as detectability rather than economic magnitude where relevant;
4. handles price/unit-value limitations where relevant;
5. correctly describes weak IV/mechanism evidence where relevant;
6. has unclear contribution, missing caveats, or wording that should be softened.

Return an actionable reviewer memo with major issues, minor issues, and specific revision instructions.

Use this empirical addendum as ground truth:
{addendum}

Segment to review:
{segment}
"""


def build_final_integration_prompt(deepseek_draft: str, claude_comments: str, addendum: str) -> list[dict[str, str]]:
    system = (
        "You are a senior agricultural economics coauthor revising a manuscript after reviewer comments. "
        "Integrate the reviewer feedback into a complete final Markdown manuscript. "
        "Do not invent results or remove necessary caveats. Output Markdown only, no code fences."
    )
    user = f"""
Revise the manuscript below in response to the Claude reviewer memo.

Ground rules:
- Keep the paper conservative and reduced-form.
- Preserve the key numerical results from the empirical addendum.
- Make the introduction and conclusion candid about the village-FE participation result.
- Clearly mark mechanism and IV evidence as weak/exploratory.
- Do not hide data-definition limitations.
- Keep the draft coherent and ready for human coauthor editing.

Empirical addendum:
{addendum}

Claude reviewer memo:
{claude_comments}

Draft to revise:
{deepseek_draft}
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_segment_prompt(segment_name: str, current: str, editor: str, addendum: str, results: str) -> list[dict[str, str]]:
    system = (
        "You are a senior agricultural/development economics manuscript writer. "
        "Rewrite only the requested manuscript segment in polished academic English. "
        "Use only the supplied evidence, preserve caveats, and output Markdown only with no code fences."
    )
    if segment_name == "front":
        target = (
            "Write these sections only: Title, Abstract, Keywords, 1. Introduction, "
            "2. Conceptual Framework, 3. Data and Variable Construction, 4. Empirical Strategy."
        )
    elif segment_name == "back":
        target = (
            "Write these sections only: 5. Main Results, 6. Extensive and Intensive Margins, "
            "7. Category Heterogeneity, 8. Robustness and Sensitivity, 9. Mechanism Diagnostics, "
            "10. Price and Measurement Diagnostics, 11. Discussion, 12. Conclusion, References."
        )
    else:
        target = f"Write the requested segment only: {segment_name}."
    user = f"""
Task: {target}

Mandatory empirical stance:
- Pooled repeated cross-section, not panel or causal identification.
- M3 participation result is significant, but M0/M1 are not and village-FE participation is not significant.
- Quantity margins are secondary/sensitive.
- NSI is relative Wald-statistic detectability, not economic magnitude.
- Dairy is excluded from substantive category interpretation.
- Price is purchase-side unit value, not farm-gate price.
- Market-friction interactions and IV are weak/exploratory.

Use the current draft as structure and the addendum as ground truth. Keep prose concise but complete.

Current draft:
{current}

Editor action plan excerpt:
{editor}

Empirical addendum:
{addendum}

Earlier results package:
{results}
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_segment_revision_prompt(segment_name: str, segment_text: str, full_draft: str, claude_comments: str, addendum: str) -> list[dict[str, str]]:
    system = (
        "You are a senior agricultural economics coauthor revising one manuscript segment after reviewer comments. "
        "Revise only the supplied segment. Output Markdown only, no code fences."
    )
    user = f"""
Revise this manuscript segment in response to the Claude reviewer memo.

Segment: {segment_name}

Ground rules:
- Preserve all necessary caveats.
- Keep the result numbers consistent with the empirical addendum.
- Do not introduce new empirical claims or new citations beyond the supplied text.
- If the reviewer asks for a change that cannot be supported by the data, state the limitation instead.

Empirical addendum:
{addendum}

Claude reviewer memo:
{claude_comments}

Full draft context:
{full_draft[:24000]}

Segment to revise:
{segment_text}
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def add_docx_table(doc, headers: list[str], rows: list[list[str]]) -> None:
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt

    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    borders = OxmlElement("w:tblBorders")
    for edge in ["top", "left", "bottom", "right", "insideH", "insideV"]:
        el = OxmlElement("w:" + edge)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "DADCE0")
        borders.append(el)
    table._tbl.tblPr.append(borders)

    def put(cell, text: str, bold: bool = False) -> None:
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(str(text))
        run.font.name = "Arial"
        run.font.size = Pt(8.5)
        run.font.bold = bold

    for i, h in enumerate(headers):
        put(table.rows[0].cells[i], h, True)
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            put(cells[i], val)
    doc.add_paragraph()


def markdown_to_docx(markdown: str, out_path: Path) -> None:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor

    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = section.bottom_margin = section.left_margin = section.right_margin = Inches(1)
    section.header_distance = section.footer_distance = Inches(0.492)

    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(8)
    normal.paragraph_format.line_spacing = 1.15

    for style_name, size, before, after, color in [
        ("Heading 1", 20, 20, 6, "000000"),
        ("Heading 2", 16, 18, 6, "000000"),
        ("Heading 3", 14, 16, 4, "434343"),
    ]:
        st = doc.styles[style_name]
        st.font.name = "Arial"
        st._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
        st.font.size = Pt(size)
        st.font.bold = False
        st.font.color.rgb = RGBColor.from_string(color)
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.line_spacing = 1.15

    lines = markdown.splitlines()
    i = 0
    title_done = False
    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith("| "):
            block = []
            while i < len(lines) and lines[i].startswith("|"):
                block.append(lines[i])
                i += 1
            if len(block) >= 2:
                headers = [x.strip() for x in block[0].strip("|").split("|")]
                rows = [[x.strip() for x in b.strip("|").split("|")] for b in block[2:]]
                add_docx_table(doc, headers, rows)
            continue
        if line.startswith("# "):
            if not title_done:
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(3)
                r = p.add_run(line[2:].strip())
                r.font.name = "Arial"
                r.font.size = Pt(26)
                r.font.bold = False
                title_done = True
            else:
                doc.add_heading(line[2:].strip(), level=1)
        elif line.startswith("## "):
            doc.add_heading(line[3:].strip(), level=1)
        elif line.startswith("### "):
            doc.add_heading(line[4:].strip(), level=2)
        elif line.startswith("#### "):
            doc.add_heading(line[5:].strip(), level=3)
        elif not line.strip():
            pass
        elif line.startswith("- "):
            doc.add_paragraph(line[2:].strip(), style="List Bullet")
        elif re.match(r"^\d+\.\s+", line):
            doc.add_paragraph(re.sub(r"^\d+\.\s+", "", line).strip(), style="List Number")
        else:
            txt = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
            txt = re.sub(r"\*(.*?)\*", r"\1", txt)
            p = doc.add_paragraph(txt)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        i += 1

    doc.core_properties.title = "Household Composition and Self-Provisioning"
    doc.core_properties.author = "Codex + DeepSeek rewrite + Claude review workflow"
    doc.save(out_path)


def main() -> int:
    current = read_text(CURRENT_DRAFT)
    editor = read_text(EDITOR_PLAN, max_chars=42000)
    addendum = read_text(ADDENDUM)
    results = read_text(RESULTS_PACKAGE)

    deepseek_key = os.environ.get("DEEPSEEK_API_KEY") or getpass.getpass("DeepSeek API key: ")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY") or getpass.getpass("Anthropic API key: ")
    if not deepseek_key or not anthropic_key:
        raise SystemExit("Both API keys are required.")

    log_lines = [
        "# LLM Manuscript Revision Log",
        "",
        f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "- DeepSeek role: token-heavy manuscript rewrite and final integration.",
        "- Claude role: skeptical reviewer.",
        "- API keys were read interactively/environment and not written to disk.",
        "",
    ]

    print("Calling DeepSeek for segmented front-half rewrite...", flush=True)
    front = get_or_generate(
        DEEPSEEK_FRONT,
        "DeepSeek front rewrite",
        lambda: deepseek_chat(deepseek_key, build_segment_prompt("front", current, editor, addendum, results), max_tokens=4200),
    )
    print("Calling DeepSeek for segmented back-half rewrite...", flush=True)
    back = get_or_generate(
        DEEPSEEK_BACK,
        "DeepSeek back rewrite",
        lambda: deepseek_chat(deepseek_key, build_segment_prompt("back", current, editor, addendum, results), max_tokens=5200),
    )
    ds_draft = clean_markdown(front + "\n\n" + back)
    DEEPSEEK_DRAFT.write_text(ds_draft, encoding="utf-8")
    log_lines.append(f"- DeepSeek rewrite written: `{DEEPSEEK_DRAFT.relative_to(ROOT)}` ({len(ds_draft)} chars).")

    print("Calling Claude as reviewer for front half...", flush=True)
    review_front = get_or_generate(
        CLAUDE_FRONT,
        "Claude reviewer memo front",
        lambda: claude_review(anthropic_key, build_claude_segment_review_prompt("front half", front, addendum), max_tokens=2600),
    )
    print("Calling Claude as reviewer for back half...", flush=True)
    if CLAUDE_BACK.exists() and CLAUDE_BACK.stat().st_size > 100:
        review_back = CLAUDE_BACK.read_text(encoding="utf-8")
        print(f"Using cached Claude reviewer memo back: {CLAUDE_BACK}", flush=True)
    else:
        split_marker = "\n## 9. Mechanism Diagnostics"
        if split_marker in back:
            back_results, back_discussion_tail = back.split(split_marker, 1)
            back_discussion = "## 9. Mechanism Diagnostics" + back_discussion_tail
        else:
            midpoint = len(back) // 2
            back_results, back_discussion = back[:midpoint], back[midpoint:]
        review_back_results = get_or_generate(
            CLAUDE_BACK_RESULTS,
            "Claude reviewer memo back-results",
            lambda: claude_review(
                anthropic_key,
                build_claude_segment_review_prompt("results and robustness sections", back_results, addendum),
                max_tokens=2300,
            ),
        )
        review_back_discussion = get_or_generate(
            CLAUDE_BACK_DISCUSSION,
            "Claude reviewer memo mechanism-discussion sections",
            lambda: claude_review(
                anthropic_key,
                build_claude_segment_review_prompt("mechanism, discussion, conclusion sections", back_discussion, addendum),
                max_tokens=2300,
            ),
        )
        review_back = clean_markdown(
            "## Back Results/Robustness Review\n\n"
            + review_back_results
            + "\n\n## Back Mechanism/Discussion Review\n\n"
            + review_back_discussion
        )
        CLAUDE_BACK.write_text(review_back, encoding="utf-8")
    review = clean_markdown(
        "# Claude Reviewer Comments\n\n"
        "## Front-Half Review\n\n"
        + review_front
        + "\n\n## Back-Half Review\n\n"
        + review_back
    )
    CLAUDE_REVIEW.write_text(review, encoding="utf-8")
    log_lines.append(f"- Claude reviewer memo written: `{CLAUDE_REVIEW.relative_to(ROOT)}` ({len(review)} chars).")

    print("Calling DeepSeek for final front-half integration...", flush=True)
    front_final = get_or_generate(
        FINAL_FRONT,
        "DeepSeek final front integration",
        lambda: deepseek_chat(deepseek_key, build_segment_revision_prompt("front", front, ds_draft, review, addendum), max_tokens=4400),
    )
    print("Calling DeepSeek for final back-half integration...", flush=True)
    back_final = get_or_generate(
        FINAL_BACK,
        "DeepSeek final back integration",
        lambda: deepseek_chat(deepseek_key, build_segment_revision_prompt("back", back, ds_draft, review, addendum), max_tokens=5400),
    )
    final = clean_markdown(front_final + "\n\n" + back_final)
    FINAL_MD.write_text(final, encoding="utf-8")
    markdown_to_docx(final, FINAL_DOCX)
    log_lines.append(f"- Final LLM-revised manuscript written: `{FINAL_MD.relative_to(ROOT)}` ({len(final)} chars).")
    log_lines.append(f"- Final DOCX written: `{FINAL_DOCX.relative_to(ROOT)}`.")

    CALL_LOG.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print(f"Wrote {FINAL_MD}")
    print(f"Wrote {FINAL_DOCX}")
    print(f"Wrote {CLAUDE_REVIEW}")
    print(f"Wrote {CALL_LOG}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
````

## `code/17_finalize_manuscript_after_llm_review.py`

- Size: 20.8 KB
- Lines: 116

````python
#!/usr/bin/env python3
"""Finalize full manuscript after DeepSeek rewrite and Claude review.

This script uses the complete Codex draft as the structural base because it
contains the full paper and tables, then integrates the main Claude reviewer
comments and the more conservative DeepSeek wording.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "manuscript"
BASE = OUT / "paper1_manuscript_draft_revised.md"
FINAL_MD = OUT / "paper1_manuscript_final_after_llm_review.md"
FINAL_DOCX = OUT / "paper1_manuscript_final_after_llm_review.docx"
LOG = ROOT / "outputs" / "logs" / "paper1_manuscript_final_after_llm_review_log.md"


def load_markdown_to_docx():
    script = ROOT / "code" / "16_llm_manuscript_revision.py"
    spec = importlib.util.spec_from_file_location("llm_manuscript_revision", script)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.markdown_to_docx


def replace_once(text: str, old: str, new: str) -> str:
    if old not in text:
        raise ValueError(f"Target text not found: {old[:120]}")
    return text.replace(old, new, 1)


def main() -> int:
    text = BASE.read_text(encoding="utf-8")

    old_abs = """Agricultural household models predict that, under complete markets and price-taking behavior, production decisions should be separable from household preferences and demographic composition. Most empirical tests of this prediction focus on labor demand or production input choices. This paper studies a different but substantively important margin: whether rural households enter self-provisioning for specific food categories. Using a pooled repeated cross-section of 3,565 rural Chinese households observed in 2023 or 2024, converted to 28,520 household-category observations across eight food categories, I test whether household size, child share, elderly share, and female share jointly predict category-specific self-provisioning. The preferred common-sample specification indicates that household composition predicts self-provisioning participation after controlling for household resources, local market access, agro-ecological suitability, purchase-side unit values, county text indicators, food-category fixed effects, province fixed effects, and survey-year fixed effects (Wald = 16.733, p = 0.002). The evidence is concentrated on the participation margin: full-sample transformed quantity outcomes are not significant in the preferred specification. However, the result is control-set sensitive. It is not significant in parsimonious specifications and does not survive a village fixed-effects participation-margin check, although log and IHS quantity margins become significant within villages. Category-level tests show strongest detectability for eggs, oils, vegetables, and fruits after false-discovery-rate adjustment, but these rankings should be interpreted as test-statistic detectability rather than economic magnitudes. The results provide cautious reduced-form evidence that household composition remains conditionally associated with rural food self-provisioning, while also underscoring the limits of cross-sectional separability tests without stronger panel or instrumental-variable identification."""
    new_abs = """Agricultural household models predict that, under complete markets and price-taking behavior, production decisions should be separable from household preferences and demographic composition. Most empirical tests of this prediction focus on labor demand or production input choices. This paper studies a different but substantively important margin: whether rural households enter self-provisioning for specific food categories. Using a pooled repeated cross-section of 3,565 rural Chinese households observed in 2023 or 2024, converted to 28,520 household-category observations across eight food categories, I test whether household size, child share, elderly share, and female share jointly predict category-specific self-provisioning. The preferred common-sample specification indicates a conditional association between household composition and self-provisioning participation after controlling for household resources, local market access, agro-ecological suitability, purchase-side unit values, county text indicators, food-category fixed effects, province fixed effects, and survey-year fixed effects (Wald = 16.733, p = 0.002). This association is control-set sensitive: it is not significant in parsimonious specifications and does not survive a village fixed-effects participation-margin check (p = 0.171), while log and IHS quantity margins become significant under village fixed effects. Thus neither participation nor quantity is robustly dominant across all specifications. Category-level tests show strongest Wald-statistic detectability for eggs, oils, vegetables, and fruits after false-discovery-rate adjustment, but these rankings are not economic effect sizes; oils also require item-code verification, and dairy is excluded because participation is nearly degenerate. Purchase-side unit values are imperfect price proxies, with roughly one-quarter hedonically imputed at moderate precision. The paper provides cautious reduced-form evidence that household composition remains conditionally associated with rural food self-provisioning under the maintained M3 controls, while underscoring the limits of cross-sectional separability tests without stronger panel or instrumental-variable identification."""
    text = replace_once(text, old_abs, new_abs)

    old_intro = """The central finding is deliberately stated cautiously. Household composition significantly predicts self-provisioning participation in the preferred M3 common-sample specification, but not in simpler M0 or M1 specifications. The participation result appears after adding market-access, agro-ecological, and province controls, and remains significant when estimated with logit and probit. Yet it does not survive a village fixed-effects participation check. This pattern suggests that the data support a conditional association between household composition and self-provisioning, especially on the extensive margin, but do not justify a strong causal or structural claim that household demographics independently determine self-provisioning."""
    new_intro = """The central finding is deliberately stated cautiously. Household composition significantly predicts self-provisioning participation in the preferred M3 common-sample specification, but not in simpler M0 or M1 specifications. The participation result appears after adding market-access, agro-ecological, and province controls, and remains significant when estimated with logit and probit. Yet it does not survive a village fixed-effects participation check: with village fixed effects, the participation-margin Wald test has p = 0.171, while log and IHS quantity margins become significant. This inversion suggests that the detectable association shifts with the level of geographic controls. The data therefore support a conditional association under the maintained M3 controls, not a robust within-village structural rejection of separability."""
    text = replace_once(text, old_intro, new_intro)

    old_contrib = """The paper makes three contributions. First, it extends separability testing from farm input demand to the food self-provisioning margin. Second, it shows that the association between household composition and self-provisioning is highly category-specific: eggs, oils, vegetables, and fruits remain significant after Benjamini-Hochberg false-discovery-rate correction, while dairy has too little variation to interpret substantively. Third, it provides a transparent account of weak evidence. Market-friction interactions do not provide strong mechanism evidence, candidate instrumental variables have weak first stages, purchase-side unit values are imperfect price proxies, and village fixed effects weaken the participation result."""
    new_contrib = """The paper makes three contributions. First, it extends separability testing from farm input demand to the food self-provisioning margin while being explicit that the exercise is reduced-form and cross-sectional. Second, it shows that the conditional association is category-specific: eggs, oils, vegetables, and fruits remain significant after Benjamini-Hochberg false-discovery-rate correction, although oils require item-code verification and dairy has too little variation to interpret substantively. Third, it provides a transparent account of weak evidence. Market-friction interactions do not provide strong mechanism evidence, candidate instrumental variables have weak first stages, purchase-side unit values are imperfect price proxies, and village fixed effects materially weaken the participation result."""
    text = replace_once(text, old_contrib, new_contrib)

    old_price_framework = """Let \(D_h\) be household composition and \(X_h\), \(M_v\), \(A_v\), and \(P_{hct}\) denote household resources, local market environment, agro-ecological conditions, and prices or price proxies. Under separability, conditional on the appropriate production-side controls, \(D_h\) should not predict \(y_{hct}\). The empirical test is whether the coefficients on household composition are jointly zero."""
    new_price_framework = """Let \(D_h\) be household composition and \(X_h\), \(M_v\), \(A_v\), and \(P_{hct}\) denote household resources, local market environment, agro-ecological conditions, and prices or price proxies. In the data, \(P_{hct}\) is proxied by purchase-side unit values rather than farm-gate prices; about 27 percent are hedonically imputed, with county-model \(R^2\) near 0.43 and log RMSE near 0.72. These variables help condition on food-cost differences but cannot fully satisfy the price-conditioning requirement of a structural separability test. Under separability, conditional on the appropriate production-side controls, \(D_h\) should not predict \(y_{hct}\). The empirical test is whether the coefficients on household composition are jointly zero."""
    text = replace_once(text, old_price_framework, new_price_framework)

    old_results = """Table 2 reports the M0-M3 sequence on the common M3 sample. The preferred M3 participation model rejects the joint exclusion of household composition (Wald = 16.733, p = 0.002). The same is not true in the parsimonious specifications: M0 has p = 0.178 and M1 has p = 0.106. The participation result becomes significant only after adding market, agro-ecological, and province controls."""
    new_results = """Table 2 reports the M0-M3 sequence on the common M3 sample. The preferred M3 participation model is inconsistent with the joint exclusion of household composition under the maintained M3 controls (Wald = 16.733, p = 0.002). The same is not true in the parsimonious specifications: M0 has p = 0.178 and M1 has p = 0.106. The participation result becomes significant only after adding market, agro-ecological, and province controls."""
    text = replace_once(text, old_results, new_results)

    old_quantity = """This contrast supports an extensive-margin interpretation in the preferred pooled specification, but it also reveals that the empirical pattern is sensitive to the control set."""
    new_quantity = """This contrast supports an extensive-margin interpretation in the preferred pooled specification, but village fixed effects reverse the detectable pattern. The empirical evidence therefore does not establish that either the participation or quantity margin is robustly dominant."""
    text = replace_once(text, old_quantity, new_quantity)

    old_reveal = """This pattern means the M3 result should not be presented as invariant across reasonable specifications. Rather, it is a conditional association that emerges after accounting for regional, market-access, and agro-ecological heterogeneity."""
    new_reveal = """This pattern means the M3 result should not be presented as invariant across reasonable specifications. Rather, it is a conditional association that appears after adding regional, market-access, and agro-ecological controls; those controls change the identifying variation rather than revealing a structural demographic effect."""
    text = replace_once(text, old_reveal, new_reveal)

    old_sec6 = """For this reason, the paper treats participation as the primary margin and conditional intensity as supplementary. The full-sample log and IHS models do not reject in M3, and transformed outcomes with many zeros are sensitive to scale and transformation choices."""
    new_sec6 = """For this reason, the two-part conditional-intensity result is descriptive rather than structural. The village fixed-effects quantity results should be treated with the same caution: they show that transformed quantities can become detectable within villages, but they do not solve selection into positive self-provisioning and remain sensitive to scale and transformation choices. The paper therefore treats the location of the detectable association as specification-dependent, rather than claiming that participation is uniformly the primary margin."""
    text = replace_once(text, old_sec6, new_sec6)

    old_nsi = """The Non-Separability Index (NSI) is defined as a category's household-composition Wald statistic divided by the mean Wald statistic across categories. This index is a relative detectability ranking, not an economic effect size."""
    new_nsi = """The Non-Separability Index (NSI), used here only as a Wald Detectability Ratio, is defined as a category's household-composition Wald statistic divided by the mean Wald statistic across categories. This index is a relative detectability ranking, not an economic effect size."""
    text = replace_once(text, old_nsi, new_nsi)

    old_cat = """After Benjamini-Hochberg FDR correction, eggs, oils, vegetables, and fruits remain significant at 5 percent. Beans is significant before correction but not after FDR correction. Oils require definition caution because the item-code audit is incomplete. Vegetables have the highest self-sufficiency rate but also high participation, so binary variation is compressed near the ceiling. Dairy is excluded from main category interpretation because almost no households self-provision dairy."""
    new_cat = """After Benjamini-Hochberg FDR correction, eggs, vegetables, and fruits remain significant at 5 percent, and oils also remains significant but is flagged before interpretation because the item-code audit is incomplete. Beans is significant before correction but not after FDR correction. Vegetables have the highest self-sufficiency rate but also high participation, so binary variation is compressed near the ceiling. Dairy is excluded from main category interpretation because almost no households self-provision dairy."""
    text = replace_once(text, old_cat, new_cat)

    insert_before_mech = """## 9. Mechanism Diagnostics"""
    price_para = """### 8.1 Price and Unit-Value Sensitivity\n\nThe price controls should be read as imperfect purchase-side unit-value controls rather than exogenous market prices. In the analysis-ready file, 73.1 percent of unit values are observed from household purchase data and 26.9 percent are hedonically imputed. The county hedonic model has \(R^2 \\approx 0.43\) and log RMSE \(\\approx 0.72\), implying substantial prediction noise. The observed-only price robustness check remains statistically similar for participation (p = 0.002), but it is estimated on a selected purchasing subsample. These facts limit how strongly price conditioning can be interpreted in a market-separability framework.\n\n"""
    text = text.replace(insert_before_mech, price_para + insert_before_mech, 1)

    old_mech = """The preferred interpretation is that household composition is conditionally associated with self-provisioning participation. A stronger mechanism claim would require evidence that this association is amplified where markets are less complete or more costly to access. The available market-friction interactions do not provide that evidence. Interaction Wald tests using survey market friction, POI market friction, and combined market-friction measures are statistically weak across participation and quantity outcomes."""
    new_mech = """The conditional association documented above is detectable under the preferred M3 controls but is sensitive to control-set choice and is not robust to village fixed effects on the participation margin. The following diagnostics therefore explore possible correlates of the pattern without claiming to identify a causal mechanism. A stronger market-incompleteness claim would require evidence that the association is amplified where markets are less complete or more costly to access. The available market-friction interactions do not provide that evidence. Interaction Wald tests using survey market friction, POI market friction, and combined market-friction measures are statistically weak across participation and quantity outcomes. The village fixed-effects result is also important for mechanism interpretation: once village-level market access, agro-ecological conditions, local production norms, province variation, and county text variation are absorbed, household composition no longer predicts participation."""
    text = replace_once(text, old_mech, new_mech)

    old_discussion = """The empirical evidence is best read as a disciplined but cautious separability test. The preferred pooled specification rejects the joint exclusion of household composition on the self-provisioning participation margin. The result is not driven by LPM functional form and remains when income and expenditure controls are removed. The category pattern also suggests that self-provisioning is not a uniform rural practice: it is more detectable for eggs, oils, vegetables, and fruits than for staples, meat/aquatic products, or dairy."""
    new_discussion = """The empirical evidence is best read as a disciplined but cautious reduced-form separability exercise. The preferred pooled specification is inconsistent with the joint exclusion of household composition on the self-provisioning participation margin, but that result is not present in parsimonious models and does not survive village fixed effects. The result is not driven by LPM functional form and remains when income and expenditure controls are removed. The category pattern also suggests that self-provisioning is not a uniform rural practice: the Wald test is more detectable for eggs, oils, vegetables, and fruits than for staples, meat/aquatic products, or dairy, although oils and dairy require the caveats discussed above."""
    text = replace_once(text, old_discussion, new_discussion)

    old_conclusion = """The main conclusion is therefore conservative: household composition conditionally predicts entry into self-provisioning, providing reduced-form evidence that the separable agricultural household benchmark is incomplete for this margin. The evidence does not establish a causal demographic effect or a clean market-friction mechanism. Future work should use panel data, validated item-level category definitions, better farm-gate and purchase price measures, and stronger instruments or natural experiments to distinguish market incompleteness from home-good quality preferences and unobserved household heterogeneity."""
    new_conclusion = """The main conclusion is therefore conservative: household composition conditionally predicts entry into self-provisioning under the maintained M3 controls, but this association is not robust to village fixed effects and should not be read as a causal demographic effect or a clean market-friction mechanism. The results are most useful as transparent reduced-form evidence that the separable agricultural household benchmark may be incomplete for food self-provisioning, while also showing where the current data are insufficient. Future work should use panel data, validated item-level category definitions, better farm-gate and purchase price measures, and stronger instruments or natural experiments to distinguish market incompleteness from home-good quality preferences and unobserved household heterogeneity."""
    text = replace_once(text, old_conclusion, new_conclusion)

    FINAL_MD.write_text(text, encoding="utf-8")
    markdown_to_docx = load_markdown_to_docx()
    markdown_to_docx(text, FINAL_DOCX)

    LOG.write_text(
        "# Manuscript Finalization After LLM Review\n\n"
        "- Base: `outputs/manuscript/paper1_manuscript_draft_revised.md`.\n"
        "- DeepSeek outputs used for conservative wording: `paper1_manuscript_deepseek_front.md`, `paper1_manuscript_deepseek_back.md`.\n"
        "- Claude reviewer comments used: `paper1_claude_reviewer_comments.md` and segment memos.\n"
        "- Final full manuscript: `outputs/manuscript/paper1_manuscript_final_after_llm_review.md`.\n"
        "- Final DOCX: `outputs/manuscript/paper1_manuscript_final_after_llm_review.docx`.\n",
        encoding="utf-8",
    )
    print(FINAL_MD)
    print(FINAL_DOCX)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
````

## `code/18_unit_kg_month_check_and_descriptives.R`

- Size: 17.5 KB
- Lines: 447

````r
options(warn = 1)

root <- getwd()
dir.create(file.path(root, "data", "analysis_ready"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "tables"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "logs"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "reports"), recursive = TRUE, showWarnings = FALSE)

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

fmt <- function(x, digits = 3) {
  ifelse(is.na(x), "", formatC(x, format = "f", digits = digits, big.mark = ","))
}

md_table <- function(df, digits = 3) {
  if (nrow(df) == 0) return("")
  out <- df
  for (nm in names(out)) {
    if (is.numeric(out[[nm]])) out[[nm]] <- fmt(out[[nm]], digits)
  }
  cols <- names(out)
  lines <- c(
    paste0("| ", paste(cols, collapse = " | "), " |"),
    paste0("|", paste(rep("---", length(cols)), collapse = "|"), "|")
  )
  for (i in seq_len(nrow(out))) {
    vals <- vapply(out[i, , drop = FALSE], function(x) as.character(x[1]), character(1))
    vals <- gsub("\\|", "\\\\|", vals)
    lines <- c(lines, paste0("| ", paste(vals, collapse = " | "), " |"))
  }
  paste(lines, collapse = "\n")
}

summarise_numeric <- function(data, vars, labels, units, module = "") {
  rows <- lapply(vars[vars %in% names(data)], function(v) {
    x <- to_num(data[[v]])
    ok <- !is.na(x) & is.finite(x)
    qs <- if (any(ok)) {
      as.numeric(quantile(x[ok], probs = c(.01, .05, .25, .5, .75, .95, .99), names = FALSE))
    } else {
      rep(NA_real_, 7)
    }
    data.frame(
      module = module,
      variable = v,
      label = labels[[v]],
      unit = units[[v]],
      n = sum(ok),
      missing = sum(!ok),
      missing_share = mean(!ok),
      zero = sum(x == 0, na.rm = TRUE),
      mean = if (any(ok)) mean(x[ok]) else NA_real_,
      sd = if (sum(ok) > 1) sd(x[ok]) else NA_real_,
      min = if (any(ok)) min(x[ok]) else NA_real_,
      p01 = qs[1],
      p05 = qs[2],
      p25 = qs[3],
      median = qs[4],
      p75 = qs[5],
      p95 = qs[6],
      p99 = qs[7],
      max = if (any(ok)) max(x[ok]) else NA_real_,
      max_to_p99 = if (any(ok) && !is.na(qs[7]) && qs[7] != 0) max(x[ok]) / qs[7] else NA_real_,
      stringsAsFactors = FALSE
    )
  })
  out <- do.call(rbind, rows)
  rownames(out) <- NULL
  out
}

category_summary <- function(data) {
  cats <- unique(data[, c("food_category", "food_category_label")])
  cats <- cats[order(match(cats$food_category, c("zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo"))), ]
  rows <- lapply(seq_len(nrow(cats)), function(i) {
    d <- data[data$food_category == cats$food_category[i], ]
    q <- function(v, p) as.numeric(quantile(to_num(d[[v]]), p, na.rm = TRUE, names = FALSE))
    mn <- function(v) mean(to_num(d[[v]]), na.rm = TRUE)
    mx <- function(v) max(to_num(d[[v]]), na.rm = TRUE)
    data.frame(
      food_category = cats$food_category[i],
      food_category_label = cats$food_category_label[i],
      n = nrow(d),
      participation_rate = mn("production_participation"),
      mean_cons_kg_month = mn("cons_kg_month"),
      p99_cons_kg_month = q("cons_kg_month", .99),
      max_cons_kg_month = mx("cons_kg_month"),
      mean_selfprod_kg_month = mn("selfprod_kg_month"),
      p99_selfprod_kg_month = q("selfprod_kg_month", .99),
      max_selfprod_kg_month = mx("selfprod_kg_month"),
      mean_purchase_qty_kg_month = mn("purchase_qty_kg_month"),
      p99_purchase_qty_kg_month = q("purchase_qty_kg_month", .99),
      max_purchase_qty_kg_month = mx("purchase_qty_kg_month"),
      mean_price_hedonic_w99_yuan_per_kg = mn("price_hedonic_imputed_w99_yuan_per_kg"),
      p99_price_hedonic_w99_yuan_per_kg = q("price_hedonic_imputed_w99_yuan_per_kg", .99),
      max_price_hedonic_w99_yuan_per_kg = mx("price_hedonic_imputed_w99_yuan_per_kg"),
      stringsAsFactors = FALSE
    )
  })
  out <- do.call(rbind, rows)
  rownames(out) <- NULL
  out
}

top_extremes <- function(data, vars, n_top = 10) {
  rows <- list()
  for (v in vars[vars %in% names(data)]) {
    x <- to_num(data[[v]])
    idx <- which(!is.na(x) & is.finite(x))
    if (length(idx) == 0) next
    idx <- idx[order(x[idx], decreasing = TRUE)]
    idx <- idx[seq_len(min(length(idx), n_top))]
    rows[[length(rows) + 1]] <- data.frame(
      variable = v,
      rank = seq_along(idx),
      value = x[idx],
      nhCode = data$nhCode[idx],
      data_year = data$data_year[idx],
      provn = data$provn[idx],
      countyn = data$countyn[idx],
      townn_std = data$townn_std[idx],
      viln_std = data$viln_std[idx],
      food_category = data$food_category[idx],
      food_category_label = data$food_category_label[idx],
      stringsAsFactors = FALSE
    )
  }
  out <- do.call(rbind, rows)
  rownames(out) <- NULL
  out
}

input_file <- path("data", "analysis_ready", "paper1_reprocessed_analysis_ready_long.csv")
data <- read_csv(
  input_file,
  colClasses = c(
    nhCode = "character",
    xzc12 = "character",
    xzc12_for_merge_final = "character",
    xzc12_for_merge = "character"
  )
)

required_categories <- c("zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo")
unexpected_categories <- setdiff(unique(data$food_category), required_categories)

conversion_rows <- list()

add_quantity_kg <- function(data, from, to, label) {
  if (!from %in% names(data)) return(data)
  data[[to]] <- to_num(data[[from]]) * 0.5
  conversion_rows[[length(conversion_rows) + 1]] <<- data.frame(
    variable_original = from,
    variable_converted = to,
    original_unit = "jin/month",
    converted_unit = "kg/month",
    operation = "converted = original * 0.5",
    n = sum(!is.na(to_num(data[[from]]))),
    max_abs_check_error = max(abs(data[[to]] - to_num(data[[from]]) * 0.5), na.rm = TRUE),
    note = label,
    stringsAsFactors = FALSE
  )
  data
}

add_price_kg <- function(data, from, to = NULL, label = "") {
  if (!from %in% names(data)) return(data)
  if (is.null(to)) to <- sub("yuan_per_jin", "yuan_per_kg", from, fixed = TRUE)
  if (identical(to, from)) to <- paste0(from, "_yuan_per_kg")
  data[[to]] <- to_num(data[[from]]) * 2
  conversion_rows[[length(conversion_rows) + 1]] <<- data.frame(
    variable_original = from,
    variable_converted = to,
    original_unit = "yuan/jin",
    converted_unit = "yuan/kg",
    operation = "converted = original * 2",
    n = sum(!is.na(to_num(data[[from]]))),
    max_abs_check_error = max(abs(data[[to]] - to_num(data[[from]]) * 2), na.rm = TRUE),
    note = label,
    stringsAsFactors = FALSE
  )
  data
}

data <- add_quantity_kg(data, "cons_monthly_jin", "cons_kg_month", "monthly consumption quantity")
data <- add_quantity_kg(data, "selfprod_monthly_total", "selfprod_kg_month", "monthly self-produced/self-consumed quantity")
data <- add_quantity_kg(data, "purchase_qty_sum_jin", "purchase_qty_kg_month", "monthly purchased quantity")

data$log_selfprod_amount_original_jin_scale <- data$log_selfprod_amount
data$ihs_selfprod_amount_original_jin_scale <- data$ihs_selfprod_amount
data$log_selfprod_amount_kg_month <- log1p(pmax(to_num(data$selfprod_kg_month), 0))
data$ihs_selfprod_amount_kg_month <- asinh(pmax(to_num(data$selfprod_kg_month), 0))

price_vars_suffix <- grep("yuan_per_jin$", names(data), value = TRUE)
for (v in price_vars_suffix) {
  data <- add_price_kg(data, v)
}

price_vars_extra <- c(
  "price_recalc_spend_sum_over_purchase_qty_sum",
  "village_price_category_median",
  "price_mean_detail_total_spend_over_qty",
  "price_mean_detail_avg_each_purchase",
  "price_mean_raw_pjxfl"
)
for (v in price_vars_extra) {
  data <- add_price_kg(data, v, paste0(v, "_yuan_per_kg"))
}

kg_file <- path("data", "analysis_ready", "paper1_reprocessed_analysis_ready_long_kg_month.csv")
write_csv(data, kg_file)

conversion_audit <- do.call(rbind, conversion_rows)
conversion_audit$max_abs_check_error[is.infinite(conversion_audit$max_abs_check_error)] <- NA_real_
write_csv(conversion_audit, path("outputs", "tables", "paper1_unit_conversion_audit_kg_month.csv"))

labels <- c(
  production_participation = "Self-provisioning participation",
  cons_kg_month = "Monthly consumption",
  selfprod_kg_month = "Monthly self-produced consumption",
  purchase_qty_kg_month = "Monthly purchased quantity",
  self_suff_rate = "Self-sufficiency rate",
  log_selfprod_amount_kg_month = "log(1 + selfprod kg/month)",
  ihs_selfprod_amount_kg_month = "asinh(selfprod kg/month)",
  price_hedonic_imputed_w99_yuan_per_kg = "Main hedonic/winsorized unit value",
  price_preferred_household_recalc_w99_yuan_per_kg = "Observed household recalculated unit value, w99",
  village_price_category_median_yuan_per_kg = "Village category median unit value",
  spend_sum_yuan = "Monthly purchase spending",
  household_size_reconstructed = "Household size",
  num_children = "Number of children",
  num_elderly = "Number of elderly members",
  adult_members = "Adult members",
  child_share = "Child share",
  elderly_share = "Elderly share",
  female_share = "Female share",
  dependency_ratio = "Dependency ratio",
  agricultural_labor_days = "Agricultural labor days, household sum",
  offfarm_labor_days = "Off-farm labor days, household sum",
  total_labor_days = "Total labor days, household sum",
  agricultural_labor_days_per_adult = "Agricultural labor days per adult",
  offfarm_labor_days_per_adult = "Off-farm labor days per adult",
  total_labor_days_per_adult = "Total labor days per adult",
  agricultural_labor_days_working_age_16_64 = "Agricultural labor days, age 16-64 sum",
  offfarm_labor_days_working_age_16_64 = "Off-farm labor days, age 16-64 sum",
  total_labor_days_working_age_16_64 = "Total labor days, age 16-64 sum",
  agricultural_labor_days_head = "Agricultural labor days, household head",
  offfarm_labor_days_head = "Off-farm labor days, household head",
  total_labor_days_head = "Total labor days, household head",
  total_sown_area = "Total sown area, cleaned",
  total_sown_area_raw = "Total sown area, raw",
  total_sown_area_nonnegative = "Total sown area, nonnegative",
  total_sown_area_component_cap500 = "Total sown area after component cap",
  area_any_component_outlier = "Any crop-area component outlier",
  area_total_winsorized_flag = "Total area winsorized flag",
  log1p_total_income_w_w99 = "Log total income, winsorized",
  log1p_agri_business_income_w99 = "Log agricultural business income, winsorized",
  log1p_annual_expense_total_w99 = "Log annual expense, winsorized",
  market_friction_survey = "Survey market friction",
  poi_market_friction_lag1 = "POI market friction",
  combined_market_friction = "Combined market friction",
  poi_market_capacity_5km = "POI market capacity within 5km",
  poi_fresh_market_capacity_5km = "Fresh-market POI capacity within 5km",
  gaez_overall_si_10km = "GAEZ overall suitability",
  gaez_staple_si_10km = "GAEZ staple suitability",
  gaez_soil_terrain_constraint_10km = "GAEZ soil/terrain constraint",
  risk_salience_z_5yr_sum = "County food-safety risk salience",
  governance_capacity_z_5yr_sum = "County governance capacity signal",
  trust_signal_z_5yr_sum = "County trust signal",
  attention_z_5yr_sum = "County attention signal"
)
units <- c(
  production_participation = "0/1",
  cons_kg_month = "kg/month",
  selfprod_kg_month = "kg/month",
  purchase_qty_kg_month = "kg/month",
  self_suff_rate = "0-1",
  log_selfprod_amount_kg_month = "log kg/month",
  ihs_selfprod_amount_kg_month = "IHS kg/month",
  price_hedonic_imputed_w99_yuan_per_kg = "yuan/kg",
  price_preferred_household_recalc_w99_yuan_per_kg = "yuan/kg",
  village_price_category_median_yuan_per_kg = "yuan/kg",
  spend_sum_yuan = "yuan/month",
  household_size_reconstructed = "persons",
  num_children = "persons",
  num_elderly = "persons",
  adult_members = "persons",
  child_share = "share",
  elderly_share = "share",
  female_share = "share",
  dependency_ratio = "ratio",
  agricultural_labor_days = "days/year, household sum",
  offfarm_labor_days = "days/year, household sum",
  total_labor_days = "days/year, household sum",
  agricultural_labor_days_per_adult = "days/year/adult",
  offfarm_labor_days_per_adult = "days/year/adult",
  total_labor_days_per_adult = "days/year/adult",
  agricultural_labor_days_working_age_16_64 = "days/year, age 16-64 sum",
  offfarm_labor_days_working_age_16_64 = "days/year, age 16-64 sum",
  total_labor_days_working_age_16_64 = "days/year, age 16-64 sum",
  agricultural_labor_days_head = "days/year, household head",
  offfarm_labor_days_head = "days/year, household head",
  total_labor_days_head = "days/year, household head",
  total_sown_area = "mu",
  total_sown_area_raw = "mu",
  total_sown_area_nonnegative = "mu",
  total_sown_area_component_cap500 = "mu",
  area_any_component_outlier = "0/1",
  area_total_winsorized_flag = "0/1",
  log1p_total_income_w_w99 = "log yuan/year",
  log1p_agri_business_income_w99 = "log yuan/year",
  log1p_annual_expense_total_w99 = "log yuan/year",
  market_friction_survey = "z-score",
  poi_market_friction_lag1 = "z-score",
  combined_market_friction = "z-score",
  poi_market_capacity_5km = "count",
  poi_fresh_market_capacity_5km = "count",
  gaez_overall_si_10km = "index",
  gaez_staple_si_10km = "index",
  gaez_soil_terrain_constraint_10km = "index",
  risk_salience_z_5yr_sum = "z-score",
  governance_capacity_z_5yr_sum = "z-score",
  trust_signal_z_5yr_sum = "z-score",
  attention_z_5yr_sum = "z-score"
)

desc_vars <- names(labels)
desc <- summarise_numeric(data, desc_vars, labels, units, "kg_month_unit_checked")
desc$outlier_attention <- ifelse(
  !is.na(desc$max_to_p99) & desc$max_to_p99 >= 5,
  "max >= 5*p99; inspect top cases",
  ""
)
write_csv(desc, path("outputs", "tables", "paper1_key_variable_descriptives_kg_month.csv"))

cat_desc <- category_summary(data)
write_csv(cat_desc, path("outputs", "tables", "paper1_category_outcome_descriptives_kg_month.csv"))

extreme_vars <- c(
  "cons_kg_month",
  "selfprod_kg_month",
  "purchase_qty_kg_month",
  "price_hedonic_imputed_w99_yuan_per_kg",
  "price_preferred_household_recalc_w99_yuan_per_kg",
  "village_price_category_median_yuan_per_kg",
  "spend_sum_yuan",
  "total_sown_area",
  "total_labor_days",
  "total_labor_days_per_adult"
)
extremes <- top_extremes(data, extreme_vars, 10)
write_csv(extremes, path("outputs", "tables", "paper1_top_extreme_values_kg_month.csv"))

unit_checks <- data.frame(
  check = c(
    "unexpected food categories outside eight-category analysis set",
    "quantity kg/month conversion records",
    "price yuan/kg conversion records",
    "rows with missing main hedonic price yuan/kg",
    "rows with old jin-based log retained for audit",
    "rows with kg-based log/IHS recomputed"
  ),
  value = c(
    if (length(unexpected_categories) == 0) "none" else paste(unexpected_categories, collapse = "; "),
    sum(conversion_audit$converted_unit == "kg/month"),
    sum(conversion_audit$converted_unit == "yuan/kg"),
    sum(is.na(data$price_hedonic_imputed_w99_yuan_per_kg)),
    sum(!is.na(data$log_selfprod_amount_original_jin_scale)),
    sum(!is.na(data$log_selfprod_amount_kg_month) & !is.na(data$ihs_selfprod_amount_kg_month))
  ),
  stringsAsFactors = FALSE
)
write_csv(unit_checks, path("outputs", "tables", "paper1_unit_checks_kg_month.csv"))

report_lines <- c(
  "# Paper 1 Unit Conversion and Descriptive Check",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Files",
  "",
  paste0("- Unit-checked data: `", kg_file, "`"),
  "- Conversion audit: `outputs/tables/paper1_unit_conversion_audit_kg_month.csv`",
  "- Key variable descriptives: `outputs/tables/paper1_key_variable_descriptives_kg_month.csv`",
  "- Category outcome descriptives: `outputs/tables/paper1_category_outcome_descriptives_kg_month.csv`",
  "- Top extreme values: `outputs/tables/paper1_top_extreme_values_kg_month.csv`",
  "",
  "## Unit Rule",
  "",
  "- Quantities originally labelled jin/month are converted to kg/month using kg = jin * 0.5.",
  "- Unit values originally labelled yuan/jin are converted to yuan/kg using yuan/kg = yuan/jin * 2.",
  "- `log_selfprod_amount_kg_month` and `ihs_selfprod_amount_kg_month` are recomputed from `selfprod_kg_month`.",
  "- Original jin-scale log/IHS columns are retained as `*_original_jin_scale` for audit.",
  "",
  "## Unit Checks",
  "",
  md_table(unit_checks, 3),
  "",
  "## Category-Level Food Outcome Descriptives",
  "",
  md_table(cat_desc, 3),
  "",
  "## Key Variable Descriptives",
  "",
  md_table(desc, 3),
  "",
  "## Variables Flagged by Max-to-P99 Ratio",
  "",
  md_table(desc[desc$outlier_attention != "", c("variable", "unit", "n", "p99", "max", "max_to_p99", "outlier_attention")], 3)
)
writeLines(report_lines, path("outputs", "reports", "paper1_unit_kg_month_descriptive_check.md"), useBytes = TRUE)

log_lines <- c(
  "# Unit kg/month Check",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  paste0("- Input: `", input_file, "`."),
  paste0("- Output: `", kg_file, "`."),
  "- Quantities converted from jin/month to kg/month.",
  "- Unit values converted from yuan/jin to yuan/kg.",
  "- Descriptive tables and top-extreme table were written for human review."
)
writeLines(log_lines, path("outputs", "logs", "unit_kg_month_check.md"), useBytes = TRUE)

message("Unit conversion and descriptive check completed.")
````

## `code/19_apply_kg_units_drop_outliers_prepare_official_data.R`

- Size: 19.2 KB
- Lines: 459

````r
options(warn = 1)

root <- getwd()
dir.create(file.path(root, "data", "analysis_ready"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "data", "cleaned"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "data", "backups"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "tables"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "logs"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(root, "outputs", "reports"), recursive = TRUE, showWarnings = FALSE)

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

fmt <- function(x, digits = 3) {
  ifelse(is.na(x), "", formatC(x, format = "f", digits = digits, big.mark = ","))
}

md_table <- function(df, digits = 3) {
  if (is.null(df) || nrow(df) == 0) return("")
  out <- df
  for (nm in names(out)) {
    if (is.numeric(out[[nm]])) out[[nm]] <- fmt(out[[nm]], digits)
  }
  cols <- names(out)
  lines <- c(
    paste0("| ", paste(cols, collapse = " | "), " |"),
    paste0("|", paste(rep("---", length(cols)), collapse = "|"), "|")
  )
  for (i in seq_len(nrow(out))) {
    vals <- vapply(out[i, , drop = FALSE], function(x) as.character(x[1]), character(1))
    vals <- gsub("\\|", "\\\\|", vals)
    lines <- c(lines, paste0("| ", paste(vals, collapse = " | "), " |"))
  }
  paste(lines, collapse = "\n")
}

get_original <- function(data, var, original_var = NULL) {
  if (is.null(original_var)) original_var <- paste0(var, "_original")
  if (original_var %in% names(data)) return(to_num(data[[original_var]]))
  to_num(data[[var]])
}

safe_quantile <- function(x, p, min_positive = 30) {
  x <- to_num(x)
  x <- x[is.finite(x)]
  if (sum(x > 0, na.rm = TRUE) < min_positive) return(NA_real_)
  as.numeric(quantile(x, p, na.rm = TRUE, names = FALSE))
}

threshold_by_category <- function(data, var, p = 0.995, min_positive = 30) {
  rows <- lapply(split(data, data$food_category), function(d) {
    x <- to_num(d[[var]])
    q <- safe_quantile(x, p, min_positive = min_positive)
    data.frame(
      food_category = d$food_category[1],
      food_category_label = d$food_category_label[1],
      variable = var,
      threshold_quantile = p,
      n_nonmissing = sum(!is.na(x)),
      n_positive = sum(x > 0, na.rm = TRUE),
      threshold = q,
      stringsAsFactors = FALSE
    )
  })
  do.call(rbind, rows)
}

flag_gt_threshold <- function(data, var, thresholds) {
  out <- rep(FALSE, nrow(data))
  if (!var %in% names(data)) return(out)
  for (i in seq_len(nrow(thresholds))) {
    cat <- thresholds$food_category[i]
    thr <- thresholds$threshold[i]
    if (!is.finite(thr)) next
    idx <- data$food_category == cat
    x <- to_num(data[[var]])
    out[idx] <- !is.na(x[idx]) & x[idx] > thr
  }
  out
}

summarise_numeric <- function(data, vars, module = "") {
  rows <- lapply(vars[vars %in% names(data)], function(v) {
    x <- to_num(data[[v]])
    ok <- !is.na(x) & is.finite(x)
    qs <- if (any(ok)) as.numeric(quantile(x[ok], c(.01, .05, .25, .5, .75, .95, .99), names = FALSE)) else rep(NA_real_, 7)
    data.frame(
      module = module,
      variable = v,
      n = sum(ok),
      missing = sum(!ok),
      missing_share = mean(!ok),
      mean = if (any(ok)) mean(x[ok]) else NA_real_,
      sd = if (sum(ok) > 1) sd(x[ok]) else NA_real_,
      min = if (any(ok)) min(x[ok]) else NA_real_,
      p01 = qs[1],
      p05 = qs[2],
      p25 = qs[3],
      median = qs[4],
      p75 = qs[5],
      p95 = qs[6],
      p99 = qs[7],
      max = if (any(ok)) max(x[ok]) else NA_real_,
      stringsAsFactors = FALSE
    )
  })
  out <- do.call(rbind, rows)
  rownames(out) <- NULL
  out
}

top_extremes <- function(data, vars, n_top = 10) {
  rows <- list()
  for (v in vars[vars %in% names(data)]) {
    x <- to_num(data[[v]])
    idx <- which(!is.na(x) & is.finite(x))
    if (length(idx) == 0) next
    idx <- idx[order(x[idx], decreasing = TRUE)]
    idx <- idx[seq_len(min(length(idx), n_top))]
    rows[[length(rows) + 1]] <- data.frame(
      variable = v,
      rank = seq_along(idx),
      value = x[idx],
      nhCode = data$nhCode[idx],
      data_year = data$data_year[idx],
      provn = data$provn[idx],
      countyn = data$countyn[idx],
      townn_std = data$townn_std[idx],
      viln_std = data$viln_std[idx],
      food_category = data$food_category[idx],
      food_category_label = data$food_category_label[idx],
      stringsAsFactors = FALSE
    )
  }
  out <- do.call(rbind, rows)
  rownames(out) <- NULL
  out
}

analysis_file <- path("data", "analysis_ready", "paper1_reprocessed_analysis_ready_long.csv")
revised_file <- path("data", "analysis_ready", "paper1_revised_analysis_ready_long.csv")
canonical_file <- path("data", "cleaned", "paper1_household_category_long.csv")
kg_clean_file <- path("data", "analysis_ready", "paper1_reprocessed_analysis_ready_long_kg_month_outlier_cleaned.csv")

timestamp <- format(Sys.time(), "%Y%m%d_%H%M%S")
for (f in c(analysis_file, revised_file, canonical_file)) {
  if (file.exists(f)) {
    backup <- path("data", "backups", paste0(timestamp, "_", basename(f)))
    file.copy(f, backup, overwrite = FALSE)
  }
}

data <- read_csv(
  analysis_file,
  colClasses = c(
    nhCode = "character",
    xzc12 = "character",
    xzc12_for_merge_final = "character",
    xzc12_for_merge = "character"
  )
)

required_categories <- c("zhushi", "doulei", "roulei", "danlei", "nailei", "youzhi", "shucai", "shuiguo")
data <- data[data$food_category %in% required_categories, ]

data$cons_monthly_jin_original_jin <- get_original(data, "cons_monthly_jin", "cons_monthly_jin_original_jin")
data$selfprod_monthly_total_original_jin <- get_original(data, "selfprod_monthly_total", "selfprod_monthly_total_original_jin")
if ("purchase_qty_sum_jin" %in% names(data)) {
  data$purchase_qty_sum_jin_original_jin <- get_original(data, "purchase_qty_sum_jin", "purchase_qty_sum_jin_original_jin")
}

data$cons_kg_month <- data$cons_monthly_jin_original_jin * 0.5
data$selfprod_kg_month <- data$selfprod_monthly_total_original_jin * 0.5
if ("purchase_qty_sum_jin" %in% names(data)) data$purchase_qty_kg_month <- data$purchase_qty_sum_jin_original_jin * 0.5

price_suffix_vars <- grep("yuan_per_jin$", names(data), value = TRUE)
for (v in price_suffix_vars) {
  original_v <- paste0(v, "_original_yuan_per_jin")
  data[[original_v]] <- get_original(data, v, original_v)
  kg_v <- sub("yuan_per_jin$", "yuan_per_kg", v)
  data[[kg_v]] <- data[[original_v]] * 2
  data[[v]] <- data[[kg_v]]
}

price_extra_vars <- c(
  "price_recalc_spend_sum_over_purchase_qty_sum",
  "village_price_category_median",
  "price_mean_detail_total_spend_over_qty",
  "price_mean_detail_avg_each_purchase",
  "price_mean_raw_pjxfl"
)
for (v in intersect(price_extra_vars, names(data))) {
  original_v <- paste0(v, "_original_yuan_per_jin")
  data[[original_v]] <- get_original(data, v, original_v)
  kg_v <- paste0(v, "_yuan_per_kg")
  data[[kg_v]] <- data[[original_v]] * 2
  data[[v]] <- data[[kg_v]]
}

data$production_participation <- as.integer(!is.na(data$selfprod_kg_month) & data$selfprod_kg_month > 0)
data$log_selfprod_amount_original_jin_scale <- data$log_selfprod_amount
data$ihs_selfprod_amount_original_jin_scale <- data$ihs_selfprod_amount
data$log_selfprod_amount <- log1p(pmax(data$selfprod_kg_month, 0))
data$ihs_selfprod_amount <- asinh(pmax(data$selfprod_kg_month, 0))
data$log_selfprod_amount_kg_month <- data$log_selfprod_amount
data$ihs_selfprod_amount_kg_month <- data$ihs_selfprod_amount

data$cons_monthly_jin <- data$cons_kg_month
data$selfprod_monthly_total <- data$selfprod_kg_month
if ("purchase_qty_sum_jin" %in% names(data)) data$purchase_qty_sum_jin <- data$purchase_qty_kg_month

quantity_vars <- c("cons_kg_month", "selfprod_kg_month", "purchase_qty_kg_month")
quantity_thresholds <- do.call(rbind, lapply(quantity_vars[quantity_vars %in% names(data)], function(v) {
  threshold_by_category(data, v, p = 0.995, min_positive = 30)
}))
write_csv(quantity_thresholds, path("outputs", "tables", "paper1_outlier_thresholds_quantity_kg_month.csv"))

data$outlier_cons_kg_month <- flag_gt_threshold(data, "cons_kg_month", quantity_thresholds[quantity_thresholds$variable == "cons_kg_month", ])
data$outlier_selfprod_kg_month <- flag_gt_threshold(data, "selfprod_kg_month", quantity_thresholds[quantity_thresholds$variable == "selfprod_kg_month", ])
data$outlier_purchase_qty_kg_month <- flag_gt_threshold(data, "purchase_qty_kg_month", quantity_thresholds[quantity_thresholds$variable == "purchase_qty_kg_month", ])
data$outlier_quantity_any <- data$outlier_cons_kg_month | data$outlier_selfprod_kg_month | data$outlier_purchase_qty_kg_month

price_clean_threshold_vars <- c(
  "price_preferred_household_recalc_w99_yuan_per_kg",
  "price_hedonic_imputed_w99_yuan_per_kg",
  "village_price_category_median_yuan_per_kg",
  "spend_sum_yuan"
)
price_thresholds <- do.call(rbind, lapply(price_clean_threshold_vars[price_clean_threshold_vars %in% names(data)], function(v) {
  p <- if (v == "village_price_category_median_yuan_per_kg") 0.99 else 0.995
  threshold_by_category(data, v, p = p, min_positive = 30)
}))
write_csv(price_thresholds, path("outputs", "tables", "paper1_outlier_thresholds_price_spend.csv"))

data$outlier_observed_price_any <- flag_gt_threshold(
  data,
  "price_preferred_household_recalc_w99_yuan_per_kg",
  price_thresholds[price_thresholds$variable == "price_preferred_household_recalc_w99_yuan_per_kg", ]
)
data$outlier_hedonic_price_any <- flag_gt_threshold(
  data,
  "price_hedonic_imputed_w99_yuan_per_kg",
  price_thresholds[price_thresholds$variable == "price_hedonic_imputed_w99_yuan_per_kg", ]
)
data$outlier_spend_any <- flag_gt_threshold(
  data,
  "spend_sum_yuan",
  price_thresholds[price_thresholds$variable == "spend_sum_yuan", ]
)
data$outlier_village_price_any <- flag_gt_threshold(
  data,
  "village_price_category_median_yuan_per_kg",
  price_thresholds[price_thresholds$variable == "village_price_category_median_yuan_per_kg", ]
)

## Price anomalies are removed from price variables. Row exclusion is driven
## by food quantity anomalies so participation is not mechanically changed by
## purchase-price availability.
for (v in c(
  "price_preferred_household_recalc_w99_yuan_per_kg",
  "price_preferred_household_recalc_w99_yuan_per_jin",
  "price_preferred_household_recalc_yuan_per_kg",
  "price_preferred_household_recalc_yuan_per_jin"
)) {
  if (v %in% names(data)) data[[v]][data$outlier_observed_price_any] <- NA_real_
}
for (v in c("village_price_category_median_yuan_per_kg", "village_price_category_median")) {
  if (v %in% names(data)) data[[v]][data$outlier_village_price_any] <- NA_real_
}

if ("price_hedonic_imputed_w99_yuan_per_kg" %in% names(data)) {
  data$price_hedonic_imputed_w99_yuan_per_kg_clean <- data$price_hedonic_imputed_w99_yuan_per_kg
  data$price_hedonic_imputed_w99_yuan_per_kg_clean[data$outlier_hedonic_price_any] <- NA_real_
  for (cat in unique(data$food_category)) {
    idx <- data$food_category == cat
    med <- median(data$price_hedonic_imputed_w99_yuan_per_kg_clean[idx], na.rm = TRUE)
    if (is.na(med)) med <- median(data$price_hedonic_imputed_w99_yuan_per_kg_clean, na.rm = TRUE)
    data$price_hedonic_imputed_w99_yuan_per_kg_clean[idx & is.na(data$price_hedonic_imputed_w99_yuan_per_kg_clean)] <- med
  }
  data$price_hedonic_imputed_w99_yuan_per_kg <- data$price_hedonic_imputed_w99_yuan_per_kg_clean
  data$price_hedonic_imputed_w99_yuan_per_jin <- data$price_hedonic_imputed_w99_yuan_per_kg_clean
}

data$outlier_row_excluded_from_models <- data$outlier_quantity_any
clean <- data[!data$outlier_row_excluded_from_models, ]

clean$unit_system <- "kg_month_outlier_cleaned_v1"
clean$quantity_unit_for_models <- "kg/month/household"
clean$price_unit_for_models <- "yuan/kg"
clean$compatibility_note <- "Columns ending in _jin or _yuan_per_jin are retained for older scripts but now contain kg/month or yuan/kg values."

food_order <- required_categories
clean$food_category <- factor(clean$food_category, levels = food_order)
clean <- clean[order(clean$nhCode, clean$food_category), ]
clean$food_category <- as.character(clean$food_category)

write_csv(clean, kg_clean_file)
write_csv(clean, analysis_file)
write_csv(clean, canonical_file)
write_csv(clean, revised_file)

summary_rows <- data.frame(
  metric = c(
    "rows_before_outlier_exclusion",
    "rows_after_outlier_exclusion",
    "rows_dropped_for_quantity_outlier",
    "households_before",
    "households_after",
    "food_categories",
    "observed_price_cells_set_missing",
    "hedonic_price_cells_replaced_by_category_median",
    "village_price_cells_set_missing",
    "spend_outlier_rows_flagged_not_dropped"
  ),
  value = c(
    nrow(data),
    nrow(clean),
    sum(data$outlier_row_excluded_from_models),
    length(unique(data$nhCode)),
    length(unique(clean$nhCode)),
    length(unique(clean$food_category)),
    sum(data$outlier_observed_price_any, na.rm = TRUE),
    sum(data$outlier_hedonic_price_any, na.rm = TRUE),
    sum(data$outlier_village_price_any, na.rm = TRUE),
    sum(data$outlier_spend_any, na.rm = TRUE)
  ),
  stringsAsFactors = FALSE
)
write_csv(summary_rows, path("outputs", "tables", "paper1_kg_month_outlier_cleaning_summary.csv"))

drop_counts <- aggregate(
  cbind(outlier_cons_kg_month, outlier_selfprod_kg_month, outlier_purchase_qty_kg_month, outlier_quantity_any,
        outlier_observed_price_any, outlier_hedonic_price_any, outlier_village_price_any, outlier_spend_any) ~
    food_category + food_category_label,
  data = data,
  FUN = function(x) sum(x, na.rm = TRUE)
)
drop_counts$n_before <- as.integer(table(factor(data$food_category, levels = drop_counts$food_category)))
drop_counts$n_after <- as.integer(table(factor(clean$food_category, levels = drop_counts$food_category)))
write_csv(drop_counts, path("outputs", "tables", "paper1_kg_month_outlier_counts_by_category.csv"))

desc_vars <- c(
  "production_participation", "cons_kg_month", "selfprod_kg_month", "purchase_qty_kg_month",
  "self_suff_rate", "log_selfprod_amount", "ihs_selfprod_amount",
  "price_hedonic_imputed_w99_yuan_per_kg", "price_preferred_household_recalc_w99_yuan_per_kg",
  "village_price_category_median_yuan_per_kg", "spend_sum_yuan",
  "household_size_reconstructed", "child_share", "elderly_share", "female_share",
  "agricultural_labor_days", "offfarm_labor_days", "total_sown_area"
)
desc <- summarise_numeric(clean, desc_vars, "kg_month_outlier_cleaned")
write_csv(desc, path("outputs", "tables", "paper1_descriptives_after_kg_outlier_cleaning.csv"))

category_desc <- aggregate(
  cbind(production_participation, cons_kg_month, selfprod_kg_month, self_suff_rate, price_hedonic_imputed_w99_yuan_per_kg) ~
    food_category + food_category_label,
  data = clean,
  FUN = function(x) mean(x, na.rm = TRUE)
)
names(category_desc)[names(category_desc) == "production_participation"] <- "participation_rate"
names(category_desc)[names(category_desc) == "cons_kg_month"] <- "mean_cons_kg_month"
names(category_desc)[names(category_desc) == "selfprod_kg_month"] <- "mean_selfprod_kg_month"
names(category_desc)[names(category_desc) == "self_suff_rate"] <- "mean_self_suff_rate"
names(category_desc)[names(category_desc) == "price_hedonic_imputed_w99_yuan_per_kg"] <- "mean_price_yuan_per_kg"
write_csv(category_desc, path("outputs", "tables", "paper1_category_descriptives_after_kg_outlier_cleaning.csv"))

extremes_after <- top_extremes(clean, c(
  "cons_kg_month", "selfprod_kg_month", "purchase_qty_kg_month",
  "price_hedonic_imputed_w99_yuan_per_kg", "village_price_category_median_yuan_per_kg",
  "total_sown_area"
), n_top = 10)
write_csv(extremes_after, path("outputs", "tables", "paper1_top_extreme_values_after_kg_outlier_cleaning.csv"))

report_lines <- c(
  "# Paper 1 kg/month Unit Conversion and Outlier Exclusion",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Official Analysis Files Updated",
  "",
  "- `data/analysis_ready/paper1_reprocessed_analysis_ready_long.csv`",
  "- `data/cleaned/paper1_household_category_long.csv`",
  paste0("- `", kg_clean_file, "`"),
  "",
  "## Unit Rules",
  "",
  "- Household food quantities are converted from jin/month to kg/month using `kg = jin * 0.5`.",
  "- Unit values are converted from yuan/jin to yuan/kg using `yuan/kg = yuan/jin * 2`.",
  "- `log_selfprod_amount` and `ihs_selfprod_amount` are recomputed from `selfprod_kg_month`.",
  "- The quantities are household totals, so the model unit is kg/month/household, not kg/person/month.",
  "- Legacy column names ending in `_jin` or `_yuan_per_jin` are retained for old scripts, but their values are now kg/month or yuan/kg. Clearly named kg/yuan-per-kg columns are also present.",
  "",
  "## Outlier Rules",
  "",
  "- Food quantity rows are excluded from model data when `cons_kg_month`, `selfprod_kg_month`, or `purchase_qty_kg_month` exceeds the food-category P99.5 threshold, provided the category has at least 30 positive observations for that variable.",
  "- Observed household unit-value outliers are set to missing before observed-price-only robustness models.",
  "- Village median unit-value outliers are set to missing before village-price robustness models; this removes the 30,000 yuan/kg village-price records.",
  "- Hedonic main price outliers are replaced by the category median so the main price control remains complete.",
  "- Spending outliers are flagged for audit but not used to drop rows, because spending is not a model outcome.",
  "",
  "## Cleaning Summary",
  "",
  md_table(summary_rows, 3),
  "",
  "## Outlier Counts by Category",
  "",
  md_table(drop_counts, 3),
  "",
  "## Category Descriptives After Cleaning",
  "",
  md_table(category_desc, 3),
  "",
  "## Key Descriptives After Cleaning",
  "",
  md_table(desc, 3)
)
writeLines(report_lines, path("outputs", "reports", "paper1_kg_month_outlier_cleaning_report.md"), useBytes = TRUE)

log_lines <- c(
  "# kg/month Unit Conversion and Outlier Cleaning Log",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "- Converted official analysis data to kg/month/household and yuan/kg.",
  "- Excluded quantity outlier household-category rows using category-specific P99.5 thresholds.",
  "- Cleaned price outliers before robustness and main-price use.",
  "- Backups of prior analysis files were written to `data/backups/`.",
  "",
  "## Summary",
  "",
  paste0("- Rows before: ", summary_rows$value[summary_rows$metric == "rows_before_outlier_exclusion"]),
  paste0("- Rows after: ", summary_rows$value[summary_rows$metric == "rows_after_outlier_exclusion"]),
  paste0("- Rows dropped: ", summary_rows$value[summary_rows$metric == "rows_dropped_for_quantity_outlier"]),
  paste0("- Households before: ", summary_rows$value[summary_rows$metric == "households_before"]),
  paste0("- Households after: ", summary_rows$value[summary_rows$metric == "households_after"])
)
writeLines(log_lines, path("outputs", "logs", "kg_month_outlier_cleaning.md"), useBytes = TRUE)

message("kg/month unit conversion and outlier cleaning completed.")
````

## `code/run_revised_pipeline.R`

- Size: 0.9 KB
- Lines: 30

````r
options(warn = 1)

root <- getwd()
if (!file.exists(file.path(root, "code", "00_setup.R"))) {
  stop("Run this script from the paper project root: ", root)
}

scripts <- c(
  "code/19_apply_kg_units_drop_outliers_prepare_official_data.R",
  "code/01_rebuild_revised_analysis_data.R",
  "code/02_common_sample_baseline.R",
  "code/03_baseline_coefficients_margins.R",
  "code/04_category_specific_nsi.R",
  "code/05_two_part_model.R",
  "code/06_price_robustness.R",
  "code/07_category_definition_audits.R",
  "code/08_robustness_checks.R",
  "code/09_appendix_market_friction_interactions.R",
  "code/10_appendix_iv_diagnostics.R",
  "code/11_compile_revised_results_report.R",
  "code/14_editor_revision_analyses.R",
  "code/13_compile_all_integrated_markdowns.R"
)

for (script in scripts) {
  message("===== RUN ", script, " =====")
  source(script, local = new.env(parent = globalenv()))
}

message("Revised Paper 1 pipeline completed.")
````

