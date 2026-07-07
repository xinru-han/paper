# postest_decomp.R — 成本增长 Törnqvist 分解（plan §4.6）+ OOS 份额预测（§4.9）
# 用法: Rscript R/postest_decomp.R <crop1> <crop2> ...
# 产出: out/decomp_{crop}.csv, out/oos_{crop}.csv
# 注：分解按名义口径（价格贡献含通胀），正文如需实际口径再统一平减，此处如实标注
suppressMessages(library(data.table))
setwd("/root/paper/cost_elasticity")
source("R/itsur.R"); source("R/itsur_concave.R"); source("R/estimate.R")

FN <- c("labor", "mach", "fert", "seed", "other")
SEGS <- list(`2004-2024` = c(2004, 2024), `2004-2013` = c(2004, 2013),
             `2013-2024` = c(2013, 2024))

decomp_crop <- function(cr) {
  pan <- fread(sprintf("data/panel_%s.csv", cr))
  r <- fit_crop(cr, write_out = FALSE, method = "cc")   # 与基线规格一致（F-7）
  th <- r$fit$theta
  d <- r$d
  rows <- list()
  for (sg in names(SEGS)) {
    y0 <- SEGS[[sg]][1]; y1 <- SEGS[[sg]][2]
    common <- intersect(pan[year == y0, province], pan[year == y1, province])
    for (pv in common) {
      a <- pan[province == pv & year == y0]; b <- pan[province == pv & year == y1]
      dlC <- log(b$C_var / a$C_var)
      Sb <- sapply(FN, function(n) (a[[paste0("S_", n)]] + b[[paste0("S_", n)]]) / 2)
      dlw <- sapply(FN, function(n) log(b[[paste0("w_", n)]] / a[[paste0("w_", n)]]))
      price_part <- sum(Sb * dlw)
      # 规模项与技术项在省级期中点评估
      mid <- d[prov == pv & year %in% c(y0:y1)]
      eCy <- mean(th["alpha_y"] + th["gamma_yy"] * mid$lny +
        as.matrix(as.data.frame(mid)[, sprintf("lnw_%d", 1:4)]) %*% th[sprintf("gamma_%dy", 1:4)] +
        th["lambda_yt"] * mid$tt)
      tauC <- mean(th["lambda_t"] + th["lambda_tt"] * mid$tt +
        as.matrix(as.data.frame(mid)[, sprintf("lnw_%d", 1:4)]) %*% th[sprintf("lambda_%dt", 1:4)] +
        th["lambda_yt"] * mid$lny)
      dly <- log(b$q_output / a$q_output)
      yield_part <- eCy * dly
      tech_part <- tauC * (y1 - y0)
      rows[[length(rows) + 1]] <- data.table(crop = cr, seg = sg, province = pv,
        q_w = b$q_output, dlnC = dlC, price = price_part,
        price_labor = Sb["labor"] * dlw["labor"], price_mach = Sb["mach"] * dlw["mach"],
        price_fert = Sb["fert"] * dlw["fert"], price_seed = Sb["seed"] * dlw["seed"],
        price_other = Sb["other"] * dlw["other"],
        yield = yield_part, tech = tech_part,
        residual = dlC - price_part - yield_part - tech_part)
    }
  }
  dd <- rbindlist(rows)
  # 全国=省按产量加权
  nat <- dd[, lapply(.SD, function(x) sum(x * q_w) / sum(q_w)), by = .(crop, seg),
            .SDcols = setdiff(names(dd), c("crop", "seg", "province", "q_w"))]
  nat[, province := "NATIONAL"]
  out <- rbind(dd[, !"q_w"], nat, fill = TRUE)
  fwrite(out, sprintf("out/decomp_%s.csv", cr))
  nat
}

oos_crop <- function(cr) {
  pan <- fread(sprintf("data/panel_%s.csv", cr))
  tr <- pan[year <= 2021]; te <- pan[year >= 2022]
  te <- te[province %in% unique(tr$province)]
  d_tr <- prep_data(tr)
  sys_tr <- tl_build_system(d_tr, 4)
  fit_tl <- tl_itsur(sys_tr); stopifnot(fit_tl$converged)
  fit_cd <- tl_itsur(sys_tr, drop_params = "^gamma_[1-4]_[1-4]$"); stopifnot(fit_cd$converged)
  centers <- attr(d_tr, "centers")
  # 用训练期中心化参数构造测试期回归元
  d_te <- as.data.table(te)
  for (n in 1:4) d_te[[sprintf("lnw_%d", n)]] <-
    log(d_te[[paste0("w_", FN[n])]] / d_te$w_other) - centers[sprintf("lnw_%d", n)]
  d_te$lny <- log(d_te$q_output) - centers["lny"]
  d_te$tt <- d_te$year - 2014
  pred_shares <- function(fit) {
    th <- fit$theta
    lnw <- as.matrix(as.data.frame(d_te)[, sprintf("lnw_%d", 1:4)])
    sapply(1:4, function(n) {
      g <- sapply(1:4, function(m) th[if (n <= m) sprintf("gamma_%d_%d", n, m) else sprintf("gamma_%d_%d", m, n)])
      fe <- th[sprintf("fe%d_%s", n, d_te$province)]; fe[is.na(fe)] <- 0
      th[sprintf("alpha_%d", n)] + as.numeric(lnw %*% g) +
        th[sprintf("gamma_%dy", n)] * d_te$lny + th[sprintf("lambda_%dt", n)] * d_te$tt + fe
    })
  }
  Sobs <- as.matrix(as.data.frame(te)[, paste0("S_", FN[1:4])])
  # 随机游走：用该省训练期最后一年的观测份额
  last <- tr[, .SD[year == max(year)], by = province]
  rw <- as.matrix(as.data.frame(last[match(te$province, province)])[, paste0("S_", FN[1:4])])
  rmse <- function(P) sqrt(mean((P - Sobs)^2))
  out <- data.table(crop = cr, model = c("translog", "cobb_douglas", "random_walk"),
                    rmse = c(rmse(pred_shares(fit_tl)), rmse(pred_shares(fit_cd)), rmse(rw)),
                    n_test = nrow(te))
  fwrite(out, sprintf("out/oos_%s.csv", cr))
  out
}

crops <- commandArgs(trailingOnly = TRUE)
if (!length(crops)) crops <- "corn"
for (cr in crops) {
  cat("=====", cr, "=====\n")
  print(decomp_crop(cr)[, .(seg, dlnC = round(dlnC, 3), price = round(price, 3),
        price_labor = round(price_labor, 3), yield = round(yield, 3),
        tech = round(tech, 3), residual = round(residual, 3))])
  print(oos_crop(cr))
}
