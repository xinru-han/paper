version 17
clear all
set more off
* Prerequisite: run_all.do has completed the eight-group model rebuild.
* This driver regenerates the additional tables required for the full manuscripts.
do "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11/code/09_paper_inference.do"
* 10_paper_data.do also runs exact Engel tests and both exposure calculations.
do "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11/code/10_paper_data.do"
foreach variant in order1 order3 nosy nopcyc omit5 {
    do "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11/code/11_paper_robustness.do" `variant'
}
do "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11/code/12_collect_paper_results.do"
do "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11/code/13_validate_paper.do"
display "EIGHT_GROUP_PAPER_ALL_SUCCESS"
