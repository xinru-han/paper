#!/usr/bin/env Rscript
# ============================================================================
# v2 step 36: curvature-constrained main estimation.
# Refits the main SY-EASI system and imposes negative semidefiniteness on the
# symmetric price coefficient matrix via B = -LL' (concentrated FGLS + BFGS,
# see impose_curvature in 31_lib_v2.R). Outputs constrained coefficients,
# elasticities, and the curvature grid re-evaluated at the aggregate point and
# all subgroups. Inference for the constrained estimator comes from the pairs
# cluster bootstrap (script 34 with CURV=1).
# ============================================================================

suppressPackageStartupMessages({ library(data.table) })
base <- "/root/data/Paper/央视数据/Paper1-EASI/model_v2_R"
source(file.path(base, "src", "31_lib_v2.R"))
odir <- file.path(base, "outputs", "demand")
rdir <- file.path(base, "outputs", "regularity")
SMOKE <- nzchar(Sys.getenv("SMOKE_V2"))

message("[36] Loading panel ...")
panel <- fread(file.path(base, "data_derived", "household_month_group9_v2.csv"), encoding = "UTF-8")
wide <- make_wide(panel, price_col = "lp_ext")
rm(panel); gc(FALSE)
if (SMOKE) {
  set.seed(1)
  wide <- wide[ID %in% sample(unique(wide$ID), 3000)]
}

wt <- rep(1, nrow(wide))
stone_w <- compute_stone_weights(wide, wt)
wide <- derive_vars(wide, stone_w, omit = "G03")
wide <- add_mundlak(wide, omit = "G03")

message("[36] First stage probits ...")
fs <- fit_probits(wide, wt, omit = "G03")
pp <- predict_probits(wide, fs$betas, omit = "G03")

message("[36] Unconstrained FGLS (keeping normal equations) ...")
lay <- system_layout(omit = "G03", az = FALSE, y2p = FALSE)
fit <- fit_system(wide, lay, pp$Phi, pp$phi, wt, Sigma = NULL, n_fgls = 2, keep_xtx_inv = TRUE)

message("[36] Imposing curvature: B + yC NSD at 1%/99% quantiles of y ...")
yq <- quantile(wide$y_easi, c(0.01, 0.99))
cv <- impose_curvature(fit, lay, y_lo = yq[1], y_hi = yq[2])
message("    converged: ", cv$converged,
        " | criterion gap: ", format(cv$criterion_gap, digits = 4),
        " | y range [", round(yq[1], 2), ", ", round(yq[2], 2), "]")
message("    eigenvalues of B + y_lo C and B + y_hi C:")
print(round(cv$M_lo_eigen, 4)); print(round(cv$M_hi_eigen, 4))

message("[36] Elasticities under constrained estimates ...")
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
el <- compute_elasticities(wide, lay, cv$beta, fs$betas, stone_w, wt, subgroups = subgroups)

fwrite(data.table(food_group10 = GROUPS9, expenditure_elasticity = el$all$exp),
       file.path(odir, "expenditure_elasticity_curv_v2.csv"), bom = TRUE)
fwrite(data.table(demand_group = GROUPS9, el$all$mar),
       file.path(odir, "marshallian_curv_v2.csv"), bom = TRUE)
fwrite(data.table(demand_group = GROUPS9, el$all$hick),
       file.path(odir, "hicksian_curv_v2.csv"), bom = TRUE)

own_dt <- data.table(food_group10 = GROUPS9, own_price = diag(el$all$mar), negative = diag(el$all$mar) < 0)
print(own_dt)
message("Curvature (aggregate, constrained): ", el$all$curvature_ok)
print(round(el$all$eigenvalues, 4))

curv_rows <- list(cbind(point = "aggregate", data.table(t(el$all$eigenvalues)),
                        curvature_ok = el$all$curvature_ok, n = el$all$n))
for (nm in names(el$sub)) {
  s <- el$sub[[nm]]
  curv_rows[[length(curv_rows)+1]] <- cbind(point = nm, data.table(t(s$eigenvalues)),
                                            curvature_ok = s$curvature_ok, n = s$n)
}
curv <- rbindlist(curv_rows)
setnames(curv, paste0("V", 1:9), paste0("eig", 1:9))
fwrite(curv, file.path(rdir, "curvature_eigenvalues_grid_curv_v2.csv"), bom = TRUE)

sub_rows <- rbindlist(lapply(names(el$sub), function(nm) {
  s <- el$sub[[nm]]
  data.table(subgroup = nm, food_group10 = GROUPS9, expenditure = s$exp,
             own_price = diag(s$mar), curvature_ok = s$curvature_ok, n = s$n)
}))
fwrite(sub_rows, file.path(odir, "subgroup_elasticities_curv_v2.csv"), bom = TRUE)

# unconstrained vs constrained comparison
main_unc <- readRDS(file.path(odir, "main_fit_v2.rds"))
cmp <- data.table(food_group10 = GROUPS9,
                  exp_unconstrained = main_unc$elasticities$all$exp,
                  exp_constrained = el$all$exp,
                  own_unconstrained = diag(main_unc$elasticities$all$mar),
                  own_constrained = diag(el$all$mar))
fwrite(cmp, file.path(rdir, "constrained_vs_unconstrained_v2.csv"), bom = TRUE)
print(cmp)

fwrite(data.table(term = lay$term_names, estimate_unconstrained = fit$beta,
                  estimate_constrained = cv$beta),
       file.path(odir, "system_coefficients_curv_v2.csv"), bom = TRUE)

saveRDS(list(lay = lay, beta = cv$beta, beta_unconstrained = fit$beta,
             Sigma = fit$Sigma, probit_betas = fs$betas, stone_w = stone_w,
             elasticities = el, B_constrained = cv$B, L = cv$L,
             criterion_gap = cv$criterion_gap),
        file.path(odir, "main_fit_curv_v2.rds"))
message("[36] Done.")
