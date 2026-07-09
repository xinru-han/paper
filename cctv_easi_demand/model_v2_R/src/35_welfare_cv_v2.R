#!/usr/bin/env Rscript
# ============================================================================
# v2 step 35: welfare post-estimation. Second-order compensating variation of
# the 2020 -> 2022 food price changes, by income group x province:
#   CV/x  ~=  wbar' dlnp + 0.5 * dlnp' S dlnp,
# where wbar and the share-weighted symmetrized Slutsky matrix S come from the
# income-group-specific Hicksian elasticities of the main fit. The first-order
# term is the pure cost-of-living effect; the second-order term measures the
# mitigation from substitution. Bootstrap CIs re-evaluate CV with each
# replication's subgroup Hicksian/share draws (price changes are external
# data and are held fixed).
# ============================================================================

suppressPackageStartupMessages({ library(data.table) })
base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
odir <- file.path(base, "outputs", "welfare")
dir.create(odir, recursive = TRUE, showWarnings = FALSE)

CURV <- nzchar(Sys.getenv("CURV"))
main <- readRDS(file.path(base, "outputs", "demand",
                          if (CURV) "main_fit_curv_v2.rds" else "main_fit_v2.rds"))
source(file.path(base, "src", "31_lib_v2.R"))

# ---------------------------------------------------------------------------
# 1. Province-level log price changes, 2020 average -> 2022 average
# ---------------------------------------------------------------------------
gp <- fread(file.path(base, "data_derived", "group_prices_v2.csv"), encoding = "UTF-8")
gp[, year := substr(year_month, 1, 4)]
pm <- gp[year %in% c("2020","2022"),
         .(lp = mean(lp_ext)), by = .(Province, food_group10, year)]
dpr <- dcast(pm, Province + food_group10 ~ year, value.var = "lp")
dpr[, dlnp := `2022` - `2020`]
dp_mat <- as.matrix(dcast(dpr, Province ~ food_group10, value.var = "dlnp")[, -1])
provs <- dcast(dpr, Province ~ food_group10, value.var = "dlnp")$Province
stopifnot(ncol(dp_mat) == 9)
fwrite(dpr[, .(Province, food_group10, lp_2020 = `2020`, lp_2022 = `2022`, dlnp)],
       file.path(odir, "price_change_2020_2022_by_province_v2.csv"), bom = TRUE)

# ---------------------------------------------------------------------------
# 2. Expenditure base and household weights by income group x province
# ---------------------------------------------------------------------------
panel <- fread(file.path(base, "data_derived", "household_month_group9_v2.csv"),
               encoding = "UTF-8",
               select = c("ID","year_month","Province","income_group_order",
                          "total_food_spend_month"))
hm <- unique(panel, by = c("ID","year_month"))
rm(panel); gc(FALSE)
xp_base <- hm[, .(annual_food_exp = 12 * mean(total_food_spend_month),
                  n_households = uniqueN(ID)),
              by = .(Province, income_group_order)]

# ---------------------------------------------------------------------------
# 3. CV per income group x province
# ---------------------------------------------------------------------------
cv_one <- function(wbar, hick, dp) {
  Sm <- diag(wbar) %*% hick
  Ssym <- (Sm + t(Sm)) / 2
  fo <- sum(wbar * dp)
  so <- 0.5 * as.numeric(t(dp) %*% Ssym %*% dp)
  c(first_order = fo, second_order = so, cv_share = fo + so)
}

inc_names <- paste0("inc", 1:5)
cv_grid <- rbindlist(lapply(inc_names, function(nm) {
  s <- main$elasticities$sub[[nm]]
  rbindlist(lapply(seq_along(provs), function(p) {
    v <- cv_one(s$wbar, s$hick, dp_mat[p, ])
    data.table(income_group = nm, Province = provs[p],
               first_order = v["first_order"], substitution = v["second_order"],
               cv_share = v["cv_share"])
  }))
}))
cv_grid[, income_group_order := as.integer(sub("inc", "", income_group))]
cv_grid <- merge(cv_grid, xp_base, by.x = c("Province","income_group_order"),
                 by.y = c("Province","income_group_order"), all.x = TRUE)
cv_grid[, cv_yuan_per_year := cv_share * annual_food_exp]
fwrite(cv_grid, file.path(odir, "cv_by_income_province_v2.csv"), bom = TRUE)

# national summary (household-weighted across provinces)
cv_nat <- cv_grid[!is.na(n_households),
                  .(first_order = weighted.mean(first_order, n_households),
                    substitution = weighted.mean(substitution, n_households),
                    cv_share = weighted.mean(cv_share, n_households),
                    cv_yuan_per_year = weighted.mean(cv_yuan_per_year, n_households)),
                  by = income_group]
print(cv_nat)

# ---------------------------------------------------------------------------
# 4. Bootstrap CIs (subgroup Hicksian/share draws; prices held fixed)
# ---------------------------------------------------------------------------
brds <- file.path(base, "outputs", "inference",
                  if (CURV) "bootstrap_draws_curv_v2.rds" else "bootstrap_draws_v2.rds")
if (file.exists(brds)) {
  reps <- readRDS(brds)
  has_hick <- !is.null(reps[[1]]$sub[[inc_names[1]]]$hick)
  if (has_hick) {
    nat_draws <- rbindlist(lapply(seq_along(reps), function(b) {
      rbindlist(lapply(inc_names, function(nm) {
        sb <- reps[[b]]$sub[[nm]]
        g <- rbindlist(lapply(seq_along(provs), function(p) {
          v <- cv_one(sb$wbar, sb$hick, dp_mat[p, ])
          data.table(Province = provs[p], cv_share = v["cv_share"])
        }))
        g <- merge(g, xp_base[income_group_order == as.integer(sub("inc","",nm)),
                              .(Province, n_households)], by = "Province", all.x = TRUE)
        data.table(rep = b, income_group = nm,
                   cv_share = g[!is.na(n_households),
                                weighted.mean(cv_share, n_households)])
      }))
    }))
    ci <- nat_draws[, .(boot_se = sd(cv_share),
                        ci_lo = quantile(cv_share, 0.025),
                        ci_hi = quantile(cv_share, 0.975)), by = income_group]
    cv_nat <- merge(cv_nat, ci, by = "income_group")
  } else {
    message("[35] bootstrap draws lack subgroup Hicksian matrices; CIs skipped")
  }
} else {
  message("[35] no bootstrap draws found; CIs skipped")
}
setorder(cv_nat, income_group)
fwrite(cv_nat, file.path(odir, "cv_national_by_income_v2.csv"), bom = TRUE)
message("[35] Done.")
