"""Same original RGD with alternating positive spectral step seeds.

BB1/BB2 choose only step size before the unchanged original Armijo check.
No direction, stopping threshold, cap, constraint or model is changed.
"""
import numpy as np
from termination import gradient_stop
from rgd_numerical_controls import criterion_increment,rate_increment


def phase_rgd(phi,fg,settings):
    # These are the existing declared source evaluator closures, not guessed
    # channels. Reject unknown evaluators instead of silently changing them.
    closure=dict(zip(fg.__code__.co_freevars,(c.cell_contents for c in fg.__closure__ or ())))
    if 'P' in closure:
        increment=lambda old,new:criterion_increment(closure['x'],old,new,closure['P'])
    elif 'W' in closure and 'noise' in closure:
        increment=lambda old,new:rate_increment(closure['x'],old,new,closure['W'],closure['noise'])
    else:raise ValueError('No exact original objective-increment contract for this evaluator')
    phi=np.asarray(phi).copy();value,g=fg(phi);history=[value];seed=1/max(np.linalg.norm(g),np.finfo(float).tiny);backtracks=0
    for iteration in range(settings['rgd_max_iterations']):
        norm2=float(np.vdot(g,g).real)
        if np.sqrt(norm2)<=settings['gradient_tolerance']:break
        alpha=seed
        for search in range(60):
            trialphi=phi+alpha*g;trialphi/=abs(trialphi);delta=increment(phi,trialphi)
            if delta>=1e-4*alpha*norm2:break
            alpha/=2;backtracks+=1
        else:raise RuntimeError('Original RGD stable exact-increment Armijo exhausted; no stop or gate relaxed')
        trial,trialg=fg(trialphi)
        step=np.angle(np.conj(phi)*trialphi);old_theta=np.real(np.conj(1j*phi)*g);new_theta=np.real(np.conj(1j*trialphi)*trialg)
        curvature=float(step@(old_theta-new_theta));distance=float(step@step)
        if curvature>0 and distance>0:
            bb1=distance/curvature;yy=float((old_theta-new_theta)@(old_theta-new_theta));bb2=curvature/yy
            seed=bb2 if iteration%2==0 else bb1
        else:seed=2*alpha
        seed=float(np.clip(seed,1e-12,1e12))
        phi,value,g=trialphi,trial,trialg;history.append(value)
    stop=gradient_stop(np.linalg.norm(g),len(history)-1,settings['rgd_max_iterations'],settings['gradient_tolerance'])
    stop.update(numerical_controls='original_RGD_direction_retraction_Armijo_with_alternating_BB1_BB2_positive_step_seeds_and_exact_polynomial_increment',
                total_backtracks=backtracks,gradient_threshold_unchanged=True)
    return phi,history,stop
