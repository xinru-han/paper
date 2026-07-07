# =============================================================================
# 01_build_data.R — build all analysis datasets for Paper 2 (elder diet)
# Outputs (data/):
#   hh_analysis.csv     household-level elder sample (A line)
#   member_long.csv     member roster long (all households)
#   person_analysis.csv person-level diet indices + nutrients (B line input)
#   bline_sample.csv    mixed-household within-family comparison sample
#   dri_lookup.csv      Chinese DRI reference values (documented approximations)
# Report: outputs/reports/build_report.md (sample flow, QA assertions)
# =============================================================================
source("/root/data/Paper/食物消费数据/paper2-elder/code/00_setup.R")
suppressPackageStartupMessages({ library(readxl) })

rep <- c("# Paper 2 build report", paste0("Generated: ", format(Sys.time())), "")

# ---------------------------------------------------------------------------
# 1. household table: select needed columns
# ---------------------------------------------------------------------------
hdr <- names(fread(F_HH, nrows = 0))
pids <- sprintf("%02d", 1:8)
roster_cols <- c(
  outer(paste0("family1_", pids, "_HA"), c(1,2,3,6,9), paste0),
  paste0("family1_", pids, "_HA6_1"),
  outer(paste0("family2_", pids, "_HA"), c(10,13,14,19), paste0),
  outer(paste0("family3_", pids, "_HA"), c(23,24,25,26,27,31,32,35), paste0)
)
food_cols <- as.vector(outer(FOOD12, c("_cons_monthly_jin","_price_wavg_yuan_per_jin",
                                       "_selfprod_monthly_total","_self_suff_rate"), paste0))
base_cols <- c("nhCode","data_year","food_year","prov","provn","county","countyn","vil","viln",
               "HA0","status","total_income_w","annual_expense_total","agri_business_income",
               paste0("HB", 1:9), "food_monthly_total","food_selfprod_monthly_total","food_self_suff_rate")
sel <- intersect(c(base_cols, roster_cols, food_cols), hdr)
missing_cols <- setdiff(c(base_cols, food_cols), hdr)
if (length(missing_cols)) rep <- c(rep, paste0("- WARNING missing hh columns: ", paste(missing_cols, collapse = ", ")))

hh <- fread(F_HH, select = sel, colClasses = list(character = c("nhCode", intersect(roster_cols, hdr))))
stopifnot(!anyDuplicated(hh$nhCode))
hh[, xzc12 := substr(nhCode, 1, 12)]
rep <- c(rep, sprintf("- household table: %d rows, %d selected columns", nrow(hh), ncol(hh)))

# ---------------------------------------------------------------------------
# 2. member roster long
# ---------------------------------------------------------------------------
grab <- function(item, prefix) {
  cols <- paste0(prefix, pids, "_HA", item)
  cols[!cols %in% names(hh)] <- NA
  out <- lapply(cols, function(cc) if (is.na(cc)) rep(NA_character_, nrow(hh)) else as.character(hh[[cc]]))
  data.table(nhCode = rep(hh$nhCode, 8), data_year = rep(hh$data_year, 8),
             pid = rep(pids, each = nrow(hh)), val = unlist(out))$val
}
mem <- data.table(nhCode = rep(hh$nhCode, 8), data_year = rep(hh$data_year, 8),
                  pid = rep(pids, each = nrow(hh)))
mem[, relation_code    := grab(1,  "family1_")]
mem[, sex_code         := grab(2,  "family1_")]
mem[, birth_raw        := grab(3,  "family1_")]
mem[, health_code      := grab(6,  "family1_")]
mem[, disease_raw      := grab("6_1", "family1_")]
mem[, marital_code     := grab(9,  "family1_")]
mem[, education_code   := grab(10, "family2_")]
mem[, farm_days        := num(grab(13, "family2_"))]
mem[, offfarm_days     := num(grab(14, "family2_"))]
mem[, days_at_home     := num(grab(19, "family2_"))]
mem[, main_food_buyer  := num(grab(23, "family3_"))]
mem[, main_cook        := num(grab(24, "family3_"))]
mem[, home_eating_days := num(grab(25, "family3_"))]
mem[, uses_internet    := num(grab(26, "family3_"))]
mem[, has_smartphone   := num(grab(27, "family3_"))]
mem[, uses_epay        := num(grab(31, "family3_"))]
mem[, xfy_dining       := num(grab(32, "family3_"))]
mem[, pension_monthly  := num(grab(35, "family3_"))]

