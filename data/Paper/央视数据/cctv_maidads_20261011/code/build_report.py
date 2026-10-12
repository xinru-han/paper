"""Render already-estimated Stata aggregates; do not estimate in Python."""
from pathlib import Path
import json
import datetime
import hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs'
NAMES=['主食','油脂','蔬菜','水果','猪肉','其他肉类','水产品','奶类']
EN=['Staples','Oil','Vegetables','Fruit','Pork','Other meat','Seafood','Dairy']
FAMILY={1:'年轻家庭',2:'成年家庭',3:'老年家庭',4:'青少年家庭'}
FAMILY_EN={1:'Young',2:'Adult',3:'Elderly',4:'Adolescent'}


def actual_native(folder):
    return folder.name.startswith(('maidads_','aidads_'))


def family_plot(df,path,title):
    fig,axs=plt.subplots(2,2,figsize=(12,8),sharex=True)
    for (t,f),ax in zip(df.groupby('type'),axs.flat):
        f=f[f.scenario_order<=5].sort_values('growth_factor')
        for j in range(1,9): ax.plot(f.growth_factor,f[f'income_elasticity{j}'],label=EN[j-1])
        ax.set_title(FAMILY[t]); ax.axhline(0,color='grey',lw=.6); ax.grid(alpha=.15)
        ax.set_xlabel('Reported-income growth factor'); ax.set_ylabel('Income elasticity')
    axs[0,0].legend(fontsize=8,frameon=False,ncol=2)
    fig.suptitle(title)
    fig.tight_layout(); fig.savefig(path,dpi=160); plt.close(fig)


def table(df):
    if df.empty: return '无可用结果。'
    def fmt(x):
        if pd.isna(x): return 'NA'
        if isinstance(x,(float,np.floating)): return f'{x:.6g}'
        return str(x)
    return '\n'.join(['| '+' | '.join(map(str,df.columns))+' |',
                     '| '+' | '.join(['---']*len(df.columns))+' |']+
                    ['| '+' | '.join(fmt(x) for x in row)+' |' for row in df.itertuples(index=False,name=None)])


def read(path):
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def collect_fit():
    rows=[]
    for folder in sorted((OUT/'estimation').glob('*')):
        if not actual_native(folder): continue
        df=read(folder/'model_summary.csv')
        if not df.empty:
            r=df.iloc[0]
            rows.append(dict(model=folder.name,N=r['N'],AIC=r['AIC'],BIC=r['BIC'],
                score=r['projected_gradient'],qualified=r['converged'],omega=r['omega']))
    for folder in sorted((OUT/'comparators').glob('*')):
        df=read(folder/'fit_summary.csv')
        if not df.empty:
            r=df.iloc[0]
            rows.append(dict(model=folder.name,N=r['observations'],AIC=r['qml_aic'],BIC=r['qml_bic'],
                score=r['max_score'],qualified=r['stationary'],omega=np.nan))
    return pd.DataFrame(rows)


