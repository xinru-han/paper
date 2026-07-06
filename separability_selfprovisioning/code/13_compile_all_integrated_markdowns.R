options(warn = 1)

root <- getwd()
report_dir <- file.path(root, "outputs", "reports")
dir.create(report_dir, recursive = TRUE, showWarnings = FALSE)

path <- function(...) file.path(root, ...)

file_info_row <- function(file) {
  info <- file.info(file)
  data.frame(
    file = file,
    relative_path = sub(paste0("^", root, "/?"), "", file),
    size_bytes = info$size,
    size_kb = round(info$size / 1024, 1),
    n_lines = if (file.exists(file) && !dir.exists(file)) length(readLines(file, warn = FALSE, encoding = "UTF-8")) else NA_integer_,
    stringsAsFactors = FALSE
  )
}

read_text <- function(file) {
  paste(readLines(file, warn = FALSE, encoding = "UTF-8"), collapse = "\n")
}

fence_block <- function(text, info = "") {
  paste0("````", info, "\n", text, "\n````")
}

md_table <- function(df) {
  if (nrow(df) == 0) return("")
  cols <- names(df)
  lines <- c(
    paste0("| ", paste(cols, collapse = " | "), " |"),
    paste0("|", paste(rep("---", length(cols)), collapse = "|"), "|")
  )
  for (i in seq_len(nrow(df))) {
    vals <- vapply(df[i, , drop = FALSE], function(x) as.character(x[1]), character(1))
    vals <- gsub("\\|", "\\\\|", vals)
    lines <- c(lines, paste0("| ", paste(vals, collapse = " | "), " |"))
  }
  paste(lines, collapse = "\n")
}

relative <- function(file) sub(paste0("^", root, "/?"), "", file)

## -------------------------------------------------------------------------
## Integrated results package
## -------------------------------------------------------------------------

result_md <- file.path(report_dir, "paper1_all_results_integrated.md")
code_md <- file.path(report_dir, "paper1_all_code_integrated.md")

report_files <- sort(list.files(path("outputs", "reports"), pattern = "\\.md$", full.names = TRUE))
superseded_report_files <- path("outputs", "reports", c(
  "paper1_unit_kg_month_descriptive_check.md"
))
superseded_log_files <- path("outputs", "logs", c(
  "unit_kg_month_check.md"
))
superseded_table_files <- path("outputs", "tables", c(
  "paper1_unit_conversion_audit_kg_month.csv",
  "paper1_key_variable_descriptives_kg_month.csv",
  "paper1_category_outcome_descriptives_kg_month.csv",
  "paper1_top_extreme_values_kg_month.csv",
  "paper1_unit_checks_kg_month.csv"
))
superseded_files <- c(superseded_report_files, superseded_log_files, superseded_table_files)
superseded_existing <- superseded_files[file.exists(superseded_files)]

report_files <- setdiff(report_files, c(result_md, code_md, superseded_report_files))
root_result_files <- sort(file.path(root, c(
  "paper1_empirical_methods_variables_results_conclusions.md"
)))
root_result_files <- root_result_files[file.exists(root_result_files)]
log_files <- sort(list.files(path("outputs", "logs"), pattern = "\\.md$", full.names = TRUE))
log_files <- setdiff(log_files, superseded_log_files)
manuscript_files <- sort(list.files(path("outputs", "manuscript"), pattern = "\\.md$", full.names = TRUE))
table_files <- sort(list.files(path("outputs", "tables"), pattern = "\\.csv$", full.names = TRUE))
table_files <- setdiff(table_files, superseded_table_files)
json_files <- sort(list.files(path("outputs", "model_summaries"), pattern = "\\.json$", full.names = TRUE))
figure_files <- sort(list.files(path("outputs", "figures"), pattern = "\\.(png|jpg|jpeg|webp)$", full.names = TRUE, ignore.case = TRUE))

all_result_text_files <- c(report_files, root_result_files, manuscript_files, log_files, table_files, json_files)
result_inventory <- do.call(rbind, lapply(c(all_result_text_files, figure_files), file_info_row))

result_lines <- c(
  "# Paper 1 All Results Integrated Package",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "This file integrates the current Paper 1 result artifacts after kg/month conversion, quantity-outlier exclusion, and full R model reruns.",
  "",
  "## 0. Execution Notes",
  "",
  "- **Econometric estimation is R-only.** The Python files in `code/` (`15`–`17`) are manuscript-writing utilities, not statistical models.",
  "- **One-command rerun:** `Rscript code/run_revised_pipeline.R` from the project root.",
  "- **Recommended order:** `19` (data prep) → `01`–`14` (models) → `13` (this compile step).",
  "- **Code review:** see `outputs/reports/paper1_econometric_code_review.md`.",
  "",
  "Binary figures are embedded by path; CSV, JSON, and Markdown outputs are included as text blocks.",
  ""
)

