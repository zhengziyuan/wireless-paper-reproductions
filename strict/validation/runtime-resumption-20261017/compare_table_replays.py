"""Compare actual independent Python/MATLAB numeric-table replay outputs."""
import argparse
import hashlib
import json
from pathlib import Path


def compare(python, matlab):
    a, b = [json.loads(path.read_text(encoding='utf-8-sig')) for path in (python, matlab)]
    assert b['execution_engine'] == 'MATLAB_native_jsondecode_parameter_replay'
    records = []
    def index(data):
        rows = {(row['paper'], row['parameter_id']): row for row in data['rows']}
        assert len(rows) == len(data['rows']) == 36
        return rows
    left, right = index(a), index(b)
    assert left.keys() == right.keys()
    for key in sorted(left):
        x, y = left[key], right[key]
        assert x['source_line'] == y['source_line']
        assert x['has_numeric_parameter_binding'] == y['has_numeric_parameter_binding']
        assert x['machine_bindings_pass'] is y['machine_bindings_pass'] is True
        checks = lambda row: {c['key']: (c['expected'], c['observed'], c['passed']) for c in row['checks']}
        assert checks(x) == checks(y)
        assert all(expected == observed and passed is True for expected, observed, passed in checks(x).values())
        records.append({'paper': key[0], 'parameter_id': key[1], 'numeric': x['has_numeric_parameter_binding'],
                        'both_language_values_match': True})
    assert sum(row['numeric'] for row in records) == 34
    return {'scope': 'two-source-parameter-table dual-language metadata replay', 'matched_rows': 36,
            'matched_numeric_rows': 34, 'unverified_external_pattern_rows': 2,
            'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (python, matlab)},
            'numeric_parameter_replay_passed': True, 'full_figure_or_physical_or_publisher_equivalence_pass': False,
            'rows': records}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', type=Path, required=True)
    parser.add_argument('--matlab', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.python, args.matlab)
    if args.output.exists():
        raise ValueError('Preserve earlier comparison; select a fresh output')
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('matched_rows', 'matched_numeric_rows', 'numeric_parameter_replay_passed')}))
