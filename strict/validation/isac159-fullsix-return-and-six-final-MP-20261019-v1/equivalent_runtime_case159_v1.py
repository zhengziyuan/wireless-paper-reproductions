"""Isolated original algorithms: explicit I and positive-alpha factored Q/P only.

The two numerical providers have fixed-state evidence. This module does not
claim a full-trajectory success. The original loops, initializers, PR/BB modes,
acceptance checks, stopping rules and budgets remain in the frozen core.
"""
import types
from pathlib import Path
import numpy as np
from stable_metrics import evaluate as stable_evaluate
from structured_original_qcqp_candidate_v1 import solve_fixed_original_qcqp

HERE=Path(__file__).resolve().parent

def supported_structured_solve(w,fc,mu,eta,lip,ga,den,rho,power,bisection_tolerance):
    # Domain guards report unsupported inputs; they never repair or fallback.
    if not all(np.isfinite(value) and value>0 for value in (den,rho,power,bisection_tolerance)):
        raise ValueError('Unsupported structured QCQP: finite positive den/rho/power/tolerance required; no fallback.')
    solution,information=solve_fixed_original_qcqp(w,fc,mu,eta,lip,ga,den,rho,power,bisection_tolerance)
    if not all(np.isfinite(information[key]) for key in ('alpha','beta','nu')) or not np.all(np.isfinite(solution)):
        raise ValueError('Unsupported nonfinite structured QCQP output; no repair or fallback.')
    return solution,information

def load_core(observer=None):
    source=HERE/'sources/core_structured_case159_v1.py'
    model=types.ModuleType('isac_case159_explicit_I_factored_QP')
    model.__file__=str(source);model.__dict__['_structured_solve']=supported_structured_solve
    exec(compile(source.read_bytes(),str(source),'exec'),model.__dict__)
    model.evaluate_subtractive_control=model.evaluate
    def evaluate(w,theta,r,c,iota=None,gradients=False,_fixed_channel_bundle=None,_fixed_rotation_base=None):
        bundle=model.channels(theta,r,c,_fixed_rotation_base) if _fixed_channel_bundle is None else _fixed_channel_bundle
        if iota is None:
            field=bundle[0];k=len(c['noise']);z=field[:,k:].conj().T@w
            pattern=np.sum(abs(z)**2,axis=1);desired=np.asarray(c['desired_pattern']);overlap=float(desired@pattern)
            if overlap<=c['iota_denominator_epsilon']:raise ValueError('Exact iota* is undefined at this zero-overlap pattern; no fabricated sensing score is returned.')
            iota=float(pattern@pattern/overlap)
        return stable_evaluate(w,*bundle,c,iota,gradients)
    model.evaluate=evaluate
    if observer is not None:
        for name in ('update_w','update_theta','update_rotation','optimize'):
            setattr(model,name,observer.wrap(name,getattr(model,name)))
    return model
