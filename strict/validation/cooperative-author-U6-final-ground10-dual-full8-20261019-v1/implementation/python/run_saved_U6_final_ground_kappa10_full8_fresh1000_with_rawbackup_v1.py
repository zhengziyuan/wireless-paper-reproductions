"""One prepared ground-K10 full8: frozen algorithms, fresh original1000 tape.

The original canonical-U6 runner is imported unchanged. The only additional
hook installs the already validated raw-backup-first reversible MAT saver on
the recorder before any numerical action. Existing factory/MC tap/full8 calls
and their order remain in that original runner. There is no process controller.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def need(predicate, message):
    if not predicate:
        raise ValueError(message)


def load_exact(path, name, pins):
    path = Path(path).resolve()
    raw = path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == pins[str(path)], 'Frozen helper mismatch: '+str(path))
    need(name not in sys.modules, 'Fresh isolated module required')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--execute', action='store_true', required=True)
    args = parser.parse_args()
    need(sys.dont_write_bytecode and not sys.flags.optimize, 'Use -B with active assertions')
    plan_raw = args.plan.read_bytes()
    plan = json.loads(plan_raw)
    output = Path(plan['fresh_output_directory']).resolve()
    need(not output.exists(), 'No retry, resume or overwrite of an actual full8 directory')
    pins = {str(Path(path).resolve()): value for path, value in plan['source_and_input_pins'].items()}
    cfg_path = Path(plan['configuration']).resolve()
    cfg_raw = cfg_path.read_bytes()
    need(hashlib.sha256(cfg_raw).hexdigest() == pins[str(cfg_path)], 'Exact new ground-K configuration')
    cfg = json.loads(cfg_raw)
    variant = cfg['physical_input_variant']
    need(cfg['reported']['kappa_ground_db'] == 10.
         and variant['source_linear_beta_R'] == 1.
         and variant['selected_linear_beta_R'] == 10.,
         'Distinguish retained source beta_R1 from selected final-ground K10')
    construction_path = Path(plan['two_field_construction_receipt']).resolve()
    construction_raw = construction_path.read_bytes()
    need(hashlib.sha256(construction_raw).hexdigest() == pins[str(construction_path)],
         'Actual two-field construction receipt identity')
    construction = json.loads(construction_raw)
    need(construction['complete'] is True
         and construction['unchanged_nine_algorithm_arrays_and_two_limits_exact'] is True
         and set(construction['actual_changed_algorithm_fields']) == {'r_mean', 'r_var'}
         and construction['actual_new_optimizer_RNG_MC_MP_calls'] == 0,
         'Only the two declared ground-K fields may differ from retained working input')
    need(plan.get('MC_return_reuse_installer') is None
         and plan.get('previous_actual_MC_directory') is None,
         'Ground-K10 has a different moment input: old beta_R1 MC return cannot be reused')
    legacy = load_exact(plan['canonical_full8_runner'], '_groundK10_original_full8_runner', pins)
    transport = load_exact(plan['raw_backup_first_transport'], '_groundK10_raw_first_transport_v2', pins)
    original_loader = legacy.module_from_file
    public_path = Path(plan['public_full8_entry']).resolve()
    installed = []
    def routed_module_from_file(path, name):
        module = original_loader(path, name)
        if Path(path).resolve() == public_path:
            original_prepare = module.prepare_installation
            def prepare_with_raw_first(*pos, **kw):
                installation = original_prepare(*pos, **kw)
                need(not installed, 'One installation for this exact single-base full8')
                binding = transport.install_raw_backup_first_recorder_saver(installation['recorder'])
                installed.append(binding)
                legacy.fresh_json(output/'RAW_BACKUP_FIRST_REVERSIBLE_MAT_TRANSPORT_BOUND_V1.json', binding)
                return installation
            module.prepare_installation = prepare_with_raw_first
        return module
    legacy.module_from_file = routed_module_from_file
    # Original main reads this exact --plan/--execute CLI, installs its saved
    # factory before recorder capture, then the unchanged original1000 MC tap.
    code = legacy.main()
    need(type(code) is int, 'Preserve the original runner actual return code')
    if code == 0 and len(installed) != 1:
        code = 1
    legacy.fresh_json(output/'ACTUAL_GROUND_KAPPA10_FULL8_FRESH1000_AND_RAWFIRST_SCOPE_V1.json', dict(
        effective_entry_exit_code=code,
        inherited_original_runner_outcome='ACTUAL_CANONICAL_NATIVE_U6_FULL8_PYTHON_VARIANT_OUTCOME_V1.json',
        retained_source_working_linear_beta_R=1., selected_linear_beta_R=10.,
        selected_ground_kappa_R_dB=10., actual_raw_first_transport_installations=len(installed),
        original_full8_runner_source_unchanged=True,
        original_full8_optimizer_initialization_and_stopping_bodies_unchanged=True,
        complete_original_reconstruction_controls_preserved=True,
        MC_return_reuse=False, actual1000_passive_tape='actual-online-MC1000',
        MC_scope='Original configured1000 channel-moment validation calls, not a performance-optimization MC average or recovered authorpopulation.',
        source_variant='Saved source U6/J3/N16/M25/K1 geometry, enabled RU, final Fig4 groundK10, literal .01 INR, 50W each. Only r_mean/r_var changed from author working betaR1.',
        author_cached_W_random_phi_and_performance_MC_population_recovered=False,
        original_beta1_results_retained=True,
        earlier_ten_strict_crosslanguage_complex_component_failures_retained=True,
        new_independent_ownstate_QT_phase_MC_dual_reference_and_fullpaper_PASS=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