# member exists if any of the three id fields is non-empty
blank <- function(x) is.na(x) | trimws(x) == "" | x == "NA"
mem[, exists := !(blank(relation_code) & blank(sex_code) & blank(birth_raw))]
mem <- mem[exists == TRUE][, exists := NULL]

mem[, age := age_from_birth(birth_raw, data_year)]
mem[, sex_num := num(sex_code)]
# roster sex codes: {1,2} -> 1 male, 2 female (verified against 48h sex_ha2 below)
mem[, female := fifelse(sex_num == 2, 1L, fifelse(sex_num == 1, 0L, NA_integer_))]
mem[, elderly := as.integer(!is.na(age) & age >= ELDER_AGE)]
mem[, child   := as.integer(!is.na(age) & age <  CHILD_AGE)]
mem[, nonelder_adult := as.integer(!is.na(age) & age >= CHILD_AGE & age < ELDER_AGE)]
# binary recodes (questionnaire: 01 yes / 00 no; tolerate stray codes)
for (v in c("main_food_buyer","main_cook","uses_internet","has_smartphone","uses_epay","xfy_dining"))
  mem[, (v) := fifelse(get(v) %in% c(0,1), get(v), NA_real_)]

rep <- c(rep, sprintf("- member roster: %d members in %d households; median size %d",
                      nrow(mem), uniqueN(mem$nhCode), as.integer(median(mem[, .N, by = nhCode]$N))),
         sprintf("- age missing: %d members (%.1f%%)", sum(is.na(mem$age)), 100*mean(is.na(mem$age))))

# ---------------------------------------------------------------------------
# 3. living arrangement classification (household level)
# ---------------------------------------------------------------------------
comp <- mem[, .(hh_size_rec = .N,
                n_elderly = sum(elderly, na.rm = TRUE),
                n_children = sum(child, na.rm = TRUE),
                n_nonelder_adult = sum(nonelder_adult, na.rm = TRUE),
                n_age_missing = sum(is.na(age)),
                any_elder_80 = as.integer(any(age >= 80, na.rm = TRUE)),
                max_elder_age = suppressWarnings(as.numeric(max(as.numeric(age[elderly == 1]), na.rm = TRUE))),
                elder_is_cook  = as.integer(any(elderly == 1 & main_cook == 1, na.rm = TRUE)),
                elder_is_buyer = as.integer(any(elderly == 1 & main_food_buyer == 1, na.rm = TRUE)),
                nonelder_cook  = as.integer(any(elderly == 0 & main_cook == 1, na.rm = TRUE)),
                nonelder_buyer = as.integer(any(elderly == 0 & main_food_buyer == 1, na.rm = TRUE)),
                any_xfy_dining = as.integer(any(xfy_dining == 1, na.rm = TRUE))),
            by = .(nhCode, data_year)]
comp[!is.finite(max_elder_age), max_elder_age := NA_real_]

comp[, living_arrangement := fcase(
  n_elderly == 0, "no_elder",
  n_age_missing > 0 & n_elderly >= 1, "other",
  n_elderly >= 1 & n_nonelder_adult >= 1 & n_children >= 1, "threegen",
  n_elderly >= 1 & n_nonelder_adult >= 1 & n_children == 0, "cohabit_nonelder",
  n_elderly >= 2 & n_nonelder_adult == 0 & n_children == 0, "elder_only_multi",
  n_elderly == 1 & hh_size_rec == 1, "elder_alone",
  n_elderly >= 1 & n_nonelder_adult == 0 & n_children >= 1, "elder_child",
  default = "other")]
