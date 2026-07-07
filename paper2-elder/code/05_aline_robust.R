# =============================================================================
# 05_aline_robust.R — Task 4/7: balance & overlap diagnostics, IPW/entropy/
# nearest-neighbor matching, permutation inference, Oster bounds,
# leave-one-province. Treatment: three-generation vs with-non-elder-adults.
# Tables: T7 (estimator comparison), T8 (balance), T9a (sensitivity)
# Figures: fig3 love plot, fig4 PS overlap, fig5 permutation, fig6 leave-one-prov
# =============================================================================
source("/root/data/Paper/食物消费数据/paper2-elder/code/00_setup.R")
suppressPackageStartupMessages({ library(fixest); library(WeightIt); library(cobalt); library(ggplot2) })

hh <- fread(file.path(DIR_DERIV, "hh_analysis.csv"), colClasses = list(character = c("nhCode","xzc12")))
for (v in c("hdds12","any_elder_80","HB2","HB5","HB8")) hh[, (v) := num(get(v))]
d <- hh[living_arrangement %in% c("threegen","cohabit_nonelder")]
d[, treat := as.integer(living_arrangement == "threegen")]
d[, county_year := paste(countyn, data_year)]
XV <- c("ln_income","any_elder_80","n_elderly","HB2","HB5","HB8",
        "market_access_index","retail_thickness_index")
d <- d[complete.cases(d[, c("hdds12","treat", XV), with = FALSE])]
d[, provy := paste(provn, data_year)]
cat(sprintf("Analysis sample: %d (treated %d, control %d)\n", nrow(d), sum(d$treat), sum(1-d$treat)))

fml_ps <- as.formula(paste("treat ~", paste(XV, collapse = " + "), "+ factor(provy)"))
res <- list()

# ---- (0) OLS benchmark -------------------------------------------------------
m0 <- feols(as.formula(paste("hdds12 ~ treat +", paste(XV, collapse = " + "), "| county_year")),
            data = d, cluster = ~xzc12)
res$OLS_countyFE <- tidy_fe(m0, "^treat")

# ---- (1) IPW (ATT) -----------------------------------------------------------
w_ipw <- weightit(fml_ps, data = d, method = "glm", estimand = "ATT")
m1 <- feols(hdds12 ~ treat, data = d, weights = w_ipw$weights, cluster = ~xzc12)
res$IPW_ATT <- tidy_fe(m1, "^treat")

# ---- (2) entropy balancing (ATT) ---------------------------------------------
w_eb <- tryCatch(weightit(fml_ps, data = d, method = "ebal", estimand = "ATT"), error = function(e) NULL)
if (!is.null(w_eb)) {
  m2 <- feols(hdds12 ~ treat, data = d, weights = w_eb$weights, cluster = ~xzc12)
  res$EntropyBal_ATT <- tidy_fe(m2, "^treat")
}

# ---- (3) 1:1 nearest-neighbor PS matching with caliper -----------------------
ps <- fitted(glm(fml_ps, data = d, family = binomial))
d[, ps := ps]
cal <- 0.2 * sd(qlogis(pmin(pmax(ps, 1e-6), 1 - 1e-6)))
tr <- which(d$treat == 1); ct <- which(d$treat == 0)
lps <- qlogis(pmin(pmax(d$ps, 1e-6), 1 - 1e-6))
used <- rep(FALSE, length(ct)); match_id <- rep(NA_integer_, length(tr))
for (i in order(-d$ps[tr])) {                      # match high-PS treated first
  dist <- abs(lps[tr[i]] - lps[ct]); dist[used] <- Inf
  j <- which.min(dist)
  if (is.finite(dist[j]) && dist[j] <= cal) { match_id[i] <- ct[j]; used[j] <- TRUE }
}
mt <- data.table(tr = tr, ct = match_id)[!is.na(ct)]
md <- d[c(mt$tr, mt$ct)][, pair := rep(seq_len(nrow(mt)), 2)]
m3 <- feols(hdds12 ~ treat, data = md, cluster = ~pair)
res$NN_match_caliper <- tidy_fe(m3, "^treat")
cat(sprintf("Matched %d of %d treated (caliper %.3f on logit PS)\n", nrow(mt), length(tr), cal))

# ---- (4) AIPW (doubly robust, ATT) -------------------------------------------
mu1 <- lm(as.formula(paste("hdds12 ~", paste(XV, collapse = "+"), "+ factor(provy)")), data = d[treat == 1])
mu0 <- lm(as.formula(paste("hdds12 ~", paste(XV, collapse = "+"), "+ factor(provy)")), data = d[treat == 0])
m1hat <- predict(mu1, newdata = d); m0hat <- predict(mu0, newdata = d)
p1 <- mean(d$treat)
att_scores <- with(d, (treat * (hdds12 - m0hat) - (1 - treat) * ps/(1 - ps) * (hdds12 - m0hat)) / p1)
att <- mean(att_scores)
# cluster-robust SE via village-block bootstrap
set.seed(1); B <- 500
vils <- unique(d$xzc12)
boot_att <- replicate(B, {
  # proper with-replacement cluster (village) resampling: replicate each village
  # as many times as it is drawn, not a set-membership subsample (%in% would keep
  # each village at most once and understate the bootstrap variance).
  sv <- table(sample(vils, length(vils), replace = TRUE))
  bs <- rbindlist(lapply(names(sv), function(v) d[xzc12 == v][rep(1:.N, sv[[v]])]), fill = TRUE)
  # recompute scores with fixed nuisance fits (score bootstrap approximation)
  m0b <- predict(mu0, newdata = bs)
  with(bs, mean((treat * (hdds12 - m0b) - (1 - treat) * ps/(1 - ps) * (hdds12 - m0b)) / mean(treat)))
})
res$AIPW_ATT <- data.table(term = "treat", est = att, se = sd(boot_att),
                           t = att/sd(boot_att), p = 2*pnorm(-abs(att/sd(boot_att))), n = nrow(d))

