"""Training-only temporal check of natural-simplex MAIDADS and matched comparators."""
from pathlib import Path
import json
import pandas as pd

from run_validation import ROOT, call_stata


def main():
    source=ROOT/'data/cells_quarter_8_coarse.csv'
    if not source.exists():
        raise FileNotFoundError(source)
    base=ROOT/'outputs/validation_simplex'
    base.mkdir(exist_ok=True)
    ledger=[]
    for model in ('maidads','aids','quaids'):
        out=base/f'temporal_{model}'
        fit,pred,metrics=(out/x for x in ('fit','prediction','metrics'))
        for directory in (fit,pred,metrics): directory.mkdir(parents=True,exist_ok=True)
        temp=ROOT/'tmp/validation_simplex'/model
        record={'model':model,'training_filter':'year<=2021','test_filter':'year==2022',
                'source':str(source.relative_to(ROOT)),'steps':[]}
        if model=='maidads':
            # This warm point was itself fitted on 2020-2021, not the full-period point.
            warm=ROOT/'outputs/validation/temporal_maidads/fit'
            record['warm_source']=str(warm.relative_to(ROOT))
            step=call_stata('02_estimate_simplex.do',
                [source,fit,model,8,2,400,'year<=2021',warm],temp,
                fit/'model_summary.csv',fit/'estimate.log',900)
        else:
            step=call_stata('04_comparators.do',
                [source,fit,model,8,2,'year<=2021'],temp,
                fit/'fit_summary.csv',fit/'run.log',600)
        record['steps'].append(step)
        if step['success']:
            if model=='maidads':
                script='06_predict.do';args=[source,fit,pred,8,'year==2022']
            else:
                script='07_comparator_predict.do';args=[source,fit,pred,model,8,'year==2022']
            step=call_stata(script,args,temp,pred/'predictions.csv',pred/'predict.log',600)
            record['steps'].append(step)
        if step['success']:
            step=call_stata('07_validation_metrics.do',
                [source,pred/'predictions.csv',metrics,model,'temporal_coarse','year<=2021',8],
                temp,metrics/'metrics.csv',metrics/'metrics.log',600)
            record['steps'].append(step)
        record['execution_success']=len(record['steps'])==3 and all(x['success'] for x in record['steps'])
        ledger.append(record)
        (out/'execution.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
        (base/'execution_ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2),encoding='utf-8')
        print(f"{model}: execution_success={record['execution_success']}",flush=True)
    frames=[pd.read_csv(base/f"temporal_{r['model']}"/'metrics/metrics.csv')
            for r in ledger if r['execution_success']]
    if frames: pd.concat(frames,ignore_index=True).to_csv(base/'all_model_metrics.csv',index=False)
    if not all(r['execution_success'] for r in ledger):
        raise SystemExit('Incomplete execution retained in ledger; no fabricated or stale metrics included.')


if __name__=='__main__': main()
