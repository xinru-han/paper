# Paper 9 script 90a: unit-value library + household-month budget panel.
#  - parse transactions, build hh x month total food spend & 14-good shares
#  - PK13 unit values: unit diagnostics, trimming, hh x month x category panel
source("/root/data/Paper/央视数据/paper9-easiq/code/00_setup.R")

tr <- fread(file.path(RAW, "Data_merged.csv"), encoding = "UTF-8",
            select = c("ID","Province","Family_Type","Family_Size","Family_Income",
                       "Date","Category","Spend","Volume"))
tr[grepl("/", Date), date := as.IDate(Date, format = "%Y/%m/%d")]
tr[is.na(date), date := as.IDate(substr(Date, 1, 10), format = "%Y-%m-%d")]
tr[, Date := NULL]
tr <- tr[Spend > 0 & is.finite(Spend)]
tr[, ym := format(date, "%Y-%m")]
if (DEBUG) { keep_id <- sample(unique(tr$ID), 3000); tr <- tr[ID %in% keep_id] }
logmsg("90a: ", nrow(tr), " transactions, ", uniqueN(tr$ID), " households")

## ---- household attributes at hh x month (income band = modal within month)
hhm_attr <- tr[, .(inc_band = names(sort(table(Family_Income), decreasing = TRUE))[1],
                   fam_type = Family_Type[1], fam_size = Family_Size[1],
                   Province = Province[1]), by = .(ID, ym)]
hhm_attr[, `:=`(inc_mid = income_mid(inc_band), fsize = famsize_mid(fam_size))]
tier <- fread(file.path(P8, "data/interim/hh_info.csv"), encoding = "UTF-8",
              select = c("ID","tier_a","CityTier"))
hhm_attr <- merge(hhm_attr, tier, by = "ID", all.x = TRUE)
fwrite(hhm_attr, file.path(DIR_INT, "hhm_attr.csv.gz"))

## ---- hh x month budget: total food spend + 14-good spends/shares
tr[, good := fifelse(Category %in% PK13, Category, COMP)]
bud <- tr[, .(spend = sum(Spend)), by = .(ID, ym, good)]
tot <- bud[, .(x = sum(spend)), by = .(ID, ym)]
budw <- dcast(bud, ID + ym ~ good, value.var = "spend", fill = 0)
budw <- merge(budw, tot, by = c("ID","ym"))
fwrite(budw, file.path(DIR_INT, "hhm_budget.csv.gz"))
logmsg("90a: budget panel ", nrow(budw), " hh-months; mean x=", round(mean(tot$x), 1))

## ---- PK13 unit values: clean & aggregate
uv <- tr[Category %in% PK13 & Volume > 0 & is.finite(Volume)]
uv[, uvi := Spend / Volume]
uv <- uv[is.finite(uvi) & uvi > 0]

## unit diagnostics: within category, flag mass near 2x / 0.5x the category
## median (unit-mixing signature); and category-province trimming 1%/99%
diag <- uv[, {
  m <- median(uvi); l <- log(uvi / m)
  .(n = .N, med = m, p1 = quantile(uvi, .01), p99 = quantile(uvi, .99),
    mass_2x  = mean(abs(l - log(2)) < 0.15),
    mass_half = mean(abs(l + log(2)) < 0.15),
    iqr_ratio = quantile(uvi, .75) / quantile(uvi, .25))
}, by = Category]
diag[, unit_flag := fifelse(mass_2x > 0.10 | mass_half > 0.10, "check", "ok")]
fwrite(diag, file.path(DIR_TAB, "t1a_uv_unit_diagnostics.csv"))
logmsg("90a: unit diagnostics — flagged: ",
       paste(diag[unit_flag == "check", Category], collapse = ", "), " (none = clean)")

uv[, `:=`(q01 = quantile(uvi, .01), q99 = quantile(uvi, .99)), by = .(Category, Province)]
uv[, medcp := median(uvi), by = .(Category, Province)]
n0 <- nrow(uv)
uv <- uv[uvi >= q01 & uvi <= q99 & uvi >= medcp / 5 & uvi <= medcp * 5]
logmsg("90a: trimming dropped ", n0 - nrow(uv), " of ", n0,
       " uv transactions (", round(100 * (n0 - nrow(uv)) / n0, 2), "%)")

## hh x month x category: spend-weighted uv, quantity, spend
uvm <- uv[, .(uv = sum(Spend) / sum(Volume), uv_med = median(uvi),
              Q = sum(Volume), X = sum(Spend), ntr = .N), by = .(ID, ym, Category)]
fwrite(uvm, file.path(DIR_INT, "uv_hh_month_cat.csv.gz"))

## T1: descriptives incl. Volume coverage per category
cov <- tr[Category %in% PK13, .(n_tr = .N, vol_cov = mean(Volume > 0 & is.finite(Volume))),
          by = Category]
t1 <- merge(cov, diag[, .(Category, med_uv = med, p1, p99, mass_2x, unit_flag)], by = "Category")
t1 <- merge(t1, uvm[, .(n_hhm = .N, uv_hm_med = median(uv)), by = Category], by = "Category")
fwrite(t1[order(-n_tr)], file.path(DIR_TAB, "t1_uv_descriptives.csv"))
logmsg("90a: done — uv hh-month-cat rows: ", nrow(uvm))
