version 17
mata:
cm_watch_active=0
cm_watch_start=0; cm_watch_deadline=0; cm_watch_calls=0
cm_watch_timeout=0; cm_watch_invalid=0; cm_watch_best_value=.; cm_watch_start_id=0
cm_watch_best_b=J(1,20,.)

real scalar cm_wall_seconds()
{
    return(clock(st_global("c(current_date)")+" "+st_global("c(current_time)"),"DMYhms")/1000)
}

void cm_checkpoint(real rowvector b, real scalar value, real scalar start,
                   real scalar calls, real scalar timeout, real scalar invalid,
                   | real scalar converged)
{
    real scalar fh
    string scalar path
    if (args()==6) converged=0
    path=st_global("cmroot")+"/outputs/corner/checkpoint_start"+strofreal(start)+".csv"
    fh=fopen(path,"rw")
    fseek(fh,0,-1)
    ftruncate(fh)
    fput(fh,"objective,start,evaluations,timeout,invalid_candidates,converged,"+
        invtokens("cm_b":+strofreal(1..cols(b)),","))
    fput(fh,invtokens(strofreal((value,start,calls,timeout,invalid,converged,b),"%21.16g"),","))
    fclose(fh)
}

real rowvector cm_softmax(real rowvector x)
{
    real rowvector a
    a=exp(x:-max(x))
    return(a:/sum(a))
}

real matrix cm_unpack(real rowvector b)
{
    real rowvector alpha,low,high,eta
    real scalar r,sigma
    alpha=cm_softmax((b[|1\7|],0))
    low=exp(b[|8\15|])
    r=cm_logistic(b[16])
    high=r*low
    sigma=.05+3.95*cm_logistic(b[17])
    eta=(0,b[|18\20|],J(1,4,0))
    return(alpha\low\high\(r,sigma,.7,0,eta[|1\4|]))
}

real matrix cm_predict(real rowvector b, real colvector m, real matrix p,
                       real colvector type, real matrix draws)
{
    real matrix par,out,rd,aa
    real rowvector alpha,low,high,q
    real scalar i,r,sigma,mult,nd
    par=cm_unpack(b)
    alpha=par[1,]; low=par[2,]; high=par[3,]; sigma=par[4,2]
    nd=rows(draws)
    aa=J(nd,8,.)
    for (r=1;r<=nd;r++) aa[r,]=cm_reweight(alpha,draws[r,],sigma)
    out=J(rows(m),15,0)
    for (i=1;i<=rows(m);i++) {
        mult=exp(par[4,4+type[i]])
        for (r=1;r<=nd;r++) {
            q=cm_regular_q(m[i],p[i,],aa[r,],mult*low,par[4,1],.7)
            if (hasmissing(q)) return(J(rows(m),15,.))
            out[i,1..7]=out[i,1..7]+(p[i,1..7]:*q[|1\7|]/m[i])/nd
            out[i,8..15]=out[i,8..15]+(q:>0)/nd
        }
    }
    return(out)
}

void cm_smd_objective(real scalar todo, real rowvector b, real colvector m,
                      real matrix p, real colvector type, real matrix Z,
                      real matrix Y, real colvector w, real matrix draws,
                      real scalar v, real rowvector g, real matrix H)
{
    real matrix prediction,mom
    real scalar penalty
    external real scalar cm_watch_active,cm_watch_start,cm_watch_deadline,cm_watch_calls
    external real scalar cm_watch_timeout,cm_watch_invalid,cm_watch_best_value,cm_watch_start_id
    external real rowvector cm_watch_best_b
    if (cm_watch_active) {
        cm_watch_calls++
        if (cm_wall_seconds()-cm_watch_start>cm_watch_deadline | cm_watch_calls>1200)
            cm_watch_timeout=1
        if (cm_watch_timeout) {
            v=1000+sum(b:^2)
            return
        }
        if (mod(cm_watch_calls,50)==0 & cm_watch_best_value<.)
            cm_checkpoint(cm_watch_best_b,cm_watch_best_value,cm_watch_start_id,
                cm_watch_calls,0,cm_watch_invalid)
    }
    if (hasmissing(b) | max(abs(b))>12) {
        v=1000+sum(b:^2)
        if (v>=.) v=1e10
        if (cm_watch_active) cm_watch_invalid++
        return
    }
    prediction=cm_predict(b,m,p,type,draws)
    if (hasmissing(prediction) | min(prediction)<-1e-9 | max(prediction)>1+1e-8) {
        v=1000+sum(b:^2)
        if (cm_watch_active) cm_watch_invalid++
        return
    }
    mom=Z'*(w:*(prediction-Y))/sum(w)
    // Fixed diagonal scaling keeps shares and purchase probabilities comparable.
    mom[,1..7]=mom[,1..7]*2
    penalty=1e-5*sum(b[|18\20|]:^2)
    v=sum(mom:^2)+penalty
    if (v>=.) {
        v=1000+sum(b:^2)
        if (cm_watch_active) cm_watch_invalid++
        return
    }
    if (cm_watch_active & v<cm_watch_best_value) {
        cm_watch_best_value=v
        cm_watch_best_b=b
        cm_checkpoint(b,v,cm_watch_start_id,cm_watch_calls,0,cm_watch_invalid)
    }
}

real rowvector cm_momvec(real rowvector b, real colvector m, real matrix p,
                         real colvector type, real matrix Z, real matrix Y,
                         real colvector w, real matrix draws)
{
    real matrix mom
    mom=Z'*(w:*(cm_predict(b,m,p,type,draws)-Y))/sum(w)
    mom[,1..7]=mom[,1..7]*2
    return(vec(mom)')
}

end
