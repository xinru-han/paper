#!/usr/bin/env Rscript
suppressPackageStartupMessages({ library(data.table); library(jsonlite) })
script_path <- tryCatch(normalizePath(sys.frame(1)$ofile), error=function(e) file.path(getwd(), "src", "22_estimate_high_frequency_demand_fast_R.R"))
base <- normalizePath(file.path(dirname(script_path), ".."), mustWork=TRUE)
dir.create(file.path(base, "outputs", "demand"), recursive=TRUE, showWarnings=FALSE)
dir.create(file.path(base, "outputs", "regularity"), recursive=TRUE, showWarnings=FALSE)

codes <- sprintf("G%02d", 1:10)
groups <- c("G01_主食","G02_食用油","G03_蔬菜","G04_水果","G05_猪肉","G06_禽类及其他肉类","G07_牛羊肉","G08_海鲜","G09_乳制品","G10_坚果")
names(groups) <- codes
eq_codes <- codes[1:9]
omitted_code <- codes[10]
h <- 0.01

message("Reading panel and casting wide...")
panel <- fread(file.path(base, "data_derived", "household_month_group10_r.csv"), encoding="UTF-8", showProgress=TRUE)
panel <- panel[is.finite(latent_log_price) & is.finite(budget_share) & total_food_spend_month > 0]
panel[, group_code := substr(food_group10, 1, 3)]
panel[, year := substr(year_month, 1, 4)]
panel[, month := substr(year_month, 6, 7)]
panel[, covid_log := log1p(covid_daily_new_sum)]
panel[, precip_log := log1p(pmax(precipitation_mm_sum, 0))]

id_cols <- c("ID","year_month","year","month","Province","Family_Type","Family_Size","Family_Income",
             "family_size_midpoint","total_food_spend_month","total_food_spend_pc_month",
             "log_total_food_spend_pc_month","fold","low_income","elderly_household","large_family",
             "cpi_yoy_prev_year_100","covid_log","holiday_days","temp_avg_c_mean","precip_log","wholesale_agri_200_mean")
base_wide <- unique(panel[, ..id_cols], by=c("ID","year_month"))
cast_one <- function(value_col, prefix) {
  x <- dcast(panel, ID + year_month ~ group_code, value.var=value_col)
  setnames(x, codes, paste0(prefix, "_", codes), skip_absent=TRUE)
  x
}
wide <- Reduce(function(a,b) merge(a,b,by=c("ID","year_month"),all.x=TRUE),
               list(base_wide, cast_one("budget_share","w"), cast_one("positive_purchase","pos"), cast_one("latent_log_price","lp")))
setorder(wide, ID, year_month)
share_cols <- paste0("w_", codes); pos_cols <- paste0("pos_", codes); lp_cols <- paste0("lp_", codes)
for (v in c(share_cols,pos_cols)) wide[is.na(get(v)), (v) := 0]
wide <- wide[rowSums(!is.finite(as.matrix(wide[, ..lp_cols]))) == 0]
wide[, stone_price := rowSums(as.matrix(.SD) * as.matrix(wide[, ..lp_cols])), .SDcols=share_cols]
wide[, y_easi := log_total_food_spend_pc_month - stone_price]
wide[, y_easi2 := y_easi^2]
for (code in eq_codes) wide[, paste0("r_", code) := get(paste0("lp_", code)) - get(paste0("lp_", omitted_code))]
r_cols <- paste0("r_", eq_codes)
scale_cols <- c("cpi_yoy_prev_year_100","covid_log","holiday_days","temp_avg_c_mean","precip_log","wholesale_agri_200_mean")
for (v in scale_cols) {
  m <- mean(wide[[v]], na.rm=TRUE); s <- sd(wide[[v]], na.rm=TRUE)
  if (!is.finite(s) || s == 0) s <- 1
  wide[, paste0("z_", v) := (get(v)-m)/s]
}
z_cols <- paste0("z_", scale_cols)
demo_cols <- c("low_income","elderly_household","large_family", z_cols)

pred_path <- file.path(base, "outputs", "demand", "selection_cre_probit_predictions_r.csv")
if (!file.exists(pred_path)) stop("Missing selection predictions. Run src/21_estimate_high_frequency_demand_R.R until first stage completes.")
first_pred <- fread(pred_path)
wide <- merge(wide, first_pred, by=c("ID","year_month"), all.x=TRUE)

base_terms <- c("const","y_easi","y_easi2", demo_cols)
upper_pairs <- which(upper.tri(matrix(0,9,9), diag=TRUE), arr.ind=TRUE)
pair_names <- paste0("p_", upper_pairs[,1], "_", upper_pairs[,2])
term_names <- c(as.vector(outer(eq_codes, base_terms, paste, sep="__")),
                paste0("sym_price__", pair_names), paste0("sym_y_price__", pair_names), paste0("sigma__", eq_codes))
