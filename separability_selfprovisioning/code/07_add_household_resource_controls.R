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