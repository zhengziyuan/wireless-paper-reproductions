"""Check the retained local evidence; do not run the optimizer."""
from pathlib import Path
import base64
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parent


def require(value, why):
    if not value:
        raise ValueError(why)


def read_json(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8-sig'))


def canonical(obj):
    return (json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode('ascii')


def main():
    data = (ROOT / 'events.jsonl').read_bytes()
    require(data.endswith(b'\n'), 'partial event tail')
    events = [json.loads(row) for row in data.splitlines()]
    require(len(events) == 4, 'unexpected event count')
    previous, context = None, None
    for seq, event in enumerate(events):
        require(event['sequence'] == seq and event['previous_digest'] == previous, 'sequence/link')
        obj = dict(event)
        digest = obj.pop('event_digest')
        require(hashlib.sha256(canonical(obj)).hexdigest() == digest, 'event digest')
        if context is None:
            context = event['context_id']
        require(event['context_id'] == context, 'event context')
        previous = digest
    first, final = events[0], events[-1]
    require(first['kind'] == 'boundary' and first['baseline'] == 'SMS' and first['start'] == 2,
            'boundary identity')
    require(first['successful_historical_mu_stages'] == 18 and first['first_failed_mu_call'] == 19
            and first['original_failed_stage_iterations'] == 5
            and first['replacement_stage_original_iteration_cap'] == 4000
            and first['replacement_is_separate_attempt'] is True
            and first['later_historical_stages_not_reused'] is True, 'boundary scope')
    require([x['kind'] for x in events[1:]] == ['rcg_iteration'] * 2 + ['final_stage_end'],
            'event order')
    states = []
    for event in events:
        raw = base64.b64decode(event['cursor']['rcg_state_base64'], validate=True)
        state = json.loads(raw)
        require(state['z']['theta']['shape'] == [0] and
                base64.b64decode(state['z']['theta']['data'], validate=True) == b'', 'empty theta')
        require(state['z']['phi']['shape'] == [64] and state['z']['X']['shape'] == [2, 1],
                'SMS block shapes')
        states.append(state)
    require([x['iteration'] for x in states] == [0, 1, 2, 2] and
            [events[i]['info']['iteration'] for i in (1, 2)] == [0, 1] and
            [x['done'] for x in states] == [False, False, True, True] and
            states[-1]['done'] is True and states[-1]['reason'] == 'gradient_tolerance', 'iteration transitions')
    require(events[-1]['cursor']['rcg_state_base64'] == events[-2]['cursor']['rcg_state_base64'] and
            all(e['cursor']['mu_hex'] == first['cursor']['mu_hex'] for e in events), 'final cursor')
    require(final['cursor']['finished'] is True and final['stop']['reason'] == 'gradient_tolerance'
            and math.isfinite(final['stop']['projected_kkt_norm'])
            and final['stop']['projected_kkt_norm'] <= 1e-6, 'recorded projected stopping test')
    result, hist, guard = read_json('result.json'), read_json('historical_stage_stops.json'), read_json('guard_sanitized.json')
    require(result['last_event_digest'] == previous and result['event_count'] == len(events)
            and result['status'] == 'finished' and result['last_cursor'] == final['cursor'], 'result binding')
    gate = result['replacement_stage_stop_gate']
    require(gate['recorded_mu_count'] == gate['required_mu_count'] == 1
            and gate['stage_stops'][0]['projected_kkt_norm'] == final['stop']['projected_kkt_norm']
            and gate['stage_stops'][0]['reason'] == final['stop']['reason']
            and gate['stage_stops'][0]['stopping_check_pass'] is True
            and events[-2]['info']['projected_kkt_norm'] == final['stop']['projected_kkt_norm']
            and gate['all_replacement_stages_stopping_pass'] is True
            and gate['eligible_for_final_ranking'] is False
            and gate['independent_physical_feasibility_verified'] is False
            and gate['original_reference_agreement'] is False
            and result['historical_content_reverified'] is False
            and result['all_6000_start_ranking_complete'] is False
            and result['experimental_floating_phase_mapping'] is True
            and result['full_paper_pass'] is False, 'result disclosure and stop')
    stages = hist['stages']
    require(len(stages) == 19 and all(s['call'] == n for n, s in enumerate(stages, 1)), 'historical sequence')
    require(all(s['stop']['reason'] == 'gradient_tolerance'
                and math.isfinite(s['stop']['projected_kkt_norm'])
                and s['stop']['projected_kkt_norm'] <= 1e-6 for s in stages[:18]), 'historical stopping summary')
    require(stages[-1]['recorded_inner_iterations'] == 5 and
            stages[-1]['stop']['reason'] == first['original_failure_reason'] and
            stages[-1]['mu'] == float.fromhex(first['cursor']['mu_hex']), 'historical failed stage')
    require(guard['guard_success'] is True and guard['terminal_reason'] == 'natural_exit'
            and guard['returncode'] == 0 and guard['scientific_acceptance'] is False
            and guard['hard_filesystem_quota'] is False, 'sanitized guard report')
    print('PASS: four-event chain, empty theta, recorded stops, and scoped disclosures; no science rerun')


if __name__ == '__main__':
    main()
