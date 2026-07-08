# =============================================================================
# 08_moderators.R — T6: who is exposed? RF interactions of detour with
# fridge / vehicle / self-sufficiency / income terciles (fgds10 + hdds12).
# Testable implications (proposal §3): no-fridge and low-self-sufficiency
# households should be MORE exposed to isolation.
# =============================================================================
source("/root/data/Paper/食物消费数据/paper3-foodenv/code/00_setup.R")
con <- log_open("08_moderators.log")

pers <- fread(file.path(DIR_DERIV, "p3_person.csv"), colClasses = list(character = c("xzc12","nhCode")))
pers[, no_fridge  := 1L - hb_fridge]
pers[, no_vehicle := 1L - hb_vehicle]
pers[, hi_ss := as.integer(food_ssr_w > median(food_ssr_w, na.rm = TRUE))]
pers[, inc_ter := cut(ln_income, quantile(ln_income, c(0, 1/3, 2/3, 1), na.rm = TRUE),
                      labels = c("T1", "T2", "T3"), include.lowest = TRUE)]
XC <- c(XI, XH, ZV)

out <- list()
for (y in c("fgds10", "hdds12")) for (md in c("no_fridge", "no_vehicle", "hi_ss")) {
  f <- as.formula(paste(y, "~", IV_RF, "*", md, "+", paste(setdiff(XC, c("hb_fridge","hb_vehicle")), collapse = "+"),
                        "| county_year"))
  m <- feols(f, pers[!is.na(get(y)) & !is.na(get(md))], cluster = ~xzc12)
  ct <- tidy_fe(m, keep = "detour")
  ct[, `:=`(outcome = y, moderator = md)]
  out[[length(out) + 1]] <- ct
}
# income terciles: separate slopes
for (y in c("fgds10", "hdds12")) {
  f <- as.formula(paste(y, "~ i(inc_ter,", IV_RF, ") +",
                        paste(setdiff(XC, "ln_income"), collapse = "+"), "| county_year"))
  m <- feols(f, pers[!is.na(get(y)) & !is.na(inc_ter)], cluster = ~xzc12)
  ct <- tidy_fe(m, keep = "inc_ter")
  ct[, `:=`(outcome = y, moderator = "income tercile slopes")]
  out[[length(out) + 1]] <- ct
}
t6 <- rbindlist(out, fill = TRUE)
wtab(t6, "t6_moderators.csv")
print(t6[, .(outcome, moderator, term, est, se, p)], digits = 3)
log_close(con)
