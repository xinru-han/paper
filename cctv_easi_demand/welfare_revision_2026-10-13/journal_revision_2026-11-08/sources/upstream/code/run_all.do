version 17
clear all
set more off
* Run with Stata 17 BE or newer: stata -b do code/run_all.do
* Every step has its own text log and an explicit success marker.
* Original nine-group data, model objects and manuscripts are read only.
do "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11/code/01_merge_data.do"
do "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11/code/02_exact_models.do"
do "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11/code/03_main_model.do"
do "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11/code/04_derivative_audit.do"
do "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11/code/05_matched_exact.do"
do "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11/code/06_main_audit.do"
do "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11/code/07_results_report.do"
do "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11/code/08_validate_results.do"
display "MEAT_MERGE_ALL_SUCCESS"
