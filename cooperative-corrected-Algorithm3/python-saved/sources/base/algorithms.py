"""Full author/thesis AP-AO and MR-PA/TS algorithm chains, no fixed shares."""
import numpy as np
import json
import time
from core import ap_evaluate, ap_qt_update, mr_evaluate, mr_qt_update
from models import channel_moments,mr_components,ap_phase_value_gradient,mr_phase_value_gradient
from termination import relative_stop,gradient_stop,scheme_status
from increments import ap_increment,mr_increment


def feasible_scale(W,Qgt,power_limit,interference_limit):
    J,N,U=W.shape; scales=[1.0]
    for j in range(J): scales.append(np.sqrt(power_limit[j]/np.sum(abs(W[j])**2)))
    for k in range(Qgt.shape[1]):
        leak=sum(np.vdot(W[j,:,u],Qgt[j,k]@W[j,:,u]).real for j in range(J) for u in range(U))
        if leak>0: scales.append(np.sqrt(interference_limit[k]/leak))
    return W*min(scales)*0.95  # tuned feasible initialization margin only


def mr_initial(coef,power_limit,interference_limit):
    _,_,power,leak=coef[:4]; p=np.ones_like(power)
    scales=[1.0]
    for j in range(p.shape[0]): scales.append(power_limit[j]/np.sum(power[j]))
    for k in range(leak.shape[2]):
        if np.sum(leak[:,:,k])>0: scales.append(interference_limit[k]/np.sum(leak[:,:,k]))
    return p*min(scales)*0.95


def mr_power(coef,p0,power_limit,interference_limit,settings,status=None):
    s,b,power,leak,offset=coef[:5]; p=p0.copy()
    # A phase change can invalidate the NoRIS warm start. Restore feasibility
    # by ONE uniform initialization scale; the optimization still has J*U
    # unrestricted powers. This is not a satellite fixed-share restriction.
    scale=1.0
    for j in range(p.shape[0]):
        if np.sum(p[j]*power[j])>0: scale=min(scale,power_limit[j]/np.sum(p[j]*power[j]))
    for k in range(leak.shape[2]):
        if np.sum(p*leak[:,:,k])>0: scale=min(scale,interference_limit[k]/np.sum(p*leak[:,:,k]))
    p*=scale
    history=[float(np.min(mr_evaluate(p,s,b,power,leak,offset)['sinr']))]
    records=[]
    for _ in range(settings['qt_max_iterations']):
        candidate,info=mr_qt_update(p,s,b,power,leak,offset,power_limit,interference_limit,
                                  settings['solver'],settings['solver_options'])
        records.append({'solver_diagnostics':info['solver_diagnostics'],'qt_bound_max_violation':info['qt_bound_max_violation']})
        value=float(np.min(info['after']['sinr']))
        if value<history[-1]-settings['solver_objective_tolerance']: raise RuntimeError('MR QT monotonicity failure')
        p=candidate; history.append(value)
        if (value-history[-2])/max(abs(history[-2]),1e-12)<settings['relative_tolerance']: break
    if status is not None: status.update(scheme_status([relative_stop(history,settings['qt_max_iterations'],settings['relative_tolerance'])],records,settings))
    return p,history


