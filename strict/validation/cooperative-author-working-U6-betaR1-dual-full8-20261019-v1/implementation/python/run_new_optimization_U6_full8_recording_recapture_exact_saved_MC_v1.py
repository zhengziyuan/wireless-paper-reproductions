"""New full8 optimization recapture, exact old1000 return reused; no new draws.

No process controller is included. No geometry generator, source conversion,
old checkpoint, saved optimized state or author random channel is consumed.
The complete current reconstruction controls and actual1000 passive tape remain.
"""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import traceback


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fresh_json(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write('\n')


def module_from_file(path, name):
    need(name not in sys.modules, 'One fresh isolated module: '+name)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--execute', action='store_true', required=True)
    args = parser.parse_args()
    need(sys.dont_write_bytecode and not sys.flags.optimize, 'Use -B with active assertions')
    plan_bytes = args.plan.read_bytes(); plan = json.loads(plan_bytes)
    output = Path(plan['fresh_output_directory']).resolve()
    need(not output.exists(), 'Preserve every prior actual/partial output; no retry/resume')
    watched = {str(Path(path).resolve()): value for path, value in plan['source_and_input_pins'].items()}
    before = {path: sha(Path(path).read_bytes()) for path in watched}
    need(before == watched, 'Admitted source/input identity changed')
    before[str(args.plan.resolve())] = sha(plan_bytes)
    code = 1; public_code = None; error = None; recording_errors = []
    retained = []; factory_calls = []; loaded_identity = None
    try:
        import numpy as np
        config_path = Path(plan['configuration'])
        cfg_raw = config_path.read_bytes(); cfg = json.loads(cfg_raw)
        need(sha(cfg_raw) == watched[str(config_path.resolve())], 'Exact converted configuration')
        need(cfg['reported']['U'] == 6 and cfg['reported']['J'] == 3 and cfg['reported']['K'] == 1,
             'Explicit U6/J3/K1 source variant required')
        variant = cfg['physical_input_variant']
        need(variant['requires_explicit_saved_factory'] is True and variant['stage'] == 'enabled',
             'Canonical source input requires the explicit enabled saved factory')
        data_path = Path(plan['canonical_data_npz']); data_raw = data_path.read_bytes()
        need(sha(data_raw) == watched[str(data_path.resolve())], 'Exact converted canonical arrays')
        adapter = module_from_file(Path(plan['saved_factory_adapter']), '_author_U6_saved_factory_adapter')
        with np.load(io.BytesIO(data_raw), allow_pickle=False) as saved:
            need(set(saved.files) == set(adapter.SHAPES) | {'power_limit', 'interference_limit'},
                 'Exactly eleven actual data fields and both original limits')
            data = {name: saved[name].copy() for name in adapter.SHAPES}
            power = saved['power_limit'].copy(); limit = saved['interference_limit'].copy()
        for name, array in data.items():
            expected = plan['canonical_output_field_identities'][name]
            need(array.shape == adapter.SHAPES[name] and str(array.dtype) == expected['dtype']
                 and list(array.shape) == expected['shape'] and bool(np.all(np.isfinite(array)))
                 and sha(array.tobytes(order='F')) == expected['column_major_raw_SHA256'],
                 'Actual converted field bytes/shape differ: '+name)
        need(power.shape == (3,) and np.array_equal(power, np.full(3, 50.)), 'Original P50 each')
        need(limit.shape == (1,) and np.array_equal(limit, np.array([.01])), 'Original normalized INR.01')
        loaded_identity = dict(input_npz_SHA256=sha(data_raw), configuration_SHA256=sha(cfg_raw),
                               all11_actual_converted_field_bytes_exact=True,
                               no_input_reconstruction_or_original_stochastic_H_read=True)
        frozen = module_from_file(Path(plan['public_full8_entry']), '_author_U6_frozen_public_full8')
        tapper = module_from_file(Path(plan['MC_return_reuse_installer']), '_author_U6_exact_saved_MC_return_reuse')
        transport = module_from_file(Path(plan['raw_backup_first_transport']), '_author_U6_raw_backup_first_transport')
        base_sources = frozen.check_sources
        def bound_sources(root):
            source_root, identities = base_sources(root)
            identities.update(before)
            return source_root, identities
        frozen.check_sources = bound_sources
        base_prepare = frozen.prepare_installation
        saved_factory = adapter.make_saved_scenario_factory(data, power, limit, cfg)
        def prepare(*pos, **kw):
            installation = base_prepare(*pos, **kw)
            def canonical_factory(scene):
                need(not factory_calls, 'One exact single-base saved input; no implicit sweep')
                value = saved_factory(scene)
                factory_calls.append(dict(canonical_saved_input_used=True,
                                          geometry_generator_calls=0,
                                          selected_stage='enabled'))
                return value
            # Frozen recorder.execute has not yet captured original.make_scenario.
            installation['entry'].original.make_scenario = canonical_factory
            transport_binding = transport.install_raw_backup_first_recorder_saver(installation['recorder'])
            fresh_json(output/'RAW_BACKUP_FIRST_REVERSIBLE_MAT_TRANSPORT_BOUND_V1.json', transport_binding)
            tape, binding = tapper.install(installation, output/'actual-saved-MC-return-reuse',
                                          Path(plan['previous_actual_MC_directory']), cfg,
                                          Path(plan['previous_independent_MC_audit']))
            retained.append(tape)
            fresh_json(output/'NEW_OPTIMIZATION_ONLY_MC_BLOCK_EXACT_SAVED_RETURN_REUSE_BINDING_V1.json', binding)
            fresh_json(output/'CANONICAL_SAVED_FACTORY_BOUND_BEFORE_RECORDER_CAPTURE_V1.json',
                       dict(**loaded_identity, exact_configuration_single_base=True,
                            source_stage='enabled', factory_bound_before_recorder=True,
                            original_initializer_and_full8_algorithm_bodies_unchanged=True,
                            author_W_mat_random_phi_and_MC_population_not_recovered=True,
                            physical_reference_or_convergence_PASS=False))
            return installation
        frozen.prepare_installation = prepare
        prior_argv = sys.argv
        sys.argv = [str(plan['public_full8_entry']), 'full8-single-configuration',
                    '--source-root', str(plan['public_full8_source_root']),
                    '--configuration', str(config_path), '--configuration-sha256', sha(cfg_raw),
                    '--data-dir', str(output), '--full', '--sweep', 'base', '--execute']
        try:
            public_code = frozen.main()
            need(type(public_code) is int, 'Preserve actual frozen main return code')
            code = public_code
        finally:
            sys.argv = prior_argv
    except SystemExit as failure:
        public_code = failure.code if type(failure.code) is int else 1
        code = public_code
        error = dict(type='SystemExit', message=str(failure))
    except BaseException as failure:
        error = dict(type=type(failure).__name__, message=str(failure), traceback=traceback.format_exc())
        code = 1
    finally:
        for tape in retained:
            try:
                tape.preserve_partial()
            except BaseException as failure:
                recording_errors.append(dict(type=type(failure).__name__, message=str(failure)))
        after = {}; source_errors = []
        for path in before:
            try:
                after[path] = sha(Path(path).read_bytes())
            except BaseException as failure:
                source_errors.append(dict(path=path, type=type(failure).__name__, message=str(failure)))
        source_ok = not source_errors and before == after
        complete_path = output/'actual-saved-MC-return-reuse/ACTUAL_EXACT_SAVED_1000_RETURN_REUSED_NO_NEW_RNG_V1.json'
        full_tape = False
        try:
            if complete_path.is_file():
                saved_MC = json.loads(complete_path.read_bytes())
                full_tape = (saved_MC.get('all11_data_and_original_ones_phi_exact') is True
                             and saved_MC.get('reused_completed_actual_draws') == 1000
                             and saved_MC.get('actual_new_MC_RNG_draws') == 0)
        except BaseException as failure:
            recording_errors.append(dict(type=type(failure).__name__, message=str(failure)))
        # Failed optimization returns retain their first real code/tape status.
        # Only an otherwise-successful run requires complete recording and one factory.
        if code == 0 and (not full_tape or len(factory_calls) != 1 or recording_errors or error):
            code = 1
        if not source_ok:
            code = 2
        output.mkdir(parents=True, exist_ok=True)
        fresh_json(output/'ACTUAL_NEW_OPTIMIZATION_RECAPTURE_U6_FULL8_WITH_EXACT_OLD_MC_REUSE_OUTCOME_V1.json', dict(
            public_wrapper_exit_code=public_code, effective_entry_exit_code=code,
            exception=error, recording_errors=recording_errors,
            source_before=before, source_after=after, source_errors=source_errors,
            source_and_canonical_input_interval_unchanged=source_ok,
            canonical_input_readback=loaded_identity, actual_saved_factory_calls=factory_calls,
            previous_actual1000_return_exactly_reused=full_tape, actual_new_MC_RNG_draws=0,
            actual_full8_action_summary='action-summary.json',
            checkpoint_scope='Frozen recorder original.full_run(config,base,None); cold full8, no old result/state resume.',
            source_variant='NEW full8 optimization recording recapture of same canonical native U6 input. First lost recording not recovered. Existing corrected algorithms/full reconstruction controls unchanged.',
            MC_scope='Previous actual1000 channel-moment return reused after exact11data+onesphi+config/seed/count binding, actualnewdraws0; not performanceMC average or recovered authorpopulation.',
            source_initialization_scope='Existing corrected cold initializer; author cachedW/randomphi not recovered.',
            historical_literal_raw_scope=dict(numeric_comparisons=130, strict_pass=120,
                strict_complex_component_failures_retained=10, compact_storage_dtype_false_reclassified=29,
                strict_raw_all_input_PASS=False, ULP_explanation_does_not_overwrite_strict_failures=True),
            all_new_independent_ownstate_QT_phase_Moments_dual_original_reference_or_fullpaper_PASS=False))
        print(json.dumps(dict(effective_entry_exit_code=code, public_wrapper_exit_code=public_code,
                              source_and_input_unchanged=source_ok, saved_factory_calls=len(factory_calls),
                              previous_actual1000_return_exactly_reused=full_tape, actual_new_MC_RNG_draws=0, independent_scientific_PASS=False)), flush=True)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