if (length(superseded_existing) > 0) {
  result_lines <- c(
    result_lines,
    "## Current-Run Scope Note",
    "",
    "The following earlier unit-check artifacts were excluded from this integrated results package because they predate the formal quantity-outlier exclusion and can show superseded extreme values:",
    "",
    paste0("- `", relative(superseded_existing), "`"),
    ""
  )
}

result_lines <- c(
  result_lines,
  "## 1. Artifact Inventory",
  "",
  md_table(result_inventory[, c("relative_path", "size_kb", "n_lines")]),
  "",
  "## 2. Figures",
  ""
)

if (length(figure_files) == 0) {
  result_lines <- c(result_lines, "- No figure files found.")
} else {
  for (fig in figure_files) {
    result_lines <- c(
      result_lines,
      paste0("### ", relative(fig)),
      "",
      paste0("![", basename(fig), "](", fig, ")"),
      ""
    )
  }
}

append_file_section <- function(lines, file, section_title, info) {
  lines <- c(
    lines,
    paste0("## ", section_title, ": `", relative(file), "`"),
    "",
    paste0("- Size: ", round(file.info(file)$size / 1024, 1), " KB"),
    paste0("- Lines: ", length(readLines(file, warn = FALSE, encoding = "UTF-8"))),
    "",
    fence_block(read_text(file), info),
    ""
  )
  lines
}

if (length(report_files) + length(root_result_files) > 0) {
  result_lines <- c(result_lines, "## 3. Result Reports", "")
  for (file in c(report_files, root_result_files)) {
    result_lines <- append_file_section(result_lines, file, "Report", "markdown")
  }
}

if (length(manuscript_files) > 0) {
  result_lines <- c(result_lines, "## 4. Manuscript and LLM Review Artifacts", "")
  for (file in manuscript_files) {
    result_lines <- append_file_section(result_lines, file, "Manuscript Artifact", "markdown")
  }
}

if (length(log_files) > 0) {
  result_lines <- c(result_lines, "## 5. Logs", "")
  for (file in log_files) {
    result_lines <- append_file_section(result_lines, file, "Log", "markdown")
  }
}

if (length(table_files) > 0) {
  result_lines <- c(result_lines, "## 6. Tables", "")
  for (file in table_files) {
    result_lines <- append_file_section(result_lines, file, "Table CSV", "csv")
  }
}

if (length(json_files) > 0) {
  result_lines <- c(result_lines, "## 7. Model Summaries JSON", "")
  for (file in json_files) {
    result_lines <- append_file_section(result_lines, file, "Model Summary JSON", "json")
  }
}

writeLines(result_lines, result_md, useBytes = TRUE)

## -------------------------------------------------------------------------
## Integrated code package
## -------------------------------------------------------------------------

code_files <- sort(list.files(path("code"), pattern = "\\.(R|py)$", full.names = TRUE))
code_inventory <- do.call(rbind, lapply(code_files, file_info_row))

code_lines <- c(
  "# Paper 1 All Code Integrated Package",
  "",
  paste0("Generated at: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  "",
  "This file concatenates all R and Python scripts in `code/`.",
  "",
  "- **Econometric pipeline (R):** `run_revised_pipeline.R`, `00_setup.R`, `19`, `01`–`14`, `13`.",
  "- **Manuscript utilities (Python, not econometrics):** `15_write_manuscript_draft.py`, `16_llm_manuscript_revision.py`, `17_finalize_manuscript_after_llm_review.py`.",
  "- **Legacy scripts:** older numbered files such as `08_baseline_separability_tests.R` are retained for audit history but are not part of the revised pipeline.",
  "",
  "Each script is preserved verbatim inside a fenced code block.",
  "",
  "## 1. Code Inventory",
  "",
  md_table(code_inventory[, c("relative_path", "size_kb", "n_lines")]),
  ""
)

for (file in code_files) {
  info_string <- if (grepl("\\.py$", file, ignore.case = TRUE)) "python" else "r"
  code_lines <- c(
    code_lines,
    paste0("## `", relative(file), "`"),
    "",
    paste0("- Size: ", round(file.info(file)$size / 1024, 1), " KB"),
    paste0("- Lines: ", length(readLines(file, warn = FALSE, encoding = "UTF-8"))),
    "",
    fence_block(read_text(file), info_string),
    ""
  )
}

writeLines(code_lines, code_md, useBytes = TRUE)

message("Integrated results markdown written: ", result_md)
message("Integrated code markdown written: ", code_md)