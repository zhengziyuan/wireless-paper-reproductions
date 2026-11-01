"""Fixed saved-state arithmetic only. No optimizer, MC or reference recomputation.

Exit1 preserves the disclosed extra intermediate-field failures. The reported
changed-branch checks and the additional intermediate checks are independent.
"""
from pathlib import Path
from decimal import Decimal,localcontext
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,sys

ROOT=Path(__file__).resolve().parent
def digest(b):return hashlib.sha256(b).hexdigest()
def read(relative):return json.loads((ROOT/relative).read_bytes())
def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
def components(value):
    if isinstance(value,dict) and 'real' in value and 'imag' in value:
        def flatten(x):
            if isinstance(x,list):return [v for y in x for v in flatten(y)]
            return [x]
        return list(zip(flatten(value['real']),flatten(value['imag'])))
    if isinstance(value,list):return [p for v in value for p in components(v)]
    return [(value,0.0)]
def compare(actual,reference):
    actual=components(actual);expected=reference['expected'];assert len(actual)==len(expected)
    absolute=Decimal.from_float(float(reference['absolute_bound']));relative=Decimal(reference['relative_bound'])
    failures=[];maxerr=Decimal(0);maxscale=Decimal(0)
    for index,((real,imag),ref) in enumerate(zip(actual,expected)):
        rr,ii=Decimal(ref['real']),Decimal(ref['imag']);dr=Decimal.from_float(float(real))-rr;di=Decimal.from_float(float(imag))-ii
        error=(dr*dr+di*di).sqrt();scale=(rr*rr+ii*ii).sqrt()
        maxerr=max(maxerr,error);maxscale=max(maxscale,scale)
        if error>absolute+relative*scale:failures.append(index)
    return dict(components=len(actual),maximum_absolute_error=str(maxerr),maximum_reference_magnitude=str(maxscale),
        absolute_bound=reference['absolute_bound'],relative_bound=reference['relative_bound'],failed_component_indices=failures,passed=not failures)
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def encoded(array,np):
    array=np.asarray(array)
    return dict(real=np.real(array).tolist(),imag=np.imag(array).tolist(),shape=list(array.shape))

def evaluate_python(fixture):
    import numpy as np
    model=load_module('isolated_public_three_state_candidate',ROOT/'sources/python/core_explicit_interference_candidate_v1.py')
    def forbidden(*a,**kw):raise RuntimeError('Optimizer, initializer and RNG are forbidden in this fixed-state entry')
    for name in ('initialize','optimize','update_w','update_theta','update_rotation'):setattr(model,name,forbidden)
    for name in ('default_rng','seed','rand','randn','random','normal','uniform'):
        if hasattr(np.random,name):setattr(np.random,name,forbidden)
    namespace=dict(model.__dict__)
    passive=ROOT/'sources/python/exact_candidate_passive_QT_prefix.py'
    exec(compile(passive.read_bytes(),str(passive),'exec'),namespace)
    rows=[]
    for state in fixture['states']:
        c=read(state['scenario']);w=np.asarray(state['W']['real'])+1j*np.asarray(state['W']['imag'])
        theta=np.asarray(state['theta']['real'])+1j*np.asarray(state['theta']['imag']);r=np.asarray(state['rotation'])
        metric,der=model.evaluate(w,theta,r,c,state['iota'],True)
        qt=namespace['passive_exact_candidate_QT_prefix'](w,theta,r,c,state['iota'])
        rows.append(dict(key=state['key'],metric={k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in metric.items()},
            derivatives={name:encoded(value,np) for name,value in zip(('W','RIS','rotation'),der)},
            QT_coefficients={name:encoded(value,np) for name,value in qt.items() if name!='y'}))
    return rows

