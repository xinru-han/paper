# AIDS/QUAIDS（FIML + SY + Bartik IV + 质量调整价格）代码整合总览

> 本文件把 `cf_aids_quaids_r_code/` 目录下全部源码整合到一处。
> 生成时间：2026-06-14 10:50。运行环境：R 4.5.2 ，仅依赖 R base。

## 方案设计

本方案不再使用 EASI/GEASI，改用 **AIDS 与 QUAIDS**，并满足以下要求：

1. **理论约束**（由参数化直接施加，无需数值罚项）：
   - Adding-up（加总性）：$\sum_i lpha_i = 1$，$\sum_i \gamma_{ij}=0$，$\sum_i eta_i = 0$，$\sum_i \lambda_i = 0$
   - Homogeneity（齐次性）：$\sum_j \gamma_{ij}=0$
   - Symmetry（对称性）：$\gamma_{ij}=\gamma_{ji}$
2. **Shonkwiler-Yen (1999) 两步法处理零值**：第一阶段对每个品类跑 probit（只用预定/严格滞后变量，避免泄漏），得到 $\Phi_i$、$\phi_i$；需求方程的观测份额写成 $w_i = \Phi_i g_i + \psi_i \phi_i$，其中 $g_i$ 是 AIDS/QUAIDS 的系统份额。
3. **Bartik IV + adjusted price**：内生总支出用 Bartik 工具变量做第一阶段，残差 $\hat v$ 作为控制函数项进入各方程；价格使用质量调整单位价值 adjusted price。
4. **模型选择用 Bewley (1986) LRB 检验**（Hovhannisyan et al. 2014）：
   $$LR_B = 2(LL_U - LL_R)   其中 $LL_U$/$LL_R$ 为 QUAIDS（一般式，无约束）/AIDS（受约束，$\lambda_i=0$）的对数似然，$N_{EQ}$=方程数，$N_{SS}$=样本量，$N^U_P$=一般式参数个数。自由度 = $\lambda$ 自由参数个数。

## 模型设定

QUAIDS 份额方程（AIDS 为 $\lambda_i=0$ 的特例）：
$$ w_i = lpha_i + \sum_j \gamma_{ij}\ln p_j + eta_i \lnrac{X}{a(p)} + rac{\lambda_i}{b(p)}\left[\lnrac{X}{a(p)}ight]^2 + \delta_i' Z + 	heta_i \hat v $$
- translog 价格指数：$\ln a(p) = lpha_0 + \sum_k lpha_k \ln p_k + 	frac12\sum_k\sum_l \gamma_{kl}\ln p_k\ln p_l$（$lpha_0=0$ 归一化，$\ln X$ 已中心化）
- Cobb-Douglas 聚合：$\ln b(p) = \sum_k eta_k \ln p_k$
- 省略份额最大的方程（大麦），由加总性恢复其参数。

## 弹性计算与统计推断
对系统份额 $g_i$ 关于 $\ln p_j$、$\ln X$ 做数值微分，按 **Green & Alston (1990) 惯例在样本均值的观测预算份额** 上求弹性（不用 SY 校正后的潜在份额作分母——因为 SY 校正会破坏精确加总性、使省略品类潜在份额变负而导致弹性发散）：
- 支出弹性：$e_i = 1 + (\partial w_i/\partial\ln X)/ar w_i$
- Marshallian：$arepsilon_{ij} = (\partial w_i/\partial\ln p_j)/ar w_i - \delta_{ij}$
- Hicksian：$arepsilon^h_{ij} = arepsilon_{ij} + e_i ar w_j$；Morishima：$arepsilon^h_{ij}-arepsilon^h_{jj}$

**标准误与 p 值（本次新增）**：弹性是估计系数 $\hat	heta$ 的函数，用 **delta method** 计算标准误。
- 参数协方差：FIML 集中目标函数 $obj(	heta)=n\log|\hat\Sigma(	heta)|$，而 $-ll = const + 	frac12 obj$，故 $\mathrm{Hessian}(-ll)=	frac12\mathrm{Hessian}(obj)$，参数协方差 $\widehat{\mathrm{Var}}(\hat	heta)=2\,[\mathrm{Hessian}(obj)]^{-1}$（用 `optimHess` 数值求 Hessian，截断 SVD 伪逆保证数值稳定）。
- 弹性协方差：$\widehat{\mathrm{Var}}(\hat e)=J\,\widehat{\mathrm{Var}}(\hat	heta)\,J^	op$，雅可比 $J=\partial e/\partial	heta$ 用中心差分数值求；$SE=\sqrt{\mathrm{diag}}$。
- z 值 = 弹性/SE，p 值为双侧正态检验 $H_0:\,弹性=0$。支出弹性、Marshallian、Hicksian、Morishima 以及结构参数 $lpha_i,eta_i,\lambda_i$ 均输出 estimate / std_error / z / p。

## 文件目录
1. `run_aids_quaids.sh` — 运行脚本
2. `estimate_aids_quaids.R` — 主入口
3. `utils_aids_quaids.R` — 工具函数（参数化/约束、FIML+SY、Bewley LRB、弹性、**delta-method 标准误**）；复用 `utils_cf_easi_geasi.R` 的共享辅助（adjusted 价格构造、选择阶段、Bartik IV、第一阶段）

> 注：本方案的 adjusted 价格构造、选择阶段、Bartik IV 第一阶段等共享函数来自 `utils_cf_easi_geasi.R`（其完整源码见 `cf_easi_geasi_代码整合总览.md`），此处不再重复粘贴。

---

## 1. run_aids_quaids.sh

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
Rscript scripts/r/estimate_aids_quaids.R \
  --outdir output/aids_quaids_sy_bartik_adjusted \
  --price_variant adjusted \
  --iv_set nonag_bartik \
  --corrected TRUE \
  --omit_product auto \
  --maxit 2000
