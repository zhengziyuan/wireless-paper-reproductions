"""Full author/thesis AP-AO and MR-PA/TS algorithm chains, no fixed shares."""
import numpy as np
from core import ap_evaluate, ap_qt_update, mr_evaluate, mr_qt_update
from models import channel_moments,mr_components,ap_phase_value_gradient,mr_phase_value_gradient
from termination import relative_stop,gradient_stop,scheme_status


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


def rmo_ascent(phi,value_gradient,max_iterations,gradient_tolerance,vector_objective=False,status=None):
    phi=phi.copy(); value,g=value_gradient(phi); history=[float(np.min(value))]
    for _ in range(max_iterations):
        if np.linalg.norm(g)<gradient_tolerance: break
        alpha=1.0; slope=np.sum(abs(g)**2,axis=1) if vector_objective else np.sum(abs(g)**2)
        for search in range(60):
            candidate=phi+alpha*g; candidate/=abs(candidate); trial,newg=value_gradient(candidate)
            if np.all(trial>=value+1e-4*alpha*slope-1e-12): break
            alpha*=0.5
        else: raise RuntimeError('Original RGD Armijo search failed; no phase substitute')
        improvement=float(np.min(trial)-np.min(value)); phi=candidate; value=trial; g=newg; history.append(float(np.min(value)))
        if improvement>=0 and improvement<1e-12 and np.linalg.norm(g)<10*gradient_tolerance: break
    stop=gradient_stop(np.linalg.norm(g),len(history)-1,max_iterations,gradient_tolerance)
    # Preserve the implemented tiny-progress + near-stationarity stopping rule.
    if not stop['converged'] and len(history)>1 and 0<=history[-1]-history[-2]<1e-12 and np.linalg.norm(g)<10*gradient_tolerance:
        stop.update(converged=True,termination='tiny_progress_and_near_stationary_gradient',stop_rule='progress_below_1e-12_and_gradient_below_10_times_tolerance',threshold=10*gradient_tolerance)
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
        phi,_=rmo_ascent(phi,lambda x:ap_phase_value_gradient(data,x,W),settings['rmo_max_iterations'],settings['gradient_tolerance'],True,stop)
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
            phi,h=rmo_ascent(phi,value_gradient,settings['rmo_max_iterations'],settings['gradient_tolerance'],status=stop)
            phase_stops.append(stop)
            phase_history.append({'mu':mu,'objective':h})
            if h[-1]-before<=settings['smoothing_progress_tolerance']: break
        else: raise RuntimeError('Smoothing repeat cap reached while improving; no completed phase claim')
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
    J,U,N=data['d_mean'].shape; M=data['r_mean'].shape[1]
    phi=np.exp(1j*np.asarray(settings['initial_phase_radians'])*np.ones((U,M)))
    s0={}; sap={}
    W0,h0=ap_no_ris(data,phi,power_limit,interference_limit,settings,s0)
    ap_phi,W,hap=ap_ao(data,phi,W0,power_limit,interference_limit,settings,sap)
    mean,C,_,_,off=channel_moments(data,ap_phi)
    ap=ap_evaluate(W,mean,C,data['gt_second'],off)
    outputs={'AP-NoRIS':{'evaluation':ap_evaluate(W0,*channel_moments(data,phi,True)[:2],data['gt_second'],channel_moments(data,phi,True)[4]),'history':h0,'status':s0},
             'AP-AO':{'evaluation':ap,'history':hap,'status':sap}}
    for tts,prefix in ((False,'MR-S'),(True,'MR-TTS')):
        coef0=mr_components(data,phi,tts,True); pinit=mr_initial(coef0,power_limit,interference_limit)
        stop={}; p0,h=mr_power(coef0,pinit,power_limit,interference_limit,settings,stop)
        outputs[prefix+'-NoRIS']={'evaluation':mr_evaluate(p0,*coef0[:5]),'history':h,'status':stop}
        coef=mr_components(data,ap_phi,tts); stop={}; ppa,h=mr_power(coef,p0,power_limit,interference_limit,settings,stop)
        stop['phase_source_converged']=sap['converged']; stop['algorithm_success']=stop['algorithm_success'] and sap['algorithm_success']
        outputs[prefix+'-PA']={'evaluation':mr_evaluate(ppa,*coef[:5]),'history':h,'status':stop}
        stop={}; tsphi,pts,h=mr_two_stage(data,phi,p0,power_limit,interference_limit,settings,tts,stop)
        coef=mr_components(data,tsphi,tts)
        outputs[prefix+'-TS']={'evaluation':mr_evaluate(pts,*coef[:5]),'history':h,'status':stop}
    return outputs
