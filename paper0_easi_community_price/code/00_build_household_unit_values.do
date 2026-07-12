version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/code/00_config.do"

* The source module DTAs were saved by Stata/MP with a format that this
* Stata/SE installation refuses to open, and long CSV headers are truncated by
* Stata. The bundled extractor reads only named 00/02/03 fields with pandas,
* monthlyizes quantity and expenditure consistently, and writes a compact CSV.
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
    assert purchase_value`g' >= 0 & purchased_quantity`g' >= 0
}
compress
save "$EASI_DATA/household_unit_values.dta", replace
