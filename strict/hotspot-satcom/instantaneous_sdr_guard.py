"""Same-SDP numerical retry after ALL original Gaussian candidates are checked.

The model, QT auxiliaries, incumbent and normal draws are never changed.
An inaccurate relaxation is not certified as an upper bound merely because
its status is 'optimal'. No gate or stopping tolerance is relaxed.
"""
import hashlib
from pathlib import Path
import numpy as np
from scipy.io import savemat
import core

_original=core.phase_sdr_update


def phase_sdr_guard(direct,cascade,phi0,W,a,noise,normal_draws,solver='CLARABEL',solver_options=None):
    base=dict(solver_options or {});controls=[base]
    if solver=='CLARABEL':
        controls.extend([dict(base,tol_gap_abs=1e-10,tol_gap_rel=1e-10,tol_feas=1e-10,equilibrate_max_iter=50),
                         dict(base,tol_gap_abs=1e-11,tol_gap_rel=1e-11,tol_feas=1e-11,static_regularization_constant=1e-12),
                         dict(base,tol_gap_abs=1e-11,tol_gap_rel=1e-11,tol_feas=1e-11,static_regularization_enable=False)])
    attempts=[];last_error=None
    for control in controls:
        try:
            phi,info=_original(direct,cascade,phi0,W,a,noise,normal_draws,solver,control)
            diag=info['solver_diagnostics'];upper=float(diag['sdr_bound_max_violation'])
            primal=float(diag['constraint_max_relative_violation'])
            accepted=bool(np.isfinite(upper) and upper<=1e-5 and np.isfinite(primal) and primal<=1e-5
                          and info['unit_modulus_error']<=1e-5 and info['diagonal_error']<=1e-5
                          and info['smallest_sdp_eigenvalue']>=-1e-5)
            attempts.append({'options':control,'status':info['solver_status'],'all_candidates':info['randomization_count'],
                             'rounded_surrogate':info['rounded_surrogate'],'sdr_upper_bound':info['sdr_upper_bound'],
                             'bound_excess':upper,'primal_relative_violation':primal,'accepted':accepted})
            if accepted:
                diag['all_original_draws_upper_bound_guard']='same_input_same_1000_draws_same_SDP_numerical_controls_only'
                diag['post_rounding_same_problem_attempts']=attempts
                return phi,info
            last_error=RuntimeError('Actual rounded candidates exceed original SDP upper-bound/primal tolerance')
        except Exception as error:
            last_error=error;attempts.append({'options':control,'error':str(error),'accepted':False})
    digest=hashlib.sha256()
    for value in (direct,cascade,phi0,W,a,np.asarray(noise),normal_draws):
        x=np.ascontiguousarray(value);digest.update(str(x.shape).encode());digest.update(x.dtype.str.encode());digest.update(x.tobytes())
    folder=Path(__file__).with_name('outputs');folder.mkdir(parents=True,exist_ok=True)
    name='instantaneous-SDP-rounding-failure-'+digest.hexdigest()[:16]+'.mat'
    fixture={'direct':direct,'cascade':cascade,'phi0':phi0,'W':W,'a':a,'noise':noise,'normal_draws':normal_draws}
    savemat(folder/name,fixture)
    error=RuntimeError('Same-input same-SDP numerical controls exhausted; no failed Gaussian candidates dropped: '+str(last_error))
    error.receipt={'block':'phase_SDP_post_1000_rounding_upper_gate','same_problem_numerical_attempts':attempts,
                   'generated_fixture':'outputs/'+name,'fixture_sha256':hashlib.sha256((folder/name).read_bytes()).hexdigest()}
    error.fixture=fixture
    raise error


def install():
    """Install in this instantaneous runner only; source files stay immutable."""
    core.phase_sdr_update=phase_sdr_guard
