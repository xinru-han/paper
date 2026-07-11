# =============================================================================
# 17_figures.R — F2 binned first stage; F3 coefficient forest (OLS/RF/2SLS+AR);
# F4 price gradient by perishability; F5 permutation-placebo distribution;
# F7 forest CATE partial dependence. (F1 village map skipped: coordinates are
# never written to outputs — privacy red line; a county-aggregated table
# replaces it, see t11b.)
# =============================================================================
source("/root/data/Paper/食物消费数据/paper3-foodenv/code/00_setup.R")
suppressPackageStartupMessages(library(ggplot2))
con <- log_open("17_figures.log")
gsave <- function(p, f, w = 7, h = 5) { ggsave(file.path(DIR_FIG, f), p, width = w, height = h, dpi = 200); cat("  [fig]", f, "\n") }

vg <- fread(file.path(DIR_DERIV, "p3_village.csv"), colClasses = list(character = "xzc12"))
vg[, county_id := substr(xzc12, 1, 6)]

# ---- F2 binned first stage (residualized on ZV + county FE) -----------------
m_x <- feols(rhs(IV_RF, ZV, fe = "county_id"), vg); m_y <- feols(rhs(TREAT, ZV, fe = "county_id"), vg)
rr <- data.table(x = resid(m_x, na.rm = FALSE)[as.integer(obs(m_x))],
                 y = resid(m_y, na.rm = FALSE)[as.integer(obs(m_y))])
rr <- data.table(x = resid(m_x), y = resid(m_y))
rr[, bin := cut(x, quantile(x, 0:20/20), include.lowest = TRUE)]
bb <- rr[, .(x = mean(x), y = mean(y), n = .N), by = bin]
p2 <- ggplot(bb, aes(x, y)) + geom_point(aes(size = n), alpha = .7) +
  geom_smooth(data = rr, method = "lm", se = TRUE, color = "firebrick") +
  labs(x = "Detour (town corridor, residualized)", y = "Retail thickness PC1 (residualized)",
       title = "F2  First stage, within county | conditioning set", size = "villages") +
  theme_minimal()
gsave(p2, "fig2_first_stage_binned.png")

# ---- F3 coefficient forest --------------------------------------------------
t3 <- fread(file.path(DIR_TAB, "t3_main.csv"))
fd <- rbindlist(list(
  t3[, .(outcome, est = rf_b, lo = rf_b - 1.96*rf_se, hi = rf_b + 1.96*rf_se, model = "Reduced form (detour, primary)")],
  t3[, .(outcome, est = ols_b, lo = ols_b - 1.96*ols_se, hi = ols_b + 1.96*ols_se, model = "OLS (retail PC1)")],
  t3[, .(outcome, est = iv_b, lo = ar_lo, hi = ar_hi, model = "2SLS (AR 95% CI)")]))
fd[, outcome := factor(outcome, c("fgds10","fvs","hdds12"),
                       c("FGDS-10 (person)","Food variety (person)","HDDS-12 (household)"))]
p3 <- ggplot(fd, aes(est, outcome, color = model)) +
  geom_vline(xintercept = 0, linetype = 2) +
  geom_pointrange(aes(xmin = lo, xmax = hi), position = position_dodge(width = .5)) +
  labs(x = "effect per 1sd exposure", y = NULL, color = NULL,
       title = "F3  Main results: a precisely estimated null") +
  theme_minimal() + theme(legend.position = "bottom")
gsave(p3, "fig3_coef_forest.png", w = 8)

# ---- F4 price gradient by perishability -------------------------------------
t5a <- fread(file.path(DIR_TAB, "t5a_price_by_category.csv"))[!is.na(b)]
t5a[, lab2 := paste0(lab, ifelse(perishable == 1, " (perishable)", ""))]
p4 <- ggplot(t5a, aes(reorder(lab2, perishable * 10 + b), b, color = factor(perishable))) +
  geom_hline(yintercept = 0, linetype = 2) +
  geom_pointrange(aes(ymin = b - 1.96*se, ymax = b + 1.96*se)) +
  coord_flip() + scale_color_manual(values = c("0" = "grey40", "1" = "firebrick"), guide = "none") +
  labs(x = NULL, y = "d ln(price) per 1sd detour",
       title = "F4  Village paid prices vs terrain isolation (reduced form)") +
  theme_minimal()
gsave(p4, "fig4_price_gradient.png")

# ---- F5 permutation distribution --------------------------------------------
pf <- fread(file.path(DIR_DERIV, "perm_fs_draws.csv"))
treal <- fread(file.path(DIR_TAB, "t7c_permutation_corridors.csv"))[stat %like% "first stage", t_real]
p5 <- ggplot(pf, aes(t_perm)) + geom_histogram(bins = 40, fill = "grey70") +
  geom_vline(xintercept = treal, color = "firebrick", linewidth = 1) +
  labs(x = "placebo first-stage t (distance-decile permutations)",
       title = sprintf("F5  Permutation corridors: real |t| at perm p = %.3f",
                       fread(file.path(DIR_TAB, "t7c_permutation_corridors.csv"))[1, perm_p])) +
  theme_minimal()
gsave(p5, "fig5_permutation_placebo.png")

# ---- F7 forest partial dependence -------------------------------------------
pd <- fread(file.path(DIR_TAB, "t11_forest_partial_dependence.csv"))
p7 <- ggplot(pd, aes(quartile, mean_cate, group = feature, color = feature)) +
  geom_hline(yintercept = 0, linetype = 2) + geom_line() + geom_point() +
  labs(x = "feature quartile", y = "mean conditional contrast (FGDS-10)",
       title = "F7  Exploratory forest heterogeneity (flat = no targeting signal)") +
  theme_minimal() + theme(legend.position = "bottom")
gsave(p7, "fig7_forest_pd.png", w = 8)
log_close(con)
