"""Audit arithmetic and flags in a bounded, already-extracted case-13 record.

This reads no original channel/trajectory data, and does not run an optimizer.
"""
import argparse
import json
import math
from pathlib import Path

CAP = 256 * 1024
NAMES = ('NoRIS', 'TwoStage', 'AO')
GATES = ('physical_constraint_pass','convergence_pass','solver_primal_pass','qt_sdr_bound_pass')


def need(condition, message):
    if not condition: raise ValueError(message)


def pairs(items):
    value = {}
    for k, v in items:
        need(k not in value, 'duplicate JSON key')
        value[k] = v
    return value


def finite(x):
    return type(x) in (int, float) and math.isfinite(x)


def check_flags(value):
    if value is None: return None
    need(isinstance(value, dict), 'check flags must be a dict')
    need(all(type(value.get(k)) is bool for k in GATES), 'unknown or invalid check flag')
    return {k:value[k] for k in GATES}


def audit(record):
    need(isinstance(record, dict) and record.get('schema') == 'CASE13_FINAL_RESULT_BOUNDED_PROJECTION_V1',
         'input schema')
    need(record.get('historical_source_authenticated') is False and
         record.get('whole_event_atomic_snapshot_verified') is False and
         record.get('full_paper_pass') is False, 'input scope')
    case = record['case']
    need(finite(case.get('U')) and case['U'] == 1 and finite(case.get('kappa_satellite_db'))
         and case['kappa_satellite_db'] == 20, 'case identity')
    need(set(record['schemes']) == set(NAMES), 'scheme set')
    result = {}
    for name in NAMES:
        scheme = record['schemes'][name]
        need(isinstance(scheme, dict), 'missing scheme')
        mc = scheme.get('independent_MC')
        need(isinstance(mc, dict), 'missing MC record')
        x = mc.get('hu_rate_samples')
        need(isinstance(x, list) and 2 <= len(x) <= 1000 and all(finite(v) for v in x),
             'invalid or missing sample vector')
        count = mc.get('count')
        need(finite(count) and count == int(count), 'invalid recorded count')
        mean = math.fsum(x) / len(x)
        se = math.sqrt(math.fsum((v-mean)**2 for v in x) / (len(x)-1) / len(x))
        saved_mean = mc.get('exact_ergodic_sum_rate_estimate')
        saved_se = mc.get('standard_error')
        need(finite(saved_mean) and finite(saved_se) and saved_se >= 0, 'invalid saved statistics')
        starts = scheme.get('recorded_starts')
        need(isinstance(starts,list) and len(starts)<=2, 'invalid recorded starts')
        summarized_starts = []
        for s in starts:
            need(isinstance(s,dict) and finite(s.get('start_id')) and
                 type(s.get('executed')) is bool and type(s.get('exception_present')) is bool,
                 'invalid start record')
            status = s.get('recorded_status')
            need(status is None or isinstance(status,dict), 'invalid start status')
            summarized_starts.append({'start_id': s['start_id'], 'executed': s['executed'],
                                      'checks_reported': check_flags(s.get('checks')),
                                      'status_reported': status,
                                      'exception_present': s['exception_present']})
        ens = scheme.get('ensemble')
        need(isinstance(ens,dict), 'missing ensemble')
        need(all(type(ens.get(k)) is bool for k in
                 ('all_required_starts_executed','all_required_starts_pass')), 'invalid ensemble flags')
        required, executed, selected = (ens.get(k) for k in
                    ('required_start_ids','executed_start_ids','selected_start_id'))
        need(all(isinstance(a,list) and len(a)<=2 and all(finite(v) for v in a)
                 for a in (required,executed,selected)), 'invalid ensemble ids')
        ids = [s['start_id'] for s in summarized_starts]
        prescribed = (sorted(required) == [0,1] and len(required) == 2)
        coverage = (prescribed and sorted(executed) == [0,1] and len(executed) == 2 and
                    sorted(ids) == [0,1] and len(ids) == 2 and
                    all(s['executed'] for s in summarized_starts))
        statuses_present = bool(summarized_starts) and all(isinstance(s['status_reported'],dict) and
                               type(s['status_reported'].get('converged')) is bool and
                               type(s['status_reported'].get('algorithm_success')) is bool
                               for s in summarized_starts)
        no_reported_failures = (coverage and statuses_present and
            all(not s['exception_present'] and s['checks_reported'] is not None and
                all(s['checks_reported'].values()) and
                s['status_reported']['converged'] is True and
                s['status_reported']['algorithm_success'] is True for s in summarized_starts))
        selected_is_reported_start = (len(selected) == 1 and selected[0] in ids)
        result[name] = {
            'sample_source_in_projection':'schemes.'+name+'.independent_MC.hu_rate_samples',
            'recorded_count':count, 'saved_sample_count':len(x),
            'recorded_count_matches_vector':count == len(x),
            'saved_budget_is_1000':count == len(x) == 1000,
            'recomputed_mean':mean, 'recorded_mean':saved_mean,
            'mean_difference':mean-saved_mean,
            'recomputed_sample_standard_error':se, 'recorded_standard_error':saved_se,
            'standard_error_difference':se-saved_se,
            'sample_min':min(x), 'sample_max':max(x),
            'recorded_starts':summarized_starts,
            'ensemble_required_start_ids':required, 'ensemble_executed_start_ids':executed,
            'ensemble_selected_start_id':selected,
            'recorded_start_ids_match_ensemble':len(ids)==len(set(ids)) and sorted(ids)==sorted(executed),
            'recorded_required_start_ids_match_case_u1':prescribed,
            'all_required_start_records_present_and_executed':coverage,
            'all_start_status_fields_present':statuses_present,
            'no_recorded_start_failures':no_reported_failures,
            'selected_id_belongs_to_recorded_starts':selected_is_reported_start,
            'recorded_ensemble_pass_agrees_with_start_reports':
                ens['all_required_starts_pass'] == no_reported_failures,
            'recorded_ensemble_executed_agrees_with_start_reports':
                ens['all_required_starts_executed'] == coverage,
            'recorded_ensemble_checks':check_flags(ens.get('checks')),
            'recorded_all_required_starts_executed':ens.get('all_required_starts_executed'),
            'recorded_all_required_starts_pass':ens.get('all_required_starts_pass'),
        }
    return {'schema':'CASE13_RECORDED_MC_ARITHMETIC_AUDIT_V1',
            'arithmetic':'math.fsum; sample standard deviation uses n-1, divided by sqrt(n)',
            'schemes':result, 'case_checks_reported':check_flags(record.get('case_checks_recorded')),
            'closed_checks_reported':check_flags(record.get('closed_checks_recorded')),
            'historical_source_authenticated':False, 'whole_event_atomic_snapshot_verified':False,
            'independent_draws_proven':False, 'physical_feasibility_proven':False,
            'recorded_stop_flags_independently_proven':False,
            'selection_optimality_independently_proven':False,
            'full_paper_pass':False}


def main():
    p=argparse.ArgumentParser();p.add_argument('projection',type=Path);a=p.parse_args()
    with a.projection.open('rb') as f:raw=f.read(CAP+1)
    need(len(raw)<=CAP, 'input cap')
    obj=json.loads(raw,object_pairs_hook=pairs,
                   parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
    print(json.dumps(audit(obj),sort_keys=True,indent=2,allow_nan=False))


if __name__=='__main__':main()
