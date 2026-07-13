version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/code/00_config.do"

* The source module DTAs were saved by Stata/MP with a format that this
* Stata/SE installation refuses to open, and long CSV headers are truncated by
* Stata. The bundled extractor reads the named acquisition and source fields
* with pandas, monthlyizes every quantity consistently, and writes a compact CSV.
capture erase "$EASI_DATA/household_unit_values.csv"
capture erase "$EASI_OUT/unit_value_source_audit.csv"
capture erase "$EASI_OUT/unit_value_final_audit.csv"
shell /usr/bin/python3 "$EASI_CODE/extract_household_unit_values.py" --source "/root/data/数据/食物消费调查数据/导出的数据/家庭食物获取消费/cleaned" --output "$EASI_DATA/household_unit_values.csv" --audit "$EASI_OUT/unit_value_source_audit.csv" --final-audit "$EASI_OUT/unit_value_final_audit.csv" > /tmp/fooddem_uv_extract.log 2>&1
capture confirm file "$EASI_DATA/household_unit_values.csv"
if _rc {
    capture type /tmp/fooddem_uv_extract.log
    di as error "household unit-value extraction failed"
    exit 601
}

import delimited using "$EASI_DATA/household_unit_values.csv", ///
    varnames(1) stringcols(1) case(preserve) encoding(utf8) clear
isid household_id data_year
forvalues g = 1/6 {
    assert uv`g' > 0 & uv`g' <= 200 if !missing(uv`g')
    assert purchase_value`g' >= 0 & purchase_value`g' < . & ///
        purchased_quantity`g' >= 0 & purchased_quantity`g' < .
    assert purchase_acquisition_quantity`g' >= 0 & ///
        purchase_acquisition_quantity`g' < . & ///
        purchase_acquisition_value`g' >= 0 & purchase_acquisition_value`g' < .
    assert purchase_consumed_quantity`g' >= 0 & purchase_consumed_quantity`g' < .
    assert purchase_direct_quantity`g' >= 0 & purchase_direct_quantity`g' < .
    assert purchase_residual_quantity`g' >= 0 & purchase_residual_quantity`g' < .
    assert purchase_typical_quantity`g' >= 0 & purchase_typical_quantity`g' < .
    assert abs(purchase_consumed_quantity`g' - ///
        purchase_direct_quantity`g' - purchase_residual_quantity`g' - ///
        purchase_typical_quantity`g') < ///
        1e-5 * max(1, purchase_consumed_quantity`g')
    assert self_consumed_quantity`g' >= 0 & self_consumed_quantity`g' < .
    assert gift_consumed_quantity`g' >= 0 & gift_consumed_quantity`g' < .
    assert self_price_covered_quantity`g' >= 0 & ///
        self_price_covered_quantity`g' < .
    assert self_price_covered_quantity`g' <= self_consumed_quantity`g' + ///
        1e-5 * max(1, self_consumed_quantity`g')
    assert self_reported_value`g' >= 0 & self_reported_value`g' < .
    assert source_total_quantity`g' >= 0 & source_total_quantity`g' < .
    assert abs(source_total_quantity`g' - purchase_consumed_quantity`g' - ///
        self_consumed_quantity`g' - gift_consumed_quantity`g') < ///
        1e-5 * max(1, source_total_quantity`g')
    assert self_unit_value`g' > 0 & self_unit_value`g' <= 200 ///
        if !missing(self_unit_value`g')
}
compress
save "$EASI_DATA/household_unit_values.dta", replace