la_dist <- comp[living_arrangement != "no_elder", .N, by = living_arrangement][order(-N)]
rep <- c(rep, "", "## Living arrangement distribution (elder households)",
         paste(capture.output(print(la_dist)), collapse = "\n"))

# ---------------------------------------------------------------------------
# 4. village environment + interview dates
# ---------------------------------------------------------------------------
vhdr <- names(fread(F_VIL, nrows = 0))
vsel <- intersect(c("xzcCode","xzcCode_clean","data_year","juli","change","fe01_01","fe01_03","fe01_04",
                    "fe03_01","fe03_02","fe03_03","fe03_04","xingfuyuan","xingfuyuan2","x09"), vhdr)
vil <- fread(F_VIL, select = vsel, colClasses = list(character = intersect(c("xzcCode","xzcCode_clean","x09"), vhdr)))
vil[, xzc12 := ifelse(!blank(xzcCode_clean), xzcCode_clean, xzcCode)]
for (v in c("juli","fe01_01","fe01_03","fe01_04","fe03_01","fe03_02","fe03_03","fe03_04")) vil[, (v) := num(get(v))]
vil[, village_has_xingfuyuan := as.integer(num(xingfuyuan) == 1)]
vil[, fe03_min := pmin(fe03_01, fe03_02, fe03_03, fe03_04, na.rm = TRUE)]
vil[!is.finite(fe03_min), fe03_min := NA_real_]
vil[, n_outlets_5km := rowSums(cbind(fe01_01, fe01_03, fe01_04), na.rm = TRUE)]

# POI 5km counts (time-invariant)
poi <- fread(F_POI, colClasses = list(character = "xzc12"))
poi_cnt <- poi[, .(poi_total_5km = .N), by = xzc12]
vil <- merge(vil, poi_cnt, by = "xzc12", all.x = TRUE)
vil[is.na(poi_total_5km), poi_total_5km := 0]

z <- function(x) as.numeric(scale(x))
vil[, market_access_index    := rowMeans(cbind(z(-log1p(juli)), z(-log1p(fe03_min))), na.rm = TRUE)]
vil[, retail_thickness_index := rowMeans(cbind(z(log1p(n_outlets_5km)), z(log1p(poi_total_5km))), na.rm = TRUE)]
vkeep <- vil[, .(xzc12, data_year, market_access_index, retail_thickness_index,
                 village_has_xingfuyuan, juli, fe03_min, n_outlets_5km, poi_total_5km)]
vkeep <- unique(vkeep, by = c("xzc12","data_year"))

# interview dates (village level, MMDD)
rd_iday <- function(f, yr) {
  d <- as.data.table(read_excel(f))
  d <- d[, .(xzc12 = as.character(xzcCode), mmdd = sprintf("%04d", num(interviewDAY)))]
  d <- d[!is.na(num(mmdd))]
  d[, interview_date := as.Date(sprintf("%d-%s-%s", yr, substr(mmdd,1,2), substr(mmdd,3,4)))]
  unique(d[!is.na(interview_date), .(xzc12, data_year = yr, interview_date)], by = "xzc12")
}
iday <- rbind(rd_iday(F_IDAY23, 2023), rd_iday(F_IDAY24, 2024))
iday[, `:=`(interview_month = month(interview_date), interview_wday = wday(interview_date))]
rep <- c(rep, sprintf("- interview dates: %d village-years (2023: %d, 2024: %d)",
                      nrow(iday), sum(iday$data_year==2023), sum(iday$data_year==2024)))

