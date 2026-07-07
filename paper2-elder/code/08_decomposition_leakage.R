# =============================================================================
# 08_decomposition_leakage.R — B3 reconciliation decomposition + leakage rate
# For each living arrangement k (vs base = with non-elder adults):
#   Delta_k(elder fgds10) = phi1 * Delta_k(HDDS)   [pass-through component]
#                         + allocation residual    [distribution component]
# Leakage rate (three-generation headline):
#   leak = 1 - (phi1 * Delta_HDDS) / Delta_HDDS_effect_on_elder_upper
# Operational definition (pre-registered §16): the provisioning gain is the
# A-line three-gen HDDS effect (b_A); its expected elder-intake value is
# phi1*b_A; the realized elder gain is the reduced-form elder fgds10 effect
# (b_R). leak = 1 - b_R / (phi1_upper * b_A) is ill-posed when phi1*b_A is the
# benchmark, so we report: pass-through share = b_R / b_A (in FGDS units per
# HDDS unit) vs phi1 (the within-sample marginal pass-through), and
#   leakage = 1 - b_R / b_A  when both in comparable units, with
# village-block-bootstrap CIs. Heterogeneity: elder-cook, children, income.
# Outputs: T12 (decomposition), T13 (leakage + heterogeneity), fig8 waterfall
# =============================================================================
source("/root/data/Paper/食物消费数据/paper2-elder/code/00_setup.R")
suppressPackageStartupMessages({ library(fixest); library(ggplot2) })

per <- fread(file.path(DIR_DERIV, "person_analysis.csv"), colClasses = list(character = c("nhCode","pid","xzc12")))
hh  <- fread(file.path(DIR_DERIV, "hh_analysis.csv"),  colClasses = list(character = c("nhCode","xzc12")))
LA_LEVELS <- c("cohabit_nonelder","elder_only_multi","threegen","elder_alone","elder_child","other")

eld <- per[elderly == 1 & !is.na(num(fgds10)) & living_arrangement %in% LA_LEVELS]
eld[, `:=`(fgds10 = num(fgds10), hdds = num(hdds12_household),
           LA = relevel(factor(living_arrangement, levels = LA_LEVELS), ref = "cohabit_nonelder"),
           county_year = paste(countyn, data_year))]
eld[is.na(main_cook), main_cook := 0]
hh[, `:=`(hdds12 = num(hdds12), county_year = paste(countyn, data_year),
          LA = relevel(factor(living_arrangement, levels = LA_LEVELS), ref = "cohabit_nonelder"))]

CT_H <- "ln_income + any_elder_80 + n_elderly"

# one full computation of all decomposition quantities on a data pair
compute_all <- function(hh_d, eld_d) {
  # (a) A line: LA -> household HDDS
  mA <- feols(as.formula(paste("hdds12 ~ LA +", CT_H, "| county_year")), data = hh_d, cluster = ~xzc12)
  # (b) pass-through: HDDS -> elder fgds10 (pooled phi1)
  mP <- feols(fgds10 ~ hdds + LA + female + main_cook + ln_income | county_year, data = eld_d, cluster = ~xzc12)
  # (c) reduced form: LA -> elder fgds10
  mR <- feols(fgds10 ~ LA + female + main_cook + ln_income | county_year, data = eld_d, cluster = ~xzc12)
  bA <- coef(mA); bR <- coef(mR); phi1 <- coef(mP)["hdds"]
  las <- paste0("LA", setdiff(LA_LEVELS, "cohabit_nonelder"))
  out <- rbindlist(lapply(las, function(trm) {
    if (!(trm %in% names(bA) && trm %in% names(bR))) return(NULL)
    data.table(arrangement = sub("^LA","",trm),
               dHDDS = bA[trm], phi1 = phi1,
               passthrough_component = phi1 * bA[trm],
               total_elder_effect = bR[trm],
               allocation_residual = bR[trm] - phi1 * bA[trm])
  }))
  out[, leakage_rate := fifelse(abs(phi1 * dHDDS) > 1e-8, 1 - total_elder_effect/(dHDDS), NA_real_)]
  # leakage for three-gen headline: share of the HDDS gain (in fgds10-equivalent
  # units at 1:1 group mapping) not showing up in elder intake
  out
}

dec <- compute_all(hh, eld)

