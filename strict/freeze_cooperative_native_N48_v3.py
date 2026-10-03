"""Freeze a distinct actual native N48 complete-eight-chain record audit."""
import argparse
import json
from pathlib import Path
import time

import numpy as np

from freeze_cooperative_native_M30_v3 import audit_scheme, sha, read, save, SCHEMES

STRICT=Path(__file__).resolve().parent
ROOT=STRICT.parent.parent
BASE=STRICT/'cooperative-satcom'
WORK=ROOT/'work/cooperative-rgd-audit'
CVX=ROOT/'work/external-cvx-2.2.2/cvx'
ALLOWED=('rmo_max_iterations','rmo_initial_step','rmo_safety_cap_evidence',
         'rmo_exact_increment_representation','mr_QT_representation')


def main(args):
    started=time.perf_counter();assert not args.output_dir.exists()
    native_path=WORK/'prospective-v3-N48-full-ACTUAL-MATLAB-v2.json'
    binding_path=WORK/'prospective-v3-N48-full-ACTUAL-MATLAB-v2-runtime-binding.json'
    cfg_path=WORK/'prospective-v3-N48-INR002-fullcase-configuration.json'
    old_input_path=WORK/'full-singleN48-INR002-exact-factored-MR-python.json'
    old_check_path=WORK/'full-singleN48-INR002-exact-factored-MR-independent-check.json'
    observer_path=WORK/'N48-native-launch-path-error-observer-note-v1.json'
    native,binding,cfg=read(native_path),read(binding_path),read(cfg_path)
    old_input,old_check,observer=read(old_input_path),read(old_check_path),read(observer_path)
    assert sha(old_input_path)==old_check['input_receipt_sha256']=='3caf86f7e275e14bf132a51e3a934a28ed25f14af4077bc07252bba55467123c'
    assert old_input['all_original_chain_gates_pass']
    expected=json.loads(json.dumps(old_input['configuration']))
    for field in ALLOWED:
        expected['tuned_not_reported'][field]=cfg['tuned_not_reported'][field]
    assert expected==cfg
    # MATLAB jsonencode collapses a one-element numeric vector to a scalar.
    # Restore only this declared shape for metadata comparison, not physics.
    native_config=json.loads(json.dumps(native['configuration']))
    assert native_config['tuned_not_reported']['satellite_latitudes_deg']==1.25
    native_config['tuned_not_reported']['satellite_latitudes_deg']=[1.25]
    assert native_config==cfg
    assert cfg['reported']==old_input['configuration']['reported']==binding['full_scene_parameters']
    assert {k:cfg['reported'][k] for k in ('J','U','N','K','M')}=={'J':1,'U':2,'N':48,'K':1,'M':25}
    assert cfg['reported']['power_w']==150 and cfg['reported']['interference_to_noise_ratio']==.02
    assert cfg['tuned_not_reported']['satellite_latitudes_deg']==[1.25]
    assert cfg['tuned_not_reported']['upa_shape']==[6,8]
    assert cfg['tuned_not_reported']['monte_carlo_realizations']==1000
    assert binding['actual_full_result_sha256']==sha(native_path)
    assert native['source_unchanged_during_run'] and binding['source_and_selected_backend_interval_pass']
    assert binding['scientific_source_and_configuration_before']==binding['scientific_source_and_configuration_after']==native['executed_source_hashes']
    assert binding['selected_backend_MAT_and_MEX_inventory_before']==binding['selected_backend_MAT_and_MEX_inventory_after']
    assert binding['actual_selected_backend_name']=='SDPT3'
    runtime_index={}
    for path in CVX.rglob('*'):
        if path.is_file() and path.suffix in ('.m','.mexw64'):
            runtime_index.setdefault(path.name,[]).append(path)
    sources=[v for v in native['executed_source_hashes'].values() if isinstance(v,dict)]
    sources+=binding['selected_backend_MAT_and_MEX_inventory_before'];verified=[]
    for item in sources:
        candidates=[BASE/item['filename'],WORK/item['filename']]+runtime_index.get(item['filename'],[])
        assert any(p.is_file() and sha(p)==item['sha256'] for p in candidates),item['filename']
        if item not in verified:verified.append(item)
    assert any(x['filename'].endswith('.mexw64') for x in verified)
    assert any(x['filename']=='cvx_sdpt3.m' and x['sha256']==binding['actual_backend_callback_Mfile_sha256'] for x in verified)
    assert len(native['results'])==1
    point=native['results'][0];schemes=point['schemes']
    assert [s['scheme'] for s in schemes]==list(SCHEMES)==binding['actual_scheme_names']
    assert point['sweep']=='base' and point['parameter']=='power_w' and point['value']==150
    audited=[]
    for entry in schemes:
        audited.append(audit_scheme(entry,cfg,not entry['scheme'].endswith('-PA') or audited[1]['all_recorded_implementation_checks_pass']))
    qt_count=sum(x['actual_QT_updates'] for x in audited)
    phase_count=sum(x['actual_phase_stop_blocks'] for x in audited)
    assert qt_count==24 and phase_count==45
    assert all(native['checks'].values()) and all(point[k] for k in ('constraint_pass','convergence_pass','solver_primal_pass','qt_bound_pass','valid_figure_point'))
    assert native['overall_implemented_scope_success'] and binding['actual_all_original_implementation_gates_pass']
    assert native['all_configured_sweeps_requested'] is False and native['new_formal183_bank_executed'] is False
    mc=point['monte_carlo'];assert mc['count']==binding['monte_carlo_moment_draw_count']==1000
    assert all(np.isfinite(mc[k]) and mc[k]>=0 for k in ('second_moment_max_relative_error','fourth_moment_max_relative_error'))
    assert observer['kind']=='root_observer_note_not_captured_raw_stdout'
    assert observer['actual_tool_session_id']==12330 and observer['actual_exit_code']==1
    assert observer['numeric_scene_executed'] is False and observer['raw_terminal_log_file_available'] is False
    m30_public=STRICT/'validation/cooperative-native-M30-full8-v3'
    m30_manifest=read(m30_public/'manifest.json')
    for name,item in m30_manifest['public_files'].items():assert sha(m30_public/name)==item['sha256']
    helper_sha=sha(STRICT/'freeze_cooperative_native_M30_v3.py')
    assert helper_sha==m30_manifest['freezer_and_independent_record_auditor_sha256']
    audit={'scope':'independent_actual_native_N48_INR002_full8_RECORD_runtime_audit_NOT_final_matrix_or_rawMC_replay',
        'actual_complete_chains':8,'actual_QT_updates':qt_count,'actual_phase_stop_blocks':phase_count,
        'all_recorded_original_implementation_checks_pass':True,
        'same_predeclared_full_N48_diagnostic_physical_input_preserved':True,
        'same_old183_point_identity_independently_asserted':False,
        'original_physical_parameters_unchanged_from_bound_prior_N48_fullcase':True,
        'actual_unreported_satellite_latitude_deg':1.25,
        'native_JSON_singleton_latitude_scalar_shape_restored_only_for_metadata_comparison':True,
        'source_input_configuration_and_actual_backend_interval_verified':True,
        'current_all_recorded_scientific_CVX_backend_MAT_and_MEX_hashes_verified':True,
        'actual_native_elapsed_seconds':native['elapsed_seconds'],'actual_outer_elapsed_seconds':binding['actual_seconds'],
        'actual_schemes':audited,'recorded_channel_moment_validation':mc,
        'native1000_draw_loop_configuration_and_source_contract_verified':True,
        'raw_native_MATLAB_1000_draws_independently_replayed':False,
        'optimized_performance_1000_draws_executed':False,
        'phase_or_W_final_matrices_saved_by_this_v3_runner':False,
        'final_phase_gradient_independently_recomputed':False,
        'final_W_or_power_physical_metrics_independently_recomputed':False,
        'old183_bank_154_valid_29_failed_not_upgraded':True,
        'new_complete183_bank_verified':False,'historical_author_inputs_or_published_figures_recovered':False,
        'all_source_constraints_verified':False,'full_reproduction_pass':False}
    args.output_dir.mkdir(parents=True)
    save(args.output_dir/'independent-native-eight-chain-record-audit.json',audit)
    save(args.output_dir/'actual-native-fullscene-compact-result.json',{
        'scope':'DERIVED_COMPACT_actual_native_v3_complete_one_predeclared_N48_scene_all8_chains_NO_numeric_values_altered',
        'original_native_result_sha256':sha(native_path),'original_native_runtime_binding_sha256':sha(binding_path),
        'configuration':cfg,'schemes':[{k:s[k] for k in ('scheme','evaluation','status')} for s in schemes],
        'monte_carlo':mc,'checks':native['checks'],'elapsed_seconds':native['elapsed_seconds'],
        'raw_phase_histories_not_copied_but_complete_record_SHA_bound':True,
        'private_absolute_paths_in_this_derived_receipt':False,'full_reproduction_pass':False})
    save(args.output_dir/'actual-native-source-runtime-bindings.json',{
        'scope':'actual_begin_end_scientific_config_and_selected_CVX_SDPT3_MAT_MEX_identity_rechecked',
        'actual_source_interval_records_match':True,'current_actual_hashes_match':True,
        'unique_actual_source_and_runtime_bindings':verified,
        'actual_full_result_sha256':sha(native_path),'actual_runtime_receipt_sha256':sha(binding_path),
        'actual_selected_backend':binding['actual_selected_backend_name'],
        'actual_selected_backend_version':binding['actual_selected_backend_version'],
        'actual_backend_callback_sha256':binding['actual_backend_callback_Mfile_sha256'],
        'all_recorded_runtime_binaries_independently_hash_verified':True,
        'final_phase_matrices_independently_verified':False,'full_reproduction_pass':False})
    save(args.output_dir/'retained-path-startup-observer-note.json',{
        'scope':'explicit_derived_root_observer_note_NOT_machine_captured_failed_stdout',
        'actual_preserved_observer_note_sha256':sha(observer_path),
        'observed_startup_failure':observer,'earlier_startup_not_numeric_case_failure_or_success':True,
        'replacement_actual_native_numeric_receipts_separately_verified':True})
    (args.output_dir/'README.md').write_text(
        '# Actual native MATLAB N48 v3 complete eight-chain diagnostic\n\n'
        'This NEW package does not overwrite the M30 evidence. It binds the predeclared N48 configuration '
        'and the actual native result/runtime interval. The same prior full N48 diagnostic physical input '
        'is preserved: J=1, U=2, N=48, K=1, M=25, power150 W, satellite Rician0 dB and normalized INR0.02. '
        'The unreported chosen satellite latitude is explicitly1.25 degrees and UPA shape6x8; it is not '
        'silently relabelled as some other old183-bank point or recovered author geometry. Only the same '
        'five declared v3 numerical representation/control fields differ from that bound prior input.\n\n'
        'All8 native original chains executed. Independent record inspection checks24 QT updates,45 phase '
        'stopping blocks, all final reported physical margins and minimum SINRs, every saved outer stopping '
        'residual, all available TS phase-history counts and every smoothing level/repeat stop, along with '
        'accepted original primal/QT/monotonicity diagnostics. All recorded implementation checks pass. '
        'The largest phase block took930 steps; original1e-6 gradient and1e-4 relative thresholds remain '
        'unchanged. The native result records179.6928303 seconds. Actual source/input/configuration/CVX '
        'and selected SDPT3 MAT/MEX begin/end hashes are current-byte matched.\n\n'
        'The earlier path startup attempt had no numerical scene execution. Its preserved root observer '
        'note explicitly says no raw terminal log is available; it is not a fabricated machine failure '
        'receipt. Correcting the launch search path does not change the scientific source.\n\n'
        'As in M30, v3 did not save final phi/W/p/channel arrays or raw native1000 draws. Independent '
        'matrix-gradient/physical replay, complete primal-dual state checks and raw RNG replay are '
        'therefore false. The actual1000 count and second/fourth-moment errors are recorded channel-moment '
        'validation, not1000 optimized-performance draws. Compact derived outputs retain stops, solver '
        'attempts, metrics and full original SHA bindings, not private author files or absolute paths. '
        'This is not a complete183 bank or published-figure reproduction; historical geometry and '
        'full_reproduction_pass remain false.\n',encoding='utf-8')
    public={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in args.output_dir.iterdir() if p.is_file()}
    save(args.output_dir/'manifest.json',{'scope':audit['scope'],
        'freezer_source_sha256':sha(__file__),'shared_immutable_M30_record_auditor_sha256':helper_sha,
        'original_native_result_sha256':sha(native_path),'original_native_runtime_receipt_sha256':sha(binding_path),
        'immutable_predeclared_N48_configuration_sha256':sha(cfg_path),
        'bound_prior_same_N48_fullcase_sha256':sha(old_input_path),'bound_prior_N48_independent_record_check_sha256':sha(old_check_path),
        'retained_actual_path_startup_observer_note_sha256':sha(observer_path),
        'previous_M30_public_manifest_sha256':sha(m30_public/'manifest.json'),'previous_M30_public_unmodified':True,
        'public_files':public,'independent_record_audit_seconds':time.perf_counter()-started,
        'native_predeclared_N48_full8_execution_record_verified':True,
        'independent_actual_final_matrix_gradient_or_rawMC_replay_verified':False,
        'new_full183_bank_verified':False,'full_reproduction_pass':False})
    print(json.dumps({'actual_native_chains':8,'all_recorded_implementation_checks_pass':True,
        'actual_QT_updates':qt_count,'actual_phase_stop_blocks':phase_count,'public_files':len(public)+1,
        'final_gradient_independently_recomputed':False,'new_complete183_bank_verified':False}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',type=Path,default=STRICT/'validation/cooperative-native-N48-full8-v3')
    main(parser.parse_args())