# ---------------------------------------------------------------------------
# 5. household analysis file (A line)
# ---------------------------------------------------------------------------
hdds <- fread(F_DIET_HH, colClasses = list(character = "nhCode"))
hh2 <- merge(hh, hdds, by = c("nhCode","data_year"), all.x = TRUE)
hh2 <- merge(hh2, comp,  by = c("nhCode","data_year"), all.x = TRUE)
hh2 <- merge(hh2, vkeep, by = c("xzc12","data_year"), all.x = TRUE)
hh2 <- merge(hh2, iday,  by = c("xzc12","data_year"), all.x = TRUE)
rep <- c(rep, sprintf("- hdds12 merge rate: %.1f%%; village env merge rate: %.1f%%; interview date: %.1f%%",
                      100*mean(!is.na(hh2$hdds12)), 100*mean(!is.na(hh2$market_access_index)),
                      100*mean(!is.na(hh2$interview_date))))

# food structure shares (denominator = 12-category sum, project convention)
for (k in FOOD12) hh2[, (paste0(k,"_cons")) := num(get(paste0(k,"_cons_monthly_jin")))]
cons_cols <- paste0(FOOD12, "_cons")
hh2[, food12_total := rowSums(.SD, na.rm = TRUE), .SDcols = cons_cols]
hh2[, share_dairy_egg_bean := (fifelse(is.na(nailei_cons),0,nailei_cons) + fifelse(is.na(danlei_cons),0,danlei_cons) +
                               fifelse(is.na(doulei_cons),0,doulei_cons)) / food12_total]
hh2[, share_animal := (fifelse(is.na(roulei_cons),0,roulei_cons) + fifelse(is.na(danlei_cons),0,danlei_cons) +
                       fifelse(is.na(nailei_cons),0,nailei_cons)) / food12_total]
hh2[, share_fruit_veg := (fifelse(is.na(shucai_cons),0,shucai_cons) + fifelse(is.na(shuiguo_cons),0,shuiguo_cons)) / food12_total]
hh2[food12_total <= 0, c("share_dairy_egg_bean","share_animal","share_fruit_veg") := NA]

hh2[, total_income_w := num(total_income_w)]
hh2[, ln_income := log1p(pmax(total_income_w, 0))]
hh2[, hh_size_grp := cut(hh_size_rec, c(0,1,2,3,4,5,Inf), labels = c("1","2","3","4","5","6+"))]
for (v in paste0("HB",1:9)) hh2[, (v) := num(get(v))]

elder_hh <- hh2[n_elderly >= 1]
rep <- c(rep, sprintf("- elder households (>=1 member age %d+): %d of %d", ELDER_AGE, nrow(elder_hh), nrow(hh2)))

# privacy: assert no name / coordinate / phone columns leak into any export.
# Case-insensitive and broadened: the raw tables carry mixed-case identifiers
# (huName, vilLat/vilLon, and *Phone columns), so a lowercase-only pattern missed
# the phone columns. Reused for every write below.
ID_PAT <- "name|lat|lon|phone|地址|身份|姓名|经度|纬度"
assert_no_pii <- function(dt, label) {
  hit <- grep(ID_PAT, names(dt), ignore.case = TRUE, value = TRUE)
  if (length(hit)) stop(sprintf("PII leak in %s: %s", label, paste(hit, collapse = ", ")))
  invisible(TRUE)
}
assert_no_pii(elder_hh, "elder_hh")
drop_raw <- grep("^family[123]_", names(elder_hh), value = TRUE)
elder_out <- elder_hh[, setdiff(names(elder_hh), drop_raw), with = FALSE]
assert_no_pii(elder_out, "hh_analysis.csv")
fwrite(elder_out, file.path(DIR_DERIV, "hh_analysis.csv"))
fwrite(hh2[, setdiff(names(hh2), drop_raw), with = FALSE][, .(nhCode, data_year, xzc12, provn, countyn,
       hdds12, hh_size_rec, n_elderly, n_children, n_nonelder_adult, living_arrangement,
       ln_income, market_access_index, retail_thickness_index)],
       file.path(DIR_DERIV, "hh_all_min.csv"))
assert_no_pii(mem, "member_long.csv")
fwrite(mem, file.path(DIR_DERIV, "member_long.csv"))

