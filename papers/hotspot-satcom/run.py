"""Two-stage RIS criterion core; final journal equation labels are unverified."""
import argparse
import json
from pathlib import Path
import numpy as np


def array_response(n, frequency):
    return np.exp(1j * np.pi * np.arange(n) * frequency)


def build_model(f):
    N, M, U, K = (f[k] for k in ('antennas', 'subsurfaces', 'hotspot_users', 'nonhotspot_users'))
    hu = np.array([f['hotspot_amplitude'][u] * np.conj(array_response(N, f['hotspot_frequency'][u])) for u in range(U)])
    nhu = np.array([f['nonhotspot_amplitude'][k] * np.conj(array_response(N, f['nonhotspot_frequency'][k])) for k in range(K)])
    G = f['satellite_ris_amplitude'] * np.outer(array_response(M, f['ris_arrival_frequency']),
                                               np.conj(array_response(N, f['satellite_ris_frequency'])))
    R = np.empty((U, M, N), dtype=complex)
    for u in range(U):
        r = f['ris_user_amplitude'][u] * array_response(M, f['ris_user_frequency'][u])
        R[u] = np.conj(r)[:, None] * G
    # This is the paper's semi-orthogonal operator; NOT an orthogonal projector.
    A = np.eye(N, dtype=complex)
    for k in range(K):
        h = np.conj(nhu[k])
        A -= np.outer(h, np.conj(h)) / np.vdot(h, h).real
    return dict(hu=hu, nhu=nhu, R=R, G=G, A=A)


def effective(model, phi, no_ris=False):
    c = model['hu'].copy()
    if not no_ris:
        for u in range(c.shape[0]):
            c[u] += phi @ model['R'][u]
    return c


def objective_gradient(model, phi):
    c = effective(model, phi)
    transformed = c @ model['A']
    f2 = float(np.sum(abs(transformed)**2))
    f3 = 0.0
    for u in range(c.shape[0]):
        for v in range(u):
            f3 += abs(c[u] @ np.conj(c[v]))**2
    g = np.zeros(phi.size)
    for m in range(phi.size):
        dc = 1j * phi[m] * model['R'][:, m, :]
        dt = dc @ model['A']
        d2 = 2 * np.real(np.sum(np.conj(transformed) * dt))
        d3 = 0.0
        for u in range(c.shape[0]):
            for v in range(u):
                inner = c[u] @ np.conj(c[v])
                derivative = dc[u] @ np.conj(c[v]) + c[u] @ np.conj(dc[v])
                d3 += 2 * np.real(np.conj(inner) * derivative)
        g[m] = d2 - d3
    return float(f2 - f3), g, float(f2), float(f3)


def optimize(f, model, phi):
    value, g, _, _ = objective_gradient(model, phi)
    history = [value]
    for _ in range(f['iterations']):
        if np.linalg.norm(g) < 1e-10:
            break
        step = 1.0
        for _ in range(35):
            candidate = phi + step * 1j * phi * g
            candidate /= abs(candidate)
            trial, gg, _, _ = objective_gradient(model, candidate)
            if trial >= value + 1e-4 * step * np.sum(g**2):
                break
            step *= 0.5
        else:
            break
        phi, value, g = candidate, trial, gg
        history.append(value)
    return phi, history


def zf_qos_baseline(f, model, phi, no_ris=False):
    """Not paper Algorithm2 stage2: exact ZF + minimum NHU QoS + HU water filling."""
    hu = effective(model, phi, no_ris)
    C = np.vstack([hu, model['nhu']])
    V = C.conj().T @ np.linalg.solve(C @ C.conj().T, np.eye(C.shape[0]))
    V /= np.sqrt(np.sum(abs(V)**2, axis=0))[None, :]
    gain = abs(np.diag(C @ V))**2
    U, K = f['hotspot_users'], f['nonhotspot_users']
    power = np.zeros(U + K)
    power[U:] = np.array(f['nonhotspot_sinr_target']) * f['noise'] / gain[U:]
    remaining = f['total_power'] - np.sum(power[U:])
    if remaining < 0:
        raise ValueError('Fixed fixture has infeasible NHU QoS under the ZF baseline')
    # Exact water-filling for the HU rates of the fixed ZF directions.
    lower, upper = 0.0, remaining + max(f['noise'] / gain[:U])
    for _ in range(60):
        level = (lower + upper) / 2
        allocation = np.maximum(level - f['noise'] / gain[:U], 0)
        if np.sum(allocation) > remaining:
            upper = level
        else:
            lower = level
    power[:U] = np.maximum(lower - f['noise'] / gain[:U], 0)
    W = V * np.sqrt(power)[None, :]
    received = abs(C @ W)**2
    sinr = np.diag(received) / (np.sum(received, axis=1) - np.diag(received) + f['noise'])
    return dict(C=C, W=W, sinr=sinr, power=power, gain=gain,
                sum_rate=float(np.sum(np.log2(1 + sinr[:U]))),
                zf_residual=float(np.max(abs(C @ V - np.diag(np.diag(C @ V))))))


