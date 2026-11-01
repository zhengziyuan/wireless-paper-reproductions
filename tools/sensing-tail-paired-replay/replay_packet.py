"""Replay all exported original5001..6000 final states and outer stop records.

No optimizer, native MATLAB process or new MP reference is executed.
Pure original initializer functions replay only their already bound source contract.
The fresh binary64 geometry replay is bound to completed MP80/100 receipts.
Historical complete initial states and original inner gradients are unavailable.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
from copy import deepcopy
from datetime import datetime
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import statistics
import sys
import tarfile
import time
from types import SimpleNamespace
import numpy as np
import reference_kernel as kernel

DEFAULT_PACKET=Path(__file__).resolve().parents[2]/'strict/validation/mis-sensing-tail1000-paired-final-state-20261018'
FIELDS=('phi','theta','X','eta','lam','padded','fields','amplitude2','echo','denominator','gamma','scheduled',
        'binary_columns','residual','weights','weighted','coefficient','field_gradient','aperture_gradient','gp','gt','tp','tt','xr','ge')
SHAPES=dict(phi=(400,),theta=(256,),X=(9,25),eta=(),lam=(9,),padded=(25,400),fields=(9,25),amplitude2=(9,25),
    echo=(9,25),denominator=(9,25),gamma=(9,25),scheduled=(9,),binary_columns=(9,),residual=(9,),weights=(9,25),
    weighted=(9,25),coefficient=(9,25),field_gradient=(9,25),aperture_gradient=(400,25),gp=(400,),gt=(256,),tp=(400,),tt=(256,),xr=(9,25),ge=())

def require(value,message):
    if not value:raise ValueError(message)
def read(path):return json.loads(path.read_bytes())
def sha_bytes(raw):return hashlib.sha256(raw).hexdigest()
def sha(path):
    result=hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(1048576),b''):result.update(block)
    return result.hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8');temporary.replace(path)

def exact_scope(rows):
    require([row['original_start'] for row in rows]==list(range(5001,6001)),
        'All original1000 pairs, including every failed result, are required exactly once')

def validate_gate_boundaries(value):
    for name in ('actual_historical_complete_initial_states_available','all_original_inner_gradients_available',
                 'end_to_end_dual_language_numerical_agreement_pass','author_reference_agreement_pass','full_original6000_or_six_papers_pass'):
        require(value[name] is False,'A partial source/given-model scope was promoted to an unsupported broader gate')

def unpack(packet,output):
    manifest=read(packet/'archive-manifest.json');validate_gate_boundaries(manifest['gate_boundaries'])
    require(manifest['original_full_population']==6000 and manifest['selected_original_range']==[5001,6000] and
        manifest['actual_paired_slots']==1000 and manifest['actual_final_states']==2000,'Retain original and export population scopes')
    blocks=[]
    for index,part in enumerate(manifest['archive']['parts']):
        require(part['index']==index and PurePosixPath(part['name']).name==part['name'],'Invalid exact archive part route/order')
        raw=(packet/part['name']).read_bytes();require(len(raw)==part['bytes'] and sha_bytes(raw)==part['SHA256'],'Archive part numeric bytes differ')
        blocks.append(raw)
    archive=b''.join(blocks)
    require(len(archive)==manifest['archive']['bytes'] and sha_bytes(archive)==manifest['archive']['SHA256'],'Complete evidence archive bytes differ')
    root=output/'inputs';root.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as handle:
        members=handle.getmembers();names=[member.name for member in members]
        require(len(names)==len(set(names)) and set(names)==set(manifest['payloads']),'Complete exact evidence payload scope differs')
        for member in members:
            name=PurePosixPath(member.name)
            require(member.isfile() and not name.is_absolute() and '..' not in name.parts,'Unsafe evidence payload member')
            raw=handle.extractfile(member).read();binding=manifest['payloads'][member.name]
            require(len(raw)==binding['bytes'] and sha_bytes(raw)==binding['SHA256'],'A complete final-state/stop payload differs')
            path=root.joinpath(*name.parts);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    return root,manifest

def binary64_basis(settings,point,prior):
    require(point==dict(ms1=[20,20],ms2=[16,16],Kphi=3,Ktheta=3),'Retain full400/256 geometry and all nine targets')
    require(settings['reference_echo_unit']=='inverse_watt' and settings['power_dbm']==30 and
            settings['effective_reference_gain_factor']==1 and prior['actual_noise_over_power']>0 and prior['actual_echo_beta_squared']>0,
            'Retain original explicit physical units and positive echo/noise scales')
    expected_beta=10**(settings['reference_echo_db']/10)
    require(abs(prior['actual_echo_beta_squared']-expected_beta)<=8*np.finfo(float).eps*expected_beta and
        prior['actual_noise_over_power']==1,'The reused completed MP scales must match the exact retained physical-unit contract')
    response=[]
    for elevation in (30,50,70):
        e=math.pi*elevation/180
        for azimuth in (0,45,90):
            a=math.pi*azimuth/180;x=math.sin(e)*math.cos(a)+settings['incidence_direction_cosines'][0]
            y=math.sin(e)*math.sin(a)+settings['incidence_direction_cosines'][1]
            row=[]
            for i in range(20):
                for j in range(20):
                    phase=2*math.pi*settings['spacing_over_wavelength']*(i*x+j*y)
                    row.append(complex(math.cos(phase),math.sin(phase)))
            response.append(row)
    indices=np.array([[(i+di)*20+j+dj for di in range(16) for dj in range(16)] for i in range(5) for j in range(5)],dtype=np.int64)
    return np.asarray(response,dtype=np.complex128),indices,prior['actual_echo_beta_squared'],prior['actual_noise_over_power']

def assert_source_kernel(root):
    source=root/'source/original-independent-audit.py'
    require(sha(source)=='1c39fa1aff6e6740eb8087012c7cf1e0da37f6a033ac6ee64ab1d4f6ef17c643','Original completed independent reference source differs')
    original=ast.parse(source.read_text(encoding='utf-8'));current=ast.parse(Path(kernel.__file__).read_text(encoding='utf-8'))
    for name in ('require','simplex_decimal','physical'):
        a=next(node for node in original.body if getattr(node,'name',None)==name)
        b=next(node for node in current.body if getattr(node,'name',None)==name)
        require(ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False),'An original independent mathematical function changed')

def replay_physics(view,response,indices,beta,noise,settings,capture=True):
    arrays={}
    def observe(frame,event,arg):
        if event=='return' and frame.f_code is kernel.physical.__code__:
            for name in FIELDS:arrays[name]=np.array(frame.f_locals[name],copy=True)
    before=sys.getprofile()
    try:
        if capture:sys.setprofile(observe)
        result=kernel.physical(view,response,indices,beta,noise,settings)
    finally:
        if capture:sys.setprofile(before)
    require(result['saved_physical_fields_match'] and result['saved_KKT_residual_fields_match'] and result['saved_KKT_boolean_reconfirmed'],
            'Fresh complete exported physical fields, binary argmax or original KKT record differ')
    if capture:
        require(set(arrays)==set(FIELDS),'A full fresh physical intermediate is missing')
        for name,shape in SHAPES.items():
            require(arrays[name].shape==shape and np.all(np.isfinite(arrays[name])),'A complete fresh physical intermediate shape/finite gate differs')
    return result,arrays

def stop_record_check(view,settings):
    history=view['history'];status=view['summary']['solver_status']
    require(len(history)==30 and [row['outer_iteration'] for row in history]==list(range(1,31)), 'All original30 outer records required')
    require(all('inner' not in row and row['actual_original_inner_entries']>=1 and
        len(row['original_inner_trace_logical_JSON_SHA256'])==64 for row in history),
        'Retain inner-log counts/bindings; do not substitute unavailable raw inner gradients')
    stationarity=[row['stop']['projected_kkt_norm']<=row['epsilon_used'] for row in history]
    reasons=[row['stop']['reason'] for row in history];failures=sum(reason not in ('gradient_tolerance','iteration_cap') for reason in reasons)
    early=history[-1]['step']<=settings['minimum_step'] and history[-1]['epsilon_next']<=settings['epsilon_min'];budget=True
    require(status['all_inner_tolerances_satisfied']==all(stationarity) and status['final_inner_stationary']==stationarity[-1] and
            status['inner_iteration_cap_exits']==reasons.count('iteration_cap') and status['inner_failure_exits']==failures and
            status['outer_early_stopping_met']==early and status['prescribed_outer_budget_execution_complete']==budget and
            status['outer_termination_valid']==(early or budget) and status['convergence_verified']==bool(all(stationarity) and
            (early or budget) and status['continuation_complete'] and not failures and status['original_problem_kkt_verified']),
            'An original failed, capped, stationary or outer-budget classification was changed')
    return dict(original_convergence_pass=bool(status['convergence_verified']),original_final_KKT_pass=bool(status['original_problem_kkt_verified']),
        actual_original_outer_stops=30,actual_original_saved_inner_entries=sum(row['actual_original_inner_entries'] for row in history),
        original_cap_exits=status['inner_iteration_cap_exits'],original_other_failure_exits=failures)

def collision_check(view):
    X=np.asarray(view['state']['X']);binary=np.asarray(view['metrics']['binary_schedule'])
    actual=np.argmax(X,axis=1);expected=np.zeros((9,25));expected[np.arange(9),actual]=1
    require(np.array_equal(binary,expected),'Every exported actual X argmax must match its complete recorded binary schedule')
    groups={}
    for target,column in enumerate(actual.tolist()):groups.setdefault(column,[]).append(target)
    multiplicity=max(map(len,groups.values()));bound=None if multiplicity==1 else 1/(multiplicity-1)
    if bound is not None:require(view['metrics']['min_binary_metric']<bound,'Positive-noise common-position minimum SINR violates1/(m-1)')
    return dict(actual_raw_X_argmax_verified=True,selected_columns_zero_based=actual.tolist(),maximum_shared_position_multiplicity=multiplicity,
        conditional_minimum_binary_SINR_upper_bound=bound,collision_groups=[dict(column_zero_based=column,targets_zero_based=targets)
            for column,targets in sorted(groups.items()) if len(targets)>1])

def binding_check(case,binding,root,settings,manifest,population):
    slot=case['original_start'];require(slot==binding['original_start'],'Paired original slot binding differs')
    require(case['original_full_population']==6000 and case['original_budgets']==dict(starts=6000,outer=30,RCG=4000),
            'Retain original6000/30/4000 budgets')
    require(sha_bytes(canonical(case))==binding['exported_case_logical_JSON_SHA256'],'Every exported logical numeric leaf must retain its complete source projection')
    receipt=read(root/f'native-receipts/start-{slot:04d}.json');inputs=read(root/f'native-inputs/start-{slot:04d}.json')
    identity=population['cases'][slot-1];before=241219071*pow(16807,(slot-1)*881,2147483647)%2147483647
    require(receipt['original_start']==slot and receipt['actual_original_population']==6000 and receipt['initial_rng_before']==identity['initial_rng_before']==before and
        receipt['initial_rng_after']==identity['initial_rng_after'] and receipt['initializer_draws']==881 and
        receipt['plan_sha256']==sha(root/'native-original6000-plan.json') and receipt['engine_sha256']==manifest['source_manifest']['source']['mis_sensing_strict_engine.m'] and
        receipt['source_unchanged_during_run'] and not receipt['execution_error'],'Original full-input/source/RNG/native receipt differs')
    expected=deepcopy(settings);expected['initialization']['seed']=before
    require(inputs==expected and sha(root/f'native-inputs/start-{slot:04d}.json')==receipt['transport_settings_sha256'],
            'One original physical/algorithm control or exact native seed transport changed')
    require(case['matlab']['summary']['solver_status']==receipt['actual_solver_status'] and
        case['matlab']['state']['eta']==receipt['actual_eta'],'One original native return or failed stop was changed')
    for language,cache_name in [('matlab',f'reference/matlab-start-{slot:04d}.json'),('python',f'reference/python-start-{slot:04d}.json')]:
        cached=read(root/cache_name);view=case[language];status=view['summary']['solver_status']
        require(all(cached['checks'].values()),'An original independent physical/KKT/stop reference did not pass its recorded-scalar comparison')
        if language=='matlab':
            require(cached['original_start']==slot and cached['all_saved_state_checks_pass'] and
                cached['native_receipt_sha256']==sha(root/f'native-receipts/start-{slot:04d}.json') and
                cached['original_native_JSON_sha256']==receipt['payload_original_json_sha256']==binding['original_native_complete_raw_JSON_SHA256'] and
                cached['original_convergence_feasibility_pass']==status['convergence_verified'], 'Original native reference/failed outcome binding changed')
        else:
            require(cached['start']==slot and cached['all_saved_record_checks_pass'] and
                cached['actual_auditor_sha256']=='1c39fa1aff6e6740eb8087012c7cf1e0da37f6a033ac6ee64ab1d4f6ef17c643' and
                cached['raw_saved_record_sha256']==binding['original_Python_complete_gzip_SHA256'] and
                cached['original_convergence_pass_retained']==status['convergence_verified'] and
                view['summary']['start']==slot and view['summary']['point_index']==0,
                'Original Python reference/failed outcome binding changed')

def primitive_uniform_match(actual,expected):
    require(np.array_equal(actual.view(np.uint64),expected.view(np.uint64)),
            'One native source-contract primitive uniform differs by at least one bit')

def initializer_coordinate_match(actual,expected):
    require(actual.shape==expected.shape==(1538,) and np.all(np.isfinite(actual)) and np.all(np.isfinite(expected)),
            'All finite1538 source-contract initial coordinates required')
    error=float(np.max(np.abs(actual-expected)))
    require(error<=8*np.finfo(float).eps,'One complete source-contract initializer coordinate mapping differs')
    return error

def initializer_source_contract(root,output):
    plan=read(root/'initializer/plan.json');require(plan['expected_cases']==1000 and
        plan['original_source_initial_states_saved_in_actual_historical_records'] is False and
        plan['reconstructed_source_contract_is_actual_historical_initial_state_verification'] is False,
        'Initializer recipe replay is not an observed historical complete input witness')
    tree=ast.parse((root/'source/original-python-run.py').read_text(encoding='utf-8'))
    nodes=[node for node in tree.body if getattr(node,'name',None) in ('PortableRandom','initialize')]
    require(len(nodes)==2,'Exact original pure initializer functions required')
    namespace={'np':np};exec(compile(ast.Module(body=nodes,type_ignores=[]),'original pure initializer','exec'),namespace)
    uniforms=np.fromfile(root/'initializer/native-uniforms-f64le.bin',dtype='<f8')
    states=np.fromfile(root/'initializer/native-initial-states-f64le.bin',dtype='<f8')
    require(uniforms.size==881000 and states.size==1538000,'Full actual source-contract native arrays required')
    uniforms=uniforms.reshape(1000,881);states=states.reshape(1000,1538)
    settings=read(root/'original-settings.json');population=read(root/'native-original6000-plan.json');maximum=0.;records=[]
    for index,slot in enumerate(range(5001,6001)):
        identity=population['cases'][slot-1];state=identity['initial_rng_before'];expected=[]
        for _ in range(881):state=state*16807%2147483647;expected.append(state/2147483647)
        expected=np.asarray(expected,dtype=np.float64)
        primitive_uniform_match(uniforms[index],expected)
        require(state==identity['initial_rng_after'],'One exact source-contract end-boundary differs')
        rng=namespace['PortableRandom'](identity['initial_rng_before']);z=namespace['initialize'](SimpleNamespace(targets=9,U=25,M=400,N=256),settings,rng)
        vector=np.concatenate((z['phi'].real,z['phi'].imag,z['theta'].real,z['theta'].imag,z['X'].ravel(),np.atleast_1d(z['eta'])))
        error=initializer_coordinate_match(states[index],vector);maximum=max(maximum,error)
        require(rng.state==state,'One complete original source-contract initializer end-boundary differs')
        records.append(dict(original_start=slot,all881_native_uniforms_bit_exact=True,all1538_initial_state_coordinates_compared=True,maximum_coordinate_gap=error))
    value=dict(actual_source_contract_cases=1000,actual_native_uniforms_bit_exact=881000,actual_initial_state_real_coordinates_compared=1538000,
        maximum_initial_coordinate_gap=maximum,actual_historical_complete_initial_state_witness=False,actual_original_optimizer_calls=0,records=records)
    write(output/'all1000-initializer-source-contract-replay.json',value)
    return value,uniforms,states

def stats(values):
    ordered=sorted(values);position=(len(ordered)-1)*.95;lower=math.floor(position)
    return dict(count=len(ordered),minimum=ordered[0],median=statistics.median(ordered),
        p95=ordered[lower]+(position-lower)*(ordered[min(lower+1,len(ordered)-1)]-ordered[lower]),maximum=ordered[-1],mean=math.fsum(ordered)/len(ordered))

def replay(packet,output):
    require(not output.exists(),'Preserve existing cold proof; use a new output directory')
    output.mkdir(parents=True);began=time.perf_counter();root,archive=unpack(packet,output);assert_source_kernel(root)
    settings=read(root/'original-settings.json');manifest=read(root/'python-original6000-manifest.json');population=read(root/'native-original6000-plan.json')
    require(settings==manifest['settings'] and (settings['number_of_starts'],settings['outer_iterations'],settings['rcg_max_iterations'])==(6000,30,4000),
            'Original physical, scene and per-start budgets must match both saved languages')
    prior=read(root/'prior-MP-reference-summary.json');response,indices,beta,noise=binary64_basis(settings,manifest['figure']['points'][0],prior)
    index=read(root/'pair-provenance-index.json');exact_scope(index)
    geometry=output/'fresh-final-fields/complete-original-geometry.npz';geometry.parent.mkdir(parents=True);np.savez_compressed(geometry,response=response,indices=indices,beta=np.asarray(beta),noise=np.asarray(noise))
    initial,uniforms,initial_states=initializer_source_contract(root,output)
    records=[];contingency=Counter();collision={'matlab':Counter(),'python':Counter()};passed_collision={'matlab':Counter(),'python':Counter()}
    max_metric=max_stationarity=0.;raw_coordinates=0;states_checked=0;first_case=failed_case=None;all_fields_coordinates=0
    for item in index:
        slot=item['original_start'];path=root/f'states/slot-{slot:04d}.json';case=read(path)
        binding_check(case,item,root,settings,manifest,population)
        one=dict(original_start=slot,exported_case_SHA256=sha(path),original_views_logical_JSON_SHA256=item['exported_case_logical_JSON_SHA256'])
        for language in ('matlab','python'):
            view=case[language];stops=stop_record_check(view,settings);physics,fields=replay_physics(view,response,indices,beta,noise,settings)
            positions=collision_check(view);multiplicity=str(positions['maximum_shared_position_multiplicity']);collision[language][multiplicity]+=1
            if stops['original_convergence_pass']:passed_collision[language][multiplicity]+=1
            field_file=output/f'fresh-final-fields/slot-{slot:04d}-{language}.npz';np.savez_compressed(field_file,**fields)
            fields_scope={name:dict(shape=list(array.shape),dtype=str(array.dtype),numeric_real_coordinates=int(array.size*(2 if np.iscomplexobj(array) else 1)))
                for name,array in fields.items()}
            count=sum(value['numeric_real_coordinates'] for value in fields_scope.values());all_fields_coordinates+=count
            one[language]=dict(original_stops=stops,independent_physics_and_final_KKT=physics,actual_raw_X_binary_schedule=positions,
                complete_fresh_field_file=field_file.relative_to(output).as_posix(),complete_fresh_field_file_SHA256=sha(field_file),
                complete_fresh_field_scope=fields_scope,all_fresh_numeric_real_coordinates=count,
                full_final_state_real_coordinates=1538,all_original_recorded_final_values_replayed=True)
            max_metric=max(max_metric,physics['maximum_physical_field_error']);max_stationarity=max(max_stationarity,physics['stationarity_norm_error'])
            raw_coordinates+=1538;states_checked+=1
        one['native_eta']=case['matlab']['state']['eta'];one['python_eta']=case['python']['state']['eta'];one['signed_eta_gap']=one['native_eta']-one['python_eta']
        flags=[case[language]['summary']['solver_status']['convergence_verified'] for language in ('matlab','python')]
        key=f"native_{'pass' if flags[0] else 'fail'}_python_{'pass' if flags[1] else 'fail'}";contingency[key]+=1
        write(output/f'fresh-paired-records/slot-{slot:04d}.json',one);records.append(one)
        if first_case is None:first_case=(case,item)
        if failed_case is None and not flags[0]:failed_case=(case,item)
        if len(records)%25==0 or slot==6000:
            progress=dict(observed_local=datetime.now().astimezone().isoformat(),actual_complete_paired_slots=len(records),actual_complete_final_states=states_checked,
                actual_complete_final_state_real_coordinates=raw_coordinates,actual_complete_fresh_field_real_coordinates=all_fields_coordinates,
                original_stop_contingency=dict(contingency),elapsed_seconds=time.perf_counter()-began,optimizer_or_original_physical_MP_calls=0)
            write(output/'progress.json',progress);print(json.dumps(progress),flush=True)
    require(dict(contingency)==dict(native_pass_python_pass=802,native_fail_python_pass=76,native_pass_python_fail=76,native_fail_python_fail=46),
            'Retain the actual original1000-pair stop contingency, including all failures')
    require({key:dict(value) for key,value in collision.items()}=={'matlab':{'1':984,'2':16},'python':{'1':981,'2':19}},
            'Actual full2000 X/argmax census differs from the copied original reported schedule census')
    controls=[]
    def reject(name,call):
        try:call()
        except (ValueError,KeyError,AssertionError) as error:controls.append(dict(control=name,rejected=True,reason=str(error)));return
        raise AssertionError('Invalid complete paired evidence accepted:'+name)
    case,item=first_case;failed,failed_item=failed_case
    reject('all_original_native_failed_pairs_filtered',lambda:exact_scope([entry for entry in index if entry['original_start']!=failed['original_start']]))
    bad=deepcopy(index);bad[-1]=deepcopy(bad[0]);reject('count1000_but_one_slot_duplicate_and_one_missing',lambda:exact_scope(bad))
    bad=deepcopy(case);bad['original_full_population']=1000
    reject('original6000_population_relabelled_as1000',lambda:binding_check(bad,item,root,settings,manifest,population))
    bad=deepcopy(case);bad['original_budgets']['RCG']=400
    reject('original4000_inner_budget_reduced_to400',lambda:binding_check(bad,item,root,settings,manifest,population))
    bad=deepcopy(case);bad['python']['state']['phi']['real'][0]+=1e-3
    reject('one_actual_final_phase_coordinate_changed',lambda:binding_check(bad,item,root,settings,manifest,population))
    bad=deepcopy(failed['matlab']);bad['summary']['solver_status']['convergence_verified']=True
    reject('one_original_failed_convergence_flag_upgraded',lambda:stop_record_check(bad,settings))
    bad=deepcopy(case['python']);bad['history'].pop()
    reject('one_original_outer_stop_omitted',lambda:stop_record_check(bad,settings))
    bad=deepcopy(case['python']);old=int(np.argmax(bad['state']['X'][0]));bad['metrics']['binary_schedule'][0][old]=0;bad['metrics']['binary_schedule'][0][(old+1)%25]=1
    reject('binary_schedule_changed_without_raw_X',lambda:collision_check(bad))
    bad=deepcopy(case['python']);angle=complex(bad['state']['phi']['real'][0],bad['state']['phi']['imag'][0])*complex(math.cos(.001),math.sin(.001));bad['state']['phi']['real'][0]=angle.real;bad['state']['phi']['imag'][0]=angle.imag
    reject('unit_modulus_preserved_but_actual_phase_and_physics_changed',lambda:replay_physics(bad,response,indices,beta,noise,settings,False))
    bad=deepcopy(case['python']);bad['metrics']['min_binary_metric']+=.01
    reject('one_saved_binary_physical_metric_changed',lambda:replay_physics(bad,response,indices,beta,noise,settings,False))
    bad=deepcopy(case['python']);bad['summary']['solver_status']['original_problem_kkt_certificate']['stationarity_norm']+=.01
    reject('one_original_final_KKT_residual_changed',lambda:replay_physics(bad,response,indices,beta,noise,settings,False))
    reject('nine_target_geometry_reduced',lambda:binary64_basis(settings,dict(ms1=[10,10],ms2=[8,8],Kphi=3,Ktheta=3),prior))
    bad=deepcopy(prior);bad['actual_echo_beta_squared']*=100
    reject('unverified_factor100_echo_scale_substituted',lambda:binary64_basis(settings,manifest['figure']['points'][0],bad))
    reject('target_response_rows_permuted',lambda:replay_physics(case['python'],response[::-1].copy(),indices,beta,noise,settings,False))
    bad=uniforms[0].copy();bad[880]=np.nextafter(bad[880],np.inf)
    reject('one_initializer_primitive_changed_by_one_ULP',lambda:primitive_uniform_match(bad,uniforms[0]))
    bad=initial_states[0].copy();bad[1312:1537]=bad[1312:1537].reshape(9,25).T.ravel()
    reject('initializer_X_primitive_draw_order_transposed',lambda:initializer_coordinate_match(bad,initial_states[0]))
    bad=deepcopy(archive['gate_boundaries']);bad['actual_historical_complete_initial_states_available']=True
    reject('source_contract_relabelled_as_historical_actual_input',lambda:validate_gate_boundaries(bad))
    bad=deepcopy(archive['gate_boundaries']);bad['end_to_end_dual_language_numerical_agreement_pass']=True
    reject('different_paired_results_promoted_to_dual_numerical_pass',lambda:validate_gate_boundaries(bad))
    bad=deepcopy(archive['gate_boundaries']);bad['author_reference_agreement_pass']=True
    reject('given_model_replay_promoted_to_author_reference_match',lambda:validate_gate_boundaries(bad))
    write(output/'actual-complete-paired-state-stop-physics-and-scope-negative-controls.json',controls)
    gaps=[row['signed_eta_gap'] for row in records]
    result=dict(observed_local=datetime.now().astimezone().isoformat(),scope='Complete original5001..6000 paired final-state and outer-stop export replay; original full population remains6000',
        actual_complete_paired_slots=1000,actual_complete_final_states=states_checked,actual_complete_final_state_real_coordinates=raw_coordinates,
        actual_complete_original_outer_records_each_language=30000,actual_complete_fresh_numeric_real_coordinates=all_fields_coordinates,
        actual_full_fresh_field_arrays_per_final_state=len(FIELDS),actual_full_fresh_field_files=states_checked,
        original_stop_contingency=dict(contingency),original_failed_or_unverified_retained_each_language=122,
        actual_raw_X_argmax_and_binary_schedule_states_checked=states_checked,
        actual_full_raw_X_maximum_position_multiplicity_census={key:dict(value) for key,value in collision.items()},
        original_pass_actual_X_multiplicity_census={key:dict(value) for key,value in passed_collision.items()},
        maximum_same_state_physical_metric_error=max_metric,maximum_original_KKT_norm_error=max_stationarity,
        fresh_reference='Binary64 trigonometry and unchanged original independent Decimal60 final-KKT functions, bound to completed MP80/100 cached reference receipts',
        actual_original_optimizer_calls=0,actual_new_production_random_trials=0,actual_new_physical_MP80_MP100_reference_calls=0,
        actual_pure_source_contract_initializer_replay_calls=1000,actual_original_pure_rng_value_calls_in_source_contract_replay=3000,
        initial_source_contract=dict(actual_native_uniforms_bit_exact=881000,actual_initial_state_real_coordinates_compared=1538000,maximum_coordinate_gap=initial['maximum_initial_coordinate_gap']),
        absolute_eta_gap=stats([abs(value) for value in gaps]),signed_eta_gap=stats(gaps),
        actual_negative_controls_rejected=len(controls),gate_boundaries=archive['gate_boundaries'],
        archive_manifest_SHA256=sha(packet/'archive-manifest.json'),complete_geometry_file_SHA256=sha(geometry),
        source_SHA256={name:sha(Path(__file__).parent/name) for name in ('replay_packet.py','reference_kernel.py','requirements.txt')},
        elapsed_seconds=time.perf_counter()-began)
    write(output/'summary.json',result);return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--packet',type=Path,default=DEFAULT_PACKET)
    parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args()
    print(json.dumps(replay(args.packet.resolve(),args.output_dir.resolve())),flush=True)
