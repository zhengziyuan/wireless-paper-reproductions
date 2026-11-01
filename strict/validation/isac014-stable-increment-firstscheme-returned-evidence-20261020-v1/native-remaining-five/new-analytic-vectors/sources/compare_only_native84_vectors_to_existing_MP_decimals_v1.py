"""No MP oracle: compare new native IEEE vectors to the existing MP decimals."""
from pathlib import Path
from decimal import Decimal,localcontext
import hashlib
import importlib.util
import io
import json
import warnings
import numpy as np
from scipy.io import loadmat

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def need(ok,message):
    if not ok:raise ValueError(message)
def integer(value):
    a=np.asarray(value).reshape(-1);need(a.size==1,'Scalar integer required');f=float(a[0]);need(np.isfinite(f)and f.is_integer(),'Actual integer required');return int(f)
def put(path,value):
    payload=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    with path.open('xb')as stream:stream.write(payload)
def components(value,shape,digest):
    a=np.asarray(value);need(a.dtype.kind in 'biufc'and a.size==int(np.prod(shape))and np.isfinite(a).all(),'Unsupported/nonfinite native array')
    re=np.asarray(a.real,dtype='<f8').reshape(shape,order='F');im=np.asarray(a.imag,dtype='<f8').reshape(shape,order='F')
    need(hashlib.sha256(re.tobytes(order='F')+im.tobytes(order='F')).hexdigest()==digest,'Typed component/class/signed-zero transport did not roundtrip')
    return re,im

