# Paper 9 script 90c: quality ladder dictionary + dairy composition panel.
#  - PK13 quality rank by national median uv
#  - dairy-5 within/between decomposition inputs: hh x month dairy uv and
#    subcategory spend shares (Bils-Klenow style decomposition done in 93)
source("/root/data/Paper/央视数据/paper9-easiq/code/00_setup.R")

uvm <- fread(file.path(DIR_INT, "uv_hh_month_cat.csv.gz"), encoding = "UTF-8")
lad <- uvm[, .(uv_med = median(uv), n = .N), by = Category][order(uv_med)]
lad[, rank := .I]
lad[, ladder_group := fcase(Category %in% DAIRY5, "dairy",
                            Category %in% c("大米","面粉","挂面","方便面"), "staple",
                            default = "other")]
fwrite(lad, file.path(DIR_LKP, "quality_ladder.csv"))

## dairy hh x month: overall dairy uv (spend-weighted across the 5 subcats,
## in comparable units only within subcat -> use log uv relative to subcat
## median, weighted) + subcat shares
dd <- uvm[Category %in% DAIRY5]
dd[, l_rel := log(uv) - log(median(uv)), by = Category]   # unit-free within subcat
dai <- dd[, .(r_within = weighted.mean(l_rel, X), X_dairy = sum(X)), by = .(ID, ym)]
shr <- dcast(dd[, .(s = X / sum(X)), by = .(ID, ym, Category)],
             ID + ym ~ Category, value.var = "s", fill = 0)
dai <- merge(dai, shr, by = c("ID","ym"))
## between component: ladder position implied by composition
lp <- lad[Category %in% DAIRY5, .(Category, lstep = log(uv_med) - mean(log(uv_med)))]
for (cc in DAIRY5) if (cc %in% names(dai)) dai[, r_between := 0]
dai[, r_between := 0]
for (cc in intersect(DAIRY5, names(dai)))
  dai[, r_between := r_between + get(cc) * lp[Category == cc, lstep]]
saveRDS(dai, file.path(DIR_INT, "dairy_panel.rds"))
logmsg("90c: ladder + dairy panel (", nrow(dai), " hh-months) done")
