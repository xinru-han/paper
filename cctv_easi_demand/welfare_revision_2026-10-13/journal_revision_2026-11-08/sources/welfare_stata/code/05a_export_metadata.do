version 17
clear all
do "/root/data/Paper/央视数据/Paper1-EASI/welfare_revision_2026-10-13/code/00_config.do"
log using "$REV/logs/05a_export_metadata.log",text replace
use "$BASE/data/basket_weights_2021.dta",clear
describe
list,abbreviate(20) noobs
export delimited using "$REV/outputs/exact/basket_weights_2021.csv",replace
use "$REV/outputs/audit/welfare_scenario_audit.dta",clear
assert _N==22
export delimited using "$REV/outputs/audit/welfare_scenario_audit.csv",replace
list scenario supported_N support_rate,noobs
use "$REV/outputs/welfare/scenario_definitions.dta",clear
assert _N==22
export delimited using "$REV/outputs/welfare/scenario_definitions.csv",replace
assert price1==0 & price2==10 & price3==0 if scenario=="oil_10"
assert price1==0 & price2==0 & price3==10 & price8==10 if scenario=="all10_staple_oil_protected"
display "WELFARE_METADATA_SUCCESS"
log close
