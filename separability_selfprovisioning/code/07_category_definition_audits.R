source("code/00_setup.R")

label_file <- path("raw_data", "户表数据_已清洗_变量标签.csv")
lab <- read_csv(label_file)

label_text <- paste(lab$var, lab$label)
roulei_hits <- lab[grepl("roulei|shuichan|肉类|水产|鱼|虾|蟹|贝", label_text, ignore.case = TRUE), ]
youzhi_hits <- lab[grepl("youzhi|油脂|油料|植物油|猪油|食用油", label_text, ignore.case = TRUE), ]

has_shuichan <- any(grepl("shuichan|水产|鱼|虾|蟹|贝", paste(roulei_hits$var, roulei_hits$label), ignore.case = TRUE))
has_roulei <- any(grepl("roulei|肉类", paste(roulei_hits$var, roulei_hits$label), ignore.case = TRUE))
has_youliao_prod <- any(grepl("youliao_shengchan|油料", paste(youzhi_hits$var, youzhi_hits$label), ignore.case = TRUE))
has_youzhi_consumption <- any(grepl("youzhi", youzhi_hits$var, ignore.case = TRUE))

audit <- data.frame(
  audit_item = c("roulei_split", "youzhi_definition"),
  status = c(
    ifelse(has_shuichan && has_roulei, "partially_feasible_raw_detail_present", "not_feasible_no_raw_detail_found"),
    ifelse(has_youzhi_consumption, "partially_identified_human_review_required", "unclear_human_review_required")
  ),
  evidence = c(
    paste0("Variable labels include roulei meat-detail variables and shuichan/aquatic-detail variables: ", has_shuichan, ". Current analysis-ready long data has only aggregate `roulei` outcome."),
    paste0("Variable labels include youzhi consumption variables: ", has_youzhi_consumption, "; oilseed production module variables: ", has_youliao_prod, ". Item-level labels do not clearly map youzhi_1-youzhi_6 to oil crops versus edible oils.")
  ),
  decision = c(
    "Do not split roulei in the revised rerun without rebuilding detail-level outcomes and prices. Report as human-review flag.",
    "Use current aggregate `youzhi` as oils category, but avoid strong substantive claims before item-code review."
  ),
  human_review_required = c(TRUE, TRUE),
  stringsAsFactors = FALSE
)
write_csv(audit, path("outputs", "tables", "tableD_category_definition_audits.csv"))

roulei_log <- c(
  "# Roulei Split Audit",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Finding",
  "",
  paste0("- Raw labels contain meat-detail variables: ", has_roulei, "."),
  paste0("- Raw labels contain aquatic-detail variables such as `shuichan_1`: ", has_shuichan, "."),
  "- The current analysis-ready household-category long data contains only the aggregate `roulei` category and does not contain separate `meat` and `aquatic_products` outcomes.",
  "- A split would require rebuilding consumption, self-provisioning participation, self-production amount, price, and self-sufficiency outcomes from item-level raw variables.",
  "",
  "## Decision",
  "",
  "- Roulei split is not performed in this revised rerun.",
  "- Human review is required before making split-category claims."
)
writeLines(roulei_log, path("outputs", "logs", "roulei_split_audit.md"), useBytes = TRUE)

youzhi_log <- c(
  "# Youzhi Definition Audit",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "## Finding",
  "",
  paste0("- Raw labels contain aggregate `youzhi` consumption/source variables: ", has_youzhi_consumption, "."),
  paste0("- Raw labels contain oilseed production module variables (`youliao_shengchan`): ", has_youliao_prod, "."),
  "- The food-category documentation defines `youzhi` as `油脂类`.",
  "- The available labels do not clearly state whether the strong `youzhi` result reflects oil crops, home-produced edible oil, self-retained oilseeds, purchased oils with self-production source, or a mixture.",
  "",
  "## Decision",
  "",
  "- Keep `youzhi` as the aggregate oils category in revised models.",
  "- Human review required before making strong substantive claims about the oil category."
)
writeLines(youzhi_log, path("outputs", "logs", "youzhi_definition_audit.md"), useBytes = TRUE)

message("Category definition audits completed.")