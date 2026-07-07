# =============================================================================
# 07_bline_passthrough.R — B2: pass-through of household provisioning diversity
# to elder individual intake diversity, by living arrangement.
#   fgds10_i = phi0 + phi1*hdds12_h + sum_k phi1k*(hdds12_h x LA_k) + LA_k + X + FE
# Sample: all elder individuals with 48h records (incl. elder-only/alone).
# Output: T11 (pass-through), fig — none (goes into decomposition figure)
# =============================================================================
source("/root/data/Paper/食物消费数据/paper2-elder/code/00_setup.R")
suppressPackageStartupMessages({ library(fixest) })

per <- fread(file.path(DIR_DERIV, "person_analysis.csv"), colClasses = list(character = c("nhCode","pid","xzc12")))
eld <- per[elderly == 1 & !is.na(num(fgds10)) & !is.na(num(hdds12_household))]
LA_LEVELS <- c("cohabit_nonelder","elder_only_multi","threegen","elder_alone","elder_child","other")
eld <- eld[living_arrangement %in% LA_LEVELS]
eld[, LA := relevel(factor(living_arrangement, levels = LA_LEVELS), ref = "cohabit_nonelder")]
eld[, `:=`(fgds10 = num(fgds10), hdds = num(hdds12_household), county_year = paste(countyn, data_year))]
eld[is.na(main_cook), main_cook := 0]

m_pool <- feols(fgds10 ~ hdds + LA + female + main_cook + ln_income | county_year,
                data = eld, cluster = ~xzc12)
m_int  <- feols(fgds10 ~ hdds*LA + female + main_cook + ln_income | county_year,
                data = eld, cluster = ~xzc12)
t11 <- rbind(tidy_fe(m_pool, "hdds|^LA")[, spec := "pooled phi1"],
             tidy_fe(m_int,  "hdds|^LA")[, spec := "phi1 x living arrangement"])
wtab(t11, "table11_bline_passthrough.csv")

# pass-through by arrangement (phi1 + phi1k), delta-method SEs
ct <- coeftable(m_int); V <- vcov(m_int)
base <- "hdds"
pt <- rbindlist(lapply(levels(eld$LA), function(la) {
  if (la == "cohabit_nonelder") {
    b <- ct[base, "Estimate"]; s <- ct[base, "Std. Error"]
  } else {
    trm <- paste0("hdds:LA", la)
    if (!trm %in% rownames(ct)) return(NULL)
    b <- ct[base,"Estimate"] + ct[trm,"Estimate"]
    s <- sqrt(V[base,base] + V[trm,trm] + 2*V[base,trm])
  }
  data.table(arrangement = la, phi1 = b, se = s, p = 2*pnorm(-abs(b/s)))
}))
wtab(pt, "table11b_passthrough_by_LA.csv")
saveRDS(list(m_pool = m_pool, m_int = m_int, passthrough = pt),
        file.path(DIR_DERIV, "passthrough_models.rds"))
cat("B2 OK\n"); print(pt)
