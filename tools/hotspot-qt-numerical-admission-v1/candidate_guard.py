"""Unintegrated, read-only check of one full-moment vector-QT candidate.

Matrices use the repository's conjugate-channel convention, Q=D^H D. The
caller supplies the exact factors used by the candidate subproblem, the old
and candidate beams, and explicit, independently reviewed tolerances.
The guard does not invoke or modify a solver, a loop, an input or a result.
"""
import numpy as np


def inspect(moments, factors, old, candidate, hu_count, noise, power, targets,
            *, covariance_rtol, psd_rtol, power_rtol, qos_atol, qt_atol,
            tightness_atol, objective_atol, surrogate_atol):
    """Return a diagnostic decision; invalid input raises ValueError.

    Numerical norms and violations are reported, not a rigorous interval proof.
    Physical and surrogate constraints use all other streams. A failure does
    not return or assign a replacement beamformer. The caller must actually
    enforce `accepted`, keep old results, and bind the factors/source/inputs.
    """
    q = np.asarray(moments, dtype=np.complex128)
    d = np.asarray(factors, dtype=np.complex128)
    w0 = np.asarray(old, dtype=np.complex128)
    w1 = np.asarray(candidate, dtype=np.complex128)
    tau = np.asarray(targets, dtype=float)
    if (q.ndim != 3 or q.shape[1] != q.shape[2] or
        d.shape != q.shape or w0.ndim != 2 or w1.shape != w0.shape or
        w0.shape != (q.shape[1], q.shape[0]) or
        type(hu_count) is not int or not 0 < hu_count < q.shape[0] or
        tau.shape != (q.shape[0]-hu_count,)):
        raise ValueError('incompatible moment/factor/beam/user dimensions')
    vals = (covariance_rtol, psd_rtol, power_rtol, qos_atol, qt_atol,
            tightness_atol, objective_atol, surrogate_atol)
    names = ('covariance_rtol', 'psd_rtol', 'power_rtol', 'qos_atol',
             'qt_atol', 'tightness_atol', 'objective_atol', 'surrogate_atol')
    tol = {k: float(v) for k, v in zip(names, vals)}
    noise, power = float(noise), float(power)
    if (not all(np.isfinite(x).all() for x in (q, d, w0, w1, tau)) or
        not np.isfinite(noise) or noise <= 0 or
        not np.isfinite(power) or power <= 0 or np.any(tau < 0) or
        any(not np.isfinite(v) or v < 0 for v in tol.values())):
        raise ValueError('nonfinite data or invalid thresholds')
    jn = q.shape[0]
    cov_errors, herm_errors, min_eigenvalues = [], [], []
    for j in range(jn):
        scale = float(np.max(np.abs(q[j])))
        # Normalize before Frobenius norms and eigenvalues: squaring weak
        # moments directly can underflow and silently recreate a unit floor.
        if scale == 0:
            if np.any(d[j] != 0):
                raise ValueError('nonzero factor for zero covariance')
            cov_errors.append(0.)
            herm_errors.append(0.)
            min_eigenvalues.append(0.)
            continue
        scaled_q = q[j] / scale
        scaled_d = d[j] / np.sqrt(scale)
        if not np.isfinite(scaled_q).all() or not np.isfinite(scaled_d).all():
            raise ValueError('nonfinite covariance scaling')
        qnorm = float(np.linalg.norm(scaled_q, 'fro'))
        residual = float(np.linalg.norm(scaled_d.conj().T @ scaled_d - scaled_q, 'fro'))
        herm = float(np.linalg.norm(scaled_q - scaled_q.conj().T, 'fro'))
        if not all(np.isfinite(x) for x in (qnorm, residual, herm)) or qnorm == 0:
            raise ValueError('nonfinite covariance or factor residual')
        cov_errors.append(residual / qnorm)
        herm_errors.append(herm / qnorm)
        eigmin = float(np.linalg.eigvalsh((scaled_q + scaled_q.conj().T) / 2)[0])
        min_eigenvalues.append(eigmin / qnorm)
    covariance_ok = (max(cov_errors) <= tol['covariance_rtol'] and
                     max(herm_errors) <= tol['covariance_rtol'] and
                     min(min_eigenvalues) >= -tol['psd_rtol'])

    def channel(w):
        # All J−1 other streams are included, including every HU beam.
        received = np.array([[np.real(np.vdot(w[:, k], q[j] @ w[:, k]))
                              for k in range(jn)] for j in range(jn)])
        desired = np.diag(received)
        # Never subtract the desired power from a potentially much larger sum:
        # cancellation can erase small interfering streams and overstate QoS.
        interference = np.array([sum(received[j, k] for k in range(jn) if k != j) + noise
                                 for j in range(jn)])
        # Even a small admitted negative eigenvalue can be magnified by a
        # large beam into a materially negative interference term. Do not
        # silently cancel or clip any individual received power: reject it.
        # This strict zero threshold can also conservatively reject a truly
        # PSD input whose floating-point quadratic suffers tiny roundoff.
        if (not np.isfinite(received).all() or not np.isfinite(interference).all()
                or np.any(received < 0)
                or np.any(desired < 0) or np.any(interference <= 0)):
            raise ValueError('invalid actual quadratic power or denominator')
        return desired, interference, desired / interference

    _, _, sinr0 = channel(w0)
    _, den1, sinr1 = channel(w1)
    lower0, lower1 = [], []
    for j in range(jn):
        # Reconstruct the exact old auxiliary and lower bound from the D used
        # by the CVX problem, not from a nearby supplied Q. Relative factor
        # error may be small while its absolute effect on a large SINR is not.
        others = [i for i in range(jn) if i != j]
        d0, d1 = d[j] @ w0, d[j] @ w1
        i0 = float(np.sum(np.abs(d0[:, others])**2) + noise)
        i1 = float(np.sum(np.abs(d1[:, others])**2) + noise)
        z = d0[:, j] / i0
        znorm = float(np.vdot(z, z).real)
        lower0.append(float(2*np.real(np.vdot(z, d0[:, j])) - znorm*i0))
        lower1.append(float(2*np.real(np.vdot(z, d1[:, j])) - znorm*i1))
    lower0, lower1 = np.array(lower0), np.array(lower1)
    p0, p1 = float(np.sum(np.abs(w0)**2)), float(np.sum(np.abs(w1)**2))
    rate0 = float(np.log2(1 + sinr0[:hu_count]).sum())
    rate1 = float(np.log2(1 + sinr1[:hu_count]).sum())
    if not all(np.isfinite(x).all() for x in (lower0, lower1, sinr0, sinr1)) or not all(
            np.isfinite(x) for x in (p0, p1, rate0, rate1)):
        raise ValueError('nonfinite intermediate calculation')
    old_domain = bool(np.all(lower0[:hu_count] > -1))
    candidate_domain = bool(np.all(lower1[:hu_count] > -1))
    surrogate0 = float(np.log1p(lower0[:hu_count]).sum()/np.log(2)) if old_domain else None
    surrogate1 = float(np.log1p(lower1[:hu_count]).sum()/np.log(2)) if candidate_domain else None
    surrogate_ok = bool(old_domain and candidate_domain and np.isfinite(surrogate0)
                        and np.isfinite(surrogate1) and surrogate1 >= surrogate0 - tol['surrogate_atol'])
    checks = {
        'covariance_and_factor': bool(covariance_ok),
        'old_power': bool(p0 <= power * (1 + tol['power_rtol'])),
        'old_true_qos': bool(np.all(sinr0[hu_count:] >= tau - tol['qos_atol'])),
        'old_auxiliary_tightness': bool(np.max(np.abs(lower0-sinr0)) <= tol['tightness_atol']),
        'candidate_power': bool(p1 <= power * (1 + tol['power_rtol'])),
        'candidate_true_qos': bool(np.all(sinr1[hu_count:] >= tau - tol['qos_atol'])),
        'candidate_fixed_auxiliary_qos': bool(np.all(lower1[hu_count:] >= tau - tol['qt_atol'])),
        'candidate_auxiliary_is_true_lower_bound': bool(np.all(lower1 <= sinr1 + tol['qt_atol'])),
        'candidate_objective_nondecrease': bool(rate1 >= rate0 - tol['objective_atol']),
        'old_surrogate_log_domain': old_domain,
        'candidate_surrogate_log_domain': candidate_domain,
        'candidate_surrogate_objective_nondecrease': surrogate_ok,
    }
    return {'accepted': all(checks.values()), 'checks': checks, 'tolerances': tol,
            'max_factor_relative_error': max(cov_errors),
            'max_hermitian_relative_error': max(herm_errors),
            'min_eigenvalue_over_frobenius': min(min_eigenvalues),
            'old_auxiliary_max_tightness_error': float(np.max(np.abs(lower0-sinr0))),
            'candidate_fixed_auxiliary_qos': lower1[hu_count:].tolist(),
            'candidate_true_qos': sinr1[hu_count:].tolist(),
            'old_power': p0, 'candidate_power': p1,
            'old_hu_rate': rate0, 'candidate_hu_rate': rate1,
            'old_surrogate_hu_rate': surrogate0, 'candidate_surrogate_hu_rate': surrogate1,
            'old_beam_modified': False, 'integrated_with_production': False,
            'full_paper_pass': False}
