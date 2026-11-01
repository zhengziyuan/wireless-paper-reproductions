"""Prepare missing native original Fig3 slots with exact serial RNG jump inputs.

The existing frozen native scientific engine is used without byte edits.
Original start377 is reused with its actual interval binding and full receipt.
"""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(repository, output, reuse):
    if output.exists():
        raise FileExistsError('Preserve prior native inputs/results')
    base = repository/'strict/validation/sensing-same-cone-v5-components-v1'
    package = base/'scientific-source-v5'; settings_path = package/'settings_corrected.json'
    settings = json.loads(settings_path.read_bytes()); binding_path = base/'native-v5-expected-binding.json'
    binding = json.loads(binding_path.read_bytes())
    for entry in binding['entries']:
        if sha(base/entry['relative_path']) != entry['sha256']:
            raise ValueError('Frozen original source/input differs')
    if (settings['number_of_starts'], settings['outer_iterations'], settings['rcg_max_iterations']) != (6000, 30, 4000):
        raise ValueError('All original6000/30/4000 budgets required')
    if settings['initialization']['seed'] != 241219071 or settings['line_search']['initial_step'] != 1:
        raise ValueError('Retain original initialization and step control')
    raw = reuse/'actual-v5-cold-start0377-full30-matlab.json'
    receipt_path = reuse/'actual-v5-cold-start0377-full30-matlab-binding.json'
    receipt = json.loads(receipt_path.read_bytes()); prior = json.loads(raw.read_bytes())
    if not receipt['source_unchanged_during_run'] or receipt['output_sha256'] != sha(raw) or prior['settings'] != settings or receipt['binding_sha256'] != sha(binding_path):
        raise ValueError('Actual original native377 provenance differs')
    if not prior['solver_status']['convergence_verified'] or prior['start'] != 377:
        raise ValueError('Only the actual completed original377 receipt may be reused')
    rows = []; seed = settings['initialization']['seed']; state = seed; prime = 2147483647; draws = 881
    for n in range(1, 6001):
        before = state
        if before != seed*pow(16807, (n-1)*draws, prime) % prime:
            raise ValueError('Exact original serial RNG jump differs')
        for _ in range(draws):
            state = state*16807 % prime
        rows.append(dict(original_start=n, initial_rng_before=before, initial_rng_after=state))
    if (rows[376]['initial_rng_before'], rows[376]['initial_rng_after']) != (receipt['initial_rng_before'], receipt['initial_rng_after']):
        raise ValueError('Exact serial RNG stream differs from the actual native377 binding')
    output.mkdir(parents=True)
    (output/'original-settings.json').write_bytes(settings_path.read_bytes())
    plan = dict(scope='New missing native Fig3 population, original6000 slots/30 outer/4000 inner; supplied corrected-paper branch',
        repository=str(repository), frozen_binding_base=str(base), frozen_binding=str(binding_path),
        frozen_binding_sha256=sha(binding_path), scientific_package=str(package),
        original_settings_sha256=sha(settings_path), engine_sha256=sha(package/'mis_sensing_strict_engine.m'),
        wrapper_sha256=sha(Path(__file__).with_name('run_native_population.m')),
        expected_starts=6000, missing_new_optimizer_starts=5999, reused_original_starts=[377],
        initializer_draws_per_start=draws, original_seed=seed,
        initializer_jump_proof='Every before-state equals seed*16807^((start-1)*881) mod2147483647 and all serial after-states are checked. Each native multiply is below2^53 and therefore exact binary64 integer arithmetic.',
        maximum_initializer_integer_product=(prime-1)*16807, exact_binary64_integer_limit=2**53,
        transport_note='For a missing original slot n, the unchanged full-start:fig3:1 dispatcher receives the exact before-state seed of original slot n. No physical variable, control, sampled phase or schedule changes. The raw dispatcher index remains1 and original slot identity stays in its separate receipt.',
        reused_case=dict(original_start=377, file=str(raw), sha256=sha(raw),
            binding_file=str(receipt_path), binding_sha256=sha(receipt_path), original_dispatcher_start=377),
        original_input_stream_and_all_budgets_preserved=True, complete_native_execution_or_convergence_or_reference_pass=False,
        cases=rows)
    (output/'native-population-plan.json').write_text(json.dumps(plan, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(original_slots=6000, new_missing_optimizer_slots=5999, reused377=True,
        all6000_rng_jumps_checked=True, plan_sha256=sha(output/'native-population-plan.json'))))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('repository', 'output-dir', 'reuse-native377'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args(); prepare(a.repository, a.output_dir, a.reuse_native377)
