"""Capture and replay a full-size M30 original RGD failure without source edits."""
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from scipy.io import savemat
import algorithms
from scenario import make_scenario
from spectral_rmo import rmo_ascent
from qt_numerical_guard import install
from receipts import save


def capture(phi,fg,*args,**kwargs):
    try:return rmo_ascent(phi,fg,*args,**kwargs)
    except RuntimeError as error:
        frame=error.__traceback__
        while frame and Path(frame.tb_frame.f_code.co_filename).name!='spectral_rmo.py':frame=frame.tb_next
        if frame is None:raise
        local=frame.tb_frame.f_locals;old=np.asarray(local['phi']).copy();g=np.asarray(local['g']).copy()
        closure=dict(zip(fg.__code__.co_freevars,(c.cell_contents for c in fg.__closure__ or ())))
        snapshot={'phi':old,'g':g,'seed':local['seed'],'data':closure['data'],'p0':closure['p0'],
                  'smoothing':float(closure['mu']),'limit':closure['interference_limit'],'tts':float(closure['tts'])}
        path=Path(__file__).with_name('outputs')/'M30-RGD-Armijo-failure-fixture.mat';savemat(path,snapshot)
        increment=kwargs['increment'];alpha=float(local['seed']);slope=float(np.sum(abs(g)**2));theta=np.real(np.conj(1j*old)*g)
        trials=[]
        for search in range(60):
            new=old+alpha*g;new/=abs(new);value,newg=fg(new);difference=float(increment(old,new))
            angle_new=old*np.exp(1j*np.arctan(alpha*theta));angle_difference=float(increment(old,angle_new))
            trials.append({'search':search,'step':alpha,'exact_original_increment':difference,
                'required_original_Armijo_increase':1e-4*alpha*slope,'coordinate_equivalent_retraction_increment':angle_difference,
                'phase_displacement_norm':float(np.linalg.norm(new-old)),
                'gradient_first_order_prediction':float(2*np.sum(np.real(np.conj(g)*(new-old)))/2),
                'candidate_unit_error':float(np.max(abs(abs(new)-1))),
                'raw_objective_difference':float(value-local['value'])})
            alpha/=2
        # Read-only diagnostic of unreported seed reset, same g and retraction.
        resets=[]
        for label,seed in [('unit_tangent_displacement',1/np.linalg.norm(g)),('ten',10.),('one',1.),('point01',.01)]:
            alpha=seed
            for search in range(60):
                new=old+alpha*g;new/=abs(new);delta=float(increment(old,new))
                if delta>=1e-4*alpha*slope:break
                alpha/=2
            resets.append({'seed_name':label,'initial_step':float(seed),'searches':search+1,'accepted':search<59,
                           'accepted_step':float(alpha),'increment':delta,'required_increase':1e-4*alpha*slope})
        error.audit={'same_original_search_replayed':trials,'same_original_direction_retraction_seed_reset_diagnosis':resets,
            'fixture_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'original_phase_radius_error':float(np.max(abs(abs(old)-1))),
            'radial_gradient_residual':float(np.max(abs(np.real(np.conj(old)*g))))}
        raise


if __name__=='__main__':
    base=Path(__file__).parent;names=('diagnose_rgd_search.py','qt_numerical_guard.py','spectral_rmo.py','algorithms.py','models.py','increments.py','core.py','scenario.py','spectral_config.json')
    hashes={n:hashlib.sha256((base/n).read_bytes()).hexdigest() for n in names}
    c=json.loads((base/'spectral_config.json').read_text());c['reported'].update(M=30,kappa_leo_db=20);data,pl,il=make_scenario(c)
    algorithms.rmo_ascent=capture;install();clock=time.perf_counter()
    try:
        schemes=algorithms.run_all_schemes(data,c['tuned_not_reported'],pl,il);result={'unexpected_complete_pass':True,'schemes':schemes}
    except RuntimeError as error:
        result={'unexpected_complete_pass':False,'error':str(error),'failure_receipt':getattr(error,'receipt',None),'audit':getattr(error,'audit',None)}
    result.update(scope='same_full_scene_original_RGD_Armijo_failure_snapshot_and_numerical_replay_NOT_figures',configuration=c,
        elapsed_seconds=time.perf_counter()-clock,executed_source_hashes=hashes,
        source_unchanged_during_run=hashes=={n:hashlib.sha256((base/n).read_bytes()).hexdigest() for n in names},full_reproduction_pass=False)
    save(base/'outputs'/'M30-RGD-Armijo-diagnosis.json',result)
    print(json.dumps({'unexpected_complete_pass':result['unexpected_complete_pass'],'elapsed_seconds':result['elapsed_seconds'],
        'source_unchanged_during_run':result['source_unchanged_during_run'],'diagnostic_audit_saved':result.get('audit') is not None}),flush=True)
