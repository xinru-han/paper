# Paper 8 script 04 (= plan 80b): analysis panels from Data_merged.csv
# Outputs (data/interim/):
#   hh_info.csv                 household covariates + activity window + tier
#   trips_hh_day_cat.csv.gz     hh x day x category purchases (positive rows only)
#   panel_hh_day.rds            hh x day grid within activity window: trip, spend
#   unit_day_cat.csv.gz         exposure-unit x day x group10 aggregates (for lags)
# P8_DEBUG=TRUE keeps a 5% household subsample.
source("/root/data/Paper/央视数据/paper8-hot/code/00_setup.R")

logmsg("04: reading Data_merged.csv ...")
tr <- fread(file.path(RAW, "Data_merged.csv"),
            select = c("ID","Province","Family_Type","Family_Size","Family_Income","Date","Category","Spend"),
            encoding = "UTF-8", showProgress = FALSE)
if (DEBUG) tr <- tr[ID %% 20L == 0L]
tr[, date := fifelse(grepl("/", Date), as.IDate(Date, format = "%Y/%m/%d"), as.IDate(Date))]
tr[, Date := NULL]
stopifnot(tr[is.na(date), .N] == 0)
tr <- tr[date >= as.IDate("2020-01-01") & date <= as.IDate("2022-12-31")]
tr <- tr[is.finite(Spend) & Spend > 0]

## tier + income midpoint
tier <- fread(file.path(P1, "processed/city_tier_sample_mapping.csv"), encoding = "UTF-8")
tr <- merge(tr, tier[, .(ID, CityTier, tier_a = city_tier_a_flag)], by = "ID", all.x = TRUE)
tr <- tr[!is.na(CityTier)]
inc_mid <- function(s) {
  s <- gsub("\\s*RMB", "", s)
  fcase(grepl("^>\\s*12000|大于12000", s), 15000,
        grepl("-", s), (as.numeric(sub("-.*","",s)) + as.numeric(sub(".*-","",s)))/2,
        grepl("^<|小于", s), as.numeric(gsub("[^0-9]","",s))/2,
        default = NA_real_)
}
tr[, income_mid := inc_mid(Family_Income)]

catmap <- fread(file.path(DIR_LKP, "category_map.csv"), encoding = "UTF-8")
tr <- merge(tr, catmap, by = "Category", all.x = TRUE)
stopifnot(tr[is.na(food_group10), .N] == 0)

hh <- tr[, .(Province = Province[1], CityTier = CityTier[1], tier_a = tier_a[1],
             Family_Type = Family_Type[1], income_mid = income_mid[1],
             first_date = min(date), last_date = max(date),
             n_trip_days = uniqueN(date), total_spend = sum(Spend)), by = ID]
fwrite(hh, file.path(DIR_INT, "hh_info.csv"))
logmsg("04: ", nrow(hh), " households, ", nrow(tr), " transactions")

trips <- tr[, .(spend = sum(Spend), n_trans = .N),
            by = .(ID, date, Category, food_group10, perish_class)]
fwrite(trips, file.path(DIR_INT, "trips_hh_day_cat.csv.gz"))
rm(tr); gc()

## hh x day grid within activity window (memory-lean: integer keys)
hh[, `:=`(d0 = as.integer(first_date), d1 = as.integer(last_date))]
grid <- hh[, .(day_i = seq.int(d0, d1)), by = .(ID)]
day_spend <- trips[, .(spend = sum(spend)), by = .(ID, date)][, day_i := as.integer(date)][, date := NULL]
grid <- merge(grid, day_spend, by = c("ID","day_i"), all.x = TRUE)
grid[, trip := as.integer(!is.na(spend))][is.na(spend), spend := 0]
saveRDS(grid, file.path(DIR_INT, "panel_hh_day.rds"), compress = FALSE)
logmsg("04: hh-day grid ", nrow(grid), " rows, trip share ", round(mean(grid$trip), 4))
rm(grid, day_spend); gc()

## exposure-unit (province x tier_a) x day x group aggregates
trips <- merge(trips, hh[, .(ID, Province, tier_a)], by = "ID")
# active households per unit x day (denominator: activity windows)
act <- hh[, .(day_i = seq.int(d0, d1)), by = .(ID, Province, tier_a)][
  , .(n_active = uniqueN(ID)), by = .(Province, tier_a, day_i)]
udc <- trips[, .(spend = sum(spend), n_buyers = uniqueN(ID)),
             by = .(Province, tier_a, date, food_group10)][, day_i := as.integer(date)]
udc <- merge(udc, act, by = c("Province","tier_a","day_i"))
udc[, `:=`(spend_pc = spend / n_active, buyer_share = n_buyers / n_active)]
fwrite(udc, file.path(DIR_INT, "unit_day_cat.csv.gz"))
logmsg("04: unit-day-cat ", nrow(udc), " rows; done")
