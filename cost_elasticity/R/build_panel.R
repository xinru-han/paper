# build_panel.R — 汇编长表 + 发改委价格 → data/panel_{crop}.csv
# 5要素可变成本系统：labor, mach, fert, seed, other（numeraire）
# 价格：w_labor=劳动日工价；w_fert=化肥费/折纯量；w_seed=种子费/用种量（汇编单位值）
#       w_mach=发改委机耕费（元/亩，2011/2013省内对数插值，2004-05省内对数趋势回推）
#       w_other=毒死蜱×地膜 定权重几何平均指数（权重=该品种农药费占农药+农膜费的样本均值）
# QC：份额加总=1、价格>0、覆盖与插补全部写 out/panel_build_log.csv
suppressMessages(library(data.table))
setwd("/root/paper/cost_elasticity")

CROPS <- c("corn", "wheat", "soybean",
           "rice_early_indica", "rice_mid_indica", "rice_late_indica", "rice_japonica",
           "peanut", "rapeseed", "cotton")
YEARS <- 2004:2024

yb <- fread("data/yearbook_long.csv", encoding = "UTF-8")
if (file.exists("data/yearbook_patch_ocr_gaps.csv")) {
  patch <- fread("data/yearbook_patch_ocr_gaps.csv", encoding = "UTF-8")
  # 补录行只在原表没有该 (crop,year,province,variable) 时并入
  key <- c("crop", "year", "province", "variable")
  patch <- patch[!yb, on = key]
  yb <- rbind(yb, patch[, names(yb), with = FALSE])
  cat(sprintf("[panel] merged OCR patch rows: %d\n", nrow(patch)))
}
ndrc <- fread("data/prices_ndrc_annual.csv", encoding = "UTF-8")

log_rows <- list()
logit <- function(...) log_rows[[length(log_rows) + 1]] <<- data.table(...)

# ---- w_mach：机耕费省×年，补缺口 -------------------------------------------
mt <- ndrc[item == "machine_tillage", .(province, year, p = price)]
fill_mach <- function(g) {
  # g: 单省序列。2011/2013 对数线性插值；2004-05 用2006-2010对数趋势回推
  full <- data.table(year = 2004:2024)
  g <- merge(full, g, by = "year", all.x = TRUE)
  obs <- g[!is.na(p)]
  if (nrow(obs) < 8) return(g[, .(year, p, src = fifelse(is.na(p), NA_character_, "obs"))])  # 观测太少不外推，后续兜底
  g[, lp := log(p)]
  # 内部缺口插值
  g[, lp_i := approx(obs$year, log(obs$p), xout = year, rule = 1)$y]
  # 期初回推：2006-2010 对数趋势
  early <- obs[year <= 2010]
  if (nrow(early) >= 3) {
    fit <- lm(log(p) ~ year, early)
    g[year < min(obs$year), lp_i := predict(fit, newdata = .SD), .SDcols = "year"]
  }
  g[, p_filled := exp(lp_i)]
  g[, src := fifelse(!is.na(p), "obs", fifelse(year < min(obs$year), "backcast", "interp"))]
  g[, .(year, p = p_filled, src)]
}
mach <- mt[, fill_mach(.SD), by = province]
# 兜底：仍缺的省年用当年全国中位数
nat_med <- mach[!is.na(p), .(p_nat = median(p)), by = year]
mach <- merge(mach, nat_med, by = "year", all.x = TRUE)
mach[is.na(p), `:=`(p = p_nat, src = "national_median")]
mach[, p_nat := NULL]
setnames(mach, "p", "w_mach")

# ---- w_other：毒死蜱 × 地膜 定权重几何平均 ---------------------------------
po <- dcast(ndrc[item %in% c("chlorpyrifos", "mulch_film")],
            province + year ~ item, value.var = "price")
# 缺失先按省内插值，再全国中位数兜底
fill_series <- function(x, yr) {
  if (sum(!is.na(x)) >= 3) x <- exp(approx(yr[!is.na(x)], log(x[!is.na(x)]), xout = yr, rule = 2)$y)
  x
}
po <- po[order(province, year)]
po[, chlorpyrifos := fill_series(chlorpyrifos, year), by = province]
po[, mulch_film := fill_series(mulch_film, year), by = province]
for (v in c("chlorpyrifos", "mulch_film")) {
  med <- po[!is.na(get(v)), .(m = median(get(v))), by = year]
  po <- merge(po, med, by = "year", all.x = TRUE)
  po[is.na(get(v)), (v) := m]; po[, m := NULL]
}

# ---- 汇编宽表 ---------------------------------------------------------------
w <- dcast(yb[year %in% YEARS], crop + province + year ~ variable, value.var = "value",
           fun.aggregate = function(x) x[1])

# 成本科目缺失=0（汇编"—"表示无此项支出）；核心科目必须为正
zero_items <- c("排灌费", "畜力费", "燃料动力费", "农膜费", "农家肥费",
                "技术服务费", "工具材料费", "修理维护费", "其他直接费用", "农药费", "雇工费用")
for (v in zero_items) if (v %in% names(w)) w[is.na(get(v)), (v) := 0] else w[, (v) := 0]

w[, cost_labor := 人工成本]
w[, cost_mach  := 机械作业费 + 排灌费 + 畜力费 + 燃料动力费]
w[, cost_fert  := 化肥费]
w[, cost_seed  := 种子费]
w[, cost_other := 农药费 + 农膜费 + 农家肥费 + 技术服务费 + 工具材料费 + 修理维护费 + 其他直接费用]
w[, C_var := cost_labor + cost_mach + cost_fert + cost_seed + cost_other]

