"""Full-budget figure executor; separate component tests never count as figure runs."""
from __future__ import annotations
import argparse, json, math, hashlib, sys, os
from pathlib import Path
import numpy as np
from engine import Model, communication_solve, sensing_solve, closed_form, check_gradient, simplex, serialize

HERE=Path(__file__).resolve().parent
PAPER_ID=HERE.name
class PortableRandom:
    def __init__(self,seed): self.state=int(seed)
    def values(self,n):
        out=np.empty(n)
        for i in range(n):
            self.state=(16807*self.state)%2147483647
            out[i]=self.state/2147483647
        return out

def initialize(model,settings,rng):
    X=rng.values(model.targets*model.U).reshape(model.targets,model.U)
    X/=np.sum(X,axis=1,keepdims=True)
    z={"phi":np.exp(2j*np.pi*rng.values(model.M)),"theta":np.exp(2j*np.pi*rng.values(model.N)),"X":X}
    if settings["kind"]=="sensing": z["eta"]=np.asarray(settings["initialization"]["eta_initial"])
    return z

def make_model(point,settings,pslr=False):
    if settings["kind"]=="communications":
        K=point["K"]
        az=np.linspace(-60,60,K) if K>1 else np.array([0.])
        el=np.full(K,45.)
    else:
        kp,kt=point["Kphi"],point["Ktheta"]
        azimuth=np.linspace(30,70,kp) if kp>1 else np.array([50.])
        elevation=(np.arange(kt)+.5)*90/kt
        az=np.repeat(azimuth,kt); el=np.tile(elevation,kp); K=len(az)
    cfg=dict(ms1=point["ms1"],ms2=point["ms2"],azimuth_deg=az.tolist(),elevation_deg=el.tolist(),
             spacing_over_wavelength=settings["spacing_over_wavelength"],
             incidence_direction_cosines=settings["incidence_direction_cosines"],
             number_of_targets=K,reference_snr=settings.get("reference_snr",.01))
    if settings["kind"]=="sensing":
        cfg["echo_beta_squared"]=10**(settings["reference_echo_db"]/10)
        cfg["noise_over_power"]=1/(10**((point.get("power_dbm",settings["power_dbm"])-30)/10))
    if pslr:
        gp,gt=settings["pslr_grid"]
        caz=np.repeat(np.linspace(30,70,gp),gt)
        cel=np.tile((np.arange(gt)+.5)*90/gt,gp)
        cfg["azimuth_deg"]+=caz.tolist(); cfg["elevation_deg"]+=cel.tolist()
        beta=np.full(K+gp*gt,10**(settings["reference_echo_db"]/10))
        beta[K:]*=settings["clutter_relative_echo"]
        cfg["echo_beta_squared"]=beta.tolist()
        cfg["pslr_opponents"]=[]
        for k in range(K):
            outside=np.hypot(caz-az[k],cel-el[k])>settings["mainlobe_guard_deg"]
            cfg["pslr_opponents"].append([i for i in range(K) if i!=k]+(K+np.flatnonzero(outside)).tolist())
        cfg["pslr_mu"]=settings["pslr_mu_initial"]
        cfg["pslr_epsilon"]=settings["pslr_epsilon"]
    return Model(cfg)

def solver_options(settings):
    rcg=dict(settings["line_search"],max_iterations=settings["rcg_max_iterations"])
    if settings["kind"]=="communications":
        rcg["gradient_tolerance"]=settings["rcg_gradient_tolerance"]
        return dict(rcg=rcg,initial_mu=settings["initial_mu_values"][0],terminal_mu=settings["terminal_mu"],
                    objective_convention=settings["objective_convention"])
    return dict(rcg=rcg,outer_iterations=settings["outer_iterations"],
                epsilon_initial=settings["epsilon_initial"],epsilon_min=settings["epsilon_min"],
                rho_initial=settings["rho_initial"],rho_factor=settings["rho_factor"],
                iota_progress_ratio=settings["iota_progress_ratio"],
                lambda_initial=settings["initialization"]["lambda_initial"],
                lambda_min=settings["lambda_min"],lambda_max=settings["lambda_max"],
                minimum_step=settings["minimum_step"],outer_stopping_logic=settings["outer_stopping_logic"])

def atomic_json(path,value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(value),encoding="utf-8"); tmp.replace(path)

