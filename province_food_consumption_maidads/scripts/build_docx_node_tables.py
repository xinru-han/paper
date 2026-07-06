"""Build all docx node-elasticity tables (T3 mean-income, T4 US$ nodes, T5 nutrient
aggregates, T8 own-price) with bootstrap CIs and p-values, for the 2015-2024 update.
Uses the 450 valid formal-bootstrap draws (success & -6000<nll<-1000).
Run from scripts/ with PYTHONPATH=scripts."""
import numpy as np, pandas as pd, warnings, json
warnings.filterwarnings("ignore")
import run_maidads_pipeline as pipe

ROOT = pipe.ROOT
RES = ROOT / "ProvinceMAIDADS" / "Results"
GN = list(pipe.GROUPS.keys())
LABELS = {"grain":"Staples","oil":"Oils and fats","vegfruit":"Vegetables and fruits",
          "pork":"Pork","meatother":"Non-pork meat/aquatic","dairyegg":"Dairy and eggs",
          "nonfood":"Other/non-covered residual"}

# US$ -> expenditure-m linear map recovered from paper's stated provincial US$ range
A_USD, B_USD = -902.4, 0.54621   # US$ = A + B*m  ->  m = (US$-A)/B
def usd_to_m(usd): return (usd - A_USD)/B_USD

