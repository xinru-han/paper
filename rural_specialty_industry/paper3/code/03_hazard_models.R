#!/usr/bin/env Rscript
# Paper 3 计量：超级明星进入的政策效应——培育还是追认
# 离散时间风险模型(logit) + 剂量反应 + 异质性；培育vs追认时序见 02/04。
suppressMessages({library(data.table); library(fixest)})
setFixest_notes(FALSE)
OUT <- "/root/paper/rural_specialty_industry/paper3/output"
p <- fread(file.path(OUT, "town_panel.csv"), encoding = "UTF-8")

# 变量准备
p[, `:=`(
  loglight = log1p(light_sum_2019),
  loglight15 = log1p(light_sum_2015),
  logagri = log1p(agri_firms_pre),
  logcoop = log1p(coop_pre),
  yearf = factor(year),
  prov = substr(county_code, 1, 2)
)]
p[is.na(loglight), loglight := 0]
p[is.na(loglight15), loglight15 := 0]
p[, layers := qz_pre2020 + park_pre + tqz_pre + brand_pre + mte_pre + gi_pre]

sink(file.path(OUT, "results_paper3.txt"))
cat("==== Paper 3：乡村产业超级明星的政策效应 ====\n")
cat("面板：镇×年(2020-2022) 离散时间风险集\n")
cat(sprintf("观测=%d 镇=%d 十亿元镇进入=%d 亿元村进入=%d\n\n",
            nrow(p), uniqueN(p$town_code), sum(p$ten_enter), sum(p$yi_enter)))

## ---------- 表1 描述：进入率 by 政策 ----------
cat("---- 表1 十亿元镇进入率 by 先期政策(pre-2020) ----\n")
for (v in c("qz_pre2020","park_pre","tqz_pre","brand_pre","gi_pre","grain800")) {
  a <- p[, .(rate = mean(ten_enter), n = .N), by = v][order(get(v))]
  cat(sprintf("%-12s  0:%.4f(%d)  1:%.4f(%d)\n", v,
              a$rate[1], a$n[1], a$rate[2], a$n[2]))
}

## ---------- 表2 十亿元镇进入 离散时间风险(logit) ----------
cat("\n---- 表2 十亿元镇进入 discrete-time logit ----\n")
m1 <- feglm(ten_enter ~ qz_pre2020 + park_pre + tqz_pre + brand_pre + gi_pre + grain800 | yearf,
            data = p, family = binomial, cluster = ~county_code)
m2 <- feglm(ten_enter ~ qz_pre2020 + park_pre + tqz_pre + brand_pre + gi_pre + grain800 +
              loglight + logagri + logcoop | yearf,
            data = p, family = binomial, cluster = ~county_code)
m3 <- feglm(ten_enter ~ qz_pre2020 + park_pre + tqz_pre + brand_pre + gi_pre + grain800 +
              loglight + logagri + logcoop | yearf + prov,
            data = p, family = binomial, cluster = ~county_code)
print(etable(m1, m2, m3, se.below = TRUE,
             dict = c(qz_pre2020="产业强镇(镇)", park_pre="现代产业园(县)",
                      tqz_pre="特优区(县)", brand_pre="品牌目录(县)", gi_pre="地理标志(县)",
                      grain800="产粮大县800", loglight="log灯光2019",
                      logagri="log涉农企业", logcoop="log合作社")))

## ---------- 表3 亿元村(镇内出现) ----------
cat("\n---- 表3 亿元村镇进入 discrete-time logit ----\n")
y1 <- feglm(yi_enter ~ qz_pre2020 + park_pre + tqz_pre + brand_pre + gi_pre + grain800 | yearf,
            data = p, family = binomial, cluster = ~county_code)
y2 <- feglm(yi_enter ~ qz_pre2020 + park_pre + tqz_pre + brand_pre + gi_pre + grain800 +
              loglight + logagri + logcoop | yearf + prov,
            data = p, family = binomial, cluster = ~county_code)
print(etable(y1, y2, se.below = TRUE))

## ---------- 表4 政策叠加剂量反应 ----------
cat("\n---- 表4 政策层级(0-6)剂量反应 ----\n")
p[, layersf := factor(pmin(layers, 5))]
d1 <- feglm(ten_enter ~ layersf + loglight + logagri | yearf + prov,
            data = p, family = binomial, cluster = ~county_code)
print(etable(d1, se.below = TRUE))
cat("\n各层级镇数与进入率:\n")
print(p[year==2020, .(n_towns=.N), by=layers][order(layers)])

## ---------- 表5 异质性：产粮大县×强镇 ----------
cat("\n---- 表5 异质性 产粮大县×政策(锦上添花 vs 雪中送炭) ----\n")
h1 <- feglm(ten_enter ~ qz_pre2020*grain800 + park_pre + loglight + logagri | yearf + prov,
            data = p, family = binomial, cluster = ~county_code)
print(etable(h1, se.below = TRUE))

## ---------- LPM 稳健性（县固定效应） ----------
cat("\n---- 稳健性：LPM 县固定效应 ----\n")
l1 <- feols(ten_enter ~ qz_pre2020 + park_pre + tqz_pre + brand_pre + gi_pre +
              loglight + logagri | county_code + yearf,
            data = p, cluster = ~county_code)
print(etable(l1, se.below = TRUE))

sink()
cat("results_paper3.txt written\n")

## ---------- 图：政策层级梯度 ----------
grad <- p[year == 2020, .(rate = mean(ten_enter), yi = mean(yi_enter), n = .N), by = layers][order(layers)]
fwrite(grad, file.path(OUT, "gradient_by_layers.csv"))
png(file.path(OUT, "fig_gradient.png"), width = 900, height = 600, res = 120)
barplot(grad$rate*1000, names.arg = grad$layers, col = "#2c7fb8",
        xlab = "先期政策叠加层数", ylab = "十亿元镇进入率(‰)",
        main = "政策叠加与超级明星涌现：剂量反应")
dev.off()

## ---------- 图：培育vs追认时序 ----------
tim <- fread(file.path(OUT, "timing_qz_vs_entry.csv"))
tb <- tim[!is.na(gap_ten), .N, by = gap_ten][order(gap_ten)]
png(file.path(OUT, "fig_timing.png"), width = 900, height = 600, res = 120)
cols <- ifelse(tb$gap_ten < 0, "#2c7fb8", "#d95f0e")
barplot(tb$N, names.arg = tb$gap_ten, col = cols,
        xlab = "强镇授牌年 - 十亿元镇进入年", ylab = "镇数",
        main = "培育(蓝,先授牌) vs 追认(橙,后授牌)")
dev.off()
cat("figures written\n")
