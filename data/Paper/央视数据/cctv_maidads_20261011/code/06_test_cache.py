"""Check cached grid auditing against the completed uncached CCTV forecast."""
import hashlib
import json
import pandas as pd
from run_validation import ROOT,call_stata


def signature():
    cols=['prediction_valid','utility_roots_finite_grid','utility_equation_error']
    cols += [f'{stem}{j}' for stem in ('fitq','fitw','eta','own_m','own_h') for j in range(1,9)]
    df=pd.read_csv(ROOT/'outputs/scenarios/pooled/predictions.csv',usecols=cols)
    return {'rows':len(df),'valid_rows':int(df.prediction_valid.sum()),
            'sha256':hashlib.sha256(pd.util.hash_pandas_object(df,index=False).values.tobytes()).hexdigest()}


def main():
    before=signature()
    run=call_stata('06_scenarios.do',[ROOT/'outputs/estimation/maidads_8_warm'],
                   ROOT/'tmp/scenarios_cache',ROOT/'outputs/scenarios/province_income_growth.csv',
                   ROOT/'logs/06_scenarios.log',1800)
    after=signature() if run['success'] else None
    result={'before':before,'after':after,'exact_numeric_match':before==after,'execution':run}
    (ROOT/'outputs/scenarios/grid_cache_equivalence.json').write_text(
        json.dumps(result,indent=2),encoding='utf-8')
    print(result,flush=True)
    if not run['success'] or before!=after: raise SystemExit('Cached forecast does not match the completed reference.')


if __name__=='__main__': main()
