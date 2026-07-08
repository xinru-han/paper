#!/usr/bin/env Rscript
# Paper 1 计量：产业强镇交错DID（Sun-Abraham事件研究）
suppressMessages({library(data.table); library(fixest)})
setFixest_notes(FALSE)
OUT <- "/root/paper/rural_specialty_industry/paper1/output"
p <- fread(file.path(OUT, "town_year_panel.csv"), encoding = "UTF-8")

p[, `:=`(
  county = substr(town_code, 1, 6),
  prov = substr(town_code, 1, 2),
  loglight = log1p(light_sum),
  logpop = log1p(pop),
  Gf = ifelse(is.na(G), 10000L, G)   # 从未处理编码为10000
)]
# 事件研究样本：去掉极端小灯光缺失
p <- p[is.finite(loglight)]

sink(file.path(OUT, "results_paper1.txt"))
cat("==== Paper 1：产业强镇交错DID ====\n")
cat(sprintf("镇×年观测=%d 镇=%d 处理镇=%d 认定镇=%d 年=%d-%d\n\n",
            nrow(p), uniqueN(p$town_code), uniqueN(p[treated==1]$town_code),
            uniqueN(p[certified==1]$town_code), min(p$year), max(p$year)))

## ---------- 1. 静态TWFE ----------
cat("---- 表1 静态TWFE：post×treated ----\n")
p[, post := as.integer(!is.na(G) & year >= G)]
s_light <- feols(loglight ~ post | town_code + year, data = p, cluster = ~county)
s_pop   <- feols(logpop  ~ post | town_code + year, data = p, cluster = ~county)
s_tb    <- feols(n_taobao_village ~ post | town_code + year, data = p, cluster = ~county)
print(etable(s_light, s_pop, s_tb, se.below = TRUE,
             headers = c("log灯光","log人口","淘宝村数")))

## ---------- 2. Sun-Abraham 事件研究（灯光） ----------
cat("\n---- 表2 Sun-Abraham 事件研究 (log灯光) ----\n")
es <- feols(loglight ~ sunab(Gf, year, ref.p = c(-1, .F)) | town_code + year,
            data = p, cluster = ~county)
print(es)
agg <- aggregate(es, "att")
cat("\n聚合ATT(灯光):\n"); print(agg)
# 导出事件时点系数供作图
co <- summary(es, agg = FALSE)$coeftable
es_dt <- data.table(term = rownames(co), est = co[,1], se = co[,2])
es_dt <- es_dt[grepl("year::", term)]
es_dt[, evt := as.integer(gsub(".*year::(-?[0-9]+).*", "\\1", term))]
fwrite(es_dt[order(evt)], file.path(OUT, "eventstudy_light.csv"))

## ---------- 3. 事件研究 人口 & 淘宝村 ----------
cat("\n---- 表3 事件研究聚合ATT：人口 / 淘宝村 ----\n")
es_pop <- feols(logpop ~ sunab(Gf, year, ref.p = c(-1, .F)) | town_code + year,
                data = p, cluster = ~county)
es_tb  <- feols(n_taobao_village ~ sunab(Gf, year, ref.p = c(-1, .F)) | town_code + year,
                data = p, cluster = ~county)
cat("人口 ATT:\n"); print(aggregate(es_pop, "att"))
cat("淘宝村 ATT:\n"); print(aggregate(es_tb, "att"))

## ---------- 4. 设计B：认定增量（限处理镇样本） ----------
cat("\n---- 表4 设计B：建设镇内 认定 vs 未认定 (post_cert) ----\n")
pt <- p[treated == 1]
pt[, post_cert := as.integer(certified == 1 & year >= G)]
pt[, post_build := as.integer(year >= G)]
b1 <- feols(loglight ~ post_build + post_cert | town_code + year, data = pt, cluster = ~county)
print(etable(b1, se.below = TRUE))
cat("解读：post_build=建设效应基准；post_cert=认定的增量效应(conditional-on-creation)\n")

## ---------- 5. 异质性：产粮大县 ----------
cat("\n---- 表5 异质性 by 主导批次早晚（2018-2020早 vs 2021+晚） ----\n")
p[, early := as.integer(!is.na(G) & G <= 2020)]
p[, post_early := post * early]
h1 <- feols(loglight ~ post + post_early | town_code + year, data = p, cluster = ~county)
print(etable(h1, se.below = TRUE))

sink()
cat("results_paper1.txt written\n")

## ---------- 图：事件研究 ----------
es_dt <- fread(file.path(OUT, "eventstudy_light.csv"))
es_dt <- es_dt[evt >= -6 & evt <= 6]
png(file.path(OUT, "fig_eventstudy_light.png"), width = 1000, height = 640, res = 120)
plot(es_dt$evt, es_dt$est, type = "b", pch = 19, col = "#2c7fb8",
     ylim = range(c(es_dt$est - 1.96*es_dt$se, es_dt$est + 1.96*es_dt$se)),
     xlab = "事件时间（相对建设年）", ylab = "log灯光 相对-1期",
     main = "产业强镇建设的动态效应（Sun-Abraham）")
abline(h = 0, lty = 2); abline(v = -0.5, lty = 3, col = "grey")
arrows(es_dt$evt, es_dt$est - 1.96*es_dt$se, es_dt$evt, es_dt$est + 1.96*es_dt$se,
       length = 0.03, angle = 90, code = 3, col = "#2c7fb8")
dev.off()
cat("figure written\n")
