"""Prepared new source replay of one saved coordinate; never a trajectory replay."""
from pathlib import Path
import argparse,copy,hashlib,importlib,json,sys,time,traceback
import numpy as np
HERE=Path(__file__).parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):
    with p.open('x',encoding='utf8',newline='\n')as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def run(args):
    adm=json.loads(args.admission.read_bytes());plan=json.loads(args.plan.read_bytes())
    assert adm['root_admitted_one_new_fixed_coordinate_source_replay']is True and adm['lane']=='python'
    fixture=json.loads(args.fixture.read_bytes());assert adm['case']==fixture['case']and adm['mode']==fixture['mode']
    assert adm['plan_SHA256']==sha(args.plan)
    assert not args.output.exists(),'Unique exact case only; preserve old attempts'
    selected=next(x for x in plan['inputs']if x['case']==fixture['case']and x['mode']==fixture['mode']);assert selected['SHA256']==sha(args.fixture)and plan['configuration']['SHA256']==sha(args.config)
    pins={x['path']:x['SHA256']for x in plan['execution_source_pins']};assert all(sha(Path(p))==v for p,v in pins.items())
    paths=[Path(p)for p in pins]+[args.fixture,args.config,args.admission,args.plan];before={str(p):sha(p)for p in paths}
    cfg=json.loads(args.config.read_bytes());job={**fixture['selected_original_job'],**fixture['optional_original_design_overrides']}
    assert cfg['convex_solver']['name']=='certified_exact_2d'and job['N']==6 and job['M']==5
    args.output.mkdir(parents=True,exist_ok=False);arrays={};observations=[];observer_errors=[];calls={};original_return=None;error=None
    def pack(v,key):
        if isinstance(v,np.ndarray):arrays[key]=v.copy();return{'array_key':key,'dtype':v.dtype.str,'shape':list(v.shape)}
        if isinstance(v,np.generic):return pack(v.item(),key)
        if isinstance(v,(tuple,list)):return[pack(x,key+'_'+str(i))for i,x in enumerate(v)]
        if isinstance(v,dict):return{k:pack(x,key+'_'+str(k))for k,x in v.items()}
        if isinstance(v,float)and not np.isfinite(v):return{'original_nonfinite_float':repr(v)}
        if v is None or isinstance(v,(str,bool,int,float)):return v
        raise TypeError(type(v).__name__)
    def observe(stage,v):
        try:observations.append({'stage':stage,'data':pack(v,'obs'+str(len(observations)))})
        except Exception as ex:observer_errors.append({'stage':stage,'type':type(ex).__name__,'message':str(ex)})
    sys.path.insert(0,str(HERE/'python-provider'))
    core=importlib.import_module('core');source_run=importlib.import_module('run');exact=importlib.import_module('coordinate_exact')
    for module,name in [(core,'core.py'),(source_run,'run.py'),(exact,'coordinate_exact.py')]:
        assert Path(module.__file__).resolve()==(HERE/'python-provider'/name).resolve(),'Imported provider path mismatch; no coordinate call allowed'
    design,unused_initial=source_run.scenario(cfg,job['N'],job['M'],job['kappa'],job['power'],job['A'],job['geometry'])
    if 'region_lower'in job:design['region_lower']=job['region_lower'];design['region_upper']=job['region_upper']
    if 'estimated_geometry'in job:design,_=source_run.scenario(cfg,job['N'],job['M'],job['kappa'],job['power'],job['A'],job['estimated_geometry'])
    t=np.asarray(fixture['actual_pre_state'],dtype=float);antenna=fixture['antenna_zero_based'];mode=fixture['mode'];assert t.shape==(6,2)and 0<=antenna<6
    observe('actual_complete_design_and_whole_saved_prestate',{'c':design,'t':t,'antenna':antenna,'mode':mode,'unused_original_scenario_initializer':unused_initial})
    corepath=str((HERE/'python-provider/core.py').resolve());exactpath=str((HERE/'python-provider/coordinate_exact.py').resolve());exactlines=(HERE/'python-provider/coordinate_exact.py').read_text().splitlines();corelines=(HERE/'python-provider/core.py').read_text().splitlines()
    def capture_trace(frame,event,arg):
        filename=frame.f_code.co_filename;name=frame.f_code.co_name;local=frame.f_locals
        if filename not in (corepath,exactpath):return None
        if event=='call':
            calls[name]=calls.get(name,0)+1
            if name=='solve':observe('actual_original_solver_arguments',{k:local.get(k)for k in ['t','c','antenna','mode','gradient','curvature','base','minor_gradient','minor_curvature','objective_before']})
        if filename==corepath and name=='zf_surrogate'and event=='line'and corelines[frame.f_lineno-1].strip().startswith('chi.append'):
            observe('actual_ZF_user_expansion',{k:local[k]for k in ['u','h','scale','g','theta1','theta2','inv','y','a','ell','x','b','lmax','q','const','f','dg','bound','xi']if k in local})
        if filename==exactpath and event=='line'and name=='solve'and exactlines[frame.f_lineno-1].strip().startswith('def candidate_quality'):
            observe('actual_original_candidates_before_tie_selection',{k:local[k]for k in ['A','b','vertices','feasibility_tolerance','candidates','valid','values','maximum','tied']})
        if event=='return':
            if name in ('solve','polygon','edge_interval','derivative','candidate_quality')and filename==exactpath:
                fields={'polygon':['A','b','vertices','tol'],'edge_interval':['index','base','direction','lower','upper'],'derivative':['parameter'],'candidate_quality':['index','x','gradient_value','gap_value'],'solve':['A','b','vertices','gradient','curvature','base','minor_gradient','minor_curvature','g','q','a','G','valid','values','maximum','tied','winner','value','gap','gap_tolerance','residual']}[name]
                observe('actual_original_'+name+'_return',{'locals':{k:local[k]for k in fields if k in local},'original_return':arg})
            if name=='mrt_statistics':observe('actual_original_MRT_statistics_return',{'gradient':local['gradient'],'curvature':arg[2],'gd':local['gd'],'psi':local['psi'],'weight':local['weight'],'numerator':local['numerator'],'denominator':local['denominator'],'original_return':arg})
        return trace
    def trace(frame,event,arg):
        try:return capture_trace(frame,event,arg)
        except Exception as ex:
            observer_errors.append({'stage':'trace_observer_only','function':frame.f_code.co_name,'event':event,'type':type(ex).__name__,'message':str(ex)})
            # An observer failure must not replace the original return/error.
            return trace
    # The scipy root function and all original callbacks receive their actual
    # argument objects; return objects are passed through unchanged.
    original_brentq=exact.brentq
    def observed_brentq(*a,**kw):
        observe('actual_scipy_brentq_input',{'L':a[1],'R':a[2],'options':kw})
        returned=original_brentq(*a,**kw);observe('actual_scipy_brentq_return',{'root':returned});return returned
    exact.brentq=observed_brentq;started=time.perf_counter()
    try:
        sys.settrace(trace);original_return=core.solve_coordinate(t,design,antenna,mode)
    except Exception as ex:error={'type':type(ex).__name__,'message':str(ex),'traceback':traceback.format_exc()}
    finally:sys.settrace(None);exact.brentq=original_brentq
    if original_return is not None:observe('actual_whole_coordinate_original_return',{'trial':original_return[0],'record':original_return[1]})
    npz=args.output/'actual-original-coordinate-operands-candidates-and-return.npz'
    with npz.open('xb')as f:np.savez_compressed(f,**arrays)
    after={str(p):sha(p)for p in paths};comparison=None
    if original_return is not None:
        returned=original_return[0];ph=np.asarray(fixture['actual_python_post_state']);mh=np.asarray(fixture['actual_matlab_post_state'])
        comparison={'new_endpoint_whole_IEEE64_equal_historical_python':returned.dtype==ph.dtype and returned.shape==ph.shape and returned.tobytes(order='F')==ph.tobytes(order='F'),'new_endpoint_whole_IEEE64_equal_historical_native':returned.dtype==mh.dtype and returned.shape==mh.shape and returned.tobytes(order='F')==mh.tobytes(order='F'),'maximum_new_minus_historical_python':float(np.max(abs(returned-ph))),'maximum_new_minus_historical_native':float(np.max(abs(returned-mh))),'not_proof_of_historical_local_arithmetic_reproduction':True}
    report={'schema':'actual-new-frozen-source-one-fixed-coordinate-replay-v1','lane':'python','case':fixture['case'],'mode':mode,'coordinate_index_zero_based':fixture['coordinate_index_zero_based'],'antenna_zero_based':antenna,'source_input_before':before,'source_input_after':after,'source_input_interval_closed':before==after,'original_function_returned':original_return is not None,'actual_exception':error,'observer_errors':observer_errors,'function_call_counts':calls,'actual_observations':observations,'array_file':npz.name,'array_SHA256':sha(npz),'comparison_to_saved_endpoints':comparison,'elapsed_seconds':time.perf_counter()-started,'new_coordinate_source_execution_not_historical_producer_replay':True,'original_subproblem_and_tolerances_unchanged':True,'no_optimize_run_job_instantaneous_benchmark_RNG_or_MP_calls':not any(calls.get(n,0)for n in ('optimize','instantaneous','fixed_array_benchmark')),'historical_path_gate_repaired_or_cause_proven':False,'independent_MP_coefficient_validation_pending':True}
    code=0 if original_return is not None and before==after and not observer_errors else 1;report['effective_exit_code']=code;put(args.output/'ACTUAL_ONE_SOURCE_BOUND_FIXED_COORDINATE_CAPTURE_V1.json',report);print(json.dumps({'exit_code':code,'lane':'python','case':fixture['case'],'mode':mode,'original_function_returned':original_return is not None,'comparison':comparison}),flush=True);return code
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('fixture','config','plan','admission','output'):p.add_argument('--'+n,type=Path,required=True)
    raise SystemExit(run(p.parse_args()))
