"""Orchestrate Stata fits; no statistical estimation is done in Python."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import argparse
import csv
import json
import os
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
STATA = Path('/usr/local/stata17/stata-se')


def call_stata(script, args, jobdir, expected, log, timeout=1800):
    jobdir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, STATATMP=str(jobdir))
    started = time.time()
    command = [str(STATA), '-b', 'do', str(ROOT / 'code' / script)]
    command.extend(str(x) for x in args)
    try:
        run = subprocess.run(command, cwd=jobdir, env=env, timeout=timeout,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    except subprocess.TimeoutExpired:
        return {'script': script, 'seconds': time.time()-started,
                'returncode': 124, 'stata_errors': ['timeout'],
                'artifact': str(expected.relative_to(ROOT)), 'success': False}
    (jobdir / (script + '.stdout.txt')).write_text(run.stdout, encoding='utf-8')
    logs=[log] if log.exists() else []
    logs.extend(p for p in jobdir.glob('*.log')
                if p.stat().st_mtime>=started-1 and p not in logs)
    errors=[]
    for path in logs:
        logtext=path.read_text(encoding='utf-8',errors='replace')
        errors.extend(re.findall(r'^r\((\d+)\);\s*$',logtext,flags=re.M))
    success = (run.returncode == 0 and not errors and expected.exists()
               and expected.stat().st_mtime >= started-1)
    return {'script': script, 'seconds': time.time()-started,
            'returncode': run.returncode, 'stata_errors': errors,
            'artifact': str(expected.relative_to(ROOT)), 'success': success}


def validate(fold, model):
    if fold == 'temporal':
        source = ROOT / 'data/cells_quarter_8.csv'
        trainfilter, testfilter = 'year<=2021', 'year==2022'
    else:
        number = int(fold.replace('province', ''))
        source = ROOT / f'data/cells_quarter_8_cvfold{number}.csv'
        trainfilter = f'year<=2021&cv_fold!={number}'
        testfilter = f'year<=2021&cv_fold=={number}'
    deadline = time.time()+600
    while not source.exists() and time.time() < deadline:
        time.sleep(10)
    out = ROOT / 'outputs/validation' / f'{fold}_{model}'
    fit, pred, metrics = (out/x for x in ('fit', 'prediction', 'metrics'))
    for directory in (out, fit, pred, metrics):
        directory.mkdir(parents=True, exist_ok=True)
    temp = ROOT / 'tmp/validation' / f'{fold}_{model}'
    record = {'fold': fold, 'model': model, 'input': str(source.relative_to(ROOT)),
              'training_filter': trainfilter, 'test_filter': testfilter, 'steps': []}
    if model in ('maidads', 'aidads'):
        args = [source, fit, model, 8, 2, 400, trainfilter]
        step = call_stata('02_estimate.do', args, temp, fit/'model_summary.csv', fit/'estimate.log')
    else:
        args = [source, fit, model, 8, 2, trainfilter]
        step = call_stata('04_comparators.do', args, temp, fit/'fit_summary.csv', fit/'run.log')
    record['steps'].append(step)
    if step['success']:
        if model in ('maidads', 'aidads'):
            script = '06_predict.do'
            args = [source, fit, pred, 8, testfilter]
        else:
            script = '07_comparator_predict.do'
            args = [source, fit, pred, model, 8, testfilter]
        step = call_stata(script, args, temp, pred/'predictions.csv', pred/'predict.log')
        record['steps'].append(step)
    if step['success']:
        args = [source, pred/'predictions.csv', metrics, model, fold, trainfilter, 8]
        step = call_stata('07_validation_metrics.do', args, temp, metrics/'metrics.csv', metrics/'metrics.log')
        record['steps'].append(step)
    record['success'] = all(s['success'] for s in record['steps']) and len(record['steps']) == 3
    (out/'execution.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"{fold} {model}: execution_success={record['success']}", flush=True)
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--folds', nargs='+', default=['temporal']+[f'province{i}' for i in range(1,6)])
    parser.add_argument('--models', nargs='+', default=['aids', 'quaids', 'aidads', 'maidads'])
    parser.add_argument('--metrics-only', action='store_true')
    args = parser.parse_args()
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(refresh_metrics if args.metrics_only else validate, f, m)
                   for f in args.folds for m in args.models]
        for future in as_completed(futures):
            results.append(future.result())
    out = ROOT/'outputs/validation'
    (out/'execution_ledger.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    rows = []
    for r in results:
        path = out/f"{r['fold']}_{r['model']}"/'metrics/metrics.csv'
        if path.exists() and r['success']:
            with path.open(encoding='utf-8') as f:
                rows.extend(csv.DictReader(f))
    if rows:
        fields = list(dict.fromkeys(field for row in rows for field in row))
        with (out/'all_fold_metrics.csv').open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
            writer.writeheader(); writer.writerows(rows)
    if not all(r['success'] for r in results):
        raise SystemExit('Some Stata validation jobs failed; see execution ledger. No fold was silently removed.')


def refresh_metrics(fold, model):
    out = ROOT/'outputs/validation'/f'{fold}_{model}'
    path = out/'execution.json'
    record = json.loads(path.read_text(encoding='utf-8'))
    source = ROOT/record['input']
    step = call_stata('07_validation_metrics.do',
                      [source, out/'prediction/predictions.csv', out/'metrics', model,
                       fold, record['training_filter'], 8],
                      ROOT/'tmp/validation'/f'{fold}_{model}',
                      out/'metrics/metrics.csv', out/'metrics/metrics.log')
    record['metrics_refresh'] = step
    record['success'] = record['success'] and step['success']
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    return record


if __name__ == '__main__':
    main()