# ---- village-block bootstrap CIs ---------------------------------------------
set.seed(4); B <- 400
vils <- unique(hh$xzc12)
boot <- vector("list", B)
for (b in seq_len(B)) {
  sv <- table(sample(vils, length(vils), replace = TRUE))
  hb <- rbindlist(lapply(names(sv), function(v) hh[xzc12 == v][rep(1:.N, sv[[v]])]), fill = TRUE)
  eb <- rbindlist(lapply(names(sv), function(v) eld[xzc12 == v][rep(1:.N, sv[[v]])]), fill = TRUE)
  boot[[b]] <- tryCatch(compute_all(hb, eb), error = function(e) NULL)
}
bootdt <- rbindlist(boot[!sapply(boot, is.null)])
ci <- bootdt[, .(pass_lo = quantile(passthrough_component, .025, na.rm = TRUE),
                 pass_hi = quantile(passthrough_component, .975, na.rm = TRUE),
                 alloc_lo = quantile(allocation_residual, .025, na.rm = TRUE),
                 alloc_hi = quantile(allocation_residual, .975, na.rm = TRUE),
                 leak_lo = quantile(leakage_rate, .025, na.rm = TRUE),
                 leak_hi = quantile(leakage_rate, .975, na.rm = TRUE)), by = arrangement]
t12 <- merge(dec, ci, by = "arrangement", all.x = TRUE)
wtab(t12, "table12_decomposition.csv")

# ---- headline: three-generation leakage --------------------------------------
tg <- t12[arrangement == "threegen"]
headline <- sprintf(paste0(
  "Three-generation co-residence raises household HDDS by %.3f groups; the marginal pass-through of ",
  "one HDDS group to elder FGDS-10 is %.3f. The elder-level total effect is %.3f groups, i.e. %.0f%% of the ",
  "household provisioning gain reaches the older adult's own 48h intake; leakage = %.0f%% (95%% CI %.0f-%.0f%%)."),
  tg$dHDDS, tg$phi1, tg$total_elder_effect, 100*tg$total_elder_effect/tg$dHDDS,
  100*tg$leakage_rate, 100*tg$leak_lo, 100*tg$leak_hi)

# ---- leakage heterogeneity (elder cook / children / income) -------------------
het_groups <- list(
  elder_cook    = quote(main_cook == 1),
  elder_notcook = quote(main_cook == 0),
  low_income    = quote(ln_income <= median(ln_income, na.rm = TRUE)),
  high_income   = quote(ln_income >  median(ln_income, na.rm = TRUE)))
het <- rbindlist(lapply(names(het_groups), function(g) {
  sub_e <- eld[eval(het_groups[[g]])]
  res <- tryCatch(compute_all(hh, sub_e)[arrangement == "threegen"], error = function(e) NULL)
  if (is.null(res)) return(NULL)
  res[, group := g]; res
}), fill = TRUE)
wtab(het, "table13_leakage_heterogeneity.csv")

# ---- fig8: waterfall ----------------------------------------------------------
wf <- data.table(
  step = factor(c("Household provisioning gain\n(HDDS, A line)",
                  "Expected elder gain\n(phi1 x provisioning)",
                  "Realized elder gain\n(reduced form)"),
                levels = c("Household provisioning gain\n(HDDS, A line)",
                           "Expected elder gain\n(phi1 x provisioning)",
                           "Realized elder gain\n(reduced form)")),
  value = c(tg$dHDDS, tg$passthrough_component, tg$total_elder_effect))
p8 <- ggplot(wf, aes(step, value)) +
  geom_col(fill = c("steelblue","goldenrod","firebrick"), alpha = .75, width = .55) +
  geom_text(aes(label = sprintf("%.3f", value)), vjust = -0.4, size = 4) +
  labs(x = NULL, y = "Dietary diversity groups (48h)",
       title = "From the household table to the elder's bowl: three-generation gain",
       subtitle = "Waterfall of the provisioning gain and what reaches older adults") +
  theme_minimal(base_size = 12)
ggsave(file.path(DIR_FIG, "fig8_waterfall_decomposition.png"), p8, width = 8, height = 5.5, dpi = 200)

writeLines(c("# B3 decomposition & leakage", "", headline, "",
             "## By-arrangement decomposition", paste(capture.output(print(t12)), collapse = "\n"),
             "", "## Heterogeneity (three-gen leakage)", paste(capture.output(print(het)), collapse = "\n")),
           file.path(DIR_REP, "decomposition_leakage.md"))
cat("DECOMPOSITION OK\n"); cat(headline, "\n")
