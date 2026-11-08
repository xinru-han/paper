version 17
set more off
set varabbrev off
capture set processors 2
set matsize 800
global ROOT "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11"
adopath ++ "$ROOT/ado"
capture mkdir "$ROOT/outputs/demand"
capture mkdir "$ROOT/outputs/inference"
capture mkdir "$ROOT/outputs/regularity"
capture mkdir "$ROOT/outputs/robustness"
capture mkdir "$ROOT/outputs/welfare"
capture mkdir "$ROOT/outputs/figures"
capture mkdir "$ROOT/outputs/models"
global DEMO "low_income elderly_household large_family"
global MACRO "z_cpi z_covid z_holiday z_temp z_precip z_wholesale"
global TIME "m_02 m_03 m_04 m_05 m_06 m_07 m_08 m_09 m_10 m_11 m_12 yr_2021 yr_2022"