```

---

## 2. estimate_aids_quaids.R

```r
#!/usr/bin/env Rscript
# Main runner: FIML AIDS / QUAIDS with adding-up + homogeneity + symmetry,
# Shonkwiler-Yen zero correction, Bartik-IV control function, quality-adjusted
# prices, and Bewley (1986) LR model selection between AIDS and QUAIDS.

parse_args <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  defaults <- list(
    panel_long = "output/model_no_ddgs/feed_demand_model_panel_quarterly_2017_2023_no_ddgs.csv",
    panel_wide = "output/model_no_ddgs/feed_demand_model_wide_quarterly_2017_2023_no_ddgs.csv",
    external_iv = "data/external/province_quarter_iv_candidates.csv",
    fallback_iv = "output/external/province_quarter_nonag_import_iv_2017_2023.csv",
    outdir = "output/aids_quaids_sy_bartik_adjusted",
    price_variant = "adjusted",
    iv_set = "nonag_bartik",
    corrected = "TRUE",
    omit_product = "auto",
    maxit = "2000",
    alpha = "0.05"
  )
  if (length(args) > 0) {
    i <- 1
    while (i <= length(args)) {
      key <- sub("^--", "", args[[i]])
      if (key %in% names(defaults) && i + 1 <= length(args)) { defaults[[key]] <- args[[i + 1]]; i <- i + 2 }
      else i <- i + 1
    }
  }
  defaults$corrected <- toupper(defaults$corrected) %in% c("TRUE", "T", "1", "YES")
  defaults$maxit <- as.integer(defaults$maxit)
  defaults$alpha <- as.numeric(defaults$alpha)
  defaults
}

