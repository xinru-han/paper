# Paper 9 script 97: quality-adjusted cost-of-living index & inflation inequality.
#  Per income decile x month: paid index (median uv by category, decile-specific)
#  vs market base index (p_base), both Stone-weighted with decile base-period
#  weights. Difference = inflation absorbed/added by the quality margin.
source("/root/data/Paper/央视数据/paper9-easiq/code/00_setup.R")
suppressPackageStartupMessages(library(ggplot2))

qd <- readRDS(file.path(DIR_INT, "quality_panel.rds"))
spA <- readRDS(file.path(DIR_INT, "stageA_panel.rds"))
# income has 5 discrete bands -> use them directly as the 5 groups
qd[, dec := factor(paste0("Q", frank(ln_inc, ties.method = "dense")))]
qd[is.na(ln_inc), dec := NA]
pb <- fread(file.path(DIR_INT, "base_price_prov_month.csv.gz"), encoding = "UTF-8")

## decile x month x category paid price (median uv) and base price (national mean)
paid <- qd[!is.na(dec), .(uv_med = median(uv), X = sum(X)), by = .(dec, ym, Category)]
base <- pb[Category %in% PK13, .(p_base = mean(p_base)), by = .(ym, Category)]
w0 <- qd[ym <= "2020-06" & !is.na(dec), .(w = sum(X)), by = .(dec, Category)]
w0[, w := w / sum(w), by = dec]
p0 <- paid[ym <= "2020-06", .(uv0 = median(uv_med)), by = .(dec, Category)]
b0 <- base[ym <= "2020-06", .(p0 = median(p_base)), by = Category]

idx <- merge(paid, w0, by = c("dec","Category"))
idx <- merge(idx, p0, by = c("dec","Category"))
idx <- merge(idx, base, by = c("ym","Category"))
idx <- merge(idx, b0, by = "Category")
ser <- idx[, .(paid_idx = sum(w * log(uv_med / uv0)),
               base_idx = sum(w * log(p_base / p0))), by = .(dec, ym)]
ser[, quality_wedge := paid_idx - base_idx]
fwrite(ser, file.path(DIR_TAB, "t9_qcpi_series.csv"))

t9 <- ser[ym >= "2022-01", .(paid_pct = 100 * mean(paid_idx), base_pct = 100 * mean(base_idx),
                             wedge_pct = 100 * mean(quality_wedge)), by = dec][order(dec)]
fwrite(t9, file.path(DIR_TAB, "t9a_qcpi_2022_by_decile.csv"))
logmsg("97: 2022 quality wedge by quintile: ", paste(round(t9$wedge_pct, 2), collapse = " / "))

lkd <- fread(file.path(P8, "data/lookups/lockdown_windows.csv"), encoding = "UTF-8")
ggsave(file.path(DIR_FIG, "fig7_effective_inflation.png"), width = 9, height = 6, dpi = 150,
  plot = ggplot(ser, aes(as.IDate(paste0(ym, "-15")), 100 * paid_idx, color = dec)) +
    geom_line() +
    geom_line(aes(y = 100 * base_idx), color = "grey40", linetype = 2) +
    annotate("rect", xmin = as.IDate("2022-03-28"), xmax = as.IDate("2022-06-01"),
             ymin = -Inf, ymax = Inf, alpha = .12, fill = "red") +
    labs(x = NULL, y = "cumulative log index x100 (vs 2020H1)", color = "income quintile",
         title = "Effective (paid) vs market-base food price index by income quintile",
         subtitle = "dashed grey = market base; shaded = Shanghai lockdown window") +
    theme_minimal(base_size = 11))
logmsg("97: done")