def run(plan,held_journal):
    out=Path(plan['fresh_output_directory']);mat=out/'actual-new-native84-analytic-vectors.mat';completion=out/'actual-native84-probe-completion.json'
    files=[mat,completion,Path(held_journal)]+[Path(path)for path in plan['source_and_input_pins']]
    before={str(path):sha(path)for path in files};j=json.loads(Path(held_journal).read_bytes())
    need(j['natural_wait_completed']and j['actual_child_terminal_exit_code']==0 and j['exact_original_handle_birth_and_exit_match'],'Native probe has no real held natural0')
    need(j['all_watched_source_and_job_bytes_unchanged']and not j['host_errors'],'Native probe source interval not closed')
    need(all(sha(path)==digest for path,digest in plan['source_and_input_pins'].items()),'Frozen source/input changed')
    done=json.loads(completion.read_bytes());need(done['source_input_interval_closed']and done['source_before']==done['source_after'],'Native direct-source interval not closed')
    need(done['native_returned_state_count']==84 and done['component_count_per_precision']==1596 and done['new_evaluate_calls']==84 and done['optimizer_update_MC_RNG_or_MP_calls']==0,'Wrong native84 scope')
    schema=Path(plan['frozen_native_schema_codec']);need(sha(schema)==plan['frozen_native_schema_codec_SHA256'],'Frozen codec changed')
    spec=importlib.util.spec_from_file_location('unchanged_native5781_typed_codec_for_probe',schema);codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec)
    loaded=loadmat(mat,simplify_cells=True,mat_dtype=False);vectors=loaded['vectors'];need(len(vectors)==84,'84 actual native vectors required')
    rows=[];counts={};component_total=0;maximum=Decimal(0);offset=0;typed_inventory=[]
    with localcontext()as ctx:
        ctx.prec=200;bound=Decimal.from_float(1e-5)
        for item in plan['schemes']:
            ordinal=item['ordinal'];name=item['scheme_name'];reference=json.loads(Path(item['existing_MP_report']).read_bytes())
            need(reference['source_input_interval_closed']and reference['source_input_before']==reference['source_input_after'],'Existing MP reference interval not closed')
            need(reference['actual_native_MAT_SHA256']==item['input_MAT_SHA256'],'Existing MP reference is for another input MAT')
            raw=Path(item['input_MAT']).read_bytes();need(hashlib.sha256(raw).hexdigest()==item['input_MAT_SHA256'],'Actual closed original MAT changed')
            actual={k:codec._unwrap(v)for k,v in loadmat(io.BytesIO(raw),struct_as_record=False,squeeze_me=False,mat_dtype=False).items()if not k.startswith('__')}
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                shadow={k:codec._unwrap(v)for k,v in loadmat(io.BytesIO(raw),struct_as_record=False,squeeze_me=False,mat_dtype=True).items()if not k.startswith('__')}
            rec=actual['recording'];cls=shadow['recording'];states=codec._sequence(rec['returns']);classes=codec._sequence(cls['returns'])
            need(len(states)==len(classes)==item['returned_states'],'Original state count differs')
            order=['update_w','update_theta','update_rotation']if item['flags'][2]else['update_w','update_rotation']
            for local_index,(state,class_state)in enumerate(zip(states,classes)):
                row=vectors[offset+local_index];method=order[local_index%len(order)];call=local_index//len(order)+1
                need(integer(row['global_index'])==offset+local_index+1 and integer(row['actual_local_return_index'])==local_index+1,'Global/local input index differs')
                need(integer(row['scheme_ordinal'])==ordinal and str(row['scheme_name'])==name and list(np.asarray(row['scheme_flags']).reshape(-1))==item['flags'],'Wrong native scheme or flags')
                need(str(row['method'])==method and integer(row['call'])==call and codec._scalar(state['AO_iteration'])==call,'Wrong actual own-block mapping')
                need(str(row['native_gradient_class'])=='double','Actual native gradient not MATLAB double')
                dims=tuple(int(x)for x in np.asarray(row['native_gradient_size']).reshape(-1));wanted={'update_w':(4,6),'update_theta':(36,1),'update_rotation':(6,1)}[method]
                need(dims==wanted,'Wrong original native gradient dimensions')
                re,im=components(row['gradient'],dims,str(row['component_real_then_imag_F_binary64_SHA256']))
                for field,shape in [('W',(4,6)),('theta',(36,)),('r',(6,))]:
                    original=codec.canonical_array(state[field],class_state[field],shape,f'ord{ordinal}_{local_index+1}_{field}',typed_inventory)
                    rr,ii=components(row['original_'+field],shape,str(row['original_'+field+'_component_SHA256']))
                    need(rr.tobytes(order='F')==np.asarray(original.real,dtype='<f8').tobytes(order='F')and ii.tobytes(order='F')==np.asarray(original.imag,dtype='<f8').tobytes(order='F'),'Probe used different actual state components')
                for field in ['lower','upper']:
                    original=codec.canonical_array(rec['initial_state'][field],cls['initial_state'][field],(6,),f'ord{ordinal}_{field}',typed_inventory)
                    rr,ii=components(row['original_'+field],(6,),str(row[field+'_component_SHA256']))
                    need(rr.tobytes(order='F')==np.asarray(original.real,dtype='<f8').tobytes(order='F')and ii.tobytes(order='F')==np.asarray(original.imag,dtype='<f8').tobytes(order='F'),'Probe actual recorded bounds differ')
                iota=codec.canonical_array(state['fixed_iota'],class_state['fixed_iota'],(1,),f'ord{ordinal}_{local_index+1}_iota',typed_inventory)
                rr,ii=components(row['fixed_iota'],(1,),str(row['fixed_iota_component_SHA256']))
                need(rr.tobytes(order='F')==np.asarray(iota.real,dtype='<f8').tobytes(order='F')and ii.tobytes(order='F')==np.asarray(iota.imag,dtype='<f8').tobytes(order='F'),'Probe used another fixed iota')
                native_metric=row['actual_native_metric']
                ur,ui=components(native_metric['utility'],(1,),str(row['metric_utility_component_SHA256']))
                ir,ii=components(native_metric['iota'],(1,),str(row['metric_iota_component_SHA256']))
                need(ir.tobytes(order='F')==np.asarray(iota.real,dtype='<f8').tobytes(order='F')and ii.tobytes(order='F')==np.asarray(iota.imag,dtype='<f8').tobytes(order='F'),'Native metric used another fixed iota')
                pairs=list(zip(re.reshape(-1,order='C'),im.reshape(-1,order='C')));comparisons={}
                for digits in ['80','100']:
                    old=reference['precision_lanes'][digits][local_index]
                    need(old['method']==method and old['call']==call,'Existing MP local row is not this own-block')
                    ref=old['block_gradient']['reference_gradient'];need(len(ref)==len(pairs),'Full MP vector missing')
                    errors=[]
                    for (real,imag),target in zip(pairs,ref):
                        dr=Decimal.from_float(float(real))-Decimal(target['real']);di=Decimal.from_float(float(imag))-Decimal(target['imag']);errors.append((dr*dr+di*di).sqrt())
                    worst=max(errors);maximum=max(maximum,worst)
                    comparisons[digits]=dict(components=len(pairs),maximum_absolute_complex_error=str(worst),original_exact_binary64_absolute_bound=str(bound),original_strict_less_than_1e_minus5_pass=all(error<bound for error in errors),per_component_absolute_errors=[str(error)for error in errors])
                counts[method]=counts.get(method,0)+1;component_total+=len(pairs)
                rows.append(dict(global_index=offset+local_index+1,scheme_ordinal=ordinal,scheme_name=name,actual_local_return_index=local_index+1,method=method,call=call,fixed_iota=float(row['fixed_iota']),actual_native_utility=float(ur[0]),actual_native_rate=float(native_metric['rate']),actual_native_nmse=float(native_metric['nmse']),native_metric_and_fixed_iota_typed_transport_bound=True,actual_native_gradient_shape=list(dims),actual_native_class=str(row['native_gradient_class']),actual_native_isreal=bool(integer(row['native_isreal'])),all_original_input_class_shape_complex_and_F_IEEE_bits_equal=True,C_order_flatten_for_existing_MP=True,comparisons=comparisons))
            offset+=item['returned_states']
            for digits in ['80','100']:
                final=reference['precision_lanes'][digits][-1]
                need(len(reference['precision_lanes'][digits])==item['returned_states']+1 and final['method']=='final_ownstate'and all('reference_gradient'not in part for part in final['block_gradient']['parts'].values()),'Final scope changed; never invent missing final vectors')
    need(offset==84 and component_total==1596 and counts=={'update_w':34,'update_theta':16,'update_rotation':34},'Actual count mismatch')
    after={str(path):sha(path)for path in files};closed=before==after;passed=all(c['original_strict_less_than_1e_minus5_pass']for row in rows for c in row['comparisons'].values());code=0 if closed and passed else 2
    result=dict(schema='actual-new-native84-analytic-vectors-vs-existing-MP80-MP100-decimals-v1',actual_entry_exit_code=code,source_input_before=before,source_input_after=after,source_input_interval_closed=closed,actual_new_native_evaluate_calls=84,counts=counts,components_per_precision=1596,all_84_existing_MP_vector_absolute_gates_PASS=passed,maximum_absolute_error=str(maximum),rows=rows,original_input_typed_inventory=typed_inventory,NoRIS_only_W_PGA_no_RCG=True,excluded_old_first36_and_five_final_states=True,new_native_source_calls_not_historical_memory_recovery=True,existing_MP_references_not_regenerated=True,original_ownstop_final_joint_W_and_reference_failures_not_promoted=True,new_MP_optimizer_MC_RNG_trial_calls=0,original_reference_fullpaper_PASS=False)
    path=out/'ACTUAL_NATIVE84_ANALYTIC_VECTORS_VS_EXISTING_MP80_MP100_DECIMALS_V1.json';put(path,result)
    print(json.dumps(dict(report=str(path),SHA256=sha(path),exit_code=code,all84_PASS=passed,components_per_precision=1596,max_absolute_error=str(maximum))),flush=True)
    return code