idx_base <- matrix(seq_len(length(eq_codes)*length(base_terms)), nrow=length(eq_codes), byrow=TRUE)
offset_price <- length(eq_codes)*length(base_terms)
offset_yp <- offset_price + nrow(upper_pairs)
offset_sigma <- offset_yp + nrow(upper_pairs)
pair_index <- matrix(NA_integer_,9,9)
for (k in seq_len(nrow(upper_pairs))) {
  a <- upper_pairs[k,1]; b <- upper_pairs[k,2]
  pair_index[a,b] <- k; pair_index[b,a] <- k
}

build_active <- function(dt, g, quaids=FALSE) {
  code <- eq_codes[g]
  mult <- dt[[paste0("Phi_", code)]]
  base_mat <- cbind(const=1, y_easi=dt$y_easi, y_easi2=dt$y_easi2, as.matrix(dt[, ..demo_cols]))
  rmat <- as.matrix(dt[, ..r_cols])
  ym <- if (quaids) dt$y_easi2 else dt$y_easi
  A <- cbind(mult*base_mat, mult*rmat, mult*(ym*rmat), dt[[paste0("phi_", code)]])
  cols <- c(idx_base[g,], offset_price + pair_index[g, seq_len(9)], offset_yp + pair_index[g, seq_len(9)], offset_sigma + g)
  list(A=A, cols=cols, y=dt[[paste0("w_", code)]])
}
fit_cp <- function(dt, quaids=FALSE, ridge=1e-8) {
  p <- length(term_names); xtx <- matrix(0, p, p); xty <- numeric(p)
  for (g in seq_along(eq_codes)) {
    z <- build_active(dt,g,quaids)
    xtx[z$cols,z$cols] <- xtx[z$cols,z$cols] + crossprod(z$A)
    xty[z$cols] <- xty[z$cols] + as.numeric(crossprod(z$A,z$y))
  }
  diag(xtx) <- diag(xtx) + ridge
  b <- as.numeric(solve(xtx, xty)); names(b) <- term_names; b
}
predict_cp <- function(dt, b, quaids=FALSE) {
  pred <- matrix(0, nrow(dt), 10); colnames(pred) <- codes
  for (g in seq_along(eq_codes)) {
    z <- build_active(dt,g,quaids)
    pred[,g] <- as.numeric(z$A %*% b[z$cols])
  }
  pred[,10] <- 1 - rowSums(pred[,1:9,drop=FALSE])
  pred[pred < 1e-8] <- 1e-8
  pred / rowSums(pred)
}

message("Estimating fast constrained SY-EASI...")
b_sy <- fit_cp(wide, quaids=FALSE)
message("Estimating fast constrained SY-QUAIDS...")
b_q <- fit_cp(wide, quaids=TRUE)
saveRDS(list(sy_easi=b_sy, sy_quaids=b_q, term_names=term_names, eq_codes=eq_codes, codes=codes, groups=groups),
        file.path(base, "outputs", "demand", "constrained_high_frequency_models_fast_r.rds"))
fwrite(rbindlist(list(
  data.table(model="constrained_sy_easi_fast", term=names(b_sy), estimate=b_sy),
  data.table(model="constrained_sy_quaids_fast", term=names(b_q), estimate=b_q)
)), file.path(base, "outputs", "demand", "constrained_model_coefficients_fast_r.csv"), bom=TRUE)

