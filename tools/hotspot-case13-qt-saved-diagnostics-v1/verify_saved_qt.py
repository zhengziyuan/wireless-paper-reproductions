"""Inspect already extracted case-13 QT diagnostics, without optimization."""
import gzip
import json
import math
from fractions import Fraction
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
ROOT = TOOLS.parent
STREAM = ROOT / 'validation/hotspot-case13-saved-stop-history-v1/recorded-stop-history.jsonl.gz'
PARAMS = TOOLS / 'hotspot-case13-evidence-v1/final_parameters_projection.json'
EXPECTED = {1327666: 0, 1327713: 0, 1327755: 0, 1327778: 0,
            1327876: 1, 1327926: 1, 1327964: 1, 1328004: 1}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def struct(node):
    require(node['tag'] == 'S' and node['header']['size'] == [1, 1] and
            len(node['values']) == 1, 'expected scalar struct')
    return node['values'][0]


def numeric(node, size):
    h = node['header']
    require(node['tag'] == 'N' and h['class'] == 'double' and h['isreal'] is True
            and h['size'] == [size, 1] and len(node['real']) == size, 'numeric shape')
    v = node['real']
    require(all(type(x) in (int, float) and math.isfinite(x) for x in v), 'numeric value')
    return [float(x) for x in v]


def scalar(node):
    return numeric(node, 1)[0]


def char(node):
    require(node['tag'] == 'H' and isinstance(node['value'], str), 'char')
    return node['value']


def frac(x):
    return Fraction.from_float(float(x))


def encoded(x):
    return {'numerator': str(x.numerator), 'denominator': str(x.denominator),
            'approx': float(x)}


def analyze(rows, params):
    require(params['schema'] == 'CASE13_AO_FINAL_PARAMETERS_IDENTITY_V1', 'parameter schema')
    by_start = {}
    for event in params['events']:
        ctx = event['context']
        start = ctx['start_id']
        require(start in (0, 1) and start not in by_start and ctx['case_id'] == 13
                and ctx['U'] == 1 and ctx['beta'] == 20 and ctx['scheme'] == 'AO'
                and ctx['geometry_id'] == 12013, 'parameter identity')
        fields = event['fields']
        require(fields['target']['shape'] == [15, 1] and len(fields['target']['real']) == 15
                and fields['power']['shape'] == [1, 1] and len(fields['power']['real']) == 1,
                'parameter shape')
        targets = fields['target']['real']
        power = fields['power']['real'][0]
        require(all(type(x) in (int, float) and math.isfinite(x) and x >= 0 for x in targets)
                and type(power) in (int, float) and math.isfinite(power) and power > 0,
                'parameter value')
        by_start[start] = (targets, float(power))
    require(set(by_start) == {0, 1}, 'parameter starts')
    out, seen = [], set()
    for row in rows:
        if row.get('action') != 'AO_iteration':
            continue
        ordinal, ctx = row['ordinal'], row['context']
        require(ordinal in EXPECTED and ordinal not in seen and ctx['start_id'] == EXPECTED[ordinal]
                and ctx['case_id'] == 13 and ctx['U'] == 1 and ctx['beta'] == 20
                and ctx['scheme'] == 'AO' and ctx['geometry_id'] == 12013, 'event identity')
        seen.add(ordinal)
        q = struct(row['fields']['QT_info'])
        diag = struct(q['solver_diagnostics'])
        before, after = struct(q['before']), struct(q['after'])
        status, diag_status = char(q['solver_status']), char(diag['status'])
        targets, limit = by_start[ctx['start_id']]
        bounds = numeric(q['qos_lower_bounds'], 15)
        gaps = [frac(b) - frac(t) for b, t in zip(bounds, targets)]
        aux = q['qos_auxiliaries_are_exact_vector_QT']
        require(aux['tag'] == 'L' and aux['header']['size'] == [1, 1]
                and len(aux['values']) == 1 and type(aux['values'][0]) is bool, 'aux flag')
        p_after = scalar(after['total_power'])
        qb = scalar(q['qt_bound_max_violation'])
        db = scalar(diag['qt_bound_max_violation'])
        violation = scalar(diag['constraint_max_relative_violation'])
        tolerance = scalar(diag['reported_solver_tolerance'])
        tightness = scalar(q['qt_tightness_error'])
        before_rate, after_rate = scalar(before['hu_sum_rate']), scalar(after['hu_sum_rate'])
        require(all(x >= 0 for x in (qb, db, violation, tolerance, tightness)), 'negative diagnostic')
        out.append({'ordinal': ordinal, 'start_id': ctx['start_id'],
                    'solver': char(diag['solver']), 'solver_status': status,
                    'diagnostic_status': diag_status, 'statuses_match': status == diag_status,
                    'reported_solver_tolerance': tolerance,
                    'reported_constraint_max_relative_violation': violation,
                    'reported_qt_bound_max_violation': qb,
                    'diagnostic_qt_bound_max_violation': db,
                    'reported_qt_tightness_error': tightness,
                    'reported_exact_vector_qt_auxiliary': aux['values'][0],
                    'lower_bound_count': 15,
                    'strictly_positive_qos_lower_bound_gaps': sum(x > 0 for x in gaps),
                    'minimum_qos_lower_bound_gap': encoded(min(gaps)),
                    'power_after': p_after, 'power_limit': limit,
                    'power_after_binary64_minus_limit': encoded(frac(p_after) - frac(limit)),
                    'hu_rate_before': before_rate, 'hu_rate_after': after_rate,
                    'saved_hu_rate_difference': encoded(frac(after_rate) - frac(before_rate))})
    require(seen == set(EXPECTED), 'missing expected event')
    out.sort(key=lambda x: x['ordinal'])
    return {'schema': 'CASE13_SAVED_QT_DIAGNOSTICS_V1', 'records': out,
            'historical_content_authenticated': False, 'complete_qt_inner_solves_proven': False,
            'independent_physical_feasibility_proven': False, 'full_paper_pass': False}


def main():
    require(STREAM.stat().st_size <= 262144 and PARAMS.stat().st_size <= 16384, 'input size')
    with gzip.open(STREAM, 'rb') as f:
        raw = f.read(524289)
    require(len(raw) <= 524288 and raw.endswith(b'\n'), 'stream bound or partial line')
    rows = [json.loads(line) for line in raw.splitlines()]
    require(len(rows) == 28, 'event count')
    with PARAMS.open('rb') as f:
        params = json.load(f)
    print(json.dumps(analyze(rows, params), sort_keys=True, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
