"""One immutable full-axis bank case: exact Eq13/39 search, original1000 evaluation.

This is a new explicitly selected statistical reconstruction. Original MA is
reused under exact readset guards or run once per missing geometry at unchanged
budgets. FPA aggregates are exactly reused, without invented original histories.
No old MC tape is modified and no historical author criterion is claimed.
"""
from __future__ import annotations
from pathlib import Path
import argparse, copy, hashlib, importlib, json, os, pickle, sys
from bounded_exact_statistical_search_v1 import (HostError, ResourcePause, atomic,
    atomic_bytes, encode, sha, same_binding, search, witnessed_model_class,
    fraction_pair, actual_model_identity)


def check_pins(pins):
    actual = {p: sha(Path(p).read_bytes()) for p in pins}
    if actual != pins:
        raise HostError('Pinned implementation/configuration changed')
    return actual


def load_case(bank, filename, overlay):
    bank = Path(bank).resolve()
    if bank != Path(overlay['bank']).resolve() or Path(filename).name != filename:
        raise HostError('Wrong bank or non-leaf input filename')
    old_config_bytes = (bank / 'run_config.json').read_bytes()
    manifest_bytes = (bank / 'manifest.json').read_bytes()
    if (sha(old_config_bytes) != overlay['original_configuration_SHA256']
        or sha(manifest_bytes) != overlay['manifest_SHA256']):
        raise HostError('Original immutable full-axis metadata differs')
    manifest = json.loads(manifest_bytes)
    if (manifest['expected_jobs'] != overlay['expected_jobs']
        or not manifest['input_bank_complete'] or manifest['realizations_per_case'] != 100
        or manifest['nlos_per_geometry'] != 1000):
        raise HostError('Incomplete original 100x1000 bank')
    expected_pairs = [(i, g) for i in range(len(overlay['D_axis'])) for g in range(100)]
    if [(v['case_index'], v['realization']) for v in manifest['files']] != expected_pairs:
        raise HostError('Full original D/geometry manifest order differs')
    rows = [v for v in manifest['files'] if v['filename'] == filename]
    if len(rows) != 1:
        raise HostError('Input is not one unique full-axis manifest slot')
    row = rows[0]
    raw = (bank / 'jobs' / filename).read_bytes()
    # Original input identity remains the original bank/config byte contract.
    old_fingerprint = hashlib.sha256(b'strict-v1\0' + old_config_bytes + b'\0' + raw).hexdigest()
    if old_fingerprint != row['input_fingerprint']:
        raise HostError('Actual selected job differs from its original fingerprint')
    job = json.loads(raw)
    cfg_raw = Path(overlay['execution_configuration']).read_bytes()
    if sha(cfg_raw) != overlay['execution_configuration_SHA256']:
        raise HostError('New explicit target overlay changed')
    cfg = json.loads(cfg_raw)
    old_cfg = json.loads(old_config_bytes)
    inverse = copy.deepcopy(cfg)
    inverse['brute_force_objective'] = old_cfg['brute_force_objective']
    inverse['configuration_scope'] = old_cfg['configuration_scope']
    inverse.pop('user_selected_statistical_reconstruction', None)
    if inverse != old_cfg:
        raise HostError('Overlay changed an algorithm budget, seed or physical control')
    if (cfg['brute_force_objective'] != 'paper_statistical_design_objective'
        or cfg['geometry_realizations'] != 100 or cfg['nlos_realizations_per_geometry'] != 1000
        or job['figure'] != overlay['figure'] or job['N'] != overlay['N']
        or job['M'] != overlay['M'] or job['kappa'] != 100 or job['power'] != 1
        or job['point'] != overlay['D_axis'][row['case_index']]
        or job['brute_force_D'] != job['point'] or job['realization'] != row['realization']
        or job['region_lower'] != overlay['region_lower']
        or job['region_upper'] != overlay['region_upper']):
        raise HostError('Original full-axis case scope differs')
    return job, cfg, raw, cfg_raw, row