main <- function() {
  args <- parse_args()
  util_path <- if (file.exists(file.path("scripts", "r", "utils_aids_quaids.R"))) {
    file.path("scripts", "r", "utils_aids_quaids.R")
  } else "utils_aids_quaids.R"
  source(util_path)

  dir.create(args$outdir, recursive = TRUE, showWarnings = FALSE)
  long_df <- read.csv(args$panel_long, check.names = FALSE)
  wide_df <- read.csv(args$panel_wide, check.names = FALSE)

  iv <- prepare_external_iv(wide_df, args$external_iv, args$fallback_iv)
  wide_df <- iv$wide
  writeLines(c("# IV merge notes", "", paste0("- ", iv$notes)), file.path(args$outdir, "iv_merge_notes.md"))

  # Quality-adjusted prices (Cox-Wohlgenant / Hovhannisyan-style decomposition).
  qa_present <- all(paste0("ln_price_quality_adjusted_usd_per_kg__", PRODUCTS) %in% names(wide_df))
  if (args$price_variant == "adjusted" && !qa_present) {
    qa <- build_quality_adjusted_prices_from_long(long_df, wide_df, products = PRODUCTS, outdir = args$outdir)
    wide_df <- qa$wide
    message(sprintf("Quality-adjusted prices built: %d/%d product regressions.",
                    sum(qa$diagnostics$regression_fitted), nrow(qa$diagnostics)))
  }
  write.csv(price_variant_availability(wide_df, args$price_variant),
            file.path(args$outdir, "price_variant_availability.csv"), row.names = FALSE)

  # Selection stage (leakage-safe), used for SY correction.
  sel <- fit_selection_stage(long_df)
  write.csv(sel$diag, file.path(args$outdir, "selection_stage_diagnostics.csv"), row.names = FALSE)
  write.csv(sel$params, file.path(args$outdir, "selection_stage_params.csv"), row.names = FALSE)
  if (nrow(sel$preds) > 0) {
    sel_wide <- pivot_selection(sel$preds)
    merge_keys <- intersect(names(sel_wide), names(wide_df))
    merge_keys <- merge_keys[!grepl("^selection_", merge_keys)]
    wide_df <- merge(wide_df, sel_wide, by = merge_keys, all.x = TRUE)
  }

  demand <- wide_df[wide_df$positive_budget_flag == 1, , drop = FALSE]
  demand <- demand[complete.cases(demand$province, demand$year_quarter), , drop = FALSE]
  if (nrow(demand) == 0) stop("No positive-budget observations found.")

  variant <- args$price_variant
  if (length(available_price_variants(demand, variant)) == 0) {
    stop("Requested price variant '", variant, "' is not available in the panel.")
  }
  iv_set <- args$iv_set
  corrected <- args$corrected

  # Bartik-IV first stage for endogenous total expenditure -> control-function residual.
  base <- PRICE_VARIANT_COLS[[variant]]
  stone_weights <- sapply(PRODUCTS, function(p) mean(demand[[paste0("budget_share__", p)]], na.rm = TRUE))
  demand <- add_model_y(demand, variant, stone_weights)
  controls_df <- budget_controls_compact(demand)
  iv_cols <- build_iv_columns(demand, iv_set)
  if (length(iv_cols$names) == 0) stop("IV set '", iv_set, "' unavailable: ", iv_cols$note)
  # First stage regresses log total expenditure on controls + Bartik instrument.
  demand$ln_total_import_expenditure_usd <- if ("ln_total_import_expenditure_usd" %in% names(demand)) {
    safe_num(demand$ln_total_import_expenditure_usd)
  } else log(pmax(safe_num(demand$total_import_expenditure_usd), 1e-12))
  fs <- first_stage_iv(demand, "ln_total_import_expenditure_usd", controls_df, iv_cols$z)
  fst <- partial_f_test(demand$ln_total_import_expenditure_usd, controls_df, iv_cols$z)
  fs_diag <- data.frame(price_variant = variant, iv_set = iv_set, n_obs = nrow(demand),
                        n_instruments = fst$n_instruments, partial_F_classical = fst$partial_F_classical,
                        first_stage_pass_10 = is.finite(fst$partial_F_classical) && fst$partial_F_classical >= 10,
                        stringsAsFactors = FALSE)
  write.csv(fs_diag, file.path(args$outdir, "expenditure_first_stage_diagnostics.csv"), row.names = FALSE)

  # Build system data and estimate AIDS then QUAIDS (QUAIDS warm-started from AIDS).
  sys <- make_aq_data(demand, variant, omitted = args$omit_product, corrected = corrected,
                      include_controls = TRUE, include_cf = TRUE, vhat = fs$vhat)
  message("Estimating AIDS ...")
  fit_aids <- fit_aids_quaids(sys, family = "AIDS", maxit = args$maxit)
  message("Estimating QUAIDS ...")
  start_q <- pack_initial_aq(sys, quaids = TRUE)
  common <- min(length(fit_aids$par), length(start_q))   # NOTE: differs because lambda inserted; warm-start alpha/gamma/beta only
  # Map AIDS params (alpha,gamma,beta) into the QUAIDS start (which inserts lambda after beta).
  m <- sys$m; n_ag <- m + m * (m + 1L) / 2L + m
  start_q[seq_len(n_ag)] <- fit_aids$par[seq_len(n_ag)]
  fit_quaids <- fit_aids_quaids(sys, family = "QUAIDS", start = start_q, maxit = args$maxit)

  # Bewley LR model selection.
  bewley <- bewley_lr_test(fit_aids, fit_quaids)
  bewley$price_variant <- variant; bewley$iv_set <- iv_set; bewley$corrected <- corrected
  write.csv(bewley, file.path(args$outdir, "bewley_model_selection.csv"), row.names = FALSE)
  selected_family <- bewley$selected[1]

  # Fit summary.
  fit_rows <- do.call(rbind, lapply(list(fit_aids, fit_quaids), function(f) data.frame(
    family = f$family, price_variant = variant, iv_set = iv_set, corrected = corrected,
    logLik = f$logLik, npar = f$npar, neq = f$neq, nobs = f$nobs, convergence = f$convergence,
    omitted_product = f$sys$omitted, stringsAsFactors = FALSE)))
  fit_rows$selected <- fit_rows$family == selected_family
  write.csv(fit_rows, file.path(args$outdir, "demand_fiml_fit_summary.csv"), row.names = FALSE)

  # Elasticities, regularities, parameters for both models.
  exp_rows <- list(); price_rows <- list(); mor_rows <- list(); reg_rows <- list(); par_rows <- list()
  for (f in list(fit_aids, fit_quaids)) {
    el <- elasticity_tables_aq(f, variant, iv_set, corrected)
    exp_rows[[length(exp_rows) + 1]] <- el$expenditure
    price_rows[[length(price_rows) + 1]] <- el$price
    mor_rows[[length(mor_rows) + 1]] <- el$morishima
    reg_rows[[length(reg_rows) + 1]] <- regularity_check_aq(f, variant, iv_set, corrected)
    par_rows[[length(par_rows) + 1]] <- aq_param_table(f, variant, iv_set, corrected)
  }
  write.csv(do.call(rbind, exp_rows), file.path(args$outdir, "fiml_expenditure_elasticities.csv"), row.names = FALSE)
  write.csv(do.call(rbind, price_rows), file.path(args$outdir, "fiml_price_elasticities_long.csv"), row.names = FALSE)
  write.csv(do.call(rbind, mor_rows), file.path(args$outdir, "fiml_morishima_elasticities_long.csv"), row.names = FALSE)
  write.csv(do.call(rbind, reg_rows), file.path(args$outdir, "fiml_theory_regularities.csv"), row.names = FALSE)
  write.csv(do.call(rbind, par_rows), file.path(args$outdir, "demand_parameters.csv"), row.names = FALSE)

  report <- c(
    "# FIML AIDS/QUAIDS model-selection report",
    "",
    paste0("- Sample: ", nrow(demand), " positive-budget province-quarter observations."),
    paste0("- Products: ", paste(PRODUCTS, collapse = ", ")),
    paste0("- Price variant: ", variant, " (quality-adjusted unit value)"),
    paste0("- Instrument: ", iv_set, " (Bartik), partial-F = ", round(fst$partial_F_classical, 2)),
    paste0("- Shonkwiler-Yen zero correction: ", corrected),
    paste0("- Omitted equation (recovered by adding-up): ", sys$omitted),
    "",
    "## Restrictions imposed by parameterization",
    "- Adding-up: sum_i alpha_i = 1; sum_i gamma_ij = 0; sum_i beta_i = 0; sum_i lambda_i = 0.",
    "- Homogeneity: sum_j gamma_ij = 0.",
    "- Symmetry: gamma_ij = gamma_ji.",
    "",
    "## Model selection (Bewley 1986 LRB)",
    paste0("- logLik AIDS = ", round(fit_aids$logLik, 3), "; logLik QUAIDS = ", round(fit_quaids$logLik, 3), "."),
    paste0("- Plain LR = ", round(bewley$LR_plain, 3), "; Bewley scale = ", round(bewley$bewley_scale, 4),
           "; LRB = ", round(bewley$LRB, 3), " on df = ", bewley$df, "."),
    paste0("- LRB p-value = ", signif(bewley$p_value_LRB, 4), " => selected model: ", selected_family, "."),
    "",
    "## Outputs",
    "- `bewley_model_selection.csv`: Bewley LRB test for AIDS vs QUAIDS.",
    "- `demand_fiml_fit_summary.csv`: logLik, npar, convergence, selected flag.",
    "- `demand_parameters.csv`: alpha, beta, lambda by product.",
    "- `fiml_expenditure_elasticities.csv`, `fiml_price_elasticities_long.csv`, `fiml_morishima_elasticities_long.csv`.",
    "- `fiml_theory_regularities.csv`: own-price sign and Slutsky local negativity.",
    "- `quality_adjusted_price_diagnostics.csv`, `quality_adjusted_price_params.csv`.",
    "",
    "## Caveat",
    "Conditional import-demand system: elasticities are conditional import-budget elasticities, not unconditional income elasticities."
  )
  writeLines(report, file.path(args$outdir, "aids_quaids_report.md"))
  cat(paste(report, collapse = "\n"), "\n")
}

