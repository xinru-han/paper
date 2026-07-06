#!/usr/bin/env Rscript
# 23_finalize_demand_diagnostics.R
# 目的：在不重估的前提下，复用 src/22 已保存的受约束系数，对
#   (1) SY-EASI 与 (2) SY-QUAIDS 两个主模型分别计算月度弹性；
#   (3) 补齐方案要求但此前缺失的“曲率/负定性诊断”（Slutsky 替代矩阵特征值）；
#   (4) 明确标注被省略的第 10 组（坚果）为残差组、其弹性不可直接解释。
# 输入：央视数据/data_derived/household_month_group10_r.csv
#       央视数据/outputs/demand/selection_cre_probit_predictions_r.csv
#       央视数据/outputs/demand/constrained_high_frequency_models_fast_r.rds
# 输出：央视数据/final_demand_model_R/outputs/*

suppressPackageStartupMessages({ library(data.table) })

base <- "/root/data/Paper/央视数据/Paper1-EASI/repro_run"
outdir <- file.path(base, "final_demand_model_R", "outputs")
dir.create(outdir, recursive = TRUE, showWarnings = FALSE)

codes <- sprintf("G%02d", 1:10)
groups <- c("G01_主食","G02_食用油","G03_蔬菜","G04_水果","G05_猪肉",
            "G06_禽类及其他肉类","G07_牛羊肉","G08_海鲜","G09_乳制品","G10_坚果")
names(groups) <- codes
eq_codes <- codes[1:9]
omitted_code <- codes[10]
h <- 0.01

models <- readRDS(file.path(base, "outputs", "demand", "constrained_high_frequency_models_fast_r.rds"))
term_names <- models$term_names

message("Reading panel and casting wide...")
panel <- fread(file.path(base, "data_derived", "household_month_group10_r.csv"), encoding = "UTF-8", showProgress = TRUE)
panel <- panel[is.finite(latent_log_price) & is.finite(budget_share) & total_food_spend_month > 0]
panel[, group_code := substr(food_group10, 1, 3)]
panel[, covid_log := log1p(covid_daily_new_sum)]
panel[, precip_log := log1p(pmax(precipitation_mm_sum, 0))]

id_cols <- c("ID","year_month","Province","Family_Type","Family_Size","Family_Income",
             "family_size_midpoint","total_food_spend_month","total_food_spend_pc_month",
             "log_total_food_spend_pc_month","fold","low_income","elderly_household","large_family",
             "cpi_yoy_prev_year_100","covid_log","holiday_days","temp_avg_c_mean","precip_log","wholesale_agri_200_mean")
base_wide <- unique(panel[, ..id_cols], by = c("ID","year_month"))
cast_one <- function(value_col, prefix) {
  x <- dcast(panel, ID + year_month ~ group_code, value.var = value_col)
  setnames(x, codes, paste0(prefix, "_", codes), skip_absent = TRUE)
  x
}
wide <- Reduce(function(a, b) merge(a, b, by = c("ID","year_month"), all.x = TRUE),
               list(base_wide, cast_one("budget_share","w"), cast_one("positive_purchase","pos"), cast_one("latent_log_price","lp")))
setorder(wide, ID, year_month)
share_cols <- paste0("w_", codes); pos_cols <- paste0("pos_", codes); lp_cols <- paste0("lp_", codes)
for (v in c(share_cols, pos_cols)) wide[is.na(get(v)), (v) := 0]
wide <- wide[rowSums(!is.finite(as.matrix(wide[, ..lp_cols]))) == 0]
wide[, stone_price := rowSums(as.matrix(.SD) * as.matrix(wide[, ..lp_cols])), .SDcols = share_cols]
wide[, y_easi := log_total_food_spend_pc_month - stone_price]
wide[, y_easi2 := y_easi^2]
for (code in eq_codes) wide[, paste0("r_", code) := get(paste0("lp_", code)) - get(paste0("lp_", omitted_code))]
r_cols <- paste0("r_", eq_codes)
scale_cols <- c("cpi_yoy_prev_year_100","covid_log","holiday_days","temp_avg_c_mean","precip_log","wholesale_agri_200_mean")
for (v in scale_cols) {
  m <- mean(wide[[v]], na.rm = TRUE); s <- sd(wide[[v]], na.rm = TRUE)
  if (!is.finite(s) || s == 0) s <- 1
  wide[, paste0("z_", v) := (get(v) - m) / s]
}
z_cols <- paste0("z_", scale_cols)
demo_cols <- c("low_income","elderly_household","large_family", z_cols)