def render_plots():
    cjk=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    if cjk.exists():
        font_manager.fontManager.addfont(str(cjk))
        plt.rcParams['font.family']=font_manager.FontProperties(fname=str(cjk)).get_name()
    figdir=ROOT/'figures'; figdir.mkdir(exist_ok=True)
    freq=read(OUT/'data_audit/frequency_diagnostics.csv')
    if not freq.empty:
        fig,ax=plt.subplots(figsize=(9,4.8))
        for frequency in ('month','quarter','year'):
            f=freq[(freq.k==8)&(freq.frequency==frequency)]
            ax.plot(range(8),f.purchase_rate.to_numpy(),marker='o',label=frequency)
        ax.set_xticks(range(8),EN,rotation=20); ax.set_ylabel('Purchase probability')
        ax.set_ylim(0,1.02); ax.legend(frameon=False); ax.grid(axis='y',alpha=.2)
        fig.tight_layout(); fig.savefig(figdir/'purchase_frequency.png',dpi=160); plt.close(fig)
    first=read(OUT/'income/food_budget_income_scenarios.csv')
    if not first.empty:
        fig,ax=plt.subplots(figsize=(8,5))
        for t,f in first.groupby('type'):
            ax.plot(f.growth_factor,100*f.income_budget/f.base_m,marker='o',label=FAMILY_EN[t])
        ax.set_xlabel('Reported-income growth factor'); ax.set_ylabel('Covered-food budget index (baseline=100)')
        ax.axhline(100,color='grey',lw=.6); ax.legend(frameon=False); ax.grid(alpha=.2)
        fig.tight_layout(); fig.savefig(figdir/'income_budget_projection.png',dpi=160); plt.close(fig)
    fam=read(OUT/'scenarios/family_income_growth.csv')
    if not fam.empty:
        title='Unqualified parameter diagnostics, not formal forecasts' if (fam.estimate_qualified!=1).any() else 'Conditional income scenarios'
        family_plot(fam,figdir/'family_income_elasticity.png',title)
    corner_fam=read(OUT/'corner_scenarios/family_income_growth_32.csv')
    if not corner_fam.empty:
        family_plot(corner_fam,figdir/'corner_family_income_elasticity.png',
                    'Restricted corner pilot diagnostics, 32 integration draws; not formal forecasts')
    prov=read(OUT/'scenarios/province_income_growth.csv')
    if not prov.empty:
        f=prov[prov.scenario_order==4].sort_values('province')
        fig,ax=plt.subplots(figsize=(10,9))
        cmap=plt.get_cmap('RdYlGn').copy(); cmap.set_bad('#dddddd')
        img=ax.imshow(f[[f'quantity_index{j}' for j in range(1,9)]].to_numpy()-100,
                      aspect='auto',cmap=cmap,vmin=-10,vmax=10)
        ax.set_xticks(range(8),EN,rotation=20)
        ax.set_yticks(range(len(f)),f.province_name.to_numpy())
        status='DIAGNOSTIC, unqualified fit. ' if (f.estimate_qualified!=1).any() else ''
        ax.set_title(status+'Income +50%, fixed 2022 prices: quantity-equivalent change (%)')
        fig.colorbar(img,ax=ax,label='Percent change'); fig.tight_layout()
        fig.savefig(figdir/'province_income_50pct.png',dpi=160); plt.close(fig)
    corner_prov=read(OUT/'corner_scenarios/province_income_growth_32.csv')
    if not corner_prov.empty:
        f=corner_prov[corner_prov.scenario_order==4].sort_values('province')
        fig,ax=plt.subplots(figsize=(10,9))
        img=ax.imshow(f[[f'quantity_index{j}' for j in range(1,9)]].to_numpy()-100,
                      aspect='auto',cmap='RdYlGn',vmin=-10,vmax=10)
        ax.set_xticks(range(8),EN,rotation=20); ax.set_yticks(range(len(f)),f.province_name.to_numpy())
        ax.set_title('Restricted pilot, 32-draw DIAGNOSTIC: income +50%, fixed 2022 prices')
        fig.colorbar(img,ax=ax,label='Percent change in quantity equivalent')
        fig.tight_layout(); fig.savefig(figdir/'corner_province_income_50pct.png',dpi=160); plt.close(fig)


