"""Check one saved No-RIS state; no optimizer, channel generation, or sampling."""
from argparse import ArgumentParser
from pathlib import Path
import json
import numpy as np

parser = ArgumentParser()
parser.add_argument('--input-dir', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
scene = json.loads((args.input_dir / 'scene.json').read_text(encoding='utf-8'))
with np.load(args.input_dir / 'operands.npz', allow_pickle=False) as f:
    if set(f.files) != {'w', 'theta', 'r', 'fc', 'interference', 'rate', 'bridge'}:
        raise ValueError('Unexpected operand set.')
    w, theta, r, fc, saved_interference, saved_rate, bridge = (
        f[k].copy() for k in ('w', 'theta', 'r', 'fc', 'interference', 'rate', 'bridge'))
if (w.shape, theta.shape, r.shape, fc.shape, bridge.shape, saved_interference.shape, saved_rate.shape) != ((4, 6), (36,), (6,), (4, 2), (4, 36), (2,), ()):
    raise ValueError('Unexpected stored array shapes.')
if not all(np.all(np.isfinite(v)) for v in (w, theta, r, fc, saved_interference, saved_rate, bridge)):
    raise ValueError('Nonfinite stored array.')
if not np.all(bridge == 0) or scene['case_metadata']['realization'] != 4:
    raise ValueError('Not the saved realization 4 No-RIS state.')

power = float(np.sum(np.abs(w) ** 2))
power_limit = float(scene['power'])
tol = float(scene['verification_tolerance'])
widths = np.r_[np.full(3, scene['bs_half_width_rad']), np.zeros(3)]
phase_error = float(np.max(np.abs(np.abs(theta) - 1)))
y = fc.conj().T @ w
noise = np.asarray(scene['noise'])
signal = np.abs(y[np.arange(2), np.arange(2)]) ** 2
interference = np.array([noise[i] + sum(abs(y[i, j]) ** 2 for j in range(w.shape[1]) if j != i) for i in range(2)])
if not np.all(interference > 0):
    raise ValueError('Nonpositive independently summed interference.')
rate_by_user = np.log2(1 + signal / interference)
rate = float(np.sum(rate_by_user))
report = {
    'scope': 'One retained ISAC004 Rot-BS No-RIS failure-state only; no solver was called.',
    'case': scene['case_metadata'],
    'power_watts': power, 'power_limit_watts': power_limit,
    'power_excess_watts': power - power_limit,
    'power_within_saved_config_tolerance': power <= power_limit + tol,
    'saved_config_tolerance': tol,
    'rotation_angles_rad': r.tolist(), 'rotation_bound_rad': widths.tolist(),
    'rotation_within_source_tolerance': bool(np.all(np.abs(r) <= widths + 1e-12)),
    'max_phase_unit_modulus_error': phase_error,
    'bridge_exact_zero': bool(np.all(bridge == 0)),
    'independent_interference': interference.tolist(),
    'saved_interference': saved_interference.tolist(),
    'independent_rate_by_user': rate_by_user.tolist(),
    'independent_rate': rate, 'saved_rate': float(saved_rate),
    'max_interference_absolute_difference': float(np.max(np.abs(interference - saved_interference))),
    'rate_absolute_difference': abs(rate - float(saved_rate)),
    'caveat': 'Unit modulus is a baseline placeholder in No-RIS. No end-to-end physical, original-reference, MATLAB, convergence, or figure acceptance is implied. The original zero-overlap failure remains.',
}
with args.output.open('x', encoding='utf-8', newline='\n') as f:
    json.dump(report, f, indent=2, allow_nan=False)
    f.write('\n')
print('One saved-state check complete; output:', args.output)
