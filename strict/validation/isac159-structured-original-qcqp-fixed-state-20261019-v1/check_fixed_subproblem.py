"""Compare saved fixed-subproblem candidates to existing MP references only.

Optional Python solve is one QCQP using the same captured inputs. No outer
optimizer, sampler, Monte Carlo, new eigenspectrum oracle or MP solve is called.
"""
from pathlib import Path
from datetime import datetime,timezone
from io import BytesIO
import argparse,gzip,hashlib,importlib.util,json,sys
import numpy as np
import mpmath as mp
from scipy.io import loadmat
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'sources'))
from comparison_helpers import ex,matrix,txt,fro,power,objective,physical
def sha(b):return hashlib.sha256(b).hexdigest()
def read(name):return json.loads((ROOT/name).read_bytes())
def put(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
def main(args):
    if args.output_dir.exists():raise FileExistsError('Choose fresh output; preserve all prior results')
    if ROOT==args.output_dir.resolve() or ROOT in args.output_dir.resolve().parents:raise ValueError('Output must be outside frozen package')
    manifest=read('manifest.json');before={row['path']:sha((ROOT/row['path']).read_bytes()) for row in manifest['files']}
    assert all(before[row['path']]==row['SHA256'] for row in manifest['files'])
    scene=read('data/scenario.json');captured=read('data/capture-metadata.json');iota=captured['target_capture']['iota']
    actual={name:loadmat(ROOT/f'results/actual-{name.lower()}-fixed-qcqp.mat',simplify_cells=True)['result'] for name in ('Python','MATLAB')}
    if args.solve_python:
        source=ROOT/'sources/structured_original_qcqp_candidate_v1.py';spec=importlib.util.spec_from_file_location('portable_isolated_fixed_Q_candidate',source)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with np.load(ROOT/'data/actual-failed-Q-operands.npz',allow_pickle=False) as z:a={k:z[k].copy() for k in z.files}
        w,info=module.solve_fixed_original_qcqp(a['w'],a['fc'],a['mu'],a['eta'],a['lip'],a['ga'],float(a['den']),float(scene['rho']),scene['power'],scene['W_solver']['bisection_tolerance'])
        actual['Python']=dict(solution=w,**info)
    external=None
    if args.native_result:
        native_bytes=args.native_result.read_bytes();external=dict(SHA256=sha(native_bytes),bytes=len(native_bytes))
        actual['MATLAB']=loadmat(BytesIO(native_bytes),simplify_cells=True)['result']
    lanes={};gates=[]
    for digits in (80,100):
        raw=gzip.decompress((ROOT/f'references/original-structure-MP{digits}-reference.json.gz').read_bytes());reference=json.loads(raw)
        with mp.workdps(digits):
            fcB,fsB=matrix(reference['B']['fc']),matrix(reference['B']['fs']);rows={}
            for language,result in actual.items():
                w=matrix(np.asarray(result['solution']));nu=ex(result['nu']);models={}
                assert w.rows==4 and w.cols==6
                for kind in ('A','B'):
                    r=reference[kind];q,p,expected=(matrix(r[name]) for name in ('Q','P','W'))
                    err=max(abs(a-b) for a,b in zip(w,expected));qp=objective(w,q,p);residual=(q+nu*mp.eye(q.rows))*w-p
                    res=fro(residual);relative=res/max(mp.mpf(1),fro(p),fro(q*w),abs(nu)*fro(w))
                    phy=physical(w,fcB,fsB,scene,ex(iota));bound=ex(scene['verification_tolerance'])
                    checks=dict(original_power=power(w)<=ex(scene['power'])+bound,original_selected_nu=nu==ex(r['nu']),
                        original_bisection_steps=int(result['bisection_steps'])==r['bisection_steps'],original_doublings=int(result['bracket_doublings'])==r['bracket_doublings'],
                        original_nu_interval_stop=ex(result['bracket_hi'])-ex(result['bracket_lo'])<=ex(scene['W_solver']['bisection_tolerance'])*max(mp.mpf(1),ex(result['bracket_hi'])),
                        added_reference_solution_comparison=err<=bound,added_QCQP_objective_comparison=abs(qp-ex(r['objective_QCQP']))<=bound,
                        added_full_physical_utility_comparison=abs(phy['utility']-ex(r['physical_utility_at_solved_W']['utility']))<=bound,
                        original_physical_non_decrease=phy['utility']>=ex(reference['B']['physical_utility_at_fixed_captured_W']['utility'])-bound)
                    gates.extend(checks.values())
                    models[kind]=dict(checks=checks,solution_max_error=txt(err),power=txt(power(w)),nu=txt(nu),QCQP_objective_error=txt(abs(qp-ex(r['objective_QCQP']))),
                        stationarity_Fro_diagnostic=txt(res),stationarity_norm_relative_diagnostic=txt(relative),physical_utility=txt(phy['utility']))
                rows[language]=models
            lanes[str(digits)]=rows
    after={name:sha((ROOT/name).read_bytes()) for name in before};assert before==after
    if args.native_result:
        assert sha(args.native_result.read_bytes())==external['SHA256'];external['file_before_after_equal']=True
        external['producer_source_and_input_identity_not_certified_by_numeric_file_alone']=True
    args.output_dir.mkdir(parents=True,exist_ok=False)
    report=dict(schema='PORTABLE_ONE_FIXED_STRUCTURED_QCQP_EXISTING_REFERENCE_CHECK_V1',created_UTC=datetime.now(timezone.utc).isoformat(),
        one_existing_fixed_subproblem=True,scoped_pass=all(gates),Python_fixed_solve_executed=args.solve_python,
        native_values='User-selected result MAT' if args.native_result else 'Stored actual fixed native output',external_native=external,
        new_optimization_trajectory_MC_RNG_or_MP_reference_solve_calls=0,source_and_input_before_after_equal=True,
        reference_A='Original structure from exact promoted captured auxiliaries',reference_B='Independent full physical recomputation at same state',
        stored_bad_Q_or_P_not_used_as_theoretical_reference=True,lanes=lanes,
        comparison_tolerance_scope='Added W/objective/utility comparison uses disclosed scene verification_tolerance1e-7; it is not a new algorithm stop',
        stationarity_scope='Absolute and relative residuals are recorded diagnostics; original source had no residual cutoff and this entry introduces none',
        original_failed_Q_and_previous_expanded_gatefalse_retained=True,full_trajectory_convergence_or_paper_PASS=False)
    put(args.output_dir/'portable-fixed-subproblem-check.json',report)
    print(json.dumps(dict(scoped_pass=all(gates),Python_fixed_solve_executed=args.solve_python,original_failed_Q_retained=True,full_trajectory_or_paper_PASS=False)),flush=True)
    return 0 if all(gates) else 1
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,required=True);parser.add_argument('--solve-python',action='store_true')
    parser.add_argument('--native-result',type=Path,help='Optional fresh native result; numeric comparison does not certify its producer identity')
    raise SystemExit(main(parser.parse_args()))
