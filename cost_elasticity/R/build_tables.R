# build_tables.R — M14c：论文表 T1–T9 全部由 out/ 生成（markdown + csv 双格式）
#  缺失输入的表跳过并在 tables/_missing.log 记录（防半成品静默）。
# 产出: tables/T{1..9}_*.{md,csv}
suppressMessages(library(data.table))
setwd("/root/paper/cost_elasticity")
dir.create("tables", showWarnings = FALSE)
CROPS <- c("corn","wheat","soybean","rice_japonica","rice_mid_indica",
           "rice_early_indica","rice_late_indica","peanut","rapeseed")
miss <- c()
rd <- function(f) if (file.exists(f)) fread(f) else { miss <<- c(miss, f); NULL }
wr <- function(dt, stem, title) {
  if (is.null(dt) || !nrow(dt)) return(invisible())
  fwrite(dt, sprintf("tables/%s.csv", stem))
  body <- dt[, do.call(paste, c(lapply(.SD, as.character), sep = " | "))]
  md <- c(sprintf("### %s", title), "", paste0("| ", paste(names(dt), collapse = " | "), " |"),
          paste0("|", paste(rep("---", ncol(dt)), collapse = "|"), "|"),
          paste0("| ", body, " |"))
  writeLines(md, sprintf("tables/%s.md", stem))
}

# T1 识别诊断（价格变异）
wr(rd("out/price_variation_diag.csv"), "T1_price_variation_diag", "T1 价格变异诊断：ln(w_m/w_other) 对年份 R² 与省内SD")

# T2 弹性主表：cc 自价格 + M_ml，daywage 与 hired 双栏，附 M1 CI
el_cc <- rbindlist(lapply(CROPS, function(cr){ e<-rd(sprintf("out/elasticities_%s_cc.csv",cr)); if(is.null(e))return(NULL)
  ea<-e[period=="all"]; data.table(crop=cr, eps_ll=ea[f_n=="labor"&f_m=="labor",eps], eps_mm=ea[f_n=="mach"&f_m=="mach",eps],
    M_ml=ea[f_n=="mach"&f_m=="labor",morishima]) }))
el_hw <- rbindlist(lapply(CROPS, function(cr){ e<-rd(sprintf("out/elasticities_%s_hw_cc.csv",cr)); if(is.null(e))return(NULL)
  ea<-e[period=="all"]; data.table(crop=cr, eps_ll_hw=ea[f_n=="labor"&f_m=="labor",eps], M_ml_hw=ea[f_n=="mach"&f_m=="labor",morishima]) }))
ci <- rd("out/bootstrap_ci_cc.csv")
if(!is.null(ci)) setnames(ci, c("eps_ll","eps_mm","M_ml","B_labor"), c("eps_ll_ci","eps_mm_ci","M_ml_ci","B_labor_ci"), skip_absent=TRUE)
if(!is.null(el_cc)) setnames(el_cc, c("eps_ll","eps_mm","M_ml"), c("eps_ll_pt","eps_mm_pt","M_ml_pt"))
t2 <- if(!is.null(el_cc)) Reduce(function(a,b) merge(a,b,by="crop",all.x=TRUE), Filter(Negate(is.null), list(el_cc, el_hw, ci))) else NULL
if(!is.null(t2)) t2[, (names(t2)[sapply(t2,is.numeric)]) := lapply(.SD, round, 3), .SDcols=sapply(t2,is.numeric)]
wr(t2, "T2_elasticity_main", "T2 弹性主表（cc；daywage 与 hired；M1 percentile CI）")

# T3 跨品种 M_ml 差异 CI
wr(rd("out/crosscrop_Mml_ci.csv"), "T3_crosscrop_Mml_ci", "T3 跨品种 M_ml 差异 CI（同 draw 配对；含旱作−稻作组）")
# T4 Γ 断点检验
wr(rd("out/gamma_break_test.csv"), "T4_gamma_break", "T4 Γ 断点 LR（2004–13 vs 2014–24）+ 分半 M_ML")
# T5 偏向一致性
wr(rd("out/bias_consistency.csv"), "T5_bias_consistency", "T5 技术偏向跨规格一致性（S1/M1CI/S2/hw/6f）")
# T6 τ_C 路径
wr(rd("out/tauC_period_summary.csv"), "T6_tauC_period", "T6 对偶技术率 τ_C 分期路径（撤 RTS/TFP）")
# T7 分解（名义；实际待 INPUT）
wr(rd("out/decomp_corn.csv"), "T7_decomp_corn_nominal", "T7 玉米成本分解（名义口径；实际口径待 INPUT-1/2）")
# T8 诱致性（区域×品种）
wr(rd("out/induced_regional.csv"), "T8_induced_regional", "T8 诱致性创新 区域×品种第二阶段（年FE+DK/wild）")
# T9 稳健性总矩阵
rm_ <- rd("out/robust_matrix.csv"); sb <- rd("out/specB_compare.csv"); s6 <- rd("out/robust6f_compare.csv"); kp <- rd("out/kappa_sensitivity.csv")
wr(rm_, "T9_robust_matrix", "T9a 稳健性矩阵（wmach/xls/covid/regionperiod/fert 各变体核心弹性）")
wr(sb, "T9_specB", "T9b Spec B（预期产量）对照")
wr(s6, "T9_sixfactor", "T9c 六要素含地对照")
wr(kp, "T9_kappa", "T9d κ 敏感性")

if (length(miss)) writeLines(miss, "tables/_missing.log")
cat(sprintf("[build_tables] 生成表；缺失输入 %d 项%s\n", length(miss),
            if(length(miss)) paste0("（见 tables/_missing.log）") else ""))