if (sys.nframe() == 0) main()
```

---

## 3. utils_aids_quaids.R

```r
# Utilities for FIML AIDS / QUAIDS demand-system estimation in R.
# China feed-grain import allocation, conditional import-demand version.
#
# Design:
#   - AIDS (Deaton-Muellbauer 1980) with translog price index a(p).
#   - QUAIDS (Banks-Blundell-Lewbel 1997) adds a quadratic expenditure term
#     lambda_i / b(p) * [ln(X/a(p))]^2; AIDS is nested at lambda_i = 0.
#   - Theoretical regularity imposed by parameterization:
#       * adding-up:    sum_i alpha_i = 1, sum_i gamma_ij = 0, sum_i beta_i = 0, sum_i lambda_i = 0
#       * homogeneity:  sum_j gamma_ij = 0
#       * symmetry:     gamma_ij = gamma_ji
#   - Shonkwiler-Yen (1999) two-step correction for zero import shares:
#       observed w_i = Phi_i * g_i + psi_i * phi_i, with Phi_i, phi_i from a
#       first-stage probit on predetermined / strictly lagged variables.
#   - Expenditure endogeneity handled by a control-function residual (vhat)
#     from a Bartik-IV first stage (vhat enters each share equation linearly).
#   - Model selection between AIDS and QUAIDS uses the Bewley (1986) small-sample
#     likelihood-ratio test (LRB) as in Hovhannisyan et al. (2014).
#
# This file sources utils_cf_easi_geasi.R for shared helpers (safe_num, clean_df,
# selection stage, quality-adjusted price construction, Bartik IV, first stage).

.aq_here <- function() {
  cands <- c(file.path("scripts", "r", "utils_cf_easi_geasi.R"),
             file.path(dirname(sys.frame(1)$ofile %||% "."), "utils_cf_easi_geasi.R"),
             "utils_cf_easi_geasi.R",
             file.path("cf_easi_geasi_r_code", "utils_cf_easi_geasi.R"))
  cands[file.exists(cands)][1]
}
`%||%` <- function(a, b) if (!is.null(a)) a else b
{
  .base <- .aq_here()
  if (is.na(.base) || is.null(.base)) stop("Cannot locate utils_cf_easi_geasi.R for shared helpers.")
  source(.base)
}

# -----------------------------------------------------------------------------
# System data assembly
# -----------------------------------------------------------------------------

make_aq_data <- function(df, variant, products = PRODUCTS, omitted = "auto",
                         controls = DEFAULT_CONTROLS, include_controls = TRUE,
                         corrected = TRUE, include_cf = TRUE, vhat = NULL) {
  omitted <- choose_omitted(df, products, omitted)
  ordered <- c(setdiff(products, omitted), omitted)
  N <- length(ordered); m <- N - 1L
  eq_products <- ordered[seq_len(m)]
  base <- PRICE_VARIANT_COLS[[variant]]
  logp <- sapply(ordered, function(p) safe_num(df[[paste0(base, "__", p)]]))
  colnames(logp) <- ordered
  w <- sapply(ordered, function(p) safe_num(df[[paste0("budget_share__", p)]]))
  colnames(w) <- ordered
  X <- if ("total_import_expenditure_usd" %in% names(df)) safe_num(df$total_import_expenditure_usd) else exp(safe_num(df$ln_total_import_expenditure_usd))
  X <- pmax(X, 1e-12)
  lnX <- log(X)
  lnX_center <- mean(lnX, na.rm = TRUE)
  zcols <- if (include_controls) intersect(controls, names(df)) else character()
  Z <- if (length(zcols)) as.matrix(clean_df(df[, zcols, drop = FALSE])) else matrix(0, nrow(df), 0)
  if (ncol(Z) > 0) {
    keep <- apply(Z, 2, function(z) stats::sd(z, na.rm = TRUE) > 1e-12)
    Z <- Z[, keep, drop = FALSE]
  }
  if (is.null(vhat)) vhat <- rep(0, nrow(df))
  vhat <- safe_num(vhat)
  Phi <- sapply(ordered, function(p) {
    cn <- paste0("selection_Phi__", p)
    if (corrected && cn %in% names(df)) pmin(pmax(safe_num(df[[cn]]), 0.01), 0.99) else rep(1, nrow(df))
  })
  phi <- sapply(ordered, function(p) {
    cn <- paste0("selection_phi__", p)
    if (corrected && cn %in% names(df)) safe_num(df[[cn]]) else rep(0, nrow(df))
  })
  colnames(Phi) <- colnames(phi) <- ordered
  list(
    df = df, variant = variant, products = ordered, eq_products = eq_products, omitted = omitted,
    m = m, N = N, n = nrow(df), logp = logp, w = w, X = X, lnX = lnX, lnX_center = lnX_center,
    Z = Z, zcols = colnames(Z), K = ncol(Z), corrected = corrected, include_cf = include_cf,
    Phi = Phi, phi = phi, vhat = vhat
  )
}

