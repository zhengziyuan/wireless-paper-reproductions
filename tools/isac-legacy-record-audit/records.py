"""Complete saved-record, source-declaration and cohort checks, without optimizers."""
from collections import Counter
from copy import deepcopy
import ast
import csv
import gzip
import itertools
import json
import math
from pathlib import Path
import operator
import struct
import numpy as np
import evidence as e
from evidence import require

KEYS=('seed','pB','pR','rotB_deg','rotR_deg','Nx','Ny','Mx','My','P_dBm')
METRICS=('sumrate','mse','itAO')

def encode_array(value):
    value = np.asarray(value)
    if value.dtype == object:
        return dict(shape=list(value.shape), kind='cell',
                    cells=[encode_array(v) for v in value.ravel(order='C')])
    require(value.dtype.kind in 'fciu b'.replace(' ', ''), 'An unhandled saved MAT type occurred')
    require(np.isfinite(value).all(), 'A nonfinite saved numeric value needs explicit handling')
    return dict(shape=list(value.shape), kind='numeric', source_dtype=str(value.dtype),
                real_hex=[float(np.real(v)).hex() for v in value.ravel(order='C')],
                imag_hex=[float(np.imag(v)).hex() for v in value.ravel(order='C')])

def decode_table(payload):
    require(payload['actual_saved_table_rows']==1000 and payload['actual_saved_table_variables']==13,
            'The entire actual saved1000-by13 MAT table is required')
    names=payload['exact_saved_column_names']
    require(names==list(KEYS+METRICS),'The full native table schema changed')
    columns={}
    for column in payload['columns']:
        name=column['name'];require(name in names and name not in columns,'A table field is duplicated/unknown')
        require(column['shape']==[1000,1] and len(column['complete_real_binary64_hex'])==1000,
                'One full1000-row table column is missing')
        values=[]
        for encoded in column['complete_real_binary64_hex']:
            require(isinstance(encoded,str) and len(encoded)==16,'A complete native binary64 ordinate is absent')
            value=struct.unpack('>d',bytes.fromhex(encoded))[0]
            require(struct.pack('>d',value).hex()==encoded.lower(),'An exact native binary64 table value changed')
            values.append(value)
        columns[name]=values
    require(set(columns)==set(names),'A complete saved table field is absent')
    return [{name:columns[name][i] for name in names} for i in range(1000)]

def key(row):return tuple(float(row[name]) for name in KEYS)

def verify_native_rows(rows,jobs):
    require(len(rows)==len(jobs)==1000,'All actual saved MAT rows and job descriptors are required')
    require(len({key(row) for row in rows})==1000,'A full saved row/job slot was aliased or removed')
    for i,(row,job) in enumerate(zip(rows,jobs)):
        require(key(row)==key(job),'A complete actual native MAT/job parameter binding differs at '+str(i))

def verify_native_export_csv(rows,csv_rows):
    require(len(rows)==len(csv_rows)==1000,'The full native-generated1000 CSV export is required')
    for row,csv_row in zip(rows,csv_rows):
        require(key(row)==key(csv_row),'A native-generated full table CSV parameter changed')
        for name in METRICS:
            a,b=row[name],float(csv_row[name])
            require((math.isnan(a) and math.isnan(b)) or
                    (a==b if not math.isfinite(a) else abs(a-b)<=1e-12*(1+abs(a))),
                    'A complete native-generated CSV/table ordinate differs')

def number(text):
    """Interpret only a numeric arithmetic literal, without eval or MATLAB."""
    node=ast.parse(text.strip().replace('^','**'),mode='eval').body
    operations={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,
                ast.Div:operator.truediv,ast.Pow:operator.pow}
    def visit(item):
        if isinstance(item,ast.Constant) and type(item.value) in (int,float):return item.value
        if isinstance(item,ast.UnaryOp) and type(item.op) in (ast.USub,ast.UAdd):
            return -visit(item.operand) if isinstance(item.op,ast.USub) else visit(item.operand)
        if isinstance(item,ast.BinOp) and type(item.op) in operations:return operations[type(item.op)](visit(item.left),visit(item.right))
        raise ValueError('Only explicit saved numeric arithmetic is allowed')
    return visit(node)

