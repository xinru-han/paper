version 17
mata:
cf_watch_active=0
cf_watch_start=0; cf_watch_deadline=0; cf_watch_calls=0; cf_watch_limit=1200
cf_watch_timeout=0; cf_watch_invalid=0; cf_watch_best_value=.; cf_watch_start_id=0
cf_watch_best_b=J(1,27,.)

real scalar cf_seconds()
{
    return(clock(st_global("c(current_date)")+" "+st_global("c(current_time)"),"DMYhms")/1000)
}

void cf_checkpoint(real rowvector b, real scalar value, real scalar converged)
{
    external real scalar cf_watch_start_id,cf_watch_calls,cf_watch_timeout,cf_watch_invalid
    real scalar fh
    string scalar filename
    filename=st_global("cfout")
    if(filename=="") filename=st_global("cfroot")+"/outputs/corner_freephi"
    filename=filename+"/checkpoint_start"+
        strofreal(cf_watch_start_id)+".csv"
    fh=fopen(filename,"rw"); fseek(fh,0,-1); ftruncate(fh)
    fput(fh,"objective,start,evaluations,timeout,invalid_candidates,converged,"+
        invtokens("b":+strofreal(1..cols(b)),","))
    fput(fh,invtokens(strofreal((value,cf_watch_start_id,cf_watch_calls,
        cf_watch_timeout,cf_watch_invalid,converged,b),"%21.16g"),","))
    fclose(fh)
}

void cf_smd_objective(real scalar todo, real rowvector b, real colvector m,
                      real matrix p, real colvector type, real matrix Z,
                      real matrix Y, real colvector w, real matrix draws,
                      real rowvector qmax, real scalar v,
                      real rowvector g, real matrix H)
{
    real matrix pred,mom
    external real scalar cf_watch_active,cf_watch_start,cf_watch_deadline,cf_watch_calls
    external real scalar cf_watch_timeout,cf_watch_invalid,cf_watch_best_value,cf_watch_limit
    external real rowvector cf_watch_best_b
    if (cf_watch_active) {
        cf_watch_calls++
        if (cf_seconds()-cf_watch_start>cf_watch_deadline | cf_watch_calls>cf_watch_limit)
            cf_watch_timeout=1
        if (cf_watch_timeout) {
            v=1000+sum(b:^2)
            return
        }
    }
    if (hasmissing(b) | max(abs(b))>12) {
        v=1000+sum(b:^2)
        if (v>=.) v=1e10
        if (cf_watch_active) cf_watch_invalid++
        return
    }
    pred=cf_predict_vector(b,m,p,type,draws,qmax)
    if (hasmissing(pred) | min(pred)<-1e-9 | max(pred)>1+1e-8) {
        v=1000+sum(b:^2)
        if (cf_watch_active) cf_watch_invalid++
        return
    }
    mom=Z'*(w:*(pred-Y))/sum(w)
    mom[,1..7]=2*mom[,1..7]
    v=sum(mom:^2)+1e-5*sum(b[|18\20|]:^2)
    if (v>=.) {
        v=1000+sum(b:^2)
        if (cf_watch_active) cf_watch_invalid++
        return
    }
    if (cf_watch_active & v<cf_watch_best_value) {
        cf_watch_best_value=v; cf_watch_best_b=b
        cf_checkpoint(b,v,0)
    }
}
end
