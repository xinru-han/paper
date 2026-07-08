# =============================================================================
# 15_investment_pricing.R — v2 §18: back-of-envelope investment pricing.
# County government work reports (62 sample counties, 2010-2024): keyword
# intensity for rural-commerce investment (商业体系/冷链/农贸市场/物流/快递),
# cross-sectional elasticity of the village retail environment to report
# intensity, then implied cost per woman crossing the MDD-W threshold using
# the AR upper-bound effect (i.e., the CHEAPEST the infrastructure route can
# plausibly be). D6 fallback: intensity version only — RMB amounts in reports
# are too sparse/heterogeneous for reliable extraction (documented).
# =============================================================================
source("/root/data/Paper/食物消费数据/paper3-foodenv/code/00_setup.R")
suppressPackageStartupMessages(library(readxl))
con <- log_open("15_pricing.log")

vg <- fread(file.path(DIR_DERIV, "p3_village.csv"), colClasses = list(character = "xzc12"))
vg[, county_id := paste(provn, countyn, sep = "_")]

# ---- county report keyword intensity ---------------------------------------
tx <- as.data.table(read_excel(F_COUNTY_TXT))
tx <- tx[, .(prov = as.character(省名), county = as.character(县名),
             year = num(年份), txt = as.character(内容))]
tx <- tx[year >= 2010 & year <= 2024 & !is.na(txt)]

KW <- c("冷链", "农贸市场", "商业体系", "物流", "快递", "农村电商", "集贸市场", "便民商店")
for (k in KW) tx[, (paste0("k_", k)) := stringr::str_count(txt, k)]
tx[, kw_total := rowSums(.SD), .SDcols = paste0("k_", KW)]
tx[, txt_len := nchar(txt)]
cint <- tx[, .(kw_per_10k = 1e4 * sum(kw_total) / sum(txt_len), n_reports = .N),
           by = .(prov, county)]

# match to sample counties (countyn strings contain the county name)
cty <- unique(vg[, .(provn, countyn, county_id)])
cint[, matched := FALSE]
mfun <- function(pn, cn_) {
  hit <- cint[grepl(substr(gsub("市|地区|自治州|盟", "", cn_), nchar(gsub("市|地区|自治州|盟","",cn_)) - 2, nchar(gsub("市|地区|自治州|盟","",cn_))), county, fixed = TRUE) |
              mapply(function(x) grepl(x, cn_, fixed = TRUE), county)]
  if (nrow(hit)) hit[1, kw_per_10k] else NA_real_
}
# countyn is like "吉林市永吉县" — take the tail county token for matching
cty[, county_tail := sub(".*市", "", countyn)]
cint_idx <- cint[, .(county, kw_per_10k)]
cty[, kw_per_10k := sapply(county_tail, function(ct) {
  hit <- cint_idx[county == ct | grepl(ct, county, fixed = TRUE) |
                  mapply(function(x) grepl(x, ct, fixed = TRUE), county)]
  if (nrow(hit)) mean(hit$kw_per_10k) else NA_real_
})]
cat(sprintf("matched %d of %d sample counties to work-report intensity\n",
            sum(!is.na(cty$kw_per_10k)), nrow(cty)))

vg <- merge(vg, cty[, .(county_id, kw_per_10k)], by = "county_id", all.x = TRUE)

# ---- elasticity: retail environment ~ report intensity (county cross-section)
vc <- vg[!is.na(kw_per_10k), .(retail_pc1 = mean(retail_pc1, na.rm = TRUE),
                               ln_kw = log1p(mean(kw_per_10k))), by = county_id]
m_el <- feols(retail_pc1 ~ ln_kw, vc, vcov = "hetero")
el <- coeftable(m_el)["ln_kw", ]
cat(sprintf("\nelasticity: retail_pc1 on ln(1+kw intensity): b=%.3f (se %.3f, p=%.3f, n=%d counties)\n",
            el[1], el[2], el[4], m_el$nobs))

# ---- implied pricing chain (all assumptions in the table note) --------------
# AR upper-bound MDD-W uplift per 1sd retail_pc1 (from 14): read t8
t8 <- fread(file.path(DIR_TAB, "t8_gap_accounting.csv"))
ar_ub_pp <- num(sub("([0-9.]+).*", "\\1", t8[quantity == "uplift, AR 95% UPPER BOUND (pp)", value]))
# benchmark cost anchors (literature): fortification ~US$0.2-2 /beneficiary-yr;
# school feeding ~US$40-80; supermarket/cold-chain county programs: no credible
# RMB anchor extractable from reports (D6) -> report the required-effectiveness
# inversion instead: cost per +1sd retail_pc1 that would make the route
# competitive with school feeding at the AR upper bound.
women_per_village <- 15   # sample-implied average women 15-49 per village survey slice
t9 <- data.table(
  quantity = c("AR upper-bound MDD-W uplift per +1sd retail (pp)",
               "implied women crossing threshold per village per +1sd (AR UB)",
               "school-feeding benchmark (US$/beneficiary-yr, literature)",
               "break-even village investment for parity at AR UB (US$/yr)",
               "elasticity retail_pc1 ~ ln report intensity (counties)",
               "NOTE"),
  value = c(sprintf("%.2f", ar_ub_pp),
            sprintf("%.2f", women_per_village * ar_ub_pp / 100),
            "40-80",
            sprintf("%.0f-%.0f", 40 * women_per_village * ar_ub_pp / 100,
                    80 * women_per_village * ar_ub_pp / 100),
            sprintf("%.3f (p=%.2f)", el[1], el[4]),
            "point effect ~0 => point-estimate cost is unbounded; the AR bound prices the BEST CASE"))
wtab(t9, "t9_investment_pricing.csv")
print(t9)
cat("\nD6 note: RMB amount extraction from work reports skipped (sparse/heterogeneous);\n",
    "intensity-elasticity version only, MVPF comparison framed as required-effectiveness inversion.\n")
log_close(con)
