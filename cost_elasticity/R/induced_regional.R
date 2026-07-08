# induced_regional.R — M8：诱致性创新 区域×品种 第二阶段（用雇工工价真实省际变异）
#  第一阶段：corn/wheat/rice_japonica 按 NBS 四大区域分别估 gindex 系统 → δ_{n,region,crop,τ}
#  第二阶段：sb=−Δδ 对滞后 Δln(w_hired,region/w̄_region)（k=1..3 与 1..5）
#            + 年份FE（吸收全国共同趋势=根治）+ 区域×品种FE；DK 与 wild(区域×品种) 双SE；
#            placebo 前置一、二期。修 F-11：滞后按年份 merge 并 assert 无断档。
# 产出: out/bias_path_regional.csv, out/induced_regional.csv, out/induced_regional_G4.csv
suppressMessages({library(data.table); library(sandwich)})
setwd("/root/paper/cost_elasticity")
source("R/itsur.R"); source("R/estimate.R")
FN <- c("labor","mach","fert","seed","other")
CROPS <- c("corn","wheat","rice_japonica")

# NBS 四大区域
NBS4 <- c(北京="east",天津="east",河北="east",上海="east",江苏="east",浙江="east",福建="east",山东="east",广东="east",海南="east",
          山西="central",安徽="central",江西="central",河南="central",湖北="central",湖南="central",
          内蒙古="west",广西="west",重庆="west",四川="west",贵州="west",云南="west",西藏="west",陕西="west",甘肃="west",青海="west",宁夏="west",新疆="west",
          辽宁="northeast",吉林="northeast",黑龙江="northeast")
NEIGHBOR <- c(northeast="east", east="central", central="west", west="central")  # 过小区域并入邻区

assign_region <- function(pan) {
  reg <- NBS4[pan$province]
  repeat {
    tab <- pan[, .(np = uniqueN(province), nobs = .N), by = .(r = reg)]
    bad <- tab[np < 4 | nobs < 60]
    if (!nrow(bad)) break
    r0 <- bad[order(nobs)][1]$r; tgt <- NEIGHBOR[r0]
    if (is.na(tgt) || tgt == r0) { tgt <- tab[order(-nobs)][r != r0][1]$r }
    reg[reg == r0] <- tgt
    if (uniqueN(reg) <= 1) break
  }
  reg
}

# 第一阶段：区域×品种 gindex → δ 路径
stage1 <- function(cr) {
  pan <- fread(sprintf("data/panel_%s.csv", cr))
  pan[, reg := assign_region(pan)]
  out <- list()
  for (rg in unique(pan$reg)) {
    sub <- pan[reg == rg]; yrs <- sort(unique(sub$year))
    if (length(yrs) < 8 || any(diff(yrs) != 1)) {   # 需足够且连续（gindex 年哑变量）
      # 允许断档：仅取最长连续段
      runs <- split(yrs, cumsum(c(1, diff(yrs) != 1)))
      yrs <- runs[[which.max(sapply(runs, length))]]; sub <- sub[year %in% yrs]
      if (length(yrs) < 8) next
    }
    d <- prep_data(sub)
    sys <- tl_build_system(d, 4, use_cost_eq = FALSE, share_time = "gindex",
                           year_dummies = as.character(yrs))
    fit <- tryCatch(tl_itsur(sys, tol = 1e-9), error = function(e) NULL)
    if (is.null(fit) || !fit$converged) next
    rows <- list()
    for (y in yrs[-1]) {
      dl <- sapply(1:4, function(n) fit$theta[sprintf("delta%d_%s", n, y)])
      rows[[as.character(y)]] <- data.table(crop = cr, region = rg, year = y, factor = FN, delta = c(dl, -sum(dl)))
    }
    out[[rg]] <- rbind(data.table(crop = cr, region = rg, year = yrs[1], factor = FN, delta = 0),
                       rbindlist(rows))
  }
  rbindlist(out)
}

paths <- rbindlist(lapply(CROPS, stage1))
fwrite(paths, "out/bias_path_regional.csv")

# 区域相对雇工工价（品种内按产量聚合到区域，相对全样本几何均值）
relwage <- function() {
  rows <- list()
  for (cr in CROPS) {
    pan <- fread(sprintf("data/panel_%s.csv", cr)); pan[, reg := assign_region(pan)]
    agg <- pan[, .(w = weighted.mean(w_labor_hired, q_output, na.rm = TRUE)), by = .(crop = cr, region = reg, year)]
    agg[, wbar := weighted.mean(w, table(pan$reg)[region], na.rm = TRUE), by = year]  # 年内区域均值
    agg[, lnrel := log(w / mean(w)), by = .(crop, year)]                              # 相对当年区域均值
    setorder(agg, crop, region, year)
    agg[, dlnrel := c(NA, diff(lnrel)), by = .(crop, region)]
    rows[[cr]] <- agg[, .(crop, region, year, dlnrel)]
  }
  rbindlist(rows)
}
rel <- relwage()

