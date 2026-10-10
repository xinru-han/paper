version 17
set more off

do "/root/data/Paper/食物消费数据/paper0-EASI/easi_total_anomaly_rebuild/code/00_extract_household_sources.do"
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_total_anomaly_rebuild/code/01_build_clean_prices.do"
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_total_anomaly_rebuild/code/02_build_anomaly_samples.do"
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_total_anomaly_rebuild/code/03_descriptives.do"
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_total_anomaly_rebuild/code/04_estimate_unconstrained.do"
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_total_anomaly_rebuild/code/05_bootstrap_reference.do"
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_total_anomaly_rebuild/code/06_validate.do"
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_total_anomaly_rebuild/code/07_write_results.do"