message("Computing elasticities...")
base_sh <- predict_cp(wide, b_sy, quaids=FALSE)
quantity_matrix <- function(dt, shares) {
  prices <- exp(as.matrix(dt[, ..lp_cols])); shares * dt$total_food_spend_pc_month / prices
}
refresh <- function(out) {
  out[, stone_price := rowSums(as.matrix(.SD)*as.matrix(out[, ..lp_cols])), .SDcols=share_cols]
  out[, y_easi := log_total_food_spend_pc_month - stone_price]
  out[, y_easi2 := y_easi^2]
  for (cc in eq_codes) out[, paste0("r_", cc) := get(paste0("lp_", cc)) - get(paste0("lp_", omitted_code))]
  out
}
q0 <- quantity_matrix(wide, base_sh)
we <- copy(wide); we[, total_food_spend_pc_month := total_food_spend_pc_month*(1+h)]
we[, log_total_food_spend_pc_month := log(total_food_spend_pc_month)]; we <- refresh(we)
q_exp <- quantity_matrix(we, predict_cp(we,b_sy,FALSE))
agg_elas <- function(q0,q1,idx) ((colMeans(q1[idx,,drop=FALSE])-colMeans(q0[idx,,drop=FALSE]))/colMeans(q0[idx,,drop=FALSE]))/h
all_idx <- rep(TRUE,nrow(wide)); exp_vec <- agg_elas(q0,q_exp,all_idx)
mar <- matrix(NA_real_,10,10,dimnames=list(groups,groups)); price_q <- list()
for (code in codes) {
  wp <- copy(wide); wp[[paste0("lp_",code)]] <- wp[[paste0("lp_",code)]] + log(1+h); wp <- refresh(wp)
  qp <- quantity_matrix(wp, predict_cp(wp,b_sy,FALSE)); price_q[[code]] <- qp
  mar[,groups[[code]]] <- agg_elas(q0,qp,all_idx)
}
avg_share <- colMeans(as.matrix(wide[, ..share_cols])); hick <- mar + exp_vec %o% avg_share
fwrite(data.table(food_group10=groups, food_expenditure_elasticity=as.numeric(exp_vec)), file.path(base, "outputs", "demand", "food_expenditure_elasticity_monthly_fast_r.csv"), bom=TRUE)
fwrite(data.table(demand_group=rownames(mar), mar), file.path(base, "outputs", "demand", "marshallian_elasticity_monthly_fast_r.csv"), bom=TRUE)
fwrite(data.table(demand_group=rownames(hick), hick), file.path(base, "outputs", "demand", "hicksian_elasticity_monthly_fast_r.csv"), bom=TRUE)

hetero_rows <- list(); specs <- c(low_income="low_income", elderly_household="elderly_household", large_family="large_family")
for (hn in names(specs)) for (lev in sort(unique(wide[[specs[[hn]]]]))) {
  idx <- wide[[specs[[hn]]]] == lev
  if (sum(idx) < 100) next
  ev <- agg_elas(q0,q_exp,idx)
  for (k in seq_along(codes)) hetero_rows[[length(hetero_rows)+1]] <- data.table(heterogeneity=hn, level=lev, elasticity_type="food_expenditure", demand_group=groups[k], shock_group="food_expenditure", elasticity=ev[k], n=sum(idx))
  for (code in codes) {
    pv <- agg_elas(q0,price_q[[code]],idx)
    for (k in seq_along(codes)) hetero_rows[[length(hetero_rows)+1]] <- data.table(heterogeneity=hn, level=lev, elasticity_type="marshallian_price", demand_group=groups[k], shock_group=groups[[code]], elasticity=pv[k], n=sum(idx))
  }
}
fwrite(rbindlist(hetero_rows), file.path(base, "outputs", "demand", "elasticities_by_prespecified_heterogeneity_fast_r.csv"), bom=TRUE)

adding <- data.table(metric=c("n_household_months","max_abs_predicted_share_sum_error","mean_abs_predicted_share_sum_error","min_predicted_share","max_predicted_share"),
                     value=c(nrow(wide), max(abs(rowSums(base_sh)-1)), mean(abs(rowSums(base_sh)-1)), min(base_sh), max(base_sh)))
theory <- data.table(model="constrained_sy_easi_fast", restriction=c("adding_up","homogeneity_relative_prices","slutsky_symmetry_price_coefficients"),
                     status=c("by_construction_predicted_10th_share","by_construction_relative_prices","by_construction_symmetric_parameterization"),
                     max_abs_error=c(max(abs(rowSums(base_sh)-1)),0,0))
own <- data.table(food_group10=groups, own_price_elasticity=diag(mar), is_negative=diag(mar)<0)
fwrite(adding, file.path(base, "outputs", "regularity", "adding_up_diagnostics_fast_r.csv"), bom=TRUE)
fwrite(theory, file.path(base, "outputs", "regularity", "theory_constraint_checks_fast_r.csv"), bom=TRUE)
fwrite(own, file.path(base, "outputs", "regularity", "own_price_sign_diagnostics_fast_r.csv"), bom=TRUE)

report <- c("# R 高频月度需求模型报告（快速正规方程版）", "",
            sprintf("- 家庭-月观测：%s", format(nrow(wide), big.mark=",")),
            sprintf("- 家庭数：%s", format(uniqueN(wide$ID), big.mark=",")),
            sprintf("- 月份：%s 至 %s", min(wide$year_month), max(wide$year_month)), "",
            "## 自价格弹性", "", capture.output(print(own)), "",
            "## 约束", "", capture.output(print(theory)), "",
            "说明：该 R 版使用外部锚定、fold-excluded 内部价格信号和受约束 SY-EASI；结果解释为 monthly food-expenditure elasticity 和 measured market-price variation 下的条件需求响应。")
writeLines(report, file.path(base, "outputs", "demand", "high_frequency_demand_model_report_fast_r.md"))
message("Fast high-frequency R demand model complete.")
