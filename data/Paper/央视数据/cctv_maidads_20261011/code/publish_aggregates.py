"""Copy an explicit privacy-safe deliverable into an isolated Git worktree."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[1]
RESULT_NAMES={
    'model_summary.csv','fit_summary.csv','parameters.csv','scale.csv',
    'raw_parameters.csv','candidates.csv','audit.csv',
    'representative_budget_elasticities.csv','representative_elasticities.csv',
    'representative_price_elasticities.csv','elasticity_distribution.csv',
    'marshallian_matrix.csv','hicksian_matrix.csv',
    'fold_metrics.csv','execution.json','coverage.csv',
    'KERNEL_VERSION.txt','metrics.csv','representative_inputs.csv',
}
PRIVATE_NAMES={
    'smd_actual_support.csv','cell_scenarios.csv',
    'category_external_prices_all_sources.csv','category_external_prices_observed.csv',
    'group_price_month_8.csv','group_price_month_9.csv',
}


def approved(path):
    rel=path.relative_to(ROOT)
    if path.name in PRIVATE_NAMES: return False
    if rel.parts[0] in ('code','ado','docs'):
        return path.suffix in ('.py','.do','.ado','.mata','.md','.sthlp','.sh')
    if rel.parts[0]=='figures': return path.suffix=='.png'
    if len(rel.parts)==1: return path.name=='README.md'
    if rel.parts[0]!='outputs': return False
    if path.name=='RUN_STATUS.md': return True
    if len(rel.parts)==2:
        return path.suffix in ('.md','.txt','.json','.csv')
    if rel.parts[1] in ('data_audit','income','scenarios','corner','corner_scenarios'):
        return len(rel.parts)==3 and path.suffix in ('.csv','.json')
    return path.name in RESULT_NAMES


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('worktree',type=Path)
    parser.add_argument('--reuse-scope',action='store_true',
                        help='Update only files from the previous public manifest while new experiments run.')
    args=parser.parse_args()
    target=args.worktree/'data/Paper/央视数据'/ROOT.name
    target.mkdir(parents=True,exist_ok=True)
    scope=None
    if args.reuse_scope:
        scope=set(json.loads((target/'PUBLIC_MANIFEST.json').read_text(encoding='utf-8')))
    manifest={}
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file() or not approved(path): continue
        rel=path.relative_to(ROOT)
        if scope is not None and str(rel) not in scope: continue
        dest=target/rel
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,dest)
        manifest[str(rel)]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                            'bytes':path.stat().st_size}
    code_manifest={name:details['sha256'] for name,details in manifest.items()
                   if Path(name).parts[0] in ('code','ado','docs')}
    cm=target/'outputs/code_manifest.json'
    cm.write_text(json.dumps(code_manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    manifest['outputs/code_manifest.json']={'sha256':hashlib.sha256(cm.read_bytes()).hexdigest(),
                                           'bytes':cm.stat().st_size}
    (target/'PUBLIC_MANIFEST.json').write_text(
        json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Copied {len(manifest)} approved files to {target}. No commit or push performed.')


if __name__=='__main__': main()
