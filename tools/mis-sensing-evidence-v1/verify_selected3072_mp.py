"""Replay the conditional start-3072 saved-state high-precision calculation.

This reads already-published small inputs and writes only to stdout. It does
not rerun optimization, authenticate historical inputs, or certify an interval.
"""
import argparse
import json
import os
from pathlib import Path
import types


def read_json(path, limit):
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError('input exceeds the bounded size')
    return json.loads(data.decode('utf-8-sig'))


def load_module(path, name):
    with path.open('rb') as stream:
        source = stream.read(65537)
    if len(source) > 65536:
        raise ValueError('required module exceeds its bounded size')
    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = ''
    exec(compile(source, str(path), 'exec', dont_inherit=True), module.__dict__)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected', type=Path, help='optional recorded result to compare')
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    repo = here.parent.parent
    source = repo / 'strict/validation/mis-sensing-fig3-5-6-saved6000-20261019-v1'
    state = read_json(source / 'data/selected-fixed-final-state.json', 128 * 1024)
    field = read_json(source / 'evidence/actual-output-and-visual-review.json', 128 * 1024)
    os.environ['MPMATH_NOGMPY'] = '1'
    import mpmath
    if mpmath.__version__ != '1.4.1' or mpmath.libmp.BACKEND != 'python':
        raise SystemExit('Replay requires mpmath 1.4.1 with its pure Python backend.')
    host = load_module(here / 'selected3072_mp_host_prepared_v1.py', '_mis3072_host')
    kernel = load_module(here / 'selected_target_sinr_mp_prepared_v1.py', '_mis3072_kernel')
    report = host.evaluate(host.prepare(state['best'], field), kernel.target_sinrs)
    if args.expected:
        expected = read_json(args.expected, 64 * 1024)
        if any(key not in expected or expected[key] != value for key, value in report.items()):
            raise SystemExit('Result differs from the recorded conditional evidence.')
    print(json.dumps(report, ensure_ascii=True, allow_nan=False, separators=(',', ':')))


if __name__ == '__main__':
    main()
