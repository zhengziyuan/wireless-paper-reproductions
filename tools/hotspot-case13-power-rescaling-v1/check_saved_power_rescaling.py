"""Conditional exact-arithmetic consequence of published Case 13 records.

No channel, optimizer or simulation is rerun; this reads small saved evidence.
"""
import argparse
from fractions import Fraction as F
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parent.parent


def load(path, cap):
    with path.open('rb') as f:
        data = f.read(cap + 1)
    if len(data) > cap:
        raise ValueError('input exceeds cap')
    return json.loads(data)


def rational(x):
    a, b = int(x['numerator']), int(x['denominator'])
    if b <= 0:
        raise ValueError('nonpositive rational denominator')
    return F(a, b)


def word(x):
    if type(x) not in (int, float) or not math.isfinite(x):
        raise ValueError('nonfinite parameter')
    return struct.pack('<d', float(x))


def q(x):
    word(x)
    return F.from_float(float(x))


def encoded(x):
    return {'numerator': str(x.numerator), 'denominator': str(x.denominator),
            'approx': float(x)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--qos-result', type=Path, default=ROOT / 'hotspot-case13-evidence-v1' / 'recorded_exact_qos_result.json')
    ap.add_argument('--qt-result', type=Path, default=ROOT / 'hotspot-case13-qt-parameter-evidence-v1' / 'recorded_qt_parameters.json')
    ap.add_argument('--final-parameters', type=Path, default=ROOT / 'hotspot-case13-evidence-v1' / 'final_parameters_projection.json')
    a = ap.parse_args()
    qos, qt, final = load(a.qos_result, 131072), load(a.qt_result, 16384), load(a.final_parameters, 16384)
    if (qos['schema'] != 'CASE13_EIGHT_AO_EXACT_SAVED_QOS_V1' or len(qos['records']) != 8 or
            qt['schema'] != 'CASE13_QT_BEGIN_PARAMETERS_EIGHT_WINDOWS_V1' or len(qt['events']) != 8 or
            final['schema'] != 'CASE13_AO_FINAL_PARAMETERS_IDENTITY_V1' or len(final['events']) != 2):
        raise ValueError('unexpected QoS record')
    matches = [r for r in qos['records'] if r['ordinal'] == 1327964 and r['start_id'] == 1]
    if len(matches) != 1:
        raise ValueError('case event identity')
    rec = matches[0]
    ev = [x for x in qt['events'] if x['start_id'] == 1 and x['ordinal'] == 1327965 and x['qt_id'] == 725]
    fr = [x for x in final['events'] if x['ordinal'] == 1328005 and x['context']['start_id'] == 1]
    if len(ev) != 1 or len(fr) != 1:
        raise ValueError('QT or final identity')
    ctx = fr[0]['context']
    if any(ctx[k] != v for k, v in {'case_id':13, 'geometry_id':12013, 'U':1, 'beta':20, 'scheme':'AO'}.items()):
        raise ValueError('case context')
    pars = ev[0]['parameters']
    fields = fr[0]['fields']
    if any(ev[0]['bitwise_equal_to_saved_final'].get(k) is not True for k in ('noise', 'power', 'target')):
        raise ValueError('QT/final comparison flags')
    for k, size in (('noise', 1), ('power', 1), ('target', 15)):
        if (fields[k]['shape'] != [size, 1] or fields[k]['order'] != 'MATLAB_column_major' or
                len(pars[k]) != size or len(fields[k]['real']) != size):
            raise ValueError('parameter dimensions')
        if [word(v) for v in pars[k]] != [word(v) for v in fields[k]['real']]:
            raise ValueError('QT/final binary64 mismatch')
    power, noise = q(pars['power'][0]), q(pars['noise'][0])
    targets = list(map(q, pars['target']))
    margin = rational(rec['power_margin'])
    if power <= 0 or noise <= 0 or margin >= 0 or rec['power_within_exact_bound'] is not False:
        raise ValueError('not the identified over-power case')
    actual_power = power - margin
    alpha_sq = power / actual_power
    if not 0 < alpha_sq < 1:
        raise ValueError('scale')
    qos_rows = rec['qos']
    if len(qos_rows) != 15 or [x['user_one_based'] for x in qos_rows] != list(range(2,17)):
        raise ValueError('QoS user order')
    result_rows = []
    for k, row in enumerate(qos_rows):
        record = {'user_one_based': k+2}
        if targets[k] < 0:
            raise ValueError('negative target')
        for key in ('moments', 'saved_Psi'):
            before = rational(row[key+'_margin'])
            if before <= 0 or row[key+'_positive'] is not True or row[key+'_zero'] is not False:
                raise ValueError('saved margin not strictly positive')
            # desired' - tau*(interference'+noise) = alpha^2*m - (1-alpha^2)*tau*noise.
            after = alpha_sq * before - (1-alpha_sq) * targets[k] * noise
            record[key+'_scaled_margin'] = encoded(after)
            record[key+'_scaled_positive'] = after > 0
        result_rows.append(record)
    result = {'schema':'CASE13_SAVED_POWER_RESCALING_EXISTENCE_V1',
              'source_event_ordinal':rec['ordinal'], 'source_start_id':rec['start_id'],
              'matched_qt_begin_ordinal':ev[0]['ordinal'], 'matched_final_ordinal':fr[0]['ordinal'],
              'noise':encoded(noise), 'power_limit':encoded(power), 'saved_power_excess':encoded(-margin),
              'scale_squared':encoded(alpha_sq), 'post_scaling_power_equals_limit':True,
              'post_scaling_margins':result_rows,
              'all_scaled_margins_positive':all(r['moments_scaled_positive'] and r['saved_Psi_scaled_positive'] for r in result_rows),
              'smallest_moments_margin':encoded(min(rational(x['moments_scaled_margin']) for x in result_rows)),
              'smallest_saved_Psi_margin':encoded(min(rational(x['saved_Psi_scaled_margin']) for x in result_rows)),
              'assumptions':['The existing QoS computation asserted positive original interference denominators for both matrix representations.',
                             'Scaling is an exact real mathematical construction, not a stored binary64 beam or optimizer iterate.',
                             'Historical input identity and atomic event provenance were not authenticated.'],
              'not_proven':['unit-modulus feasibility of stored phase','actual rounded implementation feasibility','optimization convergence','MATLAB agreement','published-figure agreement','full paper reproduction']}
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
