# =============================================================================
# 12_placebo_corridors.R — v2 §14 identification hardening, degraded version
# (GEE corridor recomputation infeasible offline; pre-registered fallbacks):
#  (A) destination relevance race: town vs county detour for predicting the
#      5km retail environment (the market-linkage test)
#  (B) permutation placebo: swap detour values among villages in the same
#      straight-distance decile (across counties), 999 draws -> where does the
#      real first-stage |t| fall in the placebo distribution? (PP1: <5% tail)
#      Same for the diet reduced form (expected NOT to beat placebos, given
#      the null RF — an honest power statement, reported as such).
# =============================================================================
source("/root/data/Paper/食物消费数据/paper3-foodenv/code/00_setup.R")
con <- log_open("12_placebo.log")

vg <- fread(file.path(DIR_DERIV, "p3_village.csv"), colClasses = list(character = "xzc12"))
vg[, county_id := substr(xzc12, 1, 6)]
pers <- fread(file.path(DIR_DERIV, "p3_person.csv"), colClasses = list(character = c("xzc12","nhCode")))

# ---- (A) destination race ---------------------------------------------------
race <- list()
for (ivv in c("detour_town_5km", "detour_county_5km")) {
  m <- feols(rhs(TREAT, c(ivv, ZV), fe = "county_id"), vg, vcov = "hetero")
  a <- coeftable(m)[ivv, ]
  race[[ivv]] <- data.table(iv = ivv, b = a[1], se = a[2], t = a[3], F = a[3]^2, n = m$nobs)
}
m_both <- feols(rhs(TREAT, c("detour_town_5km", "detour_county_5km", ZV), fe = "county_id"), vg, vcov = "hetero")
for (ivv in c("detour_town_5km", "detour_county_5km")) {
  a <- coeftable(m_both)[ivv, ]
  race[[paste0(ivv, "_joint")]] <- data.table(iv = paste0(ivv, " (joint)"), b = a[1], se = a[2],
                                              t = a[3], F = a[3]^2, n = m_both$nobs)
}
tA <- rbindlist(race)
wtab(tA, "t7b_destination_race.csv")
cat("Destination race (town corridor should dominate for 5km retail):\n"); print(tA, digits = 3)

# ---- (B) distance-decile permutation ---------------------------------------
vg[, dist_decile := cut(dist_town_5km, quantile(dist_town_5km, 0:10/10, na.rm = TRUE),
                        include.lowest = TRUE, labels = FALSE)]
dp <- vg[!is.na(dist_decile) & !is.na(detour_town_5km)]

fs_t <- function(d, ivcol) {
  m <- tryCatch(feols(rhs(TREAT, c(ivcol, ZV), fe = "county_id"), d, vcov = "hetero"),
                error = function(e) NULL)
  if (is.null(m) || !ivcol %in% rownames(coeftable(m))) return(NA_real_)
  coeftable(m)[ivcol, 3]
}
rf_t <- function(dd, ivcol) {
  m <- tryCatch(feols(rhs("fgds10", c(ivcol, XI, XH, ZV)), dd, cluster = ~xzc12),
                error = function(e) NULL)
  if (is.null(m) || !ivcol %in% rownames(coeftable(m))) return(NA_real_)
  coeftable(m)[ivcol, 3]
}

t_real_fs <- fs_t(dp, "detour_town_5km")
pers2 <- merge(pers, dp[, .(xzc12, dist_decile)], by = "xzc12")
t_real_rf <- rf_t(pers2, "detour_town_5km")

B <- 999
t_perm_fs <- numeric(B); t_perm_rf <- numeric(B)
for (b in seq_len(B)) {
  dp[, detour_perm := sample(detour_town_5km), by = dist_decile]
  t_perm_fs[b] <- fs_t(dp, "detour_perm")
  if (b <= 499) {   # RF permutation at person level is heavier; 499 draws
    pb <- merge(pers2, dp[, .(xzc12, detour_perm)], by = "xzc12")
    t_perm_rf[b] <- rf_t(pb, "detour_perm")
  }
}
t_perm_fs <- t_perm_fs[is.finite(t_perm_fs)]
t_perm_rf <- t_perm_rf[1:499][is.finite(t_perm_rf[1:499])]
p_fs <- (1 + sum(abs(t_perm_fs) >= abs(t_real_fs))) / (1 + length(t_perm_fs))
p_rf <- (1 + sum(abs(t_perm_rf) >= abs(t_real_rf))) / (1 + length(t_perm_rf))

tB <- data.table(
  stat = c("first stage (retail_pc1)", "reduced form (fgds10)"),
  t_real = c(t_real_fs, t_real_rf),
  perm_p = c(p_fs, p_rf),
  n_draws = c(length(t_perm_fs), length(t_perm_rf)),
  note = c("PP1: real corridor should sit in <5% tail",
           "expected non-rejection given the null RF (power statement)"))
wtab(tB, "t7c_permutation_corridors.csv")
print(tB, digits = 3)

# distribution for the figure
fwrite(data.table(t_perm = t_perm_fs), file.path(DIR_DERIV, "perm_fs_draws.csv"))
log_close(con)