def rmo_ascent(phi,value_gradient,max_iterations,gradient_tolerance,vector_objective=False,status=None,increment=None):
    phi=phi.copy(); value,g=value_gradient(phi); history=[float(np.min(value))]
    initial_slope=np.sum(abs(g)**2,axis=1) if vector_objective else np.sum(abs(g)**2)
    seed=1/np.sqrt(np.maximum(initial_slope,np.finfo(float).tiny))
    for _ in range(max_iterations):
        if np.linalg.norm(g)<gradient_tolerance: break
        slope=np.sum(abs(g)**2,axis=1) if vector_objective else np.sum(abs(g)**2)
        # Source AP optimizes each RIS independently. Its disclosed unreported
        # initial tangent step is one per RIS, before the same Armijo halving.
        alpha=np.asarray(seed).copy() if vector_objective else float(seed)
        if vector_objective:
            # Independently solved AP RIS blocks already below a stricter
            # per-row threshold stay fixed while other RIS blocks proceed.
            # This guarantees the unchanged joint gradient tolerance too.
            stationary=np.sqrt(slope)<gradient_tolerance/np.sqrt(len(slope))
            alpha[stationary]=0;slope[stationary]=0
        for search in range(60):
            candidate=phi+(alpha[:,None] if vector_objective else alpha)*g; candidate/=abs(candidate); trial,newg=value_gradient(candidate)
            if vector_objective:
                # A zero step must be the identity exactly, not a second
                # floating-point re-normalization of a stationary RIS row.
                candidate[stationary]=phi[stationary];trial,newg=value_gradient(candidate)
            difference=trial-value if increment is None else increment(phi,candidate)
            failed=difference<1e-4*alpha*slope
            if not np.any(failed): break
            if vector_objective:alpha[failed]*=0.5
            else:alpha*=0.5
        else:
            error=RuntimeError('Original RGD Armijo search failed; no phase substitute')
            error.receipt={'block':'RGD','iteration':len(history)-1,'gradient_norm':float(np.linalg.norm(g)),
                           'row_gradient_norms':np.linalg.norm(g,axis=1),'value':value,'last_trial':trial,
                           'last_step':alpha,'last_required_increase':1e-4*alpha*slope,'vector_objective':vector_objective}
            raise error
        step=np.angle(np.conj(phi)*candidate);old_theta=np.real(np.conj(1j*phi)*g);new_theta=np.real(np.conj(1j*candidate)*newg)
        axis=1 if vector_objective else None;curvature=np.sum(step*(old_theta-new_theta),axis=axis);distance=np.sum(step**2,axis=axis)
        if vector_objective:seed=np.divide(distance,curvature,out=2*alpha,where=(curvature>0)&(distance>0))
        else:seed=distance/curvature if curvature>0 and distance>0 else 2*alpha
        seed=np.clip(seed,1e-12,1e12)
        improvement=float(np.min(trial)-np.min(value)); phi=candidate; value=trial; g=newg; history.append(float(np.min(value)))
    stop=gradient_stop(np.linalg.norm(g),len(history)-1,max_iterations,gradient_tolerance)
    stop['initial_step_contract']='positive_BB_seed_in_original_RGD_direction_before_original_Armijo; numerical_control_not_threshold_change'
    stop['objective_increment_contract']='exact_original_moment_polynomial_ratio_logsumexp_increment' if increment is not None else 'direct_objective_difference'
    if status is not None: status.update(stop)
    return phi,history


def ap_no_ris(data,phi,power_limit,interference_limit,settings,status=None):
    mean,C,_,_,offset=channel_moments(data,phi,True)
    W=feasible_scale(np.transpose(mean,(0,2,1)),data['gt_second'],power_limit,interference_limit)
    history=[float(np.min(ap_evaluate(W,mean,C,data['gt_second'],offset)['sinr']))]
    records=[]
    for _ in range(settings['qt_max_iterations']):
        W,info=ap_qt_update(W,mean,C,data['gt_second'],offset,power_limit,interference_limit,settings['solver'],settings['solver_options'])
        records.append({'solver_diagnostics':info['solver_diagnostics'],'qt_bound_max_violation':info['qt_bound_max_violation']})
        value=float(np.min(info['after']['sinr'])); history.append(value)
        if value<history[-2]-settings['solver_objective_tolerance']: raise RuntimeError('AP QT monotonicity failure')
        if (value-history[-2])/max(abs(history[-2]),1e-12)<settings['relative_tolerance']: break
    if status is not None: status.update(scheme_status([relative_stop(history,settings['qt_max_iterations'],settings['relative_tolerance'])],records,settings))
    return W,history


def ap_ao(data,phi,W0,power_limit,interference_limit,settings,status=None):
    phi=phi.copy(); W=W0.copy(); mean,C,_,_,offset=channel_moments(data,phi)
    history=[float(np.min(ap_evaluate(W,mean,C,data['gt_second'],offset)['sinr']))]
    records=[]; stops=[]
    for _ in range(settings['ao_max_iterations']):
        W,info=ap_qt_update(W,mean,C,data['gt_second'],offset,power_limit,interference_limit,settings['solver'],settings['solver_options'])
        records.append({'solver_diagnostics':info['solver_diagnostics'],'qt_bound_max_violation':info['qt_bound_max_violation']})
        stop={}
        phi,_=rmo_ascent(phi,lambda x:ap_phase_value_gradient(data,x,W),settings['rmo_max_iterations'],settings['gradient_tolerance'],True,stop,
                         increment=lambda old,new:ap_increment(data,old,new,W))
        stops.append(stop)
        mean,C,_,_,offset=channel_moments(data,phi); value=float(np.min(ap_evaluate(W,mean,C,data['gt_second'],offset)['sinr']))
        if value<history[-1]-settings['solver_objective_tolerance']: raise RuntimeError('AP-AO monotonicity failure')
        history.append(value)
        if (value-history[-2])/max(abs(history[-2]),1e-12)<settings['relative_tolerance']: break
    stops.append(relative_stop(history,settings['ao_max_iterations'],settings['relative_tolerance']))
    if status is not None: status.update(scheme_status(stops,records,settings))
    return phi,W,history


