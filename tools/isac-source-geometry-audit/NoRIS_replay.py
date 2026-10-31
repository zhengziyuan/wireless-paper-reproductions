"""Fresh complete saved-state fields for both explicitly qualified source variants."""
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path

import mpmath as mp

import evidence as e
import physical_states as physical


def qualified_state(entry,sealed):
    e.require(entry['actual_saved_state']==sealed['actual_original_W_theta_rotation_and_iota'],
        'An actual original saved W/theta/rotation/iota coordinate changed')
    e.require(entry['label']==sealed['label'] and entry['scheme']==sealed['scheme'] and
        entry['original_result_SHA256']==sealed['actual_result_SHA256'] and
        entry['original_scenario_SHA256']==sealed['actual_scene_SHA256'],'A saved state was substituted or relabeled')
    e.require(sealed['newly_optimized_published_reference_or_original_performance_result'] is False and
        sealed['source_R1_implementation_error_or_paper_error_proved'] is False and
        sealed['optimizer_initializer_sampler_or_production_evaluator_calls']==0,
        'A given-state diagnostic was inflated into an optimized result or paper-error claim')


def replay(root,output):
    root,output=Path(root),Path(output);e.require(not output.exists(),'Preserve each complete NoRIS replay epoch');output.mkdir()
    states=e.read(root/'states/four-original-NoRIS-saved-states.json')
    expected={(label,scheme) for label in ('b0-original-scene000','b2-original-scene001') for scheme in ('Rot-BS & No-RIS','Fix-BS & No-RIS')}
    e.require(len(states)==4 and {(x['label'],x['scheme']) for x in states}==expected,'All four actual original NoRIS states are required')
    config=(root/'inputs/original-run-config.json').read_bytes();reports=[];fresh_records=[];context=None;scenes=set();coordinates={'80':0,'100':0};scalars={'80':0,'100':0}
    for entry in states:
        e.require(e.safe(entry['scene']) and e.safe(entry['sealed_report']),'Unsafe saved-state or scene path')
        scene_path=root/entry['scene'];scenes.add(entry['scene']);raw=scene_path.read_bytes()
        e.require(hashlib.sha256(raw).hexdigest()==entry['original_scenario_SHA256'] and
            hashlib.sha256(b'strict-v1\0'+config+b'\0'+raw).hexdigest()==entry['original_input_fingerprint'],
            'An original complete saved-state input/configuration binding changed')
        with gzip.open(root/entry['sealed_report'],'rb') as stream:sealed=json.load(stream)
        qualified_state(entry,sealed);scene=json.loads(raw)
        fresh=physical.replay_lanes(entry['actual_saved_state'],scene,entry['scheme'])
        checked=physical.compare_lanes(fresh,sealed['lanes'])
        for digits in coordinates:
            coordinates[digits]+=checked['full_field_coordinates_per_precision'][digits]
            scalars[digits]+=checked['physical_scalar_values_per_precision'][digits]
        with mp.workdps(140):
            a,b=[fresh['100'][v] for v in e.VARIANTS]
            pattern_delta=max(abs(mp.mpf(x)-mp.mpf(y)) for x,y in zip(a['metrics']['pattern'],b['metrics']['pattern']))
            fixed_delta=mp.mpf(b['metrics']['fixed_iota_utility'])-mp.mpf(a['metrics']['fixed_iota_utility'])
            rescaled_delta=mp.mpf(b['metrics']['analytically_rescaled_utility'])-mp.mpf(a['metrics']['analytically_rescaled_utility'])
            coupled=mp.mpf(b['full_cascade_squared_norm'])>0
            e.require(coupled==sealed['actual_public_v2_RU_only_nonzero_RIS_cascade'],'The retained zero/nonzero source-cascade result changed')
            for actual,key in ((pattern_delta,'actual_MP100_maximum_sensing_pattern_difference'),
                (fixed_delta,'actual_MP100_fixed_saved_iota_utility_difference'),(rescaled_delta,'actual_MP100_fresh_analytic_iota_utility_difference')):
                e.require(abs(actual-mp.mpf(sealed[key]))<=mp.mpf('1e-40'),'A complete same-state source-variant comparison changed')
        reports.append(dict(label=entry['label'],scheme=entry['scheme'],
            full_field_coordinates_per_precision=checked['full_field_coordinates_per_precision'],
            physical_scalar_values_per_precision=checked['physical_scalar_values_per_precision'],
            maximum_actual_coordinate_error=checked['maximum_full_field_difference_from_sealed_reference'],
            public_RU_only_has_nonzero_RIS_sensing_cascade=coupled,
            all_user_received_signals_SINR_and_rate_exact_between_variants=True,
            maximum_actual_sensing_pattern_difference=mp.nstr(pattern_delta,110),
            fixed_saved_iota_utility_difference=mp.nstr(fixed_delta,110),fresh_analytic_iota_utility_difference=mp.nstr(rescaled_delta,110)))
        fresh_records.append(dict(label=entry['label'],scheme=entry['scheme'],lanes=fresh))
        if coupled and context is None:context=dict(entry=entry,sealed=sealed,fresh=fresh)
        print(json.dumps(dict(phase='complete_saved_NoRIS_state_replayed',label=entry['label'],scheme=entry['scheme'],
            complete_field_coordinates_per_precision=checked['full_field_coordinates_per_precision'])),flush=True)
    e.require(coordinates=={'80':61056,'100':61056} and len(scenes)==2 and context is not None,
        'The complete both-precision source-state matrix population is incomplete')
    path=output/'all-four-original-NoRIS-states-fresh-MP80-MP100-fields.json.gz'
    with path.open('xb') as base,gzip.GzipFile(filename='',mode='wb',fileobj=base,mtime=0) as stream:
        stream.write((json.dumps(fresh_records,separators=(',',':'),allow_nan=False)+'\n').encode())
    result=dict(actual_original_saved_NoRIS_states=4,actual_source_variants=2,actual_fresh_independent_variant_precision_field_sets=16,
        actual_complete_physical_matrices_per_precision=48,actual_full_field_coordinates_per_precision=coordinates,
        actual_full_physical_scalar_values_per_precision=scalars,
        all_full_field_coordinates_and_metric_values_match_sealed_reference_within1e_minus40=True,
        all_fresh_MP80_MP100_full_field_coordinates_agree_within1e_minus40=True,
        actual_user_received_signals_SINR_and_rate_exact_between_variants=True,
        actual_original_scenarios_restored_and_read=2,actual_complete_original_optimizer_result_histories_read=0,
        actual_fresh_original_optimizers_initializers_samplers_or_native_MC_streams=0,
        given_model_source_variant_diagnostic_is_not_a_new_optimized_performance_result=True,
        fresh_complete_matrix_report=path.name,fresh_complete_matrix_report_SHA256=e.sha(path),cases=reports,
        original_author_curve_agreement_dual_language_paper_error_or_full_paper_pass=False)
    return result,context


