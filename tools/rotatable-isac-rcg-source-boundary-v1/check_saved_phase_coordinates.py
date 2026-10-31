"""Read-only coordinate finite differences at one saved ISAC state.

This is a current-model check, not source authentication, an optimizer replay,
an interval proof or a paper-figure acceptance.
"""
import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np

from check_saved_state_direction import read_json


def inspect(job, result, model, scheme, step):
    if not np.isfinite(step) or step <= 0:
        raise ValueError('finite positive angular step required')
    saved = result['metrics'][scheme]
    w = np.asarray(saved['w_re'], float) + 1j * np.asarray(saved['w_im'], float)
    theta = np.asarray(saved['theta_re'], float) + 1j * np.asarray(saved['theta_im'], float)
    rotation = np.asarray(saved['rotation'], float)
    iota = float(saved['iota'])
    if not all(np.isfinite(v).all() for v in (w, theta, rotation)) or not np.isfinite(iota):
        raise ValueError('nonfinite saved state')
    if theta.ndim != 1 or len(theta) == 0 or np.max(np.abs(np.abs(theta) - 1)) > 1e-12:
        raise ValueError('saved phases must be a nonempty unit-modulus vector')
    metric, (_, ambient, _) = model.evaluate(w, theta, rotation, job, iota, True)
    tangent = model.tangent(theta, ambient)
    analytic = np.real(np.conj(ambient) * (1j * theta))
    numeric = []
    for k in range(len(theta)):
        plus, minus = theta.copy(), theta.copy()
        plus[k] *= np.exp(1j * step)
        minus[k] *= np.exp(-1j * step)
        fplus = model.evaluate(w, plus, rotation, job, iota)['utility']
        fminus = model.evaluate(w, minus, rotation, job, iota)['utility']
        numeric.append((fplus - fminus) / (2 * step))
    numeric = np.asarray(numeric, float)
    if not np.isfinite(analytic).all() or not np.isfinite(numeric).all():
        raise ValueError('nonfinite phase derivative')
    difference = float(np.max(np.abs(numeric - analytic)))
    tolerance = float(1e-5 * max(1., float(np.max(np.abs(analytic)))))
    history = result['history'][scheme]
    return {'scope': 'one saved state; coordinate derivatives with current model',
            'scheme': scheme, 'phase_elements': len(theta), 'angular_step': float(step),
            'stored_utility': float(saved['utility']),
            'recomputed_utility': float(metric['utility']),
            'max_abs_coordinate_derivative_difference': difference,
            'comparison_tolerance': tolerance, 'coordinate_derivatives_agree': difference <= tolerance,
            'finite_difference_gradient_squared_norm': float(numeric @ numeric),
            'model_projected_gradient_squared_norm': float(np.real(np.vdot(tangent, tangent))),
            'saved_outer_converged': history['converged'],
            'saved_inner_all_converged': history['inner_all_converged'],
            'saved_full_converged': history['full_converged'],
            'saved_termination_reason': history['termination_reason'],
            'historical_source_authenticated': False, 'saved_trajectory_replayed': False,
            'full_paper_pass': False,
            'limitations': ['current model and fixed saved w, rotation, iota',
                            'floating finite differences are not interval bounds',
                            'saved history flags are not independent convergence evidence',
                            'one state, not MATLAB, reference or full figure verification']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--job', type=Path, required=True)
    p.add_argument('--result', type=Path, required=True)
    p.add_argument('--scheme', default='Rot-BS & Fix-RIS')
    p.add_argument('--step', type=float, default=1e-5)
    args = p.parse_args()
    source = Path(__file__).resolve().parents[2] / 'strict' / 'rotatable-isac' / 'core.py'
    spec = importlib.util.spec_from_file_location('rotatable_isac_coordinate_check_core', source)
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)
    report = inspect(read_json(args.job), read_json(args.result), model, args.scheme, args.step)
    print(json.dumps(report, indent=2, allow_nan=False))
    if not report['coordinate_derivatives_agree']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