# sb = −Δδ（labor/mach），按年份 merge 滞后（F-11：非位置shift）
bias <- paths[factor %in% c("labor","mach")]
setorder(bias, crop, region, factor, year)
bias[, sb := -(delta - shift(delta)), by = .(crop, region, factor)]
reg2 <- merge(bias[!is.na(sb)], rel, by = c("crop","region","year"))

# 年份对齐滞后/前置（merge 而非 shift）
mk_lag <- function(dd, k) {
  lg <- rel[, .(crop, region, year_lag = year + k, Lk = dlnrel)]
  setnames(lg, "Lk", paste0("L", k))
  merge(dd, lg, by.x = c("crop","region","year"), by.y = c("crop","region","year_lag"), all.x = TRUE)
}
mk_lead <- function(dd, k) {
  ld <- rel[, .(crop, region, year_lead = year - k, Fk = dlnrel)]
  setnames(ld, "Fk", paste0("F", k))
  merge(dd, ld, by.x = c("crop","region","year"), by.y = c("crop","region","year_lead"), all.x = TRUE)
}

wild_cluster_se <- function(f, cl, coefnames, Bw = 999) {
  # Rademacher wild cluster bootstrap（区域×品种聚类），返回 Σ(coefnames) 的 SE
  X <- model.matrix(f); y <- f$model[[1]]; b <- coef(f); r <- residuals(f)
  fitted0 <- fitted(f); cls <- unique(cl); XtXi <- solve(crossprod(X))
  sel <- colnames(X) %in% coefnames
  stats <- numeric(Bw)
  for (bi in seq_len(Bw)) {
    set.seed(1000 + bi)
    wgt <- setNames(sample(c(-1,1), length(cls), replace = TRUE), cls)[as.character(cl)]
    yb <- fitted0 + r * wgt
    bb <- XtXi %*% crossprod(X, yb)
    stats[bi] <- sum(bb[sel])
  }
  sd(stats)
}

res <- list()
for (n in c("labor","mach")) {
  dd <- reg2[factor == n]
  for (k in 1:5) dd <- mk_lag(dd, k)
  for (k in 1:2) dd <- mk_lead(dd, k)
  dd[, rc := paste0(region, "_", crop)]
  for (spec in list(list(nm="k1_3", L=c("L1","L2","L3")), list(nm="k1_5", L=c("L1","L2","L3","L4","L5")))) {
    vars <- spec$L
    dsub <- dd[complete.cases(dd[, c(vars,"sb"), with = FALSE])]
    f <- lm(as.formula(paste("sb ~ factor(year) + factor(rc) +", paste(vars, collapse = "+"))), dsub)
    sumpsi <- sum(coef(f)[vars], na.rm = TRUE)
    # Driscoll–Kraay（面板，时间维 HAC）
    V_dk <- tryCatch(vcovPL(f, cluster = ~ year, lag = 2), error = function(e) NULL)
    se_dk <- if (!is.null(V_dk)) sqrt(sum(V_dk[vars, vars])) else NA_real_
    se_wild <- tryCatch(wild_cluster_se(f, dsub$rc, vars), error = function(e) NA_real_)
    # placebo（前置一、二期）
    fp <- lm(as.formula(paste("sb ~ factor(year) + factor(rc) +", paste(c(vars,"F1","F2"), collapse = "+"))),
             dd[complete.cases(dd[, c(vars,"F1","F2","sb"), with = FALSE])])
    plac_t <- tryCatch({ V <- vcovPL(fp, cluster = ~ year, lag = 2)
      c(coef(fp)["F1"]/sqrt(V["F1","F1"]), coef(fp)["F2"]/sqrt(V["F2","F2"]) ) }, error = function(e) c(NA,NA))
    res[[length(res)+1]] <- data.table(factor = n, spec = spec$nm, n_obs = nrow(dsub),
      sum_psi = round(sumpsi,3), se_dk = round(se_dk,3), t_dk = round(sumpsi/se_dk,2),
      se_wild = round(se_wild,3), t_wild = round(sumpsi/se_wild,2),
      placebo_F1_t = round(plac_t[1],2), placebo_F2_t = round(plac_t[2],2))
  }
}
ii <- rbindlist(res); fwrite(ii, "out/induced_regional.csv")

# G4：placebo 干净（|t|<1.5）且 Σψ>0 → suggestive 回正文；否则降级描述性
lab13 <- ii[factor == "labor" & spec == "k1_3"]
clean_plac <- abs(lab13$placebo_F1_t) < 1.5 & abs(lab13$placebo_F2_t) < 1.5
g4 <- data.table(factor = "labor", sum_psi = lab13$sum_psi, t_dk = lab13$t_dk,
  placebo_F1_t = lab13$placebo_F1_t, placebo_F2_t = lab13$placebo_F2_t,
  verdict = ifelse(clean_plac & lab13$sum_psi > 0, "suggestive_evidence(回正文)", "descriptive_only(删因果语言)"))
fwrite(g4, "out/induced_regional_G4.csv")
cat("\n===== M8 区域×品种诱致性 第二阶段 =====\n"); print(ii)
cat("\n===== G4 =====\n"); print(g4)
cat("\n[induced_regional] done\n")
