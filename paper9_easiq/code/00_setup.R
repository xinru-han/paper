# Paper 9 "Trading Up, Trading Down" (EASI-Q) — shared setup. All scripts source this.

.libPaths(c("/root/Rlib_p8", .libPaths()))
suppressPackageStartupMessages({
  library(data.table)
  library(fixest)
})

PROJ <- "/root/data/Paper/央视数据/paper9-easiq"
RAW  <- "/root/data/数据/央视数据"
P1   <- "/root/data/Paper/央视数据/Paper1-EASI"
P8   <- "/root/data/Paper/央视数据/paper8-hot"
DIR_INT <- file.path(PROJ, "data/interim")
DIR_LKP <- file.path(PROJ, "data/lookups")
DIR_TAB <- file.path(PROJ, "outputs/tables")
DIR_FIG <- file.path(PROJ, "outputs/figs")
DIR_LOG <- file.path(PROJ, "logs")
for (d in c(DIR_INT, DIR_LKP, DIR_TAB, DIR_FIG, DIR_LOG)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

DEBUG <- as.logical(Sys.getenv("P9_DEBUG", "FALSE"))  # TRUE = 3,000-household subsample
set.seed(20260707)
setDTthreads(2)   # machine shared with another project's bootstrap

## the 13 payable categories (near-complete Volume recording) and the 8 fresh
## categories folded into one composite good for the Stage A budget system
PK13 <- c("大米","面粉","挂面","方便面","食用油","黄油","成人奶粉","奶酪",
          "常温牛奶","新鲜牛奶","常温酸奶","新鲜酸奶","坚果")
FRESH8 <- c("蔬菜","水果","猪肉","牛肉","羊肉","禽类","海鲜类","其他肉类")
COMP <- "G_fresh_composite"
G14 <- c(PK13, COMP)
## categories with genuinely observed monitor prices (rest are proxy fills that
## just copy 常温牛奶's series -> unusable as own price; their market base price
## is the province x month median unit value instead, see 90b)
OBS7 <- c("大米","面粉","食用油","方便面","常温牛奶","新鲜牛奶","成人奶粉")
DAIRY5 <- c("常温牛奶","新鲜牛奶","常温酸奶","新鲜酸奶","奶酪")

R_POLY <- as.integer(Sys.getenv("P9_RPOLY", "3"))   # Engel polynomial order (R8 varies it)

logmsg <- function(...) {
  msg <- paste0(format(Sys.time(), "%H:%M:%S"), " ", paste0(...))
  cat(msg, "\n")
  cat(msg, "\n", file = file.path(DIR_LOG, "run_log.md"), append = TRUE)
}

income_mid <- function(x) {  # band -> midpoint (yuan/month), both '>12000' spellings
  fcase(grepl("^2000", x), 1000, grepl("2000-4000", x), 3000,
        grepl("4000-6000", x), 5000, grepl("6000-8000", x), 7000,
        grepl("8000-10000", x), 9000, grepl("10000-12000", x), 11000,
        grepl(">\\s*12000", x) | grepl("12000\\s*RMB", x) & grepl(">", x), 14000,
        default = NA_real_)
}
famsize_mid <- function(x) {
  fcase(grepl("1-2", x), 1.5, grepl("数3", x), 3, grepl("数4", x), 4,
        grepl("5", x), 5.5, default = NA_real_)
}

grab <- function(m, ...) {  # coeftable -> data.table with extra id columns
  ct <- as.data.table(coeftable(m), keep.rownames = "term")
  setnames(ct, 1:5, c("term","est","se","t","p"))
  extra <- list(...)
  for (nm in names(extra)) ct[, (nm) := extra[[nm]]]
  ct[, n := nobs(m)][]
}

## theta_g(y) = d r / d y for kappa = (y, y^2, y^3) coefs, evaluated at y0
theta_at <- function(kap, y0, R = R_POLY) {
  sum(sapply(seq_len(R), function(r) if (r <= length(kap)) r * kap[r] * y0^(r - 1) else 0))
}
## delta-method SE of theta(y0) given vcov of (y, y^2, y^3)
theta_se <- function(V, y0, R = R_POLY) {
  g <- sapply(seq_len(R), function(r) r * y0^(r - 1))
  sqrt(as.numeric(t(g) %*% V %*% g))
}
POLY_Y <- function(R = R_POLY) paste0("I(y^", seq_len(R), ")", collapse = " + ")
