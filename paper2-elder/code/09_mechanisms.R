# =============================================================================
# 09_mechanisms.R — Task 5/6/8: provisioning-role mechanism (common sample),
# self-provisioning mechanism re-estimated on the elder sample,
# binary outcome family + low-diversity risk
# Tables: T14 (roles), T15 (self-provisioning chain), T16 (binary outcomes)
# =============================================================================
source("/root/data/Paper/食物消费数据/paper2-elder/code/00_setup.R")
suppressPackageStartupMessages({ library(fixest) })

hh  <- fread(file.path(DIR_DERIV, "hh_analysis.csv"), colClasses = list(character = c("nhCode","xzc12")))
LA_LEVELS <- c("cohabit_nonelder","elder_only_multi","threegen","elder_alone","elder_child","other")
hh[, LA := relevel(factor(living_arrangement, levels = LA_LEVELS), ref = "cohabit_nonelder")]
hh[, county_year := paste(countyn, data_year)]
for (v in c("hdds12","elder_is_cook","elder_is_buyer","nonelder_cook","nonelder_buyer",
            "share_dairy_egg_bean")) hh[, (v) := num(get(v))]
CT <- "ln_income + any_elder_80 + n_elderly"

# ---- T14: provisioning roles, common-sample discipline (Task 5) ---------------
cs <- hh[!is.na(nonelder_cook) & !is.na(nonelder_buyer) & !is.na(elder_is_cook)]
m_a <- feols(as.formula(paste("hdds12 ~ LA +", CT, "| county_year")), data = cs, cluster = ~xzc12)
m_b <- feols(as.formula(paste("hdds12 ~ LA + nonelder_cook + nonelder_buyer + elder_is_cook +", CT, "| county_year")),
             data = cs, cluster = ~xzc12)
# roles as outcomes: does three-gen change who provisions?
m_c <- feols(as.formula(paste("nonelder_cook ~ LA +", CT, "| county_year")), data = cs, cluster = ~xzc12)
m_d <- feols(as.formula(paste("nonelder_buyer ~ LA +", CT, "| county_year")), data = cs, cluster = ~xzc12)
m_e <- feols(as.formula(paste("elder_is_cook ~ LA +", CT, "| county_year")), data = cs, cluster = ~xzc12)
t14 <- rbindlist(list(
  tidy_fe(m_a, "^LA")[, spec := "hdds12 ~ LA (common sample)"],
  tidy_fe(m_b, "^LA|cook|buyer")[, spec := "hdds12 ~ LA + roles"],
  tidy_fe(m_c, "^LA")[, spec := "nonelder_cook ~ LA"],
  tidy_fe(m_d, "^LA")[, spec := "nonelder_buyer ~ LA"],
  tidy_fe(m_e, "^LA")[, spec := "elder_is_cook ~ LA"]))
wtab(t14, "table14_roles_mechanism.csv")
med <- 100 * (1 - coef(m_b)["LAthreegen"]/coef(m_a)["LAthreegen"])
cat(sprintf("Role variables mediate %.1f%% of the three-gen HDDS association\n", med))

# ---- T15: self-provisioning chain on elder sample (Task 6) --------------------
for (k in FOOD12) hh[, (paste0(k,"_ssr")) := num(get(paste0(k,"_self_suff_rate")))]
hh[, food_ssr := num(food_self_suff_rate)]
m_s1 <- feols(as.formula(paste("food_ssr ~ LA +", CT, "| county_year")), data = hh, cluster = ~xzc12)
m_s2 <- feols(as.formula(paste("hdds12 ~ LA + food_ssr +", CT, "| county_year")), data = hh, cluster = ~xzc12)
cat_ssr <- rbindlist(lapply(c("shucai","danlei","roulei","doulei"), function(k) {
  m <- feols(as.formula(paste0(k, "_ssr ~ LA + ", CT, " | county_year")), data = hh, cluster = ~xzc12)
  tidy_fe(m, "^LA")[, outcome := paste0(k, "_self_suff_rate")]
}))
t15 <- rbind(tidy_fe(m_s1, "^LA")[, outcome := "food_self_suff_rate"],
             tidy_fe(m_s2, "^LA|food_ssr")[, outcome := "hdds12 | + food_ssr"],
             cat_ssr, fill = TRUE)
wtab(t15, "table15_selfprovisioning_elder.csv")

# ---- T16: binary outcome family + risk (Task 8) --------------------------------
hh[, consumes_dairy := as.integer(!is.na(num(nailei_cons))  & num(nailei_cons)  > 0)]
hh[, consumes_egg   := as.integer(!is.na(num(danlei_cons))  & num(danlei_cons)  > 0)]
hh[, consumes_bean  := as.integer(!is.na(num(doulei_cons))  & num(doulei_cons)  > 0)]
hh[, consumes_fruit := as.integer(!is.na(num(shuiguo_cons)) & num(shuiguo_cons) > 0)]
hh[, low_hdds := as.integer(hdds12 < median(hdds12, na.rm = TRUE))]
t16 <- rbindlist(lapply(c("consumes_dairy","consumes_egg","consumes_bean","consumes_fruit","low_hdds"), function(y) {
  if (uniqueN(hh[[y]], na.rm = TRUE) < 2) return(NULL)
  m <- feols(as.formula(paste(y, "~ LA +", CT, "| county_year")), data = hh, cluster = ~xzc12)
  tidy_fe(m, "^LA")[, outcome := y]
}))
wtab(t16, "table16_binary_outcomes.csv")

writeLines(c("# Mechanisms summary",
  sprintf("- Provisioning-role mediation of three-gen HDDS effect: %.1f%%", med),
  sprintf("- Three-gen -> non-elder member cooks: %+.3f (p=%.3f)",
          coef(m_c)["LAthreegen"], coeftable(m_c)["LAthreegen",4]),
  sprintf("- Three-gen -> elder is cook: %+.3f (p=%.3f)",
          coef(m_e)["LAthreegen"], coeftable(m_e)["LAthreegen",4]),
  sprintf("- Three-gen -> household self-sufficiency: %+.3f (p=%.3f)",
          coef(m_s1)["LAthreegen"], coeftable(m_s1)["LAthreegen",4])),
  file.path(DIR_REP, "mechanisms_summary.md"))
cat("MECHANISMS OK\n")
