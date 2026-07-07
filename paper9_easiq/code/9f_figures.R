# Paper 9 script 9f: remaining figures — F1 theta(y) curves, F4 income gradient
# of quality vs quantity elasticity, F8 dairy ladder transition heatmap.
source("/root/data/Paper/央视数据/paper9-easiq/code/00_setup.R")
suppressPackageStartupMessages(library(ggplot2))

sa <- readRDS(file.path(DIR_INT, "stageA.rds"))
fe <- fread(file.path(DIR_TAB, "t3a_stageB_FE_coefs.csv"), encoding = "UTF-8")

## F1: theta_g(y) curves over the y interdecile range
ygrid <- seq(sa$y_pctl[1], sa$y_pctl[5], length.out = 50)
cur <- rbindlist(lapply(PK13, function(cc) {
  kap <- fe[category == cc & grepl("y\\^", term)][order(term), est]
  data.table(category = cc, y = ygrid,
             theta = sapply(ygrid, function(y0) theta_at(kap, y0)))
}))
ggsave(file.path(DIR_FIG, "fig1_theta_curves.png"), width = 10, height = 7, dpi = 150,
  plot = ggplot(cur, aes(y, theta)) + geom_line(color = "steelblue") +
    geom_hline(yintercept = 0, linetype = 2, linewidth = .3) +
    facet_wrap(~category, scales = "free_y") +
    labs(x = "implicit real expenditure y (p10-p90)", y = "quality elasticity theta_g(y)",
         title = "Quality Engel curves") + theme_minimal(base_size = 10))

## F4: income gradient — theta vs eta by income tercile (pooled PK13)
qd <- readRDS(file.path(DIR_INT, "quality_panel.rds"))
spA <- readRDS(file.path(DIR_INT, "stageA_panel.rds"))
qd <- merge(qd, spA[, .(ID, ym, y, vhat)], by = c("ID","ym"))  # qd already has ln_inc
qd[is.na(fsize), fsize := median(qd$fsize, na.rm = TRUE)]
qd[, inc_ter := cut(ln_inc, quantile(ln_inc, c(0, 1/3, 2/3, 1), na.rm = TRUE),
                    labels = c("T1","T2","T3"), include.lowest = TRUE)]
ZB <- "fsize + elderly + lock_days + ln_covid + cny_share + hot_days"
gr <- rbindlist(lapply(c("T1","T2","T3"), function(tt) rbindlist(lapply(
  c(quality = "r_prem", quantity = "lnQ"), function(dep) {
    m <- feols(as.formula(paste0(dep, " ~ y + ", ZB, " | ID^Category + prov_tier^ym")),
               data = qd[inc_ter == tt], cluster = ~ID, notes = FALSE)
    data.table(tercile = tt, margin = fifelse(dep == "r_prem", "quality (theta)", "quantity (eta)"),
               est = coef(m)["y"], se = se(m)["y"])
  }))))
fwrite(gr, file.path(DIR_TAB, "t11d_margin_income_gradient.csv"))
ggsave(file.path(DIR_FIG, "fig4_margin_gradient.png"), width = 7, height = 5, dpi = 150,
  plot = ggplot(gr, aes(tercile, est, group = margin, color = margin)) +
    geom_pointrange(aes(ymin = est - 1.96 * se, ymax = est + 1.96 * se)) + geom_line() +
    labs(x = "income tercile", y = "elasticity wrt y",
         title = "Quality vs quantity margin across the income distribution") +
    theme_minimal(base_size = 11))

## F8: dairy ladder month-to-month transition matrix (dominant subcategory)
dd <- fread(file.path(DIR_INT, "uv_hh_month_cat.csv.gz"), encoding = "UTF-8")[Category %in% DAIRY5]
dom <- dd[, .SD[which.max(X)], by = .(ID, ym)][, .(ID, ym, cat = Category)]
dom <- dom[order(ID, ym)][, cat_next := shift(cat, -1), by = ID][!is.na(cat_next)]
tm <- dom[, .N, by = .(cat, cat_next)][, share := N / sum(N), by = cat]
lad <- fread(file.path(DIR_LKP, "quality_ladder.csv"), encoding = "UTF-8")
ord <- lad[Category %in% DAIRY5][order(uv_med), Category]
tm[, `:=`(cat = factor(cat, ord), cat_next = factor(cat_next, ord))]
ggsave(file.path(DIR_FIG, "fig8_dairy_ladder_transitions.png"), width = 7, height = 6, dpi = 150,
  plot = ggplot(tm, aes(cat_next, cat, fill = share)) + geom_tile() +
    geom_text(aes(label = sprintf("%.2f", share)), size = 3) +
    scale_fill_gradient(low = "white", high = "#2166ac") +
    labs(x = "dominant dairy subcategory (t+1)", y = "dominant (t)",
         title = "Dairy quality-ladder transitions (subcats ordered by median uv)") +
    theme_minimal(base_size = 11))
logmsg("9f: done")
