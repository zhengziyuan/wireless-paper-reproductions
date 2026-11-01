"""Saved binding only for the already launched native case014 ordinals 2..6.

No producer import, optimization, RNG, numerical oracle, or current-state poll.
The original 5781 codec remains the numeric MAT authority.
"""
from pathlib import Path
import copy
import hashlib
import importlib.util
import io
import json
import warnings
import numpy as np
from scipy.io import loadmat

HERE = Path(__file__).resolve().parent
PLAN_PATH = HERE / 'PREPARED_NATIVE_REMAINING_FIVE_SAVED_MP80_MP100_CONSUMER_PLAN_V2.json'
OLD_SCHEMA = HERE.parent / 'ISAC014-native-firstscheme-returned-states-MP80-MP100-prepared-v1/native_saved_state_schema_v1.py'
OLD_SCHEMA_SHA256 = '5781cf9b30392e222e1ffee5a7e219b9a9537d5b691dae75015ee3e504bc77af'
NAMES = {2:'Rot-BS & Fix-RIS',3:'Fix-BS & Rot-RIS',4:'Fix-BS & Fix-RIS',5:'Rot-BS & No-RIS',6:'Fix-BS & No-RIS'}
FLAGS = {2:(1,0,1),3:(0,1,1),4:(0,0,1),5:(1,0,0),6:(0,0,0)}

def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()

def need(condition, message):
    if not condition:
        raise ValueError(message)

need(sha_bytes(OLD_SCHEMA.read_bytes()) == OLD_SCHEMA_SHA256, 'Frozen 5781 MAT codec changed')
spec = importlib.util.spec_from_file_location('frozen_native5781_codec', OLD_SCHEMA)
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)