def controls(context,output):
    output=Path(output);e.require(not output.exists(),'Preserve every NoRIS negative-control epoch');output.mkdir();negative=[]
    def reject(name,change):
        altered=deepcopy(context['sealed']['lanes']);change(altered)
        p=output/(name+'.json.gz')
        with p.open('xb') as base,gzip.GzipFile(filename='',mode='wb',fileobj=base,mtime=0) as stream:
            stream.write((json.dumps(altered,separators=(',',':'))+'\n').encode())
        try:physical.compare_lanes(context['fresh'],altered)
        except ValueError as error:negative.append(dict(control=name,rejected=True,reason=str(error),SHA256=e.sha(p)));return
        raise AssertionError('Invalid complete NoRIS field evidence accepted: '+name)
    reject('one_complete_precision_lane_missing',lambda x:x.pop('80'))
    reject('one_source_variant_missing',lambda x:x['100'].pop(e.VARIANTS[1]))
    def phase(x):
        a=x['80'][e.VARIANTS[1]]['full_fields']['received_signal'];locations=[]
        with mp.workdps(140):
            for i in range(a['shape'][0]):
                for j in range(a['shape'][1]):locations.append((abs(mp.mpc(a['real'][i][j],a['imag'][i][j])),i,j))
            magnitude,i,j=max(locations);e.require(magnitude>mp.mpf('1e-20'),'A meaningful nonzero complete-signal control is required')
        for component in ('real','imag'):
            value=a[component][i][j];a[component][i][j]=value[1:] if value.startswith('-') else '-'+value
    reject('signal_phase_changed_preserving_its_squared_norm',phase)
    def hide_bridge(x):
        for digits in x:
            a=x[digits][e.VARIANTS[1]]['full_fields']['BS_RIS_bridge']
            for component in ('real','imag'):a[component]=[['0' for _ in row] for row in a[component]]
    reject('RU_only_bridge_hidden_in_both_precision_lanes',hide_bridge)
    reject('one_full_RIS_outgoing_coordinate_row_missing',lambda x:x['100'][e.VARIANTS[1]]['full_fields']['RIS_outgoing']['real'].pop())
    def change_sinr(x):
        values=x['100'][e.VARIANTS[1]]['metrics']['sinr']
        with mp.workdps(140):values[0]=mp.nstr(mp.mpf(values[0])+1,140)
    reject('one_user_SINR_metric_ordinate_changed',change_sinr)
    reject('one_rescaled_NMSE_ordinate_changed',lambda x:x['100'][e.VARIANTS[1]]['metrics'].__setitem__('analytically_rescaled_NMSE','20'))
    modified=deepcopy(context['entry']);state=modified['actual_saved_state']
    locations=[(abs(x),name,i,j) for name in ('w_re','w_im') for i,row in enumerate(state[name]) for j,x in enumerate(row)]
    magnitude,name,i,j=max(locations);e.require(magnitude>1e-20,'A meaningful original nonzero W control is required');state[name][i][j]*=-1
    e.require(modified!=context['entry'],'The actual saved-W source-binding control must change a coordinate')
    try:qualified_state(modified,context['sealed'])
    except ValueError as error:negative.append(dict(control='actual_saved_W_coordinate_changed',rejected=True,reason=str(error)))
    else:raise AssertionError('Changed original saved W accepted')
    modified=deepcopy(context['sealed']);modified['source_R1_implementation_error_or_paper_error_proved']=True
    try:qualified_state(context['entry'],modified)
    except ValueError as error:negative.append(dict(control='same_state_diagnostic_relabeled_paper_error',rejected=True,reason=str(error)))
    else:raise AssertionError('Inflated original paper-error claim accepted')
    e.require(len(negative)==9,'Every complete field/source-state/scope control is required')
    return dict(actual_negative_controls=9,all_expected_invalid_full_fields_saved_state_or_scope_controls_rejected=True,controls=negative)
