"""Freeze actual all10 full-scene v3 Python preflights and independent80 chains.

No author documents, generated raw channels, or large inner histories are
copied. This is not a new183-bank, nativeMAT, or published-figure certificate.
"""
import argparse
import hashlib
import json
from pathlib import Path

STRICT = Path(__file__).resolve().parent
ROOT = STRICT.parent.parent
BASE = STRICT / 'cooperative-satcom'
WORK = ROOT / 'work/cooperative-rgd-audit'
SCHEMES = ('AP-NoRIS', 'AP-AO', 'MR-S-NoRIS', 'MR-S-PA', 'MR-S-TS',
           'MR-TTS-NoRIS', 'MR-TTS-PA', 'MR-TTS-TS')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def main(args):
    progress_path = args.input_dir / 'all10-actual-preflight-progress.json'
    snapshot_path = args.input_dir / 'required10-snapshot.json'
    progress, snapshot, audit = read(progress_path), read(snapshot_path), read(args.audit)
    assert progress['required_cases'] == progress['actually_executed_cases'] == 10
    assert progress['all_required_full8_preflight_cases_pass'] and progress['source_unchanged_during_batch']
    assert audit['required_actual_cases'] == audit['actually_independently_audited_cases'] == 10
    assert audit['all_required10_actual_preflight_audits_pass'] and audit['all_available_cases_audit_pass']
    assert audit['production_Python_numeric_AST_exactly_matches_all19_tested_WORK_provider']
    assert audit['production_MATLAB_numeric_body_exactly_matches_immutable_original_WORK_provider']
    assert audit['MATLAB_body_identity_is_NOT_actual_native_execution_success']
    assert audit['audit_source_sha256'] == sha(WORK / 'audit_v3_actual_preflight_cases_v2.py')
    assert audit['snapshot_sha256'] == sha(snapshot_path)
    assert snapshot['WORK_driver_sha256'] == progress['WORK_driver_sha256'] == sha(WORK / 'preflight_v3_all10_phase_failures.py')
    scientific = progress['executed_source_hashes']
    assert len(scientific) == 14 and scientific == snapshot['executed_source_hashes']
    assert scientific == {n: sha(BASE / n) for n in scientific}
    immutable_mat_path = WORK / 'retained-provider-scope-construction-errors-20261004-v4/solve_original_mr_qt_factored_work.m'
    assert sha(immutable_mat_path) == audit['immutable_original_MATLAB_WORK_provider_sha256']
    old_bank_path = BASE / 'outputs/guarded-all-figures-final-python.json'
    old_bank = read(old_bank_path)
    assert sha(old_bank_path) == snapshot['original_complete_bank_sha256']
    assert len(old_bank['results']) == 183
    assert len([p for p in old_bank['results'] if p['valid_figure_point']]) == 154
    assert len([p for p in old_bank['results'] if not p['valid_figure_point']]) == 29
    assert all(x is False for x in old_bank['checks'].values())
    assert {n: sha(BASE / n) for n in old_bank['executed_source_hashes']} == old_bank['executed_source_hashes']
    original10 = {(p['sweep'], p['value']) for p in old_bank['results']
                  if p.get('error') == 'Original RGD Armijo search failed; no phase substitute'}
    assert len(original10) == 10
    audits = {r['index']: r for r in audit['results']}
    summaries = {r['index']: r for r in progress['actual_results']}
    assert set(audits) == set(summaries) == set(range(10))
    compact, inputs, seen = [], [], set()
    stop_count = 0
    for record in snapshot['required_cases']:
        index = record['index']
        identity = (record['old_sweep'], record['old_value'])
        assert identity in original10 and identity not in seen
        seen.add(identity)
        path = args.input_dir / summaries[index]['actual_receipt']
        raw = read(path)
        independent = audits[index]
        assert sha(path) == summaries[index]['actual_receipt_sha256'] == independent['actual_input_receipt_sha256']
        assert independent['all_actual_preflight_audit_checks_pass'] and all(independent['checks'].values())
        assert len(raw['results']) == 1 and raw['source_unchanged_during_run']
        assert raw['executed_source_hashes'] == scientific
        assert raw['old_source_bank_not_upgraded'] and not raw['new_formal183_bank_executed']
        cfg_path = args.input_dir / record['configuration_file']
        assert sha(cfg_path) == record['configuration_file_sha256']
        cfg = read(cfg_path)
        assert raw['configuration'] == cfg
        assert cfg['tuned_not_reported']['monte_carlo_realizations'] == 1000
        assert cfg['tuned_not_reported']['gradient_tolerance'] == 1e-6
        assert cfg['tuned_not_reported']['relative_tolerance'] == 1e-4
        point = raw['results'][0]
        assert point['valid_figure_point'] and all(point[k] for k in
            ('constraint_pass', 'convergence_pass', 'solver_primal_pass', 'qt_bound_pass'))
        assert set(point['schemes']) == set(SCHEMES)
        assert point['monte_carlo']['count'] == 1000
        assert independent['full_channel_moment_replay']['count'] == 1000
        assert independent['full_channel_moment_replay']['all_1000_draw_moments_bitwise_reproduce_receipt']
        assert independent['full_channel_moment_replay']['replayed_moment_error_maximum_difference'] == 0
        scheme_audits = {x['scheme']: x for x in independent['schemes']}
        assert set(scheme_audits) == set(SCHEMES)
        entries = []
        for name in SCHEMES:
            entry = point['schemes'][name]
            checked = scheme_audits[name]
            assert checked['four_gates_pass'] and checked['complete_chain_available']
            assert entry['status']['converged'] and entry['status']['algorithm_success']
            assert len(entry['status']['blocks']) == len(checked['recorded_stops'])
            assert all(s['recorded_actual_stop_pass'] for s in checked['recorded_stops'])
            assert checked['objective_history_stop_and_final_metric_match']
            assert checked['all_phase_history_counts_match'] and checked['all_original_smoothing_levels_completed']
            assert checked['maximum_primal_relative_violation'] <= 1e-5
            assert checked['maximum_QT_bound_violation'] <= 1e-5
            stop_count += len(checked['recorded_stops'])
            entries.append({'scheme': name, 'actual_final_evaluation': entry['evaluation'],
                'actual_status': {k: entry['status'][k] for k in
                    ('converged', 'termination', 'blocks', 'numerical', 'algorithm_success')},
                'phase_source_converged': entry['status'].get('phase_source_converged', None),
                'smoothing_schedule_completed': entry['status'].get('smoothing_schedule_completed', None),
                'independent_receipt_and_history_audit': checked,
                'final_phase_gradient_independently_recomputed': False})
        compact.append({'index': index, 'original_failed_scene': {'sweep': identity[0], 'value': identity[1]},
            'all_reported_physical_parameters': cfg['reported'],
            'only_declared_numerical_control_changes': record['only_numerical_control_changes'],
            'actual_elapsed_seconds': raw['elapsed_seconds'], 'all_actual_four_gates_pass': True,
            'all_eight_complete_original_schemes': entries,
            'actual_full1000_channel_moment_check': point['monte_carlo'],
            'independent_full1000_moment_replay': independent['full_channel_moment_replay'],
            'actual_receipt_sha256': sha(path), 'actual_configuration_sha256': sha(cfg_path),
            'original_failed_checkpoint_sha256': record['old_failure_checkpoint_sha256'],
            'actual_executed_source_unchanged': True})
        inputs.append({'index': index, 'actual_receipt_sha256': sha(path),
            'actual_configuration_sha256': sha(cfg_path),
            'original_failed_checkpoint_sha256': record['old_failure_checkpoint_sha256']})
    assert seen == original10 and len(compact) == 10
    assert not args.output_dir.exists(), 'Fresh public evidence must not overwrite an older frozen identity'
    args.output_dir.mkdir(parents=True)
    public = {'scope': 'actual_all10_previous_phase_failed_full_scenes_Python_v3_original80_chains_and10000_channel_moment_replays_NOT_complete183_nativeMAT_or_historical_figures',
        'required_full_scene_preflights': 10, 'actual_full_scene_preflights': 10,
        'actual_original_complete_scheme_chains': 80, 'actual_recorded_original_stop_blocks': stop_count,
        'actual_channel_moment_draws_executed': 10000,
        'actual_channel_moment_draws_independently_replayed': 10000,
        'maximum_moment_replay_error': 0,
        'all_implementation_numerical_chain_preflight_checks_pass': True,
        'actual_batch_elapsed_seconds': progress['actual_elapsed_seconds'], 'actual_scenes': compact,
        'executed_Python_source_hashes': scientific,
        'source_unchanged_during_actual_runs_and_freeze': True,
        'old183_native_valid': 154, 'old183_native_failed': 29,
        'old183_failures_retained_and_not_upgraded': True,
        'new_complete183_bank_executed': False, 'nativeMAT_v3_complete_preflight_verified': False,
        'independent_final_phase_matrix_gradient_evaluation_available': False,
        'optimized_scheme_performance_monte_carlo_1000_claimed': False,
        'historical_author_channel_geometry_and_figures_recovered': False,
        'source_constraints_all_verified': False, 'full_reproduction_pass': False}
    save(args.output_dir / 'actual-full10-eight-chain-python.json', public)
    save(args.output_dir / 'independent-all80-chain-audit.json', audit)
    save(args.output_dir / 'actual-all10-batch-aggregate.json', progress)
    (args.output_dir / 'README.md').write_text(
        '# Ten full-scene cooperative preflights — actual Python evidence\n\n'
        'All ten original phase-failed scenes were restored from immutable old checkpoints. '
        'Every scene actually executed the eight original algorithm chains; none was discarded or reduced. '
        'All physical, original stop, solver-primal and QT gates passed. The run took approximately24.73minutes.\n\n'
        'An independent audit checked all80 chains and every recorded stop/history, restored all original '
        'physical configurations, and replayed all10000 finite-Rician channel-moment draws with zero receipt difference. '
        'These1000draws per scene validate the channel moments at the declared test phase; they are not1000 '
        'performance realizations of every optimized scheme. The old full runner did not retain final phase matrices, '
        'so their final gradients are not claimed independently reevaluated.\n\n'
        'The disclosed changes are exact circle/softmin objective increments, an author-unreported100000 '
        'safety cap, the unchanged RGD direction/retraction/Armijo and thresholds, and the exact fixed sqrt(scale) '
        'factor outside the same MR-QT cone. The actual production Python numeric body matches the separately '
        'tested19 failed-input provider. Original power/interference constraints and full scene dimensions remain.\n\n'
        'This is NOT a new complete183-point bank, native MATLAB fullpreflight, recovery of original author '
        'coordinates/channel normalization, or agreement with published curves. The old183-point bank remains '
        '154valid/29failed. Prospective MATLAB source-body identity at the independent audit time is only a '
        'text identity and does not imply construction or numerical success.\n\n'
        'The manifest binds all14 actual Python sources, immutable configuration/checkpoint/result hashes, '
        'the batch driver, the independent auditor, and compact public receipts. No author manuscripts, artwork, '
        'private paths, raw channels, or large inner histories are uploaded.\n', encoding='utf-8')
    assert scientific == {n: sha(BASE / n) for n in scientific}
    files = {p.name: {'sha256': sha(p), 'bytes': p.stat().st_size}
             for p in args.output_dir.iterdir() if p.is_file()}
    manifest = {'scope': public['scope'], 'actual_inputs': inputs,
        'actual_old_complete183_bank_sha256': sha(old_bank_path),
        'actual_batch_aggregate_sha256': sha(progress_path), 'actual_required10_snapshot_sha256': sha(snapshot_path),
        'actual_independent_all80_audit_sha256': sha(args.audit),
        'executed_Python_source_hashes': scientific,
        'executed_WORK_driver_sha256': progress['WORK_driver_sha256'],
        'executed_WORK_independent_auditor_sha256': audit['audit_source_sha256'],
        'immutable_original_MATLAB_provider_snapshot_NOT_execution_certificate_sha256': sha(immutable_mat_path),
        'freezer_source_sha256': sha(__file__), 'public_files': files,
        'source_unchanged_during_freeze': True, 'new_full183_success': False,
        'nativeMAT_v3_full_preflight_success': False, 'historical_figure_agreement': False,
        'full_reproduction_pass': False}
    save(args.output_dir / 'manifest.json', manifest)
    print(json.dumps({'actual_full_scenes': 10, 'actual_original_complete_chains': 80,
        'actual_original_stop_blocks': stop_count, 'independent_channel_moment_replay_draws': 10000,
        'all_implementation_preflight_checks_pass': True, 'public_files': len(files) + 1,
        'nativeMAT_v3_full_preflight_success': False, 'new_full183_success': False,
        'full_reproduction_pass': False}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--input-dir', type=Path, default=WORK / 'prospective-v3-all10-phase-preflight-v1')
    p.add_argument('--audit', type=Path, default=WORK / 'prospective-v3-actual-preflight-independent-all10-v2.json')
    p.add_argument('--output-dir', type=Path, default=STRICT / 'validation/cooperative-v3-full10-preflight-python-v1')
    main(p.parse_args())
