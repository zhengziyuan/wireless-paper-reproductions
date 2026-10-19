"""Independent saved MIS Fig3 physics and KKT; no production import or optimizer.

Reconstructs all nine array responses from positions/angles with MP80/100,
then evaluates actual stored phases, one-padded second-layer locations,
quartic echoes and explicitly self-excluded interference. Final gradients use
direct original Lagrangian derivatives. Decimal60 simplex projection supplies
the same finite projected-gradient KKT residual without the producer routine.
Old capped starts retain their failure flags, even with a valid final KKT.
"""
from __future__ import annotations
import argparse
from collections import Counter
from decimal import Decimal, localcontext
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import mpmath as mp
import numpy as np


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def require(test, message):
    if not test:
        raise ValueError(message)


def write(path, value):
    temp = path.with_suffix(path.suffix+'.partial')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    temp.replace(path)


def binary(value):
    n, d = float(value).as_integer_ratio()
    return mp.mpf(n)/d


def basis(settings, point):
    require(point == dict(ms1=[20, 20], ms2=[16, 16], Kphi=3, Ktheta=3),
            'All original400/256 elements and nine targets required')
    lanes = {}
    for digits in (80, 100):
        with mp.workdps(digits):
            spacing = binary(settings['spacing_over_wavelength'])
            inc = [binary(x) for x in settings['incidence_direction_cosines']]
            rows = []
            for elevation in (30, 50, 70):
                e = mp.pi*elevation/180
                for azimuth in (0, 45, 90):
                    a = mp.pi*azimuth/180
                    x, y = mp.sin(e)*mp.cos(a)+inc[0], mp.sin(e)*mp.sin(a)+inc[1]
                    rows.append([mp.exp(2j*mp.pi*spacing*(r*x+c*y)) for r in range(20) for c in range(20)])
            lanes[digits] = rows
    with mp.workdps(110):
        gap = max(abs(a-b) for x,y in zip(lanes[80], lanes[100]) for a,b in zip(x,y))
    require(gap < mp.mpf('1e-40'), 'Physical response precision did not stabilize')
    response = np.asarray([[complex(z) for z in row] for row in lanes[100]], dtype=complex)
    indices = np.asarray([[(r+i)*20+c+j for i in range(16) for j in range(16)]
                          for r in range(5) for c in range(5)])
    with mp.workdps(100):
        db = binary(settings['reference_echo_db'])
        if settings['reference_echo_unit'] == 'inverse_milliwatt':
            db += 30
        else:
            require(settings['reference_echo_unit'] == 'inverse_watt', 'Explicit echo reference unit required')
        gain = binary(settings['effective_reference_gain_factor'])
        beta = float(mp.power(10, db/10))
        noise = float(1/(mp.power(10, (binary(settings['power_dbm'])-30)/10)*gain))
    return response, indices, beta, noise, mp.nstr(gap, 105)


def simplex_decimal(y):
    """Exact-input Decimal60 Euclidean probability-simplex projection."""
    with localcontext() as context:
        context.prec = 60
        values = list(y); ordered = sorted(values, reverse=True); total = Decimal(0); threshold = None
        for count, item in enumerate(ordered, 1):
            total += item; trial = (total-1)/count
            if count == len(ordered) or ordered[count] <= trial:
                threshold = trial; break
        require(threshold is not None, 'Simplex root missing')
        result = [max(v-threshold, Decimal(0)) for v in values]
        require(abs(sum(result)-1) < Decimal('1e-55'), 'Decimal probability mass not preserved')
        return result


