"""Verbatim independent final-state physical/KKT functions; original full-source SHA256: 1c39fa1aff6e6740eb8087012c7cf1e0da37f6a033ac6ee64ab1d4f6ef17c643.
This module has no optimizer, random generator, MP basis or production import.
"""
from decimal import Decimal, localcontext
import math
import numpy as np

def require(test, message):
    if not test:
        raise ValueError(message)

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