def literals(text):
    parts=text.strip().split(':')
    if len(parts)==1:return [number(parts[0])]
    require(len(parts) in (2,3),'Unsupported saved scalar/range literal')
    values=[number(x) for x in parts]
    start,step,end=(values[0],1,values[1]) if len(values)==2 else values
    require(all(float(x).is_integer() for x in (start,step,end)) and step>0,'Only the saved integer sweep ranges are interpreted')
    return list(range(int(start),int(end)+1,int(step)))

def whole_cohort(candidate,actual):
    require(len(candidate)==len(actual)==1000,'The complete actual saved1000 task cohort is required')
    require(Counter(map(key,candidate))==Counter(map(key,actual)),
            'A full scenario/seed/power/array/rotation task label differs, despite any equal total count')


def decode_array(encoded):
    require(isinstance(encoded,dict) and encoded.get('kind') in ('numeric','cell'),
        'A complete saved numeric/cell array is required')
    shape=encoded.get('shape')
    require(isinstance(shape,list) and len(shape)==2 and all(type(n)==int and 0<=n<=4096 for n in shape),
        'An original bounded saved array shape is required')
    size=math.prod(shape);require(size<=100000,'The complete saved array exceeds the declared small-state scope')
    if encoded['kind']=='cell':
        require(set(encoded)=={'shape','kind','cells'} and len(encoded['cells'])==size,'A complete saved cell is absent')
        result=np.empty(shape,dtype=object)
        for index,value in zip(np.ndindex(*shape),encoded['cells']):result[index]=decode_array(value)
    else:
        require(set(encoded)=={'shape','kind','source_dtype','real_hex','imag_hex'},'A saved numeric component is missing')
        dtype=encoded['source_dtype'];require(dtype in ('float64','complex128','uint8'),'An unexpected original numeric dtype occurred')
        require(len(encoded['real_hex'])==len(encoded['imag_hex'])==size,'A complete saved real/imag ordinate is missing')
        real=[float.fromhex(x) for x in encoded['real_hex']];imag=[float.fromhex(x) for x in encoded['imag_hex']]
        require(all(math.isfinite(x) for x in real+imag),'One actual saved primitive is nonfinite')
        if dtype=='complex128':value=[complex(a,b) for a,b in zip(real,imag)]
        else:
            require(all(x==0 for x in imag),'A real-valued saved array contains a nonzero imaginary coordinate');value=real
        result=np.asarray(value,dtype=np.dtype(dtype)).reshape(shape,order='C')
    require(encode_array(result)==encoded,'The complete original numeric array does not round-trip exactly')
    return result


def observations(encoded):
    if encoded['kind']=='cell':return sum(observations(value) for value in encoded['cells'])
    return len(encoded['real_hex'])+len(encoded['imag_hex'])


def verify_grid(rate, mse, combos):
    require(rate.shape == mse.shape == (20, 5), 'The complete saved 20 by 5 grid is required')
    require([int(x['pB']) for x in combos] == [1, 2, 3, 4, 5], 'The nominal five exponent labels changed')
    require(all(np.array_equal(rate[:, 0], rate[:, j]) for j in range(1, 5)),
            'One full saved rate column differs from the duplicate-column observation')
    require(all(np.array_equal(mse[:, 0], mse[:, j]) for j in range(1, 5)),
            'One full saved MSE column differs from the duplicate-column observation')


def verify_power(value):
    array=decode_array(value['all_rate_values'])
    require(array.shape==(10,6) and value['powers_dBm']==[0,2,4,6,8,10],
        'Every original10-by6 power record and original power label is required')
    zeros=[i for i,row in enumerate(array) if np.all(row==0)]
    require(zeros==value['exact_all_zero_rows']==[9],'The actual complete zero row must be retained without inferring its cause')
    return array