def implementation_digest():
    files=sorted(list(HERE.glob("*.py"))+list(HERE.glob("*.m"))+[HERE/"source_map.json"],key=lambda x:x.name)
    manifest={file.name:hashlib.sha256(file.read_bytes()).hexdigest() for file in files}
    runtime={"python":sys.version.split()[0],"numpy":np.__version__,"cpu_count":os.cpu_count(),
             "thread_environment":{v:os.environ.get(v) for v in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS")}}
    return hashlib.sha256(json.dumps({"source":manifest,"runtime":runtime},sort_keys=True).encode()).hexdigest(),{"source":manifest,"runtime":runtime}

def solver_diagnostics(history,settings,objective):
    """Differentiate finite execution, feasibility, inner and outer stopping."""
    comm=settings["kind"]=="communications"
    groups=[history] if comm or objective!="pslr" else [stage["outer"] for stage in history]
    entries=[x for group in groups for x in group]
    guarded=settings["line_search"].get("non_descent_policy","literal_printed")=="documented_non_descent_restart"
    key="projected_kkt_norm" if guarded else "gradient_norm"
    tolerances=[settings["rcg_gradient_tolerance"] if comm else x["epsilon_used"] for x in entries]
    norms=[x["stop"][key] for x in entries]
    stationary=[bool(np.isfinite(n) and n<=t) for n,t in zip(norms,tolerances)]
    reasons=[x["stop"]["reason"] for x in entries]
    if comm:
        outer_met=True
        continuation_complete=bool(history and history[-1]["mu"]*.5<settings["terminal_mu"])
    else:
        decisions=[]
        for group in groups:
            stepstop=group[-1]["step"]<=settings["minimum_step"]
            epsstop=group[-1]["epsilon_next"]<=settings["epsilon_min"]
            decisions.append((stepstop or epsstop) if settings["outer_stopping_logic"]=="algorithm_OR" else (stepstop and epsstop))
        outer_met=bool(all(decisions));continuation_complete=True
    failed=sum("line_search" in r or "non_descent" in r or "zero_projected" in r for r in reasons)
    return {"final_inner_stationary":stationary[-1],"all_inner_tolerances_satisfied":all(stationary),
            "final_inner_residual":float(norms[-1]),"final_inner_tolerance":float(tolerances[-1]),
            "outer_stopping_applicable":not comm,"outer_stopping_met":outer_met,
            "continuation_complete":continuation_complete,"inner_iteration_cap_exits":reasons.count("iteration_cap"),
            "inner_failure_exits":failed,"convergence_verified":bool(all(stationary) and outer_met and continuation_complete and not failed),
            "final_inner_exit_reason":reasons[-1]}

def optimize(model,settings,objective,seed_offset=0,checkpoint_path=None):
    rng=PortableRandom(settings["initialization"]["seed"]+seed_offset)
    options=solver_options(settings)
    summaries=[]; best=None; mean_outer=np.zeros(settings.get("outer_iterations",1)); mean_violation=np.zeros_like(mean_outer); counts=np.zeros_like(mean_outer)
    source_digest,source_manifest=implementation_digest()
    signature=hashlib.sha256(json.dumps({"schema_version":2,"implementation_digest":source_digest,"settings":settings,"model":model.config,"objective":objective,"seed_offset":seed_offset},sort_keys=True).encode()).hexdigest()
    checkpoint=Path(checkpoint_path) if checkpoint_path is not None else None
    bestpath=checkpoint.with_suffix(".best.json") if checkpoint is not None else None
    if checkpoint is not None and checkpoint.exists():
        saved=json.loads(checkpoint.read_text())
        if saved.get("schema_version")!=2 or saved.get("implementation_digest")!=source_digest:
            raise ValueError("Legacy/different implementation checkpoint rejected; preserve it and use a new output directory")
        if saved["signature"]!=signature: raise ValueError("Checkpoint settings/model differ; choose a new output path")
        summaries=saved["all_start_summaries"]; rng.state=saved["random_state"]
        mean_outer=np.array(saved["mean_outer_sum"]); mean_violation=np.array(saved["mean_violation_sum"]); counts=np.array(saved["mean_outer_counts"])
        if saved["has_best"]: best=json.loads(bestpath.read_text())
    for start in range(len(summaries),settings["number_of_starts"]):
        z=initialize(model,settings,rng)
        if settings["kind"]=="communications":
            options["initial_mu"]=settings["initial_mu_values"][start%len(settings["initial_mu_values"])]
            z,h,metrics=communication_solve(model,z,options)
            feasible=True; score=metrics["min_binary_snr"]
        else:
            if objective=="pslr":
                mu=settings["pslr_mu_initial"]; stages=[]
                while mu>=settings["pslr_mu_terminal"]:
                    model.config["pslr_mu"]=mu
                    z,h,metrics=sensing_solve(model,z,options,objective)
                    stages.append({"mu":mu,"outer":h})
                    mu*=settings["pslr_mu_factor"]
                h=stages
            else:
                z,h,metrics=sensing_solve(model,z,options,objective)
                for j in range(settings["outer_iterations"]):
                    x=h[min(j,len(h)-1)]
                    # Hold terminated final state; never substitute an incumbent.
                    mean_outer[j]+=x["eta"]
                    mean_violation[j]+=max(0,max(x["q"]))
                    counts[j]+=1
            feasible=metrics["maximum_constraint"]<=settings["feasibility_tolerance"]
            score=metrics["eta"]
        diagnostic=solver_diagnostics(h,settings,objective)
        binary_feasible=bool(settings["kind"]=="communications" or metrics["eta"]-metrics["min_binary_metric"]<=settings["feasibility_tolerance"])
        status="converged_feasible" if feasible and diagnostic["convergence_verified"] else ("feasible_not_convergence_verified" if feasible else "infeasible")
        summaries.append({"start":start+1,"feasible":bool(feasible),"binary_eta_feasible":binary_feasible,
                          "score":float(score),"solver_status":diagnostic,"exit_status":status,
                          "min_binary_metric":metrics.get("min_binary_metric",metrics.get("min_binary_snr"))})
        if feasible and (best is None or score>best["score"]):
            best=dict(score=float(score),start=start+1,metrics=metrics,history=h,state=serialize(z),solver_status=diagnostic,binary_eta_feasible=binary_feasible)
            if bestpath is not None: atomic_json(bestpath,best)
        if checkpoint is not None:
            atomic_json(checkpoint,{"schema_version":2,"implementation_digest":source_digest,"source_manifest":source_manifest,"signature":signature,"completed_starts":len(summaries),"random_state":rng.state,
                        "all_start_summaries":summaries,"mean_outer_sum":mean_outer.tolist(),"mean_violation_sum":mean_violation.tolist(),
                        "mean_outer_counts":counts.tolist(),"has_best":best is not None})
    complete=len(summaries)==settings["number_of_starts"]
    certified=bool(complete and best is not None and best["solver_status"]["convergence_verified"] and best["binary_eta_feasible"])
    return {"implementation_digest":source_digest,"source_manifest":source_manifest,"best_feasible":best,"all_start_summaries":summaries,
            "full_start_budget_execution_complete":complete,"selected_best_convergence_verified":certified,
            "overall_full_success":certified,"original_figure_reproduction_certified":False,
            "mean_outer_eta":np.divide(mean_outer,counts,out=np.zeros_like(mean_outer),where=counts>0).tolist(),
            "mean_outer_violation":np.divide(mean_violation,counts,out=np.zeros_like(mean_violation),where=counts>0).tolist(),
            "mean_outer_counts":counts.astype(int).tolist(),"number_of_starts":settings["number_of_starts"]}

def evaluate_closed(model):
    try:
        z=closed_form(model)
    except ValueError as error:
        return {"available":False,"reason":str(error)}
    metric=model.metric(z,"sinr")
    mr,mc=model.config["ms1"]; nr,nc=model.config["ms2"]; ur,uc=mr-nr+1,mc-nc+1
    d=model.config["spacing_over_wavelength"]; A=np.pi/d*max(1/(ur-1),1/(uc-1))
    az=np.deg2rad(model.config["azimuth_deg"][:model.targets]); el=np.deg2rad(model.config["elevation_deg"][:model.targets])
    # Original continuous steering law; explicit orientation + nearest-index rounding.
    row=np.clip(np.floor((ur-1)-np.pi/(A*d)*np.sin(el)*np.cos(az)+.5),0,ur-1).astype(int)
    col=np.clip(np.floor((uc-1)-np.pi/(A*d)*np.sin(el)*np.sin(az)+.5),0,uc-1).astype(int)
    chosen=row*uc+col
    z["X"]=np.zeros_like(z["X"]); z["X"][np.arange(model.targets),chosen]=1
    return {"available":True,"minimum_sinr":float(np.min(metric[np.arange(model.targets),chosen])),
            "selected_positions":chosen.tolist(),"state":serialize(z)}

def beampattern_samples(model,state,selected):
    """Whole front hemisphere, 1-degree sampling; plotting resolution is inferred."""
    az=np.arange(-180,181,dtype=float); el=np.arange(0,91,dtype=float)
    cfg=dict(model.config,azimuth_deg=np.repeat(az,len(el)).tolist(),elevation_deg=np.tile(el,len(az)).tolist(),
             echo_beta_squared=1,number_of_targets=len(az)*len(el))
    grid=Model(cfg)
    z={"phi":np.array(state["phi"]["real"])+1j*np.array(state["phi"]["imag"]),
       "theta":np.array(state["theta"]["real"])+1j*np.array(state["theta"]["imag"])}
    powers=grid.fields(z)[3]
    original=model.fields(z)[3]; echo=model.beta[:model.targets,None]*original[:model.targets]**2
    maps=[]
    for k,u in enumerate(selected):
        raw=powers[:,u].reshape(len(az),len(el)).T
        denominator=np.sum(echo[:,u])-echo[k,u]+model.config["noise_over_power"]
        maps.append({"target":k,"pattern":int(u),"normalized_gain":(raw/np.max(raw)).tolist(),
                     "sinr":(model.beta[k]*raw*raw/denominator).tolist()})
    return {"scope":"full_front_hemisphere_independent_samples","resolution_deg":1,
            "azimuth_deg":az.tolist(),"elevation_deg":el.tolist(),"maps":maps}

def ris_baselines(model,settings,checkpoint_prefix=None):
    out={}
    continuous=[]; quantized={1:[],2:[]}; converged=[]
    for k in range(model.targets):
        order=[k]+[j for j in range(model.targets) if j!=k]
        cfg=dict(model.config,ms2=[0,0],number_of_targets=1,
                 azimuth_deg=[model.config["azimuth_deg"][j] for j in order],
                 elevation_deg=[model.config["elevation_deg"][j] for j in order])
        cfg["echo_beta_squared"]=np.broadcast_to(model.config["echo_beta_squared"],(model.targets,))[order].tolist()
        ris=Model(cfg)
        ck=None if checkpoint_prefix is None else Path(str(checkpoint_prefix)+"-ris-target-"+str(k)+".json")
        run=optimize(ris,settings,"sinr",seed_offset=100000+k,checkpoint_path=ck)
        if run["best_feasible"] is None:
            return {"available":False,"reason":"At least one independently optimized RIS target has no feasible run"}
        converged.append(run["overall_full_success"])
        raw=run["best_feasible"]["state"]["phi"]
        phi=np.array(raw["real"])+1j*np.array(raw["imag"])
        z={"phi":phi,"theta":np.empty(0,dtype=complex),"X":np.ones((1,1)),"eta":np.asarray(0.)}
        continuous.append(float(ris.metric(z,"sinr")[0,0]))
        for bits in (1,2):
            step=2*np.pi/(2**bits)
            # floor(a+0.5), not language-dependent bankers rounding.
            z["phi"]=np.exp(1j*step*np.floor(np.angle(phi)/step+.5))
            quantized[bits].append(float(ris.metric(z,"sinr")[0,0]))
    return {"available":True,"optimization_convergence_verified":all(converged),"continuous":continuous,"one_bit":quantized[1],"two_bit":quantized[2]}

def component_test(guarded=False):
    fixture=json.loads((HERE/"unit_fixture.json").read_text())
    model=Model(fixture["model"])
    z={"phi":np.exp(1j*np.array(fixture["phi_angles"])),"theta":np.exp(1j*np.array(fixture["theta_angles"])),
       "X":np.array(fixture["X"]),"eta":np.asarray(fixture["eta"])}
    opts=dict(fixture["unit_options"])
    if guarded:
        opts.update(line_search_policy="original_per_block_backtracking",non_descent_policy="documented_non_descent_restart")
    if PAPER_ID=="mis-communications":
        z.pop("eta")
        evaluate=lambda x:model.communication_objective(x,1.3,"maximize_negative_softmin")
        errors=check_gradient(z,evaluate)
        z,h,metrics=communication_solve(model,z,dict(rcg=opts,initial_mu=1.3,terminal_mu=.65,objective_convention="maximize_negative_softmin"))
    else:
        evaluate=lambda x:model.augmented(x,np.array([.31,.21,.27]),1.7,"sinr")
        errors=check_gradient(z,evaluate)
        options=dict(rcg=opts,outer_iterations=3,epsilon_initial=1e-3,epsilon_min=1e-6,
                     rho_initial=1,rho_factor=1.2,iota_progress_ratio=.8,lambda_initial=0,
                     lambda_min=0,lambda_max=1e10,minimum_step=1e-10,outer_stopping_logic="numerical_text_AND")
        z,h,metrics=sensing_solve(model,z,options)
    bar,v,q,a=model.fields(z)
    reconstructed=np.zeros_like(a)
    for k in range(model.K):
        G=np.outer(np.conj(model.c[k]),model.c[k])
        for u in range(model.U):
            reconstructed[k,u]=np.real(np.conj(v[u])@G@v[u])
    identity=float(np.max(np.abs(a-reconstructed))/max(1,float(np.max(a))))
    loop_q=np.array([[sum(model.c[k,m]*v[u,m] for m in range(model.M)) for u in range(model.U)] for k in range(model.K)])
    geometry=model.config["ms1"]; movable=model.config["ms2"]
    checks={"gradient_errors":errors,"gradient_pass":max(errors.values())<1e-6,
            "ordinary_transpose_amplitude_error":float(np.max(np.abs(q-loop_q))/max(1,float(np.max(np.abs(q))))),
            "quadratic_identity_error":identity,"quartic_echo_identity_error":float(np.max(np.abs(a*a-reconstructed*reconstructed))/max(1,float(np.max(a*a)))),
            "number_of_positions_correct":model.U==(geometry[0]-movable[0]+1)*(geometry[1]-movable[1]+1),
            "constraint_pass":bool(np.max(np.abs(np.abs(z["phi"])-1))<1e-12 and
                                   np.max(np.abs(np.abs(z["theta"])-1))<1e-12 and
                                   np.max(np.abs(np.sum(z["X"],axis=1)-1))<1e-12 and np.min(z["X"])>=0)}
    if guarded:
        from test_line_search import line_search_checks
        checks["production_line_search_regression"]=line_search_checks()
    if PAPER_ID=="mis-sensing":
        last_lambda=np.zeros(model.targets); last_iota=None; penalty_error=0.; multiplier_error=0.; iota_error=0.; epsilon_error=0.
        for j,x in enumerate(h):
            residual=np.array(x["q"]); rho=x["rho_used"]
            ii=np.maximum(residual,-last_lambda/rho)
            ll=np.clip(last_lambda+rho*residual,0,1e10)
            rr=rho if j==0 or max(ii)<=.8*max(last_iota) else 1.2*rho
            penalty_error=max(penalty_error,abs(rr-x["rho_next"]))
            multiplier_error=max(multiplier_error,float(np.max(np.abs(ll-x["lambda"]))))
            iota_error=max(iota_error,float(np.max(np.abs(ii-x["iota"]))))
            epsilon_error=max(epsilon_error,abs(max(1e-6,(1e-6/1e-3)**(1/3)*x["epsilon_used"])-x["epsilon_next"]))
            last_lambda=ll; last_iota=ii
        checks["ralm_update_errors"]={"penalty":penalty_error,"multipliers":multiplier_error,"iota":iota_error,"epsilon":epsilon_error}
        checks["ralm_update_pass"]=max(penalty_error,multiplier_error,iota_error,epsilon_error)<1e-12
        checkmodel=Model(dict(fixture["model"],azimuth_deg=[32,51,68,44,61],elevation_deg=[18,46,76,31,59],
                             number_of_targets=3,pslr_opponents=[[1,2,3,4],[0,2,3,4],[0,1,3,4]],
                             pslr_mu=.7,pslr_epsilon=1e-9))
        pg=check_gradient({"phi":np.exp(1j*np.array(fixture["phi_angles"])),"theta":np.exp(1j*np.array(fixture["theta_angles"])),
                           "X":np.array(fixture["X"]),"eta":np.asarray(.4)},
                           lambda x:checkmodel.augmented(x,np.array([.31,.21,.27]),1.7,"pslr"))
        checks["pslr_gradient_errors"]=pg; checks["pslr_gradient_pass"]=max(pg.values())<1e-6
    return {"paper_id":PAPER_ID,"scope":"component_unit_test_not_paper_figure","solver_policy":opts,
            "metrics":metrics,"checks":checks,"history":h,"state":serialize(z)}

def diagnostic_start(figure,settings,start,point_index=0):
    """One original full-size/per-start-budget diagnostic, never a full figure."""
    if settings["number_of_starts"]!=6000 or settings["rcg_max_iterations"]!=4000 or (settings["kind"]=="sensing" and settings["outer_iterations"]!=30):
        raise ValueError("Full-size start diagnostics retain original full per-start budgets; use separate component tests for reductions")
    if start<1 or start>settings["number_of_starts"]:raise ValueError("Diagnostic start index outside full original start bank")
    point=figure["points"][point_index];objective=figure["objective"]
    if objective=="closed_form_sinr":raise ValueError("Closed form has no stochastic optimizer start")
    model=make_model(point,settings,pslr=objective=="pslr")
    rng=PortableRandom(settings["initialization"]["seed"]+point_index*1000)
    for _ in range(start):z=initialize(model,settings,rng)
    options=solver_options(settings)
    if settings["kind"]=="communications":
        options["initial_mu"]=settings["initial_mu_values"][(start-1)%len(settings["initial_mu_values"])]
        z,h,metrics=communication_solve(model,z,options)
    elif objective=="pslr":
        mu=settings["pslr_mu_initial"];h=[]
        while mu>=settings["pslr_mu_terminal"]:
            model.config["pslr_mu"]=mu;z,outer,metrics=sensing_solve(model,z,options,objective)
            h.append({"mu":mu,"outer":outer});mu*=settings["pslr_mu_factor"]
    else:z,h,metrics=sensing_solve(model,z,options,objective)
    source,manifest=implementation_digest()
    return {"paper_id":PAPER_ID,"scope":"single_original_full_start_diagnostic_not_full_figure",
            "figure":figure["id"],"start":start,"original_number_of_starts":settings["number_of_starts"],
            "configuration":point,"settings":settings,"metrics":metrics,"solver_status":solver_diagnostics(h,settings,objective),
            "history":h,"state":serialize(z),"implementation_digest":source,"source_manifest":manifest}

def figure_execution_status(points,full_count):
    complete=len(points)==full_count; verified=complete
    for entry in points:
        run=entry["result"]
        if "available" in run:
            ok=bool(run["available"] and np.isfinite(run.get("minimum_sinr",np.nan)));complete=complete and ok;verified=verified and ok
        else:
            complete=complete and run.get("full_start_budget_execution_complete",False)
            verified=verified and run.get("overall_full_success",False)
        for name in ("SMS","RALM_reference"):
            if name in entry:
                complete=complete and entry[name].get("full_start_budget_execution_complete",False)
                verified=verified and entry[name].get("overall_full_success",False)
        if "RIS" in entry:
            complete=complete and entry["RIS"].get("available",False)
            verified=verified and entry["RIS"].get("optimization_convergence_verified",False)
    return {"full_figure_execution_complete":bool(complete),"overall_full_success":bool(verified),
            "original_figure_reproduction_certified":False}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--component-test",action="store_true")
    parser.add_argument("--guarded-component-test",action="store_true",help="Independent block-alpha safeguard component, never a figure run")
    parser.add_argument("--figure")
    parser.add_argument("--point",type=int,help="One full-sized point, zero-based; never changes starts/iterations")
    parser.add_argument("--diagnostic-start",type=int,help="One original-size start with original per-start budgets; explicitly NOT a full-figure run")
    parser.add_argument("--settings",type=Path,default=HERE/"settings.json")
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--dry-run",action="store_true")
    args=parser.parse_args()
    if args.component_test or args.guarded_component_test:
        result=component_test(args.guarded_component_test)
    else:
        settings=json.loads(args.settings.read_text())
        figures=json.loads((HERE/"figures.json").read_text())
        if args.figure is None:
            raise SystemExit("Select --figure figN; no reduced default exists")
        figure=next(x for x in figures if x["id"]==args.figure)
        if args.dry_run:
            result={"paper_id":PAPER_ID,"figure":figure,"settings":settings,"scope":"full_plan_no_execution",
                    "possible_inner_iterations_per_sensing_point":6000*30*4000}
        elif args.diagnostic_start is not None:
            result=diagnostic_start(figure,settings,args.diagnostic_start,0 if args.point is None else args.point)
        else:
            if settings["number_of_starts"]!=6000 or settings["rcg_max_iterations"]!=4000 or (settings["kind"]=="sensing" and settings["outer_iterations"]!=30):
                raise ValueError("Full figure execution must retain strict full start/iteration budgets; reduced component tests are separate.")
            points=figure["points"] if args.point is None else [figure["points"][args.point]]
            result={"paper_id":PAPER_ID,"figure":figure["id"],"scope":"full_size_full_budget_independent_reimplementation",
                    "settings":settings,"inferred_or_tuned":settings["inferred_or_tuned"],"points":[]}
            for j,point in enumerate(points):
                point_index=j if args.point is None else args.point
                prefix=args.output.with_suffix("").parent/(args.output.stem+"_checkpoints")/("point-"+str(point_index)+"-python")
                model=make_model(point,settings,pslr=figure["objective"]=="pslr")
                if figure["objective"]=="closed_form_sinr":
                    run=evaluate_closed(model)
                else:
                    run=optimize(model,settings,figure["objective"],seed_offset=point_index*1000,checkpoint_path=str(prefix)+"-main.json")
                entry={"configuration":point,"result":run}
                if figure["id"] in ("fig2","fig3","fig4") and settings["kind"]=="sensing":
                    if figure["objective"]=="closed_form_sinr" and run.get("available"):
                        entry["beampattern_samples"]=beampattern_samples(model,run["state"],run["selected_positions"])
                    elif run.get("best_feasible") is not None:
                        best=run["best_feasible"]
                        selected=np.argmax(np.array(best["metrics"]["binary_schedule"]),axis=1)
                        entry["beampattern_samples"]=beampattern_samples(make_model(point,settings),best["state"],selected)
                if "closed_form" in figure["baselines"]:
                    entry["closed_form"]=evaluate_closed(make_model(point,settings))
                if settings["kind"]=="communications":
                    if any("SMS" in b for b in figure["baselines"]):
                        sms_point=dict(point,ms2=[0,0])
                        if "same_total_SMS" in figure["baselines"]:
                            if "total" in point: sms_point["ms1"]=[int(math.sqrt(point["total"])),int(math.sqrt(point["total"]))]
                            else: raise ValueError("Fixed-total comparison requires exact total and aperture shape")
                        entry["SMS"]=optimize(make_model(sms_point,settings),settings,"communications",seed_offset=500000+point_index,checkpoint_path=str(prefix)+"-sms.json")
                    if "dynamic_RIS" in figure["baselines"]:
                        entry["dynamic_RIS"]={"minimum_snr":settings["reference_snr"]*model.M**2}
                else:
                    if any("RIS_" in b for b in figure["baselines"]):
                        entry["RIS"]=ris_baselines(model,settings,checkpoint_prefix=prefix)
                    if any(b.startswith("ralm_reference") for b in figure["baselines"]):
                        reference=dict(point)
                        if "ralm_reference_n6" in figure["baselines"]:
                            reference["ms2"]=[6,6]
                        entry["RALM_reference"]=optimize(make_model(reference,settings),settings,"sinr",seed_offset=900000+point_index,checkpoint_path=str(prefix)+"-reference.json")
                result["points"].append(entry)
                result.update(figure_execution_status(result["points"],len(figure["points"])))
                if args.point is not None:
                    result["scope"]="fullsize_partialfigure"
                    result["full_figure_point_count"]=len(figure["points"])
                    result["selected_point_index"]=args.point
                args.output.parent.mkdir(parents=True,exist_ok=True)
                args.output.write_text(json.dumps(result,indent=2),encoding="utf-8")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2),encoding="utf-8")
if __name__=="__main__": main()
