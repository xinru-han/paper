version 17
clear all
set more off
mata:
t0=clock(st_global("c(current_date)")+" "+st_global("c(current_time)"),"DMYhms")
t1=t0
for (i=1;i<=10000000 & t1==t0;i++) {
    t1=clock(st_global("c(current_date)")+" "+st_global("c(current_time)"),"DMYhms")
}
printf("Dynamic clock elapsed %g milliseconds, evaluations %g\n",t1-t0,i)
assert(t1>t0)
end
display "CORNER_DYNAMIC_CLOCK_PASSED"