t7 <- rbindlist(lapply(names(res), function(nm) copy(res[[nm]])[, estimator := nm]), fill = TRUE)
wtab(t7, "table7_estimator_comparison.csv")

# ---- T8 + fig3/4: balance & overlap ------------------------------------------
bt <- bal.tab(fml_ps, data = d, weights = list(IPW = w_ipw, EB = w_eb), un = TRUE, s.d.denom = "treated")
b8 <- as.data.table(bt$Balance, keep.rownames = "covariate")
wtab(b8, "table8_balance_smd.csv")
lp <- love.plot(bt, threshold = .1, abs = TRUE, var.order = "unadjusted",
                title = "Covariate balance: three-generation vs with-non-elder-adult households")
ggsave(file.path(DIR_FIG, "fig3_love_plot.png"), lp, width = 8, height = 6, dpi = 200)
p4 <- ggplot(d, aes(x = ps, fill = factor(treat))) +
  geom_density(alpha = .4) +
  scale_fill_manual(values = c("grey50","firebrick"), labels = c("With non-elder adults","Three generations"), name = NULL) +
  labs(x = "Propensity score", y = "Density", title = "Propensity-score overlap") +
  theme_minimal(base_size = 12)
ggsave(file.path(DIR_FIG, "fig4_ps_overlap.png"), p4, width = 7.5, height = 5, dpi = 200)

# ---- (5) permutation inference (within-village reshuffle, 1000 draws) --------
obs <- coef(m0)["treat"]
set.seed(2)
perm <- replicate(1000, {
  dp <- copy(d)[, treat := sample(treat), by = xzc12]
  coef(feols(as.formula(paste("hdds12 ~ treat +", paste(XV, collapse = "+"), "| county_year")), data = dp))["treat"]
})
# unbiased Monte-Carlo permutation p-value: (1 + #{|perm| >= |obs|}) / (1 + B)
p_perm <- (1 + sum(abs(perm) >= abs(obs))) / (1 + length(perm))
p5 <- ggplot(data.table(perm = perm), aes(perm)) +
  geom_histogram(bins = 50, fill = "steelblue", alpha = .7) +
  geom_vline(xintercept = obs, colour = "firebrick", linewidth = 1) +
  labs(x = "Permuted three-generation coefficient", y = "Count",
       title = sprintf("Permutation test (within-village reshuffle): p = %.3f", p_perm)) +
  theme_minimal(base_size = 12)
ggsave(file.path(DIR_FIG, "fig5_permutation.png"), p5, width = 7.5, height = 5, dpi = 200)

# ---- (6) Oster (2019) bounds --------------------------------------------------
mS <- lm(hdds12 ~ treat, data = d)                                # short
mL <- lm(as.formula(paste("hdds12 ~ treat +", paste(XV, collapse = "+"), "+ factor(provy)")), data = d)  # long
bS <- coef(mS)["treat"]; bL <- coef(mL)["treat"]
r2S <- summary(mS)$r.squared; r2L <- summary(mL)$r.squared
rmax <- min(1.3 * r2L, 1)
beta_star <- bL - 1 * (bS - bL) * (rmax - r2L) / (r2L - r2S)     # delta = 1
delta_b0 <- bL * (r2L - r2S) / ((bS - bL) * (rmax - r2L))        # delta for beta = 0
oster <- data.table(beta_short = bS, beta_long = bL, r2_short = r2S, r2_long = r2L,
                    rmax = rmax, beta_star_delta1 = beta_star, delta_for_beta0 = delta_b0)
wtab(oster, "table9a_oster_bounds.csv")

# ---- (7) leave-one-province ----------------------------------------------------
lop <- rbindlist(lapply(unique(d$provn), function(pv) {
  m <- feols(as.formula(paste("hdds12 ~ treat +", paste(XV, collapse = "+"), "| county_year")),
             data = d[provn != pv], cluster = ~xzc12)
  tidy_fe(m, "^treat")[, dropped := pv]
}))
wtab(lop, "table9b_leave_one_province.csv")
p6 <- ggplot(lop, aes(x = dropped, y = est)) +
  geom_point(size = 2.5) +
  geom_errorbar(aes(ymin = est - 1.96*se, ymax = est + 1.96*se), width = .15) +
  geom_hline(yintercept = coef(m0)["treat"], linetype = 2, colour = "firebrick") +
  labs(x = "Province dropped", y = "Three-generation coefficient",
       title = "Leave-one-province robustness (dashed = full sample)") +
  theme_minimal(base_size = 12)
ggsave(file.path(DIR_FIG, "fig6_leave_one_province.png"), p6, width = 8, height = 5, dpi = 200)

writeLines(c("# A-line robustness summary",
  sprintf("- Permutation p-value (1000 within-village reshuffles): %.3f", p_perm),
  sprintf("- Oster beta* (delta=1, Rmax=1.3 R2): %.3f (OLS long: %.3f); delta for beta=0: %.2f",
          beta_star, bL, delta_b0),
  sprintf("- Estimator range: %.3f to %.3f", min(t7$est), max(t7$est)),
  sprintf("- Matched sample: %d pairs of %d treated", nrow(mt), length(tr))),
  file.path(DIR_REP, "aline_robustness_summary.md"))
cat("A-LINE ROBUST OK\n"); print(t7[, .(estimator, est, se, p, n)])
