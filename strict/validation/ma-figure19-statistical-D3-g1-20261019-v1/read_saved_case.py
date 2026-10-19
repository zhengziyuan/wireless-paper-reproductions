"""Portable saved-state audit of only statistical Fig19 D3/g1; JSON only.

No optimizer, grid enumeration, FPA solve, Monte Carlo draw, or RNG is called.
The physical formulas and the complete fixed-state math block are frozen.
"""
from pathlib import Path
import argparse,gzip,hashlib,importlib.util,json,math,sys,traceback
ROOT=Path(__file__).resolve().parent
ORACLE_SHA="9db2b29a4d2235122feb3438c2a47ffe8fdebfce738b6bf3779c4d0a7cc2b81d"
SAMPLE_ATOL=1e-7
MEAN_ATOL=DESIGN_ATOL=1e-9

def sha(raw):return hashlib.sha256(raw).hexdigest()
def need(value,message):
    if not value:raise ValueError(message)

def execute(a):
    need(sys.dont_write_bytecode and not sys.flags.optimize,"Use -X utf8 -B without -O")
    out=a.output_dir.resolve();need(not out.exists() and not out.is_relative_to(ROOT),"Fresh output outside this capsule required")
    files={}
    def read(p):
        p=Path(p).resolve();need(p.is_relative_to(ROOT),"Only this capsule is read")
        raw=p.read_bytes();files[str(p)]={"SHA256":sha(raw),"bytes":len(raw)};return raw
    manifest=json.loads(read(ROOT/"MANIFEST.json"))
    for rel,identity in manifest["files"].items():
        raw=read(ROOT/rel);need(sha(raw)==identity["SHA256"] and len(raw)==identity["bytes"],"Public source/input identity differs: "+rel)
    fixture=json.loads(gzip.decompress(read(ROOT/"selected-case-and-evidence.json.gz")))
    inputs=fixture["original_input_UTF8"]
    for key,text in inputs.items():need(sha(text.encode())==fixture["input_original_identities"][key]["original_SHA256"],"Exact original input UTF8 differs")
    job=json.loads(inputs["selected_job"]);cfg=json.loads(inputs["execution_configuration"])
    fp=sha(b"strict-v1\0"+inputs["original_configuration"].encode()+b"\0"+inputs["selected_job"].encode())
    result=fixture["records"]["actual_result"];closed=fixture["records"]["original_closed_result"];binding=result["binding"]
    need(fp==binding["original_input_fingerprint"] and binding==closed["binding"],"Selected original input/result binding differs")
    need(closed["result_SHA256"]==fixture["original_record_identities"]["actual_result"]["original_SHA256"],"Original closed/result digest relationship differs")
    need(result["source_before"]==result["source_after"] and result["source_before"],"Recorded producer source interval differs")
    n,m=4,3;figure=19;need((job["figure"],job["point"],job["realization"],job["N"],job["M"])==(19,3,1,4,3),"Only actual D3/g1 selected case")
    need(cfg["brute_force_objective"]=="paper_statistical_design_objective" and cfg["nlos_realizations_per_geometry"]==1000,"Exact theory target/full1000 controls")
    a.case_dir=Path("selected-fixture-case")
    def js(p):
        p=Path(p);need(p.parent.name in ("grid-MRT","grid-ZF") and p.name in ("checkpoint.json","binding.json"),"No extra saved source")
        return fixture["grid_checkpoints"][p.parent.name[5:]][p.stem]
    out.mkdir(parents=True,exist_ok=False)
    report=dict(schema="portable-one-closed-statistical-grid-fixed-state-readback-v1",complete=False,errors=[],figure=figure,D=3,geometry=1,input_fingerprint=fp,producer_scoped_checks=closed["checks"],producer_scoped_pass=closed["scoped_numerical_pass"],producer_failure=closed["failure"],optimizer_search_FPA_MCdraw_RNG_calls=0,independent_precision="Existing independent binary64 physical reference; no MP/interval/global-search proof",historical_author_criterion_recovered=False,independent_global_optimality_or_earliest_tie_replayed=False,independent_FPA_KKT_or_gradient_pass=False,dual_language_reference_or_full_axis_pass=False)
    dest=out/"ACTUAL_PORTABLE_ONE_CLOSED_STATISTICAL_D3_G1_SAVED_STATE_READBACK_V1.json"
    try:
        oraclepath=ROOT/"sources"/"independent_saved_physics.py"
        need(sha(read(oraclepath))==ORACLE_SHA,"Frozen independent physics source changed")
        read(Path(__file__))
        spec=importlib.util.spec_from_file_location("_portable_saved_statistical_geometry",oraclepath)
        oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
        import numpy as np
        initial,_,_,draws,noise,channel,design=oracle.geometry_functions(job,cfg)
        need(draws.shape==(1000,n,m) and np.isfinite(draws).all(),"All actual1000 finite fixed draws required")
        lower=np.asarray(job["region_lower"],float);upper=np.asarray(job["region_upper"],float)
        baseline=result["original_five_component_record"];physics={};stops={};searches={}
        def feasible(t):
            distances=np.linalg.norm(t[:,None]-t[None,:],axis=2)+np.eye(n)*1e9
            return dict(shape_finite=bool(t.shape==(n,2) and np.isfinite(t).all()),minimum_spacing=float(distances.min()),spacing_pass=bool(distances.min()>=.5-cfg["verification_tolerance"]),box_pass=bool(np.all(t>=lower-cfg["verification_tolerance"]) and np.all(t<=upper+cfg["verification_tolerance"])))
        for mode in ("MRT","ZF"):
            key=mode.lower();hist=baseline["history"][key]
            pos=np.asarray(hist["positions"],float);values=np.asarray(hist["objective"],float)
            need(len(values)>=2 and pos.shape==(len(values),n,2) and np.isfinite(pos).all() and np.isfinite(values).all(),"Complete finite original MA history required")
            need(np.array_equal(pos[0],initial) and np.array_equal(pos[-1],baseline["ma"][key]["positions"]) and np.array_equal(pos[-1],baseline["ma"][key]["realized_positions"]),"Original MA initial/final identities differ")
            sweeps=len(values)-1;updates=hist["coordinate_updates"]
            need(len(updates)==n*sweeps and all((x["sweep"],x["antenna"])==divmod(i,n) for i,x in enumerate(updates)),"Original ordered coordinate counts differ")
            need(np.all(abs(values[:-1])>0),"Do not invent zero-objective fractional stop")
            rel=np.diff(values)/abs(values[:-1]);below=rel<cfg["fractional_increase_threshold"]
            conv=hist["converged"];need(type(conv) is bool,"Explicit original convergence flag required")
            consistent=sweeps<=cfg["maximum_AO_iterations"] and not bool(np.any(below[:-1])) and (bool(below[-1]) and hist["termination"]=="fractional_increase" if conv else sweeps==cfg["maximum_AO_iterations"] and not bool(below[-1]) and hist["termination"]=="configured_iteration_cap")
            independent_last=np.asarray([design(t,key) for t in pos[-2:]])
            need(np.isfinite(independent_last).all(),"Nonfinite independent design state retained as failure")
            err=float(np.max(abs(independent_last-values[-2:])))
            stops[mode]=dict(original_converged=conv,original_termination=hist["termination"],accepted_sweeps=sweeps,source_cap=cfg["maximum_AO_iterations"],first_source_stop_fields_consistent=bool(consistent),independent_last_two_design_objectives=independent_last.tolist(),maximum_last_two_design_error=err,last_two_design_pass=bool(np.isfinite(independent_last).all() and err<=DESIGN_ATOL),earlier_objectives_not_recomputed=True)
            bf=result["metrics"]["brute_force"][mode]
            for kind,t,stored in (("MA-final",pos[-1],baseline["schemes"]["MA-"+mode]),("statistical-grid-winner",np.asarray(bf["positions"],float),bf["MC"])):
                need(t.shape==(n,2) and np.isfinite(t).all(),"Finite actual saved geometry required")
                rates,powers=oracle.ma_rates(channel(t),job["power"],noise,key)
                sr=np.asarray(stored["sample_sum_rates"],float);sp=np.asarray(stored["powers"],float)
                need(rates.shape==powers.shape==sr.shape==sp.shape==(1000,),"All1000 saved sample arrays required")
                finite=all(np.isfinite(x).all() for x in (rates,powers,sr,sp)) and math.isfinite(stored["mean_sum_rate"])
                need(finite,"Nonfinite saved/independent sample or power retained as failure")
                sample_error=float(np.max(abs(rates-sr)));mean_error=abs(float(np.mean(rates))-stored["mean_sum_rate"]);power_error=float(np.max(abs(powers-sp)));geo=feasible(t)
                physics[mode+"-"+kind]=dict(geometry=geo,maximum_sample_rate_error=sample_error,mean_error=mean_error,maximum_power_error=power_error,maximum_independent_power=float(np.max(powers)),independent_sample_sum_rates=rates.tolist(),independent_total_powers=powers.tolist(),sample_tolerance=SAMPLE_ATOL,mean_power_tolerance=MEAN_ATOL,passed=bool(finite and all(geo[x] for x in ("shape_finite","spacing_pass","box_pass")) and sample_error<=SAMPLE_ATOL and mean_error<=MEAN_ATOL and power_error<=MEAN_ATOL and np.max(powers)<=job["power"]+MEAN_ATOL))
            search=bf["search"];checkpoint=js(a.case_dir/("grid-"+mode)/"checkpoint.json");gridbinding=js(a.case_dir/("grid-"+mode)/"binding.json")
            grid=np.array([[x,y] for x in np.linspace(lower[0],upper[0],job["point"]) for y in np.linspace(lower[1],upper[1],job["point"])])
            indices=bf["canonical_indices"];basis=search["actual_frozen_model"]
            counts=(search["complete"] is True and checkpoint["complete"] is True and not checkpoint["stack"] and search["mode"]==mode and search["D"]==job["point"] and search["N"]==n and indices==checkpoint["winner"] and indices==sorted(indices) and len(set(indices))==n and np.array_equal(grid[indices],bf["positions"]) and checkpoint["best"]==search["exact_product"] and checkpoint["leaves"]==search["evaluated_feasible_geometries"] and checkpoint["prunes"]==search["certified_pruned_subtrees"] and checkpoint["nodes"]==search["nodes"] and checkpoint["decision_digest"]==search["decision_digest"] and checkpoint["certificate_chain"]==search["certificate_chain"] and gridbinding["actual_frozen_model"]==basis and all(gridbinding[k]==v for k,v in binding.items()))
            pointvalue=float(design(np.asarray(bf["positions"],float),key))
            need(math.isfinite(pointvalue) and math.isfinite(search["objective"]),"Nonfinite saved/independent statistical value retained as failure")
            error=abs(pointvalue-search["objective"])
            searches[mode]=dict(actual_saved_search=search,checkpoint_counts_winner_and_basis_consistent=bool(counts),independent_saved_winner_Eq13_or_Eq39=pointvalue,stored_statistical_objective=search["objective"],fixed_point_absolute_error=error,fixed_point_objective_pass=math.isfinite(pointvalue) and error<=DESIGN_ATOL,objective_tolerance=DESIGN_ATOL,global_certificate_stream_not_read_or_replayed=True)
        report.update(complete=True,physics=physics,original_MA_stops=stops,statistical_winner_fixed_point_and_checkpoint=searches,all_four_fixed_geometries_physics_pass=all(x["passed"] for x in physics.values()),all_original_MA_stop_fields_and_last_two_values_consistent=all(x["first_source_stop_fields_consistent"] and x["last_two_design_pass"] for x in stops.values()),both_original_MA_converged=all(x["original_converged"] for x in stops.values()),both_statistical_saved_points_and_checkpoint_metadata_pass=all(x["checkpoint_counts_winner_and_basis_consistent"] and x["fixed_point_objective_pass"] for x in searches.values()),FPA_only_original_fields_retained_not_independently_recomputed=True)
    except BaseException as e:report["errors"].append(dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()))
    finally:
        after={}
        for p in files:
            try:
                raw=Path(p).read_bytes();after[p]={"SHA256":sha(raw),"bytes":len(raw)}
            except BaseException as e:after[p]=None;report["errors"].append(dict(stage="source_input_postread",path=p,type=type(e).__name__,message=str(e)))
        report["source_and_selected_input_before"]=files;report["source_and_selected_input_after"]=after;report["source_and_input_interval_pass"]=files==after
        report["all_scoped_fixed_state_readback_checks_pass"]=bool(report["complete"] and not report["errors"] and files==after and all(report.get(k) is True for k in ("all_four_fixed_geometries_physics_pass","all_original_MA_stop_fields_and_last_two_values_consistent","both_statistical_saved_points_and_checkpoint_metadata_pass")))
        dest.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(dict(report=str(dest),scoped_pass=report["all_scoped_fixed_state_readback_checks_pass"],errors=report["errors"])))
    return 0 if report["all_scoped_fixed_state_readback_checks_pass"] else 2

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output-dir",type=Path,required=True);p.add_argument("--execute",action="store_true",required=True)
    raise SystemExit(execute(p.parse_args()))
