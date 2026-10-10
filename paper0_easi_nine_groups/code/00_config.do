version 17
clear all
set more off
set linesize 255

global NINE_ROOT "/root/data/Paper/食物消费数据/paper0-EASI/easi_nine_groups"
global NINE_RAW "/root/data/数据/食物消费调查数据/处理后的data"
global NINE_ITEM "/root/data/Paper/食物消费数据/paper0-EASI/item_level_food_descriptives/outputs"
global NINE_FOODDEM "/root/data/Paper/食物消费数据/paper0-EASI/easi_community_price/ado"
global NINE_CODE "$NINE_ROOT/code"
global NINE_DATA "$NINE_ROOT/data"
global NINE_OUT "$NINE_ROOT/outputs"
global NINE_LOG "$NINE_ROOT/logs"

adopath ++ "$NINE_FOODDEM"
cap mkdir "$NINE_DATA"
cap mkdir "$NINE_OUT"
cap mkdir "$NINE_LOG"
