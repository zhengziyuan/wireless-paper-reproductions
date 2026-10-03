"""Re-solve the SAME original AP/MR convex QT block under numeric controls.

All moments, incumbent powers/precoders, QT auxiliaries, constraints and
objective remain fixed. No gate, model or optimization framework is changed.
"""
import hashlib
from pathlib import Path
import numpy as np
from scipy.io import savemat
import core


def solve_guard(kind,inputs,solver='CLARABEL',solver_options=None):
    original=core.mr_qt_update if kind=='mr' else core.ap_qt_update;base=dict(solver_options or {});attempts=[]
    controls=[(solver,base)]
    if solver=='CLARABEL':
        controls.extend([('CLARABEL',dict(base,tol_gap_abs=1e-9,tol_gap_rel=1e-9,tol_feas=1e-9,max_iter=500,max_threads=1)),
                         ('CLARABEL',dict(base,tol_gap_abs=1e-10,tol_gap_rel=1e-10,tol_feas=1e-10,max_iter=500,max_threads=1,static_regularization_constant=1e-12)),
                         ('CLARABEL',dict(base,tol_gap_abs=1e-10,tol_gap_rel=1e-10,tol_feas=1e-10,max_iter=500,max_threads=1,static_regularization_enable=False)),
                         ('CLARABEL',dict(base,tol_gap_abs=1e-10,tol_gap_rel=1e-10,tol_feas=1e-10,max_iter=500,max_threads=1,equilibrate_max_iter=50,static_regularization_constant=1e-12)),
                         ('SCS',{'eps':1e-8,'max_iters':200000})])
    last=None;fixture=None
    for backend,options in controls:
        try:
            value,info=original(*inputs,backend,options);d=info['solver_diagnostics']
            before=float(np.min(info['before']['sinr']));after=float(np.min(info['after']['sinr']))
            accepted=bool(np.isfinite(after) and after>=before-1e-5 and d['constraint_max_relative_violation']<=1e-5 and info['qt_bound_max_violation']<=1e-5)
            attempts.append({'backend':backend,'options':options,'status':info['solver_status'],
                             'primal_relative_violation':d['constraint_max_relative_violation'],'qt_bound_violation':info['qt_bound_max_violation'],
                             'before_minimum_sinr':before,'after_minimum_sinr':after,'accepted':accepted})
            if accepted:
                d['same_original_QT_numerical_attempts']=attempts
                if fixture is not None:d['generated_failed_input_fixture']=fixture
                return value,info
            last=RuntimeError('Original primal, QT bound or monotonicity gate rejected the numeric solution')
        except (RuntimeError,ValueError,core.cp.error.SolverError) as error:
            last=error;attempts.append({'backend':backend,'options':options,'error':str(error),'accepted':False})
        if fixture is None:fixture=save_fixture(kind,inputs)
    error=RuntimeError('Same-input same-QT numerical controls exhausted: '+str(last))
    error.receipt={'block':kind+'_QT_same_problem','attempts':attempts,'generated_fixture':fixture}
    raise error


def save_fixture(kind,inputs):
    keys=('p0','signal','cross','power','leak','offset','power_limit','interference_limit') if kind=='mr' else ('W0','mean','covariance','gt_second','offset','power_limit','interference_limit')
    digest=hashlib.sha256();fixture={}
    for name,value in zip(keys,inputs):
        x=np.ascontiguousarray(value);digest.update(name.encode());digest.update(str(x.shape).encode());digest.update(x.dtype.str.encode());digest.update(x.tobytes());fixture[name]=value
    folder=Path(__file__).with_name('outputs');folder.mkdir(parents=True,exist_ok=True);path=folder/(kind+'-QT-numerical-input-'+digest.hexdigest()[:16]+'.mat');savemat(path,fixture)
    return {'filename':'outputs/'+path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'input_sha256':digest.hexdigest()}


def mr_qt_update(p0,signal,cross,power,leak,offset,power_limit,interference_limit,solver='CLARABEL',solver_options=None):
    return solve_guard('mr',(p0,signal,cross,power,leak,offset,power_limit,interference_limit),solver,solver_options)


def ap_qt_update(W0,mean,covariance,gt_second,offset,power_limit,interference_limit,solver='CLARABEL',solver_options=None):
    return solve_guard('ap',(W0,mean,covariance,gt_second,offset,power_limit,interference_limit),solver,solver_options)


def install():
    import algorithms
    algorithms.ap_qt_update=ap_qt_update;algorithms.mr_qt_update=mr_qt_update
