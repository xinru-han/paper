version 17
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_total_anomaly_rebuild/code/00_config.do"
shell /usr/bin/python3 "$AR_CODE/write_results.py"
capture confirm file "$AR_ROOT/COMPLETE_RESULTS.txt"
if _rc {
    di as error "complete result writer failed"
    exit 601
}
