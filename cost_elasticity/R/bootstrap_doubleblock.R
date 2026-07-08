# bootstrap_doubleblock.R — M1e 玉米 省×时期 双重 block bootstrap（时期=4段）B=200
# 重抽单位=（省×时期）胞，兼顾横截面(省)与时序(时期)依赖；重抽省作独立个体各自FE。
# 产出: out/bootstrap_corn_doubleblock.csv
suppressMessages({library(data.table); library(parallel)})
setwd("/root/paper/cost_elasticity")
source("R/itsur.R"); source("R/itsur_concave.R"); source("R/estimate.R")

B <- 200; SEED <- 20260703
FN <- c("labor","mach","fert","seed","other")
PB <- list(`2004-2008`=2004:2008,`2009-2014`=2009:2014,`2015-2019`=2015:2019,`2020-2024`=2020:2024)
ncores <- min(as.integer(Sys.getenv("BOOT_CORES","6")), detectCores()-1)

pan <- fread("data/panel_corn.csv")
pan[, period := NA_character_]; for (nm in names(PB)) pan[year %in% PB[[nm]], period := nm]
blocks <- unique(pan[, .(province, period)])          # 省×时期胞
d0 <- prep_data(pan); sys0 <- tl_build_system(d0, 4)
So0 <- as.matrix(as.data.frame(d0)[, paste0("S_", FN[1:4])]); So0 <- cbind(So0, 1 - rowSums(So0))
a_full <- tl_itsur_c1(sys0, 4, colMeans(So0), S_obs = So0, kappa = 1e6)$a

set.seed(SEED)
draw_blocks <- lapply(1:B, function(b) blocks[sample(.N, .N, replace = TRUE)])

one <- function(b) {
  bl <- draw_blocks[[b]]
  dl <- lapply(seq_len(nrow(bl)), function(i) {
    x <- copy(pan[province == bl$province[i] & period == bl$period[i]])
    x$province <- sprintf("bs%03d", i); x })   # 每个胞作独立个体
  d <- prep_data(rbindlist(dl))
  if (uniqueN(d$prov) < 4) return(data.table(draw = b, status = "prep_fail"))
  sys <- tl_build_system(d, 4)
  So <- as.matrix(as.data.frame(d)[, paste0("S_", FN[1:4])]); So <- cbind(So, 1 - rowSums(So))
  fit <- tryCatch(tl_itsur_c1(sys, 4, colMeans(So), S_obs = So, kappa = 1e6, a_init = a_full),
                  error = function(e) NULL)
  if (is.null(fit) || !fit$converged) return(data.table(draw = b, status = "fit_fail"))
  G <- fit$Gamma_full; lam <- { l <- fit$theta[sprintf("lambda_%dt",1:4)]; c(l, -sum(l)) }
  Shat <- tl_fitted_shares(fit, sys, 4); Sb <- colMeans(Shat); el <- tl_elasticities(G, Sb)
  data.table(draw = b, status = "ok", eps_ll = el$eps[1,1], eps_mm = el$eps[2,2],
             M_ml = el$morishima[2,1], M_lm = el$morishima[1,2], B_labor = lam[1]/Sb[1])
}
res <- rbindlist(mclapply(1:B, one, mc.cores = ncores), fill = TRUE)
fwrite(res, "out/bootstrap_corn_doubleblock.csv")
ok <- res[status == "ok"]
cat(sprintf("[doubleblock] ok %d/%d\n", nrow(ok), B))
for (v in c("eps_ll","eps_mm","M_ml","B_labor"))
  cat(sprintf("%s %.3f [%.3f, %.3f]\n", v, median(ok[[v]]), quantile(ok[[v]],.025), quantile(ok[[v]],.975)))
