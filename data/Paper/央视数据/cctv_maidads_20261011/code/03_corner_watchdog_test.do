version 17
clear all
set more off
global cmroot "/root/data/Paper/央视数据/cctv_maidads_20261011"
do "$cmroot/ado/corner_maidads.mata"
do "$cmroot/ado/corner_regular.mata"
do "$cmroot/ado/corner_smd.mata"
mata:
b=(J(1,7,0),J(1,8,ln(.1)),-1.4,-1.5,0,0,0)
cm_watch_active=1; cm_watch_start=cm_wall_seconds(); cm_watch_deadline=60
cm_watch_calls=0; cm_watch_timeout=0; cm_watch_invalid=0
cm_watch_start_id=99; cm_watch_best_value=.; cm_watch_best_b=b
v=.; g=.; H=.
cm_smd_objective(0,b,J(3,1,1),J(3,8,1),J(3,1,1),J(3,1,1),
    J(3,15,.5),J(3,1,1),cm_draws(16,8),v,g,H)
assert(v<.)
assert(cm_watch_calls==1 & cm_watch_best_value==v)
cm_checkpoint(b,v,99,cm_watch_calls,0,0)
cm_watch_deadline=-1
cm_smd_objective(0,b,J(3,1,1),J(3,8,1),J(3,1,1),J(3,1,1),
    J(3,15,.5),J(3,1,1),cm_draws(16,8),v,g,H)
assert(cm_watch_timeout==1 & v>1000)
cm_watch_active=0
printf("CORNER_CHECKPOINT_AND_WATCHDOG_PASSED\n")
end
