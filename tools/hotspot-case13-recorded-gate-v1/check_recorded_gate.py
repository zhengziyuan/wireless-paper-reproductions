"""Conservatively apply an existing gate to already-published Case 13 fields.

No original trajectory, optimizer, propagation model or candidate budget is read.
"""
import gzip
import importlib.util
import json
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STOPS = ROOT / 'validation/hotspot-case13-saved-stop-history-v1/recorded-stop-history.jsonl.gz'
MC = ROOT / 'validation/hotspot-case13-final-mc-v1/recorded-projection.jsonl.gz'


def load(relative, name):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def gunzip(path, maximum):
    with gzip.open(path, 'rb') as stream:
        content = stream.read(maximum + 1)
    if len(content) > maximum:
        raise ValueError('bounded compressed evidence')
    return content


def bits(v):
    return struct.pack('<d', v)


def same_history(a, b):
    return len(a) == len(b) and all(bits(x) == bits(y) for x, y in zip(a, b))


def same_typed(a, b):
    """Compare complete typed JSON trees; dictionary key order is immaterial.

    MATLAB field order remains significant because the writer's header stores
    it as a list. Floats must be finite and bitwise equal, including signed
    zero. Strings that stand for nonfinite numeric values are rejected.
    """
    if type(a) is not type(b):
        return False
    if isinstance(a, float):
        return math.isfinite(a) and math.isfinite(b) and bits(a) == bits(b)
    if isinstance(a, list):
        return len(a) == len(b) and all(same_typed(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        if set(a) != set(b):
            return False
        if a.get('tag') == 'N':
            for key in ('real', 'imag'):
                if key in a and (not isinstance(a[key], list) or
                                 any(type(v) not in (int, float) or not math.isfinite(v)
                                     for v in a[key])):
                    return False
        return all(same_typed(a[k], b[k]) for k in a)
    return a == b


STOP_FIELDS = ('converged', 'termination', 'iterations', 'iteration_cap',
               'stop_rule', 'threshold', 'final_residual')


def same_stop(a, b):
    for key in STOP_FIELDS:
        if key not in a or key not in b or a[key] != b[key]:
            return False
    return all(bits(a[k]) == bits(b[k]) for k in
               ('iterations', 'iteration_cap', 'threshold', 'final_residual'))


def required(ok, message):
    if not ok:
        raise ValueError(message)


def make_report(rows, mc, c, gate):
    required(isinstance(rows, list) and len(rows) == 28, 'event count')
    expected = {(action, ordinal) for action, ordinals in c.EXPECTED.items() for ordinal in ordinals}
    keys = [(r.get('action'), r.get('ordinal')) for r in rows]
    required(len(set(keys)) == len(keys) and set(keys) == expected, 'event identity')
    # The prior reader checks case/geometry/U/beta and scheme/start against
    # its ordinal map. Reuse that validation for every associated event.
    for row in rows:
        c.inspect_event(row)
    required(mc.get('schema') == 'CASE13_FINAL_RESULT_BOUNDED_PROJECTION_V1' and
             mc.get('case', {}).get('U') == 1.0, 'case projection')
    schemes = {name: {'all_start_records': []} for name in ('NoRIS', 'TwoStage', 'AO')}
    associations = []
    for row in rows:
        if row['action'] != 'execute_final':
            continue
        decoded = c.inspect_event(row)
        name, sid, ordinal = decoded['scheme'], decoded['start_id'], decoded['ordinal']
        matches = [x for x in mc['schemes'][name]['recorded_starts'] if x['start_id'] == sid]
        required(len(matches) == 1 and matches[0].get('executed') is True, 'start identity')
        saved = matches[0]
        status = decoded['final_status_report']
        required(status.get('reported_converged') is saved['recorded_status']['converged'],
                 'reported status mismatch')
        raw_blocks = status['blocks']
        required(all(not b.get('inspection_status') for b in raw_blocks), 'unreadable stop')
        typed_cell = c.struct_one(row['fields']['status'])['blocks']
        required(typed_cell.get('tag') == 'C' and typed_cell.get('header', {}).get('class') == 'cell'
                 and isinstance(typed_cell.get('values'), list)
                 and len(typed_cell['values']) == len(raw_blocks), 'typed final blocks')
        typed_blocks = typed_cell['values']
        blocks = []
        for raw in raw_blocks:
            b = {k: raw[k] for k in STOP_FIELDS}
            for key in ('iterations', 'iteration_cap'):
                required(type(b[key]) in (int, float) and int(b[key]) == b[key], 'stop integer')
                b[key] = int(b[key])
            blocks.append(b)
        node = row['fields']['history']
        history = ({k: c.numeric(c.struct_one(node)[k])[0] for k in ('QT', 'phase')}
                   if name == 'TwoStage' else c.numeric(node)[0])
        rec = {'scheme': name, 'start_id': sid, 'executed': saved['executed'],
               'checks': saved['checks'], 'status': {'converged': status['reported_converged'],
                                                     'blocks': blocks}, 'history': history}
        if name in ('NoRIS', 'TwoStage'):
            q = [r for r in rows if r['action'] == 'QT_loop_end' and
                 r['context']['scheme'] == name and r['context']['start_id'] == sid and
                 r['ordinal'] < ordinal]
            required(len(q) == 1, 'QT event association')
            q_history = c.numeric(q[0]['fields']['history'])[0]
            required(same_typed(q[0]['fields']['stop'], typed_blocks[-1]) and
                     same_history(q_history, history if name == 'NoRIS' else history['QT']) and
                     same_stop(c.stop_fields(q[0]['fields']['stop']), blocks[-1]), 'QT mismatch')
        if name in ('AO', 'TwoStage'):
            ps = sorted([r for r in rows if r['action'] == 'phase_end' and
                         r['context']['scheme'] == name and r['context']['start_id'] == sid and
                         r['ordinal'] < ordinal], key=lambda r: r['ordinal'])
            required(len(ps) == (4 if name == 'AO' else 1), 'phase event association')
            hs = []
            for index, p in enumerate(ps):
                h = c.numeric(p['fields']['actual_history'])[0]
                required(same_typed(p['fields']['actual_stop'], typed_blocks[index]) and
                         same_stop(c.stop_fields(p['fields']['actual_stop']), blocks[index]),
                         'phase stop mismatch')
                if name == 'TwoStage':
                    required(same_history(h, history['phase']), 'two-stage history mismatch')
                else:
                    a = [r for r in rows if r['action'] == 'AO_iteration' and
                         r['context']['scheme'] == name and r['context']['start_id'] == sid and
                         r['ordinal'] == p['ordinal'] + 1]
                    required(len(a) == 1 and same_typed(p['fields']['actual_stop'], a[0]['fields']['phase_stop']) and
                             same_stop(c.stop_fields(a[0]['fields']['phase_stop']),
                                                        blocks[index]), 'AO phase-stop mismatch')
                    prefix = c.numeric(a[0]['fields']['history'])[0]
                    required(len(prefix) == index + 2 and same_history(prefix, history[:len(prefix)]),
                             'AO outer prefix mismatch')
                hs.append(h)
                associations.append({'scheme': name, 'start_id': sid,
                                     'phase_ordinal': p['ordinal'], 'final_ordinal': ordinal,
                                     'history_points': len(h),
                                     'complete_typed_stop_match_finite_binary64_bitwise': True})
            if name == 'AO':
                rec['phase_histories'] = hs
        schemes[name]['all_start_records'].append(rec)
    required(all(len(v['all_start_records']) == 2 for v in schemes.values()), 'start count')
    # The saved projection does not establish the gate's case.status field,
    # config authenticity, or complete trajectory capture. Do not invent them.
    result = gate.assess_case({'U': 1, 'schemes': schemes}, 1,
                              complete_history_capture=False, declared_limits=None)
    return {'schema': 'CASE13_RECORDED_GATE_CONSERVATIVE_V1',
            'case_gate': result['recorded_convergence_evidence_gate'],
            'case_status_present_in_projection': False,
            'limits_independently_authenticated': False,
            'complete_history_capture_attested': False,
            'ao_phase_histories_associated_from_separate_events': sum(a['scheme'] == 'AO' for a in associations),
            'phase_event_associations': associations,
            'schemes': result['schemes'],
            'historical_source_authenticated': False,
            'whole_event_atomic_snapshot_verified': False,
            'scientific_or_paper_pass': False}


def main():
    c = load('tools/hotspot-case13-stop-consumer-v1/consume_saved_stops.py', 'stop_consumer')
    gate = load('tools/hotspot-final-ieee-convergence-gate-v1/recorded_gate.py', 'recorded_gate')
    rows = [c.parse(line) for line in gunzip(STOPS, 512 * 1024).splitlines()]
    mc = c.parse(gunzip(MC, 256 * 1024))
    print(json.dumps(make_report(rows, mc, c, gate), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