def declared_candidates(candidates,rows):
    require(len(candidates)==2,'Both complete preserved m/asv declaration cohorts are required')
    names=('pB_vec','pR_vec','rotB_max_deg_vec','rotR_max_deg_vec','Ny_vec','My_vec','P_dBm_vec')
    output=[];saved_keys=set(map(key,rows))
    for candidate in candidates:
        settings=candidate['declared_sweep_literals'];require(set(settings)==set(names),'A complete declared sweep field is absent')
        seeds=candidate['source_seed_count'];require(type(seeds)==int and 0<seeds<=200,'The full declared saved seed count changed')
        require(all(isinstance(settings[name],list) and 0<len(settings[name])<=5 for name in names),'A declared source sweep is incomplete')
        generated=[]
        for seed in range(1,seeds+1):
            for pB,pR,rotB,rotR,ny,my,power in itertools.product(*(settings[name] for name in names)):
                generated.append(dict(seed=seed,pB=pB,pR=pR,rotB_deg=rotB,rotR_deg=rotR,
                    Nx=candidate['declared_Nx'],Ny=ny,Mx=candidate['declared_Mx'],My=my,P_dBm=power))
        require(generated==candidate['all_declared_generated_tasks'] and len(generated)==candidate['generated_task_count'],
            'A complete regenerated source-declaration cohort differs from its preserved local certificate')
        matched=sum(key(row) in saved_keys for row in generated)
        exact=len(generated)==len(rows) and Counter(map(key,generated))==Counter(map(key,rows))
        require(matched==candidate['exact_declared_parameter_slots_shared_with_saved_MAT'] and
                exact==candidate['entire_saved1000_task_cohort_matches'],'A whole source-to-record correspondence label changed')
        output.append(dict(source=candidate['source'],SHA256=candidate['SHA256'],
            generated_task_count=len(generated),all_regenerated_declared_tasks=generated,
            matched_saved_parameter_slots=matched,entire_saved1000_task_cohort_matches=exact))
    require([x['generated_task_count'] for x in output]==[20,1000] and
        [x['matched_saved_parameter_slots'] for x in output]==[20,0] and not any(
        x['entire_saved1000_task_cohort_matches'] for x in output),
        'The retained complete source-version mismatch changed; inspect the evidence')
    return output


def check_provenance(proof,metadata):
    require(proof['local_preservation_is_not_external_author_authentication'] is True and
        proof['fresh_full_archived_source_or_MAT_files_read_by_public_replay']==0,
        'A retained local source proof was mislabeled as fresh complete source inspection')
    success=proof['successful_source_bound_owners'];failed=proof['retained_failed_source_bound_owners']
    require(len(success)==4 and len(failed)==3,'All successful and failed source-intake epochs must remain explicit')
    for value in success+failed:
        require(value['status']=='actual_scientific_child_returned' and
            value['source_before']==value['source_after'] and value['all_watched_source_and_job_bytes_unchanged'],
            'A retained actual source-bound terminal receipt is incomplete')
    require(all(x['actual_child_terminal_exit_code']==0 for x in success) and
        all(x['actual_child_terminal_exit_code']==1 for x in failed),'A failed intake/host/control epoch was relabeled as success')
    native=proof['native_table_actual_process_receipt']
    require(native['actual_native_readonly_process_exit_code']==0 and native['source_before']==native['source_after'] and
        native['all_source_and_input_bytes_unchanged'],'The retained actual native table-export receipt is incomplete')
    require(len(metadata)==49 and len({value['member'] for value in metadata})==49 and
        all(value['exact_bytes_equal'] and len(value['SHA256'])==64 and value['bytes']>=0 for value in metadata),
        'The retained whole49-member local archive metadata is incomplete')


