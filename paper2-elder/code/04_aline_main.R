# =============================================================================
# 04_aline_main.R — A line (household level): FE sequence, scale vs composition,
# children dose, interview-day controls, count-model cross-checks
# Tables: T2 (FE sequence, hdds12), T3 (food structure shares),
#         T4 (scale vs composition), T5 (children dose), T6 (functional-form)
# =============================================================================
source("/root/data/Paper/食物消费数据/paper2-elder/code/00_setup.R")
suppressPackageStartupMessages({ library(fixest) })

hh <- fread(file.path(DIR_DERIV, "hh_analysis.csv"), colClasses = list(character = c("nhCode","xzc12")))
LA_LEVELS <- c("cohabit_nonelder","elder_only_multi","threegen","elder_alone","elder_child","other")
hh[, LA := relevel(factor(living_arrangement, levels = LA_LEVELS), ref = "cohabit_nonelder")]
hh[, `:=`(prov_year = paste(provn, data_year), county_year = paste(countyn, data_year),
          vill_year = paste(xzc12, data_year))]
for (v in c("hdds12","share_dairy_egg_bean","share_animal","share_fruit_veg","any_elder_80",
            "HB2","HB5","HB8","n_children")) hh[, (v) := num(get(v))]
hh[, HB2 := fifelse(HB2 %in% 0:1, HB2, NA_real_)]
hh[, HB5 := fifelse(HB5 %in% 0:1, HB5, NA_real_)]
hh[, HB8 := fifelse(HB8 %in% 0:1, HB8, NA_real_)]

CTRL <- "ln_income + any_elder_80 + n_elderly"
setFixest_estimation(data = hh)

# ---- T2: FE sequence for HDDS-12 -------------------------------------------
m_base <- feols(as.formula(paste0("hdds12 ~ LA + ", CTRL, " | data_year")),            cluster = ~xzc12)
m_prov <- feols(as.formula(paste0("hdds12 ~ LA + ", CTRL, " | prov_year")),            cluster = ~xzc12)
m_cnty <- feols(as.formula(paste0("hdds12 ~ LA + ", CTRL, " | county_year")),          cluster = ~xzc12)
m_vill <- feols(as.formula(paste0("hdds12 ~ LA + ", CTRL, " | vill_year")),            cluster = ~xzc12)
m_villc<- feols(as.formula(paste0("hdds12 ~ LA + ", CTRL, " + market_access_index + retail_thickness_index | county_year")), cluster = ~xzc12)

mods <- list(year_FE = m_base, prov_year_FE = m_prov, county_year_FE = m_cnty,
             county_year_FE_env = m_villc, village_year_FE = m_vill)
t2 <- rbindlist(lapply(names(mods), function(nm) {
  ct <- tidy_fe(mods[[nm]], keep = "^LA")
  ct[, model := nm]; ct
}))
wtab(t2, "table2_aline_fe_sequence_hdds.csv")

# ---- T3: food structure shares (county-year FE) -----------------------------
sh_out <- c("share_dairy_egg_bean","share_animal","share_fruit_veg")
t3 <- rbindlist(lapply(sh_out, function(y) {
  m <- feols(as.formula(paste0(y, " ~ LA + ", CTRL, " | county_year")), cluster = ~xzc12)
  # fractional logit cross-check (R5)
  mf <- feglm(as.formula(paste0(y, " ~ LA + ", CTRL, " | county_year")),
              family = binomial("logit"), cluster = ~xzc12,
              data = hh[get(y) >= 0 & get(y) <= 1])
  rbind(tidy_fe(m, "^LA")[, `:=`(outcome = y, spec = "OLS")],
        tidy_fe(mf, "^LA")[, `:=`(outcome = y, spec = "frac_logit")])
}))
wtab(t3, "table3_aline_food_structure_shares.csv")

# ---- T4: scale vs composition (D5 check) ------------------------------------
m_nosize <- feols(as.formula(paste0("hdds12 ~ LA + ", CTRL, " | county_year")), cluster = ~xzc12)
m_size   <- feols(as.formula(paste0("hdds12 ~ LA + ", CTRL, " + factor(hh_size_grp) | county_year")), cluster = ~xzc12)
b1 <- coef(m_nosize)["LAthreegen"]; b2 <- coef(m_size)["LAthreegen"]
atten <- 100 * (1 - b2/b1)
t4 <- rbind(tidy_fe(m_nosize, "^LA|hh_size")[, spec := "no size dummies"],
            tidy_fe(m_size,   "^LA|hh_size")[, spec := "with size dummies (2/3/4/5/6+)"])
wtab(t4, "table4_scale_vs_composition.csv")
d5 <- atten > 50
cat(sprintf("Three-gen coef: %.3f -> %.3f with size dummies (attenuation %.1f%%). D5 %s\n",
            b1, b2, atten, ifelse(d5, "TRIGGERED", "not triggered")))

# ---- T5: children dose within three-generation households -------------------
m_dose <- feols(as.formula(paste0("share_dairy_egg_bean ~ n_children + ", CTRL, " | county_year")),
                data = hh[living_arrangement == "threegen"], cluster = ~xzc12)
m_dose2 <- feols(as.formula(paste0("hdds12 ~ n_children + ", CTRL, " | county_year")),
                 data = hh[living_arrangement == "threegen"], cluster = ~xzc12)
t5 <- rbind(tidy_fe(m_dose, "n_children")[, outcome := "share_dairy_egg_bean"],
            tidy_fe(m_dose2, "n_children")[, outcome := "hdds12"])
wtab(t5, "table5_children_dose_threegen.csv")

# ---- T6: functional form + interview-day controls (R5, R8) ------------------
m_pois <- fepois(as.formula(paste0("hdds12 ~ LA + ", CTRL, " | county_year")), cluster = ~xzc12)
m_iday <- feols(as.formula(paste0("hdds12 ~ LA + ", CTRL, " + factor(interview_month) + factor(interview_wday) | county_year")),
                cluster = ~xzc12)
t6 <- rbind(tidy_fe(m_pois, "^LA")[, spec := "Poisson"],
            tidy_fe(m_iday, "^LA")[, spec := "OLS + interview month/weekday dummies"])
wtab(t6, "table6_functional_form_interviewday.csv")

# decision-node log
writeLines(c("# A-line decision-node check",
  sprintf("- D5 (scale attenuation > 50%%): attenuation = %.1f%% -> %s", atten,
          ifelse(d5, "TRIGGERED: rewrite mechanism section around meal-scale economies",
                 "not triggered: composition effect survives size dummies"))),
  file.path(DIR_REP, "decision_p2_D5_check.md"))

cat("A-LINE MAIN OK\n")
print(t2[term == "LAthreegen", .(model, est, se, p, n)])
