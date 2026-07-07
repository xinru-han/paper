# Paper 8 "Some Like It Hot" — shared setup
# All scripts source this first.

.libPaths(c("/root/Rlib_p8", .libPaths()))
suppressPackageStartupMessages({
  library(data.table)
  library(fixest)
})

PROJ <- "/root/data/Paper/央视数据/paper8-hot"
RAW  <- "/root/data/数据/央视数据"
P1   <- "/root/data/Paper/央视数据/Paper1-EASI"
NUTZ <- "/tmp/claude-0/-root/ce91ec13-d975-47d6-aa95-beabd101f6c8/scratchpad/nutri/output"  # unzipped 新版营养成分表
DIR_INT <- file.path(PROJ, "data/interim")
DIR_LKP <- file.path(PROJ, "data/lookups")
DIR_TAB <- file.path(PROJ, "outputs/tables")
DIR_FIG <- file.path(PROJ, "outputs/figs")
DIR_LOG <- file.path(PROJ, "logs")
for (d in c(DIR_INT, DIR_LKP, DIR_TAB, DIR_FIG, DIR_LOG)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

DEBUG <- as.logical(Sys.getenv("P8_DEBUG", "FALSE"))  # TRUE = 5% household subsample
set.seed(20260707)
setDTthreads(2)  # EASI bootstrap of another project shares this machine

# temperature bins (tavg, deg C); (18,24] is the reference bin
TBIN_BREAKS <- c(-Inf, 0, 6, 12, 18, 24, 30, Inf)
TBIN_LABELS <- c("le0", "b0_6", "b6_12", "b12_18", "ref18_24", "b24_30", "gt30")
TBIN_REF <- "ref18_24"
tbin_cut <- function(x) factor(TBIN_LABELS[findInterval(x, TBIN_BREAKS[-1]) + 1L], levels = TBIN_LABELS)

# precipitation bins (mm/day)
PBIN_BREAKS <- c(-Inf, 0, 10, 25, 50, Inf)
PBIN_LABELS <- c("dry", "p0_10", "p10_25", "p25_50", "p50p")
pbin_cut <- function(x) factor(PBIN_LABELS[findInterval(pmax(x, 0), PBIN_BREAKS[-1], left.open = TRUE) + 1L], levels = PBIN_LABELS)

# 10 food groups (Paper 1 convention)
G10 <- c("G01_主食","G02_食用油","G03_蔬菜","G04_水果","G05_猪肉",
         "G06_禽类及其他肉类","G07_牛羊肉","G08_海鲜","G09_乳制品","G10_坚果")

logmsg <- function(...) {
  msg <- paste0(format(Sys.time(), "%H:%M:%S"), " ", paste0(...))
  cat(msg, "\n")
  cat(msg, "\n", file = file.path(DIR_LOG, "run_log.md"), append = TRUE)
}

# wild cluster bootstrap (Rademacher, unrestricted WCB-x) p-value for one
# coefficient of a feols fit, by refitting on perturbed outcomes
# y* = yhat + e * w_g. Only used on aggregated (exposure-unit x date) panels
# where a refit costs < 0.1s; B = 399 by default. dt must contain the fit's
# variables; cl_var names the cluster column.
wcb_pvalue <- function(fit, coef_name, dt, yvar, cl_var, B = 399, seed = 1) {
  set.seed(seed)
  ok <- obs(fit)
  d <- dt[ok]
  d$..yhat <- fitted(fit)
  d$..e <- resid(fit)
  cl <- as.integer(as.factor(d[[cl_var]]))
  G <- max(cl)
  b0 <- coef(fit)[coef_name]
  fml <- formula(fit)
  draws <- vapply(seq_len(B), function(b) {
    w <- sample(c(-1, 1), G, replace = TRUE)
    d$..ystar <- d$..yhat + d$..e * w[cl]
    f2 <- update(fml, ..ystar ~ .)
    fb <- feols(f2, data = d, warn = FALSE, notes = FALSE)
    coef(fb)[coef_name] - b0
  }, numeric(1))
  # symmetric percentile-t-free p-value on coefficient distribution around b0
  mean(abs(draws) >= abs(b0))
}

# permutation p-value machinery: permute year labels of the temperature series
# within exposure-unit x calendar-month (preserves seasonality), re-estimate,
# compare |beta|; implemented ad hoc in scripts 05/12.
