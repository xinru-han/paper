# Paper 9 script 90d: LLI income-expenditure link equation (Huang-Gale style)
#  ln x = s0 + s1/I + s2 ln I + controls; within (household FE, band jumps) and
#  between versions. Multiplier (s2 - s1/I) converts theta to income-quality
#  elasticity in 93.
source("/root/data/Paper/央视数据/paper9-easiq/code/00_setup.R")

pan <- readRDS(file.path(DIR_INT, "panel_hhm.rds"))
pan <- pan[is.finite(ln_inc) & is.finite(ln_x)]

# within: inv_inc near-collinear with ln_inc under hh FE (band switchers only,
# two support points per switcher) -> log-only within version
m_w <- feols(ln_x ~ ln_inc | ID + prov_tier^ym, data = pan, cluster = ~ID)
m_b <- feols(ln_x ~ inv_inc + ln_inc + fsize + elderly | prov_tier + mo, data = pan, cluster = ~Province)
out <- rbind(grab(m_w, model = "within_hhFE"), grab(m_b, model = "between"))
fwrite(out, file.path(DIR_TAB, "t2a_income_link.csv"))

Ibar <- mean(pan$inc_mid, na.rm = TRUE)
mult_w <- coef(m_w)["ln_inc"]
mult_b <- coef(m_b)["ln_inc"] - coef(m_b)["inv_inc"] / Ibar
saveRDS(list(mult_within = mult_w, mult_between = mult_b, Ibar = Ibar),
        file.path(DIR_INT, "income_link.rds"))
logmsg("90d: LLI multiplier within=", round(mult_w, 3), " between=", round(mult_b, 3))
