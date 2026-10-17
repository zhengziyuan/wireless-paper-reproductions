"""Losslessly expose actual historical Python phase endpoints to the MP reader.

Only saved NumPy arrays and existing final FG calls are read. No optimizer,
gradient callback or RNG is invoked. QT/MC tapes remain outside this phase-only
container, so this adapter cannot supply a complete-case physics/QT certificate.
"""
import argparse
from pathlib import Path

import numpy as np
from scipy.io import loadmat,savemat

from audit_native_case import channel_data,sequence,sha
from build_power_curve_views import read,require,write


def cells(items):
    result=np.empty((len(items),1),dtype=object)
    for i,item in enumerate(items):result[i,0]=item
    return result


def adapt(case_dir,output):
    require(not output.exists(),'Preserve previous decoded phase evidence')
    paths=[case_dir/name for name in ('configuration.json','actual-result.json','actual-state.json','actual-state.npz')]
    before={p.name:sha(p) for p in paths}
    configuration,result,metadata=map(read,paths[:3])
    require(len(metadata['cases'])==1,'Exactly one actual original source case required')
    require(before['actual-state.npz']==metadata['actual_saved_array_bank_sha256'],
            'Actual original NumPy bank differs from its saved recording digest')
    original=metadata['cases'][0]
    p=configuration['reported'];J,U,N,M=(int(p[k]) for k in ('J','U','N','M'))
    require(original['settings']['gradient_tolerance']==1e-6,'Original strict phase threshold must remain unchanged')
    phases=[]
    with np.load(paths[3],allow_pickle=False) as bank:
        def decode(value):
            if isinstance(value,dict) and 'recorded_array' in value:
                actual=bank[value['recorded_array']]
                require(list(actual.shape)==value['shape'] and actual.dtype.str==value['dtype'],
                        'An original array descriptor differs from actual saved bytes')
                return actual.copy()
            if isinstance(value,dict):return {k:decode(v) for k,v in value.items()}
            if isinstance(value,list):return [decode(v) for v in value]
            return value
        data=decode(original['data'])
        require(data['d_mean'].shape==(J,U,N) and data['r_mean'].shape==(U,M),
                'Original physical dimensions differ from the exact configuration')
        for record in original['phase_stages']:
            require(record['complete_original_return'] and record['same_final_phi_as_existing_FG_call'] and
                    record['no_extra_gradient_evaluation'],'Every actual complete endpoint/FG association required')
            phi=decode(record['original_final_phi'])
            call=decode(record['original_final_fg_call'])
            require(np.array_equal(phi,call['phi']) and phi.shape==(U,M),
                    'Endpoint differs from its actual existing FG call')
            context=decode(record['original_FG_closure_context'])
            vector=set(context)=={'W','data'}
            if not vector:
                require(set(context)=={'data','interference_limit','mu','p0','tts'},
                        'Unknown original closure must not be guessed')
                context['interferenceLimit']=context.pop('interference_limit')
            gradient=np.asarray(call['original_gradient'])
            require(gradient.shape==(U,M) and np.isfinite(phi).all() and np.isfinite(gradient).all() and
                    np.isfinite(call['original_value']).all(),'Every actual finite endpoint field required')
            phases.append(dict(context=context,final_phi=phi,gradient=gradient,value=call['original_value'],
                vector_objective=vector,original_status=record['original_phase_status'],
                original_scalar_history=np.asarray(record['original_history'],dtype=float)))
        power=decode(original['power_limits']);limit=decode(original['interference_limits'])
    require(len(phases)==len(original['phase_stages']) and phases,'Every original phase row must be retained')
    output.mkdir(parents=True)
    matrix=output/'actual-historical-Python-phase-endpoints.mat'
    recording=dict(input=dict(configuration=configuration,data=data,power_limit=power,interference_limit=limit),
                   phase_endpoints=cells(phases))
    savemat(matrix,dict(recording=recording),do_compression=True,long_field_names=True)
    restored=loadmat(matrix,simplify_cells=True)['recording']
    actual=sequence(restored['phase_endpoints'])
    require(len(actual)==len(phases),'Converted phase count differs')
    for old,new in zip(phases,actual):
        for key in ('final_phi','gradient'):
            require(np.array_equal(old[key],np.asarray(new[key]).reshape(U,M)),
                    'A phase/gradient value changed during serialization')
        require(np.array_equal(np.asarray(old['value']).reshape(-1),np.asarray(new['value']).reshape(-1)),
                'An original criterion changed during serialization')
        restored_data=channel_data(new['context']['data'],J,U,N,M)
        require(set(restored_data)==set(old['context']['data']) and all(
            np.array_equal(old['context']['data'][k],restored_data[k]) for k in restored_data),
            'A phase physical input changed during serialization')
        if old['vector_objective']:
            require(np.array_equal(old['context']['W'],np.asarray(new['context']['W']).reshape(J,N,U)),
                    'An actual AP beamformer changed')
        else:
            require(np.array_equal(old['context']['p0'],np.asarray(new['context']['p0']).reshape(J,U)) and
                    float(old['context']['mu'])==float(new['context']['mu']) and
                    np.array_equal(np.asarray(old['context']['interferenceLimit']).reshape(-1),
                                   np.asarray(new['context']['interferenceLimit']).reshape(-1)) and
                    bool(old['context']['tts'])==bool(new['context']['tts']),
                    'An actual MR power/smoothing/limit or mode changed')
    require(before=={p.name:sha(p) for p in paths},'An original source/recording changed during read-only conversion')
    view=dict(scope='Historical actual Python phase-only saved-state container; no new optimizer',language='python',
        configuration=configuration,source_unchanged_during_run=result['source_unchanged_during_run'],
        overall_implemented_scope_success=result['overall_implemented_scope_success'],
        unchanged_original_result_sha256=before['actual-result.json'],
        original_state_manifest_sha256=before['actual-state.json'],original_array_bank_sha256=before['actual-state.npz'],
        state_recording=dict(filename=matrix.name,sha256=sha(matrix),phase_endpoints=len(phases),
                             complete_QT_or_MC_recording_included=False),
        adapter_sha256=sha(Path(__file__)),full183_or_original_reference_or_paper_pass=False)
    write(output/'case-python-phase-recorded.json',view)
    receipt=dict(scope='Lossless serialization of every actual saved original Python phase endpoint',
        exact_original_case_folder=case_dir.name,source_before_and_after_SHA256=before,
        original_recorded_bank_digest_matched=True,actual_phase_endpoints=len(phases),
        complex_gradient_coordinates_per_precision=len(phases)*U*M,
        all_phase_criteria_gradients_contexts_designs_bitwise_equal_after_MAT_readback=True,
        only_context_field_renamed_from_interference_limit_to_interferenceLimit=True,
        original_gradient_tolerance=original['settings']['gradient_tolerance'],
        original_iteration_cap=original['settings']['rmo_max_iterations'],
        actual_original_QT_calls_not_adapted=sum(c['function'] in ('ap_qt_update','mr_qt_update') for c in original['boundary_calls']),
        actual_original_MC_draws_not_replayed=len(original['effective_channel_draws']),
        new_optimizer_gradient_callback_RNG_or_MP_calls=0,
        independent_phase_mathematical_checks_already_complete=False,
        complete_original_QT_MC_or_full183_or_paper_certificate=False,
        common_container_SHA256=sha(output/'case-python-phase-recorded.json'),MAT_SHA256=sha(matrix),
        adapter_SHA256=sha(Path(__file__)))
    write(output/'actual-lossless-phase-adapter-receipt.json',receipt)
    print(dict(actual_original_phase_endpoints=len(phases),all_serialized_values_equal=True,
        new_optimizer_gradient_RNG_calls=0,independent_MP_still_required=True),flush=True)
    return output/'case-python-phase-recorded.json'


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case-dir',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();adapt(a.case_dir,a.output_dir)