def put(path, value):
    encoded = (json.dumps(value, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with path.open('xb') as stream:
        stream.write(encoded)

def normpath(value):
    return str(Path(value).resolve()).replace('\\','/').casefold()

def guard_closed_lane(plan, raw):
    """Only immutable final evidence is admitted, never a current PID lookup."""
    journal = json.loads(raw['journal'])
    lane = json.loads(raw['lane_closure'])
    job = json.loads(Path(plan['producer_job']).read_bytes())
    start = json.loads(Path(plan['immutable_initial_start_receipt']).read_bytes())
    initial = next(row for row in start['rows'] if row['lane'] == 'native')
    need(journal['actual_child_terminal_exit_code'] in (0,2), 'Native lane did not return complete numeric scope')
    need(journal['natural_wait_completed'] and journal['exact_original_handle_birth_and_exit_match'], 'Missing original held natural terminal')
    need(journal['all_watched_source_and_job_bytes_unchanged'] and not journal['host_errors'], 'Native held source interval/host failure')
    need(journal['source_before'] == journal['source_after'], 'Native held source maps changed')
    child = initial['current_OS_observation']['child']
    need(journal['child']['PID'] == child['PID'] == 58452 and journal['child']['creation_FILETIME'] == child['actual_creation_FILETIME'] == 134369190575104373, 'Wrong original native child birth')
    owner = initial['current_OS_observation']['owner']
    need(journal['owner']['PID'] == owner['PID'] == 22092 and journal['owner']['creation_FILETIME'] == owner['actual_creation_FILETIME'] == 134369190570058634, 'Wrong original native owner birth')
    need(initial['allowed_scheme_ordinals'] == [2,3,4,5,6] and job['allowed_scheme_ordinals'] == [2,3,4,5,6], 'Wrong native missing-only scope')
    before = {normpath(k):v for k,v in journal['source_before'].items()}
    for path, digest in job['source_guard_pins'].items():
        need(before.get(normpath(path)) == digest, 'Actual held source map does not bind authorized source: ' + path)
    need(before.get(normpath(plan['producer_job'])) == initial['job_SHA256'], 'Original held job identity not present')
    need(lane['schema'] == 'actual-remaining-five-only-native-case014-source-closure-v1', 'Wrong lane closure schema')
    need(lane['source_and_input_interval_closed'] and lane['source_before'] == lane['source_after'] and not lane['host_error'], 'Native lane source/capture not closed')
    need(lane['effective_entry_exit_code'] == journal['actual_child_terminal_exit_code'], 'Native lane/held exit differ')
    need(not lane['first_completed_scheme_repeated'] and lane['new_channel_MC_RNG_calls'] == 0, 'Wrong old-first/MC scope')
    need([row['ordinal'] for row in lane['rows']] == [2,3,4,5,6], 'Native lane did not close the five expected ordinals')
    producer = json.loads(Path(plan['producer_plan']).read_bytes())
    need(lane['source_before'] == [{'path':p['path'],'SHA256':p['SHA256']} for p in producer['native_guard_sources']], 'Native internal source list differs from frozen plan')
    return journal, lane

def load_native(plan, out):
    """Canonicalize one actual native scheme; numeric values stay MAT-derived."""
    ordinal = plan['scheme_ordinal']
    need(ordinal in NAMES, 'Old firstscheme is outside this reader')
    name = NAMES[ordinal]
    flags = FLAGS[ordinal]
    paths = {key:Path(value) for key,value in plan['actual_inputs'].items()}
    raw = {key:path.read_bytes() for key,path in paths.items()}
    for key,path in paths.items():
        need(sha_bytes(raw[key]) == plan['source_and_input_pins'][str(path)], 'Loaded actual input digest differs: ' + key)
    journal = json.loads(raw['journal'])
    result = json.loads(raw['result'])
    original_scene = json.loads(raw['scene'])
    cfg = json.loads(raw['configuration'])
    local = json.loads(raw['scheme_closure'])
    root_row = json.loads(raw['scheme_root_closure'])
    lane = json.loads(raw['lane_closure'])
    lane_row = next(row for row in lane['rows'] if row['ordinal'] == ordinal)
    need(local == root_row == lane_row, 'Joint scheme result closure differs')
    need(local['scheme'] == name and local['actual_entry_exit'] in (0,2), 'Scheme closure is not a complete returned numeric result')
    need(result['scheme_names'] == [name] and result['scheme_ordinal'] == ordinal, 'Native result scheme mismatch')
    need(result['capture_complete_for_returned_scheme'] is True, 'Native capture reports incomplete returned state scope')
    need(len(cfg) == 28 and all(original_scene[key] == value for key,value in cfg.items()), 'Original 28 controls not embedded in scene')
    scene = copy.deepcopy(original_scene)
    if not flags[2]:
        for key in ('br_gain_re','br_gain_im'):
            scene[key] = np.zeros_like(np.asarray(scene[key])).tolist()
    false = {key:codec._unwrap(value) for key,value in loadmat(io.BytesIO(raw['MAT']),struct_as_record=False,squeeze_me=False,mat_dtype=False).items() if not key.startswith('__')}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        shadow = {key:codec._unwrap(value) for key,value in loadmat(io.BytesIO(raw['MAT']),struct_as_record=False,squeeze_me=False,mat_dtype=True).items() if not key.startswith('__')}
    need(set(false) == {'result','scene','cfg','recording'} and set(shadow) == set(false), 'Unexpected MAT top-level schema')
    notes = []
    for key,expected in [('result',result),('scene',scene),('cfg',cfg)]:
        codec.semantic_equal(false[key],expected,'MAT/'+key,notes)
    rec = false['recording']
    cls = shadow['recording']
    need(rec['schema'] == 'actual-native-first-scheme-returned-block-states-v1' and codec._scalar(rec['extra_objective_gradient_RNG_calls']) == 0, 'Wrong passive recording scope')
    source = rec['source_inputs']
    for key,expected in [('scene',scene),('configuration',cfg),('original_scene',original_scene),('scheme',name),('scheme_ordinal',ordinal)]:
        codec.semantic_equal(source[key],expected,'recording/source_inputs/'+key,notes)
    canonical_result = copy.deepcopy(result)
    for key in ('history','metrics','checks'):
        need(isinstance(result[key],list) and len(result[key]) == 1, 'Expected exactly one native scheme cell')
        canonical_result[key] = {name:copy.deepcopy(result[key][0])}
    need(canonical_result['checks'][name].get('status') == 'executed', 'No full returned state for this failed scheme; keep it unverified')
    blocks = codec._sequence(canonical_result['history'][name]['blocks'])
    canonical_result['history'][name]['blocks'] = blocks
    container_notes = []
    for call,block in enumerate(blocks,1):
        block['W']['QCQP'] = codec._sequence(block['W']['QCQP'])
        for kind,field,count_key,offset in [('W','objective','iterations',1),('RIS','objective','iterations',0),('RIS','PR_coefficients','updates',0),('rotation','objective','iterations',0),('rotation','steps','updates',0)]:
            status = block[kind]
            if field not in status:
                continue
            value = status[field]
            if type(value) in (int,float):
                need(status[count_key]+offset == 1, 'Scalar native container is not an original singleton')
                status[field] = [value]
                need(codec._float_bits(value) == codec._float_bits(status[field][0]), 'Singleton wrapping changed IEEE bits')
                container_notes.append(dict(AO_iteration=call,block=kind,field=field,original_scalar_float_hex=float(value).hex(),same_numeric_IEEE_bits=True))
    order = ('W','RCG','PGA') if flags[2] else ('W','PGA')
    returns = codec._sequence(rec['returns'])
    classes = codec._sequence(cls['returns'])
    count = len(blocks)*len(order)
    need(len(returns) == len(classes) == count == result['actual_returned_block_state_count'] and count > 0, 'Actual native return count/order incomplete')
    need(bool(codec._scalar(rec['initial_state']['with_RIS'])) == bool(flags[2]) and result['RCG_gate_applicable'] == bool(flags[2]), 'Wrong actual RIS applicability')
    receipts = []
    shapes = [('W',(4,6)),('theta',(36,)),('r',(6,))]
    previous = {key:codec.canonical_array(rec['initial_state'][key],cls['initial_state'][key],shape,'initial__'+key,receipts) for key,shape in shapes}
    lower = codec.canonical_array(rec['initial_state']['lower'],cls['initial_state']['lower'],(6,),'actual_lower',receipts)
    upper = codec.canonical_array(rec['initial_state']['upper'],cls['initial_state']['upper'],(6,),'actual_upper',receipts)
    width = np.r_[np.full(3,original_scene.get('rotation_bs_half_width',original_scene.get('rotation_half_width',np.pi/2)))*flags[0],np.full(3,original_scene.get('rotation_ris_half_width',original_scene.get('rotation_half_width',np.pi/2)))*flags[1]]
    codec.semantic_equal(lower,(-width).tolist(),'actual_bounds/lower',notes)
    codec.semantic_equal(upper,width.tolist(),'actual_bounds/upper',notes)
    rows = []
    arrays = {}
    counts = {'update_w':0,'update_theta':0,'update_rotation':0}
    methods = {'W':'update_w','RCG':'update_theta','PGA':'update_rotation'}
    for i,(state,class_state) in enumerate(zip(returns,classes)):
        call = i//len(order)+1
        block = order[i%len(order)]
        method = methods[block]
        need(codec._scalar(state['AO_iteration']) == call and state['block'] == block, 'Actual native returned block order mismatch')
        iota = float(codec._scalar(state['fixed_iota']))
        need(codec._float_bits(iota) == codec._float_bits(blocks[call-1]['iota']), 'Actual fixed AO iota differs')
        status = blocks[call-1][{'W':'W','RCG':'RIS','PGA':'rotation'}[block]]
        codec.semantic_equal(state['original_status'],status,'returned/'+str(i)+'/status',notes)
        keys = {}
        for key,shape in shapes:
            label = f'native_{ordinal}_{method}_{call:03d}__{key}'
            keys[key] = label
            arrays[label] = codec.canonical_array(state[key],class_state[key],shape,label,receipts)
            if key != {'W':'W','RCG':'theta','PGA':'r'}[block]:
                need(codec._float_bits(arrays[label].real) == codec._float_bits(previous[key].real) and codec._float_bits(arrays[label].imag) == codec._float_bits(previous[key].imag), 'An actual fixed component changed across block return')
        previous = {key:arrays[keys[key]] for key in ('W','theta','r')}
        scalar_flags = {key:copy.deepcopy(value) for key,value in status.items() if not isinstance(value,(list,dict))}
        rows.append(dict(method=method,call=call,fixed_iota=iota,arrays=keys,actual_returned_flags=scalar_flags))
        counts[method] += 1
    final_arrays = {key:previous[key].copy(order='F') for key in previous}
    final = canonical_result['metrics'][name]
    for key,value in [('w_re',final_arrays['W'].real),('w_im',final_arrays['W'].imag),('theta_re',final_arrays['theta'].real),('theta_im',final_arrays['theta'].imag),('rotation',final_arrays['r'])]:
        codec.semantic_equal(value,final[key],'actual_final/'+key,notes)
    need(canonical_result['original_controls'] == {key:scene[key] for key in ('W_solver','RCG_solver','PGA_solver','AO_solver')}, 'Actual native controls differ')
    receipt = dict(schema='actual-native-missing-only-MAT-scheme-typed-binding-v1',scheme_ordinal=ordinal,scheme_name=name,scheme_flags=list(flags),actual_native_input_SHA256={key:sha_bytes(value) for key,value in raw.items()},returned_states=count,actual_outer_blocks=len(blocks),actual_return_order=list(order),NoRIS_RCG_not_applicable_not_a_PASS=not bool(flags[2]),array_inventory_and_semantic_casts=receipts,JSON_transport_notes=notes,singleton_container_shape_normalizations=container_notes,class_shadow_warnings=[dict(type=type(w.message).__name__,message=str(w.message)) for w in caught],numeric_class_shadow_values_never_used=True,actual_complex_class_shape_and_signed_zero_from_MAT=True,all_fixed_components_between_returns_IEEE64_equal=True,original_scene_unchanged_except_effective_NoRIS_zero_br_gains=True,native_analytic_vectors_not_saved=True,no_optimizer_MP_objective_gradient_MC_calls_in_loader=True)
    put(out/'ACTUAL_NATIVE_MAT_TYPED_STATE_SCHEMA_AND_INPUT_BINDING_V1.json',receipt)
    return dict(j=journal,sm=dict(rows=rows,counts=counts),result=canonical_result,scene=scene,arrays=arrays,final_arrays=final_arrays,rotation_width=upper,rotation_lower=lower,rotation_upper=upper,with_RIS=bool(flags[2]),receipt=receipt)
