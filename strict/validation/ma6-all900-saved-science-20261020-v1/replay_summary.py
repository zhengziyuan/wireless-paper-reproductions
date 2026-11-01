"""Replay all 900 delivered scientific summaries, not the underlying physics."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

HISTORY_KEYS = ('shared_prefix_position_max_abs_difference', 'shared_prefix_objective_max_abs_difference', 'terminal_position_max_abs_difference', 'terminal_design_objective_difference_python_minus_matlab')
SCHEME_KEYS = ('saved_sample_rate_difference_max_abs', 'independent_same_evaluator_at_own_states_sample_difference_max_abs', 'independent_mean_difference_python_minus_matlab', 'evaluator_residual_after_own_state_difference_max_abs')
SCHEMES = ('MA-MRT', 'MA-ZF', 'FPA-MRT', 'FPA-ZF', 'FPA-OPT')
STAGES = ('complete_saved_state_extension', 'whole_original_history_math', 'whole_original_terminal1000_math', 'whole_original_coordinate_certificate_math')

def require(condition, message):
    if not condition:
        raise ValueError(message)

def aggregate(records):
    expected = {f'case-{p:03d}-mc-{g:03d}' for p in range(9) for g in range(100)}
    seen = set()
    inputs = set()
    counts = dict(math_pass=0, same_paths=0, same_terminal_samples=0, mean_within_1e_9=0, evaluator_residual_within_2e_7=0)
    hm = {m: {k: 0.0 for k in HISTORY_KEYS} for m in ('mrt', 'zf')}
    sm = {m: {k: 0.0 for k in SCHEME_KEYS} for m in SCHEMES}
    exceptions = []
    for record in records:
        case = record['case']
        require(case in expected and case not in seen, 'Unexpected or duplicate case')
        seen.add(case)
        require(record['input_fingerprint'] not in inputs, 'Duplicate input fingerprint')
        inputs.add(record['input_fingerprint'])
        require(record['figure'] == 6 and record['language'] == 'matlab', 'Wrong scientific population')
        require(set(record['gates']) == set(STAGES), 'Four original mathematical stages required')
        mp = (record['complete_native_case_independent_math_passed'] is True and all(record['gates'].values()) and not record['failures'] and record['source_and_case_inputs_unchanged'] is True)
        comp = record['actual_independent_own_state_dual_language_comparison']
        require(set(comp['histories']) == {'mrt', 'zf'} and set(comp['schemes']) == set(SCHEMES), 'Missing method or history')
        hp = True
        for mode, values in hm.items():
            h = comp['histories'][mode]
            # Recalculate the path gate from the saved counts and numerical maxima.
            path = (h['python_position_count'] == h['matlab_position_count'] and h['shared_prefix_position_max_abs_difference'] <= 1e-9 and h['shared_prefix_objective_max_abs_difference'] <= 1e-9)
            require(path == h['same_path_within_fixed_comparison_gates'], 'History flag disagrees with numeric summaries')
            hp = hp and path
            for key in values:
                value = float(h[key])
                require(math.isfinite(value), 'Nonfinite history difference')
                values[key] = max(values[key], abs(value))
        sp = me = ep = True
        for mode, values in sm.items():
            s = comp['schemes'][mode]
            same = s['saved_sample_rate_difference_max_abs'] < 1e-7
            require(same == s['same_terminal_samples_within_fixed_sample_comparison_gate'], 'Sample flag disagrees with numeric summaries')
            sp = sp and same
            me = me and abs(s['independent_mean_difference_python_minus_matlab']) < 1e-9
            ep = ep and abs(s['evaluator_residual_after_own_state_difference_max_abs']) < 2e-7
            for key in values:
                value = float(s[key])
                require(math.isfinite(value), 'Nonfinite scheme difference')
                values[key] = max(values[key], abs(value))
        for key, value in zip(counts, (mp, hp, sp, me, ep)):
            counts[key] += int(value)
        if not all((mp, hp, sp, me, ep)):
            exceptions.append(dict(case=case, math_pass=mp, same_paths=hp, same_terminal_samples=sp, independent_means_within_1e_9=me, comparison=comp))
    require(seen == expected, 'All 900 cases, including exceptions, are required')
    return dict(expected_cases=900, checked_cases=len(seen), counts=counts, history_maximum_absolute_differences=hm, scheme_maximum_absolute_differences=sm, exceptions=exceptions, original_reference_agreement=False, full_paper_pass=False, new_optimizer_or_RNG_calls=0)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Keep previous replay evidence')
    manifest = json.loads((args.packet/'manifest.json').read_bytes())
    for name, spec in manifest['files'].items():
        data = (args.packet/name).read_bytes()
        require(len(data) == spec['bytes'] and hashlib.sha256(data).hexdigest() == spec['sha256'], 'Packet differs: '+name)
    records = json.loads(gzip.decompress((args.packet/'all900-scientific-summaries.json.gz').read_bytes()))
    result = aggregate(records)
    reference = json.loads((args.packet/'actual-aggregate.json').read_bytes())
    require(result == reference, 'Published scientific aggregation does not replay')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as f:
        json.dump(dict(all900_delivered_summary_aggregation_replayed=True, counts=result['counts'], retained_trajectory_exception_cases=[r['case'] for r in result['exceptions']], underlying_all900_physics_rerun_by_this_command=False, optimizer_or_RNG_calls=0), f, indent=2, allow_nan=False)
    print(json.dumps(dict(output=str(args.output), counts=result['counts'], exceptions=len(result['exceptions']))))

if __name__ == '__main__':
    main()
