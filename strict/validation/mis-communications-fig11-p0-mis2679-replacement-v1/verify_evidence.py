"""Check the retained local evidence; do not run the optimizer."""
from pathlib import Path
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
    require(len(events) == 5, 'unexpected event count')
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
    require(first['kind'] == 'boundary' and first['baseline'] == 'MIS' and first['start'] == 2679,
            'boundary identity')
    require(first['successful_historical_mu_stages'] == 19 and first['first_failed_mu_call'] == 20
            and first['original_failed_stage_iterations'] == 3
            and first['replacement_stage_original_iteration_cap'] == 4000
            and first['replacement_is_separate_attempt'] is True
            and first['later_historical_stages_not_reused'] is True, 'boundary scope')
    require([x['kind'] for x in events[1:]] == ['rcg_iteration'] * 3 + ['final_stage_end'],
            'event order')
    require(final['cursor']['finished'] is True and final['stop']['reason'] == 'gradient_tolerance'
            and math.isfinite(final['stop']['projected_kkt_norm'])
            and final['stop']['projected_kkt_norm'] <= 1e-6, 'recorded projected stopping test')
    result, hist, guard = read_json('result.json'), read_json('historical_stage_stops.json'), read_json('guard_sanitized.json')
    require(result['last_event_digest'] == previous and result['event_count'] == len(events)
            and result['status'] == 'finished' and result['last_cursor'] == final['cursor'], 'result binding')
    gate = result['replacement_stage_stop_gate']
    require(gate['recorded_mu_count'] == gate['required_mu_count'] == 1
            and gate['stage_stops'][0]['projected_kkt_norm'] == final['stop']['projected_kkt_norm']
            and gate['all_replacement_stages_stopping_pass'] is True
            and gate['eligible_for_final_ranking'] is False
            and gate['independent_physical_feasibility_verified'] is False
            and gate['original_reference_agreement'] is False
            and result['historical_content_reverified'] is False
            and result['full_paper_pass'] is False, 'result disclosure and stop')
    stages = hist['stages']
    require(len(stages) == 20 and all(s['call'] == n for n, s in enumerate(stages, 1)), 'historical sequence')
    require(all(s['stop']['reason'] == 'gradient_tolerance'
                and math.isfinite(s['stop']['projected_kkt_norm'])
                and s['stop']['projected_kkt_norm'] <= 1e-6 for s in stages[:19]), 'historical stopping summary')
    require(stages[-1]['recorded_inner_iterations'] == 3 and
            stages[-1]['stop']['reason'] == first['original_failure_reason'] and
            stages[-1]['mu'] == float.fromhex(first['cursor']['mu_hex']), 'historical failed stage')
    require(guard['guard_success'] is True and guard['terminal_reason'] == 'natural_exit'
            and guard['returncode'] == 0 and guard['scientific_acceptance'] is False
            and guard['hard_filesystem_quota'] is False, 'sanitized guard report')
    print('PASS: retained five-event chain, recorded stops, and scoped disclosures; no science rerun')


if __name__ == '__main__':
    main()
