"""Losslessly decode all actual historical Python final states and QT calls.

No solver, production evaluator, gradient callback or RNG is invoked. Every
numerical QT operand and before/after returned metric is retained; only the
trailing solver name/options are stored as provenance rather than MP operands.
Phase/MC/outer histories retain their separate independent-audit requirements.
"""
import argparse
import copy
from pathlib import Path

import numpy as np
from scipy.io import loadmat,savemat

from audit_native_case import channel_data,sequence,sha
from build_power_curve_views import NAMES,read,require,write


def cells(values):
    result=np.empty((len(values),1),dtype=object)
    for i,value in enumerate(values):result[i,0]=value
    return result


def adapt(case_dir,output):
    require(not output.exists(),'Preserve previous converted QT evidence')
    paths=[case_dir/name for name in ('configuration.json','actual-result.json','actual-state.json','actual-state.npz')]
    before={p.name:sha(p) for p in paths}
    configuration,result,metadata=map(read,paths[:3])
    require(len(metadata['cases'])==1 and metadata['actual_saved_array_bank_sha256']==before['actual-state.npz'],
            'One exact actual original recording and its NumPy digest required')
    original=metadata['cases'][0]
    J,U,N,M=(int(configuration['reported'][k]) for k in ('J','U','N','M'))
    calls=[];final=[];solver_provenance=[];original_mutations=[]
    with np.load(paths[3],allow_pickle=False) as bank:
        def decode(value):
            if isinstance(value,dict) and 'recorded_array' in value:
                actual=bank[value['recorded_array']]
                require(list(actual.shape)==value['shape'] and actual.dtype.str==value['dtype'],
                        'Actual saved array differs from the original recording descriptor')
                return actual.copy()
            if isinstance(value,dict):return {k:decode(v) for k,v in value.items()}
            if isinstance(value,list):return [decode(v) for v in value]
            return value
        data=decode(original['data'])
        power=decode(original['power_limits']);limit=decode(original['interference_limits'])
        require(data['d_mean'].shape==(J,U,N) and data['r_mean'].shape==(U,M),'Actual original dimensions differ')
        for state in original['scheme_final_states']:
            name=state['scheme']
            item=dict(scheme=name,phi=decode(state['phi']),no_ris=bool(state['noRIS']))
            key='AP_W' if name.startswith('AP') else 'MR_p'
            item['W' if key=='AP_W' else 'p']=decode(state[key])
            final.append(item)
        require([s['scheme'] for s in final]==list(NAMES),'Every actual original final state must remain in order')
        for call in original['boundary_calls']:
            kind=call['function']
            if kind not in ('ap_qt_update','mr_qt_update'):continue
            count=7 if kind=='ap_qt_update' else 8
            args=decode(call['original_inputs'])
            after=decode(call['original_inputs_after'])
            require(len(args)>=count and len(after)>=count and len(args)<=count+2,
                    'Every original numerical QT operand must be retained')
            require(set(call['original_keyword_inputs']).issubset({'solver','solver_options'}),
                    'Unknown original numerical keyword input must not be discarded')
            returned=decode(call['original_return'])
            require(isinstance(returned,list) and len(returned)==2,'Actual candidate and complete original return required')
            candidate,info=returned
            require(np.asarray(candidate).shape==((J,N,U) if kind=='ap_qt_update' else (J,U)),
                    'Actual original candidate dimensions differ')
            wanted=('before','after','surrogate_minimum_sinr','solver_status','qt_bound_max_violation','qt_tightness_error')
            require(all(key in info for key in wanted),'Every original reported before/after/QT field required')
            keep={key:info[key] for key in wanted}
            calls.append(dict(kind=kind,input=cells(args[:count]),candidate=candidate,info=keep))
            solver_provenance.append(dict(kind=kind,trailing_solver_positional_inputs=call['original_inputs'][count:],
                original_solver_keyword_inputs=call['original_keyword_inputs'],
                original_solver_status=info['solver_status']))
            changed=[]
            for i,(a,b) in enumerate(zip(args[:count],after[:count])):
                a,b=np.asarray(a),np.asarray(b)
                if a.shape!=b.shape or a.dtype!=b.dtype or a.tobytes(order='C')!=b.tobytes(order='C'):changed.append(i)
            if changed:original_mutations.append(dict(QT_index=len(calls)-1,numerical_operand_positions=changed))
    require(calls,'A genuine original QT population is required')
    require(before=={p.name:sha(p) for p in paths},'Original recorded files changed during decoding')
    output.mkdir(parents=True)
    matrix=output/'actual-historical-Python-final-and-QT.mat'
    recording=dict(input=dict(configuration=configuration,data=data,power_limit=power,interference_limit=limit),
                   final_states=cells(final),QT_candidates=cells(calls))
    savemat(matrix,dict(recording=recording),do_compression=True,long_field_names=True)
    restored=loadmat(matrix,simplify_cells=True)['recording'];checks=0
    def same(a,b):
        nonlocal checks
        a=np.asarray(a);b=np.asarray(b).reshape(a.shape)
        require(a.dtype==b.dtype and a.tobytes(order='C')==b.tobytes(order='C'),
                'A numeric dtype or value changed in the converted recording')
        checks+=1
    loaded_data=channel_data(restored['input']['data'],J,U,N,M)
    for key,value in data.items():same(value,loaded_data[key])
    same(power,restored['input']['power_limit']);same(limit,restored['input']['interference_limit'])
    restored_final=sequence(restored['final_states']);restored_qt=sequence(restored['QT_candidates'])
    require(len(restored_final)==8 and len(restored_qt)==len(calls),'All actual original states/candidates required')
    for old,new in zip(final,restored_final):
        require(old['scheme']==new['scheme'] and old['no_ris']==bool(new['no_ris']),'Actual scheme identity changed')
        same(old['phi'],new['phi']);key='W' if old['scheme'].startswith('AP') else 'p';same(old[key],new[key])
    for old,new in zip(calls,restored_qt):
        require(old['kind']==new['kind'],'Actual original QT kind changed')
        for a,b in zip(sequence(old['input']),sequence(new['input'])):same(a,b)
        same(old['candidate'],new['candidate'])
        require(old['info']['solver_status']==new['info']['solver_status'],'Original solver status must remain unchanged')
        for key in ('surrogate_minimum_sinr','qt_bound_max_violation','qt_tightness_error'):same(old['info'][key],new['info'][key])
        for time in ('before','after'):
            for key in ('sinr','denominator','satellite_power','gt_interference'):same(old['info'][time][key],new['info'][time][key])
    point=copy.deepcopy(result['results'][0])
    require(set(point['schemes'])==set(NAMES),'All original reported physical fields required')
    point['schemes']=[dict(scheme=name,**point['schemes'][name]) for name in NAMES]
    view=dict(scope='Actual historical Python final/QT-only container; no new optimization',language='python',
        configuration=configuration,results=[point],source_unchanged_during_run=result['source_unchanged_during_run'],
        overall_implemented_scope_success=result['overall_implemented_scope_success'],
        unchanged_original_result_sha256=before['actual-result.json'],
        original_state_manifest_sha256=before['actual-state.json'],original_array_bank_sha256=before['actual-state.npz'],
        state_recording=dict(filename=matrix.name,sha256=sha(matrix),final_scheme_states=8,QT_candidates=len(calls),
                             complete_phase_or_MC_tape_included=False),
        adapter_sha256=sha(Path(__file__)),full183_or_original_reference_or_paper_pass=False)
    write(output/'case-python-final-QT-recorded.json',view)
    require(before=={p.name:sha(p) for p in paths},'Original source bytes changed during serialization/readback')
    write(output/'actual-lossless-final-QT-adapter-receipt.json',dict(
        exact_original_case_folder=case_dir.name,source_before_and_after_SHA256=before,
        original_recorded_array_bank_digest_matched=True,actual_final_states=8,actual_QT_candidates=len(calls),
        actual_numeric_dtype_and_C_order_byte_comparisons=checks,all_serialized_numeric_bytes_equal=True,
        original_numerical_inputs_changed_during_original_call=original_mutations,
        original_solver_metadata=solver_provenance,
        new_optimizer_production_evaluator_gradient_callback_RNG_or_MP_calls=0,
        independent_final_QT_MP_already_complete=False,original_phase_MC_outer_or_full_paper_pass=False,
        common_container_SHA256=sha(output/'case-python-final-QT-recorded.json'),
        MAT_SHA256=sha(matrix),adapter_SHA256=sha(Path(__file__))))
    print(dict(actual_original_final_states=8,actual_original_QT_candidates=len(calls),
        byte_level_comparisons=checks,all_numeric_bytes_equal=True,independent_MP_still_required=True),flush=True)
    return output/'case-python-final-QT-recorded.json'


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case-dir',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();adapt(a.case_dir,a.output_dir)
