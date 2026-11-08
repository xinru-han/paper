#!/usr/bin/env python3
"""Read audited Stata CSVs and format bilingual manuscripts. No statistical estimation.
Only row selection, labels, rounding and percent display conversion are performed here.
"""
from pathlib import Path
import csv,re,argparse
P=Path('/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11')
M=P/'manuscript'
FOOD_CN=['主食','食用油','蔬菜','水果','猪肉','其他肉类','水产品','乳制品']
FOOD_EN=['Staples','Oils','Vegetables','Fruit','Pork','Other meat','Seafood','Dairy']
SHORT_CN=['主食','油','蔬菜','水果','猪肉','其他肉类','水产','乳品']
SHORT_EN=['Staples','Oils','Veg.','Fruit','Pork','Other meat','Seafood','Dairy']
MODEL={'aids':'AIDS','quaids':'QUAIDS','easi':'Exact EASI','sy_easi':'SY-EASI'}
VAR_CN={'main':'二次主模型','order1':'一次Engel项','order3':'三次Engel项','nosy':'不作SY修正','nopcyc':'删除购买历史排除项','omit5':'遗漏猪肉方程'}
VAR_EN={'main':'Quadratic main model','order1':'Linear Engel term','order3':'Cubic Engel term','nosy':'Without SY correction','nopcyc':'Without purchase-history exclusions','omit5':'Pork equation omitted'}
def data(path):
    with (P/path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def number(v,d=3):
    if v in ('',None,'.'):return '—'
    return f'{float(v):.{d}f}'.replace('-', '−\u2060')
def pct(v,d=2):return number(100*float(v),d)
def integer(v):return f'{int(float(v)):,}'
def sci(v):return f'{float(v):.2e}'.replace('e-','e−')
def one(rows,**keys):
    found=[r for r in rows if all(r[k]==str(v) for k,v in keys.items())]
    if len(found)!=1:raise ValueError((keys,len(found)))
    return found[0]
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,row))+' |' for row in rows])
def interval(r):return '['+number(r['ci_lower'])+', '+number(r['ci_upper'])+']'
def figure(n,title,path):return f'![{n}. {title}](../{path}){{width=6.0in}}'

