# Paper 8 script 03: lookup tables
#  (a) lockdown windows (hand-compiled, same table as Paper 2 plan §0.3)
#  (b) category -> group10 map + perishability class
#  (c) nutrient coefficients per kg as-purchased, from 中国食物成分表
#      (新版营养成分表.zip, values per 100g edible portion x 食部)
source("/root/data/Paper/央视数据/paper8-hot/code/00_setup.R")

## ---------------------------------------------------------------- (a) lockdowns
lockdown <- data.table(
  province = c("湖北省","新疆维吾尔自治区","河北省","陕西省","吉林省","上海市","广东省","广东省"),
  city     = c("武汉","乌鲁木齐","石家庄","西安","长春","上海","深圳","广州"),
  start    = as.IDate(c("2020-01-23","2020-07-16","2021-01-06","2021-12-23","2022-03-11","2022-04-01","2022-03-14","2022-11-05")),
  end      = as.IDate(c("2020-04-08","2020-08-31","2021-02-08","2022-01-24","2022-04-28","2022-06-01","2022-03-20","2022-11-30")),
  clean_single_shock = c(1,1,1,1,1,1,0,0)
)
fwrite(lockdown, file.path(DIR_LKP, "lockdown_windows.csv"))

## ------------------------------------------------- (b) categories & perishability
# perish class: fresh (cold-chain dependent, days) / semi (weeks) / storable (months)
catmap <- fread(text = '
Category,food_group10,perish_class
大米,G01_主食,storable
面粉,G01_主食,storable
挂面,G01_主食,storable
方便面,G01_主食,storable
食用油,G02_食用油,storable
蔬菜,G03_蔬菜,fresh
水果,G04_水果,fresh
猪肉,G05_猪肉,fresh
禽类,G06_禽类及其他肉类,fresh
其他肉类,G06_禽类及其他肉类,fresh
牛肉,G07_牛羊肉,fresh
羊肉,G07_牛羊肉,fresh
海鲜类,G08_海鲜,fresh
新鲜牛奶,G09_乳制品,fresh
新鲜酸奶,G09_乳制品,fresh
常温牛奶,G09_乳制品,storable
常温酸奶,G09_乳制品,semi
成人奶粉,G09_乳制品,storable
奶酪,G09_乳制品,semi
黄油,G09_乳制品,semi
坚果,G10_坚果,storable
')
fwrite(catmap, file.path(DIR_LKP, "category_map.csv"))

## ------------------------------------------------------------- (c) nutrients
# representative foods per monitored category (file names in 新版营养成分表);
# nutrient values are per 100 g EDIBLE portion; multiply by 食部 share to get
# per 100 g as-purchased, then x10 -> per kg.
rep_foods <- list(
  蔬菜   = c("大白菜(均值).csv","番茄[西红柿].csv","黄瓜[胡瓜](鲜).csv","菠菜[赤根菜](鲜).csv","白萝卜[莱菔](鲜).csv"),
  水果   = c("苹果(均值).csv","香蕉[甘蕉].csv","梨(均值).csv","橙.csv","西瓜(均值).csv"),
  猪肉   = c("猪肉(肥瘦)(均值).csv"),
  牛肉   = c("牛肉(肥瘦)(均值).csv"),
  羊肉   = c("羊肉(肥瘦)(均值).csv"),
  禽类   = c("鸡(均值).csv","鸭(均值).csv"),
  其他肉类 = c("兔肉.csv","牛肉(肥瘦)(均值).csv","羊肉(肥瘦)(均值).csv"),
  海鲜类 = c("草鱼[白鲩，草包鱼].csv","鲤鱼[鲤拐子].csv","带鱼[白带鱼，刀鱼].csv","虾（海虾）.csv"),
  新鲜牛奶 = c("牛乳(光明牌).csv","牛乳(伊利牌).csv","牛乳(蒙牛牌).csv"),
  常温牛奶 = c("牛乳(光明牌).csv","牛乳(伊利牌).csv","牛乳(蒙牛牌).csv"),
  新鲜酸奶 = c("酸奶(调味).csv","酸奶(果粒).csv"),
  常温酸奶 = c("酸奶(调味).csv","酸奶(果粒).csv"),
  成人奶粉 = c("全脂奶粉(伊利牌).csv","全脂奶粉(雀巢).csv"),
  奶酪   = c("奶酪[干酪].csv"),
  黄油   = c("黄油.csv"),
  坚果   = c("花生仁(生).csv","核桃(干)[胡桃].csv"),
  食用油 = c("花生油.csv","豆油.csv","色拉油.csv"),
  方便面 = c("方便面.csv")
)

num_of <- function(x) {  # "442KJ" -> 442 ; "19.2g" -> 19.2 ; "" / "—" -> NA
  v <- suppressWarnings(as.numeric(gsub("[^0-9.\\-]", "", x)))
  ifelse(is.finite(v), v, NA_real_)
}

read_food <- function(f) {
  d <- fread(file.path(NUTZ, f), encoding = "UTF-8")
  setnames(d, c("type","item","value","rank","mean","level"))
  get <- function(pat, unit_kj = FALSE) {
    r <- d[grepl(pat, item)][1]
    if (nrow(r) == 0) return(NA_real_)
    num_of(r$value)
  }
  edible <- get("食部") / 100          # share
  if (!is.finite(edible) || edible <= 0 || edible > 1) edible <- 1
  data.table(
    edible   = edible,
    kcal     = get("能量\\(Energy\\)") / 4.184,   # KJ -> kcal per 100g edible
    protein  = get("蛋白质"),
    fat      = get("脂肪\\(Fat\\)"),
    cho      = get("碳水化合物"),
    fe_mg    = get("铁\\(Fe\\)"),
    ca_mg    = get("钙\\(Ca\\)"),
    zn_mg    = get("锌\\(Zn\\)"),
    va_ug    = get("维生素A")
  )
}

nut <- rbindlist(lapply(names(rep_foods), function(cat) {
  fl <- rep_foods[[cat]][file.exists(file.path(NUTZ, rep_foods[[cat]]))]
  if (length(fl) == 0) return(NULL)
  vals <- rbindlist(lapply(fl, read_food))
  # per kg as-purchased = per100g_edible * edible_share * 10
  out <- vals[, lapply(.SD, function(x) mean(x * edible * 10, na.rm = TRUE)), .SDcols = setdiff(names(vals), "edible")]
  out[, Category := cat][, n_rep_foods := length(fl)][]
}), fill = TRUE)

# staples missing from the zip: standard values, 中国食物成分表(第6版) per 100g
# edible (edible share ~1 for milled rice/flour/dried noodles), x10 -> per kg
manual <- data.table(
  Category = c("大米","面粉","挂面"),
  kcal    = c(346, 349, 353) * 10,
  protein = c(7.9, 11.2, 11.4) * 10,
  fat     = c(0.9, 1.5, 0.9) * 10,
  cho     = c(77.2, 73.6, 75.1) * 10,
  fe_mg   = c(1.1, 3.5, 3.0) * 10,
  ca_mg   = c(8, 27, 20) * 10,
  zn_mg   = c(1.45, 1.64, 1.2) * 10,
  va_ug   = c(0, 0, 0),
  n_rep_foods = 0L
)
nut <- rbind(nut, manual, fill = TRUE)
setcolorder(nut, c("Category"))
fwrite(nut, file.path(DIR_LKP, "nutrient_coef_cn.csv"))
logmsg("03 lookups done: ", nrow(lockdown), " lockdown rows; ", nrow(catmap), " categories; ", nrow(nut), " nutrient rows")
print(nut[, .(Category, kcal, protein, fe_mg)])
