# =============================================================================
# 11_county_policy_text.R — Post-estimation ③: county elder-feeding policy
# context from county government work reports (32k county-year full texts).
# RED LINE: text measures are COUNTY-level context only, never a household
# treatment; 幸福院 (n=12 users) is never used as an individual treatment.
# Outputs: county_policy_panel.csv, fig9 diffusion timeline,
#          T18 exploratory moderation (LA x policy intensity),
#          validity sample of 100 keyword sentences for manual audit
# =============================================================================
source("/root/data/Paper/食物消费数据/paper2-elder/code/00_setup.R")
suppressPackageStartupMessages({ library(readxl); library(fixest); library(ggplot2); library(stringr) })

txt <- as.data.table(read_excel(F_COUNTY_TXT))
setnames(txt, c("seq","county_code","county","city","city_code","prov","prov_code","year","title","content"))
txt[, year := num(year)]
txt <- txt[!is.na(content) & nchar(content) > 200]

# --- match sample counties by normalized name ---------------------------------
hh <- fread(file.path(DIR_DERIV, "hh_analysis.csv"), colClasses = list(character = c("nhCode","xzc12")))
norm_cty <- function(x) {
  x <- gsub("\\s", "", x)
  # take the last 县/市/区/旗-terminated token (strip prefixed city names)
  m <- regmatches(x, gregexpr("[\\p{Han}]{1,8}?(县|市|区|旗)", x, perl = TRUE))
  sapply(m, function(v) if (length(v)) tail(v, 1) else NA_character_)
}
samp_cty <- unique(hh[, .(provn, countyn)])
samp_cty[, cty_norm := norm_cty(countyn)]
txt[, cty_norm := norm_cty(county)]
txt[, prov_norm := gsub("省|自治区|回族|壮族|维吾尔", "", prov)]
samp_cty[, prov_norm := gsub("省|自治区|回族|壮族|维吾尔", "", provn)]
matched <- merge(samp_cty, unique(txt[, .(prov_norm, cty_norm)]), by = c("prov_norm","cty_norm"))
cat(sprintf("County match: %d of %d sample counties found in report corpus\n", nrow(matched), nrow(samp_cty)))

ctx <- merge(txt, matched[, .(prov_norm, cty_norm, countyn, provn)], by = c("prov_norm","cty_norm"))

# --- keyword families (pre-registered) ----------------------------------------
KW_ELDERFOOD <- c("老年助餐","长者食堂","老年食堂","幸福院","助餐服务","助餐点","养老服务","居家养老","日间照料")
KW_PLACEBO   <- c("商贸流通","招商引资")   # general-commerce placebo family
count_kw <- function(text, kws) rowSums(sapply(kws, function(k) str_count(text, fixed(k))))
ctx[, n_elderfood := count_kw(content, KW_ELDERFOOD)]
ctx[, n_placebo   := count_kw(content, KW_PLACEBO)]
ctx[, nchar_total := nchar(content)]
ctx[, dens_elderfood := 1e4 * n_elderfood / nchar_total]
ctx[, dens_placebo   := 1e4 * n_placebo   / nchar_total]

# audit fix (2026-07): county names repeat across provinces, so every county-level
# key below is (provn, countyn), never countyn alone.
county_panel <- ctx[, .(n_reports = .N, n_elderfood = sum(n_elderfood),
                        dens_elderfood = mean(dens_elderfood), dens_placebo = mean(dens_placebo)),
                    by = .(provn, countyn, year)][order(provn, countyn, year)]
first_mention <- county_panel[n_elderfood > 0, .(t0_county = min(year)), by = .(provn, countyn)]
intensity <- county_panel[year >= 2018, .(policy_intensity = mean(dens_elderfood),
                                          placebo_intensity = mean(dens_placebo)), by = .(provn, countyn)]
intensity[, policy_intensity_z := as.numeric(scale(policy_intensity))]
county_panel <- merge(county_panel, first_mention, by = c("provn","countyn"), all.x = TRUE)
fwrite(county_panel, file.path(DIR_DERIV, "county_policy_panel.csv"))
fwrite(intensity, file.path(DIR_DERIV, "county_policy_intensity.csv"))