def mr_two_stage(data,phi,p0,power_limit,interference_limit,settings,tts,status=None):
    # Full square residual penalty exactly as the thesis, including feasible
    # residuals; not silently replaced by a positive-part/hinge penalty.
    phi=phi.copy(); mu=settings['smoothing_initial']; phase_history=[]; phase_stops=[]
    while mu>=settings['smoothing_final']:
        value_gradient=lambda x:mr_phase_value_gradient(data,x,p0,mu,interference_limit,tts)
        # Algorithm 3 retains mu while improving and halves at stationarity.
        for inner in range(settings['smoothing_max_repeats']):
            before=value_gradient(phi)[0]
            stop={}
            phi,h=rmo_ascent(phi,value_gradient,settings['rmo_max_iterations'],settings['gradient_tolerance'],status=stop,
                             increment=lambda old,new:mr_increment(data,old,new,p0,mu,interference_limit,tts))
            phase_stops.append(stop)
            phase_history.append({'mu':mu,'objective':h})
            if h[-1]-before<=settings['smoothing_progress_tolerance']: break
        else:
            error=RuntimeError('Smoothing repeat cap reached while improving; no completed phase claim')
            error.receipt={'block':'MR-TTS_smoothing' if tts else 'MR-S_smoothing','mu':mu,'repeats':settings['smoothing_max_repeats'],
                           'last_phase_stop':phase_stops[-1],'last_objective_history':phase_history[-1],'power_initialization':p0}
            raise error
        mu/=2
    coef=mr_components(data,phi,tts)
    # Start stage 2 with the p_INIT from original NoRIS design. Constraints are
    # in the QT subproblem, so it obtains a feasible output even if phase changed.
    power_status={}; p,history=mr_power(coef,p0,power_limit,interference_limit,settings,power_status)
    if status is not None:
        status.update(scheme_status(phase_stops+power_status['blocks'],power_status['solver_diagnostics'],settings))
        status['smoothing_schedule_completed']=bool(mu<settings['smoothing_final'])
    return phi,p,{'phase':phase_history,'power':history}


def run_all_schemes(data,settings,power_limit,interference_limit):
    started=time.perf_counter()
    def progress(name,status):print(json.dumps({'cooperative_scheme_completed':name,'elapsed_seconds':time.perf_counter()-started,'converged':status['converged'],'algorithm_success':status['algorithm_success']}),flush=True)
    J,U,N=data['d_mean'].shape; M=data['r_mean'].shape[1]
    phi=np.exp(1j*np.asarray(settings['initial_phase_radians'])*np.ones((U,M)))
    s0={}; sap={}
    W0,h0=ap_no_ris(data,phi,power_limit,interference_limit,settings,s0)
    progress('AP-NoRIS',s0)
    ap_phi,W,hap=ap_ao(data,phi,W0,power_limit,interference_limit,settings,sap)
    progress('AP-AO',sap)
    mean,C,_,_,off=channel_moments(data,ap_phi)
    ap=ap_evaluate(W,mean,C,data['gt_second'],off)
    outputs={'AP-NoRIS':{'evaluation':ap_evaluate(W0,*channel_moments(data,phi,True)[:2],data['gt_second'],channel_moments(data,phi,True)[4]),'history':h0,'status':s0},
             'AP-AO':{'evaluation':ap,'history':hap,'status':sap}}
    for tts,prefix in ((False,'MR-S'),(True,'MR-TTS')):
        coef0=mr_components(data,phi,tts,True); pinit=mr_initial(coef0,power_limit,interference_limit)
        stop={}; p0,h=mr_power(coef0,pinit,power_limit,interference_limit,settings,stop)
        outputs[prefix+'-NoRIS']={'evaluation':mr_evaluate(p0,*coef0[:5]),'history':h,'status':stop}
        progress(prefix+'-NoRIS',stop)
        coef=mr_components(data,ap_phi,tts); stop={}; ppa,h=mr_power(coef,p0,power_limit,interference_limit,settings,stop)
        stop['phase_source_converged']=sap['converged']; stop['algorithm_success']=stop['algorithm_success'] and sap['algorithm_success']
        outputs[prefix+'-PA']={'evaluation':mr_evaluate(ppa,*coef[:5]),'history':h,'status':stop}
        progress(prefix+'-PA',stop)
        stop={}; tsphi,pts,h=mr_two_stage(data,phi,p0,power_limit,interference_limit,settings,tts,stop)
        coef=mr_components(data,tsphi,tts)
        outputs[prefix+'-TS']={'evaluation':mr_evaluate(pts,*coef[:5]),'history':h,'status':stop}
        progress(prefix+'-TS',stop)
    return outputs
