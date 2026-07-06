#!/usr/bin/env Rscript
# ============================================================================
# v2 step 32: main estimation
#  - CRE/Mundlak probit first stage (9 groups)
#  - constrained SY-EASI share system, 8 equations (G03 vegetables omitted),
#    month-of-year FE + year FE + Mundlak means, fixed-weight Stone deflation,
#    iterated FGLS
#  - household- and province-clustered analytic sandwich SEs
#  - province-level wild cluster bootstrap for price coefficients
#  - elasticities (with participation margin), curvature diagnostics at the
#    aggregate point and on an expenditure-quintile x income grid
#  - QUAIDS variant, A(z) parametric heterogeneity variant + Wald test
#  - numeraire invariance check (omit G05 instead of G03)
#  - out-of-fold fit (5-fold household CV)
# ============================================================================

suppressPackageStartupMessages({ library(data.table) })
base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
source(file.path(base, "src", "31_lib_v2.R"))
dir.create(file.path(base, "outputs", "demand"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(base, "outputs", "regularity"), recursive = TRUE, showWarnings = FALSE)
odir <- file.path(base, "outputs", "demand")
rdir <- file.path(base, "outputs", "regularity")
SMOKE <- nzchar(Sys.getenv("SMOKE_V2"))

message("[32] Loading panel ...")
panel <- fread(file.path(base, "data_derived", "household_month_group9_v2.csv"), encoding = "UTF-8")
wide <- make_wide(panel, price_col = "lp_ext")
rm(panel); gc(FALSE)
if (SMOKE) {
  set.seed(1)
  keep_ids <- sample(unique(wide$ID), 3000)
  wide <- wide[ID %in% keep_ids]
  message("[32] SMOKE mode: ", nrow(wide), " rows, ", uniqueN(wide$ID), " households")
}

wt <- rep(1, nrow(wide))
stone_w <- compute_stone_weights(wide, wt)
wide <- derive_vars(wide, stone_w, omit = "G03")
wide <- add_mundlak(wide, omit = "G03")

message("[32] First stage probits ...")
t0 <- Sys.time()
fs <- fit_probits(wide, wt, omit = "G03")
message(sprintf("    probits done in %.1f min", as.numeric(difftime(Sys.time), t0, units="mins"))[1])
print(fs$stats)
fwrite(fs$stats, file.path(odir, "probit_fit_stats_v2.csv"), bom = TRUE)
pp <- predict_probits(wide, fs$betas, omit = "G03")

message("[32] Main constrained SY-EASI system (FGLS) ...")
lay <- system_layout(omit = "G03", az = FALSE, quaids = FALSE)
fit <- fit_system(wide, lay, pp$Phi, pp$phi, wt, Sigma = NULL, n_fgls = 2, keep_xtx_inv = TRUE)
message(sprintf("    system done, %d parameters", lay$n_par))

message("[32] Analytic cluster-robust SEs ...")
V_hh <- system_cluster_vcov(wide, lay, pp$Phi, pp$phi, wt, fit$beta, fit$Sigma, fit$xtx_inv, cluster = wide$ID)
V_pr <- system_cluster_vcov(wide, lay, pp$Phi, pp$phi, wt, fit$beta, fit$Sigma, fit$xtx_inv, cluster = wide$Province)
coefs <- data.table(term = lay$term_names, estimate = fit$beta,
                    se_cluster_household = sqrt(diag(V_hh)),
                    se_cluster_province = sqrt(diag(V_pr)))
coefs[, t_household := estimate / se_cluster_household]
fwrite(coefs, file.path(odir, "system_coefficients_main_v2.csv"), bom = TRUE)

message("[32] Wild cluster bootstrap (province, Webb weights) for price terms ...")
wild_cluster <- function(wide, lay, Phi, phi, wt, fitobj, B = 999, seed = 42) {
  set.seed(seed)
  G <- lay$G
  Sinv <- solve(fitobj$Sigma)
  U <- fitobj$resid %*% Sinv
  prov <- as.integer(factor(wide$Province))
  nP <- max(prov)
  blocks <- vector("list", G)
  for (g in seq_len(G)) {
    z <- build_Ag(wide, g, lay, Phi, phi)
    blocks[[g]] <- list(S = rowsum(z$A * (wt * U[, g]), prov), cols = z$cols)
  }
  webb <- c(-sqrt(1.5), -1, -sqrt(0.5), sqrt(0.5), 1, sqrt(1.5))
  P <- lay$n_par
  draws <- matrix(0, B, P)
  for (b in seq_len(B)) {
    fl <- sample(webb, nP, replace = TRUE)
    delta <- numeric(P)
    for (g in seq_len(G)) delta[blocks[[g]]$cols] <- delta[blocks[[g]]$cols] + as.numeric(crossprod(blocks[[g]]$S, fl))
    draws[b, ] <- as.numeric(fitobj$xtx_inv %*% delta)
  }
  pv <- colMeans(abs(draws) >= matrix(abs(fitobj$beta), B, P, byrow = TRUE))
  data.table(term = lay$term_names, estimate = fitobj$beta, wild_cluster_p = pv)
}
wc <- wild_cluster(wide, lay, pp$Phi, pp$phi, wt, fit, B = if (SMOKE) 99 else 999)
fwrite(wc[grepl("^(bp|cyp)__", term)], file.path(odir, "wild_cluster_province_price_terms_v2.csv"), bom = TRUE)

message("[32] Elasticities and curvature ...")
xq <- cut(wide$total_food_spend_pc_month,
          quantile(wide$total_food_spend_pc_month, seq(0, 1, 0.2)), include.lowest = TRUE, labels = FALSE)
subgroups <- list(low_income = wide$low_income == 1,
                  non_low_income = wide$low_income == 0,
                  elderly = wide$elderly_household == 1,
                  non_elderly = wide$elderly_household == 0,
                  large_family = wide$large_family == 1,
                  small_family = wide$large_family == 0)
for (q in 1:5) subgroups[[paste0("xq", q)]] <- xq == q
for (q in 1:5) subgroups[[paste0("inc", q)]] <- wide$income_group_order == q
el <- compute_elasticities(wide, lay, fit$beta, fs$betas, stone_w, wt, subgroups = subgroups)

save_el <- function(el_set, tag) {
  fwrite(data.table(food_group10 = GROUPS9, expenditure_elasticity = el_set$exp),
         file.path(odir, sprintf("expenditure_elasticity_%s.csv", tag)), bom = TRUE)
  fwrite(data.table(demand_group = GROUPS9, el_set$mar),
         file.path(odir, sprintf("marshallian_%s.csv", tag)), bom = TRUE)
  fwrite(data.table(demand_group = GROUPS9, el_set$hick),
         file.path(odir, sprintf("hicksian_%s.csv", tag)), bom = TRUE)
}
save_el(el$all, "main_v2")
own_dt <- data.table(food_group10 = GROUPS9, own_price = diag(el$all$mar), negative = diag(el$all$mar) < 0)
print(own_dt)
message("Curvature (aggregate): all eigenvalues <= 0 : ", el$all$curvature_ok)
print(round(el$all$eigenvalues, 4))

curv_rows <- list(cbind(point = "aggregate", data.table(t(el$all$eigenvalues)), curvature_ok = el$all$curvature_ok, n = el$all$n))
for (nm in names(el$sub)) {
  s <- el$sub[[nm]]
  curv_rows[[length(curv_rows)+1]] <- cbind(point = nm, data.table(t(s$eigenvalues)), curvature_ok = s$curvature_ok, n = s$n)
}
curv <- rbindlist(curv_rows)
setnames(curv, paste0("V", 1:9), paste0("eig", 1:9))
fwrite(curv, file.path(rdir, "curvature_eigenvalues_grid_v2.csv"), bom = TRUE)
fwrite(own_dt, file.path(rdir, "own_price_signs_main_v2.csv"), bom = TRUE)
fwrite(data.table(stat = names(el$resid_share_range), value = as.numeric(el$resid_share_range)),
       file.path(rdir, "residual_share_G03_distribution_v2.csv"), bom = TRUE)

sub_rows <- rbindlist(lapply(names(el$sub), function(nm) {
  s <- el$sub[[nm]]
  data.table(subgroup = nm, food_group10 = GROUPS9, expenditure = s$exp,
             own_price = diag(s$mar), n = s$n)
}))
fwrite(sub_rows, file.path(odir, "subgroup_elasticities_main_v2.csv"), bom = TRUE)

message("[32] QUAIDS variant ...")
layq <- system_layout(omit = "G03", az = FALSE, quaids = TRUE)
fitq <- fit_system(wide, layq, pp$Phi, pp$phi, wt, Sigma = NULL, n_fgls = 2)
elq <- compute_elasticities(wide, layq, fitq$beta, fs$betas, stone_w, wt)
save_el(elq$all, "quaids_v2")
fwrite(data.table(food_group10 = GROUPS9, own_easi = diag(el$all$mar), own_quaids = diag(elq$all$mar)),
       file.path(rdir, "own_price_easi_vs_quaids_v2.csv"), bom = TRUE)

message("[32] A(z) heterogeneous-price-response variant ...")
laz <- system_layout(omit = "G03", az = TRUE, quaids = FALSE)
fitz <- fit_system(wide, laz, pp$Phi, pp$phi, wt, Sigma = NULL, n_fgls = 2, keep_xtx_inv = TRUE)
Vz <- system_cluster_vcov(wide, laz, pp$Phi, pp$phi, wt, fitz$beta, fitz$Sigma, fitz$xtx_inv, cluster = wide$ID)
az_idx <- grep("^az_", laz$term_names)
bz <- fitz$beta[az_idx]
Wstat <- tryCatch(as.numeric(t(bz) %*% solve(Vz[az_idx, az_idx], bz)), error = function(e) NA_real_)
wald <- data.table(test = "H0: all A(z) price interactions = 0",
                   wald = Wstat, df = length(az_idx),
                   p_value = pchisq(Wstat, length(az_idx), lower.tail = FALSE))
print(wald)
fwrite(wald, file.path(odir, "az_wald_test_v2.csv"), bom = TRUE)
elz <- compute_elasticities(wide, laz, fitz$beta, fs$betas, stone_w, wt,
                            subgroups = subgroups[c("low_income","non_low_income","elderly","non_elderly","large_family","small_family")])
save_el(elz$all, "az_v2")
subz <- rbindlist(lapply(names(elz$sub), function(nm) {
  s <- elz$sub[[nm]]
  data.table(subgroup = nm, food_group10 = GROUPS9, expenditure = s$exp,
             own_price = diag(s$mar), curvature_ok = s$curvature_ok, n = s$n)
}))
fwrite(subz, file.path(odir, "subgroup_elasticities_az_v2.csv"), bom = TRUE)
fwrite(data.table(term = laz$term_names, estimate = fitz$beta, se_cluster_household = sqrt(diag(Vz))),
       file.path(odir, "system_coefficients_az_v2.csv"), bom = TRUE)

message("[32] Numeraire invariance check (omit G05) ...")
wide2 <- copy(wide)
wide2 <- derive_vars(wide2, stone_w, omit = "G05")
eq5 <- setdiff(CODES9, "G05")
for (rc in paste0("r_", eq5)) wide2[, paste0("mn_", rc) := mean(get(rc)), by = ID]
fs5 <- fit_probits(wide2, wt, omit = "G05")
pp5 <- predict_probits(wide2, fs5$betas, omit = "G05")
lay5 <- system_layout(omit = "G05", az = FALSE, quaids = FALSE)
fit5 <- fit_system(wide2, lay5, pp5$Phi, pp5$phi, wt, Sigma = NULL, n_fgls = 2)
el5 <- compute_elasticities(wide2, lay5, fit5$beta, fs5$betas, stone_w, wt)
inv_chk <- data.table(matrix_1 = "omit_G03", matrix_2 = "omit_G05",
                      max_abs_diff_marshallian = max(abs(el$all$mar - el5$all$mar)),
                      max_abs_diff_expenditure = max(abs(el$all$exp - el5$all$exp)),
                      corr_marshallian = cor(as.numeric(el$all$mar), as.numeric(el5$all$mar)))
print(inv_chk)
fwrite(inv_chk, file.path(rdir, "numeraire_invariance_check_v2.csv"), bom = TRUE)
rm(wide2); gc(FALSE)

message("[32] Out-of-fold fit (5-fold household CV) ...")
oof <- rbindlist(lapply(1:5, function(k) {
  wtr <- as.numeric(wide$fold != k)
  sw_k <- compute_stone_weights(wide, wtr)
  # training-fold estimates
  fsk <- fit_probits(wide, wtr, omit = "G03", beta0_list = fs$betas)
  ppk <- predict_probits(wide, fsk$betas, omit = "G03")
  fitk <- fit_system(wide, lay, ppk$Phi, ppk$phi, wtr, Sigma = fit$Sigma)
  predk <- predict_shares(wide, lay, fitk$beta, fsk$betas, sw_k)
  te <- wide$fold == k
  W <- as.matrix(wide[te, paste0("w_", CODES9), with = FALSE])
  Pk <- predk[te, ]
  rbindlist(lapply(seq_along(CODES9), function(g) {
    ssr <- sum((W[, g] - Pk[, g])^2); sst <- sum((W[, g] - mean(W[, g]))^2)
    data.table(fold = k, food_group10 = GROUPS9[g], oof_r2 = 1 - ssr / sst,
               oof_rmse = sqrt(mean((W[, g] - Pk[, g])^2)))
  }))
}))
fwrite(oof, file.path(odir, "out_of_fold_fit_v2.csv"), bom = TRUE)
print(oof[, .(oof_r2 = mean(oof_r2), oof_rmse = mean(oof_rmse)), by = food_group10])

saveRDS(list(lay = lay, beta = fit$beta, Sigma = fit$Sigma, probit_betas = fs$betas,
             stone_w = stone_w, elasticities = el, elasticities_quaids = elq$all,
             lay_az = laz, beta_az = fitz$beta, Sigma_az = fitz$Sigma,
             V_hh = V_hh, V_pr = V_pr, subgroups_def = names(subgroups)),
        file.path(odir, "main_fit_v2.rds"))
message("[32] Done.")
