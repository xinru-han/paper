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