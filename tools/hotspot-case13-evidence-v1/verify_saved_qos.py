"""Recompute the conditional Case 13 saved-point audit from small projections.

This reads local files and writes only to stdout. It does not run an optimizer or
authenticate the historical trajectory, its physical units, or its source.
"""
import argparse
import importlib.util
import json
from pathlib import Path


def read_json(path, maximum):
    with path.open('rb') as stream:
        data = stream.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError('input exceeds the bounded size: ' + str(path))
    return json.loads(data.decode('utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--expected', type=Path,
                        help='optional recorded exact result JSON to compare')
    args = parser.parse_args()
    module_path = (Path(__file__).resolve().parent.parent / 'hotspot-projector-memo-v1'
                   / 'case13_eight_ao_exact_qos_prepared_v1.py')
    spec = importlib.util.spec_from_file_location('_case13_exact_saved_qos', module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Explicit opt-in for this standalone, read-only audit; it is not the
    # external process/storage guard used for the original execution.
    module.REAL_SCIENCE_ENABLED = True
    result = module.compute(
        read_json(args.inputs / 'moment_projection.json', 65536),
        read_json(args.inputs / 'ao_projection.json', 262144),
        read_json(args.inputs / 'first_ao_projection.json', 65536),
        read_json(args.inputs / 'final_parameters_projection.json', 16384),
    )
    # These fields describe the original guarded run, not the portable replay.
    result.pop('saved_inputs_held_during_task', None)
    result.pop('saved_inputs_historical_content_freshly_authenticated', None)
    if args.expected:
        expected = read_json(args.expected, 131072)
        expected.pop('saved_inputs_held_during_task', None)
        expected.pop('saved_inputs_historical_content_freshly_authenticated', None)
        if result != expected:
            raise SystemExit('Result differs from the recorded exact evidence.')
    print(json.dumps(result, separators=(',', ':'), allow_nan=False))


if __name__ == '__main__':
    main()
