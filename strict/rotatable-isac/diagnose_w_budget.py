"""One full-dimension original W QT/MM block; never an AO/MC figure run.

The only permitted override is the unpublished W iteration safety budget.
The saved reference verifies that the original 500-step trajectory is unchanged.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,time
from pathlib import Path
import numpy as np
from core import evaluate,initialize,update_w
from isac_metadata import implementation_fingerprint


def original_power_ball_stationarity(w,theta,r,c,iota):
    """Real-Euclidean first-order residual of the actual fixed-iota utility."""
    _,(gradient,_,_)=evaluate(w,theta,r,c,iota,True)
    power=float(np.sum(abs(w)**2));active=abs(power-c["power"])<=c["verification_tolerance"]
    nu=max(0.,float(np.real(np.vdot(w,gradient))/(2*power))) if active else 0.
    residual=gradient-2*nu*w
    return {"actual_objective_gradient_norm":float(np.linalg.norm(gradient)),
            "estimated_actual_objective_power_dual":nu,
            "actual_objective_KKT_residual":float(np.linalg.norm(residual)),
            "actual_objective_KKT_relative_residual":float(np.linalg.norm(residual)/max(1.,np.linalg.norm(gradient),2*nu*np.linalg.norm(w))),
            "power_constraint_active":active,
            "KKT_convention":"grad_real_F=2*nu*W for max F subject to ||W||_F^2<=P; diagnostic only, not a new stop rule"}


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--scene",type=Path,required=True)
    parser.add_argument("--reference",type=Path,required=True);parser.add_argument("--maximum-iterations",type=int,default=10000)
    parser.add_argument("--output",type=Path,required=True);args=parser.parse_args()
    scene_bytes=args.scene.read_bytes();c=json.loads(scene_bytes);reference_bytes=args.reference.read_bytes();reference=json.loads(reference_bytes)
    engine=implementation_fingerprint()
    if reference.get("implementation_fingerprint")!=engine:
        raise RuntimeError("Reference engine fingerprint differs; do not silently trial a changed model.")
    original=c["W_solver"]["maximum_iterations"]
    if args.maximum_iterations<=original:raise ValueError("Diagnostic trial must increase only the W safety budget.")
    trial=copy.deepcopy(c);trial["W_solver"]["maximum_iterations"]=args.maximum_iterations
    w,theta,r=initialize(trial);initial=evaluate(w,theta,r,trial);iota=initial["iota"]
    clock=time.perf_counter();new,history=update_w(w,theta,r,trial,iota);elapsed=time.perf_counter()-clock
    ref=reference["history"]["Rot-BS & Rot-RIS"]["blocks"][0]["W"]
    prefix=np.asarray(history["objective"][:len(ref["objective"])]);expected=np.asarray(ref["objective"])
    error=float(np.max(abs(prefix-expected))) if prefix.shape==expected.shape else None
    if error is None or error>1e-8:raise RuntimeError("High-budget trajectory does not reproduce the original reference prefix.")
    final=evaluate(new,theta,r,trial,iota);result={
        "paper_id":"rotatable-isac","scope":"full_dimension_one_initial_original_W_QT_MM_block_NOT_full_AO_or_MC",
        "only_override":{"W_solver.maximum_iterations":{"original":original,"trial":args.maximum_iterations}},
        "unchanged_W_solver_settings":{k:v for k,v in c["W_solver"].items() if k!="maximum_iterations"},
        "provenance":{"scene_sha256":hashlib.sha256(scene_bytes).hexdigest(),"reference_sha256":hashlib.sha256(reference_bytes).hexdigest(),
                      "implementation_fingerprint":engine,"diagnostic_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        "dimensions":{"BS":len(c["bs_coordinates"]),"RIS":len(c["ris_coordinates"]),"users":len(c["noise"]),"sensing_samples":len(c["desired_pattern"])},
        "case_metadata":c.get("case_metadata",{}),"elapsed_seconds":elapsed,
        "metrics":{"initial_fixed_iota_utility":initial["utility"],"final_fixed_iota_utility":final["utility"],
                   "fixed_iota":iota,"power":float(np.sum(abs(new)**2)),"actual_stationarity":original_power_ball_stationarity(new,theta,r,trial,iota),
                   "final_MM_QCQP":history["QCQP"][-1]},
        "reference_500_step_stop":{k:v for k,v in ref.items() if k not in ["objective","QCQP"]},
        "checks":{"same_original_trajectory_prefix":error<1e-8,"prefix_max_error":error,
                  "actual_original_stop_reached":history["converged"],"power_feasible":bool(np.sum(abs(new)**2)<=c["power"]+c["verification_tolerance"]),
                  "objective_monotone":bool(np.all(np.diff(history["objective"])>=-c["verification_tolerance"])),"full_reproduction_pass":False},
        "history":history}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({k:result[k] for k in ["scope","only_override","dimensions","elapsed_seconds","metrics","checks"]}))


if __name__=="__main__":main()
