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