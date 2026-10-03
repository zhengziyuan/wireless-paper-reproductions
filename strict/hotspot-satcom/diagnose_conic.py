"""Repeat the unchanged failed QT subproblem using numerical backend controls.

No channel, power/QoS, auxiliary, objective, or algorithm threshold is tuned.
The input is an independently generated failing fixture, not author curve data.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from scipy.io import loadmat
from core import active_qt_update


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--fixture',type=Path,default=Path(__file__).with_name('outputs')/'full-case-failing-subproblem.mat')
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('outputs')/'conic-diagnosis.json')
    args=parser.parse_args(); f=loadmat(args.fixture,squeeze_me=True)
    base={'tol_gap_abs':1e-9,'tol_gap_rel':1e-9,'tol_feas':1e-9,'max_iter':500,'max_threads':1}
    controls=[('current',{}),('smaller_static_regularizer',{'static_regularization_constant':1e-12}),
              ('smaller_static_and_dynamic',{'static_regularization_constant':1e-12,'dynamic_regularization_delta':1e-10}),
              ('no_static',{'static_regularization_enable':False}),
              ('kkt_qdldl',{'direct_solve_method':'qdldl','static_regularization_constant':1e-12}),
              ('tighter_refinement',{'static_regularization_constant':1e-12,'iterative_refinement_max_iter':50,
                                    'iterative_refinement_reltol':1e-15,'iterative_refinement_abstol':1e-15}),
              ('longer_equilibration',{'equilibrate_max_iter':50,'static_regularization_constant':1e-12})]
    rows=[]
    for label,changes in controls:
        options=dict(base,**changes); start=time.perf_counter()
        try:
            W,info,_=active_qt_update(f['hu'],f['nhu'],f['W0'],float(f['noise']),float(f['power']),
                                     f['target'],solver_options=options,a=f['a'])
            e=info['after']; d=info['solver_diagnostics']
            physical=max(0,e['total_power']/float(f['power'])-1,float(np.max(f['target']-e['sinr'][f['hu'].shape[0]:])))
            row={'label':label,'options':options,'executed':True,'physical_violation':physical,'info':info,
                 'independent_numerical_pass':bool(physical<1e-5 and d['constraint_max_relative_violation']<1e-5 and info['qt_bound_max_violation']<1e-5)}
        except Exception as error:
            row={'label':label,'options':options,'executed':False,'error':str(error)}
        row['seconds']=time.perf_counter()-start;rows.append(row)
        print(json.dumps({'label':label,'executed':row['executed'],'seconds':row['seconds'],
                          'numerical_pass':row.get('independent_numerical_pass',False)}),flush=True)
    out={'scope':'unchanged_full_dimension_failing_QT_numerical_control_diagnosis',
         'fixture_sha256':hashlib.sha256(args.fixture.read_bytes()).hexdigest(),'model_or_constraint_changes':False,
         'objective_or_stop_tolerance_changes':False,'rows':rows}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item())+'\n')


if __name__=='__main__':main()
