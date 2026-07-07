# =============================================================================
# 03_descriptives.R — Table 1 (household by living arrangement), person table,
# Fig1 HDDS by living arrangement, Fig2 elder fgds10 by LA
# =============================================================================
source("/root/data/Paper/食物消费数据/paper2-elder/code/00_setup.R")
suppressPackageStartupMessages({ library(ggplot2) })

hh  <- fread(file.path(DIR_DERIV, "hh_analysis.csv"), colClasses = list(character = "nhCode"))
per <- fread(file.path(DIR_DERIV, "person_analysis.csv"), colClasses = list(character = c("nhCode","pid")))

LA_LEVELS <- c("cohabit_nonelder","elder_only_multi","threegen","elder_alone","elder_child","other")
LA_LAB <- c(cohabit_nonelder = "With non-elder adults", elder_only_multi = "Elder-only (2+)",
            threegen = "Three generations", elder_alone = "Elder living alone",
            elder_child = "Elder + children", other = "Other/age missing")
hh[, LA := factor(living_arrangement, levels = LA_LEVELS)]

# ---- Table 1: household characteristics by LA -------------------------------
vars <- c("hdds12","food12_total","share_dairy_egg_bean","share_animal","share_fruit_veg",
          "food_self_suff_rate","total_income_w","hh_size_rec","n_elderly","n_children",
          "any_elder_80","market_access_index","retail_thickness_index","village_has_xingfuyuan")
t1 <- hh[, c(list(N = .N), lapply(.SD, function(x) mean(num(x), na.rm = TRUE))), by = LA, .SDcols = vars][order(LA)]
allrow <- hh[, c(list(LA = factor("All")), list(N = .N), lapply(.SD, function(x) mean(num(x), na.rm = TRUE))), .SDcols = vars]
t1 <- rbind(t1, allrow, fill = TRUE)
wtab(t1, "table1_household_by_LA.csv")

# ---- Table 1b: elder individuals with 48h records ---------------------------
eld <- per[elderly == 1 & !is.na(fgds10)]
eld[, LA := factor(living_arrangement, levels = LA_LEVELS)]
t1b <- eld[, .(N = .N, age = mean(age_yrs, na.rm = TRUE), female = mean(female, na.rm = TRUE),
               fgds10 = mean(num(fgds10), na.rm = TRUE), fvs = mean(num(fvs_unique_foods), na.rm = TRUE),
               dbi_variety = mean(num(dbi16_variety_subscore), na.rm = TRUE),
               is_cook = mean(main_cook, na.rm = TRUE), is_buyer = mean(main_food_buyer, na.rm = TRUE),
               home_eating_days = mean(home_eating_days, na.rm = TRUE)), by = LA][order(LA)]
wtab(t1b, "table1b_elder_individuals_by_LA.csv")

# ---- Fig 1: HDDS-12 distribution by living arrangement ----------------------
p1 <- ggplot(hh[!is.na(hdds12) & !is.na(LA)], aes(x = LA, y = hdds12)) +
  geom_boxplot(outlier.alpha = .2, fill = "steelblue", alpha = .6) +
  stat_summary(fun = mean, geom = "point", shape = 23, size = 3, fill = "orange") +
  scale_x_discrete(labels = function(x) LA_LAB[x]) +
  labs(x = NULL, y = "Household dietary diversity (HDDS-12, 48h)",
       title = "Household dietary diversity by living arrangement",
       subtitle = sprintf("Elder households, pooled 2023-2024 (N=%d); diamond = mean", nrow(hh[!is.na(hdds12)]))) +
  theme_minimal(base_size = 12) + theme(axis.text.x = element_text(angle = 20, hjust = 1))
ggsave(file.path(DIR_FIG, "fig1_hdds_by_LA.png"), p1, width = 9, height = 5.5, dpi = 200)

# ---- Fig 2: elder individual diversity by LA --------------------------------
p2 <- ggplot(eld[!is.na(LA)], aes(x = LA, y = num(fgds10))) +
  geom_boxplot(outlier.alpha = .2, fill = "darkseagreen", alpha = .7) +
  stat_summary(fun = mean, geom = "point", shape = 23, size = 3, fill = "orange") +
  scale_x_discrete(labels = function(x) LA_LAB[x]) +
  labs(x = NULL, y = "Elder individual dietary diversity (FGDS-10, 48h)",
       title = "Older adults' individual dietary diversity by living arrangement",
       subtitle = sprintf("Elders (60+) with 48h records (N=%d)", nrow(eld))) +
  theme_minimal(base_size = 12) + theme(axis.text.x = element_text(angle = 20, hjust = 1))
ggsave(file.path(DIR_FIG, "fig2_elder_fgds_by_LA.png"), p2, width = 9, height = 5.5, dpi = 200)

cat("DESCRIPTIVES OK\n")
print(t1[, .(LA, N, hdds12, share_dairy_egg_bean, total_income_w)])
