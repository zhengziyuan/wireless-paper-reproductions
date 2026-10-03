"""Preserve exact old executed checkpoints without certifying wrong geometry."""
import hashlib
import json
from pathlib import Path
from run_support import save_receipt

if __name__=='__main__':
    base=Path(__file__).parent;folder=base/'outputs'/'instantaneous-cdf20-full1000-final'
    receipts=[];hashes=None
    for path in sorted(folder.rglob('sample-*.json')):
        d=json.loads(path.read_text());c=d['contract'];sample=d['sample']
        if hashes is None:hashes=c['executed_source_hashes']
        if hashes!=c['executed_source_hashes']:raise RuntimeError('Old checkpoints mix executed numerical source versions')
        receipts.append({'checkpoint':path.relative_to(base).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                         'sample_index':sample['index'],'status':sample['status'],
                         'actual_model_gates':{k:sample[k] for k in ('physical_constraint_pass','convergence_pass','solver_primal_pass','qt_sdr_bound_pass')},
                         'checkpoint_contract_sha256':c['sha256'],'rng_state_preserved_in_checkpoint':True})
    if not receipts:raise RuntimeError('No actual checkpoint to preserve')
    result={'scope':'preserved_interrupted_old_geometry_actual_samples_NOT_full_figure_bank',
            'reason':'Confirmed implementation geometry error: radius15 cluster has pair distances above original10..20m; distinct radius10 runner replaces it. No files deleted.',
            'executed_sample_count':len(receipts),'required_original_MC_count':1000,
            'executed_source_hashes':hashes,'old_executed_sources_current_match':all(hashlib.sha256((base/n).read_bytes()).hexdigest()==v for n,v in hashes.items()),
            'checkpoints':receipts,'original_source_geometry_pass':False,'full_MC_figure_bank_pass':False,
            'full_reproduction_pass':False,'survivor_averaging_performed':False}
    save_receipt(folder/'interrupted-geometry-manifest.json',result)
    print(json.dumps({'executed_sample_count':len(receipts),'original_source_geometry_pass':False,'old_executed_sources_current_match':result['old_executed_sources_current_match']}))
