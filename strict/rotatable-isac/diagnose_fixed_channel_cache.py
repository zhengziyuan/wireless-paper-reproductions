"""Full-dimension six-scheme exact cache audit; NOT a new full-bank run.

Uses the immutable completed first bank job and its actual W-block histories.
No frozen source file, live process, threshold, input, or algorithm is changed.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import core
from fixed_channel_cache import FixedChannelEvaluator
from isac_metadata import implementation_fingerprint,complete,fingerprint
from run import initialize
from execute_bank import atomic_json

SCHEMES=["Rot-BS & Rot-RIS","Rot-BS & Fix-RIS","Fix-BS & Rot-RIS","Fix-BS & Fix-RIS","Rot-BS & No-RIS","Fix-BS & No-RIS"]


def scalar_field(theta,r,c):
    """Independent scalar response and per-element path sums; no core calls."""
    def frame(angles):
        x,y,z=angles;cx,sx,cy,sy,cz,sz=np.cos(x),np.sin(x),np.cos(y),np.sin(y),np.cos(z),np.sin(z)
        Rx=np.array([[1.,0.,0.],[0.,cx,-sx],[0.,sx,cx]])
        Ry=np.array([[cy,0.,sy],[0.,1.,0.],[-sy,0.,cy]])
        Rz=np.array([[cz,-sz,0.],[sz,cz,0.],[0.,0.,1.]])
        return Rx@Ry@Rz
    qb,qr=frame(r[:3]),frame(r[3:]);cb=np.asarray(c["bs_coordinates"]);cr=np.asarray(c["ris_coordinates"])
    def response(coordinate,center,direction,q):
        direction=np.asarray(direction);cosine=float(q[:,2]@direction)
        if cosine<=0:return 0j
        xyz=q@coordinate+np.asarray(center)
        amplitude=np.sqrt(c["maximum_gain"])*cosine**(c["directivity_exponent"]/2)
        return amplitude*np.exp(2j*np.pi/c["wavelength"]*sum(xyz[d]*direction[d] for d in range(3)))
    k=len(c["noise"]);a=len(c["bt_directions"]);H=np.zeros((len(cb),k+a),complex);G=np.zeros((len(cr),k+a),complex)
    for user in range(k):
        for ray in range(len(c["bu_directions"][user])):
            gain=complex(c["bu_gain_re"][user][ray],c["bu_gain_im"][user][ray])
            for antenna in range(len(cb)):H[antenna,user]+=gain*response(cb[antenna],c["bs_center"],c["bu_directions"][user][ray],qb)
        for ray in range(len(c["ru_directions"][user])):
            gain=complex(c["ru_gain_re"][user][ray],c["ru_gain_im"][user][ray])
            for antenna in range(len(cr)):G[antenna,user]+=gain*response(cr[antenna],c["ris_center"],c["ru_directions"][user][ray],qr)
    for target in range(a):
        for antenna in range(len(cb)):H[antenna,k+target]=response(cb[antenna],c["bs_center"],c["bt_directions"][target],qb)
        for antenna in range(len(cr)):G[antenna,k+target]=response(cr[antenna],c["ris_center"],c["rt_directions"][target],qr)
    bridge=np.zeros((len(cb),len(cr)),complex)
    for ray in range(len(c["br_directions"])):
        gain=complex(c["br_gain_re"][ray],c["br_gain_im"][ray])
        for antenna in range(len(cb)):
            ab=response(cb[antenna],c["bs_center"],c["br_directions"][ray],qb)
            for element in range(len(cr)):
                ar=response(cr[element],c["ris_center"],c["rb_directions"][ray],qr)
                bridge[antenna,element]+=gain*ab*ar.conjugate()
    F=H.copy()
    for antenna in range(len(cb)):
        for link in range(k+a):
            F[antenna,link]+=sum(bridge[antenna,element]*theta[element]*G[element,link] for element in range(len(cr)))
    return F


def scalar_utility(w,theta,r,c,iota):
    F=scalar_field(theta,r,c);k=len(c["noise"]);rate=0.;pattern=[]
    for user in range(k):
        amplitudes=[sum(F[a,user].conjugate()*w[a,j] for a in range(len(w))) for j in range(w.shape[1])]
        signal=abs(amplitudes[user])**2;interference=sum(abs(v)**2 for j,v in enumerate(amplitudes) if j!=user)+c["noise"][user]
        rate+=np.log2(1+signal/interference)
    for target in range(len(c["desired_pattern"])):
        amplitudes=[sum(F[a,k+target].conjugate()*w[a,j] for a in range(len(w))) for j in range(w.shape[1])]
        pattern.append(sum(abs(v)**2 for v in amplitudes))
    residual=np.asarray(pattern)-iota*np.asarray(c["desired_pattern"])
    nmse=sum(v*v for v in residual)/(iota*iota*sum(v*v for v in c["desired_pattern"]))
    return float(rate-c["rho"]*nmse)


def audit(scene_bytes,config_bytes,source_bytes):
    c=json.loads(scene_bytes);source=json.loads(source_bytes)
    if not complete(source,fingerprint(config_bytes,scene_bytes)):raise ValueError("Actual complete full-dimension six-scheme source receipt required")
    if len(c["bs_coordinates"])!=4 or len(c["ris_coordinates"])!=36 or len(c["desired_pattern"])!=66:raise ValueError("Full original4/36/66 dimensions required")
    original_evaluate=core.evaluate;rng=np.random.default_rng(615144);records=[];runs={};started=time.perf_counter()
    for name in SCHEMES:
        cfg=copy.deepcopy(c);no_ris="No-RIS" in name
        if no_ris:cfg["br_gain_re"]=[0.]*len(c["br_gain_re"]);cfg["br_gain_im"]=[0.]*len(c["br_gain_im"])
        saved=source["metrics"][name];w=np.asarray(saved["w_re"])+1j*np.asarray(saved["w_im"])
        theta=np.asarray(saved["theta_re"])+1j*np.asarray(saved["theta_im"]);r=np.asarray(saved["rotation"])
        fixed=FixedChannelEvaluator(theta,r,cfg);actual,grad=original_evaluate(w,theta,r,cfg,None,True);fast,fg=fixed.evaluate(w,None,True)
        metric_errors={key:float(np.max(abs(np.asarray(actual[key])-np.asarray(fast[key])))) for key in actual}
        gradient_errors=[float(np.max(abs(a-b))) for a,b in zip(grad,fg)]
        if max(list(metric_errors.values())+gradient_errors)!=0:raise RuntimeError("Cached full metrics/gradients not bitwise identical")
        scalar_value=scalar_utility(w,theta,r,cfg,actual["iota"])
        if not np.isclose(scalar_value,actual["utility"],rtol=1e-9,atol=1e-9):raise RuntimeError("Independent scalar physical-model utility failed")
        # Gradient oracle at the original INITIAL full-dimensional state.
        # Its normal projections are away from the halfspace cusp; final
        # metrics/gradient cache equality above includes actual final states.
        wi,ti,ri=initialize(cfg);initial,ig=original_evaluate(wi,ti,ri,cfg,None,True);iota=initial["iota"]
        dw=(rng.normal(size=wi.shape)+1j*rng.normal(size=wi.shape));dw/=np.linalg.norm(dw)
        phase=rng.normal(size=len(ti));phase/=np.linalg.norm(phase);dr=rng.normal(size=6);dr/=np.linalg.norm(dr)
        eps=1e-6
        fdw=(scalar_utility(wi+eps*dw,ti,ri,cfg,iota)-scalar_utility(wi-eps*dw,ti,ri,cfg,iota))/(2*eps)
        fdt=(scalar_utility(wi,ti*np.exp(1j*eps*phase),ri,cfg,iota)-scalar_utility(wi,ti*np.exp(-1j*eps*phase),ri,cfg,iota))/(2*eps)
        fdr=(scalar_utility(wi,ti,ri+eps*dr,cfg,iota)-scalar_utility(wi,ti,ri-eps*dr,cfg,iota))/(2*eps)
        analytic=[float(np.real(np.vdot(ig[0],dw))),float(np.real(np.vdot(ig[1],1j*ti*phase))),float(ig[2]@dr)]
        fd=[fdw,fdt,fdr];gradient_oracle_relative_errors=[abs(a-b)/max(1,abs(a),abs(b)) for a,b in zip(analytic,fd)]
        if max(gradient_oracle_relative_errors)>1e-5:raise RuntimeError("Independent scalar directional gradient oracle failed")
        group="no_RIS" if no_ris else "with_RIS"
        if group not in runs:
            # Full original W budget and stop gates, not a shortened run.
            wi,ti,ri=initialize(cfg);iota=original_evaluate(wi,ti,ri,cfg)["iota"]
            clock=time.perf_counter();uncached,uh=core.update_w(wi.copy(),ti,ri,cfg,iota);slow_seconds=time.perf_counter()-clock
            context=FixedChannelEvaluator(ti,ri,cfg)
            try:
                core.evaluate=context.bind
                clock=time.perf_counter();cached,ch=core.update_w(wi.copy(),ti,ri,cfg,iota);fast_seconds=time.perf_counter()-clock
            finally:core.evaluate=original_evaluate
            context.check_immutable_configuration()
            if not np.array_equal(uncached,cached) or uh!=ch:raise RuntimeError("Full original QT/MM state/objectives/QCQP/stop gates changed")
            runs[group]={"original_iterations":uh["iterations"],"original_converged":uh["converged"],"original_stop_reason":uh["termination_reason"],
                "full_original_W_budget":cfg["W_solver"]["maximum_iterations"],"all_prefix_objectives_bitwise_equal":True,
                "full_final_W_state_bitwise_equal":True,"all_QCQP_history_and_stop_gates_exactly_equal":True,
                "uncached_seconds":slow_seconds,"cached_seconds":fast_seconds,"measured_W_block_speedup":slow_seconds/fast_seconds,
                "objective":ch["objective"],"W_re":cached.real.tolist(),"W_im":cached.imag.tolist(),"history":ch}
        reference=source["history"][name]["blocks"][0]["W"]
        if runs[group]["objective"]!=reference["objective"]:raise RuntimeError("W trajectory differs from actual saved original full-bank prefix")
        for key in ["iterations","converged","termination_reason","relative_objective_improvement","relative_step"]:
            if runs[group]["history"][key]!=reference[key]:raise RuntimeError("Source receipt stop gate does not match cached original W run")
        records.append({"scheme":name,"actual_final_full_state_metrics_and_gradients_bitwise_equal":True,
            "metric_max_abs_errors":metric_errors,"gradient_max_abs_errors":gradient_errors,
            "independent_scalar_final_utility_absolute_error":abs(scalar_value-actual["utility"]),
            "initial_state_scalar_directional_gradient_relative_errors_W_RIS_rotation":gradient_oracle_relative_errors,
            "full_original_initial_W_trajectory_matches_saved_scheme_reference":True,"W_test_group":group})
        print(json.dumps({"scheme":name,"verified":True,"group":group,"W_speedup":runs[group]["measured_W_block_speedup"]}),flush=True)
    return {"paper_id":"rotatable-isac","scope":"isolated_full_dimension_fixed_channel_cache_equivalence_not_full_bank",
        "dimensions":{"BS":4,"RIS":36,"sensing_samples":66,"schemes":6},"source_implementation_fingerprint":implementation_fingerprint(),
        "source_scene_sha256":hashlib.sha256(scene_bytes).hexdigest(),"source_result_sha256":hashlib.sha256(source_bytes).hexdigest(),
        "prototype_source_sha256":hashlib.sha256(Path(__file__).read_bytes()+Path(__file__).with_name("fixed_channel_cache.py").read_bytes()).hexdigest(),
        "numeric_source_or_live_process_changed":False,"all_six_schemes_verified":True,"W_runs":runs,"scheme_checks":records,
        "full_bank_acceleration_or_figure_completion_claimed":False,"elapsed_seconds":time.perf_counter()-started}


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scene",type=Path,required=True);p.add_argument("--config",type=Path,required=True);p.add_argument("--source-result",type=Path,required=True);p.add_argument("--output",type=Path,required=True);args=p.parse_args()
    result=audit(args.scene.read_bytes(),args.config.read_bytes(),args.source_result.read_bytes());args.output.parent.mkdir(parents=True,exist_ok=True);atomic_json(args.output,result)
    print(json.dumps({"all_six_schemes_verified":True,"speedups":{k:v["measured_W_block_speedup"] for k,v in result["W_runs"].items()},"numeric_source_or_live_process_changed":False}))