pred <- fread(file.path(base, "outputs", "demand", "selection_cre_probit_predictions_r.csv"))
wide <- merge(wide, pred, by = c("ID","year_month"), all.x = TRUE)

# ---- design indexing identical to src/22 ----
base_terms <- c("const","y_easi","y_easi2", demo_cols)
upper_pairs <- which(upper.tri(matrix(0,9,9), diag = TRUE), arr.ind = TRUE)
idx_base <- matrix(seq_len(length(eq_codes)*length(base_terms)), nrow = length(eq_codes), byrow = TRUE)
offset_price <- length(eq_codes)*length(base_terms)
offset_yp <- offset_price + nrow(upper_pairs)
offset_sigma <- offset_yp + nrow(upper_pairs)
pair_index <- matrix(NA_integer_, 9, 9)
for (k in seq_len(nrow(upper_pairs))) { a<-upper_pairs[k,1]; b<-upper_pairs[k,2]; pair_index[a,b]<-k; pair_index[b,a]<-k }

build_active <- function(dt, g, quaids = FALSE) {
  code <- eq_codes[g]
  mult <- dt[[paste0("Phi_", code)]]
  base_mat <- cbind(const=1, y_easi=dt$y_easi, y_easi2=dt$y_easi2, as.matrix(dt[, ..demo_cols]))
  rmat <- as.matrix(dt[, ..r_cols])
  ym <- if (quaids) dt$y_easi2 else dt$y_easi
  A <- cbind(mult*base_mat, mult*rmat, mult*(ym*rmat), dt[[paste0("phi_", code)]])
  cols <- c(idx_base[g,], offset_price + pair_index[g, seq_len(9)], offset_yp + pair_index[g, seq_len(9)], offset_sigma + g)
  list(A=A, cols=cols)
}
predict_cp <- function(dt, b, quaids = FALSE) {
  pr <- matrix(0, nrow(dt), 10); colnames(pr) <- codes
  for (g in seq_along(eq_codes)) { z <- build_active(dt,g,quaids); pr[,g] <- as.numeric(z$A %*% b[z$cols]) }
  pr[,10] <- 1 - rowSums(pr[,1:9,drop=FALSE]); pr[pr<1e-8] <- 1e-8; pr/rowSums(pr)
}
quantity_matrix <- function(dt, shares) { prices <- exp(as.matrix(dt[, ..lp_cols])); shares*dt$total_food_spend_pc_month/prices }
refresh <- function(out) {
  out[, stone_price := rowSums(as.matrix(.SD)*as.matrix(out[, ..lp_cols])), .SDcols=share_cols]
  out[, y_easi := log_total_food_spend_pc_month - stone_price]; out[, y_easi2 := y_easi^2]
  for (cc in eq_codes) out[, paste0("r_", cc) := get(paste0("lp_", cc)) - get(paste0("lp_", omitted_code))]; out
}
agg_elas <- function(q0,q1) ((colMeans(q1)-colMeans(q0))/colMeans(q0))/h

avg_share <- colMeans(as.matrix(wide[, ..share_cols]))

