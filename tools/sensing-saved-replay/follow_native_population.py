"""Independently check each closed original native Fig3 slot without a solver.

Uses the exact actual MATLAB process object, complete saved final states and
separate recorded inner-stop decisions. Native failures remain failed.
"""
import argparse
import gzip
import json
from pathlib import Path
import sys
import time

import audit_population as ref
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'cooperative-stable-replay'))
from follow_native_validation import Producer


def write(path, value):
    for n in range(100):
        try:
            return ref.write(path, value)
        except PermissionError:
            if n == 99:
                raise
            time.sleep(.05)


def follow(bank, output, pid, creation):
    plan_path = bank/'native-population-plan.json'; plan_raw = plan_path.read_bytes(); plan = json.loads(plan_raw)
    settings = ref.read(bank/'original-settings.json')
    ref.require(ref.sha((bank/'original-settings.json').read_bytes()) == plan['original_settings_sha256'], 'Original native settings differ')
    response, indices, beta, noise, gap = ref.basis(settings, dict(ms1=[20, 20], ms2=[16, 16], Kphi=3, Ktheta=3))
    own = Path(__file__).read_bytes(); reference = Path(ref.__file__).read_bytes()
    binding = dict(plan_sha256=ref.sha(plan_raw), auditor_sha256=ref.sha(own),
        physical_reference_sha256=ref.sha(reference), producer_pid=pid, producer_creation_FILETIME=creation)
    if output.exists():
        ref.require(ref.read(output/'source-binding.json') == binding, 'Existing native audits use different source/input/producer')
    else:
        output.mkdir(parents=True); write(output/'source-binding.json', binding)
    owner = Producer(pid, creation); records = []; began = time.perf_counter()
    if not (output/'progress.json').exists():
        write(output/'progress.json', dict(expected=6000, checked=0, status='waiting_first_closed_native_slot',
            actual_producer_pid=pid, actual_producer_creation_FILETIME=creation,
            all6000_original_convergence_or_reference_pass=False))
    try:
        for n in range(1, 6001):
            result_path = bank/'starts'/f'start-{n:04d}-receipt.json'
            while not result_path.exists():
                if not owner.live():
                    write(output/'progress.json', dict(expected=6000, checked=len(records),
                        status='producer_closed_with_missing_slot', missing_original_start=n,
                        all6000_original_convergence_or_reference_pass=False))
                    return False
                time.sleep(5)
            raw = result_path.read_bytes(); receipt = json.loads(raw)
            ref.require(receipt['original_start'] == n and receipt['plan_sha256'] == binding['plan_sha256'], 'Native original slot differs')
            destination = output/f'start-{n:04d}-independent.json'
            if destination.exists():
                checked = ref.read(destination)
                ref.require(checked['native_receipt_sha256'] == ref.sha(raw), 'Cached native receipt differs')
            elif receipt['execution_error']:
                checked = dict(original_start=n, native_receipt_sha256=ref.sha(raw),
                    retained_native_execution_error=True, all_saved_state_checks_pass=False,
                    original_convergence_feasibility_pass=False)
                write(destination, checked)
            else:
                payload = bank/'starts'/receipt['payload_file']; compressed = payload.read_bytes()
                ref.require(ref.sha(compressed) == receipt['payload_gzip_sha256'], 'Native compressed return changed')
                decoded = gzip.decompress(compressed)
                ref.require(ref.sha(decoded) == receipt['payload_original_json_sha256'], 'Native numerical JSON bytes changed')
                doc = json.loads(decoded); current = doc['settings']; original = json.loads(json.dumps(current))
                original['initialization']['seed'] = plan['original_seed']
                ref.require(original == settings, 'Original native physical/solver control changed')
                identity = plan['cases'][n-1]
                expected_seed = plan['original_seed'] if receipt['reused_prior_actual_case'] else identity['initial_rng_before']
                ref.require(current['initialization']['seed'] == expected_seed and
                    receipt['initial_rng_before'] == identity['initial_rng_before'] and
                    receipt['initial_rng_after'] == identity['initial_rng_after'] and
                    doc['start'] == receipt['raw_dispatcher_start'], 'Exact original native initializer mapping differs')
                common = dict(state=doc['state'], metrics=doc['metrics'], summary=dict(solver_status=doc['solver_status']))
                numerical = ref.physical(common, response, indices, beta, noise, settings)
                history = doc['history']; history = [history] if isinstance(history, dict) else history
                ref.require(0 < len(history) <= 30 and doc['original_number_of_starts'] == 6000, 'Original native population/outer budget differs')
                stop = [h['stop']['projected_kkt_norm'] <= h['epsilon_used'] for h in history]
                caps = sum(h['stop']['reason'] == 'iteration_cap' for h in history); status = doc['solver_status']
                checks = dict(saved_native_physics_match=numerical['saved_physical_fields_match'],
                    original_KKT_residual_fields_match=numerical['saved_KKT_residual_fields_match'],
                    original_KKT_flag_reconfirmed=numerical['saved_KKT_boolean_reconfirmed'],
                    recorded_inner_stops_match=bool(all(stop)) == status['all_inner_tolerances_satisfied'] and
                        bool(stop[-1]) == status['final_inner_stationary'] and caps == status['inner_iteration_cap_exits'],
                    actual_native_source_interval_unchanged=receipt['source_unchanged_during_run'])
                checked = dict(original_start=n, actual_execution_language='matlab', native_receipt_sha256=ref.sha(raw),
                    original_native_JSON_sha256=ref.sha(decoded), actual_new_optimizer_executed=receipt['actual_new_optimizer_executed'],
                    reused_original_native_case=receipt['reused_prior_actual_case'], exact_original_serial_initializer_verified=True,
                    final_independent_metrics=numerical['metrics'], final_independent_KKT=numerical['certificate'],
                    maximum_saved_physical_field_error=numerical['maximum_physical_field_error'],
                    original_KKT_norm_error=numerical['stationarity_norm_error'], actual_recorded_inner_stops=len(history),
                    original_inner_cap_exits=caps, checks=checks, all_saved_state_checks_pass=all(checks.values()),
                    original_convergence_feasibility_pass=receipt['original_convergence_feasibility_verified'],
                    raw_original_inner_gradients_or_reference_or_complete6000_pass=False)
                write(destination, checked)
            records.append(checked)
            ref.require(plan_path.read_bytes() == plan_raw and Path(__file__).read_bytes() == own and Path(ref.__file__).read_bytes() == reference,
                        'Native audit source/input changed while following actual process')
            progress = dict(expected=6000, checked=len(records), passed_saved_state_fields=sum(r['all_saved_state_checks_pass'] for r in records),
                original_convergence_feasibility_pass_starts=sum(r['original_convergence_feasibility_pass'] for r in records),
                retained_failed_or_unverified_starts=sum(not r['original_convergence_feasibility_pass'] for r in records),
                last_original_start=n, status='complete' if n == 6000 else 'running',
                actual_response_MP80_MP100_maximum_difference=gap, elapsed_seconds=time.perf_counter()-began,
                all6000_saved_state_fields_verified=n == 6000 and all(r['all_saved_state_checks_pass'] for r in records),
                all6000_original_convergence_or_reference_pass=False)
            write(output/'progress.json', progress); print(json.dumps(progress), flush=True)
        return progress['all6000_saved_state_fields_verified']
    finally:
        owner.close()


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('bank', 'output-dir'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--producer-pid', type=int, required=True); p.add_argument('--producer-creation-filetime', type=int, required=True)
    a = p.parse_args()
    if not follow(a.bank, a.output_dir, a.producer_pid, a.producer_creation_filetime):
        raise SystemExit(1)
