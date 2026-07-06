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