def execute(args):
    plan_raw = args.plan.read_bytes(); plan = json.loads(plan_raw)
    overlay_raw = args.overlay.read_bytes(); overlay = json.loads(overlay_raw)
    admission_raw = args.admission.read_bytes(); admission = json.loads(admission_raw)
    if (not args.execute or admission.get('root_admitted_statistical_grid_fixed1000') is not True
        or admission.get('plan_SHA256') != sha(plan_raw)
        or admission.get('overlay_SHA256') != sha(overlay_raw)
        or admission.get('filename') != args.filename
        or Path(admission.get('output_dir', '')).resolve() != args.output_dir.resolve()):
        raise HostError('Root admission for this exact missing statistical point required')
    if str(args.overlay.resolve()) not in plan['overlay_SHA256'] or plan['overlay_SHA256'][str(args.overlay.resolve())] != sha(overlay_raw):
        raise HostError('Overlay is outside the reviewed full-axis plan')
    before = check_pins(plan['source_pins'])
    job, config, raw, config_raw, manifest_row = load_case(args.bank, args.filename, overlay)
    output = args.output_dir.resolve(); bank = args.bank.resolve()
    if bank == output or bank in output.parents or output in bank.parents:
        raise HostError('Output must be separate from the immutable bank')
    source = Path(plan['original_python_source_root']).resolve()
    sys.path.insert(0, str(source))
    original = importlib.import_module('run'); core = importlib.import_module('core')
    for module in (original, core):
        if Path(module.__file__).resolve().parent != source:
            raise HostError('Wrong original physical/evaluation module')
    sys.path.insert(0, str(Path(plan['exact_source_root']).resolve()))
    exact = importlib.import_module('statistical_grid_exact_v10')
    if Path(exact.__file__).resolve().parent != Path(plan['exact_source_root']).resolve():
        raise HostError('Wrong frozen exact statistical solver')
    # Reuse only the typed call-tape host. No old MC search state is read.
    sys.path.insert(0, str(Path(plan['original_call_tape_host']).parent.resolve()))
    tape_module = importlib.import_module(Path(plan['original_call_tape_host']).stem)
    c, _ = original.scenario(config, job['N'], job['M'], job['kappa'], job['power'], job['A'], job['geometry'])
    c['region_lower'], c['region_upper'] = job['region_lower'], job['region_upper']
    import numpy as np
    nlos = np.asarray(job['nlos_re']) + 1j * np.asarray(job['nlos_im'])
    if nlos.shape != (1000, job['N'], job['M']) or not np.isfinite(nlos).all():
        raise HostError('Original complete finite1000 channel operands required')
    import platform
    from importlib import metadata as runtime_metadata
    runtime = dict(Python=platform.python_version(), NumPy=np.__version__,
                   SciPy=runtime_metadata.version('scipy'),
                   Python_executable=sys.executable, NumPy_module=np.__file__)
    binding = dict(runtime=runtime, schema='source-bound-statistical-grid-bank-overlay-v1',
                   plan_SHA256=sha(plan_raw), overlay_SHA256=sha(overlay_raw),
                   original_job_SHA256=sha(raw), original_input_fingerprint=manifest_row['input_fingerprint'],
                   original_manifest_SHA256=overlay['manifest_SHA256'],
                   execution_configuration_SHA256=sha(config_raw), original_source_pins=before,
                   exact_objectives={'MRT': 'Eq13', 'ZF': 'Eq39'},
                   canonical_permutation='ascending grid-row indices; no MC permutation selection',
                   historical_author_criterion_recovered=False)
    same_binding(output, binding)
    lock = output / 'active-case.json'
    with lock.open('xb') as handle:
        handle.write(encode(dict(PID=os.getpid(), admission_SHA256=sha(admission_raw))))
        handle.flush(); os.fsync(handle.fileno())
    result_path = output / 'actual-statistical-grid-and-final1000.json'
    closed = output / 'closed-result.json'
    if closed.exists():
        lock.unlink()
        receipt = json.loads(closed.read_bytes())
        if receipt['binding'] != binding or sha(result_path.read_bytes()) != receipt['result_SHA256']:
            raise HostError('Closed statistical result changed')
        print(encode(dict(reused_closed_result=True, **receipt['checks'])).decode())
        return 0 if receipt['scoped_numerical_pass'] else 1
    error = None; partial = {}; complete = False; baseline = None; baseline_receipt = None
    tape = tape_module.OriginalCallTape(output / 'original-final1000-call-tape', binding)
    try:
        from original_components_for_statistical_overlay_v1 import components
        cache = Path(admission['baseline_cache_root']).resolve()
        if bank == cache or bank in cache.parents or cache in bank.parents:
            raise HostError('Component cache must be outside the immutable input bank')
        baseline, baseline_receipt = components(job, config, plan,
            cache/('Fig%d-g%03d' % (job['figure'],job['realization'])), original, core, admission)
        for mode in ('MRT', 'ZF'):
            model = witnessed_model_class(exact.ExactStatisticalGrid)(c, job['N'], job['point'], mode)
            # This explicit all-pair guard confirms the exact prototype and
            # original float spacing define the same actual full D grid.
            float_mask = np.linalg.norm(model.grid[:, None] - model.grid[None, :], axis=2) >= c['minimum_distance']
            if not np.array_equal(float_mask, np.asarray(model.compatible, dtype=bool)):
                raise HostError('Actual grid spacing sets differ; no epsilon or subset repair')
            best, winner, state = search(model, output / ('grid-' + mode),
                dict(binding, mode=mode, actual_frozen_model=actual_model_identity(model)), batch_nodes=admission.get('batch_nodes', 256),
                batch_witness_bytes=admission.get('batch_witness_bytes', 1024*1024),
                max_certificate_bytes=admission.get('certificate_bytes_per_mode', 64*1024*1024),
                minimum_free_bytes=admission.get('minimum_free_bytes', 16*1024**3))
            positions = model.grid[list(winner)]
            evaluated = tape.call('original_core.instantaneous-' + mode, core.instantaneous,
                                   (positions, c, nlos, mode), {})
            if (len(evaluated['sample_sum_rates']) != 1000
                or not np.isfinite(evaluated['sample_sum_rates']).all()):
                raise HostError('Final original1000 evaluation incomplete/nonfinite; retained')
            partial[mode] = dict(positions=positions.tolist(), canonical_indices=list(winner),
                search=dict(D=job['point'], N=job['N'], mode=mode, complete=True,
                    objective_protocol='paper_statistical_design_objective',
                    actual_frozen_model=actual_model_identity(model),
                    exact_product=fraction_pair(best), objective=model.display_rate(best),
                    nodes=state['nodes'], evaluated_feasible_geometries=state['leaves'],
                    certified_pruned_subtrees=state['prunes'], infeasible_partial_branches=state['infeasible'],
                    certificate_bytes=state['certificate_bytes'], certificate_chain=state['certificate_chain'],
                    decision_digest=state['decision_digest'], elapsed_seconds=state['elapsed_seconds'],
                    standalone_certificate_replay_executed=False,
                    permutation_symmetry_reduction=True, float_argmax_equivalence_claimed=False),
                MC=evaluated)
            atomic(output / 'retained-completed-modes.json', partial)
        tape.ensure_consumed(); complete = True
    except BaseException as exc:
        error = dict(type=type(exc).__name__, message=str(exc),
                     safe_resource_pause=isinstance(exc, ResourcePause))
    finally:
        after = {p: sha(Path(p).read_bytes()) for p in before}
        checks = dict(all_two_statistical_grids_closed=complete,
                      all_final_evaluations_complete1000=complete,
                      original_five_components_returned=baseline_receipt is not None and baseline_receipt['all_original_five_components_present'],
                      original_five_component_checks=baseline_receipt is not None and baseline_receipt['scoped_original_return_checks'],
                      sources_unchanged=before == after,
                      full_axis_or_full_paper_pass=False, original_reference_PASS=False,
                      dual_language_PASS=False)
        result = dict(schema='actual-selected-statistical-grid-plus-original1000-v1',
                      binding=binding, job_metadata={k: job[k] for k in ('figure','point','N','M','realization')},
                      metrics={'brute_force': partial, 'schemes': baseline['schemes'] if baseline else {}}, checks=checks,
                      original_five_component_record=baseline,
                      original_five_component_closure=baseline_receipt,
                      host_error=error, source_before=before, source_after=after,
                      baseline_components_scope='source-bound original components, exact relevant-input projection; no fabricated FPA per-call history',
                      historical_author_search_criterion_recovered=False)
        atomic(result_path, result)
        success = complete and error is None and before == after and checks['original_five_component_checks']
        if complete or (error and error['type'] == 'OriginalScientificFailure'):
            atomic(closed, dict(binding=binding, result_SHA256=sha(result_path.read_bytes()),
                                scoped_numerical_pass=success, checks=checks, failure=error))
            lock.unlink()
        elif error and error['safe_resource_pause'] and before == after:
            # A safe committed pause may be resumed with the same source/input.
            # Uncertain/host errors retain the ownership marker for explicit recovery.
            lock.unlink()
    print(encode(dict(complete=complete, source_closed=before == after, error=error,
                      original_reference_PASS=False, paper_PASS=False)).decode(), flush=True)
    return 0 if success else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('plan', 'overlay', 'admission', 'bank', 'output-dir'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--filename', required=True)
    parser.add_argument('--execute', action='store_true')
    raise SystemExit(execute(parser.parse_args()))