def physical(record, response, indices, beta, noise, settings):
    state = record['state']; phi = np.asarray(state['phi']['real'])+1j*np.asarray(state['phi']['imag'])
    theta = np.asarray(state['theta']['real'])+1j*np.asarray(state['theta']['imag'])
    X = np.asarray(state['X'], dtype=float); eta = float(state['eta']); lam = np.asarray(record['metrics']['multipliers'])
    require(phi.shape == (400,) and theta.shape == (256,) and X.shape == (9, 25) and lam.shape == (9,),
            'Stored complete original state shape differs')
    require(all(np.isfinite(v).all() for v in (phi, theta, X, lam)), 'Nonfinite actual state')
    padded = np.ones((25, 400), dtype=complex)
    for row, locations in enumerate(indices):
        padded[row, locations] = theta
    fields = response @ (padded*phi[None, :]).T
    amplitude2 = np.real(fields)**2+np.imag(fields)**2
    echo = beta*amplitude2**2
    denominator = np.asarray([noise+np.sum(echo[np.arange(9) != k], axis=0) for k in range(9)])
    require(np.min(denominator) > 0, 'Positive original echo denominator required')
    gamma = echo/denominator; scheduled = np.sum(X*gamma, axis=1)
    binary_columns = np.argmax(X, axis=1); residual = eta-scheduled
    metric = dict(eta=eta, min_relaxed_metric=float(min(scheduled)),
        min_binary_metric=float(min(gamma[np.arange(9), binary_columns])), maximum_constraint=float(max(residual)))
    # Original relaxed constrained Lagrangian -eta + sum lambda_k q_k.
    weights = -lam[:, None]*X
    weighted = weights*echo/denominator**2
    coefficient = np.asarray([weights[k]/denominator[k]-np.sum(weighted[np.arange(9) != k], axis=0)
                              for k in range(9)])
    field_gradient = 4*beta*amplitude2*fields*coefficient
    aperture_gradient = response.conj().T @ field_gradient
    gp = np.sum(padded.conj().T*aperture_gradient, axis=1)
    gt = np.zeros(256, dtype=complex)
    for row, locations in enumerate(indices):
        gt += phi[locations].conj()*aperture_gradient[locations, row]
    tp = gp-np.real(gp*phi.conj())*phi
    tt = gt-np.real(gt*theta.conj())*theta
    # Simplex projection is invariant to the producer's row-mean gradient
    # subtraction. Import the actual X, lambda, gamma as exact binary values.
    xr = np.empty_like(X)
    with localcontext() as context:
        context.prec = 60
        for row in range(9):
            actual = [Decimal.from_float(float(x)) for x in X[row]]
            gradient = [Decimal.from_float(float(v)) for v in -lam[row]*gamma[row]]
            projected = simplex_decimal([x-g for x,g in zip(actual, gradient)])
            xr[row] = [float(x-y) for x,y in zip(actual, projected)]
        ge = float(sum(Decimal.from_float(float(x)) for x in lam)-1)
    norm = math.sqrt(math.fsum(float(abs(z)**2) for v in (tp, tt, xr.reshape(-1)) for z in v)+ge*ge)
    phase_error = max(float(max(abs(abs(phi)-1))), float(max(abs(abs(theta)-1))))
    simplex_error = max(float(max(abs(np.sum(X, axis=1)-1))), float(max(0, -np.min(X))))
    primal = max(0., float(max(residual))); dual = max(0., float(-min(lam)))
    complementarity = float(max(abs(lam*residual)))
    tolerance = record['summary']['solver_status']['original_problem_kkt_certificate']['stationarity_tolerance']
    ftol = settings['feasibility_tolerance']
    certificate = dict(stationarity_norm=norm, stationarity_tolerance=tolerance,
        maximum_positive_primal_residual=primal, maximum_negative_dual_residual=dual,
        maximum_absolute_complementarity=complementarity, feasibility_tolerance=ftol,
        maximum_phase_modulus_error=phase_error, maximum_simplex_storage_error=simplex_error)
    certificate['original_problem_kkt_verified'] = bool(norm < tolerance and primal <= ftol and dual <= ftol and
        complementarity <= ftol and max(phase_error, simplex_error) <= 32*np.finfo(float).eps)
    metric_ok = all(abs(value-record['metrics'][key]) <= 1e-9+1e-10*abs(value) for key,value in metric.items())
    original = record['summary']['solver_status']['original_problem_kkt_certificate']
    certificate_fields_ok = all(abs(value-original[key]) <= 1e-9+1e-10*abs(value)
                               for key,value in certificate.items() if key != 'original_problem_kkt_verified')
    certificate_boolean_ok = certificate['original_problem_kkt_verified'] == original['original_problem_kkt_verified']
    selected = np.zeros((9, 25)); selected[np.arange(9), binary_columns] = 1
    binary_ok = np.array_equal(selected, record['metrics']['binary_schedule'])
    return dict(metrics=metric, certificate=certificate, saved_physical_fields_match=bool(metric_ok and binary_ok),
        saved_KKT_residual_fields_match=bool(certificate_fields_ok), saved_KKT_boolean_reconfirmed=bool(certificate_boolean_ok),
        maximum_physical_field_error=max(abs(v-record['metrics'][k]) for k,v in metric.items()),
        stationarity_norm_error=abs(norm-original['stationarity_norm']))


