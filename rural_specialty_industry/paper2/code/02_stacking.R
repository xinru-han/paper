#!/usr/bin/env Rscript
# Paper 2 计量：认证叠加的边际回报（certification stacking）
suppressMessages({library(data.table); library(fixest)})
setFixest_notes(FALSE)
OUT <- "/root/paper/rural_specialty_industry/paper2/output"
p <- fread(file.path(OUT, "county_cat_panel.csv"), encoding = "UTF-8")

p[, `:=`(
  unit = paste(county_code, cat, sep = "_"),
  prov = substr(county_code, 1, 2),
  logfirms = log1p(n_firms),
  logcap = log1p(cap_wan),
  logcoop = log1p(n_coop),
  Gf = ifelse(is.na(first_cert_year), 10000L, as.integer(first_cert_year))
)]

sink(file.path(OUT, "results_paper2.txt"))
cat("==== Paper 2：认证叠加的边际回报 ====\n")
cat(sprintf("面板 县×品类×年: %d 行, 单元=%d, 年=%d-%d, 曾认证单元=%d\n\n",
            nrow(p), uniqueN(p$unit), min(p$year), max(p$year),
            uniqueN(p[any_cert==1]$unit)))

## ---------- 表1 首次认证的事件研究（第一块牌） ----------
cat("---- 表1 首次认证 Sun-Abraham 事件研究 (log涉农企业) ----\n")
es <- feols(logfirms ~ sunab(Gf, year, ref.p = c(-1, .F)) | unit + year^cat,
            data = p, cluster = ~county_code)
cat("聚合ATT:\n"); print(aggregate(es, "att"))
es_agg <- aggregate(es, agg = "year::(-?[0-9]+)")
es_dt <- data.table(term = rownames(es_agg), est = es_agg[,1], se = es_agg[,2])
es_dt[, evt := as.integer(gsub(".*?(-?[0-9]+).*", "\\1", term))]
es_dt <- es_dt[!is.na(evt)][order(evt)]
fwrite(es_dt, file.path(OUT, "eventstudy_firstcert.csv"))
print(es_dt)

## ---------- 表2 剂量反应：认证层数的边际回报 β^(k) ----------
cat("\n---- 表2 认证层数剂量反应 (log企业) ----\n")
p[, layf := factor(pmin(cert_layers, 4))]
d1 <- feols(logfirms ~ i(layf, ref = "0") | unit + year^cat, data = p, cluster = ~county_code)
d2 <- feols(logfirms ~ i(layf, ref = "0") | unit + year^prov, data = p, cluster = ~county_code)
print(etable(d1, d2, se.below = TRUE, headers = c("品类×年FE","省×年FE")))
cat("\n边际回报(相邻层差 β^k - β^{k-1}):\n")
co <- coef(d1); cs <- co[grepl("layf", names(co))]
cat(sprintf("β1=%.3f  β2=%.3f  β3=%.3f  β4=%.3f\n", cs[1], cs[2], cs[3], cs[4]))
mg <- c(cs[1], diff(cs))
cat(sprintf("边际: 第1块=%.3f 第2块=%.3f 第3块=%.3f 第4块=%.3f\n", mg[1], mg[2], mg[3], mg[4]))

## ---------- 表3 各认证类型的独立效应（同时进入） ----------
cat("\n---- 表3 各认证类型 stock 效应 ----\n")
for (pol in c("GI","名特优新","特优区","品牌目录")) {
  p[[paste0(pol,"_on")]] <- as.integer(!is.na(p[[paste0(pol,"_year")]]) &
                                         p$year >= p[[paste0(pol,"_year")]])
}
t1 <- feols(logfirms ~ GI_on + 名特优新_on + 特优区_on + 品牌目录_on | unit + year^cat,
            data = p, cluster = ~county_code)
print(etable(t1, se.below = TRUE,
             dict = c(GI_on="地理标志", 名特优新_on="名特优新",
                      特优区_on="特优区", 品牌目录_on="品牌目录")))

## ---------- 表4 其他结果：注册资本、合作社 ----------
cat("\n---- 表4 剂量反应：注册资本 / 合作社 ----\n")
c1 <- feols(logcap ~ i(layf, ref = "0") | unit + year^cat, data = p, cluster = ~county_code)
c2 <- feols(logcoop ~ i(layf, ref = "0") | unit + year^cat, data = p, cluster = ~county_code)
print(etable(c1, c2, se.below = TRUE, headers = c("log注册资本","log合作社")))

## ---------- 表5 异质性：锦上添花 vs 雪中送炭 ----------
cat("\n---- 表5 异质性 by 基期企业规模(高/低) ----\n")
base2010 <- p[year == 2010, .(base = log1p(n_firms)), by = unit]
p <- merge(p, base2010, by = "unit", all.x = TRUE)
p[, highbase := as.integer(base > median(base, na.rm = TRUE))]
h1 <- feols(logfirms ~ i(layf, ref="0") + i(layf, highbase, ref="0") | unit + year^cat,
            data = p, cluster = ~county_code)
print(etable(h1, se.below = TRUE))

sink()
cat("results written\n")

## ---------- 图：首次认证事件研究 + 剂量反应 ----------
es_dt <- fread(file.path(OUT, "eventstudy_firstcert.csv"))[evt >= -6 & evt <= 8]
png(file.path(OUT, "fig_firstcert_es.png"), width = 1000, height = 620, res = 120)
plot(es_dt$evt, es_dt$est, type="b", pch=19, col="#2c7fb8",
     ylim=range(c(es_dt$est-1.96*es_dt$se, es_dt$est+1.96*es_dt$se)),
     xlab="事件时间(相对首次认证)", ylab="log涉农企业 相对-1期",
     main="首次认证的动态效应")
abline(h=0,lty=2); abline(v=-0.5,lty=3,col="grey")
arrows(es_dt$evt, es_dt$est-1.96*es_dt$se, es_dt$evt, es_dt$est+1.96*es_dt$se,
       length=0.03, angle=90, code=3, col="#2c7fb8")
dev.off()

lay <- coef(d1)[grepl("layf", names(coef(d1)))]
se_lay <- se(d1)[grepl("layf", names(se(d1)))]
fwrite(data.table(layer=1:4, est=as.numeric(lay), se=as.numeric(se_lay)),
       file.path(OUT, "dose_response.csv"))
png(file.path(OUT, "fig_dose_response.png"), width=900, height=600, res=120)
bp <- barplot(as.numeric(lay), names.arg=1:4, col="#2c7fb8",
        xlab="累计认证层数", ylab="log涉农企业(相对0层)",
        main="认证叠加的剂量反应曲线")
arrows(bp, as.numeric(lay)-1.96*se_lay, bp, as.numeric(lay)+1.96*se_lay,
       length=0.03, angle=90, code=3)
dev.off()
cat("figures written\n")
