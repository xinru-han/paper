#!/usr/bin/env Rscript
# ============================================================================
# v2 step 34: pairs cluster bootstrap (household level) for the full two-step
# pipeline. Households are resampled with replacement and enter every stage
# through frequency weights (no row duplication):
#   Stone weights -> probit first stage (warm start) -> GLS system with the
#   main-fit Sigma held fixed -> elasticities incl. participation margin.
# Reported: percentile CIs + bootstrap SEs for expenditure elasticities, the
# full Marshallian/Hicksian matrices, Slutsky eigenvalues, and key subgroup
# elasticities. This carries the two-step (probit-generated-regressor) and
# Stone-weight uncertainty that the analytic sandwich misses.
# ============================================================================

suppressPackageStartupMessages({ library(data.table); library(parallel) })
base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
source(file.path(base, "src", "31_lib_v2.R"))
odir <- file.path(base, "outputs", "inference")
dir.create(odir, recursive = TRUE, showWarnings = FALSE)

SMOKE <- nzchar(Sys.getenv("SMOKE_V2"))
B <- if (SMOKE) 8 else as.integer(Sys.getenv("BOOT_B", "200"))
N_CORES <- if (SMOKE) 2 else as.integer(Sys.getenv("BOOT_CORES", "5"))
CURV <- nzchar(Sys.getenv("CURV"))   # impose B = -LL' in every replication
sfx <- if (CURV) "_curv" else ""

message("[34] Loading panel and main fit ...")
main <- readRDS(file.path(base, "outputs", "demand",
                          if (CURV) "main_fit_curv_v2.rds" else "main_fit_v2.rds"))
lay <- main$lay
panel <- fread(file.path(base, "data_derived", "household_month_group9_v2.csv"), encoding = "UTF-8")
wide <- make_wide(panel, price_col = "lp_ext")
rm(panel); gc(FALSE)
if (SMOKE) {
  set.seed(1)
  wide <- wide[ID %in% sample(unique(wide$ID), 3000)]
}

wt1 <- rep(1, nrow(wide))
stone_base <- compute_stone_weights(wide, wt1)
wide <- derive_vars(wide, stone_base, omit = lay$omit)
wide <- add_mundlak(wide, omit = lay$omit)

ids <- unique(wide$ID)
nH <- length(ids)
message(sprintf("[34] %d households, %d rows, B = %d, cores = %d", nH, nrow(wide), B, N_CORES))

# expenditure quintiles fixed at base sample (subgroup definitions must not
# shift across bootstrap replications)
xq <- cut(wide$total_food_spend_pc_month,
          quantile(wide$total_food_spend_pc_month, seq(0, 1, 0.2)),
          include.lowest = TRUE, labels = FALSE)
subgroups <- list(low_income = wide$low_income == 1,
                  non_low_income = wide$low_income == 0,
                  elderly = wide$elderly_household == 1,
                  non_elderly = wide$elderly_household == 0,
                  large_family = wide$large_family == 1,
                  small_family = wide$large_family == 0)
for (q in 1:5) subgroups[[paste0("xq", q)]] <- xq == q
for (q in 1:5) subgroups[[paste0("inc", q)]] <- wide$income_group_order == q

yq_curv <- quantile(wide$y_easi, c(0.01, 0.99))  # fixed constraint points

# All resampling draws generated up-front in the parent for reproducibility
# BOOT_SEED/BOOT_TAG support top-up batches (new seed, separate draws file,
# no summary CSVs); 34b merges all draws files and rebuilds the summaries.
TAG <- Sys.getenv("BOOT_TAG", "")
set.seed(as.integer(Sys.getenv("BOOT_SEED", "20240707")))
freq_list <- lapply(seq_len(B), function(b) {
  draw <- sample.int(nH, nH, replace = TRUE)
  tab <- tabulate(draw, nbins = nH)
  tab[match(wide$ID, ids)]
})

row_id <- match(wide$ID, ids)  # unused below but kept for clarity of mapping

