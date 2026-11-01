"""Inspect saved aggregate metadata only; do not open the historical trace."""
import json
from pathlib import Path


def read(name):
    path = Path(__file__).resolve().parent / name
    with path.open('rb') as stream:
        raw = stream.read(16385)
    if len(raw) > 16384:
        raise ValueError('small evidence input exceeds cap')
    return json.loads(raw)


def need(condition, message):
    if condition is not True:
        raise ValueError(message)


def main():
    a, c, g = (read(n) for n in ('recorded-audit.json', 'child-summary.json',
                                  'guard-summary.json'))
    counts = {'MC_begin': 1, 'MC_draw': 1000, 'MC_end': 1,
              'MC_evaluation': 3000, 'geometry_G': 1000,
              'geometry_begin': 1000, 'geometry_end': 1000,
              'geometry_ground': 1000}
    need(a.get('action_counts') == counts and
         all(type(v) is int for v in a['action_counts'].values()) and
         sum(counts.values()) == 8002,
         'recorded action coverage')
    need(c.get('events_completed') == 8002 and c.get('status') == 'completed' and
         c.get('read_bytes') == a.get('read_bytes') == 56608228, 'child summary')
    for field in ('MC_boundary_position_mismatch_count', 'MC_end_array_mismatch_count',
                  'adjacent_rng_chain_mismatch_count', 'draw_group_order_mismatch_count',
                  'negative_saved_rate_count', 'rate_mismatch_count',
                  'saved_direct_NHU_mismatch_count', 'value_context_mismatch_count'):
        need(type(a.get(field)) is int and a[field] == 0, 'reported mismatch: ' + field)
    for field in ('complete_interval_recorded', 'draw_and_geometry_id_coverage',
                  'geometry_G_and_ground_record_coverage', 'scheme_draw_record_coverage',
                  'reported_draw_counts_match_expected', 'MC_rng_before_matches_first_geometry',
                  'last_geometry_rng_matches_MC_end'):
        need(a.get(field) is True, 'recorded flag: ' + field)
    need(a.get('actual_draw_count') == a.get('original_draw_count') ==
         a.get('draws_expected') == 1000, 'recorded draw counts')
    need(a.get('geometry_rng_pairs_compared') == a.get('geometry_rng_changed_pairs') == 1000 and
         a.get('geometry_rng_equal_pairs') == 0 and
         a.get('adjacent_saved_NHU_different_pairs') == 999 and
         a.get('adjacent_saved_NHU_identical_pairs') == 0, 'recorded equality counts')
    need(g.get('child_terminal_observed') is True and g.get('child_returncode') == 0 and
         g.get('reason') == 'natural_exit' and g.get('errors') == [] and
         g.get('peak_accounted_bytes') == 18652, 'guard terminal')
    for record in (a, c, g):
        need(record.get('historical_source_authenticated') is False, 'source boundary')
    need(a.get('statistical_independence_proven') is False and
         a.get('common_underlying_channel_across_schemes_proven') is False and
         a.get('full_paper_pass') is False and g.get('scientific_acceptance') is False,
         'scientific boundary')
    print('saved aggregate records consistent; no original trace was read')


if __name__ == '__main__':
    main()
