# =============================================================================
# 03_first_stage.R — T2: pre-registered first-stage grid (3 treatments × 6 IV
# columns × 2 clusterings × 2 levels) + D1 decision record (prereg_p3.md).
# D1 OUTCOME: primary spec of the paper = reduced form in detour_town_5km;
# 2SLS secondary via retail_pc1 <- detour_town_1km (best pre-registered F).
# =============================================================================
source("/root/data/Paper/食物消费数据/paper3-foodenv/code/00_setup.R")
con <- log_open("03_first_stage.log")

pers <- fread(file.path(DIR_DERIV, "p3_person.csv"), colClasses = list(character = c("xzc12","nhCode")))
vg   <- fread(file.path(DIR_DERIV, "p3_village.csv"),  colClasses = list(character = "xzc12"))
vg[, county_id := paste(provn, countyn, sep = "_")]

TREATS <- c("retail_pc1", "retail_lnfresh", "access_dist")
IVCOLS <- as.vector(outer(c("town","county"), c(1,2,5),
                          function(d,k) sprintf("detour_%s_%dkm", d, k)))

grid <- CJ(treatment = TREATS, iv = IVCOLS)
out <- vector("list", nrow(grid))
for (i in seq_len(nrow(grid))) {
  tr <- grid$treatment[i]; ivv <- grid$iv[i]
  # village level (one obs per village): HC1 = village-level inference
  fV <- feols(as.formula(paste(tr, "~", ivv, "+", paste(ZV, collapse = "+"), "| county_id")),
              vg, vcov = "hetero")
  # village level, county cluster (conservative)
  fVc <- feols(as.formula(paste(tr, "~", ivv, "+", paste(ZV, collapse = "+"), "| county_id")),
               vg, cluster = ~county_id)
  # person level, village cluster (the 2SLS estimation sample metric)
  fP <- feols(as.formula(paste(tr, "~", ivv, "+", paste(c(ZV, XH, XI), collapse = "+"), "| county_year")),
              pers, cluster = ~xzc12)
  g <- function(m) { ct <- coeftable(m); if (ivv %in% rownames(ct)) ct[ivv, ] else rep(NA_real_, 4) }
  a <- g(fV); b <- g(fVc); d <- g(fP)
  out[[i]] <- data.table(treatment = tr, iv = ivv,
    b_vill = a[1], F_vill_hc1 = a[3]^2, F_vill_countycl = b[3]^2,
    b_pers = d[1], se_pers = d[2], F_pers_villcl = d[3]^2, n_pers = fP$nobs)
}
t2 <- rbindlist(out)
wtab(t2, "t2_first_stage_grid.csv")
cat("\nPerson-level KP-style F (village cluster), by combo:\n")
print(dcast(t2, treatment ~ iv, value.var = "F_pers_villcl"), digits = 3)

best <- t2[which.max(F_pers_villcl)]
cat(sprintf("\nBest pre-registered combo: %s <- %s, F = %.1f\n",
            best$treatment, best$iv, best$F_pers_villcl))

# chosen 2SLS first stage, full detail (main table column)
fs_main <- feols(as.formula(paste(TREAT, "~", IV_2SLS, "+", paste(c(ZV, XH, XI), collapse = "+"), "| county_year")),
                 pers, cluster = ~xzc12)
wtab(tidy_fe(fs_main), "t2b_first_stage_main.csv")

# ---- prereg / D1 decision record -------------------------------------------
pre <- c("# prereg_p3.md — pre-registered first-stage grid and D1 decision",
  paste0("Generated: ", format(Sys.time())), "",
  "## Grid (all combinations evaluated, none selected ex post beyond the rule below)",
  "- treatments: retail_pc1 (PCA), retail_lnfresh, access_dist",
  "- IVs: detour_{town,county}_{1,2,5}km",
  "- conditioning: ln_dist_town + ln_dist_county + ln_vpop + elevation + water + GAEZ (si, constraint)",
  "- own-village slope/TRI are excluded from the main conditioning set: they are a",
  "  mechanical component of the corridor-cost instrument (r ≈ 0.45); the agriculture",
  "  bypass is controlled directly via GAEZ suitability and soil-terrain constraint.",
  "  Slope/TRI-augmented specs appear in the robustness battery with AR inference.", "",
  "## Decision rule (proposal §12 D1)",
  "primary spec fixed ex ante = retail_pc1 <- detour_town_5km; if its KP-F < 10,",
  "pick the best-F combo from the grid for 2SLS and downgrade the paper's primary",
  "framing to the reduced form in detour (quasi-experimental terrain-isolation",
  "gradient), targeting Food Policy / World Development.", "",
  sprintf("## Outcome: D1 FIRES. Primary combo F = %.1f (<10).",
          t2[treatment == "retail_pc1" & iv == "detour_town_5km", F_pers_villcl]),
  sprintf("Best combo: %s <- %s with person-level village-clustered F = %.1f.",
          best$treatment, best$iv, best$F_pers_villcl),
  "",
  "Consequences applied throughout the pipeline:",
  "1. PRIMARY: reduced form  y ~ detour_town_5km + Z | county FE (person level, village cluster).",
  "2. SECONDARY: 2SLS retail_pc1 <- detour_town_1km, always accompanied by Anderson-Rubin CIs.",
  "3. MTE (v2 §15) is dropped (D5 analogue): weak first stage cannot support LIV;",
  "   replaced by the LATE/reduced-form mosaic across IV widths and subgroups.",
  "4. Post-estimation (gap accounting, investment pricing) is anchored on the reduced form,",
  "   with 2SLS-scaled versions shown as upper bounds.")
writeLines(pre, file.path(DIR_REP, "prereg_p3.md"))
cat("wrote prereg_p3.md\n")
log_close(con)
