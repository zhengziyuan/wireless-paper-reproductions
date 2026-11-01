"""Host/schema adapter only. No objective, derivative, optimizer or MP formula."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import sys
import traceback
import warnings
import numpy as np
from scipy.io import loadmat
from scipy.io.matlab import mat_struct

HERE=Path(__file__).resolve().parent
PLAN_PATH=HERE/'PREPARED_NATIVE_NEW36_AND_FINAL_EXISTING_MP_READER_PLAN_V1.json'
SCHEME='Rot-BS & Rot-RIS'

def sha_bytes(value):return hashlib.sha256(value).hexdigest()
def _need(condition,message):
    if not condition:raise ValueError(message)
def _unwrap(value):
    if isinstance(value,mat_struct):return {key:_unwrap(getattr(value,key))for key in value._fieldnames}
    if isinstance(value,np.ndarray)and value.dtype.kind=='O':
        values=[_unwrap(x)for x in value.ravel(order='F')]
        return values[0]if len(values)==1 else values
    if isinstance(value,np.ndarray)and value.dtype.kind in 'US'and value.size==1:return str(value.item())
    return value
def _scalar(value):
    a=np.asarray(value);_need(a.size==1,'Expected an actual scalar field')
    return a.reshape(-1)[0].item()
def _sequence(value):return value if isinstance(value,list)else[value]
def _float_bits(value):return np.asarray(value,dtype=np.float64).tobytes(order='F')
def _numeric_tree(value):
    return (type(value)in(int,float,bool))or(isinstance(value,list)and all(_numeric_tree(x)for x in value))

def semantic_equal(actual,expected,path,notes):
    """Compare actual MAT values to original JSON; keep original MAT unchanged."""
    if isinstance(expected,dict):
        _need(isinstance(actual,dict)and set(actual)==set(expected),path+': object fields differ')
        for key in expected:semantic_equal(actual[key],expected[key],path+'/'+key,notes)
    elif isinstance(expected,list)and not _numeric_tree(expected):
        values=_sequence(actual);_need(len(values)==len(expected),path+': cell/list length differs')
        for i,(a,b)in enumerate(zip(values,expected)):semantic_equal(a,b,path+'/'+str(i),notes)
    elif isinstance(expected,(int,float,bool,list)):
        a=np.asarray(actual);b=np.asarray(expected)
        _need(a.dtype.kind in 'biuf'and b.dtype.kind in 'biuf',path+': expected real numeric data')
        if b.size==0:_need(a.size==0,path+': expected empty numeric field');return
        _need(a.size==b.size,path+': numeric size differs')
        _need(a.shape==b.shape or np.squeeze(a).shape==np.squeeze(b).shape,path+': semantic shape differs')
        af=np.asarray(a,dtype=np.float64).reshape(-1,order='F');bf=np.asarray(b,dtype=np.float64).reshape(-1,order='F')
        _need(np.all(np.isfinite(af))and np.all(np.isfinite(bf)),path+': nonfinite saved scalar')
        _need(np.array_equal(af,bf),path+': numeric values differ')
        # MATLAB jsonencode may omit a zero sign. The MAT remains authoritative;
        # record this transport distinction instead of silently changing its bits.
        different=af.view(np.uint64)!=bf.view(np.uint64)
        _need(not np.any(different&((af!=0)|(bf!=0))),path+': nonzero IEEE64 values differ')
        if np.any(different):notes.append({'path':path,'JSON_signed_zero_differences':int(np.count_nonzero(different)),'MAT_values_preserved':True})
    elif isinstance(expected,str):_need(str(actual)==expected,path+': string differs')
    elif expected is None:_need(np.asarray(actual).size==0,path+': null/empty transport differs')
    else:raise TypeError(path+': unsupported saved metadata type')

def canonical_array(actual,class_shadow,shape,label,receipts):
    """Use False values; True is read only for dtype/shape class metadata."""
    a=np.asarray(actual);shadow=np.asarray(class_shadow)
    _need(a.shape==shadow.shape,label+': class shadow shape differs')
    _need(shadow.dtype.kind=='f'and shadow.dtype.itemsize==8,label+': original MATLAB double class required')
    _need(a.dtype.kind in 'iufc'and a.size==int(np.prod(shape)),label+': state shape/dtype unsupported')
    original=a.copy(order='F')
    cast=False
    if a.dtype.kind in 'iu':
        a=a.astype(np.float64)
        _need(np.array_equal(a.astype(original.dtype),original),label+': compact-double integer roundtrip failed')
        cast=True
    _need(a.dtype in(np.dtype('float64'),np.dtype('complex128')),label+': expected full IEEE64 values')
    if len(shape)==2:_need(a.shape==shape,label+': matrix orientation differs')
    else:_need(a.shape in(shape,(shape[0],1),(1,shape[0])),label+': vector orientation unsupported')
    a=np.array(a.reshape(shape,order='F'),copy=True,order='F')
    _need(np.all(np.isfinite(a)),label+': nonfinite saved state')
    receipts.append({'field':label,'raw_storage_dtype':str(original.dtype),'raw_MAT_shape':list(original.shape),
        'original_class_shadow_dtype_only':str(shadow.dtype),'canonical_shape':list(a.shape),'canonical_dtype':str(a.dtype),
        'compact_original_double_exact_cast':cast,'class_shadow_values_never_used':True,
        'complex_values_from_False_load_preserved':True,
        'canonical_real_F_IEEE64_SHA256':sha_bytes(np.asarray(a.real,dtype=np.float64).tobytes(order='F')),
        'canonical_imag_F_IEEE64_SHA256':sha_bytes(np.asarray(a.imag,dtype=np.float64).tobytes(order='F'))})
    return a

def load_native(plan,out):
    paths={key:Path(value)for key,value in plan['actual_inputs'].items()}
    raw={key:path.read_bytes()for key,path in paths.items()}
    for key,path in paths.items():_need(sha_bytes(raw[key])==plan['source_and_input_pins'][str(path)],'Actual loaded native input bytes differ: '+key)
    j=json.loads(raw['journal']);result=json.loads(raw['result']);scene=json.loads(raw['scene']);cfg=json.loads(raw['configuration'])
    _need(j['actual_child_terminal_exit_code']==0 and j['effective_host_exit_code']==0,'Closed native producer0 required for this exact packet')
    _need(j['natural_wait_completed']and j['exact_original_handle_birth_and_exit_match']and j['all_watched_source_and_job_bytes_unchanged']and not j['host_errors'],'Native natural lifecycle/source interval is not closed')
    _need(j['source_before']==j['source_after'],'Native source maps differ')
    _need(j['child']['PID']==6356 and j['child']['creation_FILETIME']==134369152992434377,'Wrong native child identity')
    _need(result['scheme_names']==[SCHEME]and result['effective_entry_exit_code']==0,'Wrong native result scope')
    _need(len(cfg)==28 and all(scene[key]==value for key,value in cfg.items()),'Original JSON configuration not embedded in scene')
    _need(sha_bytes(raw['configuration'])=='62d9450cd8ae67986a92c0cd7344f7788d75a3bfb8e89d11d54a59e501536460','Wrong native original configuration')
    _need(sha_bytes(raw['scene'])=='3b5e8fced9d90337bc574d660ea29c0a2b1b67aae8fc11950cdbbb28d609c302','Wrong native original scene')
    false={key:_unwrap(value)for key,value in loadmat(io.BytesIO(raw['MAT']),struct_as_record=False,squeeze_me=False,mat_dtype=False).items()if not key.startswith('__')}
    with warnings.catch_warnings(record=True)as caught:
        warnings.simplefilter('always')
        shadow={key:_unwrap(value)for key,value in loadmat(io.BytesIO(raw['MAT']),struct_as_record=False,squeeze_me=False,mat_dtype=True).items()if not key.startswith('__')}
    _need(set(false)=={'result','scene','cfg','recording'}and set(shadow)==set(false),'Unexpected native MAT top-level schema')
    notes=[]
    for key,expected in [('result',result),('scene',scene),('cfg',cfg)]:semantic_equal(false[key],expected,'MAT/'+key,notes)
    recording=false['recording'];recording_class=shadow['recording']
    _need(recording['schema']=='actual-native-first-scheme-returned-block-states-v1','Wrong native recording schema')
    _need(_scalar(recording['extra_objective_gradient_RNG_calls'])==0,'Recording reports extra evaluations')
    semantic_equal(recording['source_inputs']['scene'],scene,'recording/source_inputs/scene',notes)
    semantic_equal(recording['source_inputs']['configuration'],cfg,'recording/source_inputs/configuration',notes)
    canonical_result=dict(result)
    for key in('history','checks','metrics'):
        values=result[key];_need(isinstance(values,list)and len(values)==1,'Expected one native JSON scheme cell')
        canonical_result[key]={SCHEME:values[0]}
    blocks=canonical_result['history'][SCHEME]['blocks'];blocks=_sequence(blocks)
    canonical_result['history'][SCHEME]['blocks']=blocks
    for block in blocks:block['W']['QCQP']=_sequence(block['W']['QCQP'])
    _need(len(blocks)==12,'Unexpected native AO count')
    returns=_sequence(recording['returns']);classes=_sequence(recording_class['returns'])
    _need(len(returns)==len(classes)==36==result['actual_returned_block_state_count'],'Native returned-state count differs')
    rows=[];arrays={};receipts=[];fixed_iota=[]
    previous={name:canonical_array(recording['initial_state'][name],recording_class['initial_state'][name],shape,'native_initial__'+name,receipts)for name,shape in [('W',(4,6)),('theta',(36,)),('r',(6,))]}
    for i,(state,class_state)in enumerate(zip(returns,classes)):
        call=i//3+1;block=('W','RCG','PGA')[i%3];method=('update_w','update_theta','update_rotation')[i%3]
        _need(int(_scalar(state['AO_iteration']))==call and state['block']==block,'Native order/index mismatch')
        iota=float(_scalar(state['fixed_iota']))
        _need(_float_bits(iota)==_float_bits(blocks[call-1]['iota']),'Native fixed AO iota does not match returned block')
        original_status=blocks[call-1][{'W':'W','RCG':'RIS','PGA':'rotation'}[block]]
        semantic_equal(state['original_status'],original_status,'returned/'+str(i)+'/original_status',notes)
        keys={}
        for name,shape in [('W',(4,6)),('theta',(36,)),('r',(6,))]:
            key=f'native_{method}_{call:03d}__{name}';keys[name]=key
            arrays[key]=canonical_array(state[name],class_state[name],shape,key,receipts)
            if name!={'W':'W','RCG':'theta','PGA':'r'}[block]:
                current=arrays[key]
                _need(_float_bits(current.real)==_float_bits(previous[name].real)and _float_bits(current.imag)==_float_bits(previous[name].imag),'A fixed component changed across the actual native block return')
        previous={name:arrays[keys[name]]for name in('W','theta','r')}
        flags={key:original_status[key]for key in('applicable','converged','termination_reason','iterations','updates','iteration_budget','budget_exhausted','capped_unconverged')if key in original_status}
        rows.append({'method':method,'call':call,'fixed_iota':iota,'arrays':keys,'actual_returned_flags':flags})
        fixed_iota.append(iota)
    final_arrays={name:arrays[rows[-1]['arrays'][name]].copy(order='F')for name in('W','theta','r')}
    final=canonical_result['metrics'][SCHEME]
    for name,expected in [('w_re',final_arrays['W'].real),('w_im',final_arrays['W'].imag),('theta_re',final_arrays['theta'].real),('theta_im',final_arrays['theta'].imag),('rotation',final_arrays['r'])]:
        semantic_equal(expected,final[name],'native_final/'+name,notes)
    _need(canonical_result['original_controls']=={key:scene[key]for key in('W_solver','RCG_solver','PGA_solver','AO_solver')},'Original native controls differ')
    sm={'schema':'explicit-host-view-of-native-MAT-returned-states-v1','rows':rows,'counts':{'update_w':12,'update_theta':12,'update_rotation':12},'derived_from_exact_native_MAT_not_a_historical_Python_recording':True}
    receipt={'schema':'actual-native-MAT-to-unchanged-MP-reader-input-schema-v1',
        'native_input_SHA256':{key:sha_bytes(value)for key,value in raw.items()},
        'semantic_shape_complex_and_compact_double_checks_pass':True,'returned_states':36,
        'numeric_class_shadow_values_never_used':True,
        'class_shadow_warnings':[{'type':type(w.message).__name__,'message':str(w.message)}for w in caught],
        'array_inventory_and_semantic_casts':receipts,'JSON_transport_notes':notes,
        'all_fixed_components_between_actual_native_block_returns_IEEE64_equal':True,
        'fixed_iota_per_return':fixed_iota,'final_iota_from_original_native_result':final['iota'],
        'native_analytic_per_coordinate_vectors_were_not_saved':True,
        'future_binary64_gradient_formula_comparator':'Frozen common Python provider on actual native states; not relabeled captured native gradient vectors.',
        'no_optimizer_MP_objective_gradient_or_MC_calls_in_loader':True}
    with(out/'ACTUAL_NATIVE_MAT_TYPED_STATE_SCHEMA_AND_INPUT_BINDING_V1.json').open('x',encoding='utf-8')as stream:json.dump(receipt,stream,indent=2,allow_nan=False);stream.write('\n')
    return dict(j=j,sm=sm,result=canonical_result,scene=scene,arrays=arrays,final_arrays=final_arrays,receipt=receipt)

def admitted_main(namespace,run):
    parser=argparse.ArgumentParser(description='Only native36+final saved-state MP80/100; no trajectory or MC.')
    parser.add_argument('--admission',type=Path,required=True);parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();plan_bytes=PLAN_PATH.read_bytes();plan=json.loads(plan_bytes);admission=json.loads(args.admission.read_bytes())
    _need(admission.get('root_admitted_only_new_native36_and_final_saved_MP')is True,'Root native-only saved-MP admission is required')
    _need(admission.get('prepared_plan_SHA256')==sha_bytes(plan_bytes),'Admission does not bind this exact plan')
    _need(str(args.output_dir.resolve())==str(Path(plan['fresh_output_directory']).resolve()),'Wrong fresh native MP output')
    _need(not args.output_dir.exists(),'Never repeat or overwrite a saved-reader output')
    for path,digest in plan['source_and_input_pins'].items():_need(sha_bytes(Path(path).read_bytes())==digest,'Frozen source/input changed: '+path)
    args.output_dir.mkdir(parents=True,exist_ok=False)
    namespace.update(NATIVE_PLAN=plan,OUT=args.output_dir,NATIVE_ADMISSION_PATH=args.admission)
    try:run()
    except BaseException as error:
        if not isinstance(error,SystemExit):
            failure={'schema':'actual-native-saved-reader-retained-host-or-schema-error-v1','type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc(),'no_automatic_retry':True,'scientific_PASS':False}
            with(args.output_dir/'ACTUAL_RETAINED_HOST_OR_SCHEMA_FAILURE_V1.json').open('x',encoding='utf-8')as stream:json.dump(failure,stream,indent=2);stream.write('\n')
        raise