def build():
    panel, long_df, nutrition = pipe.build_model_data()
    arr = pipe.panel_to_arrays(panel)
    # Price anchor: 2023 mean prices held fixed, matching Methods para 31 and the
    # income-elasticity grid / Figure 3. (An earlier ad hoc build used full-sample
    # mean prices, which shifted node points, e.g. pork@US$15k 0.184->0.112. Fixed.)
    p_mean = panel[panel["year"]==2023][[f"p_{g}_model" for g in GN]].mean().to_numpy(float)
    m_mean = float(arr.m.mean()); m_med = float(np.median(arr.m))
    m_min, m_max = float(arr.m.min()), float(arr.m.max())

    # point params
    pe = pd.read_csv(RES/"parameter_estimates.csv")
    mrow = pe[pe.model=="MAIDADS_sat"].set_index("group").loc[GN]
    def mk_params(row_alpha,row_beta,row_delta,row_tau,omega,kappa):
        return dict(alpha=row_alpha,beta=row_beta,delta=row_delta,tau=row_tau,omega=omega,kappa=kappa)
    point = mk_params(mrow["alpha"].values,mrow["beta"].values,mrow["delta"].values,
                      mrow["tau"].values,float(mrow["omega"].iloc[0]),float(mrow["kappa"].iloc[0]))

    # valid bootstrap draws
    st = pd.read_csv(RES/"FormalBootstrap_correct"/"bootstrap"/"formal_bootstrap_draw_status.csv")
    dr = pd.read_csv(RES/"FormalBootstrap_correct"/"bootstrap"/"formal_bootstrap_parameter_draws.csv")
    st["ok"]=st["success"].astype(bool)&(st["nll"]>-6000)&(st["nll"]<-1000)
    valid=set(st[st["ok"]]["draw"])
    draws=[]
    for d,g in dr[dr["draw"].isin(valid)].groupby("draw"):
        g=g.set_index("group").loc[GN]
        draws.append(mk_params(g["alpha"].values,g["beta"].values,g["delta"].values,
                               g["tau"].values,float(g["omega"].iloc[0]),float(g["kappa"].iloc[0])))
    nboot=len(draws); print(f"valid draws={nboot}, m_mean={m_mean:.1f}, m_med={m_med:.1f}")

    # nutrient content per 2000-kcal unit per group (protein/fat/carb grams)
    # quantities are in daily 2000-kcal units => energy identical across groups per unit.
    # macronutrient grams per 2000 kcal = 2000 * (grams_per_kcal) using group kcal-weighted item comp.
    shares = pipe.group_item_shares(panel, nutrition)  # province,item,group,kcal_share
    nut = nutrition.set_index("code")
    # composite codes GRAIN (blended finished grain) and OIL (mean of edible oils)
    # synthesize their per-100g-edible macro/kcal from component means.
    def composite(codes):
        sub=nut.loc[[c for c in codes if c in nut.index]]
        return {m: float(sub[m].mean()) for m in ["protein","fat","carb","kcal_per_100g_edible"]}
    comp_oil=composite(["SOYO","RAPO","GRDO"])
    comp_grain=composite(["RICE","WHEA","MAIZ","BARL"])
    # map item->code
    item_code={it:sp["code"] for it,sp in pipe.FOOD_ITEMS.items()}
    # per-item grams per kcal (edible basis): protein/kcal = protein_100g / kcal_100g_edible
    def per_kcal(code,macro):
        if code=="GRAIN": r=comp_grain
        elif code=="OIL": r=comp_oil
        else: r=nut.loc[code]
        kc=r["kcal_per_100g_edible"]
        return (r[macro]/kc) if kc>0 else 0.0
    # group-level grams per 2000 kcal (avg over provinces of kcal-share-weighted item comp)
    gnut={}
    sh=shares.copy(); sh["code"]=sh["item"].map(item_code)
    for macro in ["protein","fat","carb"]:
        sh[f"pk_{macro}"]=sh["code"].map(lambda c: per_kcal(c,macro))
    grp=sh.groupby(["province","group"]).apply(
        lambda x: pd.Series({m:np.average(x[f"pk_{m}"],weights=x["kcal_share"]) for m in ["protein","fat","carb"]}))
    grpm=grp.groupby("group").mean()  # per kcal
    PROT=np.array([grpm.loc[g,"protein"]*2000 if g in grpm.index else 0.0 for g in GN])
    FAT =np.array([grpm.loc[g,"fat"]*2000 if g in grpm.index else 0.0 for g in GN])
    CARB=np.array([grpm.loc[g,"carb"]*2000 if g in grpm.index else 0.0 for g in GN])
    animal_idx=[GN.index(x) for x in ["pork","meatother","dairyegg"]]
    plant_idx=[GN.index(x) for x in ["grain","oil","vegfruit"]]
    covered_idx=list(range(6))

    def eta_at(params,m):
        eta,xhat,u,phi=pipe.elasticity_for_point(p_mean,m,params); return eta,xhat

    # aggregate nutrient/energy elasticities at income m given group eta & xhat
    def nutrient_row(eta,xhat):
        # weights: energy ~ xhat (2000kcal units); nutrient ~ grams*xhat
        def wavg(idx,w): 
            w=w[idx]; 
            return float(np.average(eta[idx],weights=w)) if w.sum()>0 else np.nan
        cov_e=wavg(covered_idx,xhat)
        plant_e=wavg(plant_idx,xhat)
        animal_e=wavg(animal_idx,xhat)
        protein=wavg(covered_idx,PROT*xhat)
        fat=wavg(covered_idx,FAT*xhat)
        carb=wavg(covered_idx,CARB*xhat)
        return dict(covered_energy=cov_e,plant_energy=plant_e,animal_energy=animal_e,
                    protein=protein,fat=fat,carb=carb)

    def ci_p(boot_vals, point_val):
        v=np.array([x for x in boot_vals if np.isfinite(x)])
        lo,hi=np.percentile(v,[2.5,97.5])
        # two-sided p for H0: value=0, via bootstrap sign
        p=2*min((v>0).mean(),(v<0).mean()); p=min(p,1.0)
        return lo,hi,p,len(v)

    # ---- T3: mean-income group elasticities ----
    eta0,xhat0=eta_at(point,m_mean)
    rows=[]
    boot_eta={g:[] for g in GN}
    boot_nut={k:[] for k in ["covered_energy","plant_energy","animal_energy","protein","fat","carb"]}
    for pr in draws:
        try: e,xh=eta_at(pr,m_mean)
        except Exception: continue
        for j,g in enumerate(GN): boot_eta[g].append(e[j])
        nr=nutrient_row(e,xh)
        for k in boot_nut: boot_nut[k].append(nr[k])
    for j,g in enumerate(GN):
        lo,hi,p,n=ci_p(boot_eta[g],eta0[j])
        bshare=float(p_mean[j]*xhat0[j]/m_mean)
        rows.append(dict(group=LABELS[g],point=round(eta0[j],3),ci_lo=round(lo,3),
                         ci_hi=round(hi,3),p=round(p,3),budget_share=round(bshare,4)))
    t3=pd.DataFrame(rows); t3.to_csv(RES/"docx_table3_meanGDP_elasticity.csv",index=False)

    # ---- T4: group income elasticities at US$ nodes ----
    usd_nodes=[15000,20000,25000,30000]
    t4rows=[]
    for usd in usd_nodes:
        m=usd_to_m(usd)
        e0,_=eta_at(point,m)
        bvals={g:[] for g in GN}
        for pr in draws:
            try: e,_=eta_at(pr,m)
            except Exception: continue
            for j,g in enumerate(GN): bvals[g].append(e[j])
        for j,g in enumerate(GN):
            lo,hi,p,n=ci_p(bvals[g],e0[j])
            t4rows.append(dict(group=g,usd=usd,point=round(e0[j],3),
                               ci_lo=round(lo,3),ci_hi=round(hi,3),p=round(p,3),n=n))
    t4=pd.DataFrame(t4rows)
    t4.to_csv(RES/"table4_node_elasticity_ci_pval.csv",index=False)
    # also emit the wide milestone view used by Figure 3 / docx Table 4
    mile=t4.pivot(index="group",columns="usd",values="point").loc[GN]
    mile.columns=[str(c) for c in mile.columns]
    mile.reset_index().to_csv(RES/"elasticity_usd_milestones_MAIN.csv",index=False)

    # ---- T5: nutrient aggregates at US$ nodes ----
    nut0=nutrient_row(eta0,xhat0)
    usd_nodes=[15000,20000,25000,30000]
    t5rows=[]
    for usd in usd_nodes:
        m=usd_to_m(usd)
        e0,xh0=eta_at(point,m)
        base=nutrient_row(e0,xh0)
        bvals={k:[] for k in base}
        for pr in draws:
            try: e,xh=eta_at(pr,m)
            except Exception: continue
            nr=nutrient_row(e,xh)
            for k in bvals: bvals[k].append(nr[k])
        for k in base:
            lo,hi,p,n=ci_p(bvals[k],base[k])
            t5rows.append(dict(indicator=k,usd=usd,point=round(base[k],3),
                               ci_lo=round(lo,3),ci_hi=round(hi,3),p=round(p,3)))
    t5=pd.DataFrame(t5rows); t5.to_csv(RES/"docx_table5_nutrient_nodes.csv",index=False)

    # ---- T8: own-price elasticities at mean income ----
    mar0,hic0,eta_p,bshare0,u0=pipe.price_elasticities_for_point(p_mean,m_mean,point)
    own_m0=np.diag(mar0); own_h0=np.diag(hic0)
    bm={g:[] for g in GN}; bh={g:[] for g in GN}
    for pr in draws:
        try: mar,hic,_,_,_=pipe.price_elasticities_for_point(p_mean,m_mean,pr)
        except Exception: continue
        dm,dh=np.diag(mar),np.diag(hic)
        for j,g in enumerate(GN): bm[g].append(dm[j]); bh[g].append(dh[j])
    t8rows=[]
    for j,g in enumerate(GN):
        lom,him,pm,_=ci_p(bm[g],own_m0[j])
        loh,hih,ph,_=ci_p(bh[g],own_h0[j])
        t8rows.append(dict(group=LABELS[g],marshallian=round(own_m0[j],3),m_lo=round(lom,3),
                           m_hi=round(him,3),m_p=round(pm,3),hicksian=round(own_h0[j],3),
                           h_lo=round(loh,3),h_hi=round(hih,3),h_p=round(ph,3)))
    t8=pd.DataFrame(t8rows); t8.to_csv(RES/"docx_table8_ownprice.csv",index=False)

    # meta
    meta=dict(m_mean=m_mean,m_median=m_med,m_min=m_min,m_max=m_max,nboot=nboot,
              usd_map=dict(A=A_USD,B=B_USD),usd_nodes_m={u:usd_to_m(u) for u in usd_nodes})
    json.dump(meta,open(RES/"docx_node_tables_meta.json","w"),indent=2)
    print("T3:\n",t3.to_string())
    print("\nT4:\n",t4.to_string())
    print("\nT5:\n",t5.to_string())
    print("\nT8:\n",t8.to_string())
    print("\nmeta:",meta)

if __name__=="__main__":
    build()
