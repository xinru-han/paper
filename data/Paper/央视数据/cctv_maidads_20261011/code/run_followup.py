"""Run the natural-boundary follow-up in Stata, without publication or bootstrap."""
from pathlib import Path
import argparse
import csv
import json
from run_validation import ROOT, call_stata


def run_one(name, model, source, sample, warm=None, validate=False,
            starts=2, iterate=500, timeout=1800):
    base = ROOT / 'outputs/followup_20261013' / name
    fit, prediction, metrics = (base / x for x in ('fit', 'prediction', 'metrics'))
    temp = ROOT / 'tmp/followup_20261013' / name
    for path in (base, fit, prediction, metrics):
        path.mkdir(parents=True, exist_ok=True)
    native = model in ('maidads', 'aidads')
    if native:
        script = '02_estimate_simplex.do'
        args = [source, fit, model, 8, starts, iterate, sample]
        if warm is not None:
            args.append(warm)
        expected, log = fit / 'model_summary.csv', fit / 'estimate.log'
    else:
        script = '04_comparators.do'
        args = [source, fit, model, 8, starts, sample]
        expected, log = fit / 'fit_summary.csv', fit / 'run.log'
    record = dict(name=name, model=model, input=str(source.relative_to(ROOT)),
                  training_filter=sample, warm_source=str(warm) if warm else None,
                  test_filter='year==2022' if validate else None, steps=[])
    print(f'Start {name}; training_filter={sample}', flush=True)
    step = call_stata(script, args, temp, expected, log, timeout=timeout)
    record['steps'].append(step)
    if step['success']:
        with expected.open(encoding='utf-8') as stream:
            summary = next(csv.DictReader(stream))
        record['numeric_point_qualified'] = float(summary['converged' if native else 'stationary']) == 1
    if step['success'] and validate:
        script = '06_predict.do' if native else '07_comparator_predict.do'
        args = [source, fit, prediction]
        if not native:
            args.append(model)
        args += [8, 'year==2022']
        step = call_stata(script, args, temp, prediction / 'predictions.csv',
                          prediction / 'predict.log', timeout=timeout)
        record['steps'].append(step)
        if step['success']:
            step = call_stata('07_validation_metrics.do',
                [source, prediction / 'predictions.csv', metrics, model,
                 'coarse_temporal', sample, 8], temp, metrics / 'metrics.csv',
                 metrics / 'metrics.log', timeout=timeout)
            record['steps'].append(step)
    expected_steps = 3 if validate else 1
    record['execution_success'] = len(record['steps']) == expected_steps and all(
        x['success'] for x in record['steps'])
    (base / 'execution.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Finished {name}: execution={record['execution_success']}, "
          f"point_qualified={record.get('numeric_point_qualified')}", flush=True)
    return record


def collect():
    root = ROOT / 'outputs/followup_20261013'
    records, fitrows, metricrows, familyrows = [], [], [], []
    for path in sorted(root.glob('*/execution.json')):
        record = json.loads(path.read_text(encoding='utf-8'))
        records.append(record)
        if not record['execution_success']:
            continue
        native = record['model'] in ('maidads', 'aidads')
        file = path.parent / 'fit' / ('model_summary.csv' if native else 'fit_summary.csv')
        with file.open(encoding='utf-8') as stream:
            row = next(csv.DictReader(stream))
        fitrows.append(dict(name=record['name'], model=record['model'],
            sample=record['training_filter'], N=row['N' if native else 'observations'],
            AIC=row['AIC' if native else 'qml_aic'], BIC=row['BIC' if native else 'qml_bic'],
            numeric_point_qualified=record['numeric_point_qualified'],
            score=row['projected_gradient' if native else 'max_score']))
        file = path.parent / 'metrics/metrics.csv'
        if file.exists() and record['test_filter']:
            with file.open(encoding='utf-8') as stream:
                metricrows.extend(dict(name=record['name'], **r) for r in csv.DictReader(stream))
        if record['name'].startswith('family_'):
            file = path.parent / 'fit/representative_budget_elasticities.csv'
            with file.open(encoding='utf-8') as stream:
                familyrows.extend(dict(type=record['name'].split('_')[1],
                    numeric_point_qualified=record['numeric_point_qualified'], **r)
                    for r in csv.DictReader(stream))
    (root / 'execution_ledger.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    for name, rows in [('fit_comparison', fitrows), ('temporal_metrics', metricrows),
                       ('family_representative_elasticities', familyrows)]:
        if rows:
            fields = list(dict.fromkeys(k for row in rows for k in row))
            with (root / f'{name}.csv').open('w', encoding='utf-8', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--jobs', nargs='+', default=['temporal_maidads',
        'temporal_aidads', 'temporal_aids', 'temporal_quaids', 'family_1', 'family_2', 'family_4'])
    parser.add_argument('--starts', type=int, default=2)
    parser.add_argument('--iterate', type=int, default=500)
    parser.add_argument('--timeout', type=int, default=1800)
    parser.add_argument('--collect-only', action='store_true')
    args = parser.parse_args()
    source = ROOT / 'data/cells_quarter_8_coarse.csv'
    if not args.collect_only:
        for name in args.jobs:
            if name.startswith('temporal_'):
                model = name.removeprefix('temporal_')
                if model not in ('maidads', 'aidads', 'aids', 'quaids'):
                    parser.error(f'Unknown job {name}')
                run_one(name, model, source, 'year<=2021', validate=True,
                        starts=args.starts, iterate=args.iterate, timeout=args.timeout)
            elif name in ('family_1', 'family_2', 'family_3', 'family_4'):
                run_one(name, 'maidads', source, f'type=={name[-1]}',
                        warm=ROOT / 'outputs/estimation/maidads_8_coarse_simplex_multistart',
                        starts=args.starts, iterate=args.iterate, timeout=args.timeout)
            else:
                parser.error(f'Unknown job {name}')
            collect()
    records = collect()
    if not all(r['execution_success'] for r in records):
        raise SystemExit('Some jobs failed or timed out; failures remain in the ledger.')


if __name__ == '__main__':
    main()
