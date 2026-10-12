"""Rebuild local inputs and orchestrate the complete Stata research workflow."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import json
import subprocess
import sys
import time
import csv
from run_validation import ROOT, call_stata


def run(script,args,artifact,log,name,timeout=1800):
    out=ROOT/artifact
    out.parent.mkdir(parents=True,exist_ok=True)
    logpath=ROOT/log
    logpath.parent.mkdir(parents=True,exist_ok=True)
    result=call_stata(script,args,ROOT/'tmp/pipeline'/name,out,logpath,timeout)
    print(f"{name}: execution_success={result['success']}",flush=True)
    return result


def native(model,k=8,family=None):
    suffix=f'{model}_{k}' if family is None else f'{model}_family_{family}'
    target=ROOT/'outputs/estimation'/suffix
    target.mkdir(parents=True,exist_ok=True)
    args=[ROOT/f'data/cells_quarter_{k}.csv',target,model,k,3,400]
    if family is not None: args.append(f'type=={family}')
    return run('02_estimate.do',args,f'outputs/estimation/{suffix}/model_summary.csv',
               f'outputs/estimation/{suffix}/estimate.log',suffix)


def bounded_corner():
    started=time.time()
    artifact=ROOT/'outputs/corner/fit_status.csv'
    try:
        process=subprocess.run(['bash',str(ROOT/'code/03_corner_bounded.sh')],
                               timeout=2500,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        rc=process.returncode
        (ROOT/'logs/corner_bounded_driver.log').write_text(process.stdout,encoding='utf-8')
    except subprocess.TimeoutExpired:
        rc=124
    fresh=artifact.exists() and artifact.stat().st_mtime>=started-1
    pending=True
    if fresh:
        with artifact.open(encoding='utf-8') as f:
            row=next(csv.DictReader(f))
        pending=float(row.get('postprocessing_pending',0))!=0
    return {'script':'03_corner_bounded.sh','seconds':time.time()-started,
            'returncode':rc,'artifact':str(artifact.relative_to(ROOT)),
            'success':rc==0 and fresh and not pending}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--rebuild-data',action='store_true')
    parser.add_argument('--validation',action='store_true')
    parser.add_argument('--corner',action='store_true')
    parser.add_argument('--diagnostic-modeldir',type=Path,
                        help='Explicit native parameter directory for diagnostic scenarios; no silent fallback.')
    args=parser.parse_args()
    results=[]
    if args.rebuild_data:
        results.append(run('01_build_data.do',[], 'data/cells_quarter_8.csv',
                           'logs/01_build_data.log','build_data',7200))
        results.append(run('01_validate_data.do',[], 'outputs/data_audit/validation_metrics.csv',
                           'logs/01_validate_data.log','validate_data',1800))
    if args.validation:
        results.append(run('01_build_cv_prices.do',[], 'data/cells_quarter_8_cvfold5.csv',
                           'logs/01_build_cv_prices.log','cv_prices',1800))
    with ThreadPoolExecutor(max_workers=2) as pool:
        tasks=[pool.submit(native,m) for m in ('aidads','maidads')]
        tasks.append(pool.submit(native,'maidads',9))
        tasks.extend(pool.submit(native,'maidads',8,t) for t in range(1,5))
        results.extend(task.result() for task in tasks)
    for m in ('aids','quaids'):
        target=ROOT/'outputs/comparators'/f'{m}_8'
        target.mkdir(parents=True,exist_ok=True)
        results.append(run('04_comparators.do',[ROOT/'data/cells_quarter_8.csv',target,m,8,3],
                           f'outputs/comparators/{m}_8/fit_summary.csv',
                           f'outputs/comparators/{m}_8/run.log',f'{m}_8'))
    subprocess.run([sys.executable,str(ROOT/'code/run_comparisons.py')],check=True)
    results.append(run('05_income.do',[], 'outputs/income/model_scope.csv',
                       'logs/05_income.log','income'))
    results.append(run('05_income_sensitivity.do',[], 'outputs/income/sensitivity.csv',
                       'logs/05_income_sensitivity.log','income_sensitivity'))
    results.append(run('05_income_tests.do',[], 'outputs/income/conditional_wald_tests.csv',
                       'logs/05_income_tests.log','income_tests'))
    scenario_args=[] if args.diagnostic_modeldir is None else [args.diagnostic_modeldir]
    results.append(run('06_scenarios.do',scenario_args, 'outputs/scenarios/province_income_growth.csv',
                       'logs/06_scenarios.log','scenarios',3600))
    if args.validation:
        subprocess.run([sys.executable,str(ROOT/'code/run_validation.py'),'--workers','4'],check=True)
    if args.corner:
        results.append(bounded_corner())
        results.append(run('03_corner_elasticity.do',[], 'outputs/corner/price_response_all_4_families.csv',
                           'logs/03_corner_elasticity.log','corner_elasticity',3600))
        results.append(run('03_test_corner_forecast.do',[], 'outputs/corner/forecast_numeric_validation.csv',
                           'logs/03_test_corner_forecast.log','corner_forecast_test'))
        results.append(run('03_corner_scenarios.do',[32], 'outputs/corner_scenarios/family_income_growth_32.csv',
                           'logs/03_corner_scenarios_32.log','corner_scenarios32',3600))
        results.append(run('03_corner_scenarios.do',[64,'sensitivity'], 'data/corner_scenario_sensitivity_64.dta',
                           'logs/03_corner_scenarios_64.log','corner_scenarios64',1800))
        results.append(run('03_corner_scenario_sensitivity.do',[], 'outputs/corner_scenarios/integration_sensitivity_32_64.csv',
                           'logs/03_corner_scenario_sensitivity.log','corner_scenario_integration'))
    (ROOT/'outputs/pipeline_execution.json').write_text(
        json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    subprocess.run([sys.executable,str(ROOT/'code/build_report.py')],check=True)
    if not all(r['success'] for r in results):
        raise SystemExit('Some stages failed. See pipeline ledger and disclosed results; no successful-stage claim was inferred from exit code alone.')


if __name__=='__main__':
    main()
