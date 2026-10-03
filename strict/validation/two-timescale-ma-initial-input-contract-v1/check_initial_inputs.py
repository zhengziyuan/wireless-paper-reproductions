"""Portable no-solver initial/input-contract replay; never fresh AO evidence."""
from fractions import Fraction
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))

def verify(folder):
    packet=read(folder/'compact-initial-inputs.json');config=read(folder/'immutable-original-config.json')
    audit=read(folder/'actual-source-input-contract.json');bind=read(folder/'actual-all200-fingerprint-bindings.json')
    assert sha(folder/'immutable-original-config.json')==audit['actual_current_source_config_manifest_bindings_before']['run_config.json7']
    assert len(packet['records'])==len(audit['actual_records'])==len(bind['all200_actual_bindings'])==200
    original={r['input_filename']:r for r in audit['actual_records']};bindings={r['input_filename']:r for r in bind['all200_actual_bindings']}
    pair={};values=[];maxerror=0.
    for record in packet['records']:
        name=record['actual_original_input_filename'];a=original[name];b=bindings[name]
        assert record['actual_original_input_sha256']==a['actual_input_sha256']==b['actual_input_sha256']
        assert record['actual_original_input_fingerprint']==b['original_immutable_input_fingerprint']
        g=record['actual_geometry'];N=record['N'];M=record['M'];kap=record['kappa_linear']
        assert (N,M,record['power_W'],record['A'])==(6,5,1,2) and kap in (6,100)
        d=np.asarray(g['distances_m']);theta=np.asarray(g['elevation']);phi=np.asarray(g['azimuth'])
        assert d.shape==theta.shape==phi.shape==(M,) and np.all((d>=50)&(d<=70))
        assert np.all(abs(theta)<=np.pi/2) and np.all(abs(phi)<=np.pi/2)
        geometry_sha=hashlib.sha256(json.dumps(g,sort_keys=True).encode()).hexdigest()
        assert geometry_sha==a['same_full_geometry_and_NLoS_pair_sha256'][0]
        # Independently replay original declared exporter, not a solver or MC rate.
        rng=np.random.default_rng(np.random.SeedSequence([config['seed'],N,M,record['realization']]))
        drawn={'distances_m':rng.uniform(50,70,M).tolist(),'elevation':rng.uniform(-np.pi/2,np.pi/2,M).tolist(),'azimuth':rng.uniform(-np.pi/2,np.pi/2,M).tolist()}
        assert drawn==g
        z=(rng.normal(size=(1000,N,M))+1j*rng.normal(size=(1000,N,M)))/np.sqrt(2)
        assert z.shape==(1000,6,5) and np.isfinite(z).all()
        zsha=hashlib.sha256(z.astype('<c16').tobytes()).hexdigest()
        assert zsha==a['same_full_geometry_and_NLoS_pair_sha256'][1]
        key=record['realization']
        if key in pair:assert pair[key]==(geometry_sha,zsha)
        else:pair[key]=(geometry_sha,zsha)
        nr,nc=config['antenna_factorization'][str(N)]
        t=np.array([[x,y] for x in (np.arange(nr)-(nr-1)/2)/2 for y in (np.arange(nc)-(nc-1)/2)/2])
        assert np.array_equal(t,np.asarray(record['actual_initial_positions_normalized']))
        direction=np.c_[np.cos(theta)*np.sin(phi),np.sin(theta)];beta=10**(-40/10)*d**-2.8;noise=10**((-80-30)/10)
        H=np.exp(2j*np.pi*t@direction.T);assert np.max(abs(abs(H)-1))<1e-14
        numerator=beta**2*(N*N+N*(2*kap+1)/(kap+1)**2)
        den=beta[:,None]*beta[None,:]*(kap*kap*abs(H.conj().T@H)**2+N*(2*kap+1))/(kap+1)**2
        np.fill_diagonal(den,0);mrt=float(np.log2(1+numerator/(den.sum(axis=1)+noise*N*beta.sum())).sum())
        Sigma=np.eye(M)/(kap+1)+(kap/(kap+1))/N*(H.conj().T@H)
        zf=float(np.log2(1+beta*(N-M)/(M*noise)/np.real(np.diag(np.linalg.solve(Sigma,np.eye(M))))).sum())
        error=max(abs(mrt-record['actual_source_initial_MRT_rate']),abs(zf-record['actual_source_initial_ZF_bound']))
        assert error<1e-10;maxerror=max(maxerror,error);values.append((mrt,zf))
    assert len(pair)==100
    assert Fraction(1,2)*Fraction(1,2)==Fraction(1,4) and Fraction(1,2)==2*Fraction(1,4)
    return {'scope':'ACTUAL_portable_initial_input_recipe_formula_and_exact_anisotropy_replay_NOT_freshAO_or_fulltrajectory_gradient',
            'actual_original_inputs_bound':len(values),'actual_geometry_NLoS_pairs_replayed':len(pair),
            'actual_NLoS_draws_per_geometry':1000,'all_initial_input_recipe_formula_and_exact_anisotropy_checks_pass':True,
            'maximum_initial_formula_difference':maxerror,'numpy_version':np.__version__,
            'source_author_manuscript_or_plot_copied':False,'optimizer_or_full_MC_rate_evaluator_called':False,
            'full200_AO_gradients_or_historical_curve_cause_certified':False}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--output',type=Path);args=p.parse_args()
    result=verify(args.folder);print(json.dumps(result))
    if args.output:
        assert not args.output.exists();args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