def replay(root,output):
    root,output=Path(root),Path(output);require(not output.exists(),'Preserve prior complete record-replay epochs');output.mkdir()
    scope=e.read(root/'scope.json')
    require(scope['scope']==e.SCOPE and scope['all_original150_tasks_preserved'] and
        scope['exact_full1000_generation_recipe_recovered'] is False and
        scope['full_original_model_algorithm_reference_or_six_paper_pass'] is False,
        'A complete original task/source qualification is absent or was relabeled')
    proof=e.read(root/'actual-local-closed-source-proof-receipts.json')
    metadata=e.read(root/'local-archive49-member-metadata.json');check_provenance(proof,metadata)
    with gzip.open(root/'saved-initial138-numeric-exact-hex.json.gz','rt',encoding='utf-8') as handle:snapshot=json.load(handle)
    encoded=snapshot['exact_binary64_numeric_variables'];require(len(encoded)==138,'Every original saved numeric variable is required')
    require(snapshot['snapshot_is_saved_initial_example_not_final_optimizer_return'] is True and
        snapshot['exact_generation_seed_stream_receipt_available'] is False and
        snapshot['paper_final100_channel_ensemble_or_figure_binding_proved'] is False,
        'An initial legacy state was relabeled as a final original reference realization')
    data={name:decode_array(value) for name,value in encoded.items()}
    require({name:encode_array(value) for name,value in data.items()}==encoded,
        'The complete138-variable original saved numeric payload differs')
    require(e.sha(root/'native1000x13-exact-binary64.json')==proof['native_table_actual_process_receipt'][
        'actual_complete1000_row_native_table_payload']['SHA256'],'The complete native table differs from its actual native process receipt')
    native=e.read(root/'native1000x13-exact-binary64.json');rows=decode_table(native);jobs=native['complete_saved_job_descriptors']
    verify_native_rows(rows,jobs)
    generated=list(csv.DictReader((root/'native1000x13-generated.csv').read_text(encoding='utf-8-sig').splitlines()))
    verify_native_export_csv(rows,generated)
    require(len({job['basefile'] for job in jobs})==200 and len({int(job['seed']) for job in jobs})==200,
        'The entire200-seed saved task/baseline-name scope must remain explicit')
    original=list(csv.DictReader((root/'original-distinct20.csv').read_text(encoding='utf-8-sig').splitlines()))
    require(len(original)==20,'The separate complete original20-row CSV cohort is required')
    lookup={key(row):row for row in rows};paired=[]
    for i,row in enumerate(original):
        other=lookup.get(key(row));require(other is not None,'A distinct original CSV parameter match is absent')
        paired.append(dict(original_CSV_row=i,parameters=list(key(row)),source_original_CSV_text=dict(row),
            actual_native_MAT_row=dict(other),
            absolute_metric_differences={name:abs(float(row[name])-other[name]) for name in METRICS},
            same_saved_iteration_count=float(row['itAO'])==other['itAO'],
            all_saved_metrics_agree_within_disclosed_ASCII_roundoff_bound=all(
                abs(float(row[name])-other[name])<=1e-12*(1+abs(other[name])) for name in METRICS)))
    require(paired==e.read(root/'sealed-all20-original-CSV-to-MAT-comparisons.json'),
        'A complete matched-parameter original CSV/MAT metric difference changed')
    caps=sum(row['itAO']==1500 for row in rows);above=sum(row['mse']>0.1 for row in rows)
    matches=sum(row['all_saved_metrics_agree_within_disclosed_ASCII_roundoff_bound'] for row in paired)
    require(caps==636 and above==296 and matches==0,'The retained original cap/threshold/cohort discrepancy changed')
    grid=e.read(root/'complete20x5-grid.json')
    rate,mse,flags=[decode_array(grid[name]) for name in ('all_rate_values','all_MSE_values','all_saved_success_flags')]
    verify_grid(rate,mse,grid['nominal_combos'])
    require(flags.shape==(20,5) and np.all(flags==1) and grid['seeds']==list(range(1,21)),
        'All original20-by5 nominal outcomes and flags are required')
    power=e.read(root/'complete10x6-power-grid.json');power_values=verify_power(power)
    candidates=e.read(root/'source-driver-candidates.json');candidate_results=declared_candidates(candidates,rows)
    declarations=e.read(root/'source-pre-RNG-parameter-declarations.json')
    constants={value['variable']:number(value['literal']) for value in declarations['assignments']}
    require(constants=={'lambda':0.1,'Mx':2,'My':2,'Nx':6,'Ny':6,'PB':1.0,'K':2,'G0B':1,'pB':2,'G0R':1,'pR':2},
        'An exact saved pre-RNG source declaration changed')
    transfer=e.read(root/'source-driver-static-flow.json')
    require(transfer['actual_unconditional_before_first_RNG_assignment_values']==constants and
        transfer['caller_sets_rotB_deg_and_rotR_deg_but_no_rot_bounds_structure'] and
        transfer['untitled18_fresh_worker_absent_rot_bounds_branch_fixes_both_rotation_boxes_to_zero'] and
        transfer['not_a_claim_that_this_version_generated_the_preserved_grid_or_final_paper_curves'],
        'A retained conditional static-flow/source-generation qualification changed')
    for value in transfer['all_five_external_exponent_symbolic_transfers']:
        require(value['external_cfg_G0B']==2*(value['external_cfg_pB']+1) and
            value['exact_pre_RNG_result_pB']==constants['pB'] and value['exact_pre_RNG_result_G0B']==constants['G0B'],
            'One derived complete external-parameter transfer differs')
    e.write(output/'fresh-all1000-decoded-native-table-and-jobs.json',dict(complete_saved_rows=rows,complete_saved_jobs=jobs))
    e.write(output/'fresh-all20-original-CSV-to-MAT-comparisons.json',paired)
    e.write(output/'fresh-both-complete-source-declaration-candidate-cohorts.json',candidate_results)
    e.write(output/'fresh-full-legacy-20x5-and10x6-grids.json',dict(all20x5_rate=rate.tolist(),all20x5_MSE=mse.tolist(),
        all20x5_saved_success_flags=flags.tolist(),all10x6_power_rates=power_values.tolist(),
        all_saved_zero_rows=power['exact_all_zero_rows'],saved_flags_or_zero_rows_not_stationarity_certificates=True))
    report=dict(scope=e.SCOPE,complete_native_table_shape=[1000,13],complete_native_binary64_values=13000,
        complete_saved_job_descriptors=1000,complete_saved_native_generated_CSV_rows=1000,
        complete_distinct_original_CSV_rows=20,matched_parameter_original_CSV_MAT_metric_differences=60,
        original_CSV_rows_with_all_metrics_agreeing=matches,original_CSV_rows_with_same_iteration_count=sum(
            row['same_saved_iteration_count'] for row in paired),saved_source_cap1500_rows=caps,
        saved_source_MSE_above0_1_rows=above,cap_and_threshold_categories_can_overlap=True,
        actual_executed_version_or_per_record_stationarity_not_proved=True,
        saved_numeric_variables_exactly_reconstructed=138,complete_saved_hex_real_imag_observations=sum(map(observations,encoded.values())),
        observation_aliases_not_claimed_as_independent_draws=True,all20x5_nominal_exponent_columns_identical=True,
        complete_saved10x6_power_values=60,all_zero_original_power_rows=[9],
        complete_source_declaration_tasks_regenerated=[20,1000],source_declaration_matching_slots=[20,0],
        all_five_external_parameter_transfers_recomputed=True,retained_whole_local_archive_metadata_members=49,
        retained_actual_successful_source_bound_readers=4,retained_failed_host_intake_or_fixture_epochs=3,
        fresh_original_optimizer_initializer_sampler_or_native_MAT_export_calls=0,
        fresh_full_archived_source_MAT_or_publisher_documents_read=0,
        original_model_generation_recipe_reference_convergence_dual_language_or_full_six_paper_pass=False)
    e.write(output/'summary.json',report)
    context=dict(data=data,encoded=encoded,native=native,rows=rows,jobs=jobs,generated=generated,original=original,
        grid=grid,rate=rate,mse=mse,power=power,candidates=candidates)
    return report,context