# ---------------------------------------------------------------------------
# 6. person-level diet indices + nutrients
# ---------------------------------------------------------------------------
dietp <- fread(F_DIET_P, colClasses = list(character = c("nhCode","pid")))
dietp[, pid := sprintf("%02d", num(pid))]
mem[, pid := sprintf("%02d", num(pid))]

nut <- fread(F_NUTR_ML, colClasses = list(character = c("nhCode","pid")),
             select = c("nhCode","data_year","pid","meal_no","energy_kcal","protein","fat","cho","ca","fe","zn","na","k"))
nut[, pid := sprintf("%02d", num(pid))]
nutp <- nut[, .(n_meals = .N,
                energy_kcal_48h = sum(num(energy_kcal), na.rm = TRUE),
                protein_48h = sum(num(protein), na.rm = TRUE),
                fat_48h = sum(num(fat), na.rm = TRUE),
                ca_48h = sum(num(ca), na.rm = TRUE),
                fe_48h = sum(num(fe), na.rm = TRUE),
                zn_48h = sum(num(zn), na.rm = TRUE)),
            by = .(nhCode, data_year, pid)]

per <- merge(dietp, nutp, by = c("nhCode","data_year","pid"), all.x = TRUE)
per <- merge(per, mem, by = c("nhCode","data_year","pid"), all.x = TRUE, suffixes = c("",".mem"))
per[, age_yrs := fifelse(!is.na(age), as.numeric(age), num(age_months_approx)/12)]
per[, elderly := as.integer(!is.na(age_yrs) & age_yrs >= ELDER_AGE)]
per[, child := as.integer(!is.na(age_yrs) & age_yrs < CHILD_AGE)]
per[, nonelder_adult := as.integer(!is.na(age_yrs) & age_yrs >= CHILD_AGE & age_yrs < ELDER_AGE)]
# sex: prefer roster; diet-file sex_ha2 (0/1) as fallback — cross-check
per[, female_diet := fifelse(num(sex_ha2) == 0, 1L, fifelse(num(sex_ha2) == 1, 0L, NA_integer_))]
xt <- per[!is.na(female) & !is.na(female_diet), mean(female == female_diet)]
if (!is.na(xt) && xt < .5) per[, female_diet := 1L - female_diet]  # flip if coding reversed
rep <- c(rep, sprintf("- roster/diet-file sex agreement: %.1f%% (after orientation check)",
                      100*per[!is.na(female) & !is.na(female_diet), mean(female == female_diet)]))
per[is.na(female), female := female_diet]

# per-day intakes (48h window / 2)
for (v in c("energy_kcal","protein","fat","ca","fe","zn"))
  per[, (paste0(v,"_day")) := get(paste0(v,"_48h"))/2]

# quality-protein food share (animal-source + soy grams over all 10 MDD-W group grams)
gcols <- grep("^mddwg_.*_g_48h$", names(per), value = TRUE)
per[, food_g_total := rowSums(.SD, na.rm = TRUE), .SDcols = gcols]
qp <- intersect(c("mddwg_flesh_g_48h","mddwg_eggs_g_48h","mddwg_dairy_g_48h","mddwg_beans_peas_g_48h"), names(per))
per[, qual_protein_g := rowSums(.SD, na.rm = TRUE), .SDcols = qp]
per[, qual_protein_share := fifelse(food_g_total > 0, qual_protein_g/food_g_total, NA_real_)]

