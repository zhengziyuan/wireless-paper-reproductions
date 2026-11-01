"""Recompute a conditional saved-point Case 13 HU matrix and rate audit.

The projections share historical sources and do not authenticate them. This
standalone reader does not launch an optimizer or enforce a storage guard.
"""
import argparse
import json
from pathlib import Path
import types


def read_json(path, maximum):
    with path.open('rb') as stream:
        raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError('input exceeds size bound: ' + str(path))
    return json.loads(raw.decode('utf-8'))


def module(name, path):
    with path.open('rb') as stream:
        raw = stream.read(65537)
    if len(raw) > 65536:
        raise ValueError('source exceeds size bound: ' + str(path))
    value = types.ModuleType(name)
    value.__file__ = str(path)
    value.__package__ = ''
    exec(compile(raw, str(path), 'exec', dont_inherit=True), value.__dict__)
    value.REAL_SCIENCE_ENABLED = True
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected', type=Path, help='recorded result to compare')
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    prior = here.parent / 'hotspot-case13-evidence-v1'
    tools = here.parent / 'hotspot-projector-memo-v1'
    decoder = module('_case13_qos_decoder', tools / 'case13_eight_ao_exact_qos_prepared_v1.py')
    worker = module('_case13_hu_q', tools / 'case13_hu_q_check_prepared_v1.py')
    hu = read_json(here / 'hu_input_projection.json', 65536)
    extra = read_json(here / 'q_rate_projection.json', 131072)
    ao = read_json(prior / 'ao_projection.json', 262144)
    first = read_json(prior / 'first_ao_projection.json', 65536)
    final = read_json(prior / 'final_parameters_projection.json', 16384)
    if extra.get('schema') != 'CASE13_HU_Q_RATE_PROJECTION_V1':
        raise ValueError('unexpected supplementary projection schema')
    if len(ao['events']) != 8 or len(extra['events']) != 8 or len(ao['arrays']) != 1:
        raise ValueError('unexpected event or baseline array count')
    offset = len(ao['arrays'])
    ao['arrays'].extend(extra['arrays'])
    for event, addition in zip(ao['events'], extra['events']):
        if (event['ordinal'], event['context']) != (addition['ordinal'], addition['context']):
            raise ValueError('supplement does not match saved AO event')
        ref = addition['q_array_ref']
        if type(ref) is not int or ref < 0 or ref >= len(extra['arrays']):
            raise ValueError('invalid supplemental Q reference')
        event['fields']['Q'] = {'array_ref': offset + ref}
        event['fields']['evaluation'] = addition['evaluation']
    first['fields']['evaluation'] = {'hu_sum_rate': extra['first_hu_sum_rate']}
    result = worker.compute(hu, ao, first, final, decoder)
    # The original guard added this fact; portable replay makes no such claim.
    if args.expected:
        expected = read_json(args.expected, 131072)
        expected.pop('saved_inputs_held_during_task', None)
        result.pop('saved_inputs_held_during_task', None)
        if result != expected:
            raise SystemExit('Result differs from the recorded exact evidence.')
    print(json.dumps(result, separators=(',', ':'), allow_nan=False))


if __name__ == '__main__':
    main()