one_rep <- function(b) {
  wt_b <- as.numeric(freq_list[[b]])
  wb <- copy(wide)
  sw_b <- compute_stone_weights(wb, wt_b)
  # guard: fill any empty province-month cell from base Stone weights
  sw_cols <- paste0("sw_", CODES9)
  bad <- !stats::complete.cases(sw_b[, ..sw_cols])
  if (any(bad)) {
    fill <- stone_base[sw_b[bad, .(Province, year_month)], on = c("Province","year_month")]
    sw_b[bad, (sw_cols) := fill[, ..sw_cols]]
  }
  wb <- derive_vars(wb, sw_b, omit = lay$omit)
  wb <- add_mundlak(wb, omit = lay$omit)
  fs_b <- fit_probits(wb, wt_b, omit = lay$omit, beta0_list = main$probit_betas)
  pp_b <- predict_probits(wb, fs_b$betas, omit = lay$omit)
  fit_b <- fit_system(wb, lay, pp_b$Phi, pp_b$phi, wt_b, Sigma = main$Sigma,
                      keep_xtx_inv = CURV)
  beta_b <- if (CURV) impose_curvature(fit_b, lay, y_lo = yq_curv[1], y_hi = yq_curv[2])$beta else fit_b$beta
  el_b <- compute_elasticities(wb, lay, beta_b, fs_b$betas, sw_b, wt_b,
                               subgroups = subgroups)
  rm(wb); gc(FALSE)
  list(rep = b,
       exp = el_b$all$exp,
       mar = el_b$all$mar,
       hick = el_b$all$hick,
       eig = el_b$all$eigenvalues,
       curvature_ok = el_b$all$curvature_ok,
       sub = lapply(el_b$sub, function(s)
         list(exp = s$exp, own = diag(s$mar), hick = s$hick, wbar = s$wbar,
              eig_max = max(s$eigenvalues))),
       beta_price = beta_b[grepl("^(bp|cyp)__", lay$term_names)])
}

message("[34] Running bootstrap ...")
t0 <- Sys.time()
reps <- mclapply(seq_len(B), function(b) {
  out <- tryCatch(one_rep(b), error = function(e) {
    message(sprintf("  rep %d FAILED: %s", b, conditionMessage(e))); NULL
  })
  message(sprintf("  rep %d done (%.1f min elapsed)", b,
                  as.numeric(difftime(Sys.time(), t0, units = "mins"))))
  out
}, mc.cores = N_CORES, mc.preschedule = FALSE)
ok <- !vapply(reps, is.null, TRUE)
message(sprintf("[34] %d/%d replications succeeded", sum(ok), B))
reps <- reps[ok]
saveRDS(reps, file.path(odir, paste0("bootstrap_draws", sfx, TAG, "_v2.rds")))
if (nzchar(TAG)) {
  message(sprintf("[34] Top-up batch '%s' saved; run 34b to merge and rebuild CIs.", TAG))
  message(sprintf("[34] Done in %.1f min.", as.numeric(difftime(Sys.time(), t0, units = "mins"))))
  quit(save = "no")
}

# ---------------------------------------------------------------------------
# Summaries: bootstrap SE + percentile CI around the MAIN point estimates
# ---------------------------------------------------------------------------
el0 <- main$elasticities$all
qlh <- function(x) quantile(x, c(0.025, 0.975), na.rm = TRUE)

# expenditure elasticities
Ex <- do.call(rbind, lapply(reps, `[[`, "exp"))
exp_dt <- data.table(food_group10 = GROUPS9,
                     estimate = el0$exp,
                     boot_se = apply(Ex, 2, sd),
                     ci_lo = apply(Ex, 2, function(x) qlh(x)[1]),
                     ci_hi = apply(Ex, 2, function(x) qlh(x)[2]))
fwrite(exp_dt, file.path(odir, paste0("expenditure_elasticity_ci", sfx, "_v2.csv")), bom = TRUE)

# full Marshallian and Hicksian matrices
mat_ci <- function(field, point) {
  arr <- simplify2array(lapply(reps, `[[`, field))   # 9 x 9 x R
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

# Slutsky eigenvalues / curvature
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

# subgroups
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

message(sprintf("[34] Done in %.1f min.", as.numeric(difftime(Sys.time(), t0, units = "mins"))))
