"""Read-only phase-direction check at one saved ISAC state, not an optimizer.

The input files are supplied by the caller. The current repository model is
re-evaluated, but this does not authenticate the source used in the saved run.
"""
import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np


def read_json(path):
    if path.stat().st_size > 128 * 1024 * 1024:
        raise ValueError('input exceeds 128 MiB read limit')
    with path.open(encoding='utf-8-sig') as stream:
        return json.load(stream, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def inspect(job, result, model, scheme, step):
    if not np.isfinite(step) or step <= 0:
        raise ValueError('step must be finite and positive')
    saved = result['metrics'][scheme]
    w = np.asarray(saved['w_re'], dtype=float) + 1j * np.asarray(saved['w_im'], dtype=float)
    theta = np.asarray(saved['theta_re'], dtype=float) + 1j * np.asarray(saved['theta_im'], dtype=float)
    rotation = np.asarray(saved['rotation'], dtype=float)
    if not all(np.isfinite(x).all() for x in (w, theta, rotation)):
        raise ValueError('nonfinite saved state')
    if np.max(np.abs(np.abs(theta) - 1)) > 1e-12:
        raise ValueError('saved phase is not unit modulus')
    iota = float(saved['iota'])
    metric, (_, ambient, _) = model.evaluate(w, theta, rotation, job, iota, True)
    gradient = model.tangent(theta, ambient)
    directions = []
    for sign in (1, -1):
        v = theta + sign * step * gradient
        if np.any(np.abs(v) == 0):
            raise ValueError('retraction undefined')
        v = v / np.abs(v)
        directions.append(float(model.evaluate(w, v, rotation, job, iota)['utility']))
    value = float(metric['utility'])
    analytic = float(np.real(np.vdot(gradient, gradient)))
    centered = float((directions[0] - directions[1]) / (2 * step))
    history = result['history'][scheme]
    return {'scope': 'one saved final state, using current source and saved job',
            'scheme': scheme, 'stored_utility': float(saved['utility']),
            'recomputed_utility': value, 'utility_difference': value - float(saved['utility']),
            'ambient_gradient_norm': float(np.linalg.norm(ambient)),
            'projected_gradient_norm': float(np.linalg.norm(gradient)),
            'analytic_ascent_directional_derivative': analytic,
            'centered_directional_difference': centered,
            'positive_retraction_change': directions[0] - value,
            'negative_retraction_change': directions[1] - value,
            'step': step, 'saved_outer_converged': bool(history['converged']),
            'saved_full_converged': bool(history['full_converged']),
            'saved_termination_reason': history['termination_reason'],
            'source_identity_authenticated': False,
            'saved_inner_directions_replayed': False, 'full_paper_pass': False,
            'limitations': ['floating finite differences are not interval bounds',
                            'does not authenticate historical job or source identity',
                            'not a replay of recorded optimization directions',
                            'one state, not the paper figures or convergence proof']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job', type=Path, required=True)
    parser.add_argument('--result', type=Path, required=True)
    parser.add_argument('--scheme', default='Rot-BS & Fix-RIS')
    parser.add_argument('--step', type=float, default=1e-6)
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[2] / 'strict' / 'rotatable-isac' / 'core.py'
    spec = importlib.util.spec_from_file_location('rotatable_isac_saved_check_core', source)
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)
    print(json.dumps(inspect(read_json(args.job), read_json(args.result), model,
                             args.scheme, args.step), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
