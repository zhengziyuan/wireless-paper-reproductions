"""Audit only actual saved domains/power/matrices, without solver or fake mean inputs."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
PACKAGE=ROOT/'wireless-paper-reproductions/strict/hotspot-satcom'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def decode(value):
    assert set(value)=={'real','imag'}
    a=np.asarray(value['real'],dtype=float);b=np.asarray(value['imag'],dtype=float)
    assert a.shape==b.shape and np.all(np.isfinite(a)) and np.all(np.isfinite(b))
    return a+1j*b


def has_mean_inputs(value):
    if isinstance(value,dict):return any(k in ('mean_inputs','direct_mean','matrix_mean','ground_mean','Q','Psi') for k in value) or any(has_mean_inputs(v) for v in value.values())
    if isinstance(value,list):return any(has_mean_inputs(v) for v in value)
    return False


def audit(args):
    assert not args.output.exists() and not args.array_output.exists()
    progress_path=args.bank_directory/'execution-progress.json';progress_bytes=progress_path.read_bytes()
    progress=json.loads(progress_bytes.decode('utf-8-sig'));prefix=progress['records']
    assert len(prefix)==progress['completed_cases'] and 0<len(prefix)<18
    arrays={};records=[];count=0;mean_found=False
    for entry in prefix:
        config_path=args.bank_directory/entry['configuration_filename'];result_path=args.bank_directory/entry['result_filename']
        assert sha(config_path)==entry['configuration_sha256'] and sha(result_path)==entry['result_sha256']
        before_input=sha(config_path);before_result=sha(result_path)
        config=read(config_path);raw=read(result_path);assert config==raw['configuration']
        assert raw['source_unchanged_during_run'];mean_found=mean_found or has_mean_inputs(raw)
        for spec in raw['executed_source_hashes'].values():
            path=config_path if spec['filename']==config_path.name else PACKAGE/spec['filename']
            assert sha(path)==spec['sha256']
        assert len(raw['cases'])==1
        case=raw['cases'][0];U=entry['U'];N=config['reported']['N'];J=config['reported']['J'];M=config['reported']['M'];power=config['reported']['power_w']
        assert N==J==16 and M==25 and config['reported']['K']==16-U
        assert case['U']==U and case['kappa_satellite_db']==entry['kappa_satellite_db']
        assert tuple(case['schemes'])==('NoRIS','TwoStage','AO')
        case_records=[];case_count=0
        for scheme,output in case['schemes'].items():
            starts=output['all_start_records'];required=list(range(U+1))
            assert len(starts)==U+1 and [s['start_id'] for s in starts]==required
            assert output['ensemble']['required_start_ids']==output['ensemble']['executed_start_ids']==required
            for start in starts:
                assert start['scheme']==scheme and start['executed']
                assert 'initial_state' in start and 'final_state' in start
                parsed={}
                for state_name in ('initial_state','final_state'):
                    state=start[state_name];W=decode(state['W']);phi=decode(state['phi'])
                    # JSON drops native singleton vector orientation. Check only
                    # the actual encoded vector domain, not nonexistent MAT shape.
                    assert W.shape==(N,J) and phi.ndim==1 and phi.size==M
                    phi_error=float(np.max(abs(abs(phi)-1)));total=float(np.sum(abs(W)**2))
                    assert phi_error<=1e-10 and total<=power*(1+1e-5)
                    key=f'case_{len(records):02d}_{scheme.replace("-","_")}_start_{start["start_id"]}_{state_name}'
                    arrays[key+'_W']=W;arrays[key+'_phi_encoded_vector']=phi
                    parsed[state_name]={'encoded_W_shape':list(W.shape),'encoded_phi_vector_length':phi.size,
                        'independent_total_power':total,'original_power_limit':power,'unit_modulus_maximum_error':phi_error,
                        'finite_domain_shape_power_gate_pass':True,'saved_array_W':key+'_W','saved_array_phi':key+'_phi_encoded_vector'}
                final=start['final_state'];assert final['no_ris']==(scheme=='NoRIS')
                error=abs(parsed['final_state']['independent_total_power']-start['evaluation']['total_power'])
                assert error<=1e-10*max(1,power)
                case_records.append({'scheme':scheme,'start_id':start['start_id'],'actual_states':parsed,
                    'actual_no_ris_flag':final['no_ris'],'reported_and_rebuilt_total_power_error':error,
                    'independent_original_total_power_gate_pass':True,'native_phi_orientation_recovered':False})
                case_count+=1
        assert case_count==entry['executed_starts'];count+=case_count
        assert sha(config_path)==before_input and sha(result_path)==before_result
        records.append({'U':U,'kappa_satellite_db':entry['kappa_satellite_db'],'actual_configuration_sha256':before_input,
            'actual_original_result_sha256':before_result,'input_and_result_A_to_B_unchanged':True,
            'actual_current_source_binding_matches':True,'actual_required_saved_starts':case_count,'actual_domain_records':case_records})
    assert not mean_found,'A saved real mean-input block was found: review scope before extending this audit'
    args.array_output.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(args.array_output,**arrays)
    checks={'actual_configuration_result_and_current_source_bindings_pass':True,'all_required_prefix_saved_start_ids_present':True,
        'all_actual_initial_and_final_W_domains_shapes_finite_and_power_pass':True,
        'all_actual_initial_and_final_encoded_phase_vectors_unit_modulus_pass':True,
        'actual_final_noRIS_flags_and_reported_total_power_rebuilt_pass':True,'actual_original_input_result_bytes_unchanged':True}
    result={'scope':'ACTUAL_EXISTING_NATIVE_saved_initial_final_domains_total_power_only_NOT_QoS_moments_gradients_RNG_full18',
        'observed_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'actual_progress_snapshot_sha256':hashlib.sha256(progress_bytes).hexdigest(),
        'actual_prefix_cases':len(records),'required_full_cases':18,'actual_prefix_starts':count,'required_full_starts':243,
        'actual_state_arrays_sha256':sha(args.array_output),'array_bank_dtype_shape_derived_from_actual_JSON':True,
        'actual_case_records':records,'checks':checks,'all_independent_saved_domain_only_checks_pass':all(checks.values()),
        'actual_mean_inputs_found_in_raw':mean_found,'solver_or_optimizer_called':False,
        'missing_mean_inputs_gradient_channels_or_RNG_synthesized':False,
        'original_full_moment_QoS_independently_certified':False,'original_stage_gradient_stop_independently_certified':False,
        'original_native1000_channels_RNG_independently_replayed':False,'all_selected_solver_callbacks_and_MEX_bound_before_actual_run':False,
        'native_exact_phi_row_column_orientation_certified':False,'full18_numerical_certificate':False,'full_reproduction_pass':False,
        'auditor_source_sha256':sha(Path(__file__)),'numpy_version':np.__version__}
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'actual_cases':len(records),'actual_starts':count,'all_saved_domain_only_checks_pass':True,
        'mean_inputs_found':False,'QoS_gradient_RNG_or_full18_certified':False}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--bank-directory',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--array-output',type=Path,required=True);audit(p.parse_args())
