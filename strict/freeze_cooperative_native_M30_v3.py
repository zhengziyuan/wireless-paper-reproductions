"""Independently audit/freeze actual native M30 eight-chain v3 receipts.

Audit recorded values, not just flags. No solver rerun; no claimed final
matrix-gradient or raw-MATLAB-MC replay when those states were not saved.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

STRICT = Path(__file__).resolve().parent
ROOT = STRICT.parent.parent
BASE = STRICT / 'cooperative-satcom'
WORK = ROOT / 'work/cooperative-rgd-audit'
CVX = ROOT / 'work/external-cvx-2.2.2/cvx'
FOLDER = WORK / 'prospective-v3-all10-phase-preflight-v1'
SCHEMES = ('AP-NoRIS', 'AP-AO', 'MR-S-NoRIS', 'MR-S-PA', 'MR-S-TS',
           'MR-TTS-NoRIS', 'MR-TTS-PA', 'MR-TTS-TS')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def items(value):
    return [value] if isinstance(value, dict) else value


def array(value):
    return np.asarray(value, dtype=float).reshape(-1)


def history_summary(value):
    x = array(value)
    assert len(x) and np.all(np.isfinite(x))
    return {'count': len(x), 'first': float(x[0]), 'last': float(x[-1]),
            'little_endian_float64_sha256': hashlib.sha256(x.astype('<f8').tobytes()).hexdigest(),
            'minimum_recorded_direct_objective_increment': float(np.min(np.diff(x))) if len(x)>1 else None}


def audit_scheme(entry, config, phase_source_pass):
    name = entry['scheme']; settings = config['tuned_not_reported']; physical = config['reported']
    status = entry['status']; power = array(entry['evaluation']['satellite_power'])
    leak = array(entry['evaluation']['gt_interference']); sinr = array(entry['evaluation']['sinr'])
    denominator = array(entry['evaluation']['denominator'])
    assert len(power)==physical['J'] and len(leak)==physical['K'] and len(sinr)==physical['U']
    assert len(denominator)==physical['U']
    finite = all(np.all(np.isfinite(x)) for x in (power,leak,sinr,denominator))
    finite = finite and np.all(power>=0) and np.all(leak>=0) and np.all(sinr>=0) and np.all(denominator>0)
    limit = (physical['interference_to_noise_ratio'] if 'interference_to_noise_ratio' in physical
             else 10**(physical['interference_to_noise_db']/10))
    physical_error = float(max(0, np.max(power-physical['power_w']), np.max(leak-limit)))
    stops = items(status['blocks']); phases = []; relatives = []
    for stop in stops:
        rule = stop['stop_rule']; count = stop['iterations']; cap = stop['iteration_cap']; value = stop['final_residual']
        assert stop['converged'] is True and isinstance(count,int) and 0<=count<=cap
        assert isinstance(value,(int,float)) and np.isfinite(value)
        if rule=='Riemannian_gradient_norm':
            assert stop['threshold']==settings['gradient_tolerance']==1e-6
            assert cap==settings['rmo_max_iterations']==100000 and 0<=value<1e-6
            phases.append(stop)
        else:
            assert rule=='signed_relative_objective_increase'
            assert stop['threshold']==settings['relative_tolerance']==1e-4
            expected_cap=settings['ao_max_iterations'] if name=='AP-AO' else settings['qt_max_iterations']
            assert cap==expected_cap and value<1e-4
            relatives.append(stop)
    assert len(relatives)==1
    h = array(entry['history']['power'] if name.endswith('-TS') else entry['history'])
    assert len(h)>=2 and np.all(np.isfinite(h))
    residual = float((h[-1]-h[-2])/max(abs(h[-2]),1e-12))
    assert relatives[0]['iterations']==len(h)-1 and residual==relatives[0]['final_residual']
    final_metric_error = float(abs(h[-1]-np.min(sinr)))
    assert final_metric_error<=1e-10
    assert np.min(np.diff(h))>=-settings['solver_objective_tolerance']
    if name=='AP-AO':
        assert len(phases)==len(h)-1
    elif not name.endswith('-TS'):
        assert not phases
    if name.endswith('-PA'):
        assert phase_source_pass and status['phase_source_converged'] is True
    diagnostics = items(status['solver_diagnostics'])
    assert len(diagnostics)==len(h)-1
    primal, bound, attempt_records = [], [], []
    for index, record in enumerate(diagnostics):
        raw=record['solver_diagnostics']; pv=raw['constraint_max_relative_violation']; bv=record['qt_bound_max_violation']
        assert np.isfinite(pv) and 0<=pv<=settings['solver_primal_relative_tolerance']==1e-5
        assert np.isfinite(bv) and 0<=bv<=settings['qt_bound_tolerance']==1e-5
        primal.append(pv);bound.append(bv)
        attempts=items(raw['same_original_QT_numerical_attempts'])
        assert 1<=len(attempts)<=2
        assert [a['numerical_precision'] for a in attempts]==['high','best'][:len(attempts)]
        assert sum(a['accepted'] is True for a in attempts)==1 and attempts[-1]['accepted'] is True
        for attempt in attempts:
            if not attempt['accepted']:
                attempt_records.append({'QT_step':index+1,'accepted':False,
                    'numerical_precision':attempt['numerical_precision'],'retained_failure':True})
                continue
            before,after=attempt['before_minimum_sinr'],attempt['after_minimum_sinr']
            assert np.isfinite(before) and np.isfinite(after)
            assert abs(before-h[index])<=1e-10
            monotonicity=max(0,before-after)
            assert monotonicity<=settings['solver_objective_tolerance']==1e-5
            assert attempt['primal_relative_violation']==pv and attempt['qt_bound_violation']==bv
            if name=='AP-AO':
                assert after<=h[index+1]+1e-5
            else:
                assert abs(after-h[index+1])<=1e-10
            assert 'Solved' in attempt['solver_status']
            attempt_records.append({'QT_step':index+1,**attempt,
                'independently_recomputed_original_QT_monotonicity_violation':monotonicity})
    numerical=status['numerical']
    assert numerical['maximum_primal_relative_violation']==max(primal)
    assert numerical['maximum_qt_bound_violation']==max(bound)
    assert numerical['solver_primal_relative_tolerance']==numerical['qt_bound_tolerance']==1e-5
    assert numerical['solver_primal_pass'] and numerical['qt_bound_pass']
    phase_records=[]
    if name.endswith('-TS'):
        histories=items(entry['history']['phase']);assert len(histories)==len(phases)
        levels=[];mu=settings['smoothing_initial']
        while mu>=settings['smoothing_final']:
            levels.append(mu);mu/=2
        actual_levels=list(dict.fromkeys(x['mu'] for x in histories))
        assert actual_levels==levels and status['smoothing_schedule_completed'] is True
        for history,stop in zip(histories,phases):
            values=array(history['objective']);assert len(values)-1==stop['iterations']
            phase_records.append({'mu':history['mu'],'recorded_stop':stop,
                'actual_history_identity':history_summary(values),
                'gradient_independently_recomputed_from_final_phase':False})
        for level in levels:
            group=[p for p in phase_records if p['mu']==level]
            assert 1<=len(group)<=settings['smoothing_max_repeats']
            gains=[p['actual_history_identity']['last']-p['actual_history_identity']['first'] for p in group]
            assert gains[-1]<=settings['smoothing_progress_tolerance']
            assert all(g>settings['smoothing_progress_tolerance'] for g in gains[:-1])
            for previous,current in zip(group,group[1:]):
                assert previous['actual_history_identity']['last']==current['actual_history_identity']['first']
    assert status['converged'] and status['algorithm_success']
    checks={'recorded_physical_constraints_independently_checked':bool(finite and physical_error<1e-5),
        'all_recorded_original_stopping_residuals_counts_thresholds_pass':True,
        'all_saved_outer_QT_histories_counts_relative_stops_final_SINR_pass':True,
        'all_original_QT_attempt_precision_and_monotonicity_records_pass':True,
        'all_available_TS_phase_history_counts_and_smoothing_repeat_stops_pass':True}
    assert all(checks.values())
    return {'scheme':name,'checks':checks,'all_recorded_implementation_checks_pass':True,
        'actual_evaluation':entry['evaluation'],'actual_power_limits_w':[physical['power_w']]*physical['J'],
        'actual_normalized_GT_interference_limits':[limit]*physical['K'],
        'independently_computed_physical_maximum_violation':physical_error,
        'actual_recorded_original_stops':stops,'actual_saved_final_QT_outer_history':h.tolist(),
        'independently_recomputed_relative_stop_residual':residual,
        'independently_checked_final_history_minimum_SINR_error':final_metric_error,
        'actual_original_QT_attempts':attempt_records,'actual_TS_phase_records':phase_records,
        'actual_QT_updates':len(diagnostics),'actual_phase_stop_blocks':len(phases),
        'actual_recorded_phase_steps':sum(s['iterations'] for s in phases),
        'maximum_actual_recorded_phase_steps':max((s['iterations'] for s in phases),default=0),
        'maximum_primal_relative_violation':max(primal),'maximum_QT_bound_violation':max(bound),
        'AP_AO_phase_objective_histories_saved':False if name=='AP-AO' else None,
        'all_phase_Armijo_increments_independently_recomputed':False,
        'final_phase_gradient_independently_recomputed':False,
        'final_W_or_power_physical_metrics_independently_recomputed':False,
        'every_QT_primal_dual_state_independently_certified80digits':False}


def main(args):
    started=time.perf_counter();assert not args.output_dir.exists()
    native_path=WORK/'prospective-v3-M30-full-ACTUAL-MATLAB-v2.json'
    binding_path=WORK/'prospective-v3-M30-full-ACTUAL-MATLAB-v2-runtime-binding.json'
    cfg_path=FOLDER/'case-00-configuration.json';snapshot_path=FOLDER/'required10-snapshot.json'
    native,binding,cfg,snapshot=read(native_path),read(binding_path),read(cfg_path),read(snapshot_path)
    record=snapshot['required_cases'][0]
    assert record['index']==0 and record['old_sweep']=='subsurfaces_kL20' and record['old_value']==30
    assert sha(cfg_path)==record['configuration_file_sha256']
    originals=[p for p in (BASE/'outputs/guarded-all-figures-final').glob('subsurfaces_kL20-*.json')
               if sha(p)==record['old_failure_checkpoint_sha256']]
    assert len(originals)==1
    old_path=originals[0];old=read(old_path);old_cfg=old['contract']['configuration']
    expected=json.loads(json.dumps(old_cfg))
    for field,change in record['only_numerical_control_changes'].items():
        assert old_cfg['tuned_not_reported'].get(field)==change['old']
        expected['tuned_not_reported'][field]=change['new']
    assert expected==cfg==native['configuration']
    assert cfg['reported']==old_cfg['reported']==binding['full_scene_parameters']
    assert old['contract']['sha256']==record['old_configuration_contract_sha256']
    assert old['result']['valid_figure_point'] is False
    assert {k:cfg['reported'][k] for k in ('J','U','N','K','M')}=={'J':3,'U':2,'N':16,'K':1,'M':30}
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
    scientific=[v for v in native['executed_source_hashes'].values() if isinstance(v,dict)]
    runtime=binding['selected_backend_MAT_and_MEX_inventory_before'];verified=[]
    for item in scientific+runtime:
        candidates=[BASE/item['filename'],WORK/item['filename'],FOLDER/item['filename']]+runtime_index.get(item['filename'],[])
        assert any(p.is_file() and sha(p)==item['sha256'] for p in candidates),item['filename']
        if item not in verified:verified.append(item)
    assert any(x['filename'].endswith('.mexw64') for x in verified)
    assert any(x['filename']=='cvx_sdpt3.m' and x['sha256']==binding['actual_backend_callback_Mfile_sha256'] for x in verified)
    assert len(native['results'])==1
    point=native['results'][0];schemes=point['schemes']
    assert [s['scheme'] for s in schemes]==list(SCHEMES)==binding['actual_scheme_names']
    assert point['sweep']=='base' and point['parameter']=='power_w' and point['value']==cfg['reported']['power_w']
    audited=[]
    for entry in schemes:
        audited.append(audit_scheme(entry,cfg,not entry['scheme'].endswith('-PA') or audited[1]['all_recorded_implementation_checks_pass']))
    assert sum(x['actual_QT_updates'] for x in audited)==33
    assert sum(x['actual_phase_stop_blocks'] for x in audited)==48
    assert all(native['checks'].values()) and all(point[k] for k in ('constraint_pass','convergence_pass','solver_primal_pass','qt_bound_pass','valid_figure_point'))
    assert native['overall_implemented_scope_success'] and binding['actual_all_original_implementation_gates_pass']
    assert native['all_configured_sweeps_requested'] is False and native['new_formal183_bank_executed'] is False
    mc=point['monte_carlo'];assert mc['count']==binding['monte_carlo_moment_draw_count']==1000
    assert np.isfinite(mc['second_moment_max_relative_error']) and mc['second_moment_max_relative_error']>=0
    assert np.isfinite(mc['fourth_moment_max_relative_error']) and mc['fourth_moment_max_relative_error']>=0
    runner=(BASE/'run_strict_cooperative_v3.m').read_text(encoding='utf-8')
    assert "rng(seed,'twister')" in runner and 'for realization=1:count' in runner
    assert 'moment_mc(data,scene.tuned_not_reported.monte_carlo_realizations,scene.tuned_not_reported.seed)' in runner
    assert 'phi=ones(U,M)' in runner
    old_native_path=WORK/'production-v2-M30-capture-matlab-20261004-v2.json'
    old_native=read(old_native_path)
    assert all(v is False for v in old_native['checks'].values())
    audit={'scope':'independent_actual_native_M30_full_eight_chain_RECORD_and_runtime_audit_NOT_final_matrix_or_rawMC_replay',
        'actual_complete_chains':8,'actual_QT_updates':33,'actual_phase_stop_blocks':48,
        'all_recorded_original_implementation_checks_pass':True,'original_physical_scene_preserved':True,
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
        'old_native_M30_v2_failure_sha256':sha(old_native_path),'old_native_M30_v2_failure_not_upgraded':True,
        'old183_bank_154_valid_29_failed_not_upgraded':True,
        'new_complete183_bank_verified':False,'historical_author_inputs_or_published_figures_recovered':False,
        'all_source_constraints_verified':False,'full_reproduction_pass':False}
    args.output_dir.mkdir(parents=True)
    save(args.output_dir/'independent-native-eight-chain-record-audit.json',audit)
    save(args.output_dir/'actual-native-fullscene-compact-result.json',{
        'scope':'DERIVED_COMPACT_actual_native_v3_complete_one_M30_scene_all8_chains_NO_numeric_values_altered',
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
    (args.output_dir/'README.md').write_text(
        '# Actual native MATLAB M30 v3 full eight-chain preflight\n\n'
        'This separate evidence package binds the actual native full result and runtime receipt. '
        'The complete physical scene is J=3, U=2, N=16, K=1, M=30, power50 W and satellite Rician20 dB. '
        'Its immutable original failed-scene configuration is preserved except for the five explicitly '
        'declared numerical-control/representation fields. No original model, constraint, stopping threshold '
        'or reference ordinate is changed. The old183-point bank and failed native v2 result remain unchanged.\n\n'
        'All8 original chains were executed. Independent record inspection recomputes every final physical '
        'margin,33 accepted QT updates and their monotonicity/precision checks,48 recorded phase stopping '
        'blocks, outer relative residuals, final reported minimum SINRs, and every available TS phase-history '
        'length/smoothing-level/repeat stopping condition. This checks numerical records, not just success flags. '
        'The longest phase block took47572 steps under the declared unreported100000 cap; original1e-6 '
        'gradient and1e-4 relative thresholds remain unchanged. Native execution took438.4089921 seconds '
        '(outer source/backend evidence wrapper440.2664656 seconds).\n\n'
        'All recorded scientific/input/configuration/CVX and actually selected SDPT3 MAT/MEX bytes are '
        'hash-matched against the actual unchanged begin/end receipts. Source/input/output identities '
        'are preserved separately from scientific historical conformance.\n\n'
        'Important limits: the v3 runner did not save final phi, AP W, MR p, channel deterministic arrays or '
        'raw native MC draws. Final gradients, matrix-based physical metrics and full primal/dual states '
        'therefore are NOT independently recomputed here. Direct phase-history differences may contain '
        'floating cancellation; they are retained, not relabelled as independent Armijo certificates. '
        'The1000 count and finite-Rician second/fourth moment errors are actual recorded channel-moment '
        'validation and are source-loop/configuration consistent. They are NOT1000 performance draws '
        'of the optimized schemes and their raw native RNG replay has not been independently executed.\n\n'
        'The compact result is an explicitly derived receipt: large phase histories are replaced by '
        'lengths/endpoints/hashes in the audit; actual stops, solver attempts and metrics are retained. '
        'No private absolute paths, raw author manuscript or artwork are copied. Original local result '
        'bytes remain unchanged and SHA-bound. A future recording-only adapter must save the missing '
        'states before any new full183-bank claim. Historical author inputs, complete183 execution and '
        'published-figure agreement remain unverified; full_reproduction_pass is false.\n',encoding='utf-8')
    public={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in args.output_dir.iterdir() if p.is_file()}
    save(args.output_dir/'manifest.json',{'scope':audit['scope'],
        'freezer_and_independent_record_auditor_sha256':sha(__file__),
        'original_native_result_sha256':sha(native_path),'original_native_runtime_receipt_sha256':sha(binding_path),
        'immutable_config_sha256':sha(cfg_path),'immutable_original_failed_scene_sha256':sha(old_path),
        'old_failed_scene_contract_sha256':old['contract']['sha256'],
        'all10_required_old_scene_snapshot_sha256':sha(snapshot_path),
        'retained_old_native_v2_failure_sha256':sha(old_native_path),'public_files':public,
        'independent_record_audit_seconds':time.perf_counter()-started,
        'native_one_M30_full8_execution_record_verified':True,
        'independent_actual_final_matrix_gradient_or_rawMC_replay_verified':False,
        'new_full183_bank_verified':False,'full_reproduction_pass':False})
    print(json.dumps({'actual_native_chains':8,'all_recorded_implementation_checks_pass':True,
        'actual_QT_updates':33,'actual_phase_stop_blocks':48,'public_files':len(public)+1,
        'final_gradient_independently_recomputed':False,'new_complete183_bank_verified':False}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',type=Path,default=STRICT/'validation/cooperative-native-M30-full8-v3')
    main(parser.parse_args())