def audit(bank, output, selected=None):
    manifest_path = bank/'manifest.json'; result_path = bank/'full-result-python.json'
    manifest_raw = manifest_path.read_bytes(); result_raw = result_path.read_bytes(); own = Path(__file__).read_bytes()
    manifest, result = json.loads(manifest_raw), json.loads(result_raw)
    settings = manifest['settings']; point = manifest['figure']['points'][0]
    require(manifest['figure']['id'] == 'fig3' and manifest['expected_jobs'] == settings['number_of_starts'] == 6000,
            'Complete original Fig3 population required')
    require(settings['outer_iterations'] == 30 and settings['rcg_max_iterations'] == 4000,
            'Retain the original30/4000 budgets')
    require(result['bank_signature'] == manifest['signature'], 'Saved bank signature differs')
    summaries = result['points'][0]['result']['all_start_summaries']
    require([s['start'] for s in summaries] == list(range(1, 6001)), 'All6000 original slots required')
    response, indices, beta, noise, basis_gap = basis(settings, point)
    wanted = selected or list(range(1, 6001)); require(len(set(wanted)) == len(wanted), 'Duplicate selected slot')
    plan = dict(bank_signature=manifest['signature'], manifest_sha256=sha(manifest_raw),
        full_result_sha256=sha(result_raw), actual_auditor_sha256=sha(own), selected_original_starts=wanted,
        actual_runtime=dict(python=sys.version.split()[0], numpy=np.__version__, mpmath=mp.__version__))
    if output.exists():
        require((output/'audit-plan.json').exists() and read(output/'audit-plan.json') == plan,
                'Existing independent checkpoint has different inputs/source/runtime; preserve it')
    else:
        output.mkdir(parents=True); write(output/'audit-plan.json', plan)
    (output/'starts').mkdir(exist_ok=True)
    records = []; started = time.perf_counter(); failures = Counter()
    for number in wanted:
        require(1 <= number <= 6000, 'Original start slot outside population')
        path = bank/'starts'/f'point-0000-start-{number:04d}.json.gz'; raw = path.read_bytes()
        cached = output/'starts'/f'start-{number:04d}-audit.json'
        if cached.exists():
            checked = read(cached)
            require(checked['start'] == number and checked['raw_saved_record_sha256'] == sha(raw) and
                    checked['actual_auditor_sha256'] == sha(own), 'Cached independent start uses changed source/input')
        else:
            record = json.loads(gzip.decompress(raw)); summary = summaries[number-1]
            require(record['bank_signature'] == manifest['signature'] and record['summary'] == summary and
                    record['source_unchanged_during_run'] is True and record['source_manifest'] == manifest['source_manifest'],
                    'Actual saved start binding differs')
            numerical = physical(record, response, indices, beta, noise, settings)
            history = record['history']; require(0 < len(history) <= 30, 'Original outer record missing')
            stationarity = [h['stop']['projected_kkt_norm'] <= h['epsilon_used'] for h in history]
            caps = sum(h['stop']['reason'] == 'iteration_cap' for h in history)
            status = summary['solver_status']
            stops_match = (bool(all(stationarity)) == status['all_inner_tolerances_satisfied'] and
                           bool(stationarity[-1]) == status['final_inner_stationary'] and caps == status['inner_iteration_cap_exits'])
            checks = dict(actual_saved_physical_fields_match=numerical['saved_physical_fields_match'],
                actual_KKT_residual_fields_match=numerical['saved_KKT_residual_fields_match'],
                actual_KKT_pass_flag_reconfirmed=numerical['saved_KKT_boolean_reconfirmed'],
                all_recorded_inner_stop_decisions_match=bool(stops_match))
            checked = dict(start=number, raw_saved_record_sha256=sha(raw), actual_auditor_sha256=sha(own), checks=checks,
                independent_final_metrics=numerical['metrics'], independent_final_KKT=numerical['certificate'],
                maximum_same_state_metric_error=numerical['maximum_physical_field_error'],
                final_stationarity_norm_error=numerical['stationarity_norm_error'],
                original_convergence_pass_retained=status['convergence_verified'],
                original_exit_status_retained=summary['exit_status'], original_inner_cap_exits=caps,
                actual_recorded_inner_stops=len(history), all_saved_record_checks_pass=all(checks.values()))
            write(cached, checked)
        checks = checked['checks']
        for key,value in checks.items():
            if not value:
                failures[key] += 1
        records.append(checked)
        if len(records) % 25 == 0 or len(records) == len(wanted):
            progress = dict(scope='Independent saved final physics and KKT, not a new optimizer',
                expected_selected_starts=len(wanted), checked=len(records), passed=sum(r['all_saved_record_checks_pass'] for r in records),
                failure_counts=dict(failures), last_start=number, elapsed_seconds=time.perf_counter()-started,
                original_full6000_convergence_pass=False,
                durable_per_start_audits_and_source_bindings_retained=True)
            write(output/'progress.json', progress); print(json.dumps(progress), flush=True)
    unchanged = (manifest_path.read_bytes() == manifest_raw and result_path.read_bytes() == result_raw and Path(__file__).read_bytes() == own)
    require(all(sha((bank/'starts'/f'point-0000-start-{r["start"]:04d}.json.gz').read_bytes()) == r['raw_saved_record_sha256']
                for r in records), 'An actual saved input changed during the independent audit')
    complete = wanted == list(range(1, 6001))
    final = dict(scope='Independent actual saved final-state physics and original projected KKT; recorded inner stops checked separately',
        full6000_population_checked=complete, selected_original_starts=wanted if not complete else None,
        checked_starts=len(records), all_saved_records_source_and_input_bindings_unchanged=unchanged,
        all_checked_saved_fields_KKT_flags_and_stop_decisions_match=bool(unchanged and all(r['all_saved_record_checks_pass'] for r in records)),
        original_convergence_pass_starts=sum(r['original_convergence_pass_retained'] for r in records),
        independent_final_KKT_pass_starts=sum(r['independent_final_KKT']['original_problem_kkt_verified'] for r in records),
        maximum_same_state_metric_error=max(r['maximum_same_state_metric_error'] for r in records),
        maximum_final_stationarity_norm_error=max(r['final_stationarity_norm_error'] for r in records),
        physical_response_MP80_MP100_maximum_difference=basis_gap,
        response_contract='Exact binary input spacing and source-recovered angles, high-precision trigonometry; no production response/evaluator imported',
        final_field_comparison_policy='1e-9+1e-10*abs(independent_reference); original feasibility/stationarity thresholds unchanged',
        simplex_reference='Independent Decimal60 probability-simplex projection; exact binary state and computed gradient inputs',
        actual_echo_beta_squared=beta, actual_noise_over_power=noise, failure_counts=dict(failures), records=records,
        input_sha256=dict(manifest=sha(manifest_raw), full_result=sha(result_raw), auditor=sha(own)),
        optimizer_or_random_generator_calls=0, unsaved_inner_gradients_reconstructed=False,
        old_failed_or_unverified_flags_upgraded=False, full6000_convergence_or_original_reference_or_paper_pass=False,
        elapsed_seconds=time.perf_counter()-started)
    write(output/'summary.json', final)
    print(json.dumps({k:v for k,v in final.items() if k not in ('records', 'selected_original_starts')}), flush=True)
    return final


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--bank', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True); p.add_argument('--starts', type=int, nargs='+')
    a = p.parse_args()
    if not audit(a.bank, a.output_dir, a.starts)['all_checked_saved_fields_KKT_flags_and_stop_decisions_match']:
        raise SystemExit(1)
