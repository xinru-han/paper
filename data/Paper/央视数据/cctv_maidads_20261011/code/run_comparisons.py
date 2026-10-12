"""Run additional sample/specification comparisons in Stata."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json
import argparse
from run_validation import ROOT, call_stata


def fit(sample, model, k):
    source = ROOT/'data'/f'cells_{sample}.csv'
    out = ROOT/'outputs/comparators'/f'{model}_{sample}'
    out.mkdir(parents=True, exist_ok=True)
    result = call_stata('04_comparators.do', [source,out,model,k,3],
                        ROOT/'tmp/comparisons'/f'{model}_{sample}',
                        out/'fit_summary.csv', out/'run.log')
    result.update(sample=sample, model=model, k=k)
    print(f"{sample} {model}: success={result['success']}",flush=True)
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--samples',nargs='+',default=['quarter_9','year_8','quarter_8_complete_stable'])
    args=parser.parse_args()
    results=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        tasks=[pool.submit(fit,s,m,9 if s=='quarter_9' else 8) for s in args.samples for m in ('aids','quaids')]
        for task in as_completed(tasks):
            results.append(task.result())
    ledger='additional_execution.json' if args.samples==['quarter_9','year_8','quarter_8_complete_stable'] else 'measurement_sensitivity_execution.json'
    (ROOT/'outputs/comparators'/ledger).write_text(
        json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    if not all(r['success'] for r in results):
        raise SystemExit('At least one Stata comparison failed; see ledger.')
