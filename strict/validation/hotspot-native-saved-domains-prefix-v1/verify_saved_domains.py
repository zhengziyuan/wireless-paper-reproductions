"""No-solver replay of the actual saved JSON-derived domain array bank only."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def verify(folder):
    receipt=json.loads((folder/'domain-only-actual.json').read_text(encoding='utf-8'))
    path=folder/'saved-initial-final-domain-arrays.npz'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==receipt['actual_state_arrays_sha256']
    arrays=np.load(path,allow_pickle=False);count=0;states=0;keys=set()
    for case in receipt['actual_case_records']:
        for start in case['actual_domain_records']:
            count+=1
            for state in start['actual_states'].values():
                W=arrays[state['saved_array_W']];phi=arrays[state['saved_array_phi']]
                keys.update((state['saved_array_W'],state['saved_array_phi']))
                assert W.shape==tuple(state['encoded_W_shape'])==(16,16)
                assert phi.shape==(state['encoded_phi_vector_length'],)==(25,)
                assert np.all(np.isfinite(W)) and np.all(np.isfinite(phi))
                power=float(np.sum(abs(W)**2));err=float(np.max(abs(abs(phi)-1)))
                assert power<=state['original_power_limit']*(1+1e-5) and err<=1e-10
                assert abs(power-state['independent_total_power'])<=1e-10
                assert abs(err-state['unit_modulus_maximum_error'])<=1e-14
                states+=1
    assert count==receipt['actual_prefix_starts'] and keys==set(arrays.files)
    return {'scope':'portable_replay_ACTUAL_saved_domains_only_NOT_QoS_gradient_rng_or_full18',
            'actual_cases':len(receipt['actual_case_records']),'actual_starts':count,'actual_states':states,
            'all_saved_domain_replays_pass':True,'solver_or_optimizer_called':False,
            'original_native_RNG_or_QoS_or_full18_certified':False,'numpy_version':np.__version__}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--output',type=Path)
    a=p.parse_args();result=verify(a.folder);print(json.dumps(result))
    if a.output:
        assert not a.output.exists();a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
