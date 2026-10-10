version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_nine_groups/code/00_config.do"

capture log close _all
log using "$NINE_LOG/nine_group_run.log", text replace name(nine)

shell /usr/bin/python3 "$NINE_CODE/01_build_nine_group_data.py" > "$NINE_LOG/build_data.log" 2>&1
capture confirm file "$NINE_DATA/nine_group_analysis.dta"
if _rc {
    type "$NINE_LOG/build_data.log"
    di as error "Nine-group data build failed"
    exit 601
}

do "$NINE_CODE/02_estimate_models.do"
do "$NINE_CODE/04_easi_gmm_onestep.do"
shell /usr/bin/python3 "$NINE_CODE/03_compile_results.py" > "$NINE_LOG/compile_results.log" 2>&1
capture confirm file "$NINE_OUT/NINE_GROUP_MODEL_RESULTS.md"
if _rc {
    type "$NINE_LOG/compile_results.log"
    di as error "Nine-group result compilation failed"
    exit 601
}

log close nine
