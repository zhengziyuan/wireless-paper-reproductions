"""Count saved MIS failure-field records, without rerunning the experiment."""
import json
from pathlib import Path


def load(path, limit):
    with path.open('rb') as stream:
        content = stream.read(limit + 1)
    if len(content) > limit:
        raise ValueError('input too large')
    return json.loads(content)


def need(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    root = Path(__file__).resolve().parent
    front_tail = load(root / 'recorded_695.json', 65536)
    middle = load(root / 'middle25_projection.json', 65536)
    need(front_tail['schema'] == 'MIS_695_SAVED_FAILURE_FIELD_CLASSIFICATION_V1', '695 schema')
    need(middle['schema'] == 'MIS_MIDDLE_25_SAVED_FIELDS_PROJECTION_V1', '25 schema')
    records = front_tail['records']
    rows = middle['rows']
    need(front_tail['selected_count'] == front_tail['report_count'] == len(records) == 695, '695 count')
    need(front_tail['error_count'] == 0 and front_tail['errors'] == [], 'report errors')
    need(len(rows) == 25, '25 count')
    need(all(type(r) is list and len(r) == 5 and type(r[0]) is int
             and all(type(v) is int and v in (0, 1) for v in r[1:]) for r in records), '695 records')
    ids = [r[0] for r in records] + [r['original_start'] for r in rows]
    need(len(set(ids)) == len(ids) == 720, 'duplicate start IDs')
    need(all(r['stored_original_combined_flag'] is False and
             type(r['stored_inner_cap_exits']) is int and r['stored_inner_cap_exits'] >= 0 and
             type(r['stored_final_original_KKT_flag']) is bool and
             r['same_eta_binary_inequality_from_saved_independent_metrics'] in ('pass', 'fail')
             for r in rows), '25 row values')
    cap = sum(r[1] == 1 for r in records) + sum(r['stored_inner_cap_exits'] > 0 for r in rows)
    kkt_false = sum(r[2] == 0 for r in records) + sum(not r['stored_final_original_KKT_flag'] for r in rows)
    binary_false = sum(r[3] == 0 for r in records) + sum(r['same_eta_binary_inequality_from_saved_independent_metrics'] == 'fail' for r in rows)
    s = middle['start2223']
    need(s['original_start'] == 2223 and s['inner_iteration_cap_exits'] == 0 and
         s['inner_failure_exits'] == 1 and s['all_inner_tolerances_satisfied'] is False and
         s['original_problem_kkt_verified'] is True, '2223 saved receipt')
    need((cap, kkt_false, binary_false) == (688, 44, 34), 'recorded count mismatch')
    print(json.dumps({'starts': len(ids), 'cap_present': cap, 'saved_final_kkt_false': kkt_false,
                      'derived_binary_false': binary_false,
                      'groups_overlap': True, 'historical_content_reverified': False,
                      'scientific_or_paper_pass': False}, separators=(',', ':')))


if __name__ == '__main__':
    main()
