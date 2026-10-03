"""Independent high-precision LSE increment checks, never original plot data."""
from decimal import Decimal, localcontext
import argparse
import json
from pathlib import Path
import unittest
import numpy as np
from engine import Model, retract, serialize

HERE=Path(__file__).resolve().parent

def unpack(value):
    return {key:np.asarray(item['real'])+1j*np.asarray(item['imag'])
            if isinstance(item,dict) else np.asarray(item) for key,item in value.items()}

def decimal_objective(model,z,mu):
    """Direct 75-digit physical fields, squares, schedule and LSE, not Δ formula."""
    D=Decimal.from_float
    bar,_,_,_=model.fields(z)
    values=[]
    for k in range(model.K):
        g=Decimal(0)
        for u in range(model.U):
            real=Decimal(0);imag=Decimal(0)
            for m in range(model.M):
                pr,pi=D(float(z['phi'][m].real)),D(float(z['phi'][m].imag))
                tr,ti=D(float(bar[u,m].real)),D(float(bar[u,m].imag))
                vr,vi=pr*tr-pi*ti,pr*ti+pi*tr
                cr,ci=D(float(model.c[k,m].real)),D(float(model.c[k,m].imag))
                real+=cr*vr-ci*vi;imag+=cr*vi+ci*vr
            g+=D(float(z['X'][k,u]))*D(float(model.config['reference_snr']))*(real*real+imag*imag)
        values.append(g)
    dm=D(float(mu))
    mn=min(values)
    return -mn+dm*sum((-(value-mn)/dm).exp() for value in values).ln()

def cases():
    rng=np.random.default_rng(62801)
    configurations=[([2,1],[1,1],4),([2,2],[1,1],4),([10,10],[6,6],32)]
    result=[]
    for shape,movable,K in configurations:
        cfg=dict(ms1=shape,ms2=movable,azimuth_deg=np.linspace(-60,60,K).tolist(),
                 elevation_deg=[45.]*K,number_of_targets=K,reference_snr=.01,
                 incidence_direction_cosines=[0,0],spacing_over_wavelength=.5)
        model=Model(cfg)
        X=rng.uniform(.1,1,(K,model.U));X/=np.sum(X,axis=1,keepdims=True)
        z={'phi':np.exp(1j*rng.uniform(-np.pi,np.pi,model.M)),
           'theta':np.exp(1j*rng.uniform(-np.pi,np.pi,model.N)),'X':X}
        for mu,step in ((1000.,1e-12),(.001,1e-10),(.001,.2)):
            direction={'phi':1j*z['phi']*rng.normal(size=model.M),
                       'theta':1j*z['theta']*rng.normal(size=model.N),
                       'X':rng.normal(size=X.shape)}
            direction['X']-=np.mean(direction['X'],axis=1,keepdims=True)
            trial=retract(z,direction,step)
            with localcontext() as context:
                context.prec=75
                truth=decimal_objective(model,trial,mu)-decimal_objective(model,z,mu)
            result.append({'name':f'{shape[0]}x{shape[1]}_K{K}_mu{mu}_step{step}',
                'model':cfg,'coefficients':{'real':model.c.real.tolist(),'imag':model.c.imag.tolist()},
                'base':serialize(z),'candidate':serialize(trial),'mu':mu,
                'decimal_reference':str(truth)})
    return result

def validate(items):
    receipts=[]
    for item in items:
        model=Model(item['model'])
        model.c=np.asarray(item['coefficients']['real'])+1j*np.asarray(item['coefficients']['imag'])
        z,trial=unpack(item['base']),unpack(item['candidate']);mu=item['mu']
        actual=model.communication_difference(z,trial,mu,'maximize_negative_softmin')
        truth=float(item['decimal_reference'])
        tolerance=max(5e-18,abs(truth)*3e-10)
        naive=model.communication_objective(trial,mu,'maximize_negative_softmin')[0]-model.communication_objective(z,mu,'maximize_negative_softmin')[0]
        if abs(actual-truth)>tolerance:
            raise AssertionError((item['name'],actual,truth,tolerance))
        reverse=model.communication_difference(z,trial,mu,'literal_paper_descent_of_f')
        if reverse!=-actual:raise AssertionError('Source convention sign not preserved')
        receipts.append({'name':item['name'],'stable_increment':actual,'naive_increment':naive,
                         'decimal_reference':truth,'absolute_error':abs(actual-truth),
                         'tolerance':tolerance,'pass':True})
    return {'scope':'independent_Decimal_algebra_tests_not_original_figures','cases':receipts,'pass':True}

class IncrementTests(unittest.TestCase):
    def test_decimal_cases(self):
        fixture=HERE/'tests'/'communication_increment_cases.json'
        self.assertTrue(validate(json.loads(fixture.read_text())['cases'])['pass'])

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--export',action='store_true');parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    fixture=HERE/'tests'/'communication_increment_cases.json'
    if args.export:
        fixture.parent.mkdir(parents=True,exist_ok=True)
        fixture.write_text(json.dumps({'scope':'our_independent_algebra_fixture_NOT_author_data','cases':cases()},indent=2)+'\n',encoding='utf-8')
    result=validate(json.loads(fixture.read_text())['cases'])
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