# --- validity sample: 100 keyword sentences for manual audit -------------------
sent <- ctx[n_elderfood > 0, {
  ss <- unlist(strsplit(content, "[。；;]"))
  hit <- ss[str_detect(ss, paste(KW_ELDERFOOD, collapse = "|"))]
  .(sentence = hit)
}, by = .(provn, countyn, year)]
set.seed(5)
audit_smp <- sent[sample(.N, min(100, .N))]
fwrite(audit_smp, file.path(DIR_REP, "text_validity_sample_100.csv"))

# --- fig9: diffusion timeline ---------------------------------------------------
diff <- county_panel[, .(share_mentioning = mean(n_elderfood > 0)), by = year][order(year)]
p9 <- ggplot(diff[year >= 2010], aes(year, share_mentioning)) +
  geom_line(linewidth = 1, colour = "firebrick") + geom_point(size = 2) +
  scale_y_continuous(labels = scales::percent) +
  labs(x = NULL, y = "Share of sample counties",
       title = "Diffusion of elder-feeding policy language in county government work reports",
       subtitle = sprintf("Keyword family: %s", paste(KW_ELDERFOOD[1:5], collapse = " / "))) +
  theme_minimal(base_size = 12)
ggsave(file.path(DIR_FIG, "fig9_policy_diffusion.png"), p9, width = 8.5, height = 5, dpi = 200)

# --- T18: exploratory moderation ------------------------------------------------
per <- fread(file.path(DIR_DERIV, "person_analysis.csv"), colClasses = list(character = c("nhCode","pid","xzc12")))
LA_LEVELS <- c("cohabit_nonelder","elder_only_multi","threegen","elder_alone","elder_child","other")
eld <- per[elderly == 1 & !is.na(num(fgds10)) & living_arrangement %in% LA_LEVELS]
eld[, `:=`(fgds10 = num(fgds10), LA = relevel(factor(living_arrangement, levels = LA_LEVELS), ref = "cohabit_nonelder"))]
eld[is.na(main_cook), main_cook := 0]
eld[, prov_year := paste(provn, data_year)]
eld <- merge(eld, intensity[, .(provn, countyn, policy_intensity_z, placebo_intensity)],
             by = c("provn","countyn"), all.x = TRUE)
eld[, county_id := paste(provn, countyn)]
eld[, solo_or_elderonly := as.integer(living_arrangement %in% c("elder_alone","elder_only_multi"))]

m18  <- feols(fgds10 ~ solo_or_elderonly*policy_intensity_z + female + main_cook + ln_income | prov_year,
              data = eld, cluster = ~county_id)
m18p <- feols(fgds10 ~ solo_or_elderonly*placebo_intensity + female + main_cook + ln_income | prov_year,
              data = eld, cluster = ~county_id)
t18 <- rbind(tidy_fe(m18,  "solo|policy")[, spec := "elder-feeding intensity"],
             tidy_fe(m18p, "solo|placebo")[, spec := "placebo: general commerce"])
wtab(t18, "table18_policy_text_moderation.csv")

int_p <- coeftable(m18)["solo_or_elderonly:policy_intensity_z", ]
writeLines(c("# County policy text (exploratory)",
  sprintf("- Counties matched: %d/%d; county-year reports with text: %d", nrow(matched), nrow(samp_cty), nrow(ctx)),
  sprintf("- Moderation solo/elder-only x policy intensity: %.3f (p=%.3f) — %s", int_p[1], int_p[4],
          ifelse(int_p[1] > 0 & int_p[4] < .1, "consistent with S2 offset story",
          ifelse(int_p[1] < 0 & int_p[4] < .1, "D8: negative — interpret as endogenous targeting, report honestly",
                 "imprecise — descriptive context only"))),
  "- Validity: 100 keyword sentences exported for manual audit (target >=85% true elder-feeding policy content).",
  "- Red line respected: county-level context variable only."),
  file.path(DIR_REP, "county_policy_text_summary.md"))
cat("POLICY TEXT OK\n"); print(t18[, .(spec, term, est, se, p)])