def main():
    native_qualified=[p.parent.name for p in (OUT/'estimation').glob('*/model_summary.csv')
                      if actual_native(p.parent) and read(p).iloc[0]['converged']==1]
    status={'native_qualified_actual_fits':native_qualified,
            'built_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
            'pooled_diagnostic_model':'maidads_8_warm',
            'corner_outputs_present':(OUT/'corner/fit_status.csv').exists(),
            'final_food_elasticity_sampling_inference':False,
            'bootstrap':False,'notion_synced':False}
    corner_status=read(OUT/'corner/fit_status.csv')
    status['corner_postprocessing_completed']=bool(not corner_status.empty and
        corner_status.iloc[0].get('postprocessing_pending',1)==0)
    status['corner_forecast_formal']=False
    (OUT/'delivery_status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
    sections=['# 央视数据 MAIDADS 实证结果',
        '本报告仅使用本次 Stata/Mata 输出，不沿用农户调查或旧 EASI 弹性。没有 bootstrap；最终食品弹性不提供伪造的标准误、p 值或置信区间。',
        '## 主要结论与未完成项',
        ('当前真实数据的原生完整自由 MAIDADS/AIDADS 没有通过资格检查，不能将以下负价格弹性或情景解释为正式估计结论。'
         if not native_qualified else '实际数据通过原生数值资格检查的目录：'+', '.join(native_qualified)),
        'AIDS、QUAIDS 的八类主规格达到数值驻点，但主食补偿自价格弹性仍为正。人口口径和汇总敏感性不是按显著性或符号选择样本。',
        'warm8 虽然代表点弹性温和，最低预算前沿附近的部分食品支出弹性最大达到约4.9×10^15，均值也被拉到约3.35×10^11；所有极值保留。这本身就使该候选的弹性分布不适合作正式结论。',
        '2022 时间留出中，省份历史季度份额基准比 AIDS/QUAIDS 的份额预测更准确；当前 pooled 规格不能证明已经识别可靠的因果价格响应。',
        '零购买扩展是完整季度记录上的受限随机偏好试估，不是全样本完整自由 MAIDADS。支持点近似的平均预算低估约13%，其外部验证不能当作全体家庭验证。',
        '受限角点也未达到正式实证标准：同θ从16增加到256积分draw使目标值上升约9.4%；支持点2022留出中水果份额/购买率明显低估、猪肉份额明显高估。不能因为自价格由效用结构保证为负就认定拟合合格。',
        '受限角点的2022支持点留出中，7个独立份额方程有6个RMSE劣于常数训练均值，8类购买概率有6个Brier劣于该基准；其曲线不能作为已经通过样本外验证的需求预测。',
        '没有坚果独立价格、准确人口或确认的收入报告周期；十类体系和准确人均年/月收入不能从现有信息中凭空补全。',
        '## 1. 样本与测量',
        table(read(OUT/'data_audit/sample_flow.csv')),
        '零购买按正支出定义，不把记录数量为零当作零购买。价格为独立外部类别监测价格的固定篮子指数；数量是参考价格下的购买量等价值，不是公斤。八类不包含坚果，不能用食用油价格给坚果补一个第十类。',
        '样本没有已验证的收入报告周期、准确家庭人口及人口权重。家庭形态仅为年轻、成年、老年、青少年四种原始标签，不是核家庭/扩展家庭。',
        table(read(OUT/'data_audit/group_price_coverage_8.csv')),
        '**人口口径敏感性**',table(read(OUT/'data_audit/permonth_size_sensitivity.csv')),
        '基准按窗口末次人口档代理归一化，另列逐月人口代理后平均的结果。发生人口档变化的窗口中，两种预算口径的平均绝对相对差约为季度38.4%、年度27.4%；不能以全样本均值变化很小掩盖个体测量影响。',
        '## 2. 模型比较与资格',
        '同一类别/同一窗口/同一样本的 QML AIC/BIC 才可比较。九类与八类、年与季、删选样本间不能直接用这些信息准则择优。AIDS/QUAIDS 的 qualified 列仅代表数值驻点，并不自动满足全样本凹性；MAIDADS 的该列还包含根、边界与秩诊断。',
        table(collect_fit()),
        '八类季度同样本：QUAIDS的AIC比AIDS低约209.83，但2022留出RMSE仅从0.043401降到0.043398，且二者都未满足全系统凹性；不能仅凭AIC将其宣布为经过理论与预测验证的最优模型。原生九类MAIDADS在30分钟上限内没有完整自由候选，不补造其弹性。',
        '模型退化、弱端点、数值边界、根不唯一与非驻点均保留。不以负 Hicksian 符号替代数据检验；原生 MAIDADS 的非正自价格和非负交叉替代来自理论结构，不是 Cholesky 后处理。',
        'alpha/beta 的 softmax 实现未覆盖精确零的自然 simplex 边界。触及 logit guard 不是无边界合格解，但也不是证明经济模型不成立；后续若探索自然边界需直接 simplex/facet KKT，而非无限放宽数值 guard。',
        '## 3. 完整弹性与分布']
    for folder in sorted((OUT/'estimation').glob('*')):
        if not actual_native(folder): continue
        rep=read(folder/'representative_budget_elasticities.csv')
        if rep.empty: continue
        if len(rep)==8: rep.insert(1,'食品',NAMES)
        sections.extend([f'### {folder.name}',table(rep),
            '代表点评价使用样本平均预算、几何平均价格；不是逐户弹性的简单平均。'])
        for name in ('representative_price_elasticities.csv','elasticity_distribution.csv','audit.csv'):
            d=read(folder/name)
            if not d.empty: sections.extend([f'**{name}**',table(d)])
    for folder in sorted((OUT/'comparators').glob('*')):
        m=folder.name
        if m.startswith('synthetic'): continue
        rep=read(folder/'representative_elasticities.csv')
        if not rep.empty:
            if len(rep)==8: rep.insert(1,'食品',NAMES)
            if len(rep)==9: rep.insert(1,'食品',NAMES[:5]+['禽类及其他肉','牛羊肉']+NAMES[6:])
            sections.extend([f'### {m}',table(rep)])
            if m in ('aids_8','quaids_8'):
                for name in ('marshallian_matrix.csv','hicksian_matrix.csv'):
                    sections.extend([f'**{name}**',table(read(folder/name))])
    validation=read(OUT/'validation/all_fold_metrics.csv')
    if not validation.empty:
        keep=[c for c in ('model','fold','target_cells','target_household_quarters',
              'invalid_household_quarters','estimate_stationary','estimate_qualified','eligible_complete_fit',
              'share_rmse','share_mae','cell_equal_weight_rmse','training_mean_share_rmse',
              'province_history_share_rmse','rmse_ratio') if c in validation]
        sections.extend(['## 4. 留出验证',table(validation[keep]),
            '这是给定实际留出价格和预算的条件需求预测。五折按整省划分并重新计算训练篮子，2022 不进入时间验证的估计。训练均值和历史份额均按户季数权重计算；不合格拟合仍展示诊断误差，但不进入合格模型选择。'])
    sections.extend(['## 5. 收入与家庭差异',
        '人均收入由收入区间的条件分布及人口代理构造。第一阶段是条件平均对数食品预算投影，不是收入的因果识别，也不是已验证的支出工具变量。食品收入弹性为食品支出弹性乘食品预算收入响应。',
        table(read(OUT/'income/family_income_band_summary.csv')),
        '**收入预算条件 Wald 检验**',table(read(OUT/'income/conditional_wald_tests.csv')),
        '**收入预算斜率的条件推断**',table(read(OUT/'income/conditional_slope_inference.csv')),
        '以上 p 值使用家庭聚类协方差，但将估计的区间收入矩及情景锚点视为固定，未传递收入分布估计误差，不能代替最终食品收入弹性的联合推断。',
        '**收入第一阶段敏感性**',table(read(OUT/'income/sensitivity.csv')),
        '**2022 年每户一次的预算情景**',table(read(OUT/'income/food_budget_income_scenarios.csv')),
        '连续二次曲线的老年家庭斜率可能转负；线性与开口收入档假设的不同结果必须同时解释。情景以实际年度月均购买预算为锚点，施加条件几何预算响应，不冒称分布积分后的算术期望预算。'])
    fam=read(OUT/'scenarios/family_income_growth.csv')
    if not fam.empty:
        keep=['type','growth_factor','complete_coverage','estimate_stationary','estimate_qualified']
        keep += [f'income_elasticity{j}' for j in range(1,9)]
        sections.extend(['## 6. 收入增长参数情景诊断',table(fam[fam.scenario_order<=5][keep]),
            'pooled 文件中的家庭差异来自收入预算曲线及家庭构成，偏好差异须看四家庭分开拟合的文件。逐户预测后才按省/家庭等权汇总，不对平均预算先进行非线性变换。',
            '省均数据见 `scenarios/province_income_growth.csv`，包含收入增幅10/25/50/100%和年增长1/2/3%至2030/2035/2050。价格和2022家庭构成固定；这是样本条件情景，不是含人口、价格变化的省级总量预测。',
            '预测覆盖失败会使该汇总值空缺；预算拟合域、收入中央域及全域外推比例均单列。不合格 MAIDADS 的情景只是参数诊断，正式列 formal_quantity/formal_income_elasticity 只在 qualified_forecast=1 时提供。',
            '![家庭收入弹性曲线](../figures/family_income_elasticity.png)',
            '![省均收入情景](../figures/province_income_50pct.png)'])
    sections.extend(['## 7. 零购买角点扩展',
        '平移对数效用的 KKT 角点模型让集合外数量严格为零，不加小常数，不套用 AIDS/QUAIDS 的两步份额修正。试估不按食品正购买状态删人，但只使用有完整三个月记录的季度，必须另看窗口选择偏差。真实试估为 alpha=beta、共同高低位移比率、固定转换速度的受限扩展，不能称完整自由 MAIDADS 或已证明的首次创新。',
        '该受限结构本身保证所有食品正常性、非正自价格和毛替代；这些符号不能作为独立的数据检验。支持点约束、有限积分与参数边界仍须核查。'])
    for name in ('fit_status.csv','full_sample_descriptive.csv','training_fit.csv','holdout_fit.csv',
                 'own_price_and_budget_at_median_all_4_families.csv',
                 'point_prediction_metrics.csv','constant_mean_baseline_holdout_metrics.csv',
                 'integration_sensitivity_no_refit.csv','support_moment_sensitivity_no_refit.csv',
                 'fitted_solver_checks.csv','moment_jacobian_singular_values.csv',
                 'independent_variation_scope.csv','optimizer_starts_status.csv',
                 'price_response_all_4_families.csv',
                 'budget_response_curve_all_4_families.csv'):
        d=read(OUT/'corner'/name)
        if not d.empty: sections.extend([f'**{name}**',table(d)])
    corner_fam=read(OUT/'corner_scenarios/family_income_growth_32.csv')
    if not corner_fam.empty:
        keep=['type','growth_factor','complete_coverage','full_sample_fit','qualified_forecast']
        keep += [f'income_elasticity{j}' for j in range(1,9)]
        sections.extend(['### 受限角点的逐户收入情景诊断',
            table(corner_fam[corner_fam.scenario_order<=5][keep]),
            '使用已估计受限参数、32固定偏好积分draw、解析的draw内预算导数，逐户预测全部22,775个正预算年度家庭后汇总。不是在全体家庭重估的参数，不是完整自由MAIDADS，qualified_forecast=0。按省及14情景见 corner_scenarios/province_income_growth_32.csv。',
            '季度估计的购买kernel在年度活跃月平均预算和年度价锚点下求值，这是额外的跨频率结构假设，没有处理库存或记录周期机制。purchase_prob是模型条件参与概率，不是全年至少买一次的概率；原生季度参数情景也有跨频率限制。',
            table(read(OUT/'corner_scenarios/integration_sensitivity_32_64.csv'))])
        sections.append('32/64draw同θ子样本的类别平均绝对相对数量差约1.7%至9.4%，个别油脂低量点接近91%，尚未收敛为高精度积分预测；这是数值积分敏感性，不是置信区间。')
        sections.extend(['**32/64/128/256draw同θ全国子样本汇总**',
            table(read(OUT/'data_audit/corner_integration_summary.csv')),
            '提高积分数的同一227户子样本中，+50%收入的数量增长指数相邻最大差缩至约0.036个指数点，收入弹性相邻最大绝对差约0.00051；增长曲线比水平稳定，但128→256draw的基准数量最大仍差约6.27%，不能宣称水平预测已经数值收敛。'])
        sections.extend(['![受限角点家庭收入曲线](../figures/corner_family_income_elasticity.png)',
                         '![受限角点省均情景](../figures/corner_province_income_50pct.png)'])
    sections.extend(['支持点留出不等于全部家庭留出；预算分层支撑近似和16/64/256积分敏感性详见角点文档。模拟偏好积分不是 bootstrap。总量弹性、参与概率响应、正购买条件均量响应分开；选择后条件均量为正不直接违反 Slutsky。',
        '## 8. 结果边界',
        '价格弹性仅为覆盖食品预算内的 Marshallian 与食品子效用内的 Hicksian。未观察非食品/外食/储蓄，不能将收入减食品支出伪造成完整外部商品。外部省价格仍有品类代理和价格内生性局限。',
        '当前无总体联合推断；没有给这些最终食品弹性报告 p 值不是遗漏显著性，而是没有实施足以支持它的完整推断。边界和未识别嵌套比较也不能硬套常规 LR 卡方检验。',
        '收入预算表的 income_elasticity_new 是家庭对数预算斜率的等户均值；aggregate_budget_income_eta 是预算加权的总预算收入弹性。食品数量弹性按数量加权，二者不可混用。跨省家庭类型的支出份额和数量弹性使用不同价格与权重，不能机械要求其份额加权和等于1；微观及同价省份的预算导数闭合已独立检验。',
        '科研日志在 `docs/RESEARCH_LOG.md`。当前工具未提供 Notion 连接，不能声称已写入 Notion。'])
    report='\n\n'.join(sections)+'\n'
    (OUT/'RESULTS_CN.md').write_text(report,encoding='utf-8')
    txt=[report, '\n\n全部省均情景与其他主要汇总表（原始 CSV）：\n']
    for folder in ('data_audit','income','scenarios','corner','corner_scenarios'):
        for path in sorted((OUT/folder).glob('*.csv')):
            if path.name in ('smd_actual_support.csv','cell_scenarios.csv',
                 'category_external_prices_all_sources.csv','category_external_prices_observed.csv',
                 'group_price_month_8.csv','group_price_month_9.csv'): continue
            txt.extend([f'\n--- {path.relative_to(ROOT)} ---\n',path.read_text(encoding='utf-8')])
    for directory in ('estimation','comparators'):
        for folder in sorted((OUT/directory).glob('*')):
            if directory=='estimation' and not actual_native(folder): continue
            if directory=='comparators' and not folder.name.startswith(('aids_','quaids_')): continue
            for filename in ('model_summary.csv','fit_summary.csv','parameters.csv','audit.csv',
                             'representative_budget_elasticities.csv','representative_elasticities.csv',
                             'representative_price_elasticities.csv','elasticity_distribution.csv',
                             'marshallian_matrix.csv','hicksian_matrix.csv'):
                path=folder/filename
                if path.exists(): txt.extend([f'\n--- {path.relative_to(ROOT)} ---\n',path.read_text(encoding='utf-8')])
    (OUT/'ALL_MAIN_RESULTS.txt').write_text('\n'.join(txt),encoding='utf-8')
    render_plots()
    checksums={}
    for folder in ('code','ado','docs'):
        for path in sorted((ROOT/folder).glob('*')):
            if path.is_file(): checksums[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
    (OUT/'code_manifest.json').write_text(json.dumps(checksums,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Rendered RESULTS_CN.md, ALL_MAIN_RESULTS.txt and figures from Stata outputs.')


if __name__=='__main__': main()
