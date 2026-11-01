"""Compare ordered Case 13 saved-point hotspot rates, without optimization.

The only input is a small previously published projection.  Its historical
producer and complete-event provenance are not authenticated by this reader.
"""
import base64
import json
import math
from pathlib import Path
import struct


def read_vector(item, size):
    if item.get('shape') != [size, 1] or item.get('order') != 'MATLAB_column_major':
        raise ValueError('unexpected numeric shape or storage order')
    if item.get('encoding') != 'ieee754_binary64_little_endian_base64':
        raise ValueError('unexpected numeric encoding')
    if 'imag_base64' in item:
        raise ValueError('expected a real-valued numeric field')
    raw = base64.b64decode(item['real_base64'], validate=True)
    if len(raw) != 8 * size:
        raise ValueError('unexpected numeric byte count')
    values = struct.unpack('<' + 'd' * size, raw)
    if not all(math.isfinite(v) for v in values):
        raise ValueError('nonfinite value')
    return values


def main():
    source = (Path(__file__).resolve().parent.parent /
              'hotspot-case13-hu-evidence-v1' / 'q_rate_projection.json')
    with source.open('rb') as stream:
        raw = stream.read(65537)
    if len(raw) > 65536:
        raise ValueError('projection exceeds size limit')
    obj = json.loads(raw.decode('utf-8'))
    if obj.get('schema') != 'CASE13_HU_Q_RATE_PROJECTION_V1':
        raise ValueError('unexpected projection schema')
    events = obj['events']
    if len(events) != 8:
        raise ValueError('expected exactly eight saved events')
    if events[0]['ordinal'] != 1327666 or events[0]['context']['start_id'] != 0:
        raise ValueError('first rate is not bound to the expected saved event')
    first = obj['first_hu_sum_rate']
    if first.get('shape') != [1, 1] or first.get('order') != 'MATLAB_column_major' or len(first.get('real', [])) != 1:
        raise ValueError('unexpected first saved rate')
    if type(first['real'][0]) not in (int, float):
        raise ValueError('first saved rate is not numeric')
    rows = []
    for i, e in enumerate(events):
        context = e['context']
        expected_context = {'case_id': 13, 'U': 1, 'beta': 20, 'scheme': 'AO',
                            'MC_draw': 0, 'QT_id': 0, 'geometry_id': 12013,
                            'initializer_id': 0, 'phase_id': 0}
        if any(context.get(k) != v for k, v in expected_context.items()):
            raise ValueError('unexpected experiment context')
        gamma = read_vector(e['evaluation']['sinr'], 16)[0]
        if gamma < 0:
            raise ValueError('negative hotspot SINR')
        recomputed = math.log1p(gamma) / math.log(2.0)
        saved = float(first['real'][0]) if i == 0 else read_vector(e['evaluation']['hu_sum_rate'], 1)[0]
        if not math.isfinite(saved):
            raise ValueError('nonfinite saved rate')
        rows.append(dict(start_id=context['start_id'], ordinal=e['ordinal'],
                         saved_sinr=gamma, saved_rate=saved, recomputed_rate=recomputed,
                         recomputed_minus_saved=recomputed-saved))
    groups = {}
    for row in rows:
        groups.setdefault(row['start_id'], []).append(row)
    if sorted(groups) != [0, 1] or any(len(group) != 4 for group in groups.values()):
        raise ValueError('expected four saved points in each of starts 0 and 1')
    sequences = []
    for start, group in sorted(groups.items()):
        group.sort(key=lambda x: x['ordinal'])
        expected_ordinals = {0: [1327666, 1327713, 1327755, 1327778],
                             1: [1327876, 1327926, 1327964, 1328004]}
        if [x['ordinal'] for x in group] != expected_ordinals[start]:
            raise ValueError('unexpected saved-event identity or ordering')
        differences = [group[i+1]['recomputed_rate'] - group[i]['recomputed_rate'] for i in range(3)]
        sequences.append(dict(start_id=start, ordinals=[x['ordinal'] for x in group],
                              adjacent_recomputed_differences=differences,
                              all_strictly_increasing=all(d > 0 for d in differences)))
    result = dict(schema='case13_ordered_saved_objectives_v1', source=source.name,
                  method='log1p(saved hotspot SINR) / log(2), binary64',
                  records=rows, saved_event_sequences=sequences,
                  max_abs_rate_difference=max(abs(r['recomputed_minus_saved']) for r in rows),
                  limitations=['Only stored SINR and rate fields are compared; no channel or optimizer is recomputed.',
                               'Ordinal ordering does not prove intermediate iterations were saved.',
                               'Historical input authentication, atomic source snapshot, physical feasibility, convergence and reference agreement are not established.'])
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
