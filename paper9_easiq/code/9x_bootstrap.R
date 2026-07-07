# Paper 9 script 9x: household-cluster bootstrap of the theta chain (B=200).
#  Per draw: resample households with replacement -> recompute Stone y (mean
#  weights of the draw) -> Stage B FE theta (linear-y version) per category.
#  Deviation from the md (documented): the probit/selection layer and the
#  Stage A y-iteration are NOT re-estimated per draw (lambda_sel held fixed;
#  y approximated by the one-shot Stone index, which the iteration barely
#  moves). CI covers sampling + generated-y first-order variation.
source("/root/data/Paper/央视数据/paper9-easiq/code/00_setup.R")

B <- as.integer(Sys.getenv("P9_BOOT_B", "200"))
qd <- readRDS(file.path(DIR_INT, "quality_panel.rds"))
spA <- readRDS(file.path(DIR_INT, "stageA_panel.rds"))
qd <- merge(qd, spA[, c("ID","ym","ln_x","vhat", paste0("w_", 1:14), paste0("lnp_", 1:14)),
                    with = FALSE], by = c("ID","ym"))
qd[is.na(fsize), fsize := median(qd$fsize, na.rm = TRUE)]
ZB <- "fsize + elderly + lock_days + ln_covid + cny_share + hot_days"
ids <- unique(qd$ID)
lnPm <- as.matrix(qd[, paste0("lnp_", 1:14), with = FALSE])

draws <- vector("list", B)
set.seed(20260707)
for (b in 1:B) {
  bid <- data.table(ID = sample(ids, length(ids), replace = TRUE))[, bid := .I]
  db <- merge(qd, bid, by = "ID", allow.cartesian = TRUE)
  wbar_b <- sapply(1:14, function(k) mean(db[[paste0("w_", k)]]))
  db[, y := ln_x - as.vector(as.matrix(db[, paste0("lnp_", 1:14), with = FALSE]) %*% wbar_b)]
  draws[[b]] <- rbindlist(lapply(PK13, function(cc) {
    m <- tryCatch(feols(as.formula(paste0("r_prem ~ y + ", ZB, " | bid + prov_tier^ym")),
                        data = db[Category == cc], notes = FALSE, se = "standard"),
                  error = function(e) NULL)
    if (is.null(m)) NULL else data.table(b = b, category = cc, theta = coef(m)["y"])
  }))
  rm(db); gc(FALSE)
  if (b %% 10 == 0) logmsg("9x: bootstrap draw ", b, "/", B)
}
bd <- rbindlist(draws)
saveRDS(bd, file.path(DIR_INT, "boot_draws.rds"))
ci <- bd[, .(theta_boot_mean = mean(theta), ci_lo = quantile(theta, .025),
             ci_hi = quantile(theta, .975), boot_se = sd(theta), B = .N), by = category]
fwrite(ci, file.path(DIR_TAB, "t3c_theta_bootstrap_ci.csv"))
logmsg("9x: done")