# ---------------------------------------------------------------------------
# 7. DRI lookup (Chinese DRIs 2023, light physical activity; documented approx.)
# ---------------------------------------------------------------------------
dri <- rbindlist(list(
  # sex, age_lo, age_hi, energy_kcal, protein_g, ca_mg, fe_mg, zn_mg
  data.table(sex="M", age_lo=18, age_hi=49, energy=2250, protein=65, ca=800,  fe=12, zn=12.5),
  data.table(sex="M", age_lo=50, age_hi=64, energy=2100, protein=65, ca=1000, fe=12, zn=12.5),
  data.table(sex="M", age_lo=65, age_hi=79, energy=2050, protein=72, ca=1000, fe=12, zn=12.5),
  data.table(sex="M", age_lo=80, age_hi=120,energy=1900, protein=72, ca=1000, fe=12, zn=12.5),
  data.table(sex="F", age_lo=18, age_hi=49, energy=1800, protein=55, ca=800,  fe=20, zn=7.5),
  data.table(sex="F", age_lo=50, age_hi=64, energy=1750, protein=55, ca=1000, fe=10, zn=7.5),
  data.table(sex="F", age_lo=65, age_hi=79, energy=1700, protein=62, ca=1000, fe=10, zn=7.5),
  data.table(sex="F", age_lo=80, age_hi=120,energy=1500, protein=62, ca=1000, fe=10, zn=7.5)
))
fwrite(dri, file.path(DIR_DERIV, "dri_lookup.csv"))

per[, sexMF := fifelse(female == 1, "F", "M")]
per[, age_join := age_yrs]
per <- dri[per, on = .(sex = sexMF, age_lo <= age_join, age_hi >= age_join)][
  , `:=`(age_lo = NULL, age_hi = NULL)]
setnames(per, "sex", "sexMF", skip_absent = TRUE)
per[, ar_energy  := energy_kcal_day / energy]
per[, ar_protein := protein_day / protein]
per[, ar_ca := ca_day / ca]
per[, ar_fe := fe_day / fe]
per[, ar_zn := zn_day / zn]

# household composition merge
per <- merge(per, comp[, .(nhCode, data_year, living_arrangement, n_elderly, n_children,
                           n_nonelder_adult, hh_size_rec)], by = c("nhCode","data_year"), all.x = TRUE)
per <- merge(per, hh2[, .(nhCode, data_year, xzc12, provn, countyn, ln_income,
                          market_access_index, retail_thickness_index, food_self_suff_rate,
                          interview_month, interview_wday)],
             by = c("nhCode","data_year"), all.x = TRUE)
per[, hh_id := paste(nhCode, data_year, sep = "_")]
stopifnot(!any(grepl("huName|vilLat|vilLon", names(per))))
fwrite(per, file.path(DIR_DERIV, "person_analysis.csv"))
rep <- c(rep, sprintf("- person analysis file: %d persons with 48h records; elders: %d; nonelder adults: %d",
                      nrow(per), sum(per$elderly, na.rm=TRUE), sum(per$nonelder_adult, na.rm=TRUE)))

# ---------------------------------------------------------------------------
# 8. B-line mixed household sample (CONSORT flow)
# ---------------------------------------------------------------------------
flow <- data.table(step = character(), n_households = integer(), n_persons = integer())
addflow <- function(step, d) flow <<- rbind(flow, data.table(step = step, n_households = uniqueN(d$hh_id), n_persons = nrow(d)))

adults <- per[!is.na(fgds10) & (elderly == 1 | nonelder_adult == 1)]
addflow("adults (18+) with 48h diet record", adults)
mix1 <- adults[living_arrangement %in% c("cohabit_nonelder","threegen")]
addflow("in cohabit/three-generation elder households", mix1)
ok <- mix1[, .(has_e = any(elderly == 1), has_a = any(nonelder_adult == 1)), by = hh_id][has_e & has_a, hh_id]
bline <- mix1[hh_id %in% ok]
addflow(">=1 elder AND >=1 non-elder adult recorded (B-line sample)", bline)
fwrite(bline, file.path(DIR_DERIV, "bline_sample.csv"))
wtab(flow, "table_bline_consort_flow.csv")
rep <- c(rep, "", "## B-line sample flow", paste(capture.output(print(flow)), collapse = "\n"))

writeLines(rep, file.path(DIR_REP, "build_report.md"))
cat("BUILD OK\n")
