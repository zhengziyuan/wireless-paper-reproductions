"""Portable saved-state reader. It never launches an optimizer or initializer.

The default only verifies files/schema. Mathematical modes are optional,
finite saved-state re-evaluations, not author-figure or trajectory acceptance.
"""
from pathlib import Path
from decimal import Decimal, localcontext
import argparse
import gzip
import hashlib
import importlib.util
import json
import struct
import sys
import numpy as np

HERE = Path(__file__).resolve().parent

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def read(name):
    path = HERE / name
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)

def load_source(name):
    spec = importlib.util.spec_from_file_location('_saved_' + name.replace('.', '_'), HERE/'sources'/name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def sig(value):
    if isinstance(value, dict):
        return ('dict', tuple(sorted((k, sig(v)) for k, v in value.items())))
    if isinstance(value, (tuple, list)):
        return ('list', tuple(map(sig, value)))
    if isinstance(value, float):
        return ('binary64', struct.pack('<d', value).hex())
    return (type(value).__name__, value)

def verify_files():
    manifest = read('MANIFEST.json')
    checks = {}
    for name, identity in manifest['files'].items():
        raw = (HERE/name).read_bytes()
        checks[name] = len(raw) == identity['bytes'] and sha(raw) == identity['SHA256']
    if not all(checks.values()):
        raise ValueError('Manifest mismatch: ' + repr([k for k, v in checks.items() if not v]))
    return checks

def fixture():
    records = read('fixtures/fig11-actual-records.json')['records']
    with np.load(HERE/'fixtures/fig11-actual-typed-states.npz', allow_pickle=False) as arrays:
        for row in records:
            if 'typed_state_array_keys' not in row:
                continue
            row['typed_state'] = {key: arrays[name] for key, name in row['typed_state_array_keys'].items()}
            for key, array in row['typed_state'].items():
                ident = row['array_identities'][key]
                if not (array.dtype.str == ident['dtype'] and list(array.shape) == ident['shape'] and
                    sha(array.tobytes(order='F')) == ident['IEEE_F_order_SHA256']):
                    raise ValueError('Typed-state IEEE identity differs')
    return records

def serialized(z):
    return {key: {'real': value.real.tolist(), 'imag': value.imag.tolist()}
        if np.iscomplexobj(value) else value.tolist() for key, value in z.items()}

def geometry(config):
    # Exact geometry statements from the actual first17 auditor. This is
    # binary64 source reconstruction, not independently captured/MP geometry.
    coords=np.array([[0,col] for col in range(64)])
    az=np.deg2rad(np.array(config['azimuth_deg']));el=np.deg2rad(np.array(config['elevation_deg']))
    direction=np.column_stack((np.sin(el)*np.cos(az),np.sin(el)*np.sin(az)))
    coefficient=np.exp(2j*np.pi*config['spacing_over_wavelength']*(direction@coords.T))
    coefficient*=np.exp(2j*np.pi*config['spacing_over_wavelength']*(coords@np.array(config['incidence_direction_cosines'])))[None,:]
    return {'real':coefficient.real.tolist(),'imag':coefficient.imag.tolist()}, [list(range(offset,offset+36)) for offset in range(29)]

def inspect():
    records = fixture()
    original = read('fixtures/fig11-first-original-start.json.gz')
    header, terminal = records[0], records[-1]
    checks = dict(records36=len(records)==36,
        header=header['event']=='actual_start_header',
        terminal=terminal['event']=='actual_start_observer_terminal',
        final_serialized_state=sig(serialized(records[-2]['typed_state']))==sig(original['state']),
        returned17=terminal['observer']['actual_original_RCG_returns']==17,
        capture_errors_empty=not terminal['observer']['callback_errors'])
    for stage in range(17):
        before, after = records[1+2*stage:3+2*stage]
        checks[f'stop{stage:02d}'] = sig(after['actual_stop'])==sig(original['history'][stage]['stop'])
        if stage:
            previous = records[2+2*(stage-1)]
            checks[f'link{stage:02d}'] = before['array_identities']==previous['array_identities']
    return dict(schema='portable-saved-evidence-file-and-transport-inspection-v1',
        checks=checks, passed=all(checks.values()),
        mathematical_re_evaluation_performed=False, fullpaper_reference_or_dual_PASS=False)

def fig11():
    report = read('evidence/fig11-Decimal60.json')
    oracle = load_source('fig11_Decimal60_reference.py')
    records = fixture()
    config = report['configuration']
    c, indices = geometry(config)
    rows = []
    for stage in range(17):
        ret = records[2+2*stage]
        physical = oracle.physical(config, c, indices, serialized(ret['typed_state']), ret['mu'])
        stop = ret['actual_stop']
        error = abs(physical['projected_kkt_norm']-stop['projected_kkt_norm'])
        obj_error = abs(physical['objective']-stop['objective'])
        rows.append(dict(stage_zero_based=stage, mu=ret['mu'], independent_Decimal60_physical=physical,
            actual_stop=stop, norm_absolute_error=error, unchanged_norm_comparison_bound=5e-13,
            norm_comparison_pass=error<=5e-13,
            objective_absolute_error=obj_error, objective_comparison_pass=obj_error<=5e-12+5e-14*abs(stop['objective']),
            independently_computed_printed_open_simplex_gradient_threshold_pass=physical['printed_rowmean_norm']<=1e-6,
            independent_closed_simplex_implemented_KKT_threshold_pass=physical['unchanged_implemented_1e_minus6_gate_pass']))
    all_strict=all(r['norm_comparison_pass'] and r['objective_comparison_pass'] and r['independent_closed_simplex_implemented_KKT_threshold_pass'] and r['independent_Decimal60_physical']['domain_feasible'] for r in rows)
    return dict(schema='portable-finite-first17-saved-state-Decimal60-replay-v1', rows=rows,
        all17_original_strict_comparisons_pass=all_strict,
        archive_original_strict_comparison_false_retained=report['all17_physical_LSE_KKT_comparisons_and_implemented_stops_pass'] is False,
        printed_threshold_is_implementation_selected=True, producer_convergence_flags_unchanged=True,
        all_other_starts_reference_dual_and_fullpaper_PASS=False)

def sensing2223():
    doc = read('fixtures/sensing2223-new-original-result.json.gz')
    settings = read('fixtures/sensing2223-settings.json')
    if sig(doc['settings']) != sig(settings):
        raise ValueError('Exact settings do not match the saved new result')
    ref = load_source('sensing_saved_reference.py')
    response, indices, beta, noise, gap = ref.basis(settings, doc['configuration'])
    record = dict(state=doc['state'], metrics=doc['metrics'], summary=dict(solver_status=doc['solver_status']))
    actual = ref.physical(record, response, indices, beta, noise, settings)
    return dict(schema='portable-only-new2223-saved-final-physical-KKT-replay-v1', independent_numerical_result=actual,
        physical_response_MP80_MP100_maximum_difference=gap,
        passed=all(actual[k] is True for k in ('saved_physical_fields_match','saved_KKT_residual_fields_match','saved_KKT_boolean_reconfirmed')) and actual['certificate']['original_problem_kkt_verified'] is True,
        precision_scope='MP80/100 steering then binary64 field/Lagrangian contractions and Decimal60 simplex; not all-gradient MP.',
        historical_producer_13checks_are_archived_not_reexecuted_here=True,
        old2223_failure_and_global720_false_retained=True,
        old_failed_state_not_recovered_or_reclassified=True,
        all_trajectory_reference_dual_or_fullpaper_PASS=False)

def trace():
    old = read('fixtures/sensing2223-old-outer1-all66.json')
    new = read('fixtures/sensing2223-new-original-result.json.gz')
    oldrows, newrows = old['inner'], new['history'][0]['inner']
    exact = [sig(a)==sig(b) for a,b in zip(oldrows, newrows)]
    first = next((i for i, value in enumerate(exact) if not value), None)
    scalar = None if first is None else dict(old_objective=oldrows[first]['objective'], new_objective=newrows[first]['objective'],
        old_objective_binary64_hex=float(oldrows[first]['objective']).hex(), new_objective_binary64_hex=float(newrows[first]['objective']).hex())
    return dict(schema='portable-old66-versus-new-first-outer-scalar-comparison-v1',
        old_rows=len(oldrows), new_first_outer_rows=len(newrows), compared_common=len(exact),
        identical_rows=exact, first_nonidentical_iteration=first, first_objective=scalar,
        old_failed_curve_iterate_and_trial_operands_included=False,
        specific_JIT_BLAS_observer_cause_established=False,
        old_failure_and_global720_false_retained=True)

def roundoff():
    report = read('evidence/fig11-Decimal60.json')
    kernel = HERE/'sources/fig11_Decimal60_reference.py'
    text = kernel.read_text(encoding='utf-8')
    old="'printed_open_simplex_gradient_criterion_claimed':False}"
    new="'printed_open_simplex_gradient_criterion_claimed':False,'causal_users_decimal':[str(v) for v in users],'causal_weights_decimal':[str(v) for v in weights]}"
    if text.count(old)!=1:
        raise ValueError('Frozen additive existing-value-return guard differs')
    derived=text.replace(old,new,1)
    assert derived.replace(new,old,1)==text
    reference={};exec(compile(derived,str(kernel)+':existing-values-only','exec'),reference)
    engine=load_source('frozen_communication_engine.py')
    config=report['configuration'];model=engine.Model(config)
    records=fixture();rows=[]
    for stage in (12,16):
        ret=records[2+2*stage];z=ret['typed_state'];mu=ret['mu'];stop=ret['actual_stop']
        c={'real':model.c.real.tolist(),'imag':model.c.imag.tolist()}
        exact=reference['physical'](config,c,model.indices.tolist(),serialized(z),mu)
        value,eg,_=model.communication_objective(z,mu,'maximize_negative_softmin')
        gradient=engine.project(z,eg);norm=engine.projected_kkt_norm(z,gradient)
        gamma=model.metric(z,'communications');users=np.sum(z['X']*gamma,axis=1)
        ex=np.exp(-(users-np.min(users))/mu);weights=ex/np.sum(ex)
        exact_weights=np.array([float(Decimal(v)) for v in exact['causal_weights_decimal']])
        _,gp,gt=model.metric(z,'communications',exact_weights[:,None]*z['X'])
        changed={'phi':-gp,'theta':-gt,'X':-exact_weights[:,None]*gamma}
        changednorm=engine.projected_kkt_norm(z,engine.project(z,changed))
        with localcontext() as ctx:
            ctx.prec=70
            du=[Decimal.from_float(float(v))-Decimal(e) for v,e in zip(users,exact['causal_users_decimal'])]
            dw=[Decimal.from_float(float(v))-Decimal(e) for v,e in zip(weights,exact['causal_weights_decimal'])]
            logodd_error=-(du[1]-du[0])/Decimal.from_float(float(mu))
        rows.append(dict(stage=stage,mu=mu,actual_saved_KKT=stop['projected_kkt_norm'],
            frozen_source_fixed_state_KKT=float(norm),independent_Decimal60_KKT=exact['projected_kkt_norm'],
            diagnostic_exact_reference_weight_only_KKT=float(changednorm),
            original_double_minus_reference_KKT=float(norm)-exact['projected_kkt_norm'],
            diagnostic_exact_weight_KKT_minus_full_Decimal60=float(changednorm)-exact['projected_kkt_norm'],
            users_binary64=users.tolist(),users_full_Decimal60=exact['causal_users_decimal'],
            users_binary64_minus_Decimal60=[str(v) for v in du],
            weights_binary64=weights.tolist(),weights_full_Decimal60=exact['causal_weights_decimal'],
            weights_binary64_minus_Decimal60=[str(v) for v in dw],
            induced_two_user_log_odds_error_from_rounded_user_scores=str(logodd_error)))
    return dict(schema='portable-only-two-saved-small-mu-diagnostic-replay-v1',rows=rows,
        counterfactual_weights_are_diagnostic_only=True,no_source_or_state_or_threshold_changed=True,
        original_strict_comparison_false_and_paper_scope_retained=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=('inspect','fig11','sensing2223','trace','roundoff'),default='inspect')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():
        raise FileExistsError('Choose a fresh output; never replace archived results')
    verify_files()
    result=globals()[args.mode]()
    result['optimizer_initialization_MC_or_RNG_calls']=0
    result['public_reader_first_true_use_is_a_new_replay_not_an_archived_execution']=True
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(output=str(args.output),mode=args.mode)))
    if args.mode=='fig11':
        return 0 if result['all17_original_strict_comparisons_pass'] else 2
    return 0 if result.get('passed',True) else 2

if __name__=='__main__':
    raise SystemExit(main())