def build(cn):
    food=FOOD_CN if cn else FOOD_EN; short=SHORT_CN if cn else SHORT_EN
    d=data('outputs/paper/descriptives.csv')
    fit=data('outputs/exact/model_fit_full.csv')
    exact=data('outputs/exact/elasticities_common_full.csv')
    inf=data('outputs/inference/elasticity_inference_paper_main.csv')
    pts=data('outputs/demand/elasticities_main.csv')
    regular=data('outputs/paper/main_regularity.csv')
    ereg=data('outputs/exact/regularity_common_full.csv')
    freq=data('outputs/paper/purchase_frequency.csv')
    rob=data('outputs/paper/robustness_summary.csv')
    robpts=data('outputs/paper/robustness_all_points.csv')
    price=data('outputs/paper/price_variation.csv')
    hist=data('outputs/welfare/policy_exposure_historical.csv')
    scen=data('outputs/welfare/policy_exposure.csv')
    stats={r['statistic']:r['value'] for r in data('outputs/paper/sample_statistics.csv')}
    engel=data('outputs/exact/engel_nested_tests.csv')
    spec=data('outputs/paper/main_specification_tests.csv')
    t={}
    H=lambda zh,en:zh if cn else en
    t['table_descriptives']=table(H(['食品组','预算份额 %','月购买率 %','购买者份额 %','份额标准差'],['Food group','Budget share %','Monthly purchase %','Share if purchased %','Share SD']),[[food[g-1],pct(one(d,good=g)['mean_share']),pct(one(d,good=g)['purchase_rate']),pct(one(d,good=g)['mean_share_buyers']),number(one(d,good=g)['sd_share'])] for g in range(1,9)])
    t['table_fits']=table(H(['模型','估计户月','参数数','导数秩','收敛','GMM准则'],['Model','Estimation N','Parameters','Jacobian rank','Converged','GMM criterion']),[[MODEL[model],integer(one(fit,model=model)['N']),one(fit,model=model)['n_parameters'],one(fit,model=model)['moment_jacobian_rank'],one(fit,model=model)['converged'],number(one(fit,model=model)['criterion'],7)] for model in ['aids','quaids','easi']])
    rr=[]
    for g in range(1,9):
        e=one(inf,sample='common_positive',good=g,type='expenditure'); own=one(inf,sample='common_positive',good=g,type='own_price')
        rr.append([food[g-1],number(e['estimate']),number(e['se_province_two_step']),interval(e),number(own['estimate']),number(own['se_province_two_step']),interval(own)])
    t['table_main']=table(H(['食品组','支出弹性','省SE','95%区间','自价弹性','省SE','95%区间'],['Food group','Expend.','Prov. SE','95% interval','Own price','Prov. SE','95% interval']),rr)
    t['table_exact_own']=table(H(['食品组','AIDS','QUAIDS','精确EASI','SY-EASI'],['Food group','AIDS','QUAIDS','Exact EASI','SY-EASI']),[[food[g-1]]+[number(one(exact,model=m,good=g)['marshallian_own']) for m in ['aids','quaids','easi']]+[number(one(inf,sample='common_positive',good=g,type='own_price')['estimate'])] for g in range(1,9)])
    t['table_exact_exp']=table(H(['食品组','AIDS','QUAIDS','精确EASI','SY-EASI'],['Food group','AIDS','QUAIDS','Exact EASI','SY-EASI']),[[food[g-1]]+[number(one(exact,model=m,good=g)['expenditure']) for m in ['aids','quaids','easi']]+[number(one(inf,sample='common_positive',good=g,type='expenditure')['estimate'])] for g in range(1,9)])
    bef=data('outputs/comparison/meat_before_after.csv')
    matched=data('outputs/comparison/exact_matched_sample.csv')
    t['table_aggregation']=table(H(['精确模型','九类原禽肉','九类原牛羊肉','八类其他肉类','同样本其他肉类'],['Exact model','Original poultry','Original beef/mutton','Merged other meat','Merged, matched N']),[[MODEL[m],number(one(bef,model=m)['old_poultry']),number(one(bef,model=m)['old_beef_mutton']),number(one(bef,model=m)['merged_other_meat']),number(one(matched,grouping='eight',model=m,good=6)['marshallian_own'])] for m in ['aids','quaids','easi']])
    rows=[]
    for g in range(1,9):
        vals=[]
        for sub in ['inc1','inc5']:
            for typ,shock in [('expenditure',0),('marshallian',g)]:
                vals.append(number(one(pts,margin='unconditional',sample='common_positive',subgroup=sub,good=g,type=typ,shock=shock)['elasticity']))
        rows.append([food[g-1]]+vals)
    t['table_income']=table(H(['食品组','最低档支出','最低档自价','最高档支出','最高档自价'],['Food group','Lowest: expend.','Lowest: own price','Highest: expend.','Highest: own price']),rows)
    regs=[[H('SY无条件','SY unconditional'),integer(one(regular,margin='unconditional')['N']),number(one(regular,margin='unconditional')['mean_slutsky_asymmetry'],6),number(one(regular,margin='unconditional')['max_eigenvalue'],6)]]
    regs += [[MODEL[m],integer(one(exact,model=m,good=1)['N']),number(one(ereg,model=m)['slutsky_asymmetry'],6),number(one(ereg,model=m)['slutsky_max_eigenvalue'],6)] for m in ['aids','quaids','easi']]
    t['table_regularity']=table(H(['模型/边际','正支持户月','平均矩阵非对称度','最大特征值'],['Model/margin','Positive-support N','Mean asymmetry','Maximum eigenvalue']),regs)
    t['table_frequency']=table(H(['食品组','月度 %','季度 %','年度 %'],['Food group','Monthly %','Quarterly %','Annual %']),[[food[g-1]]+[pct(one(freq,frequency=frequency,good=g)['purchase_rate']) for frequency in ['monthly','quarterly','annual']] for g in range(1,9)])
    t['table_robustness']=table(H(['规格','正支持户月','正支持 %','最大自价变化','最大支出变化','非负自价数'],['Specification','Positive N','Support %','Largest own change','Largest expend. change','Nonnegative own']),[[(VAR_CN if cn else VAR_EN)[v],integer(one(rob,variant=v)['N']),pct(one(rob,variant=v)['support_rate']),number(one(rob,variant=v)['max_abs_own_change']),number(one(rob,variant=v)['max_abs_exp_change']),one(rob,variant=v)['own_nonnegative']] for v in ['main','order1','order3','nosy','nopcyc','omit5']])
    brackets=H(['全部样本','<5,000','5,001—7,000','7,001—9,000','9,001—12,000','>12,000'],['All','<5,000','5,001–7,000','7,001–9,000','9,001–12,000','>12,000'])
    subgroups=['all','inc1','inc2','inc3','inc4','inc5']
    t['table_historical']=table(H(['报告收入档（元）','全部食品 %','元/代理成员/月','肉类贡献 %','乳品贡献 %','主食油贡献 %'],['Reported income (yuan)','All food %','Yuan/member/month','Meat contrib. %','Dairy contrib. %','Staples/oils %']),[[label,number(one(hist,scenario='all_food_2020_2022',subgroup=sub)['mean_food_budget_pct'],2),number(one(hist,scenario='all_food_2020_2022',subgroup=sub)['mean_cost_yuan_pc'],2)]+[number(one(hist,scenario=s,subgroup=sub)['mean_food_budget_pct'],2) for s in ['meat_2020_2022','dairy_2020_2022','staple_oil_2020_2022']] for label,sub in zip(brackets,subgroups)])
    t['table_scenarios']=table(H(['报告收入档（元）','全部食品+10%','肉类+10%','乳品+10%','主食油+10%'],['Reported income (yuan)','All food +10%','Meat +10%','Dairy +10%','Staples/oils +10%']),[[label]+[number(one(scen,scenario=s,subgroup=sub)['mean_food_budget_pct'],2) for s in ['all_food_10','meat_10','dairy_10','staple_oil_10']] for label,sub in zip(brackets,subgroups)])
    t['table_prices']=table(H(['食品组','定价覆盖 %','省+月+年残差 %','省+年月残差 %'],['Food group','Priced coverage %','Province/month/year %','Province/year-month %']),[[food[g-1],pct(one(d,good=g)['coverage']),pct(one(price,good=g)['residual_prov_month_year']),pct(one(price,good=g)['residual_prov_ym'])] for g in range(1,9)])
    t['table_engel']=table(H(['模型','限制数','协方差秩','F参照统计量','参照自由度','参照p值'],['Model','Restrictions','Covariance rank','F reference','Reference df','Reference p']),[[MODEL[m],one(engel,model=m)['restrictions'],one(engel,model=m)['covariance_rank'],number(one(engel,model=m)['F_reference'],2),'(7,23)',sci(one(engel,model=m)['p_F_reference'])] for m in ['quaids','easi']])
    t['table_spec_tests']=table(H(['主系统系数组','限制数','省协方差秩','最大绝对t','得分p值'],['Main coefficient block','Restrictions','Province rank','Max abs. t','Score p']),[[({'quadratic_Engel':'二次Engel项','demographics':'人口平移项','Mundlak_means':'家庭均值项','SY_correction':'SY修正项','A_prices':'价格A块','C_price_expenditure':'支出价格C块'}[r['test']] if cn else r['test']),r['restrictions'],r['covariance_rank'],number(r['max_t'],2),number(r['score_p'])] for r in spec])
    support=data('outputs/regularity/prediction_support_main.csv')
    t['table_support']=table(H(['食品组','无条件负预测 %','潜在负预测 %','参与购买率 %'],['Food group','Uncond. negative %','Latent negative %','Purchase %']),[[food[g-1],pct(one(support,margin='unconditional',good=g)['negative_rate'],3),pct(one(support,margin='latent',good=g)['negative_rate'],3),pct(one(d,good=g)['purchase_rate'])] for g in range(1,9)])
    t['table_main_margins']=table(H(['食品组','无条件支出','无条件自价','固定参与自价','潜在自价'],['Food group','Uncond. expenditure','Uncond. own','Fixed-participation own','Latent own']),[[food[g-1],number(one(pts,margin='unconditional',sample='common_positive',subgroup='all',good=g,type='expenditure',shock=0)['elasticity'])]+[number(one(pts,margin=m,sample='common_positive',subgroup='all',good=g,type='marshallian',shock=g)['elasticity']) for m in ['unconditional','intensive','latent']] for g in range(1,9)])
    cross=data('outputs/exact/cross_price_common_full.csv')
    t['table_easi_cross']=table([H('需求/价格','Demand/price')]+short,[[food[g-1]]+[number(one(cross,model='easi',demand_good=g,price_good=k)['marshallian']) for k in range(1,9)] for g in range(1,9)])
    t['table_main_cross']=table([H('需求/价格','Demand/price')]+short,[[food[g-1]]+[number(one(pts,margin='unconditional',sample='common_positive',subgroup='all',good=g,type='marshallian',shock=k)['elasticity']) for k in range(1,9)] for g in range(1,9)])
    t['table_simultaneous']=table(H(['食品组','支出弹性同时区间','自价弹性同时区间'],['Food group','Simultaneous expend. band','Simultaneous own band']),[[food[g-1]]+['['+number(one(inf,sample='common_positive',good=g,type=typ)['simultaneous_lower'])+', '+number(one(inf,sample='common_positive',good=g,type=typ)['simultaneous_upper'])+']' for typ in ['expenditure','own_price']] for g in range(1,9)])
    incomes=data('outputs/paper/income_descriptives.csv')
    t['table_sample_income']=table(H(['报告档（元）','户月','档内家庭数','家庭食品月支出','代理人均月支出'],['Reported bracket (yuan)','Household-months','Distinct households','Household food/month','Proxy per-capita/month']),[[brackets[i],integer(one(incomes,income_group_order=i)['household_months']),integer(one(incomes,income_group_order=i)['households']),number(one(incomes,income_group_order=i)['mean_food_spend'],2),number(one(incomes,income_group_order=i)['mean_food_spend_pc'],2)] for i in range(1,6)])
    # Scalar values copied from audited output records; no averaging or covariance operations.
    other=one(inf,sample='common_positive',good=6,type='own_price')
    hx=one(hist,scenario='all_food_2020_2022',subgroup='all')
    scalars={'other_own':number(other['estimate']),'other_ci':interval(other),'other_se':number(other['se_province_two_step']),'other_budget':number(one(inf,sample='common_positive',good=6,type='expenditure')['estimate']),
      'historical_pct':number(hx['mean_food_budget_pct'],2),'historical_yuan':number(hx['mean_cost_yuan_pc'],2),'historical_p10':number(hx['p10_food_budget_pct'],2),'historical_p90':number(hx['p90_food_budget_pct'],2),
      'mean_food_spend':number(stats['mean_monthly_food_spend'],2),'median_food_spend':number(stats['median_monthly_food_spend'],2),'mean_pc_spend':number(stats['mean_proxy_per_capita_food_spend'],2),
      'regular_main_asym':number(one(regular,margin='unconditional')['mean_slutsky_asymmetry'],5),'regular_main_eig':number(one(regular,margin='unconditional')['max_eigenvalue'],5),
      'meat_historical':number(one(hist,scenario='meat_2020_2022',subgroup='all')['mean_food_budget_pct'],2),
      'uniform_yuan':number(one(scen,scenario='all_food_10',subgroup='all')['mean_cost_yuan_pc'],2),
      'other_price_order1':number(one(robpts,variant='order1',good=6)['own_price']),
      'other_price_order3':number(one(robpts,variant='order3',good=6)['own_price']),
      'other_price_nosy':number(one(robpts,variant='nosy',good=6)['own_price']),
      'other_price_nopcyc':number(one(robpts,variant='nopcyc',good=6)['own_price']),
      'other_price_omit5':number(one(robpts,variant='omit5',good=6)['own_price'])}
    for key,value in scalars.items():t[key]=value
    captions=H(['八类食品外部价格路径','八类食品预算份额与未购买比例','主模型自身价格响应及省级两阶段区间','报告收入档的食品支出响应','10%特定食品涨价的固定篮子暴露'],['External prices for eight food groups','Budget shares and nonpurchase by food group','Main own-price responses and province two-step intervals','Food-expenditure responses by reported income bracket','Fixed-basket exposure to 10% category-price increases'])
    paths=['figures/fig1_eight_group_prices.png','figures/fig2_eight_group_budget.png','figures/fig3_main_own_price_ci.png','figures/fig4_income_expenditure.png','outputs/figures/policy_exposure.png']
    for i,(caption,path) in enumerate(zip(captions,paths),1):t['figure'+str(i)]=figure(('图' if cn else 'Figure ')+str(i),caption,path)
    return t