def evaluate(args):
    if args.output_dir.exists():raise FileExistsError('Choose a new output directory; preserve previous results')
    target=args.output_dir.resolve()
    if target==ROOT or ROOT in target.parents:raise ValueError('Output must be outside the frozen package')
    manifest=read('manifest.json')
    before={r['path']:digest((ROOT/r['path']).read_bytes()) for r in manifest['files']}
    assert all(before[r['path']]==r['SHA256'] for r in manifest['files']),'A source/input differs from the manifest'
    fixture=read('data/three-saved-states.json');reference=read('data/MP80-MP100-references.json')
    native=read('results/actual-native-three-state-vectors.json')
    old=read('results/historical-scoped-results.json')
    python=evaluate_python(fixture) if args.mode=='evaluate-python' else None
    external_native=None
    if args.native_mat:
        from io import BytesIO
        import numpy as np
        from scipy.io import loadmat
        native_bytes=args.native_mat.read_bytes();external_native=dict(SHA256=digest(native_bytes),bytes=len(native_bytes))
        rows=loadmat(BytesIO(native_bytes),simplify_cells=True)['result'];assert len(rows)==3
        for actual,state in zip(rows,fixture['states']):
            assert actual['key']==state['key'] and actual['scheme']==state['scheme']
            assert actual['input']['iota']==state['iota']
            for native_name,public_name in [('W','W'),('theta','theta'),('r','rotation')]:
                wanted=state[public_name]
                wanted=np.asarray(wanted['real'])+1j*np.asarray(wanted['imag']) if isinstance(wanted,dict) else np.asarray(wanted)
                got=np.asarray(actual['input'][native_name]).reshape(wanted.shape)
                assert got.dtype==wanted.dtype and got.real.tobytes()==wanted.real.tobytes()
                if np.iscomplexobj(wanted):assert got.imag.tobytes()==wanted.imag.tobytes()
        native=dict(records=[dict(key=r['key'],mode='candidate',metric={k:(v.tolist() if hasattr(v,'tolist') else v) for k,v in r['metric'].items()},
            W_gradient=encoded(np.asarray(r['gw']),np),RIS_gradient=encoded(np.asarray(r['gt']),np),rotation_gradient=r['gr'].tolist(),
            QT_coefficients={k:encoded(np.asarray(v),np) for k,v in r['qt'].items()}) for r in rows])
    lanes={};all_modified=True;all_expanded=True
    with localcontext() as context:
        context.prec=110
        for language in ('MATLAB','Python'):
            if language=='Python' and python is None:continue
            source=python if language=='Python' else [r for r in native['records'] if r['mode']=='candidate']
            assert len(source)==3
            language_rows=[]
            for actual,ref in zip(source,reference['states']):
                assert actual['key']==ref['key'];row=dict(key=ref['key'],scheme=ref['scheme'],precision={})
                for digits in ('80','100'):
                    rr=ref['lanes'][digits];fields={k:compare(actual['metric'][k],rr['fields'][k]) for k in rr['fields']}
                    derivatives={}
                    for name,member in [('W','W_gradient'),('RIS','RIS_gradient'),('rotation','rotation_gradient')]:
                        value=actual['derivatives'][name] if language=='Python' else actual[member]
                        derivatives[name]=compare(value,rr['derivatives'][name])
                    coefficients={k:compare(actual['QT_coefficients'][k],v) for k,v in rr['QT_coefficients'].items()}
                    modified=all(v['passed'] for v in fields.values()) and all(v['passed'] for v in derivatives.values()) and all(coefficients[k]['passed'] for k in ('signal','interference','total','mu','eta','q','p'))
                    extra=all(coefficients[k]['passed'] for k in ('lip','ga'))
                    all_modified=all_modified and modified;all_expanded=all_expanded and modified and extra
                    row['precision'][digits]=dict(fields=fields,derivatives=derivatives,QT_coefficients=coefficients,
                        physical_derivatives_and_changed_QT_passed=modified,additional_unchanged_intermediates_passed=extra)
                language_rows.append(row)
            lanes[language]=language_rows
    after={p:digest((ROOT/p).read_bytes()) for p in before}
    assert before==after,'Frozen sources or inputs changed during evaluation'
    if args.native_mat:
        assert digest(args.native_mat.read_bytes())==external_native['SHA256'],'External native MAT changed during this comparison'
        external_native.update(source_before_after_unchanged=True,all_three_saved_input_binary64_bytes_equal=True)
    args.output_dir.mkdir(parents=True,exist_ok=False)
    result=dict(schema='PORTABLE_ISAC_THREE_FIXED_STATE_ARITHMETIC_COMPARISON_V1',created_UTC=datetime.now(timezone.utc).isoformat(),mode=args.mode,
        fixture_states=3,reference_precisions=[80,100],new_MP_or_optimizer_MC_or_initializer_calls=0,
        Python_fixed_state_evaluate_called=args.mode=='evaluate-python',native_MATLAB_executed_by_this_entry=False,
        native_values='Provided fresh native MAT' if args.native_mat else 'Stored actual MATLAB fixed-state outputs',
        external_native_input=external_native,
        source_and_input_manifest_unchanged=True,manifest_SHA256=digest((ROOT/'manifest.json').read_bytes()),
        physical_derivatives_and_changed_QT_passed=all_modified,expanded_all_coefficients_gate_passed=all_expanded,
        historical_original_Python_process_exit=old['Python']['actual_process_exit_code'],
        historical_original_Python_expanded_gate_false_retained=not old['Python']['expanded_all_coefficients_gate_passed'],
        threshold_scope='The1e-5 extra lip/ga check was newly borrowed from the existing derivative comparison bound. It is not a recovered original lip/ga acceptance standard.',
        lanes=lanes,all_original_failures_retained=True,full_convergence_dual_optimized_equality_reference_or_paper_PASS=False,
        effective_exit_code=0 if all_expanded else 1)
    write(args.output_dir/'portable-comparison.json',result)
    print(json.dumps(dict(states=3,languages=list(lanes),physical_derivatives_and_changed_QT_passed=all_modified,
        expanded_all_coefficients_gate_passed=all_expanded,effective_exit_code=result['effective_exit_code'])),flush=True)
    return result['effective_exit_code']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=('recorded-only','evaluate-python'),default='recorded-only')
    p.add_argument('--native-mat',type=Path,help='Optional separately generated native fixed-state MAT; SciPy required')
    p.add_argument('--output-dir',type=Path,required=True);args=p.parse_args()
    raise SystemExit(evaluate(args))