# -----------------------------------------------------------------------------
# Parameter packing / unpacking (restrictions imposed here)
# -----------------------------------------------------------------------------

aq_npar <- function(sys, quaids) {
  m <- sys$m; K <- sys$K
  n_alpha <- m
  n_gamma <- m * (m + 1L) / 2L
  n_beta  <- m
  n_lambda <- if (quaids) m else 0L
  n_delta <- m * K
  n_cf <- if (sys$include_cf) m else 0L
  n_psi <- if (sys$corrected) m else 0L
  n_alpha + n_gamma + n_beta + n_lambda + n_delta + n_cf + n_psi
}

pack_initial_aq <- function(sys, quaids, start = NULL) {
  if (!is.null(start)) return(start)
  m <- sys$m; K <- sys$K
  mean_shares <- colMeans(sys$w, na.rm = TRUE)
  alpha_free <- pmax(mean_shares[seq_len(m)], 1e-4)
  gamma_free <- rep(0, m * (m + 1L) / 2L)
  beta_free <- rep(0, m)
  lambda_free <- if (quaids) rep(0, m) else numeric(0)
  delta_free <- if (K > 0) rep(0, m * K) else numeric(0)
  cf_free <- if (sys$include_cf) rep(0, m) else numeric(0)
  psi_free <- if (sys$corrected) rep(0, m) else numeric(0)
  c(as.numeric(alpha_free), gamma_free, beta_free, lambda_free, delta_free, cf_free, psi_free)
}

unpack_aq <- function(par, sys, quaids) {
  m <- sys$m; N <- sys$N; K <- sys$K
  idx <- 1L
  alpha_free <- par[idx:(idx + m - 1L)]; idx <- idx + m
  alpha <- c(alpha_free, 1 - sum(alpha_free))                   # adding-up
  n_gamma <- m * (m + 1L) / 2L
  gamma <- alpha_from_free(par[idx:(idx + n_gamma - 1L)], m)    # symmetry + homogeneity + adding-up
  idx <- idx + n_gamma
  beta_free <- par[idx:(idx + m - 1L)]; idx <- idx + m
  beta <- c(beta_free, -sum(beta_free))                         # adding-up
  lambda <- rep(0, N)
  if (quaids) {
    lambda_free <- par[idx:(idx + m - 1L)]; idx <- idx + m
    lambda <- c(lambda_free, -sum(lambda_free))                 # adding-up
  }
  delta <- matrix(0, N, K)
  if (K > 0) {
    delta_free <- matrix(par[idx:(idx + m * K - 1L)], m, K); idx <- idx + m * K
    delta[seq_len(m), ] <- delta_free
    delta[N, ] <- -colSums(delta_free)                          # adding-up
  }
  cf <- rep(0, N)
  if (sys$include_cf) {
    cf_free <- par[idx:(idx + m - 1L)]; idx <- idx + m
    cf <- c(cf_free, -sum(cf_free))                             # adding-up
  }
  psi <- rep(0, m)
  if (sys$corrected) {
    psi <- par[idx:(idx + m - 1L)]; idx <- idx + m
  }
  list(alpha = alpha, gamma = gamma, beta = beta, lambda = lambda,
       delta = delta, cf = cf, psi = psi)
}

# -----------------------------------------------------------------------------
# Systematic share prediction (latent demand, before SY scaling)
# -----------------------------------------------------------------------------

ln_a_of_p <- function(logp, prm, alpha0 = 0) {
  # logp: n x N matrix. translog price index ln a(p).
  lin <- as.numeric(logp %*% prm$alpha)
  quad <- 0.5 * rowSums((logp %*% prm$gamma) * logp)
  alpha0 + lin + quad
}

predict_systematic <- function(par, sys, quaids, override = list()) {
  prm <- unpack_aq(par, sys, quaids)
  logp <- override$logp %||% sys$logp
  if (is.null(dim(logp))) logp <- matrix(logp, nrow = 1)
  n_obs <- nrow(logp)
  lnX <- rep_len(as.numeric(override$lnX %||% sys$lnX), n_obs)
  Z <- override$Z %||% sys$Z
  if (is.null(dim(Z))) Z <- matrix(Z, nrow = n_obs)
  if (nrow(Z) != n_obs && ncol(Z) > 0) Z <- matrix(rep(as.numeric(Z), length.out = n_obs * ncol(Z)), nrow = n_obs)
  vhat <- rep_len(as.numeric(override$vhat %||% sys$vhat), n_obs)

  ln_a <- ln_a_of_p(logp, prm)
  ln_b <- as.numeric(logp %*% prm$beta)
  g_exp <- (lnX - sys$lnX_center) - ln_a
  G_term <- logp %*% prm$gamma                                   # n x N, col i = sum_j gamma_ij logp_j
  beta_term <- outer(g_exp, prm$beta)
  W <- matrix(prm$alpha, n_obs, sys$N, byrow = TRUE) + G_term + beta_term
  if (quaids) {
    quad <- (g_exp^2) / pmax(exp(ln_b), 1e-8)
    W <- W + outer(quad, prm$lambda)
  }
  if (ncol(Z) > 0) W <- W + Z %*% t(prm$delta)
  if (sys$include_cf) W <- W + outer(vhat, prm$cf)
  colnames(W) <- sys$products
  W
}

# -----------------------------------------------------------------------------
# FIML objective with Shonkwiler-Yen correction
# -----------------------------------------------------------------------------

