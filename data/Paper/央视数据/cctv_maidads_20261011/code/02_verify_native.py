#!/usr/bin/env python3
"""Independent cross-check only; estimation remains in Stata/Mata."""
import json
import runpy
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path('/root/data/Paper/央视数据/cctv_maidads_20261011')
SOURCE = Path('/root/data/Paper/省级食物消费/paper-AE/submission_0921/replication/code/estimate_demand.py')
native = runpy.run_path(str(SOURCE))
params = {
    'alpha': np.array([.25, .15, .1, .1, .15, .1, .15]),
    'beta': np.array([.1, .15, .2, .15, .1, .2, .1]),
    'delta': np.array([1, 2, 1, .5, 1, .7, 2]),
    'tau': np.array([2, 1, 2, 1, 3, 1.5, 1]),
    'omega': .6, 'kappa': 3,
}
rows = pd.read_csv(ROOT / 'outputs/estimation/native_verification.csv')
prices = pd.read_csv(ROOT / 'outputs/estimation/native_verification_prices.csv')
p = rows.pivot(index='scenario', columns='good', values='price').to_numpy()
m = rows.groupby('scenario').budget.first().to_numpy()
reference = native['analytical_responses'](params, p, m)
checks = {}
for column, key in [('q', 'x'), ('eta', 'eta'), ('utility', 'u')]:
    actual = rows.pivot(index='scenario', columns='good', values=column).to_numpy()
    target = reference[key]
    if target.ndim == 1:
        target = np.repeat(target[:, None], 7, axis=1)
    checks[column] = float(np.max(np.abs(actual - target)))
for key in ['marshallian', 'hicksian']:
    actual = prices[key].to_numpy().reshape(5, 7, 7)
    checks[key] = float(np.max(np.abs(actual - reference[key])))
checks['all_pass_tolerance_1e-8'] = all(v < 1e-8 for v in checks.values())
print(json.dumps(checks, indent=2))
(ROOT / 'outputs/estimation/native_verification.json').write_text(json.dumps(checks, indent=2) + '\n')
if not checks['all_pass_tolerance_1e-8']:
    raise SystemExit('Native-function verification failed')
