"""Independent LoS-limit MR/RIS core implementation; see README for restrictions."""
import argparse
import json
from pathlib import Path
import numpy as np


def array_response(size, frequency):
    return np.exp(1j * np.pi * np.arange(size) * frequency)


def build_model(f):
    J, U, N, M = (f[k] for k in ('satellites', 'users', 'antennas', 'subsurfaces'))
    direct = np.zeros((J, U, N), dtype=complex)
    cascade = np.zeros((J, U, N, M), dtype=complex)
    hr = np.array([f['ris_user_amplitude'][u] * array_response(M, f['ris_user_frequency'][u]) for u in range(U)])
    for j in range(J):
        for u in range(U):
            direct[j, u] = f['direct_amplitude'][j][u] * array_response(N, f['direct_frequency'][j][u])
            G = f['satellite_ris_amplitude'][j][u] * np.outer(
                array_response(N, f['satellite_ris_frequency'][j][u]),
                np.conj(array_response(M, f['ris_arrival_frequency'][j][u])))
            cascade[j, u] = G * hr[u][None, :]
    gt = np.array([f['leo_gt_amplitude'][j] * array_response(N, f['leo_gt_frequency'][j]) for j in range(J)])
    geo_direct = np.array(f['geo_direct_real']) + 1j * np.array(f['geo_direct_imag'])
    geo_cascade = np.array([np.conj(hr[u]) * np.conj(
        f['geo_ris_amplitude'][u] * array_response(M, f['geo_ris_frequency'][u])) for u in range(U)])
    return dict(direct=direct, cascade=cascade, gt=gt, geo_direct=geo_direct, geo_cascade=geo_cascade)


def channels(model, phi, no_ris=False):
    h = model['direct'].copy()
    z = model['geo_direct'].copy()
    if not no_ris:
        for j in range(h.shape[0]):
            for u in range(h.shape[1]):
                h[j, u] += model['cascade'][j, u] @ phi[u]
        z += np.sum(model['geo_cascade'] * phi, axis=1)
    return h, z


def evaluate(f, model, phi, p, no_ris=False):
    h, z = channels(model, phi, no_ris)
    J, U, _ = h.shape
    numerator = np.zeros(U)
    denominator = np.array(f['noise'], dtype=float) + np.abs(z)**2
    sat_power = np.zeros(J)
    leakage = 0.0
    for j in range(J):
        for u in range(U):
            norm2 = np.vdot(h[j, u], h[j, u]).real
            numerator[u] += p[j, u] * norm2**2
            sat_power[j] += p[j, u] * norm2
            leakage += p[j, u] * abs(np.vdot(model['gt'][j], h[j, u]))**2
            for i in range(U):
                if i != u:
                    denominator[u] += p[j, i] * abs(np.vdot(h[j, u], h[j, i]))**2
    return dict(sinr=numerator / denominator, numerator=numerator, denominator=denominator,
                sat_power=sat_power, leakage=float(leakage))


def allocate(f, model, phi, no_ris=False):
    """Exact max-min power solution within p[j,u] = share[j] q[u]."""
    h, z = channels(model, phi, no_ris)
    J, U, _ = h.shape
    share = np.array(f['satellite_share'])
    signal, cross, power, leak = np.zeros(U), np.zeros((U, U)), np.zeros((J, U)), np.zeros(U)
    for j in range(J):
        for u in range(U):
            norm2 = np.vdot(h[j, u], h[j, u]).real
            signal[u] += share[j] * norm2**2
            power[j, u] = share[j] * norm2
            leak[u] += share[j] * abs(np.vdot(model['gt'][j], h[j, u]))**2
            for i in range(U):
                if i != u:
                    cross[u, i] += share[j] * abs(np.vdot(h[j, u], h[j, i]))**2
    offset = np.array(f['noise']) + abs(z)**2
    limits = np.array(f['satellite_power_limit'])
    upper = min(signal[u] * min(limits / power[:, u]) / offset[u] for u in range(U))
    lower, best = 0.0, np.zeros(U)
    trace = []
    for _ in range(f['bisection_steps']):
        target = (lower + upper) / 2
        A = np.eye(U) - target * cross / signal[:, None]
        try:
            q = np.linalg.solve(A, target * offset / signal)
            ok = np.all(q >= 0) and np.all(power @ q <= limits) and leak @ q <= f['gt_interference_limit']
            ok = ok and np.max(abs(A @ q - target * offset / signal)) < 1e-7
        except np.linalg.LinAlgError:
            ok, q = False, np.zeros(U)
        if ok:
            lower, best = target, q
        else:
            upper = target
        trace.append(lower)
    return share[:, None] * best[None, :], trace, upper