fiml_objective_aq <- function(par, sys, quaids) {
  g <- tryCatch(predict_systematic(par, sys, quaids), error = function(e) NULL)
  if (is.null(g) || any(!is.finite(g))) return(1e30)
  m <- sys$m; n <- sys$n; eq <- sys$eq_products
  g_eq <- g[, eq, drop = FALSE]
  if (sys$corrected) {
    pred <- sys$Phi[, eq, drop = FALSE] * g_eq + sys$phi[, eq, drop = FALSE] *
      matrix(unpack_aq(par, sys, quaids)$psi, nrow = n, ncol = m, byrow = TRUE)
  } else {
    pred <- g_eq
  }
  R <- sys$w[, eq, drop = FALSE] - pred
  R[!is.finite(R)] <- 0
  Sigma <- crossprod(R) / n + diag(1e-8, m)
  ld <- determinant(Sigma, logarithm = TRUE)$modulus[1]
  if (!is.finite(ld)) return(1e30)
  n * ld
}

fit_aids_quaids <- function(sys, family = c("AIDS", "QUAIDS"), start = NULL, maxit = 2000, trace = 0) {
  family <- match.arg(family)
  quaids <- family == "QUAIDS"
  par0 <- pack_initial_aq(sys, quaids, start = start)
  opt <- optim(par0, fiml_objective_aq, sys = sys, quaids = quaids,
               method = "BFGS", control = list(maxit = maxit, trace = trace, REPORT = 25))
  k <- length(opt$par); n <- sys$n; m <- sys$m
  ll <- -0.5 * (n * m * (log(2 * pi) + 1) + opt$value)
  structure(list(
    family = family, quaids = quaids, par = opt$par, objective = opt$value,
    logLik = as.numeric(ll), npar = k, neq = m, nobs = n,
    convergence = opt$convergence, message = opt$message, sys = sys,
    params = unpack_aq(opt$par, sys, quaids)
  ), class = "aids_quaids_fit")
}

# -----------------------------------------------------------------------------
# Model selection: Bewley (1986) small-sample LR test
# -----------------------------------------------------------------------------
# LRB = 2 (LLU - LLR) * (NEQ*NSS - NU_P) / (NEQ*NSS)
# AIDS is the restricted model (lambda_i = 0), QUAIDS the unrestricted (general) model.
# df = number of free lambda parameters = m (= NEQ).
bewley_lr_test <- function(restricted_aids, unrestricted_quaids) {
  LLR <- restricted_aids$logLik
  LLU <- unrestricted_quaids$logLik
  NEQ <- unrestricted_quaids$neq
  NSS <- unrestricted_quaids$nobs
  NU_P <- unrestricted_quaids$npar
  scale <- (NEQ * NSS - NU_P) / (NEQ * NSS)
  LR_plain <- 2 * (LLU - LLR)
  LRB <- LR_plain * scale
  df <- unrestricted_quaids$npar - restricted_aids$npar
  data.frame(
    test = "Bewley LRB: QUAIDS (unrestricted) vs AIDS (restricted)",
    logLik_AIDS = LLR, logLik_QUAIDS = LLU, NEQ = NEQ, NSS = NSS, NU_P = NU_P,
    bewley_scale = scale, LR_plain = LR_plain, LRB = LRB, df = df,
    p_value_LRB = if (df > 0) 1 - pchisq(LRB, df) else NA_real_,
    p_value_plain = if (df > 0) 1 - pchisq(LR_plain, df) else NA_real_,
    selected = if (df > 0 && is.finite(LRB) && (1 - pchisq(LRB, df)) < 0.05) "QUAIDS" else "AIDS",
    stringsAsFactors = FALSE
  )
}

# -----------------------------------------------------------------------------
# Elasticities (numeric derivatives of the systematic share at sample means)
# -----------------------------------------------------------------------------

aq_mean_reference <- function(sys) {
  list(
    logp = matrix(colMeans(sys$logp, na.rm = TRUE), nrow = 1, dimnames = list(NULL, sys$products)),
    lnX = mean(sys$lnX, na.rm = TRUE),
    Z = if (sys$K > 0) matrix(colMeans(sys$Z, na.rm = TRUE), nrow = 1) else matrix(0, 1, 0),
    vhat = mean(sys$vhat, na.rm = TRUE)
  )
}

aq_predict_one <- function(fit, ref) {
  as.numeric(predict_systematic(fit$par, fit$sys, fit$quaids,
                                override = list(logp = ref$logp, lnX = ref$lnX, Z = ref$Z, vhat = ref$vhat)))
}

# Core elasticity computation as an explicit function of the parameter vector,
# so the same map can be differentiated for delta-method standard errors.
# w0 (observed mean budget shares) is held fixed (it does not depend on par).
.aq_elast_core <- function(par, sys, quaids, w0, eps = 1e-5) {
  ref <- aq_mean_reference(sys)
  products <- sys$products; N <- length(products)
  pred1 <- function(ov) as.numeric(predict_systematic(par, sys, quaids, override = ov))
  base_ov <- list(logp = ref$logp, lnX = ref$lnX, Z = ref$Z, vhat = ref$vhat)
  Dp <- matrix(0, N, N, dimnames = list(products, products))
  for (j in seq_len(N)) {
    ovp <- base_ov; ovm <- base_ov
    ovp$logp <- ref$logp; ovp$logp[1, j] <- ovp$logp[1, j] + eps
    ovm$logp <- ref$logp; ovm$logp[1, j] <- ovm$logp[1, j] - eps
    Dp[, j] <- (pred1(ovp) - pred1(ovm)) / (2 * eps)
  }
  ovp <- base_ov; ovm <- base_ov; ovp$lnX <- ref$lnX + eps; ovm$lnX <- ref$lnX - eps
  DX <- (pred1(ovp) - pred1(ovm)) / (2 * eps); names(DX) <- products
  eta <- 1 + DX / pmax(w0, 1e-8); names(eta) <- products
  H <- matrix(0, N, N, dimnames = list(products, products))
  M <- matrix(0, N, N, dimnames = list(products, products))
  for (i in seq_len(N)) for (j in seq_len(N)) {
    M[i, j] <- Dp[i, j] / pmax(w0[i], 1e-8) - as.numeric(i == j)
    H[i, j] <- M[i, j] + eta[i] * w0[j]
  }
  MOR <- matrix(0, N, N, dimnames = list(products, products))  # MOR[qi, pj]
  for (pj in seq_len(N)) for (qi in seq_len(N)) MOR[qi, pj] <- H[qi, pj] - H[pj, pj]
  list(eta = eta, d_share_d_lnX = DX, d_share_d_lnp = Dp, marshall = M, hicks = H, morishima = MOR)
}

