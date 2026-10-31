"""Prepared conditional validation of a saved Fig5 ZF trajectory for Fig20.

This module never reads an input or launches a task on import.  A caller must
supply already held, decoded objects and current source modules.  It does not
run an optimizer.  Scientific claims remain conditional on the saved producer
having followed the recorded single-coordinate source order and on its input
identity, neither of which this replay authenticates.
"""
from __future__ import annotations
import math
import numpy as np


def verify(old_job, target_job, config, saved, run, core, coordinate_exact):
    fields = ("N", "M", "kappa", "power", "A", "realization", "geometry")
    if not all(old_job.get(k) == target_job.get(k) for k in fields):
        raise ValueError("current saved geometry/config differ")
    if (target_job.get("figure"), target_job.get("point"), target_job.get("N"),
        target_job.get("M"), target_job.get("kappa"), target_job.get("power"),
        target_job.get("A"), target_job.get("realization")) != (20, 3, 6, 5, 100, 1.0, 2.0, 0):
        raise ValueError("wrong target scenario")
    lo = np.asarray(target_job["region_lower"], dtype=np.float64)
    hi = np.asarray(target_job["region_upper"], dtype=np.float64)
    has_old_lo="region_lower" in old_job;has_old_hi="region_upper" in old_job
    if has_old_lo != has_old_hi:
        raise ValueError("partial old region override")
    if has_old_lo:
        old_lo=np.asarray(old_job["region_lower"],dtype=np.float64)
        old_hi=np.asarray(old_job["region_upper"],dtype=np.float64)
        old_region_interpretation="explicit_job_region"
    else:
        old_defaults,_=run.scenario(config,old_job["N"],old_job["M"],old_job["kappa"],
                                    old_job["power"],old_job["A"],old_job["geometry"])
        old_lo=np.asarray(old_defaults["region_lower"],dtype=np.float64)
        old_hi=np.asarray(old_defaults["region_upper"],dtype=np.float64)
        old_region_interpretation="current_run_scenario_default_for_job_without_override"
    if (lo.tolist(),hi.tolist()) != ([-1.6,-1.6],[1.6,2.4]) or not (
        np.all(lo >= old_lo) and np.all(hi <= old_hi)):
        raise ValueError("target box not the specified subset")
    for key in ("nlos_re","nlos_im"):
        a=np.asarray(old_job[key],dtype=np.float64)
        b=np.asarray(target_job[key],dtype=np.float64)
        if a.shape!=(1000,6,5) or b.shape!=a.shape or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)) or not np.array_equal(a.view(np.uint64),b.view(np.uint64)):
            raise ValueError("present saved samples differ")
    model,initial=run.scenario(config,target_job["N"],target_job["M"],
        target_job["kappa"],target_job["power"],target_job["A"],target_job["geometry"])
    if model.get("maximum_AO_iterations")!=10000 or model.get("nlos_realizations_per_geometry")!=1000:
        raise ValueError("wrong AO or Monte Carlo configured budget")
    model["region_lower"],model["region_upper"]=lo.tolist(),hi.tolist()
    large_model=dict(model,region_lower=old_lo.tolist(),region_upper=old_hi.tolist())
    hist=saved["history"]["zf"]; positions=np.asarray(hist["positions"],dtype=np.float64)
    objectives=np.asarray(hist["objective"],dtype=np.float64); records=hist["coordinate_updates"]
    if (positions.ndim!=3 or positions.shape[1:]!=(6,2) or len(positions)<2 or
        len(records)!=(len(positions)-1)*6 or len(objectives)!=len(positions) or
        not np.all(np.isfinite(positions)) or not np.all(np.isfinite(objectives)) or
        not np.array_equal(positions[0].view(np.uint64),np.asarray(initial,dtype=np.float64).view(np.uint64))):
        raise ValueError("history shape or target initial state")
    tolerance=float(model["verification_tolerance"])
    objective_tol=1e-10
    max_old_gap=0.;max_old_gap_recomputed=0.;max_small_gap=0.;max_source_error=0.
    initial_box=float(np.min(np.concatenate((positions[0]-lo,hi-positions[0]),axis=1)))
    initial_dist=np.linalg.norm(positions[0][:,None,:]-positions[0][None,:,:],axis=2)
    initial_spacing=float(np.min(initial_dist+np.eye(6)*1e9))
    min_box=initial_box;min_spacing=initial_spacing;min_linear=float("inf")
    checked=0;failures=[]
    if initial_box < -1e-10 or initial_spacing < model["minimum_distance"]-1e-10:
        failures.append({"index":None,"reason":"initial_state_feasibility"})
    for k,rec in enumerate(records):
        sweep,ant=divmod(k,6)
        for key in ("before","after","surrogate"):
            v=rec.get(key)
            if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):
                raise ValueError("nonfinite or invalid saved objective")
        if rec.get("solver_status")!="certified_global_2d" or rec.get("original_subproblem_unchanged") is not True:
            raise ValueError("unrecognized saved solver status")
        if rec.get("sweep")!=sweep or rec.get("antenna")!=ant:
            raise ValueError("recorded coordinate order differs from current source")
        before=positions[sweep].copy();before[:ant]=positions[sweep+1,:ant]
        after=before.copy();after[ant]=positions[sweep+1,ant]
        d=after[ant]-before[ant]
        box=float(np.min(np.concatenate((after-lo,hi-after),axis=1)))
        distances=np.linalg.norm(after[:,None,:]-after[None,:,:],axis=2)
        spacing=float(np.min(distances+np.eye(6)*1e9))
        constraints=[]
        for other in range(6):
            if other!=ant:
                q=before[ant]-before[other]
                constraints.append(float(2*q@d+q@q-model["minimum_distance"]**2))
        lin=min(constraints)
        min_box=min(min_box,box);min_spacing=min(min_spacing,spacing);min_linear=min(min_linear,lin)
        val=core.zf_statistics(before,model)[0];val_after=core.zf_statistics(after,model)[0]
        if not math.isfinite(val) or not math.isfinite(val_after):
            failures.append({"index":k,"reason":"nonfinite_source_objective"});continue
        source_error=max(abs(val-float(rec["before"])),abs(val_after-float(rec["after"])))
        max_source_error=max(max_source_error,source_error)
        if box < -1e-10 or spacing < model["minimum_distance"]-1e-10 or lin < -1e-10:
            failures.append({"index":k,"reason":"target_feasibility"})
        if source_error > objective_tol or val_after < val-tolerance or val_after < float(rec["surrogate"])-tolerance:
            failures.append({"index":k,"reason":"current_source_objective"})
        s=core.zf_surrogate(before,model,ant);eta=core.zf_statistics(before,model)[3]
        if not np.all(np.isfinite(eta)) or np.any(eta<=0) or not np.all(np.isfinite(s["ratio"])) or not np.all(np.isfinite(s["gradient"])) or not np.all(np.isfinite(s["curvature"])) or np.any(s["curvature"]<0):
            failures.append({"index":k,"reason":"surrogate_finite_and_concave"});continue
        base=s["ratio"]+1/eta;change=s["gradient"]@d-s["curvature"]*(d@d)/2
        denom=base+change
        if np.any(base<=0) or np.any(denom<=0) or not np.all(np.isfinite(denom)):
            failures.append({"index":k,"reason":"surrogate_domain"});continue
        gain=float(np.log1p(change/base).sum()/np.log(2))
        grad=((s["gradient"]-s["curvature"][:,None]*d)/denom[:,None]).sum(axis=0)/np.log(2)
        target_a,target_b,vertices,polygon_tol=coordinate_exact.polygon(before,model,ant)
        large_a,large_b,large_vertices,large_tol=coordinate_exact.polygon(before,large_model,ant)
        target_residual=float(np.max(target_a@d-target_b))
        large_residual=float(np.max(large_a@d-large_b))
        if target_residual>polygon_tol or large_residual>large_tol:
            failures.append({"index":k,"reason":"normalized_polygon_feasibility"})
        target_products=(vertices-d)@grad;large_products=(large_vertices-d)@grad
        if not (np.isfinite(gain) and np.all(np.isfinite(base)) and np.all(np.isfinite(change)) and
                np.all(np.isfinite(grad)) and np.all(np.isfinite(vertices)) and
                np.all(np.isfinite(large_vertices)) and np.all(np.isfinite(target_products)) and
                np.all(np.isfinite(large_products)) and np.isfinite(target_residual) and np.isfinite(large_residual)):
            failures.append({"index":k,"reason":"nonfinite_gap_inputs"});continue
        gap=max(0.,float(np.max(target_products)))
        large_gap=max(0.,float(np.max(large_products)))
        max_old_gap_recomputed=max(max_old_gap_recomputed,large_gap)
        cert=rec.get("certificate",{})
        old_gap_value=cert.get("global_objective_gap_upper_bound")
        old_limit_value=cert.get("global_objective_gap_tolerance")
        if any(isinstance(x,bool) or not isinstance(x,(int,float)) for x in (old_gap_value,old_limit_value)):
            failures.append({"index":k,"reason":"invalid_saved_gap_fields"});continue
        old_gap=float(old_gap_value);old_limit=float(old_limit_value)
        gap_limit=max(model["convex_solver"]["options"].get("objective_gap_absolute_tolerance",1e-10),
            model["convex_solver"]["options"].get("objective_gap_relative_tolerance",1e-10)*abs(val))
        max_old_gap=max(max_old_gap,old_gap);max_small_gap=max(max_small_gap,gap)
        if cert.get("backend")!="exact_2D_original_subproblem_active_set" or cert.get("original_subproblem_unchanged") is not True or not math.isfinite(old_gap) or not math.isfinite(old_limit) or old_gap<0 or old_limit<0 or abs(old_limit-gap_limit)>max(1e-20,1e-13*abs(gap_limit)) or old_gap>old_limit or not math.isfinite(large_gap) or large_gap>old_limit:
            failures.append({"index":k,"reason":"saved_larger_box_gap"})
        if not math.isfinite(gap) or gap>gap_limit or abs((val+gain)-float(rec["surrogate"]))>objective_tol:
            failures.append({"index":k,"reason":"target_surrogate_or_gap"})
        checked+=1
    sweep_errors=[abs(core.zf_statistics(t,model)[0]-float(v)) for t,v in zip(positions,objectives)]
    if not all(math.isfinite(x) and x <= objective_tol for x in sweep_errors):
        failures.append({"index":None,"reason":"saved_sweep_objective"})
    if np.any(objectives[:-1]==0):
        raise ValueError("zero stopping denominator")
    step_increases=(objectives[1:]-objectives[:-1])/np.abs(objectives[:-1])
    triggers=np.flatnonzero(step_increases<float(model["fractional_increase_threshold"]))
    saved_final=np.asarray(saved["metrics"]["zf_positions"],dtype=np.float64)
    if not np.array_equal(saved_final.view(np.uint64),positions[-1].view(np.uint64)):
        failures.append({"index":None,"reason":"saved_terminal_differs"})
    if len(triggers)!=1 or int(triggers[0])!=len(objectives)-2 or not hist.get("converged") or hist.get("termination")!="fractional_increase":
        failures.append({"index":None,"reason":"saved_stopping_rule"})
    return {"schema":"MA20_ZF_FIG5_DONOR_CONDITIONAL_REPLAY_PREPARED_V2",
        "saved_sweeps":len(positions)-1,"coordinates_examined":checked,"failures":failures,
        "old_region_interpretation":old_region_interpretation,"old_region_lower":old_lo.tolist(),"old_region_upper":old_hi.tolist(),
        "configured_AO_iteration_cap":model["maximum_AO_iterations"],"configured_nlos_count":model["nlos_realizations_per_geometry"],
        "conditional_same_source_check_pass":bool(not failures and checked==198 and len(positions)-1==33),
        "maximum_saved_large_box_gap":max_old_gap,"maximum_recomputed_large_box_gap":max_old_gap_recomputed,"maximum_recomputed_target_gap":max_small_gap,
        "maximum_objective_error":max_source_error,"maximum_sweep_objective_error":max(sweep_errors),"minimum_target_box_margin":min_box,
        "minimum_spacing":min_spacing,"minimum_linearized_spacing_residual":min_linear,
        "conditional_on_historical_single_coordinate_order":True,
        "historical_producer_or_input_authenticated":False,"solver_rerun":False,
        "float_gap_is_interval_certificate":False,"same_source_floating_gap_check_not_rigorous":True,"full_physical_validation":False,"full_figure_or_paper_pass":False}
