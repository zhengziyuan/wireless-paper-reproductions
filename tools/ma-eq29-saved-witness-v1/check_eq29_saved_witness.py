"""Check a saved MRT state against Eq. (26) and Eq. (29) of the MA paper.

This is a deterministic 30-matrix diagnostic, not a new optimization or an
error certificate for the full physical simulation.  Decimal output is a
binary64 approximation; discriminant signs are compared exactly for the
computed matrix entries using fractions.
"""
import argparse
import json
import math
from fractions import Fraction
from pathlib import Path

import numpy as np


def analyze(data):
    if data['schema'] != 'MA_FIG5_CASE7_GEOM0_EQ29_SAVED_INPUT_V1':
        raise ValueError('Unexpected saved state')
    pos = np.asarray(data['mrt_positions'], dtype=float)
    dirs = np.asarray(data['directions'], dtype=float)
    beta = np.asarray(data['beta'], dtype=float)
    kap = np.asarray(data['rician'], dtype=float)
    n, m = data['N'], data['M']
    if pos.shape != (n, 2) or dirs.shape != (m, 2) or beta.shape != (m,) or kap.shape != (m,):
        raise ValueError('Inconsistent dimensions')
    if not all(np.isfinite(v).all() for v in (pos, dirs, beta, kap)) or np.any(beta <= 0) or np.any(kap < 0):
        raise ValueError('Nonfinite or invalid data')
    wavelength = float(data['wavelength'])
    if not math.isfinite(wavelength) or wavelength <= 0:
        raise ValueError('Invalid wavelength')
    wave = 2 * math.pi / wavelength
    matrices = []
    max_eigen_relative_gap = 0.0
    max_repository_scale_gap = 0.0
    for antenna in range(n):
        for user in range(m):
            psi = np.zeros((2, 2), dtype=float)
            source_scaled = np.zeros((2, 2), dtype=float)
            for other in range(m):
                if other == user:
                    continue
                delta = dirs[user] - dirs[other]
                phasors = np.exp(1j * wave * (pos @ delta))
                tau = abs(sum(phasors[index] for index in range(n) if index != antenna))
                c1 = beta[other] * kap[user] * kap[other] / ((kap[user] + 1) * (kap[other] + 1))
                psi += c1 * tau * np.abs(np.outer(delta, delta))
                # The checked repository kernel builds its denominator scaled
                # by beta[user]; compare that scaled matrix without treating it
                # as the paper's unscaled Psi.
                tau_source = abs(phasors.sum() - phasors[antenna])
                q = beta[user] * beta[other] * kap[user] * kap[other] / ((kap[user] + 1) * (kap[other] + 1))
                source_scaled += q * tau_source * np.abs(np.outer(delta, delta))
            scale = float(np.max(np.abs(psi)))
            if not math.isfinite(scale) or scale <= 0:
                raise ValueError('Degenerate matrix not covered by this witness')
            normalized = psi / scale
            source_scale = float(np.max(np.abs(source_scaled)))
            if source_scale <= 0:
                raise ValueError('Degenerate repository matrix')
            scale_gap = float(np.max(np.abs(source_scaled - beta[user] * psi))) / source_scale
            max_repository_scale_gap = max(max_repository_scale_gap, scale_gap)
            a = Fraction.from_float(float(normalized[0, 0]))
            b = Fraction.from_float(float(normalized[0, 1]))
            d = Fraction.from_float(float(normalized[1, 1]))
            old_rad = (a - d) ** 2 - 4 * b ** 2
            proper_rad = (a - d) ** 2 + 4 * b ** 2
            eig = float(np.linalg.eigvalsh(normalized)[-1])
            formula = (float(a + d) + math.sqrt(float(proper_rad))) / 2
            max_eigen_relative_gap = max(max_eigen_relative_gap, abs(eig - formula) / abs(eig))
            matrices.append({'antenna_one_based': antenna + 1, 'user_one_based': user + 1,
                             'matrix_scale': scale, 'normalized_matrix': normalized.tolist(),
                             'printed_minus_discriminant_normalized': float(old_rad),
                             'correct_plus_discriminant_normalized': float(proper_rad),
                             'printed_minus_sign': (old_rad > 0) - (old_rad < 0),
                             'numpy_max_eigenvalue_normalized': eig,
                             'correct_formula_max_eigenvalue_normalized': formula})
    return {'schema': 'MA_EQ29_SAVED_MATRIX_WITNESS_V1',
            'scope': 'Fixed saved Python MRT position and geometry, Eq.26 real symmetric matrices; no optimizer or random samples.',
            'matrix_count': len(matrices),
            'negative_printed_discriminants': sum(x['printed_minus_sign'] < 0 for x in matrices),
            'maximum_relative_eigen_formula_difference': max_eigen_relative_gap,
            'maximum_relative_repository_beta_scaled_matrix_difference': max_repository_scale_gap,
            'matrices': matrices,
            'limitations': ['Matrix entries are reconstructed binary64 estimates, not interval-certified forward-model values.',
                            'The sign and characteristic-polynomial comparison applies to each computed symmetric matrix; it is not full-figure or whole-paper acceptance.',
                            'No interpretation of author intent or output generation beyond the stated Eq.29a/29b inconsistency.']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('saved_input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = analyze(json.loads(args.saved_input.read_text(encoding='utf8')))
    with args.output.open('x', encoding='utf8', newline='\n') as file:
        json.dump(result, file, indent=2, allow_nan=False)
        file.write('\n')


if __name__ == '__main__':
    main()