compute_set <- function(b, quaids, tag) {
  message("Computing elasticities for ", tag, " ...")
  base_sh <- predict_cp(wide, b, quaids)
  q0 <- quantity_matrix(wide, base_sh)
  we <- copy(wide); we[, total_food_spend_pc_month := total_food_spend_pc_month*(1+h)]
  we[, log_total_food_spend_pc_month := log(total_food_spend_pc_month)]; we <- refresh(we)
  q_exp <- quantity_matrix(we, predict_cp(we, b, quaids)); exp_vec <- agg_elas(q0, q_exp)
  mar <- matrix(NA_real_, 10, 10, dimnames = list(groups, groups))
  for (code in codes) {
    wp <- copy(wide); wp[[paste0("lp_",code)]] <- wp[[paste0("lp_",code)]] + log(1+h); wp <- refresh(wp)
    qp <- quantity_matrix(wp, predict_cp(wp, b, quaids)); mar[, groups[[code]]] <- agg_elas(q0, qp)
  }
  hick <- mar + exp_vec %o% avg_share
  # 曲率/负定性诊断：份额加权 Slutsky 替代矩阵 S_ij = w_i * e^h_ij，对称化后求特征值
  S <- diag(avg_share) %*% hick
  Ssym <- (S + t(S)) / 2
  ev <- sort(eigen(Ssym, symmetric = TRUE, only.values = TRUE)$values, decreasing = TRUE)
  list(exp_vec=exp_vec, mar=mar, hick=hick, eig=ev,
       own=data.table(food_group10=groups, own_price_elasticity=diag(mar),
                      is_negative=diag(mar)<0,
                      is_omitted_residual_group = codes==omitted_code))
}

res_easi <- compute_set(models$sy_easi, FALSE, "SY-EASI")
res_quaids <- compute_set(models$sy_quaids, TRUE, "SY-QUAIDS")

write_set <- function(res, suf) {
  fwrite(data.table(food_group10=groups, food_expenditure_elasticity=as.numeric(res$exp_vec)),
         file.path(outdir, paste0("food_expenditure_elasticity_", suf, ".csv")), bom=TRUE)
  fwrite(data.table(demand_group=rownames(res$mar), res$mar),
         file.path(outdir, paste0("marshallian_elasticity_", suf, ".csv")), bom=TRUE)
  fwrite(data.table(demand_group=rownames(res$hick), res$hick),
         file.path(outdir, paste0("hicksian_elasticity_", suf, ".csv")), bom=TRUE)
  fwrite(res$own, file.path(outdir, paste0("own_price_sign_", suf, ".csv")), bom=TRUE)
}
write_set(res_easi, "sy_easi")
write_set(res_quaids, "sy_quaids")

# 曲率诊断汇总（含/不含残差组）
curv <- function(res, tag) {
  ev <- res$eig
  data.table(model=tag,
             n_nonpositive_eig = sum(ev <= 1e-8),
             max_eig = max(ev), min_eig = min(ev),
             negative_semidefinite_full = all(ev <= 1e-8),
             eigenvalues = paste(sprintf("%.4f", ev), collapse="; "))
}
curv_dt <- rbindlist(list(curv(res_easi, "constrained_sy_easi"), curv(res_quaids, "constrained_sy_quaids")))
fwrite(curv_dt, file.path(outdir, "curvature_negativity_diagnostics.csv"), bom=TRUE)

# 自价格符号汇总（两模型并排，标注残差组）
sign_cmp <- data.table(food_group10=groups,
                       sy_easi_own = diag(res_easi$mar),
                       sy_quaids_own = diag(res_quaids$mar),
                       omitted_residual_group = codes==omitted_code,
                       sy_easi_negative = diag(res_easi$mar)<0,
                       sy_quaids_negative = diag(res_quaids$mar)<0)
fwrite(sign_cmp, file.path(outdir, "own_price_sign_comparison.csv"), bom=TRUE)

saveRDS(list(easi=res_easi, quaids=res_quaids, avg_share=avg_share,
             n_hh_months=nrow(wide), n_households=uniqueN(wide$ID)),
        file.path(outdir, "finalize_diagnostics.rds"))
fwrite(data.table(metric=c("n_household_months","n_households","year_month_min","year_month_max"),
                  value=c(nrow(wide), uniqueN(wide$ID), min(wide$year_month), max(wide$year_month))),
       file.path(outdir, "sample_summary.csv"), bom=TRUE)
message("Done. Outputs in ", outdir)
