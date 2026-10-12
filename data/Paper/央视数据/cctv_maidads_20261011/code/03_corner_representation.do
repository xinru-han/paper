version 17
clear all
set more off
global cmroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
capture log close _all
log using "$cmroot/logs/03_corner_representation.log", text replace
import delimited "$cmroot/data/household_quarter_8.csv", clear varnames(1) encoding(utf8) asdouble stringcols(1)
keep if m>0 & m<. & month_count==3
generate byte train=year<2022
egen byte household_tag=tag(train hh_id)
egen byte price_tag=tag(train province tq)
bysort hh_id: egen byte seen_training=max(train)
bysort hh_id: egen byte seen_holdout=max(1-train)
generate byte overlapping_household=household_tag & seen_training & seen_holdout
collapse (count) household_quarters=m (sum) distinct_households=household_tag distinct_province_quarter_prices=price_tag overlapping_households=overlapping_household, by(train)
generate str24 scope="full_complete_positive"
export delimited "$cmroot/outputs/corner/independent_variation_scope.csv", replace
display "CORNER_REPRESENTATION_AUDIT_FINISHED"
log close
