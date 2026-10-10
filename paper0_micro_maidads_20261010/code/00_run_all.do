version 17
clear all
set more off
set linesize 160

args project_root run_mode
if `"`project_root'"' == "" local project_root "/root/data/Paper/食物消费数据/paper0-EASI/micro_maidads_20261010"
if `"`run_mode'"' == "" local run_mode "run"
if !inlist("`run_mode'","run","check") {
    display as error "Second argument must be run or check"
    exit 198
}
capture confirm file "`project_root'/code/run_pipeline.py"
if _rc {
    display as error "Missing code/run_pipeline.py below project_root"
    exit 601
}
capture mkdir "`project_root'/outputs"
capture mkdir "`project_root'/logs"
capture log close mma_entry
log using "`project_root'/logs/00_run_all_entry.log", name(mma_entry) text replace
local marker "`project_root'/outputs/RUN_ALL_COMPLETE.json"
local checkoption ""
if "`run_mode'"=="check" {
    local marker "`project_root'/outputs/PIPELINE_CHECK_COMPLETE.json"
    local checkoption "--check"
}
* Stata shell does not reliably return the child exit code. The runner creates
* this fresh marker only after every command, output, and validation succeeds.
capture erase "`marker'"
capture confirm file "`marker'"
if !_rc {
    display as error "Cannot remove the previous success marker; refusing an ambiguous run."
    exit 603
}
shell env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 ///
    /usr/bin/python3 "`project_root'/code/run_pipeline.py" ///
    --root "`project_root'" --stata /usr/local/stata17/stata-se `checkoption'
capture confirm file "`marker'"
if _rc {
    display as error "Pipeline did not create a fresh success marker."
    display as error "Inspect outputs/RUN_ALL_MANIFEST.json or PIPELINE_CHECK_MANIFEST.json and logs/pipeline_* logs."
    exit 459
}
type "`marker'"
log close mma_entry
exit, clear
