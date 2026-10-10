version 17
clear all
set more off

global AR_ROOT "/root/data/Paper/食物消费数据/paper0-EASI/easi_total_anomaly_rebuild"
global AR_RAW  "/root/data/数据/食物消费调查数据/处理后的data"
global AR_SOURCE "/root/data/数据/食物消费调查数据/导出的数据/家庭食物获取消费/cleaned"
global AR_FOODDEM "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/ado"
global AR_CODE "$AR_ROOT/code"
global AR_DATA "$AR_ROOT/data"
global AR_OUT  "$AR_ROOT/outputs"
global AR_DOCS "$AR_ROOT/docs"

adopath ++ "$AR_FOODDEM"
adopath ++ "$AR_CODE"
cap mkdir "$AR_DATA"
cap mkdir "$AR_OUT"
cap mkdir "$AR_DOCS"
