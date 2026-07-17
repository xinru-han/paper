version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_total_anomaly_rebuild/code/00_config.do"

capture erase "$AR_DATA/household_sources.csv"
capture erase "$AR_DATA/household_core.dta"
capture erase "$AR_OUT/source_field_audit.csv"
capture erase "$AR_OUT/source_summary_audit.csv"

shell /usr/bin/python3 "$AR_CODE/extract_household_core.py" ///
    --input "$AR_RAW/户表数据_已清洗.dta" ///
    --output "$AR_DATA/household_core.dta" ///
    > /tmp/easi_anomaly_household_core.log 2>&1
capture confirm file "$AR_DATA/household_core.dta"
if _rc {
    capture type /tmp/easi_anomaly_household_core.log
    di as error "compact household field extraction failed"
    exit 601
}

shell /usr/bin/python3 "$AR_CODE/extract_household_sources.py" ///
    --source "$AR_SOURCE" ///
    --output "$AR_DATA/household_sources.csv" ///
    --audit "$AR_OUT/source_field_audit.csv" ///
    --final-audit "$AR_OUT/source_summary_audit.csv" ///
    > /tmp/easi_anomaly_source_extract.log 2>&1

capture confirm file "$AR_DATA/household_sources.csv"
if _rc {
    capture type /tmp/easi_anomaly_source_extract.log
    di as error "household source extraction failed"
    exit 601
}

import delimited using "$AR_DATA/household_sources.csv", ///
    varnames(1) stringcols(1) case(preserve) encoding(utf8) clear
replace household_id = strtrim(household_id)
isid household_id data_year
assert strlen(household_id) <= 20

forvalues g = 1/6 {
    assert purchase_consumed_quantity`g' >= 0 & purchase_consumed_quantity`g' < .
    assert self_consumed_quantity`g' >= 0 & self_consumed_quantity`g' < .
    assert gift_consumed_quantity`g' >= 0 & gift_consumed_quantity`g' < .
    assert source_total_quantity`g' >= 0 & source_total_quantity`g' < .
    assert abs(source_total_quantity`g' - purchase_consumed_quantity`g' - ///
        self_consumed_quantity`g' - gift_consumed_quantity`g') < ///
        1e-5 * max(1, source_total_quantity`g')
    assert uv`g' > 0 & uv`g' <= 200 if !missing(uv`g')
    assert self_unit_value`g' > 0 & self_unit_value`g' <= 200 ///
        if !missing(self_unit_value`g')
}

compress
save "$AR_DATA/household_sources.dta", replace