elasticities_aq <- function(fit, eps = 1e-5) {
  sys <- fit$sys; ref <- aq_mean_reference(sys)
  products <- sys$products
  # Green & Alston (1990) convention: evaluate elasticities at OBSERVED mean budget
  # shares. The fitted systematic latent share is not used as the denominator because
  # the SY correction breaks exact adding-up, driving the omitted good's latent share
  # negative and producing degenerate elasticities for that equation.
  w_fitted <- aq_predict_one(fit, ref); names(w_fitted) <- products
  w0 <- colMeans(sys$w, na.rm = TRUE); names(w0) <- products
  core <- .aq_elast_core(fit$par, sys, fit$quaids, w0, eps = eps)
  c(list(w = w0, w_fitted = w_fitted), core)
}

# Flatten all elasticities into one named vector (for delta-method Jacobian).
.aq_elast_flat <- function(par, sys, quaids, w0, eps = 1e-5) {
  core <- .aq_elast_core(par, sys, quaids, w0, eps = eps)
  products <- sys$products
  out <- core$eta; names(out) <- paste0("eta__", products)
  M <- core$marshall; H <- core$hicks; MOR <- core$morishima
  mv <- as.vector(M); names(mv) <- as.vector(outer(rownames(M), colnames(M), function(a, b) paste0("M__", a, "__", b)))
  hv <- as.vector(H); names(hv) <- as.vector(outer(rownames(H), colnames(H), function(a, b) paste0("H__", a, "__", b)))
  morv <- as.vector(MOR); names(morv) <- as.vector(outer(rownames(MOR), colnames(MOR), function(a, b) paste0("MOR__", a, "__", b)))
  c(out, mv, hv, morv)
}

# Robust (pseudo) inverse via truncated SVD.
.psd_inv <- function(Hmat) {
  s <- svd(Hmat)
  tol <- max(dim(Hmat)) * max(s$d) * .Machine$double.eps^0.5
  di <- ifelse(s$d > tol, 1 / s$d, 0)
  s$v %*% (di * t(s$u))
}

# Parameter covariance from the Hessian of the concentrated FIML objective.
# objective = n*log|Sigma(par)|; -logLik = const + 0.5*objective, so
# Hessian(-logLik) = 0.5*Hessian(objective) and Vcov(par) = 2*inv(Hessian(objective)).
aq_param_vcov <- function(fit) {
  H_obj <- tryCatch(optimHess(fit$par, fiml_objective_aq, sys = fit$sys, quaids = fit$quaids),
                    error = function(e) NULL)
  if (is.null(H_obj) || any(!is.finite(H_obj))) return(NULL)
  V <- tryCatch(2 * .psd_inv((H_obj + t(H_obj)) / 2), error = function(e) NULL)
  V
}

# Delta-method standard errors for every elasticity, returned as a named vector.
aq_elast_se <- function(fit, eps = 1e-5, h_rel = 1e-4) {
  sys <- fit$sys; quaids <- fit$quaids
  w0 <- colMeans(sys$w, na.rm = TRUE); names(w0) <- sys$products
  V <- aq_param_vcov(fit)
  base <- .aq_elast_flat(fit$par, sys, quaids, w0, eps = eps)
  if (is.null(V)) return(list(estimate = base, se = setNames(rep(NA_real_, length(base)), names(base)),
                              vcov_ok = FALSE))
  par <- fit$par; npar <- length(par)
  J <- matrix(0, length(base), npar, dimnames = list(names(base), NULL))
  for (k in seq_len(npar)) {
    step <- max(h_rel * abs(par[k]), 1e-6)
    pp <- par; pp[k] <- pp[k] + step
    pm <- par; pm[k] <- pm[k] - step
    J[, k] <- (.aq_elast_flat(pp, sys, quaids, w0, eps = eps) -
               .aq_elast_flat(pm, sys, quaids, w0, eps = eps)) / (2 * step)
  }
  Var <- J %*% V %*% t(J)
  se <- sqrt(pmax(diag(Var), 0)); names(se) <- names(base)
  list(estimate = base, se = se, vcov_ok = TRUE)
}

# Two-sided normal p-value for H0: elasticity = 0.
.z_p <- function(est, se) {
  z <- est / se
  list(z = z, p = 2 * stats::pnorm(-abs(z)))
}