def run():
    f = json.loads(Path(__file__).with_name('fixture.json').read_text())
    model = build_model(f)
    initial = np.exp(1j * np.array(f['initial_phase']))
    value0, analytic, _, _ = objective_gradient(model, initial)
    eps = f['gradient_step']
    numeric = np.zeros_like(analytic)
    for m in range(initial.size):
        plus, minus = initial.copy(), initial.copy()
        plus[m] *= np.exp(1j * eps)
        minus[m] *= np.exp(-1j * eps)
        numeric[m] = (objective_gradient(model, plus)[0] - objective_gradient(model, minus)[0]) / (2 * eps)
    phi, trace = optimize(f, model, initial.copy())
    final, _, f2, f3 = objective_gradient(model, phi)
    initial_zf = zf_qos_baseline(f, model, initial)
    optimized = zf_qos_baseline(f, model, phi)
    no = zf_qos_baseline(f, model, phi, no_ris=True)
    U = f['hotspot_users']
    # Independent signal-loop SINR identity, rather than repeating matrix formula.
    manual = []
    for user in range(optimized['C'].shape[0]):
        desired, interference = 0.0, 0.0
        for beam in range(optimized['W'].shape[1]):
            r = abs(optimized['C'][user] @ optimized['W'][:, beam])**2
            if beam == user:
                desired += r
            else:
                interference += r
        manual.append(desired / (interference + f['noise']))
    identity_error = float(np.max(abs(np.array(manual) - optimized['sinr'])))
    grad_error = float(np.max(abs(analytic - numeric)))
    actual_power = float(np.sum(abs(optimized['W'])**2))
    power_violation = max(0.0, actual_power - f['total_power'])
    qos_violation = float(max(0.0, np.max(np.array(f['nonhotspot_sinr_target']) - optimized['sinr'][U:])))
    result = dict(paper_id='hotspot-satcom', metrics={
        'ris_criterion_initial': value0, 'ris_criterion_final': final,
        'semi_orthogonal_gain': f2, 'pairwise_correlation_penalty': f3,
        'hotspot_sum_rate_zf': optimized['sum_rate'], 'initial_ris_hotspot_sum_rate_zf': initial_zf['sum_rate'],
        'no_ris_hotspot_sum_rate_zf': no['sum_rate'], 'user_sinr': optimized['sinr'].tolist(),
        'beam_power': optimized['power'].tolist(), 'total_transmit_power': actual_power},
        checks={'gradient_pass': grad_error < 1e-7, 'gradient_max_error': grad_error,
                'identity_pass': identity_error < 1e-8, 'identity_max_error': identity_error,
                'constraint_pass': power_violation < 1e-8 and qos_violation < 1e-8,
                'power_violation': power_violation, 'qos_violation': qos_violation,
                'unit_modulus_error': float(np.max(abs(abs(phi) - 1))),
                'zf_residual': optimized['zf_residual'], 'zf_pass': optimized['zf_residual'] < 1e-8,
                'criterion_monotone': bool(np.all(np.diff(trace) >= -1e-12))},
        history={'ris_criterion': trace})
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('outputs/hotspot-satcom-python.json'))
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result['checks'], indent=2))
    if not all(result['checks'][k] for k in ('gradient_pass', 'identity_pass', 'constraint_pass', 'zf_pass')):
        raise SystemExit(1)
