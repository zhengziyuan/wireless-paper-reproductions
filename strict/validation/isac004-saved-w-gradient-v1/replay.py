"""Check W gradients at one saved No-RIS state; no optimizer or random draws."""
import argparse
import json
from pathlib import Path
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--input-dir', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
scene = json.loads((args.input_dir / 'scene.json').read_text(encoding='utf-8'))
with np.load(args.input_dir / 'operands.npz', allow_pickle=False) as values:
    w, fc, fs, pd = (values[name].copy() for name in ('w', 'fc', 'fs', 'pd'))
if (w.shape, fc.shape, fs.shape, pd.shape) != ((4, 6), (4, 2), (4, 66), (66,)):
    raise ValueError('Unexpected saved input shapes')
iota = float(scene['saved_previous_iota'])
noise = np.asarray(scene['noise'])
rho = float(scene['rho'])
users = 2

def objective(v):
    y = fc.conj().T @ v
    z = fs.conj().T @ v
    signal = abs(y[np.arange(users), np.arange(users)])**2
    interference = np.array([noise[i] + sum(abs(y[i, j])**2 for j in range(v.shape[1]) if j != i) for i in range(users)])
    pattern = (abs(z)**2).sum(axis=1)
    residual = pattern / iota - pd
    return float(np.log2(1 + signal / interference).sum() - rho * (residual @ residual) / (pd @ pd))

y = fc.conj().T @ w
z = fs.conj().T @ w
signal = abs(y[np.arange(users), np.arange(users)])**2
interference = np.array([noise[i] + sum(abs(y[i, j])**2 for j in range(w.shape[1]) if j != i) for i in range(users)])
total = interference + signal
coeff = np.repeat((1 / total - 1 / interference)[:, None], w.shape[1], axis=1)
coeff[np.arange(users), np.arange(users)] += 1 / interference
pattern = (abs(z)**2).sum(axis=1)
gradient = (2 * fc @ (coeff * y) / np.log(2)
            - 4 * rho * fs @ ((pattern - iota * pd)[:, None] * z) / (iota**2 * (pd @ pd)))
rows = []
for step in (1e-4, 1e-5, 1e-6):
    errors = []
    for row in range(w.shape[0]):
        for column in range(w.shape[1]):
            for part in ('real', 'imag'):
                delta = np.zeros_like(w)
                delta[row, column] = step if part == 'real' else 1j * step
                fd = (objective(w + delta) - objective(w - delta)) / (2 * step)
                exact = float(gradient[row, column].real if part == 'real' else gradient[row, column].imag)
                errors.append(abs(fd - exact))
    rows.append({'step': step, 'coordinates': len(errors), 'maximum_absolute_error': max(errors)})
report = {'schema': 'ISAC004_FIXED_SCALE_ALL_W_GRADIENT_CHECK_V1',
          'scope': 'One saved No-RIS intermediate state, fixed channels and scale; 48 real W coordinates. Perturbations need not meet power constraints and are not optimizer iterates.',
          'saved_iota': iota, 'results': rows, 'original_failure_retained': True,
          'original_loaded_code_identity_proven': False, 'full_scientific_acceptance': False}
with args.output.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(report, stream, indent=2, allow_nan=False)
    stream.write('\n')
print('Saved-state W-gradient diagnostic complete.')