def controls(context,output):
    output=Path(output);require(not output.exists(),'Keep every previous record-control epoch');output.mkdir();groups={}
    def reject(group,name,call):
        try:call()
        except (ValueError,AssertionError,KeyError) as error:
            groups.setdefault(group,[]).append(dict(control=name,rejected=True,reason=str(error)));return
        raise AssertionError('Invalid complete preserved-record control accepted: '+name)
    rows,jobs=context['rows'],context['jobs']
    bad=deepcopy(rows);bad[-1]['P_dBm']+=1
    reject('full_table','last_of1000_native_job_parameters_changed',lambda:verify_native_rows(bad,jobs))
    reject('full_table','last_of1000_native_rows_removed',lambda:verify_native_rows(rows[:-1],jobs))
    bad_csv=deepcopy(context['generated']);bad_csv[-1]['sumrate']=str(float(bad_csv[-1]['sumrate'])+0.01)
    reject('full_table','last_of1000_native_generated_rate_ordinates_changed',lambda:verify_native_export_csv(rows,bad_csv))
    reject('full_table','original20_CSV_substituted_as_complete1000_export',lambda:verify_native_export_csv(rows,context['original']))
    bad_payload=deepcopy(context['native']);bad_payload['columns'][-1]['complete_real_binary64_hex'].pop()
    reject('full_table','one_complete_native_binary64_table_ordinate_omitted',lambda:decode_table(bad_payload))
    candidates=context['candidates']
    reject('source_cohort','asv1000_total_matches_but_whole_scenario_differs',lambda:whole_cohort(candidates[1]['all_declared_generated_tasks'],rows))
    reject('source_cohort','m20_matching_parameter_subset_substituted_for1000',lambda:whole_cohort(candidates[0]['all_declared_generated_tasks'],rows))
    duplicate=deepcopy(rows);duplicate[-1]=deepcopy(duplicate[0])
    reject('source_cohort','one_slot_duplicated_and_one_omitted_with_count1000',lambda:whole_cohort(duplicate,rows))
    reject('source_cohort','non_numeric_source_call_is_not_executed',lambda:number('rng(0)'))
    rate,mse,combos=context['rate'],context['mse'],context['grid']['nominal_combos']
    bad_rate=rate.copy();bad_rate[19,4]=np.nextafter(bad_rate[19,4],np.inf)
    reject('complete_grids','last_full_rate_grid_ordinate_changed_one_ULP',lambda:verify_grid(bad_rate,mse,combos))
    bad_mse=mse.copy();bad_mse[19,3]=np.nextafter(bad_mse[19,3],np.inf)
    reject('complete_grids','last_full_MSE_grid_ordinate_changed_one_ULP',lambda:verify_grid(rate,bad_mse,combos))
    bad_combos=deepcopy(combos);bad_combos[-1]['pB']=6
    reject('complete_grids','one_actual_nominal_exponent_label_changed',lambda:verify_grid(rate,mse,bad_combos))
    reject('complete_grids','one_complete_original_grid_row_removed',lambda:verify_grid(rate[:-1],mse,combos))
    bad_power=deepcopy(context['power']);array=decode_array(bad_power['all_rate_values']);bad_power['all_rate_values']=encode_array(array[:-1])
    reject('complete_grids','all_zero_original_power_row_deleted',lambda:verify_power(bad_power))
    require({name:len(values) for name,values in groups.items()}==dict(full_table=5,source_cohort=4,complete_grids=5),
        'Every complete-table, source-cohort and original-grid control is required')
    report=dict(actual_negative_controls=14,all_expected_complete_record_source_and_grid_controls_rejected=True,groups=groups)
    e.write(output/'all14-complete-record-source-and-grid-controls.json',report)
    return report
