"""Equivalent ISAC metrics using explicit self-excluded interference sums.

This is an arithmetic provider, not an optimizer. It accepts the original
channel fields and derivatives. No iteration, acceptance, or stop rule lives
here. The fixed inner-block iota is supplied by the caller.
"""
import numpy as np


def evaluate(w, field, jac, bridge, ris_links, c, iota, gradients=False):
    k = len(c['noise'])
    fc, fs = field[:, :k], field[:, k:]
    y, z = fc.conj().T @ w, fs.conj().T @ w
    powers = abs(y)**2
    mask = np.ones_like(powers, dtype=bool)
    mask[np.arange(k), np.arange(k)] = False
    interference = np.asarray(c['noise']) + np.sum(np.where(mask, powers, 0.0), axis=1)
    signal = powers[np.arange(k), np.arange(k)]
    total = signal + interference
    rate = float(np.log1p(signal / interference).sum() / np.log(2.0))
    pattern = np.sum(abs(z)**2, axis=1)
    desired = np.asarray(c['desired_pattern'])
    denominator = iota*iota*float(desired @ desired)
    residual = pattern-iota*desired
    nmse = float(residual @ residual / denominator)
    result = dict(utility=rate-c['rho']*nmse, rate=rate, nmse=nmse,
                  pattern=pattern, iota=iota, sinr=signal/interference)
    if not gradients:
        return result
    coefficients = np.repeat((-signal / (total*interference))[:, None], w.shape[1], axis=1)
    coefficients[np.arange(k), np.arange(k)] = 1.0 / total
    gw = 2*fc @ (coefficients*y) / np.log(2.0) - 4*c['rho']*fs @ (residual[:, None]*z) / denominator
    bridge_w = bridge.conj().T @ w
    gt = np.zeros(len(ris_links), complex)
    for u in range(k):
        gt += 2*ris_links[:, u].conj()*(bridge_w @ (coefficients[u]*y[u].conj())) / np.log(2.0)
    for v in range(len(desired)):
        gt -= 4*c['rho']*residual[v]/denominator*ris_links[:, k+v].conj()*(bridge_w @ z[v].conj())
    gr = np.zeros(6)
    for d in range(6):
        dy, dz = jac[:, :k, d].conj().T @ w, jac[:, k:, d].conj().T @ w
        derivatives = 2*np.real(y.conj()*dy)
        dsignal = derivatives[np.arange(k), np.arange(k)]
        dinterference = np.sum(np.where(mask, derivatives, 0.0), axis=1)
        drate = np.sum(dsignal/total-signal/(total*interference)*dinterference) / np.log(2.0)
        dpattern = 2*np.real(np.sum(z.conj()*dz, axis=1))
        gr[d] = drate-2*c['rho']*(residual @ dpattern)/denominator
    return result, (gw, gt, gr)