def utility_gradient(f, model, phi, p):
    """Analytic phase derivatives of soft-min SINR and signed residual penalty."""
    e = evaluate(f, model, phi, p)
    h, z = channels(model, phi)
    J, U, _ = h.shape
    M = phi.shape[1]
    mu, rho = f['smoothing'], f['penalty_weight']
    r = e['sinr']
    shift = np.min(r)
    weights = np.exp(-(r - shift) / mu)
    softmin = shift - mu * np.log(np.sum(weights))
    weights /= np.sum(weights)
    residual = e['leakage'] - f['gt_interference_limit']
    value = softmin - rho * residual**2
    gradient = np.zeros_like(phi.real)
    for v in range(U):
        for m in range(M):
            dh = np.zeros_like(h)
            for j in range(J):
                dh[j, v] = 1j * phi[v, m] * model['cascade'][j, v, :, m]
            dz = np.zeros(U, dtype=complex)
            dz[v] = 1j * phi[v, m] * model['geo_cascade'][v, m]
            ds = np.zeros(U)
            dd = 2 * np.real(np.conj(z) * dz)
            dl = 0.0
            for j in range(J):
                for u in range(U):
                    norm2 = np.vdot(h[j, u], h[j, u]).real
                    ds[u] += 4 * p[j, u] * norm2 * np.real(np.vdot(h[j, u], dh[j, u]))
                    c = np.vdot(model['gt'][j], h[j, u])
                    dc = np.vdot(model['gt'][j], dh[j, u])
                    dl += 2 * p[j, u] * np.real(np.conj(c) * dc)
                    for i in range(U):
                        if i != u:
                            c = np.vdot(h[j, u], h[j, i])
                            dc = np.vdot(dh[j, u], h[j, i]) + np.vdot(h[j, u], dh[j, i])
                            dd[u] += 2 * p[j, i] * np.real(np.conj(c) * dc)
            dr = (ds * e['denominator'] - e['numerator'] * dd) / e['denominator']**2
            gradient[v, m] = weights @ dr - 2 * rho * residual * dl
    return float(value), gradient


def optimize(f, model, phi, p):
    value, g = utility_gradient(f, model, phi, p)
    history = [value]
    for _ in range(f['iterations']):
        if np.linalg.norm(g) < 1e-10:
            break
        step = 1.0
        for _ in range(35):
            candidate = phi + step * 1j * phi * g
            candidate /= np.abs(candidate)
            trial, gg = utility_gradient(f, model, candidate, p)
            if trial >= value + 1e-4 * step * np.sum(g**2):
                break
            step *= 0.5
        else:
            break
        phi, value, g = candidate, trial, gg
        history.append(value)
    return phi, history


def run():
    f = json.loads(Path(__file__).with_name('fixture.json').read_text())
    model = build_model(f)
    initial = np.exp(1j * np.array(f['initial_phase']))
    p0, b0, _ = allocate(f, model, initial)
    base = evaluate(f, model, initial, p0)
    value, analytic = utility_gradient(f, model, initial, p0)
    numeric = np.zeros_like(analytic)
    eps = f['gradient_step']
    for u in range(initial.shape[0]):
        for m in range(initial.shape[1]):
            plus, minus = initial.copy(), initial.copy()
            plus[u, m] *= np.exp(1j * eps)
            minus[u, m] *= np.exp(-1j * eps)
            numeric[u, m] = (utility_gradient(f, model, plus, p0)[0] - utility_gradient(f, model, minus, p0)[0]) / (2 * eps)
    phi, trace = optimize(f, model, initial.copy(), p0)
    p, b, upper = allocate(f, model, phi)
    optimized = evaluate(f, model, phi, p)
    accepted = np.min(optimized['sinr']) >= np.min(base['sinr'])
    if not accepted:
        phi, p, optimized, b = initial, p0, base, b0
        _, _, upper = allocate(f, model, phi)
    pn, _, _ = allocate(f, model, initial, no_ris=True)
    no = evaluate(f, model, initial, pn, no_ris=True)
    # Direct evaluation from explicit W validates the reduced MR expression independently.
    h, z = channels(model, phi)
    direct_sinr = np.zeros(f['users'])
    for u in range(f['users']):
        signal, interference = 0.0, 0.0
        for j in range(f['satellites']):
            for i in range(f['users']):
                w = np.sqrt(p[j, i]) * h[j, i]
                received = abs(np.vdot(h[j, u], w))**2
                if i == u:
                    signal += received
                else:
                    interference += received
        direct_sinr[u] = signal / (interference + abs(z[u])**2 + f['noise'][u])
    grad_error = float(np.max(abs(analytic - numeric)))
    identity_error = float(np.max(abs(direct_sinr - optimized['sinr'])))
    power_violation = float(max(0.0, np.max(optimized['sat_power'] - f['satellite_power_limit'])))
    leak_violation = float(max(0.0, optimized['leakage'] - f['gt_interference_limit']))
    result = dict(paper_id='cooperative-satcom', metrics={
        'minimum_sinr': float(np.min(optimized['sinr'])), 'initial_ris_minimum_sinr': float(np.min(base['sinr'])),
        'no_ris_minimum_sinr': float(np.min(no['sinr'])), 'sinr': optimized['sinr'].tolist(),
        'satellite_power': optimized['sat_power'].tolist(), 'gt_interference': optimized['leakage'],
        'power_allocation': p.tolist(), 'fixed_share_bisection_upper': float(upper),
        'initial_phase_utility': value, 'phase_candidate_accepted': bool(accepted)},
        checks={'gradient_pass': grad_error < 1e-7, 'gradient_max_error': grad_error,
                'identity_pass': identity_error < 1e-10, 'identity_max_error': identity_error,
                'constraint_pass': power_violation < 1e-9 and leak_violation < 1e-9,
                'power_violation': power_violation, 'interference_violation': leak_violation,
                'unit_modulus_error': float(np.max(abs(abs(phi) - 1))),
                'phase_objective_monotone': bool(np.all(np.diff(trace) >= -1e-12)),
                'bisection_gap': float(upper - np.min(optimized['sinr'])),
                'bisection_pass': bool(abs(upper - np.min(optimized['sinr'])) < 1e-8)},
        history={'phase_utility': trace, 'power_bisection_lower': b})
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('outputs/cooperative-satcom-python.json'))
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result['checks'], indent=2))
    if not all(result['checks'][k] for k in ('gradient_pass', 'identity_pass', 'constraint_pass', 'bisection_pass')):
        raise SystemExit(1)
