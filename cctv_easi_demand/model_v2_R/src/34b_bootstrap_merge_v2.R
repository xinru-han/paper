#!/usr/bin/env Rscript
# v2 step 34b: merge bootstrap draws files (base + top-up batches) and rebuild
# all CI summary CSVs. Env: CURV=1 to use the curvature-constrained fit/draws.
suppressPackageStartupMessages({ library(data.table) })
base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
source(file.path(base, "src", "31_lib_v2.R"))
odir <- file.path(base, "outputs", "inference")

CURV <- nzchar(Sys.getenv("CURV"))
sfx <- if (CURV) "_curv" else ""
main <- readRDS(file.path(base, "outputs", "demand",
                          if (CURV) "main_fit_curv_v2.rds" else "main_fit_v2.rds"))

# merge batch files bootstrap_draws<sfx>_b*_v2.rds; write the merged list to
# the canonical bootstrap_draws<sfx>_v2.rds consumed by script 35
files <- list.files(odir, pattern = paste0("^bootstrap_draws", sfx, "_b[0-9]+_v2\\.rds$"),
                    full.names = TRUE)
if (!CURV) files <- files[!grepl("_curv", files)]
message(sprintf("[34b] merging %d draws files:\n  %s", length(files),
                paste(basename(files), collapse = "\n  ")))
reps <- do.call(c, lapply(files, readRDS))
message(sprintf("[34b] total replications: %d", length(reps)))
saveRDS(reps, file.path(odir, paste0("bootstrap_draws", sfx, "_v2.rds")))

el0 <- main$elasticities$all
qlh <- function(x) quantile(x, c(0.025, 0.975), na.rm = TRUE)

Ex <- do.call(rbind, lapply(reps, `[[`, "exp"))
exp_dt <- data.table(food_group10 = GROUPS9,
                     estimate = el0$exp,
                     boot_se = apply(Ex, 2, sd),
                     ci_lo = apply(Ex, 2, function(x) qlh(x)[1]),
                     ci_hi = apply(Ex, 2, function(x) qlh(x)[2]))
fwrite(exp_dt, file.path(odir, paste0("expenditure_elasticity_ci", sfx, "_v2.csv")), bom = TRUE)

mat_ci <- function(field, point) {
  arr <- simplify2array(lapply(reps, `[[`, field))
  rbindlist(lapply(1:9, function(i) rbindlist(lapply(1:9, function(j) {
    x <- arr[i, j, ]
    data.table(demand_group = GROUPS9[i], price_group = GROUPS9[j],
               estimate = point[i, j], boot_se = sd(x),
               ci_lo = qlh(x)[1], ci_hi = qlh(x)[2],
               sig_5pct = (qlh(x)[1] > 0) | (qlh(x)[2] < 0))
  }))))
}
fwrite(mat_ci("mar", el0$mar), file.path(odir, paste0("marshallian_ci", sfx, "_v2.csv")), bom = TRUE)
fwrite(mat_ci("hick", el0$hick), file.path(odir, paste0("hicksian_ci", sfx, "_v2.csv")), bom = TRUE)

Eig <- do.call(rbind, lapply(reps, `[[`, "eig"))
eig_dt <- data.table(order = 1:9,
                     estimate = el0$eigenvalues,
                     boot_se = apply(Eig, 2, sd),
                     ci_lo = apply(Eig, 2, function(x) qlh(x)[1]),
                     ci_hi = apply(Eig, 2, function(x) qlh(x)[2]))
curv_share <- mean(vapply(reps, `[[`, TRUE, "curvature_ok"))
fwrite(eig_dt, file.path(odir, paste0("slutsky_eigenvalue_ci", sfx, "_v2.csv")), bom = TRUE)
fwrite(data.table(stat = c("share_reps_curvature_ok", "n_reps"),
                  value = c(curv_share, length(reps))),
       file.path(odir, paste0("curvature_bootstrap_share", sfx, "_v2.csv")), bom = TRUE)

sub_names <- names(reps[[1]]$sub)
sub_dt <- rbindlist(lapply(sub_names, function(nm) {
  Ex_s <- do.call(rbind, lapply(reps, function(r) r$sub[[nm]]$exp))
  Ow_s <- do.call(rbind, lapply(reps, function(r) r$sub[[nm]]$own))
  p0 <- main$elasticities$sub[[nm]]
  data.table(subgroup = nm, food_group10 = GROUPS9,
             expenditure = p0$exp, exp_se = apply(Ex_s, 2, sd),
             exp_lo = apply(Ex_s, 2, function(x) qlh(x)[1]),
             exp_hi = apply(Ex_s, 2, function(x) qlh(x)[2]),
             own_price = diag(p0$mar), own_se = apply(Ow_s, 2, sd),
             own_lo = apply(Ow_s, 2, function(x) qlh(x)[1]),
             own_hi = apply(Ow_s, 2, function(x) qlh(x)[2]))
}))
fwrite(sub_dt, file.path(odir, paste0("subgroup_elasticity_ci", sfx, "_v2.csv")), bom = TRUE)
message("[34b] Done.")
