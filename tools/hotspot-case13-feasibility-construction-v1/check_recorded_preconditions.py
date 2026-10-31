"""Check recorded premises for a continuous construction; do not recompute a matrix."""
import argparse
import base64
from fractions import Fraction
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent


def read(path, cap):
    with path.open('rb') as stream:
        content = stream.read(cap + 1)
    if len(content) > cap:
        raise ValueError('input too large')
    return json.loads(content)


def fraction(value):
    denominator = int(value['denominator'])
    if denominator <= 0:
        raise ValueError('invalid denominator')
    return Fraction(int(value['numerator']), denominator)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--qos-result', type=Path,
        default=TOOLS / 'hotspot-case13-evidence-v1' / 'recorded_exact_qos_result.json')
    parser.add_argument('--scaled-result', type=Path,
        default=TOOLS / 'hotspot-case13-power-rescaling-v1' / 'recorded_power_rescaling.json')
    parser.add_argument('--ao-projection', type=Path,
        default=TOOLS / 'hotspot-case13-evidence-v1' / 'ao_projection.json')
    args = parser.parse_args()
    old, scaled = read(args.qos_result, 131072), read(args.scaled_result, 32768)
    projection = read(args.ao_projection, 262144)
    require(old['schema'] == 'CASE13_EIGHT_AO_EXACT_SAVED_QOS_V1', 'QoS record schema')
    hits = [r for r in old['records'] if r['ordinal'] == 1327964 and r['start_id'] == 1]
    require(len(hits) == 1, 'original event identity')
    event = hits[0]
    require(projection['schema'] == 'CASE13_ALL_AO_IDENTITY_COMPACT_FIELDS_V1',
            'phase projection schema')
    phase_hits = [r for r in projection['events'] if r['ordinal'] == 1327964
                  and r['context']['start_id'] == 1]
    require(len(phase_hits) == 1 and phase_hits[0]['context']['case_id'] == 13,
            'phase event identity')
    phase = phase_hits[0]['fields']['phi']
    require(phase['shape'] == [1, 25] and phase['order'] == 'MATLAB_column_major'
            and phase['encoding'] == 'ieee754_binary64_little_endian_base64'
            and len(base64.b64decode(phase['real_base64'], validate=True)) == 200
            and len(base64.b64decode(phase['imag_base64'], validate=True)) == 200,
            'phase vector shape or encoding')
    require(scaled['schema'] == 'CASE13_SAVED_POWER_RESCALING_EXISTENCE_V1' and
            scaled['source_event_ordinal'] == 1327964 and scaled['source_start_id'] == 1,
            'scaled record identity')
    e = fraction(event['max_abs_unit_modulus_squared_error'])
    require(e == Fraction(14344986692602049, 40564819207303340847894502572032)
            and 0 <= e < 1, 'recorded phase error bound')
    limit, noise = fraction(scaled['power_limit']), fraction(scaled['noise'])
    excess, t = -fraction(event['power_margin']), fraction(scaled['scale_squared'])
    require(limit == 100 and noise > 0 and excess > 0 and
            excess == fraction(scaled['saved_power_excess']) and
            t == limit / (limit + excess) and 0 < t < 1, 'power scaling')
    rows = scaled['post_scaling_margins']
    require(len(rows) == 15 and [r['user_one_based'] for r in rows] == list(range(2, 17)),
            'NHU record identity')
    for row in rows:
        for key in ('moments', 'saved_Psi'):
            require(fraction(row[key + '_scaled_margin']) > 0 and
                    row[key + '_scaled_positive'] is True, 'nonpositive recorded margin')
    print(json.dumps({'event_ordinal': 1327964,
        'recorded_max_phase_squared_error_less_than_one': True,
        'recorded_phase_vector_elements': 25,
        'strictly_positive_recorded_scaled_margins': 30,
        'scope': 'recorded premises only; no matrix, optimizer or rounded candidate recomputed',
        'publisher_full_problem_independently_checked': False,
        'paper_or_full_science_pass': False}, sort_keys=True))


if __name__ == '__main__':
    main()
