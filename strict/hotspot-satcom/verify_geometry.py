"""Independent source-distance, model-permutation and dual-language fixture audit."""
import copy
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.io import savemat
from scenario_geometry import sample_scenario,cluster_positions
from scenario import sample_scenario as old_scenario
from statistical import moments,expected_projector_square,criterion_value_gradient,evaluate


def verify():
    base=Path(__file__).parent;config=json.loads((base/'statistical_geometry_config.json').read_text())
    rng=np.random.default_rng(2026100407);cn=lambda shape:(rng.standard_normal(shape)+1j*rng.standard_normal(shape))/np.sqrt(2)
    cases=[];records=[]
    for u in range(1,7):
        c=copy.deepcopy(config);c['reported'].update(U=u,K=16-u,kappa_ground_db=20,kappa_satellite_db=20)
        f=sample_scenario(c,np.random.default_rng(c['tuned_not_reported']['seed']));old=old_scenario(c,np.random.default_rng(c['tuned_not_reported']['seed']))
        pos=f['geometry']['hu_xy_m'];dist=np.linalg.norm(pos[:,None]-pos[None,:],axis=2)[np.triu_indices(u,1)]
        oldpos=old['geometry']['hu_xy_m'];olddist=np.linalg.norm(oldpos[:,None]-oldpos[None,:],axis=2)[np.triu_indices(u,1)]
        x=f['mean_inputs'];phi=f['phi0'];Q,Psi,mean,C=moments(x,phi);P=expected_projector_square(x)
        value,g=criterion_value_gradient(x,phi,P);W=.1*cn((16,16));e=evaluate(Q,Psi,W,1)
        perm=np.arange(u)[::-1];xp=copy.deepcopy(x)
        for k in ('direct_mean','direct_variance','ground_mean','ground_variance'):xp[k]=xp[k][perm]
        Qp,Psip,_,_=moments(xp,phi);vp,gp=criterion_value_gradient(xp,phi,P)
        ep=evaluate(Qp,Psip,W[:,np.r_[perm,np.arange(u,16)]],1)
        ground=x['ground_mean'];direct=x['direct_mean']
        normalize=lambda a:a/np.linalg.norm(a,axis=1)[:,None]
        directcorr=abs(normalize(direct)@normalize(direct).conj().T)
        groundcorr=abs(normalize(ground)@normalize(ground).conj().T)
        record={'U':u,'all_pair_distances_m':dist.tolist(),'minimum_pair_distance_m':None if u==1 else float(min(dist)),
                'maximum_pair_distance_m':None if u==1 else float(max(dist)),
                'old_radius15_pair_distances_m':olddist.tolist(),
                'source_distance_contract_pass':bool(u==1 or (min(dist)>=10-1e-12 and max(dist)<=20+1e-12)),
                'only_HU_geometry_changed_pass':bool(np.array_equal(f['nhu'],old['nhu']) and np.array_equal(f['phi0'],old['phi0']) and
                     np.array_equal(x['matrix_mean'],old['mean_inputs']['matrix_mean']) and np.array_equal(x['matrix_variance'],old['mean_inputs']['matrix_variance']) and
                     np.array_equal(x['ground_variance'],old['mean_inputs']['ground_variance'])),
                'HU_permutation_Q_error':float(np.max(abs(Qp-Q[perm]))),
                'HU_permutation_criterion_relative_error':float(abs(vp-value)/max(1,abs(value))),
                'HU_permutation_gradient_relative_error':float(np.linalg.norm(gp-g)/max(1,np.linalg.norm(g))),
                'HU_permutation_rate_error':float(abs(ep['hu_sum_rate']-e['hu_sum_rate'])),
                'direct_LoS_normalized_Gram_abs':directcorr.tolist(),'ground_LoS_normalized_Gram_abs':groundcorr.tolist(),
                'not_an_optimized_figure':True}
        record['permutation_contract_pass']=bool(record['HU_permutation_Q_error']<1e-12 and record['HU_permutation_criterion_relative_error']<1e-12 and record['HU_permutation_gradient_relative_error']<1e-12 and record['HU_permutation_rate_error']<1e-12)
        records.append(record);cases.append({'config':c,'geometry':f['geometry'],'mean_inputs':x})
    reject=False
    try:cluster_positions(6,15)
    except ValueError:reject=True
    checks={'all6_source_distance_contract_pass':all(r['source_distance_contract_pass'] for r in records),
            'all6_only_HU_geometry_changed_pass':all(r['only_HU_geometry_changed_pass'] for r in records),
            'all6_HU_index_permutation_pass':all(r['permutation_contract_pass'] for r in records),
            'invalid_old_radius15_rejected_pass':reject}
    def matlab_config(value):
        if isinstance(value,dict):return {k:matlab_config(v) for k,v in value.items()}
        if isinstance(value,list):return [matlab_config(v) for v in value]
        if isinstance(value,int) and not isinstance(value,bool):return float(value)
        return value
    for case in cases:case['config']=matlab_config(case['config'])
    return {'scope':'source_geometry_and_index_invariance_component_NOT_full_figures','checks':checks,
            'cases':records,'all_passed':all(checks.values()),'historical_author_coordinates_recovered':False,
            'full_reproduction_pass':False}, {'cases':np.asarray(cases,dtype=object)}


if __name__=='__main__':
    result,fixture=verify();base=Path(__file__).parent;folder=base/'outputs';folder.mkdir(exist_ok=True)
    path=folder/'source-geometry-fixture.mat';savemat(path,fixture,long_field_names=True)
    result['fixture_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    result['executed_source_hashes']={n:hashlib.sha256((base/n).read_bytes()).hexdigest() for n in
        ('scenario_geometry.py','scenario.py','statistical.py','verify_geometry.py','statistical_geometry_config.json')}
    (folder/'source-geometry-python.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'checks':result['checks'],'fixture_sha256':result['fixture_sha256'],'all_passed':result['all_passed']}))
    if not result['all_passed']:raise SystemExit(1)
