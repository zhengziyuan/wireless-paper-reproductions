"""Independent full-rank moment/QT/gradient evidence and shared MATLAB fixture."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.io import savemat
from statistical import (moments,evaluate,auxiliaries,qt_bounds,normalized_projector,
                         expected_projector_square,pair_moment,criterion_value_gradient,
                         rate_value_gradient)


def make_fixture():
    rng=np.random.default_rng(202610031);U,N,K,M=6,16,10,25
    cn=lambda shape:(rng.standard_normal(shape)+1j*rng.standard_normal(shape))/np.sqrt(2)
    inputs={'direct_mean':0.2*cn((U,N)),'direct_variance':0.01*(0.5+rng.random((U,N))),
            'matrix_mean':0.025*cn((M,N)),'matrix_variance':0.0005*(0.5+rng.random((M,N))),
            'ground_mean':0.3*cn((U,M)),'ground_variance':0.03*(0.5+rng.random((U,M))),
            'nhu_mean':0.25*cn((K,N)),'nhu_variance':0.015*(0.5+rng.random((K,N)))}
    return inputs,np.exp(1j*rng.uniform(-np.pi,np.pi,M)),0.1*cn((N,U+K))


def verify(count=20000):
    inputs,phi,W=make_fixture();Q,Psi,means,C=moments(inputs,phi);D,z,_=auxiliaries(Q,Psi,W,0.1)
    e=evaluate(Q,Psi,W,0.1);tight=float(np.max(abs(qt_bounds(D,z,W,0.1)-e['sinr'])))
    rng=np.random.default_rng(202610032);worst=0.0
    for _ in range(128):
        trial=0.2*(rng.standard_normal(W.shape)+1j*rng.standard_normal(W.shape))/np.sqrt(2)
        worst=max(worst,float(np.max(qt_bounds(D,z,trial,0.1)-evaluate(Q,Psi,trial,0.1)['sinr'])))
    P=expected_projector_square(inputs);f,g=criterion_value_gradient(inputs,phi,P);rate,rg=rate_value_gradient(inputs,phi,W,0.1)
    gradient_errors=[];rate_errors=[];delta=1e-5
    for m in range(len(phi)):
        plus,minus=phi.copy(),phi.copy();plus[m]*=np.exp(1j*delta);minus[m]*=np.exp(-1j*delta)
        numeric=(criterion_value_gradient(inputs,plus,P)[0]-criterion_value_gradient(inputs,minus,P)[0])/(2*delta)
        gradient_errors.append(abs(numeric-np.real(np.conj(1j*phi[m])*g[m])))
        numeric=(rate_value_gradient(inputs,plus,W,0.1)[0]-rate_value_gradient(inputs,minus,W,0.1)[0])/(2*delta)
        rate_errors.append(abs(numeric-np.real(np.conj(1j*phi[m])*rg[m])))
    # Paired HUs share every G draw, as the original physical model requires.
    cn=lambda shape:(rng.standard_normal(shape)+1j*rng.standard_normal(shape))/np.sqrt(2)
    sumQ=np.zeros_like(Q);pairs=[];projectors=[]
    for start in range(0,count,250):
        size=min(250,count-start)
        G=inputs['matrix_mean'][None,:,:]+np.sqrt(inputs['matrix_variance'])[None,:,:]*cn((size,25,16))
        r=inputs['ground_mean'][None,:,:]+np.sqrt(inputs['ground_variance'])[None,:,:]*cn((size,6,25))
        d=inputs['direct_mean'][None,:,:]+np.sqrt(inputs['direct_variance'])[None,:,:]*cn((size,6,16))
        h=d+np.einsum('m,sum,smn->sun',phi,r,G)
        sumQ+=np.einsum('sun,sum->unm',np.conj(h),h)
        pairs.extend(abs(np.einsum('sn,sn->s',np.conj(h[:,0]),h[:,1]))**2)
        nh=inputs['nhu_mean'][0]+np.sqrt(inputs['nhu_variance'][0])*cn((size,16));nh=np.conj(nh)
        projectors.extend(np.einsum('sn,sm->snm',nh,np.conj(nh))/np.sum(abs(nh)**2,axis=1)[:,None,None])
    empirical=sumQ/count;exactpair=pair_moment(inputs,phi,0,1);pair_array=np.asarray(pairs)
    pair_error=abs(np.mean(pair_array)-exactpair);pair_se=np.std(pair_array,ddof=1)/np.sqrt(count)
    np0=normalized_projector(np.conj(inputs['nhu_mean'][0]),inputs['nhu_variance'][0]);empiricalP=np.mean(projectors,axis=0)
    checks={'full_rank_covariances_pass':bool(min(np.linalg.eigvalsh(q).min() for q in Psi)>0),
            'vector_qt_tightness_pass':tight<1e-12,'vector_qt_tightness_error':tight,
            'vector_qt_global_lower_bound_pass':worst<1e-12,'worst_bound_excess':worst,
            'statistical_criterion_gradient_pass':max(gradient_errors)<1e-7,'criterion_gradient_error':max(gradient_errors),
            'statistical_rate_gradient_pass':max(rate_errors)<1e-7,'rate_gradient_error':max(rate_errors),
            'normalized_projector_trace_pass':abs(np.trace(np0).real-1)<1e-10,
            'normalized_projector_MC_pass':np.linalg.norm(np0-empiricalP)<0.02,
            'normalized_projector_MC_frobenius_error':float(np.linalg.norm(np0-empiricalP)),
            'exact_shared_G_pair_fourth_moment_MC_pass':pair_error<6*pair_se,
            'pair_fourth_moment_error':float(pair_error),'pair_MC_standard_error':float(pair_se),
            'channel_second_moment_MC_pass':np.linalg.norm(empirical-Q)/np.linalg.norm(Q)<0.03,
            'channel_second_moment_MC_relative_error':float(np.linalg.norm(empirical-Q)/np.linalg.norm(Q))}
    fixture={'inputs':inputs,'phi':phi,'W':W,'noise':0.1,'Q':Q,'Psi':Psi,'projector_square':P,
             'projector0':np0,'qt_bounds':qt_bounds(D,z,W,0.1),'criterion':f,'criterion_gradient':g,
             'rate':rate,'rate_gradient':rg,'pair_moment01':exactpair}
    return {'scope':'independent_full_dimension_statistical_model_and_corrected_QT_erratum_component_evidence_NOT_full_paper_reproduction',
            'dimensions':{'N':16,'U':6,'K':10,'M':25},'independent_MC_samples':count,'checks':checks,
            'full_reproduction_pass':False},fixture


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path(__file__).with_name('outputs')/'statistical-component-python.json')
    parser.add_argument('--fixture',type=Path,default=Path(__file__).with_name('outputs')/'statistical-component-fixture.mat');args=parser.parse_args()
    result,fixture=verify();args.fixture.parent.mkdir(parents=True,exist_ok=True);savemat(args.fixture,fixture)
    result['fixture_sha256']=hashlib.sha256(args.fixture.read_bytes()).hexdigest()
    result['executed_source_sha256']=hashlib.sha256(Path(__file__).with_name('statistical.py').read_bytes()).hexdigest()
    serial=json.dumps(result,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else x.tolist())
    args.output.write_text(serial+'\n');print(serial)
    if not all(v for k,v in result['checks'].items() if k.endswith('_pass')):raise SystemExit(1)
