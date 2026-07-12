version 17
clear all
set more off

* Change only this line when moving the project.
global EASI_ROOT "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price"
global EASI_RAW  "/root/data/数据/食物消费调查数据/处理后的data"
global EASI_CODE "$EASI_ROOT/code"
global EASI_ADO  "$EASI_ROOT/ado"
global EASI_DATA "$EASI_ROOT/data"
global EASI_OUT  "$EASI_ROOT/outputs"

adopath ++ "$EASI_ADO"
cap mkdir "$EASI_DATA"
cap mkdir "$EASI_OUT"
