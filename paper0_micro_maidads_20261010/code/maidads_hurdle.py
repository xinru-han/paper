"""Choice-set conditional MAIDADS with an exact Dirichlet share likelihood.

The low-utility commitment endpoint is fixed at zero.  Both endpoint marginal
share vectors are free simplexes; there is no outside good in this food system.
Participation is a separately estimated hurdle, not additive Gaussian censoring.
"""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize
from scipy.special import digamma, expit, gammaln, softmax


@dataclass
class Demand:
    q: np.ndarray
    shares: np.ndarray
    utility: np.ndarray
    eu: np.ndarray
    phi: np.ndarray
    gamma: np.ndarray
    discretionary: np.ndarray
    qu: np.ndarray


class ConditionalMAIDADS:
    def __init__(self, k, demographics=0, commitment=True, expanded_guards=False):
        self.k = int(k)
        self.d = int(demographics)
        self.commitment = bool(commitment)
        self.expanded_guards = bool(expanded_guards)
        self.base_count = 2 * (self.k - 1)
        self.d_count = self.d * (self.k - 1)
        self.npar = self.base_count + self.d_count + (self.k + 1 if commitment else 0) + 2

    def unpack(self, theta, z):
        k, b = self.k, self.k - 1
        j = self.base_count
        demographic = theta[j:j + self.d_count].reshape(self.d, b)
        shift = z @ demographic if self.d else np.zeros((len(z), b))
        alpha = softmax(np.column_stack([theta[:b] + shift, np.zeros(len(z))]), axis=1)
        beta = softmax(np.column_stack([theta[b:2*b] + shift, np.zeros(len(z))]), axis=1)
        j += self.d_count
        if self.commitment:
            tau = np.exp(theta[j:j+k])
            omega = float(np.exp(theta[j+k]))
            j += k + 1
        else:
            tau = np.zeros(k)
            omega = 1.0
        return alpha, beta, tau, omega, float(theta[j]), float(np.exp(theta[j+1]))

    def _state(self, u, p, active, alpha, beta, tau, omega, kappa):
        s = expit(u)[:, None]
        base = alpha * (1-s) + beta*s
        base_u = (beta-alpha)*s*(1-s)
        denom = np.sum(base*active, axis=1, keepdims=True)
        phi = base*active/denom
        denom_u = np.sum(base_u*active, axis=1, keepdims=True)
        phi_u = (base_u*active - phi*denom_u)/denom
        t = expit(omega*u)[:, None]
        gamma = tau*t*active
        gamma_u = omega*t*(1-t)*tau*active
        logratio = np.log(np.where(active, phi/p, 1.0))
        logdisc = u+kappa-np.sum(phi*logratio, axis=1)
        disc = np.exp(np.clip(logdisc, -700, 700))
        disc_u = disc*(1-np.sum(phi_u*logratio, axis=1))
        expenditure = np.sum(p*gamma, axis=1)+disc
        eu = np.sum(p*gamma_u, axis=1)+disc_u
        q = gamma+phi*disc[:, None]/p
        qu = gamma_u+(phi_u*disc[:, None]+phi*disc_u[:, None])/p
        return expenditure, eu, q, qu, phi, gamma, disc, base, denom, logratio

    def predict(self, theta, p, m, active, z=None):
        p, m, active = np.asarray(p, float), np.asarray(m, float), np.asarray(active, bool)
        if z is None:
            z = np.zeros((len(m), self.d))
        if np.any(active.sum(axis=1) == 0) or np.any(m <= 0) or np.any(p <= 0):
            raise ValueError("Conditional demands need a nonempty set and positive budget/prices")
        alpha, beta, tau, omega, kappa, _ = self.unpack(theta, z)
        lo, hi = np.full(len(m), -40.), np.full(len(m), 40.)
        # A safeguarded Newton solve makes the kernel fast enough for micro data.
        u = np.clip(np.log(m)-kappa, -20, 20)
        for _ in range(26):
            e, eu, *_ = self._state(u,p,active,alpha,beta,tau,omega,kappa)
            done = np.abs(e-m)/m < 2e-11
            if np.all(done):
                break
            below = e < m
            lo = np.where(below & ~done,u,lo)
            hi = np.where(~below & ~done,u,hi)
            step = u-(e-m)/np.maximum(eu, 1e-12)
            usable = np.isfinite(step) & (eu > 0) & (step > lo) & (step < hi)
            updated = np.where(usable, step, (lo+hi)/2)
            u = np.where(done,u,updated)
        e, eu, q, qu, phi, gamma, disc, *_ = self._state(u,p,active,alpha,beta,tau,omega,kappa)
        if np.max(np.abs(e-m)/m) > 2e-7:
            for _ in range(35):
                done = np.abs(e-m)/m < 2e-11
                if np.all(done):
                    break
                u = np.where(done,u,(lo+hi)/2)
                e, *_ = self._state(u,p,active,alpha,beta,tau,omega,kappa)
                below = e < m
                lo = np.where(below & ~done,u,lo)
                hi = np.where(~below & ~done,u,hi)
            e, eu, q, qu, phi, gamma, disc, *_ = self._state(u,p,active,alpha,beta,tau,omega,kappa)
        if np.any(~np.isfinite(q)) or np.any(eu <= 0) or np.max(np.abs(e-m)/m) > 1e-6:
            raise ValueError("Invalid expenditure root: budget residual or nonpositive E_u")
        return Demand(q, p*q/m[:,None], u, eu, phi, gamma, disc, qu)

    def objective(self, theta, p, m, active, z, observed, return_scores=False):
        try:
            prediction = self.predict(theta,p,m,active,z)
        except ValueError:
            if return_scores:
                raise
            return (1e10, np.zeros(self.npar))
        if np.any(prediction.eu <= 1e-9) or np.any(~np.isfinite(prediction.shares)):
            return (1e10, np.zeros(self.npar))
        alpha,beta,tau,omega,kappa,rho = self.unpack(theta,z)
        u,mu = prediction.utility,prediction.shares
        s,t = expit(u)[:,None],expit(omega*u)[:,None]
        multinomial = active.sum(axis=1) > 1
        amu = np.where(active,rho*mu,1.)
        logw = np.log(np.where(active,observed,1.))
        ll = gammaln(rho)-np.sum(np.where(active,gammaln(amu),0),axis=1)
        ll += np.sum(np.where(active,(amu-1)*logw,0),axis=1)
        ll = np.where(multinomial,ll,0.)
        gmu = np.where(active,rho*(logw-digamma(amu)),0.)
        gmu[~multinomial] = 0
        gq = gmu*p/m[:,None]
        root_adj = np.sum(gq*prediction.qu,axis=1)/prediction.eu
        b_adj = np.sum(gq*prediction.phi/p,axis=1)-root_adj
        logratio = np.log(np.where(active,prediction.phi/p,1.))
        gphi = prediction.discretionary[:,None]*(gq/p-b_adj[:,None]*logratio)
        ggamma = gq-root_adj[:,None]*p
        base = alpha*(1-s)+beta*s
        denom = np.sum(base*active,axis=1,keepdims=True)
        gpbase = active*(gphi-np.sum(gphi*prediction.phi,axis=1,keepdims=True))/denom
        ga,gb = gpbase*(1-s),gpbase*s
        da = alpha*(ga-np.sum(alpha*ga,axis=1,keepdims=True))
        db = beta*(gb-np.sum(beta*gb,axis=1,keepdims=True))
        blocks = [da[:,:-1],db[:,:-1]]
        if self.d:
            blocks.append((z[:,:,None]*(da+db)[:,None,:-1]).reshape(len(m),-1))
        if self.commitment:
            blocks.append(ggamma*prediction.gamma)
            blocks.append(np.sum(ggamma*active*tau*t*(1-t)*u[:,None]*omega,axis=1)[:,None])
        blocks.append((b_adj*prediction.discretionary)[:,None])
        drho = rho*(digamma(rho)-np.sum(np.where(active,mu*digamma(amu),0),axis=1)+np.sum(mu*logw,axis=1))
        blocks.append(np.where(multinomial,drho,0.)[:,None])
        scores = np.column_stack(blocks)
        if return_scores:
            return ll,scores,prediction
        return -float(np.mean(ll)), -scores.mean(axis=0)

    def initialize(self, observed, active, z):
        shares = np.maximum(observed.mean(axis=0),1e-4)
        shares /= shares.sum()
        logits = np.log(shares[:-1]/shares[-1])
        theta = np.r_[logits,logits,np.zeros(self.d_count)]
        if self.commitment:
            theta = np.r_[theta,np.full(self.k,np.log(.025)),np.log(.8)]
        return np.r_[theta,0.,np.log(3.)]

    def bounds(self):
        if self.expanded_guards:
            bounds = [(-12,12)]*self.base_count+[(-3,3)]*self.d_count
            if self.commitment:
                bounds += [(-18,8)]*self.k+[(-3.5,3)]
            return bounds+[(-8,8),(-3,6)]
        bounds = [(-7,7)]*self.base_count+[(-3,3)]*self.d_count
        if self.commitment:
            bounds += [(-14,5.)]*self.k+[(-2.3,2.)]
        return bounds+[(-5,5),(-3,6)]

    def fit(self,p,m,active,z,observed,starts=3,seed=20261010,maxiter=400,initial_theta=None):
        base = self.initialize(observed,active,z)
        if self.commitment:
            j=self.base_count+self.d_count
            base[j:j+self.k]=np.log(np.maximum(np.mean(m[:,None]*observed/p,axis=0)*.15,1e-4))
        if initial_theta is not None:
            base=np.asarray(initial_theta,float).copy()
        rng = np.random.default_rng(seed)
        candidates=[]
        for i in range(starts):
            start = base.copy()
            if i:
                start[:self.base_count] += rng.normal(0,.25,self.base_count)
                if self.commitment:
                    start[self.base_count+self.d_count:self.base_count+self.d_count+self.k] += rng.normal(0,.4,self.k)
            fit = minimize(self.objective,start,args=(p,m,active,z,observed),jac=True,
                           method="L-BFGS-B",bounds=self.bounds(),
                           options={"maxiter":maxiter,"ftol":1e-11,"gtol":2e-6,"maxls":30,"maxcor":30})
            try:
                pred=self.predict(fit.x,p,m,active,z)
                positive_eu=bool(np.all(pred.eu>0))
                budget_error=float(np.max(np.abs(np.sum(p*pred.q,axis=1)-m)/m))
            except ValueError:
                positive_eu=False
                budget_error=float("inf")
            pg=np.asarray(fit.jac).copy()
            bounds=np.asarray(self.bounds())
            pg[(fit.x <= bounds[:,0]+1e-7)&(pg>0)]=0
            pg[(fit.x >= bounds[:,1]-1e-7)&(pg<0)]=0
            candidate={"start":i,"success":bool(fit.success),"message":str(fit.message),
                       "iterations":int(fit.nit),"objective":float(fit.fun),
                       "gradient_max":float(np.max(np.abs(fit.jac))),
                       "projected_gradient_max":float(np.max(np.abs(pg))),
                       "positive_eu":positive_eu,
                       "budget_max_error":budget_error,
                       "theta":fit.x.tolist()}
            candidates.append(candidate)
            print(f"K={self.k} commitment={self.commitment} start={i} nll={fit.fun:.5f} success={fit.success} iter={fit.nit}",flush=True)
        feasible=[c for c in candidates if c["success"] and c["projected_gradient_max"]<1e-3
                  and c["positive_eu"] and c["budget_max_error"]<1e-6]
        if not feasible:
            raise RuntimeError("No converged, stationary and numerically feasible MAIDADS candidate: "+str(candidates))
        best=min(feasible,key=lambda c:c["objective"])
        return np.asarray(best["theta"]),candidates

    def responses(self,theta,p,m,active,z=None):
        pred=self.predict(theta,p,m,active,z)
        eta_m=m[:,None]*pred.qu/pred.eu[:,None]/np.where(active,pred.q,np.nan)
        n,k=p.shape
        h=np.empty((n,k,k))
        for j in range(k):
            deriv=pred.discretionary[:,None]*(pred.phi*pred.phi[:,j,None]/(p*p[:,j,None]))
            deriv[:,j]-=pred.discretionary*pred.phi[:,j]/p[:,j]**2
            h[:,:,j]=deriv*p[:,j,None]/np.where(active,pred.q,np.nan)
        mar=h-eta_m[:,:,None]*pred.shares[:,None,:]
        return pred,eta_m,mar,h