w[, w_labor := 劳动日工价]
w[, w_fert  := 化肥费 / 每亩化肥折纯用量]
w[, w_seed  := 种子费 / 每亩种子用量]
w[, q_output := 主产品产量]

REGION <- c(河北="huabei", 山西="huabei", 内蒙古="dongbei", 辽宁="dongbei", 吉林="dongbei",
            黑龙江="dongbei", 江苏="changjiang", 浙江="changjiang", 安徽="changjiang",
            福建="huanan", 江西="changjiang", 山东="huabei", 河南="huabei", 湖北="changjiang",
            湖南="changjiang", 广东="huanan", 广西="huanan", 海南="huanan", 重庆="xinan",
            四川="xinan", 贵州="xinan", 云南="xinan", 陕西="xibei", 甘肃="xibei",
            青海="xibei", 宁夏="xibei", 新疆="xibei", 北京="huabei", 天津="huabei",
            上海="changjiang", 西藏="xinan")

dir.create("data", showWarnings = FALSE); dir.create("out", showWarnings = FALSE)
summary_rows <- list()

for (cr in CROPS) {
  d <- w[crop == cr]
  if (nrow(d) < 50) { logit(crop = cr, step = "skip", detail = sprintf("rows=%d", nrow(d))); next }
  n0 <- nrow(d)
  d <- merge(d, mach, by = c("province", "year"), all.x = TRUE)
  d <- merge(d, po[, .(province, year, p_pest = chlorpyrifos, p_film = mulch_film)],
             by = c("province", "year"), all.x = TRUE)
  # 京津沪藏无发改委价格：机耕费用全国中位数、农药农膜用全国中位数兜底
  for (v in c("w_mach", "p_pest", "p_film")) {
    med <- d[!is.na(get(v)), .(m = median(get(v))), by = year]
    d <- merge(d, med, by = "year", all.x = TRUE)
    nfill <- d[is.na(get(v)), .N]
    if (nfill > 0) logit(crop = cr, step = paste0("fill_", v), detail = sprintf("national_median n=%d", nfill))
    d[is.na(get(v)), (v) := m]; d[, m := NULL]
  }
  # w_other：定权重（该品种样本均值）几何平均
  wt <- d[, mean(农药费 / pmax(农药费 + 农膜费, 1e-9), na.rm = TRUE)]
  wt <- min(max(wt, 0.05), 0.95)
  d[, w_other := p_pest^wt * p_film^(1 - wt)]
  logit(crop = cr, step = "w_other_weight", detail = sprintf("pesticide_weight=%.3f", wt))

  # 样本筛选：核心变量齐全且为正
  core <- c("C_var", "q_output", "w_labor", "w_fert", "w_seed", "w_mach", "w_other",
            "cost_labor", "cost_mach", "cost_fert", "cost_seed", "cost_other")
  ok <- d[, Reduce(`&`, lapply(.SD, function(x) is.finite(x) & x > 0)), .SDcols = setdiff(core, "cost_other")]
  ok <- ok & d$cost_other >= 0
  dropped <- d[!ok, .(province, year)]
  if (nrow(dropped) > 0)
    logit(crop = cr, step = "drop_obs", detail = paste0(nrow(dropped), " obs: ",
          paste(head(sprintf("%s%d", dropped$province, dropped$year), 12), collapse = ",")))
  d <- d[ok]

  d[, `:=`(S_labor = cost_labor / C_var, S_mach = cost_mach / C_var,
           S_fert = cost_fert / C_var, S_seed = cost_seed / C_var,
           S_other = cost_other / C_var)]
  stopifnot(max(abs(d$S_labor + d$S_mach + d$S_fert + d$S_seed + d$S_other - 1)) < 1e-8)
  # 单位值范围粗检：越界视为OCR错值，剔除并记录（如 甘肃小麦2023 化肥费=4.39）
  bad <- d[!(w_fert > 0.5 & w_fert < 50) | !(w_labor > 5 & w_labor < 300) |
           !(w_seed > 0.2 & w_seed < 500)]
  if (nrow(bad) > 0) {
    logit(crop = cr, step = "drop_unitvalue_outlier",
          detail = paste(sprintf("%s%d(wf=%.2f,wl=%.1f,ws=%.1f)", bad$province, bad$year,
                                 bad$w_fert, bad$w_labor, bad$w_seed), collapse = ";"))
    d <- d[!bad, on = c("province", "year")]
  }
  d[, region := REGION[province]]

  out <- d[, .(crop, province, region, year, C_var, q_output,
               S_labor, S_mach, S_fert, S_seed, S_other,
               w_labor, w_mach, w_fert, w_seed, w_other,
               labor_days = 每亩用工数量, fert_kg = 每亩化肥折纯用量,
               cost_labor, cost_mach, cost_fert, cost_seed, cost_other,
               cost_land = 土地成本, land_rent = if ("流转地租金" %in% names(d)) 流转地租金 else NA_real_)]
  setorder(out, province, year)
  fwrite(out, sprintf("data/panel_%s.csv", cr))
  summary_rows[[cr]] <- data.table(crop = cr, n_obs = nrow(out),
                                   n_prov = uniqueN(out$province),
                                   yr_min = min(out$year), yr_max = max(out$year),
                                   dropped = n0 - nrow(out),
                                   S_labor = round(mean(out$S_labor), 3),
                                   S_mach = round(mean(out$S_mach), 3),
                                   S_fert = round(mean(out$S_fert), 3),
                                   S_seed = round(mean(out$S_seed), 3),
                                   S_other = round(mean(out$S_other), 3))
}

fwrite(rbindlist(log_rows, fill = TRUE), "out/panel_build_log.csv")
smry <- rbindlist(summary_rows)
fwrite(smry, "out/panel_summary.csv")
print(smry)
cat("\n[panel] done\n")