elasticity_tables_aq <- function(fit, price_variant, iv_set, corrected) {
  el <- elasticities_aq(fit)
  products <- fit$sys$products
  tag <- paste0(fit$family, if (corrected) "_SY" else "")
  ses <- aq_elast_se(fit)
  SE <- ses$se
  getse <- function(nm) if (nm %in% names(SE)) as.numeric(SE[[nm]]) else NA_real_
  exp_rows <- list(); price_rows <- list(); mor_rows <- list()
  for (p in products) {
    est <- el$eta[[p]]; se <- getse(paste0("eta__", p)); zp <- .z_p(est, se)
    exp_rows[[length(exp_rows) + 1]] <- data.frame(
      model_name = tag, family = fit$family, price_variant = price_variant, iv_set = iv_set,
      corrected = corrected, product = p, product_cn = PRODUCT_CN[[p]],
      mean_budget_share = el$w[[p]], fitted_latent_share = el$w_fitted[[p]],
      d_share_d_lnX = el$d_share_d_lnX[[p]],
      expenditure_elasticity = est, std_error = se, z_value = zp$z, p_value = zp$p,
      stringsAsFactors = FALSE)
    for (pj in products) {
      m_est <- el$marshall[p, pj]; m_se <- getse(paste0("M__", p, "__", pj)); m_zp <- .z_p(m_est, m_se)
      h_est <- el$hicks[p, pj];    h_se <- getse(paste0("H__", p, "__", pj)); h_zp <- .z_p(h_est, h_se)
      price_rows[[length(price_rows) + 1]] <- data.frame(
        model_name = tag, family = fit$family, price_variant = price_variant, iv_set = iv_set,
        corrected = corrected, quantity_product = p, quantity_product_cn = PRODUCT_CN[[p]],
        price_product = pj, price_product_cn = PRODUCT_CN[[pj]],
        marshallian_elasticity = m_est, marshallian_se = m_se, marshallian_z = m_zp$z, marshallian_p = m_zp$p,
        hicksian_elasticity = h_est, hicksian_se = h_se, hicksian_z = h_zp$z, hicksian_p = h_zp$p,
        stringsAsFactors = FALSE)
    }
  }
  for (pj in products) for (qi in products) if (qi != pj) {
    est <- el$hicks[qi, pj] - el$hicks[pj, pj]
    se <- getse(paste0("MOR__", qi, "__", pj)); zp <- .z_p(est, se)
    mor_rows[[length(mor_rows) + 1]] <- data.frame(
      model_name = tag, family = fit$family, price_variant = price_variant, iv_set = iv_set,
      corrected = corrected, price_product = pj, price_product_cn = PRODUCT_CN[[pj]],
      ratio_quantity_product = qi, ratio_quantity_product_cn = PRODUCT_CN[[qi]],
      morishima_elasticity = est, std_error = se, z_value = zp$z, p_value = zp$p,
      stringsAsFactors = FALSE)
  }
  list(expenditure = do.call(rbind, exp_rows), price = do.call(rbind, price_rows),
       morishima = do.call(rbind, mor_rows), core = el)
}

regularity_check_aq <- function(fit, price_variant, iv_set, corrected) {
  el <- elasticities_aq(fit); w <- el$w
  S <- diag(as.numeric(w)) %*% el$hicks
  eig <- eigen((S + t(S)) / 2, symmetric = TRUE, only.values = TRUE)$values
  data.frame(
    model_name = paste0(fit$family, if (corrected) "_SY" else ""), family = fit$family,
    price_variant = price_variant, iv_set = iv_set, corrected = corrected,
    logLik = fit$logLik, npar = fit$npar, convergence = fit$convergence,
    max_own_hicksian = max(diag(el$hicks), na.rm = TRUE),
    min_own_hicksian = min(diag(el$hicks), na.rm = TRUE),
    passes_own_price_sign = all(diag(el$hicks) <= 1e-8),
    min_slutsky_eigenvalue = min(eig, na.rm = TRUE),
    max_slutsky_eigenvalue = max(eig, na.rm = TRUE),
    passes_local_negativity = all(eig <= 1e-8), stringsAsFactors = FALSE)
}

# Flatten the structural alpha/beta/lambda (all N goods, incl. the adding-up-recovered
# omitted good) into one named vector, for delta-method parameter standard errors.
.aq_param_flat <- function(par, sys, quaids) {
  prm <- unpack_aq(par, sys, quaids); products <- sys$products
  a <- prm$alpha; names(a) <- paste0("alpha__", products)
  b <- prm$beta;  names(b) <- paste0("beta__", products)
  l <- prm$lambda; names(l) <- paste0("lambda__", products)
  c(a, b, l)
}

aq_param_table <- function(fit, price_variant, iv_set, corrected, h_rel = 1e-4) {
  prm <- fit$params; products <- fit$sys$products; sys <- fit$sys; quaids <- fit$quaids
  V <- aq_param_vcov(fit)
  base <- .aq_param_flat(fit$par, sys, quaids)
  se <- setNames(rep(NA_real_, length(base)), names(base))
  if (!is.null(V)) {
    par <- fit$par; J <- matrix(0, length(base), length(par), dimnames = list(names(base), NULL))
    for (k in seq_along(par)) {
      step <- max(h_rel * abs(par[k]), 1e-6)
      pp <- par; pp[k] <- pp[k] + step; pm <- par; pm[k] <- pm[k] - step
      J[, k] <- (.aq_param_flat(pp, sys, quaids) - .aq_param_flat(pm, sys, quaids)) / (2 * step)
    }
    se <- sqrt(pmax(diag(J %*% V %*% t(J)), 0)); names(se) <- names(base)
  }
  gse <- function(nm) if (nm %in% names(se)) as.numeric(se[[nm]]) else NA_real_
  rows <- list()
  for (i in seq_along(products)) {
    p <- products[i]
    for (par_name in c("alpha", "beta", "lambda")) {
      est <- prm[[par_name]][i]; s <- gse(paste0(par_name, "__", p)); zp <- .z_p(est, s)
      rows[[length(rows) + 1]] <- data.frame(
        model_name = paste0(fit$family, if (corrected) "_SY" else ""), family = fit$family,
        price_variant = price_variant, iv_set = iv_set, corrected = corrected,
        product = p, product_cn = PRODUCT_CN[[p]], parameter = par_name,
        estimate = est, std_error = s, z_value = zp$z, p_value = zp$p,
        stringsAsFactors = FALSE)
    }
  }
  do.call(rbind, rows)
}
```
